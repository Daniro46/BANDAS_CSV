"""Flag dates outside the expected range, in HD and DD_DAILY. Flag 7.

The oldest expected BANDAS date is from 1900 and the newest should not pass 2020.
Dates outside [MIN_YEAR, MAX_YEAR] are kept as they are, only flagged.
"""

from . import load

SUSPICIOUS_DATE, add_flag = load("03_flags", "SUSPICIOUS_DATE", "add_flag")

MIN_YEAR = 1900
MAX_YEAR = 2020


def flag_date_range(table, date_column):
    """Add flag 7 to `table["flag"]` (in place) where `date_column` is out of range."""
    dates = table[date_column]
    out_of_range = dates.notna() & ~dates.dt.year.between(MIN_YEAR, MAX_YEAR)
    table["flag"] = add_flag(table["flag"], out_of_range, SUSPICIOUS_DATE)  # flag 7
