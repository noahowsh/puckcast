#!/usr/bin/env python3
"""Orchestrate the daily site refresh workflow."""

from __future__ import annotations

import argparse
import logging
import subprocess
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Iterable, Sequence, Tuple

LOGGER = logging.getLogger("refresh_site_data")

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "data"
WEB_DATA_DIR = REPO_ROOT / "web" / "src" / "data"
PREDICT_SCRIPT = REPO_ROOT / "predict_full.py"
STARTING_GOALIE_SCRIPT = REPO_ROOT / "scripts" / "fetch_starting_goalies.py"
STANDINGS_SCRIPT = REPO_ROOT / "scripts" / "fetch_current_standings.py"
METRICS_SCRIPT = REPO_ROOT / "scripts" / "generate_site_metrics.py"
GOALIE_PULSE_SCRIPT = REPO_ROOT / "scripts" / "generate_goalie_pulse.py"
GAMECENTER_INGEST_SCRIPT = REPO_ROOT / "scripts" / "run_gamecenter_ingest.py"
SHIFT_INGEST_SCRIPT = REPO_ROOT / "scripts" / "run_shift_ingest.py"
LINE_COMBO_SUMMARY_SCRIPT = REPO_ROOT / "scripts" / "summarize_line_combos.py"
PLAYER_HUB_ARTIFACT_SCRIPT = REPO_ROOT / "scripts" / "build_player_hub_artifacts.py"

SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from nhl_prediction.player_hub.context import refresh_player_hub_context  # noqa: E402
from _native_pipeline import derive_season_id  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Regenerate web JSON payloads for the marketing site.")
    parser.add_argument("--date", help="Override date (YYYY-MM-DD) passed to predict_full.py.")
    parser.add_argument("--skip-standings", action="store_true", help="Skip refreshing currentStandings.json.")
    parser.add_argument("--skip-metrics", action="store_true", help="Skip refreshing modelInsights.json.")
    parser.add_argument("--skip-goalie-pulse", action="store_true", help="Skip refreshing goaliePulse.json.")
    parser.add_argument(
        "--skip-line-combos",
        action="store_true",
        help="Skip summarizing line combos JSON payload.",
    )
    parser.add_argument(
        "--skip-player-hub-artifacts",
        action="store_true",
        help="Skip rebuilding Player Hub parquet artifacts for the slate.",
    )
    parser.add_argument(
        "--run-ingest",
        action="store_true",
        help="Trigger GameCenter + shift ingest scripts before running predictions.",
    )
    parser.add_argument(
        "--season",
        help="Season id (e.g., 20242025). Defaults to inferred season for the provided/derived date.",
    )
    parser.add_argument("--log-level", default="INFO", help="Logging level (DEBUG, INFO, WARNING, ...).")
    return parser.parse_args()


def configure_logging(level: str) -> None:
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s %(levelname)s %(message)s",
    )


