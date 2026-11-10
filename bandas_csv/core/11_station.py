"""Convert one station (.mdb) into one CSV per table.

Output in <out_dir>/<station>/:
    <TABLE>.csv        every table with rows, named like the .mdb table in uppercase
                       (HD18243.csv, LI18243.csv...), with its original columns.
                       HD also gets `datetime` (corrected) and `flag`.
    DD<ID>_DAILY.csv   the DD table in long format: date, discharge, flag.
"""

from . import load

open_mdb, read_table, user_tables = load("02_access_reader", "open_mdb", "read_table", "user_tables")
fix_hd_dates = load("05_hd_dates", "fix_hd_dates")
dd_to_daily = load("06_dd_daily", "dd_to_daily")
flag_date_range = load("07_date_range", "flag_date_range")
flag_hd_dd_mismatch = load("08_hd_dd_check", "flag_hd_dd_mismatch")
flag_isolated_dates = load("09_isolated_dates", "flag_isolated_dates")
DATETIME_FORMAT, write_csv = load("10_csv_writer", "DATETIME_FORMAT", "write_csv")


def read_tables(db, station):
    """Return ({name: DataFrame} of the tables with rows, [(station, table, error), ...])."""
    tables, errors = {}, []
    for name in user_tables(db):
        try:
            table = read_table(db, name)
        except Exception as error:  # corrupt table: report it and continue
            errors.append((station, name, f"{type(error).__name__}: {error}"))
            continue
        if not table.empty:
            tables[name] = table
    return tables, errors


def is_hd(name, table):
    return name[:2].upper() == "HD" and "pk_fecha" in table


def convert_station(path, out_dir):
    """Write the station's CSV files and return the list of read errors."""
    station = path.stem
    db = open_mdb(path)
    tables, errors = read_tables(db, station)
    folder = out_dir / station
    folder.mkdir(parents=True, exist_ok=True)

    # DD first: its daily version is compared with HD (flag 8) and written last.
    daily = daily_name = None
    for name, table in tables.items():
        if name[:2].upper() == "DD":
            daily = dd_to_daily(table)
            daily_name = f"{name.upper()}_DAILY"
            if daily is not None:
                flag_date_range(daily, "date")  # flag 7 (07_date_range.py)

    for name, table in tables.items():
        if is_hd(name, table):
            table = fix_hd_dates(table)  # flags 1-6 (04_day_month_swap.py, 05_hd_dates.py)
            flag_date_range(table, "datetime")  # flag 7 (07_date_range.py)
            if daily is not None and "ngasto" in table:
                flag_hd_dd_mismatch(table, daily)  # flag 8 (08_hd_dd_check.py)
                flag_isolated_dates(table, daily)  # flag 9 (09_isolated_dates.py)
            write_csv(table, folder / f"{name.upper()}.csv", DATETIME_FORMAT)
        else:
            write_csv(table, folder / f"{name.upper()}.csv")

    if daily is not None:
        write_csv(daily, folder / f"{daily_name}.csv")
    return errors
