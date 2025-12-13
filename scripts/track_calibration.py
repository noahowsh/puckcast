#!/usr/bin/env python3
"""
Track confidence calibration over time to validate that A-grade picks
actually perform better than B-grade picks, etc.

This script compares predicted confidence grades against actual outcomes
to ensure the model's confidence estimates are well-calibrated.
"""

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = REPO_ROOT / "data" / "archive" / "predictions"
CALIBRATION_TRACKER = REPO_ROOT / "data" / "archive" / "calibration_tracker.csv"
CALIBRATION_REPORT = REPO_ROOT / "web" / "src" / "data" / "calibrationReport.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Track and analyze confidence calibration over time."
    )
    parser.add_argument(
        "--days",
        type=int,
        default=30,
        help="Number of days to analyze (default: 30)",
    )
    return parser.parse_args()


def load_archived_predictions(days: int) -> List[Dict[str, Any]]:
    """Load recent archived predictions."""
    if not ARCHIVE_DIR.exists():
        print("⚠️  No archived predictions found")
        return []

    # Get all archive files, sorted by date (newest first)
    archive_files = sorted(ARCHIVE_DIR.glob("predictions_*.json"), reverse=True)

    # Load the most recent N days
    all_games = []
    for archive_file in archive_files[:days]:
        try:
            with open(archive_file) as f:
                data = json.load(f)
                games = data.get("games", [])
                date = data.get("originalDate") or archive_file.stem.split("_")[-1]

                for game in games:
                    game["archiveDate"] = date
                    all_games.append(game)

        except Exception as e:
            print(f"⚠️  Failed to load {archive_file}: {e}")
            continue

    return all_games


def fetch_game_results(game_id: str) -> Dict[str, Any] | None:
    """
    Fetch actual game results from NHL API.

    Returns game outcome with home/away scores if game is complete.
    """
    import ssl
    from urllib.request import Request, urlopen

    url = f"https://api-web.nhle.com/v1/gamecenter/{game_id}/boxscore"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    context = ssl._create_unverified_context()

    try:
        with urlopen(req, timeout=30, context=context) as response:
            data = json.loads(response.read().decode("utf-8"))
            game_state = data.get("gameState", "")

            if game_state not in ["FINAL", "OFF"]:
                return None  # Game not complete

            home_score = data.get("homeTeam", {}).get("score", 0)
            away_score = data.get("awayTeam", {}).get("score", 0)

            return {
                "gameId": game_id,
                "homeScore": home_score,
                "awayScore": away_score,
                "actualWinner": "home" if home_score > away_score else "away",
                "gameState": game_state,
            }
    except Exception as e:
        print(f"  Failed to fetch results for game {game_id}: {e}")
        return None


