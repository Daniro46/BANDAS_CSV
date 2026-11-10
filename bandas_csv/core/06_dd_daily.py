"""DD table (daily discharge: pk_anio, pk_mes, ngasto_d01..d31) to long format.

Only real calendar days are kept (Feb 30, Apr 31... are dropped), as well as
rows with an impossible year or month (e.g. year 1381). The `flag` column
starts at "0"; flags 7 and 8 are added by 07_date_range.py and 08_hd_dd_check.py.
"""

import pandas as pd

from . import load

empty_flags = load("03_flags", "empty_flags")


def day_columns(dd):
    return [c for c in dd.columns if c.startswith("ngasto_d") and c[8:].isdigit()]


def dd_to_daily(dd):
    """DataFrame with date, discharge and flag; None if `dd` is not a valid DD table."""
    columns = day_columns(dd)
    if not columns or not {"pk_anio", "pk_mes"} <= set(dd.columns):
        return None

    long = dd.melt(id_vars=["pk_anio", "pk_mes"], value_vars=columns,
                   var_name="day_column", value_name="discharge")
    year = pd.to_numeric(long["pk_anio"], errors="coerce")
    month = pd.to_numeric(long["pk_mes"], errors="coerce")
    valid_year_month = year.between(1800, 2100) & month.between(1, 12)
    long["date"] = pd.to_datetime(
        pd.DataFrame({"year": year, "month": month, "day": long["day_column"].str[8:].astype(int)})
        .where(valid_year_month),
        errors="coerce",
    )

    daily = long.loc[long["date"].notna(), ["date", "discharge"]].sort_values("date", kind="stable")
    daily["flag"] = empty_flags(daily.index)
    return daily
