"""Build the corrected `datetime` column of HD tables (pk_fecha + pk_hora). Flags 1, 5 and 6.

The original columns are kept as they are in the .mdb; only `datetime` (first
column) and `flag` (last column) are added. The day/month fix (flags 2-4) is
done by 04_day_month_swap.py.
"""

import pandas as pd

from . import load

NO_DATE, HOUR_24, INVALID_HOUR, add_flag, empty_flags = load(
    "03_flags", "NO_DATE", "HOUR_24", "INVALID_HOUR", "add_flag", "empty_flags"
)
fix_day_month = load("04_day_month_swap", "fix_day_month")


def read_hours(table):
    if "pk_hora" in table:
        return pd.to_numeric(table["pk_hora"], errors="coerce")
    return pd.Series(0, index=table.index)


def fix_hd_dates(table):
    """Return the HD table with `datetime` and `flag`, sorted by `datetime`."""
    dates = pd.to_datetime(table["pk_fecha"], errors="coerce").dt.normalize()
    hours = read_hours(table)
    # Valid hours are whole numbers 0-24; invalid ones are replaced by 0.
    valid_hour = hours.between(0, 24) & (hours % 1 == 0)

    # The order of the calls keeps the codes sorted in the flag column (1;2;...;6).
    flags = add_flag(empty_flags(table.index), dates.isna(), NO_DATE)          # flag 1
    fixed, flags = fix_day_month(dates, hours, flags)                          # flags 2-4
    flags = add_flag(flags, hours == 24, HOUR_24)                              # flag 5
    flags = add_flag(flags, dates.notna() & ~valid_hour, INVALID_HOUR)         # flag 6

    # No special case for hour 24: adding 24 h gives 00:00 of the next day.
    timestamp = fixed + pd.to_timedelta(hours.where(valid_hour, 0), unit="h")

    output = table.assign(pk_fecha=dates.dt.strftime("%Y-%m-%d"))
    output.insert(0, "datetime", timestamp)
    output["flag"] = flags
    return output.sort_values("datetime", kind="stable")