def analyze_calibration(games: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Analyze calibration by confidence grade."""

    grade_stats = defaultdict(lambda: {"total": 0, "correct": 0, "sum_prob": 0.0})

    for game in games:
        grade = game.get("confidenceGrade", "C")
        home_prob = game.get("homeWinProb", 0.5)
        model_favorite = game.get("modelFavorite", "home")

        # Check if we have actual result
        actual_winner = game.get("actualWinner")  # Set manually or from API

        if actual_winner:
            is_correct = (
                (model_favorite == "home" and actual_winner == "home")
                or (model_favorite == "away" and actual_winner == "away")
            )

            grade_stats[grade]["total"] += 1
            grade_stats[grade]["correct"] += int(is_correct)

        # Track probability regardless of result
        grade_stats[grade]["sum_prob"] += max(home_prob, 1 - home_prob)

    # Calculate accuracy and average probability per grade
    results = {}
    for grade, stats in grade_stats.items():
        total = stats["total"]
        correct = stats["correct"]
        avg_prob = stats["sum_prob"] / max(total, 1)

        results[grade] = {
            "grade": grade,
            "total": total,
            "correct": correct,
            "accuracy": correct / total if total > 0 else 0.0,
            "avgProbability": avg_prob,
            "calibrationError": abs((correct / total if total > 0 else 0.0) - avg_prob),
        }

    return results


def generate_calibration_report(analysis: Dict[str, Any], days: int) -> None:
    """Generate JSON report for web frontend."""

    # Sort by grade (A+ to C)
    grade_order = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C"]
    sorted_grades = sorted(
        analysis.items(),
        key=lambda x: grade_order.index(x[0]) if x[0] in grade_order else 999,
    )

    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "daysAnalyzed": days,
        "gradePerformance": [stats for _, stats in sorted_grades],
        "summary": {
            "totalGames": sum(s["total"] for s in analysis.values()),
            "overallAccuracy": (
                sum(s["correct"] for s in analysis.values())
                / sum(s["total"] for s in analysis.values())
                if sum(s["total"] for s in analysis.values()) > 0
                else 0.0
            ),
            "avgCalibrationError": (
                sum(s["calibrationError"] for s in analysis.values()) / len(analysis)
                if analysis
                else 0.0
            ),
        },
        "notes": (
            "Calibration measures if predicted confidence matches actual accuracy. "
            "Low calibration error means A-grade picks really do win more than B-grade picks."
        ),
    }

    CALIBRATION_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(CALIBRATION_REPORT, "w") as f:
        json.dump(report, f, indent=2)

    print(f"📊 Generated calibration report → {CALIBRATION_REPORT}")


def update_calibration_tracker(analysis: Dict[str, Any]) -> None:
    """Append to historical calibration tracker."""

    # Initialize if doesn't exist
    if not CALIBRATION_TRACKER.exists():
        CALIBRATION_TRACKER.parent.mkdir(parents=True, exist_ok=True)
        with open(CALIBRATION_TRACKER, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "date",
                    "grade",
                    "total",
                    "correct",
                    "accuracy",
                    "avg_probability",
                    "calibration_error",
                ],
            )
            writer.writeheader()

    # Append today's analysis
    today = datetime.now().strftime("%Y-%m-%d")

    with open(CALIBRATION_TRACKER, "a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "date",
                "grade",
                "total",
                "correct",
                "accuracy",
                "avg_probability",
                "calibration_error",
            ],
        )

        for grade, stats in analysis.items():
            writer.writerow(
                {
                    "date": today,
                    "grade": grade,
                    "total": stats["total"],
                    "correct": stats["correct"],
                    "accuracy": f"{stats['accuracy']:.4f}",
                    "avg_probability": f"{stats['avgProbability']:.4f}",
                    "calibration_error": f"{stats['calibrationError']:.4f}",
                }
            )

    print(f"📈 Updated calibration tracker → {CALIBRATION_TRACKER}")


def print_summary(analysis: Dict[str, Any]) -> None:
    """Print calibration summary to console."""

    print("\n" + "=" * 70)
    print("📊 CONFIDENCE CALIBRATION ANALYSIS")
    print("=" * 70)
    print(f"{'Grade':<8} {'Games':<8} {'Correct':<8} {'Accuracy':<10} {'Avg Prob':<10} {'Error':<8}")
    print("-" * 70)

    grade_order = ["A+", "A", "A-", "B+", "B", "B-", "C+", "C"]
    for grade in grade_order:
        if grade in analysis:
            stats = analysis[grade]
            print(
                f"{grade:<8} {stats['total']:<8} {stats['correct']:<8} "
                f"{stats['accuracy']:<10.1%} {stats['avgProbability']:<10.1%} "
                f"{stats['calibrationError']:<8.3f}"
            )

    print("=" * 70)
    print(
        "\nInterpretation: Low calibration error means the model's confidence "
        "grades accurately reflect actual win rates."
    )
    print(
        "Example: If A-grade picks have 70% avg probability and 70% actual accuracy, "
        "calibration error is ~0."
    )
    print("=" * 70 + "\n")


def main() -> None:
    args = parse_args()

    print(f"📅 Analyzing last {args.days} days of predictions...")

    # Load archived predictions
    games = load_archived_predictions(args.days)

    if not games:
        print("❌ No archived predictions found. Run archive_predictions.py first.")
        return

    print(f"✅ Loaded {len(games)} games from archives")

    # Analyze calibration
    analysis = analyze_calibration(games)

    if not analysis:
        print("⚠️  Not enough data with outcomes to analyze calibration")
        return

    # Print summary
    print_summary(analysis)

    # Generate report for web
    generate_calibration_report(analysis, args.days)

    # Update historical tracker
    update_calibration_tracker(analysis)

    print("✅ Calibration tracking complete!")


if __name__ == "__main__":
    main()
