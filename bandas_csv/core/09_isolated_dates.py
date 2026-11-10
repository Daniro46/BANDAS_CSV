"""Flag isolated HD dates that are very probably errors. Flag 9.

Example: station 12587 has HD data from 1972 to 1980, plus two rows dated 1919
(discharge 0). They form a group 53 years away from the rest of the series.

To avoid false positives a group of rows is flagged only when ALL of these hold:
  1. Isolated: its dates are separated by more than GAP from the station's main
     period (the largest group of consecutive dates).
  2. Not backed by DD: the station has a DD table and DD has no data (>= 0) on
     any day of the group. Real isolated periods do appear in DD too.
  3. No discharge: no row of the group has ngasto > 0.
Rows are only flagged; nothing is moved or deleted.
"""

import pandas as pd

from . import load

ISOLATED_DATE, add_flag = load("03_flags", "ISOLATED_DATE", "add_flag")

GAP = pd.Timedelta(days=365)  # a break longer than this splits the series into groups


def date_groups(dates):
    """Group id of every dated row: consecutive dates split where the gap is > GAP."""
    ordered = dates.dropna().sort_values(kind="stable")
    return (ordered.diff() > GAP).cumsum()


def dd_days_with_data(daily):
    discharge = pd.to_numeric(daily["discharge"], errors="coerce")
    return set(daily.loc[discharge >= 0, "date"])


def isolated_rows(hd, daily):
    """True for the HD rows that meet the three conditions above."""
    flagged = pd.Series(False, index=hd.index)
    groups = date_groups(hd["datetime"])
    if groups.empty:
        return flagged

    main = groups.value_counts().idxmax()
    dd_days = dd_days_with_data(daily)
    discharge = pd.to_numeric(hd["ngasto"], errors="coerce")
    for group, rows in groups[groups != main].groupby(groups[groups != main]).groups.items():
        backed_by_dd = hd.loc[rows, "datetime"].dt.normalize().isin(dd_days).any()
        has_discharge = (discharge[rows] > 0).any()
        if not backed_by_dd and not has_discharge:
            flagged[rows] = True
    return flagged


def flag_isolated_dates(hd, daily):
    """Add flag 9 to `hd["flag"]` (in place). Needs the station's DD_DAILY table."""
    hd["flag"] = add_flag(hd["flag"], isolated_rows(hd, daily), ISOLATED_DATE)  # flag 9
