"""Convert the BANDAS .mdb files to .csv, fixing the HD dates.

Usage:
    python Scrips/Extras/bandas_csv/00_bandas_mdb_to_csv.py              # all stations
    python Scrips/Extras/bandas_csv/00_bandas_mdb_to_csv.py --n 5        # first 5
    python Scrips/Extras/bandas_csv/00_bandas_mdb_to_csv.py --stations 01002 18243

Output (default Data Base/BANDAS/Bases_Datos_Bandas_CSV/): one folder per
station (see core/11_station.py). If a station or table fails, _errors.txt lists it.

Helper modules (core/), numbered in the order the data goes through them:
    01_paths.py           project paths
    02_access_reader.py   reading .mdb files (access_parser, raw dates)
    03_flags.py           flag codes and helpers (each flag is assigned in one module)
    04_day_month_swap.py  day/month swap fix                     flags 2, 3, 4
    05_hd_dates.py        corrected HD datetime                  flags 1, 5, 6
    06_dd_daily.py        DD table to daily long format
    07_date_range.py      dates outside 1900-2020 (HD, DD)       flag 7
    08_hd_dd_check.py     HD vs DD comparison                    flag 8
    09_isolated_dates.py  isolated HD dates, probable errors     flag 9
    10_csv_writer.py      CSV output
    11_station.py         converts one station (uses 02-10)
Module names start with a number, so they are imported with core.load().
"""

import argparse
import os
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

from tqdm import tqdm

from core import load

BANDAS_DIR, DEFAULT_OUT = load("01_paths", "BANDAS_DIR", "DEFAULT_OUT")
convert_station = load("11_station", "convert_station")

ERRORS_FILE = "_errors.txt"


def parse_args():
    parser = argparse.ArgumentParser(description="Convert the BANDAS .mdb files to .csv")
    parser.add_argument("--n", type=int, help="only the first N stations")
    parser.add_argument("--stations", nargs="+", help="station IDs (e.g. 01002 18243)")
    parser.add_argument("--src", type=Path, default=BANDAS_DIR, help="folder with the .mdb files")
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT, help="output folder")
    parser.add_argument("--workers", type=int, default=max(1, (os.cpu_count() or 2) - 1))
    return parser.parse_args()


def select_files(src, stations, n):
    files = sorted(src.rglob("*.mdb"))
    if stations:
        files = [f for f in files if f.stem in set(stations)]
    return files[:n]


def safe_convert(job):
    """Convert one station; any error is returned instead of raised."""
    path, out_dir = job
    try:
        return convert_station(path, out_dir)
    except Exception as error:
        return [(path.stem, "", f"{type(error).__name__}: {error}")]


def write_errors(errors, out_dir):
    """Write _errors.txt (station, table, error; tab-separated) or remove an old one."""
    path = out_dir / ERRORS_FILE
    if errors:
        path.write_text("".join("\t".join(e) + "\n" for e in sorted(errors)), encoding="utf-8")
    else:
        path.unlink(missing_ok=True)


def main():
    args = parse_args()
    files = select_files(args.src, args.stations, args.n)
    if not files:
        raise SystemExit("No .mdb files to convert.")

    args.out.mkdir(parents=True, exist_ok=True)
    print(f"Converting {len(files)} stations -> {args.out}")

    errors = []
    jobs = [(f, args.out) for f in files]
    with ProcessPoolExecutor(max_workers=min(args.workers, len(files))) as pool:
        for station_errors in tqdm(pool.map(safe_convert, jobs), total=len(jobs)):
            errors += station_errors

    write_errors(errors, args.out)
    print(f"Done. Errors: {len(errors)}" + (f" (see {args.out / ERRORS_FILE})" if errors else ""))


if __name__ == "__main__":
    main()
