"""Fix HD dates stored with day and month swapped. Flags 2, 3 and 4.

In many stations and years, dates with day <= 12 were stored as MM/DD
(12-Jan-1986 appears as 1986-12-01). Access keeps rows in the order they were
entered, so for each year we count how many times the date goes backwards
compared with the previous row, once with the dates as stored and once with day
and month swapped. The more ordered version wins. Years without a clear winner
inherit the decision of the nearest decided year.
"""

import numpy as np
import pandas as pd

from . import load

DAY_MONTH_SWAPPED, SWAP_INHERITED, AMBIGUOUS_NOT_SWAPPED, add_flag = load(
    "03_flags", "DAY_MONTH_SWAPPED", "SWAP_INHERITED", "AMBIGUOUS_NOT_SWAPPED", "add_flag"
)

# A version wins when it has fewer than half the backsteps of the other one.
WIN_RATIO = 0.5


def swap_day_month(dates):
    """Swap day and month of the dates with day <= 12 (others are unchanged)."""
    valid = dates.dropna()
    swap = valid.dt.day <= 12
    swapped = pd.to_datetime(
        pd.DataFrame({
            "year": valid.dt.year,
            "month": valid.dt.day.where(swap, valid.dt.month),
            "day": valid.dt.month.where(swap, valid.dt.day),
        }),
        errors="coerce",
    )
    return swapped.reindex(dates.index)


def count_backsteps(times, years):
    """Per year, how many rows have an earlier time than the previous row."""
    return (times.diff() < pd.Timedelta(0)).groupby(years).sum()


def decide_swap(dates, hours):
    """Per-year DataFrame with two booleans: `swap` and `inherited`.

    dates: pk_fecha as stored (normalized), in physical row order.
    hours: pk_hora; used so several readings on the same day count as ordered.
    """
    valid = dates.dropna()
    offset = pd.to_timedelta(hours[valid.index].where(hours.between(0, 24), 0), unit="h")
    years = valid.dt.year

    as_stored = count_backsteps(valid + offset, years)
    swapped = count_backsteps(swap_day_month(valid) + offset, years)
    decision = pd.Series(
        np.select(
            [swapped < as_stored * WIN_RATIO, as_stored < swapped * WIN_RATIO],
            ["swap", "keep"],
            "tie",
        ),
        index=as_stored.index,
    )

    # Tie years take the decision of the nearest decided year; `inherited` marks them.
    decided = decision[decision != "tie"]
    if decided.empty:
        final = pd.Series("keep", index=decision.index)
    else:
        final = decided.reindex(decision.index, method="nearest")
    return pd.DataFrame({"swap": final == "swap", "inherited": decision == "tie"})


def fix_day_month(dates, hours, flags):
    """Swap day and month back where the year needs it.

    Returns (fixed dates, flags with codes 2, 3 and 4 added).
    """
    years = decide_swap(dates, hours)
    year = dates.dt.year
    swap = year.map(years["swap"]).fillna(False).astype(bool)
    inherited = year.map(years["inherited"]).fillna(False).astype(bool)
    # Only dates with day <= 12 (and day != month) change when swapped.
    ambiguous = (dates.dt.day <= 12) & (dates.dt.day != dates.dt.month)

    # Flags 2, 3 and 4 are exclusive: a row gets at most one of them.
    flags = add_flag(flags, swap & ambiguous & ~inherited, DAY_MONTH_SWAPPED)      # flag 2
    flags = add_flag(flags, swap & ambiguous & inherited, SWAP_INHERITED)          # flag 3
    flags = add_flag(flags, ~swap & ambiguous & inherited, AMBIGUOUS_NOT_SWAPPED)  # flag 4
    return dates.mask(swap, swap_day_month(dates)), flags
