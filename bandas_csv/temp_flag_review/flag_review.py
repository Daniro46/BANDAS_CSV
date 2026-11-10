"""TEMPORARY: one CSV per flag with the file and date of every problem, for manual review.

It reads the converter output (HD*.csv and DD*_DAILY.csv of every station) and
does not change core/ or the converter. Delete this folder when the review is done.

Usage (after running 00_bandas_mdb_to_csv.py):
    python Scrips/Extras/bandas_csv/temp_flag_review/flag_review.py

Output (default Data Base/BANDAS/Bases_Datos_Bandas_CSV_flag_review/):
    flag_1.csv ... flag_9.csv   station_id, file, date, rows
        one line per file and day with that flag; `rows` is how many rows of
        that day have it (HD has several readings per day, DD_DAILY one).
        Rows without a date (flag 1) have an empty `date`.
"""

import argparse
import csv
import os
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import pandas as pd
from tqdm import tqdm

# Reuse the converter's paths (core/ is one folder up).
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core import load  # noqa: E402

DEFAULT_OUT = load("01_paths", "DEFAULT_OUT")
FLAG_CODES = range(1, 10)
HEADER = ["station_id", "file", "date", "rows"]


def flagged_days(path):
    """[(code, date, rows), ...] for one HD or DD_DAILY file."""
    date_column = "date" if path.stem.endswith("_DAILY") else "datetime"
    table = pd.read_csv(path, usecols=[date_column, "flag"], dtype=str, keep_default_na=False)
    table = table[table["flag"] != "0"]
    if table.empty:
        return []
    table = table.assign(day=table[date_column].str[:10], code=table["flag"].str.split(";"))
    counts = table.explode("code").groupby(["code", "day"]).size()
    return [(int(code), day, int(rows)) for (code, day), rows in counts.items()]


def station_rows(folder):
    """All flagged days of one station folder: [(code, station, file, date, rows), ...]."""
    files = sorted(folder.glob("HD*.csv")) + sorted(folder.glob("DD*_DAILY.csv"))
    return [
        (code, folder.name, path.stem, day, rows)
        for path in files
        for code, day, rows in flagged_days(path)
    ]


def parse_args():
    parser = argparse.ArgumentParser(description="TEMPORARY: one CSV per flag for manual review")
    parser.add_argument("--src", type=Path, default=DEFAULT_OUT, help="converter output folder")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT.parent / "Bases_Datos_Bandas_CSV_flag_review")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    return parser.parse_args()


def main():
    args = parse_args()
    stations = sorted(p for p in args.src.iterdir() if p.is_dir())
    if not stations:
        raise SystemExit(f"No station folders in {args.src}")
    args.out.mkdir(parents=True, exist_ok=True)
    print(f"Reading {len(stations)} stations -> {args.out}")

    # Write to .tmp files and replace the old CSVs only at the end, so a file
    # that is open in Excel is not left empty.
    final = {code: args.out / f"flag_{code}.csv" for code in FLAG_CODES}
    temp = {code: path.with_suffix(".csv.tmp") for code, path in final.items()}
    handles = {code: open(path, "w", newline="", encoding="utf-8") for code, path in temp.items()}
    writers = {code: csv.writer(handle) for code, handle in handles.items()}
    for writer in writers.values():
        writer.writerow(HEADER)
    totals = {code: [0, 0] for code in FLAG_CODES}  # [days, rows]

    try:
        with ProcessPoolExecutor(max_workers=args.workers) as pool:
            for rows in tqdm(pool.map(station_rows, stations, chunksize=4), total=len(stations)):
                for code, *line in rows:
                    writers[code].writerow(line)
                    totals[code][0] += 1
                    totals[code][1] += line[-1]
    finally:
        for handle in handles.values():
            handle.close()

    for code, (days, rows) in totals.items():
        try:
            os.replace(temp[code], final[code])
            print(f"{final[code].name}: {days} file-days, {rows} rows")
        except PermissionError:
            temp[code].unlink(missing_ok=True)
            print(f"{final[code].name}: NOT updated, the file is open in another program (close it and run again)")


if __name__ == "__main__":
    main()
