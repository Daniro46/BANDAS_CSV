"""Write DataFrames to CSV with ISO dates."""

DATE_FORMAT = "%Y-%m-%d"
DATETIME_FORMAT = "%Y-%m-%d %H:%M"


def write_csv(table, path, date_format=None):
    """Write `table` as UTF-8 CSV.

    Without `date_format`, dates include the time only if some date column has one.
    """
    if date_format is None:
        dates = table.select_dtypes("datetime")
        has_time = any((dates[c].dropna() != dates[c].dropna().dt.normalize()).any() for c in dates)
        date_format = DATETIME_FORMAT if has_time else DATE_FORMAT
    table.to_csv(path, index=False, encoding="utf-8", date_format=date_format)