def parse_target_date(date_arg: str | None) -> date:
    if not date_arg:
        return datetime.utcnow().date()
    try:
        return datetime.strptime(date_arg, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit(f"Invalid --date value '{date_arg}': {exc}") from exc


def verify_directories(paths: Iterable[Tuple[str, Path]]) -> None:
    missing = [(label, path) for label, path in paths if not path.exists()]
    if not missing:
        return
    messages = ", ".join(f"{label} ({path})" for label, path in missing)
    raise FileNotFoundError(f"Missing required data directories: {messages}")


def run_command(command: Sequence[str], description: str) -> None:
    LOGGER.info("→ %s", description)
    LOGGER.debug("Running command: %s", " ".join(command))
    subprocess.run(command, cwd=str(REPO_ROOT), check=True)


def call_python(script: Path, args: Sequence[str], description: str) -> None:
    if not script.exists():
        raise FileNotFoundError(f"{description} script missing: {script}")
    run_command([sys.executable, str(script), *args], description)


def refresh_starting_goalies(target: date) -> None:
    call_python(
        STARTING_GOALIE_SCRIPT,
        ["--date", target.isoformat()],
        "Starting goalie confirmations",
    )


def run_ingest(season_id: str) -> None:
    LOGGER.info("Running ingest for season %s", season_id)
    ingest_args = ["--season", season_id]
    call_python(GAMECENTER_INGEST_SCRIPT, ingest_args, "GameCenter ingest")
    call_python(SHIFT_INGEST_SCRIPT, ingest_args, "Shift ingest")


def refresh_predictions(date_arg: str | None) -> None:
    extra_args = [date_arg] if date_arg else []
    call_python(PREDICT_SCRIPT, extra_args, "Predictive model + todaysPredictions.json export")


def refresh_standings() -> None:
    call_python(STANDINGS_SCRIPT, [], "currentStandings.json refresh")


def refresh_model_insights() -> None:
    call_python(METRICS_SCRIPT, [], "modelInsights.json refresh")


def refresh_goalie_pulse(target: date) -> None:
    call_python(
        GOALIE_PULSE_SCRIPT,
        ["--date", target.isoformat()],
        "goaliePulse.json refresh",
    )


def refresh_player_hub(target: date, season_id: str) -> None:
    LOGGER.info("Refreshing Player Hub context (date=%s, season=%s)", target.isoformat(), season_id)
    refresh_player_hub_context(target, season_id)


def build_player_hub_artifacts(target: date, season_id: str, *, force: bool = False) -> None:
    LOGGER.info("Building Player Hub artifacts (date=%s, season=%s)", target.isoformat(), season_id)
    args = ["--season", season_id, "--date", target.isoformat()]
    if force:
        args.append("--force")
    call_python(PLAYER_HUB_ARTIFACT_SCRIPT, args, "Player Hub artifact generation")


def summarize_line_combos(season_id: str | None) -> None:
    combo_args: list[str] = []
    if season_id:
        combo_args.extend(["--season", season_id])
    call_python(LINE_COMBO_SUMMARY_SCRIPT, combo_args, "lineCombos.json export")


def required_directories() -> list[Tuple[str, Path]]:
    return [
        ("Raw data root", DATA_ROOT / "raw"),
        ("GameCenter cache", DATA_ROOT / "raw" / "web_v1"),
        ("Shift chart cache", DATA_ROOT / "raw" / "stats_rest" / "shiftcharts"),
        ("Processed data", DATA_ROOT / "processed"),
        ("Web data directory", WEB_DATA_DIR),
    ]


def main() -> None:
    args = parse_args()
    configure_logging(args.log_level)

    target_date = parse_target_date(args.date)
    season_id = args.season or derive_season_id(target_date)
    LOGGER.info("Starting site refresh (date=%s, season=%s)", target_date.isoformat(), season_id)

    if args.run_ingest:
        run_ingest(season_id)

    verify_directories(required_directories())
    refresh_starting_goalies(target_date)
    call_python(
        REPO_ROOT / "scripts" / "fetch_injuries.py",
        ["--date", target_date.isoformat()],
        "Player injury list",
    )

    if args.skip_line_combos:
        LOGGER.info("Skipping line combo summary (--skip-line-combos).")
    else:
        summarize_line_combos(season_id)

    if args.skip_player_hub_artifacts:
        LOGGER.info("Skipping Player Hub artifact build (--skip-player-hub-artifacts).")
    else:
        build_player_hub_artifacts(target_date, season_id, force=args.run_ingest)

    refresh_predictions(args.date)

    if args.skip_standings:
        LOGGER.info("Skipping standings refresh (--skip-standings).")
    else:
        refresh_standings()

    if args.skip_metrics:
        LOGGER.info("Skipping model insights refresh (--skip-metrics).")
    else:
        refresh_model_insights()

    if args.skip_goalie_pulse:
        LOGGER.info("Skipping goalie pulse refresh (--skip-goalie-pulse).")
    else:
        refresh_goalie_pulse(target_date)

    refresh_player_hub(target_date, season_id)

    LOGGER.info("Site data refresh complete.")


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        LOGGER.error("Command failed with exit code %s: %s", exc.returncode, exc)
        raise SystemExit(exc.returncode) from exc
