#!/usr/bin/env python3
"""
Archive daily predictions to track model performance over time.

This script saves each day's predictions to a historical archive and
updates a rolling performance tracker.
"""

import argparse
import csv
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS_FILE = REPO_ROOT / "web" / "src" / "data" / "todaysPredictions.json"
ARCHIVE_DIR = REPO_ROOT / "data" / "archive" / "predictions"
PERFORMANCE_TRACKER = REPO_ROOT / "data" / "archive" / "performance_tracker.csv"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Archive predictions and track performance over time."
    )
    parser.add_argument(
        "--date",
        help="Date to archive (YYYY-MM-DD). Defaults to today.",
    )
    return parser.parse_args()


def load_predictions() -> Dict[str, Any]:
    """Load today's predictions."""
    if not PREDICTIONS_FILE.exists():
        raise FileNotFoundError(f"Predictions file not found: {PREDICTIONS_FILE}")

    with open(PREDICTIONS_FILE) as f:
        return json.load(f)


def archive_predictions(data: Dict[str, Any], target_date: str) -> None:
    """Save predictions to date-stamped archive file."""
    ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    archive_file = ARCHIVE_DIR / f"predictions_{target_date}.json"

    # Add archive metadata
    archived_data = {
        "archivedAt": datetime.now(timezone.utc).isoformat(),
        "originalDate": target_date,
        **data,
    }

    with open(archive_file, "w") as f:
        json.dump(archived_data, f, indent=2)

    print(f"📦 Archived predictions → {archive_file}")


def initialize_performance_tracker() -> None:
    """Create performance tracker CSV if it doesn't exist."""
    if PERFORMANCE_TRACKER.exists():
        return

    PERFORMANCE_TRACKER.parent.mkdir(parents=True, exist_ok=True)

    headers = [
        "date",
        "total_games",
        "high_confidence_games",  # A/B grades
        "avg_edge",
        "avg_home_prob",
        "archived_at",
    ]

    with open(PERFORMANCE_TRACKER, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

    print(f"📊 Created performance tracker → {PERFORMANCE_TRACKER}")


def update_performance_tracker(data: Dict[str, Any], target_date: str) -> None:
    """Add today's summary stats to performance tracker."""
    initialize_performance_tracker()

    games = data.get("games", [])

    if not games:
        print("ℹ️  No games to track")
        return

    # Calculate summary stats
    total_games = len(games)
    high_confidence = sum(
        1 for g in games if g.get("confidenceGrade", "C")[0] in ["A", "B"]
    )
    avg_edge = sum(abs(g.get("edge", 0)) for g in games) / total_games
    avg_home_prob = sum(g.get("homeWinProb", 0.5) for g in games) / total_games

    # Append to tracker
    with open(PERFORMANCE_TRACKER, "a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "date",
                "total_games",
                "high_confidence_games",
                "avg_edge",
                "avg_home_prob",
                "archived_at",
            ],
        )
        writer.writerow(
            {
                "date": target_date,
                "total_games": total_games,
                "high_confidence_games": high_confidence,
                "avg_edge": f"{avg_edge:.4f}",
                "avg_home_prob": f"{avg_home_prob:.4f}",
                "archived_at": datetime.now(timezone.utc).isoformat(),
            }
        )

    print(f"📈 Updated performance tracker: {total_games} games, {high_confidence} high confidence")


def generate_archive_summary() -> None:
    """Generate a summary report of archived predictions."""
    if not PERFORMANCE_TRACKER.exists():
        return

    with open(PERFORMANCE_TRACKER, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return

    total_days = len(rows)
    total_games = sum(int(r["total_games"]) for r in rows)
    total_high_conf = sum(int(r["high_confidence_games"]) for r in rows)

    print("\n" + "=" * 60)
    print("📊 ARCHIVE SUMMARY")
    print("=" * 60)
    print(f"Total days archived: {total_days}")
    print(f"Total games tracked: {total_games}")
    print(f"High confidence picks: {total_high_conf} ({total_high_conf/total_games*100:.1f}%)")
    print(f"Average edge: {sum(float(r['avg_edge']) for r in rows) / total_days:.4f}")
    print("=" * 60)


def main() -> None:
    args = parse_args()

    # Determine target date
    if args.date:
        target_date = args.date
    else:
        target_date = datetime.now().strftime("%Y-%m-%d")

    print(f"📅 Archiving predictions for {target_date}")

    try:
        # Load current predictions
        data = load_predictions()

        # Archive to dated file
        archive_predictions(data, target_date)

        # Update performance tracker
        update_performance_tracker(data, target_date)

        # Show summary
        generate_archive_summary()

        print("\n✅ Archive complete!")

    except Exception as e:
        print(f"❌ Archive failed: {e}")
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
