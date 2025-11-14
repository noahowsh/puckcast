#!/usr/bin/env python3
"""Orchestrate nightly data refresh tasks for puckcast."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path
import gzip
import shutil

REPO_ROOT = Path(__file__).resolve().parents[1]
PYTHON = sys.executable or "python3"
MONEYPUCK_CSV = REPO_ROOT / "data" / "moneypuck_all_games.csv"
MONEYPUCK_GZ = REPO_ROOT / "data" / "moneypuck_all_games.csv.gz"


def run_step(name: str, command: list[str]) -> None:
    print(f"\n{'=' * 80}\n▶ {name}\n{'=' * 80}")
    result = subprocess.run(command, cwd=REPO_ROOT, check=False)
    if result.returncode != 0:
        raise SystemExit(f"Step '{name}' failed with exit code {result.returncode}")


def refresh_predictions(date_arg: str | None) -> None:
    ensure_moneypuck_data()
    cmd = [PYTHON, str(REPO_ROOT / "predict_full.py")]
    if date_arg:
        cmd.append(date_arg)
    run_step("Run prediction pipeline", cmd)


def refresh_standings() -> None:
    cmd = [PYTHON, str(REPO_ROOT / "scripts" / "fetch_current_standings.py")]
    run_step("Update standing snapshot", cmd)


def refresh_metrics() -> None:
    cmd = [PYTHON, str(REPO_ROOT / "scripts" / "generate_site_metrics.py")]
    run_step("Regenerate site metrics", cmd)


def refresh_goalie_pulse(date_arg: str | None) -> None:
    cmd = [PYTHON, str(REPO_ROOT / "scripts" / "refresh_goalie_pulse.py")]
    if date_arg:
        cmd.extend(["--date", date_arg])
    run_step("Update goalie pulse", cmd)


def ensure_moneypuck_data() -> None:
    if MONEYPUCK_CSV.exists():
        return
    if MONEYPUCK_GZ.exists():
        print("[info] Inflating moneypuck_all_games.csv from bundled gzip...")
        MONEYPUCK_CSV.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(MONEYPUCK_GZ, "rb") as src, MONEYPUCK_CSV.open("wb") as dst:
            shutil.copyfileobj(src, dst)
        return
    raise SystemExit(
        "Missing data/moneypuck_all_games.csv. Add the CSV or the compressed data/moneypuck_all_games.csv.gz to run predictions."
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Refresh data bundles consumed by the web app.")
    parser.add_argument("--date", help="Predict games for YYYY-MM-DD (default: today)")
    parser.add_argument("--skip-predictions", action="store_true", help="Skip running predict_full.py")
    parser.add_argument("--skip-standings", action="store_true", help="Skip fetching NHL standings")
    parser.add_argument("--skip-goalies", action="store_true", help="Skip refreshing goalie pulse data")
    parser.add_argument("--include-metrics", action="store_true", help="Regenerate modelInsights.json as well")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.skip_predictions and args.skip_standings and args.skip_goalies and not args.include_metrics:
        raise SystemExit("Nothing to do. Enable at least one step.")

    if not args.skip_predictions:
        refresh_predictions(args.date)

    if not args.skip_standings:
        refresh_standings()

    if not args.skip_goalies:
        refresh_goalie_pulse(args.date)

    if args.include_metrics:
        refresh_metrics()

    print("\n✅ Data refresh complete")


if __name__ == "__main__":
    main()
