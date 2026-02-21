"""
Dry run: pull a small amount of real data from 247sports and verify DOM structure.
Run this before main.py to confirm the site layout hasn't changed.

Usage (from repo root):
  python -m scrape.utils.dryrun

Uses its own output and progress files so it does not affect production data.
Exits 0 if structure is valid, 1 otherwise.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

import pandas as pd

# Allow running as script or as module (utils dir -> parent.parent.parent = repo root)
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from scrape.utils.scrape_transfers import scrape_transfer_portal

DRYRUN_OUTPUT = "dryrun_transfer_data.csv"
DRYRUN_PROGRESS = "dryrun_progress.json"
MAX_RECORDS_PER_YEAR = 2


def _validate_structure(csv_path: str) -> Tuple[bool, List[str]]:
    """Check that CSV has expected columns and minimal data quality. Returns (ok, errors)."""
    errors = []
    if not os.path.exists(csv_path):
        return False, [f"Output file not created: {csv_path}"]

    df = pd.read_csv(csv_path)
    if len(df) == 0:
        return False, ["No records were captured."]

    expected_static = [
        "Player Name",
        "247Sports Profile URL",
        "Listing Year",
        "Position",
        "Height",
        "Rating",
        "Old School",
        "New School",
        "Weight",
    ]
    for col in expected_static:
        if col not in df.columns:
            errors.append(f"Missing expected column: {col}")

    if not any("Games Played (" in c for c in df.columns):
        errors.append("Missing dynamic column pattern: 'Games Played (Year)'")
    if not any("Minutes Played (" in c for c in df.columns):
        errors.append("Missing dynamic column pattern: 'Minutes Played (Year)'")
    if not any("Points Per Game (" in c for c in df.columns):
        errors.append("Missing dynamic column pattern: 'Points Per Game (Year)'")

    if (df["Height"] == "N/A").all():
        errors.append("Height column contains only N/A (DOM may have changed).")
    if (df["Rating"] == "N/A").all():
        errors.append("Rating column contains only N/A (DOM may have changed).")

    return len(errors) == 0, errors


def main() -> int:
    print("Dry run: fetching a few records from 247sports to verify DOM structure...")
    print(f"  Output: {DRYRUN_OUTPUT}, Progress: {DRYRUN_PROGRESS}")
    print(f"  Limit: {MAX_RECORDS_PER_YEAR} record(s) per year.\n")

    scrape_transfer_portal(
        max_records_per_year=MAX_RECORDS_PER_YEAR,
        output_filename=DRYRUN_OUTPUT,
        progress_file=DRYRUN_PROGRESS,
    )

    ok, errors = _validate_structure(DRYRUN_OUTPUT)
    if ok:
        n = len(pd.read_csv(DRYRUN_OUTPUT))
        print(f"\nDry run OK: DOM structure matches expectations ({n} record(s) in {DRYRUN_OUTPUT}).")
        return 0
    print("\nDry run FAILED (DOM may have changed):")
    for e in errors:
        print(f"  - {e}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
