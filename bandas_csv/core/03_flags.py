"""Codes for the `flag` column of HD[ID].csv and DD[ID]_DAILY.csv.

The column is "0" when the row has no issues; otherwise it lists every code
that applies, joined with ';' (e.g. "2;5"). Data values are never modified.
Each flag is computed and assigned in a single module (last column):

    0  no issues
    1  NO_DATE                pk_fecha is empty in the .mdb (0 in Access =      05_hd_dates.py
                              1899-12-30); `datetime` is left empty. (HD)
    2  DAY_MONTH_SWAPPED      the date was stored as MM/DD (day <= 12); day     04_day_month_swap.py
                              and month were swapped back, decided with the
                              row's own year. (HD)
    3  SWAP_INHERITED         day and month were swapped back, but the year     04_day_month_swap.py
                              had no clear signal and took the decision of
                              the nearest decided year. Never together with
                              2 or 4. (HD)
    4  AMBIGUOUS_NOT_SWAPPED  day <= 12 in a year with no clear signal; it      04_day_month_swap.py
                              inherited "keep" and was left as stored. (HD)
    5  HOUR_24                pk_hora = 24; converted to 00:00 of the next      05_hd_dates.py
                              day. (HD)
    6  INVALID_HOUR           pk_hora empty or outside 0-24; 00:00 was used.    05_hd_dates.py
                              (HD)
    7  SUSPICIOUS_DATE        date before 1900 or after 2020; kept as is.       07_date_range.py
                              (HD, DD_DAILY)
    8  HD_DD_MISMATCH         the daily mean of HD ngasto differs from the DD   08_hd_dd_check.py
                              discharge of that day by more than 10% (and
                              more than 0.001). (HD, DD_DAILY)
    9  ISOLATED_DATE          probable error: the row is in a group of dates     09_isolated_dates.py
                              more than 1 year away from the rest of the
                              series, with no DD data on those days and no
                              discharge > 0 (e.g. 1919 in a 1972-1980
                              station). (HD)
"""

import pandas as pd

NO_DATE = 1                 # flag 1 -> 05_hd_dates.py
DAY_MONTH_SWAPPED = 2       # flag 2 -> 04_day_month_swap.py
SWAP_INHERITED = 3          # flag 3 -> 04_day_month_swap.py
AMBIGUOUS_NOT_SWAPPED = 4   # flag 4 -> 04_day_month_swap.py
HOUR_24 = 5                 # flag 5 -> 05_hd_dates.py
INVALID_HOUR = 6            # flag 6 -> 05_hd_dates.py
SUSPICIOUS_DATE = 7         # flag 7 -> 07_date_range.py
HD_DD_MISMATCH = 8          # flag 8 -> 08_hd_dd_check.py
ISOLATED_DATE = 9           # flag 9 -> 09_isolated_dates.py


def empty_flags(index):
    """A flag column with no issues ("0") for every row."""
    return pd.Series("0", index=index)


def add_flag(flags, mask, code):
    """Append `code` to the flag column where mask is True."""
    with_code = (flags.mask(flags == "0", "") + f";{code}").str.lstrip(";")
    return flags.mask(mask, with_code)
