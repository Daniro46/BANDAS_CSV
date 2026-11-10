"""Compare HD against DD and flag the days that do not match. Flag 8.

DD has explicit year/month/day, so it does not have the day/month problem. The
daily mean of HD should match DD; days that do not are flagged in both tables.
No value is ever replaced.
"""

import numpy as np
import pandas as pd

from . import load

HD_DD_MISMATCH, add_flag = load("03_flags", "HD_DD_MISMATCH", "add_flag")

TOLERANCE = 0.10  # maximum relative difference between the HD daily mean and DD
MIN_DIFF = 0.001  # minimum absolute difference to flag (days with discharge ~0)


def hd_daily_mean(hd):
    """Daily mean of ngasto by corrected date. Negative values (-999, -1 = no data) are skipped."""
    values = pd.Series(pd.to_numeric(hd["ngasto"], errors="coerce").to_numpy(),
                       index=hd["datetime"].dt.normalize())
    values = values[values.index.notna() & (values >= 0).to_numpy()]
    return values.groupby(level=0).mean()


def dd_by_day(daily):
    """DD discharge by date. Negative values (-999, -1 = no data) are skipped."""
    values = pd.to_numeric(daily.set_index("date")["discharge"], errors="coerce")
    return values[values >= 0].groupby(level=0).mean()


def mismatched_days(hd, daily):
    """Days with data in both tables where HD and DD disagree."""
    both = pd.concat({"hd": hd_daily_mean(hd), "dd": dd_by_day(daily)}, axis=1, join="inner")
    # A day matches if |HD mean - DD| <= max(10% of DD, 0.001).
    matches = (both["hd"] - both["dd"]).abs() <= np.maximum(TOLERANCE * both["dd"], MIN_DIFF)
    return both.index[~matches]


def flag_hd_dd_mismatch(hd, daily):
    """Add flag 8 to the `flag` column of `hd` and `daily` (both modified in place)."""
    days = mismatched_days(hd, daily)
    # Every HD row of a mismatched day, and the same days in DD_DAILY.
    hd["flag"] = add_flag(hd["flag"], hd["datetime"].dt.normalize().isin(days), HD_DD_MISMATCH)  # flag 8
    daily["flag"] = add_flag(daily["flag"], daily["date"].isin(days), HD_DD_MISMATCH)  # flag 8
