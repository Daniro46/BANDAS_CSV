"""Read BANDAS .mdb files with access_parser.

access_parser turns dates into text ("1960-01-01 00:00:00", "(Empty Date)", ...)
and handles negative dates incorrectly. Its converter is replaced here so dates
come back as datetime objects (None when empty), and pandas builds datetime64
columns without guessing formats.
"""

import math
import struct
from datetime import datetime, timedelta

import access_parser.utils as ap_utils
import pandas as pd
from access_parser import AccessParser

ACCESS_EPOCH = datetime(1899, 12, 30)


def access_date(raw):
    """Raw Access value (a double stored as int64) -> datetime.

    Access stores days since 1899-12-30; 0 means "no date". The fractional part
    is the time of day even for negative dates, hence abs().
    """
    days = struct.unpack("<d", struct.pack("<q", raw))[0]
    if days == 0 or not math.isfinite(days):
        return None
    whole = int(days)
    try:
        return ACCESS_EPOCH + timedelta(days=whole, seconds=round(abs(days - whole) * 86400))
    except OverflowError:
        return None


# access_parser's parse_type() looks this function up by name in its utils module.
ap_utils.mdb_date_to_readable = access_date


def open_mdb(path):
    return AccessParser(str(path))


def user_tables(db):
    """Table names, without Access system tables (MSys*)."""
    return [name for name in db.catalog if not name.lower().startswith("msys")]


def read_table(db, name):
    """Table as a DataFrame with lowercase column names (empty if it has no rows)."""
    data = db.parse_table(name)
    # Empty tables come back as {} or as a dict of scalars.
    if not data or not isinstance(next(iter(data.values())), list):
        return pd.DataFrame()
    return pd.DataFrame(data).rename(columns=lambda column: str(column).strip().lower())
