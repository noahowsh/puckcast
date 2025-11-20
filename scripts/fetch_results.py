#!/usr/bin/env python3
"""
Fetch game results from NHL API and update archived predictions.

This script runs after games complete to update predictions with actual outcomes,
enabling automated backtesting and accuracy tracking.
"""

import argparse
import json
import ssl
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
ARCHIVE_DIR = REPO_ROOT / "data" / "archive" / "predictions"
RESULTS_TRACKER = REPO_ROOT / "data" / "archive" / "results_tracker.csv"
BACKTESTING_REPORT = REPO_ROOT / "web" / "src" / "data" / "backtestingReport.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Fetch game results and update archived predictions."
    )
    parser.add_argument(
        "--date",
        help="Date to fetch results for (YYYY-MM-DD). Defaults to yesterday.",
    )
    parser.add_argument(
        "--days-back",
        type=int,
        default=7,
        help="Number of days back to check for results (default: 7)",
    )
    return parser.parse_args()


def fetch_game_result(game_id: str) -> Dict[str, Any] | None:
    """Fetch final score and result for a completed game."""
    try:
        # Use NHL Stats API v1 for game results
        url = f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        context = ssl._create_unverified_context()

        with urlopen(req, timeout=10, context=context) as response:
            data = json.loads(response.read().decode("utf-8"))

        game_data = data.get("gameData", {})
        live_data = data.get("liveData", {})
        line_score = live_data.get("linescore", {})

        # Check if game is final
        status = game_data.get("status", {})
        state = status.get("detailedState", "")

        if state not in ["Final", "Final/OT", "Final/SO"]:
            return None  # Game not complete yet

        # Get scores
        home_score = line_score.get("teams", {}).get("home", {}).get("goals")
        away_score = line_score.get("teams", {}).get("away", {}).get("goals")

        if home_score is None or away_score is None:
            return None

        return {
            "gameId": game_id,
            "homeScore": home_score,
            "awayScore": away_score,
            "winner": "home" if home_score > away_score else "away",
            "gameState": state,
            "fetchedAt": datetime.now(timezone.utc).isoformat(),
        }

    except Exception as e:
        print(f"⚠️  Failed to fetch result for game {game_id}: {e}")
        return None


def load_archived_predictions(date_str: str) -> Dict[str, Any] | None:
    """Load archived predictions for a specific date."""
    archive_file = ARCHIVE_DIR / f"predictions_{date_str}.json"

    if not archive_file.exists():
        return None

    with open(archive_file) as f:
        return json.load(f)


def update_predictions_with_results(
    predictions: Dict[str, Any], date_str: str
) -> tuple[int, int]:
    """Update predictions with actual results and return (total, updated) count."""
    games = predictions.get("games", [])
    updated_count = 0
    total_count = len(games)

    for game in games:
        # Skip if already has result
        if game.get("actualWinner"):
            continue

        game_id = game.get("id")
        if not game_id:
            continue

        # Fetch result
        result = fetch_game_result(game_id)

        if result:
            # Update game with result
            game["actualWinner"] = result["winner"]
            game["homeScore"] = result["homeScore"]
            game["awayScore"] = result["awayScore"]
            game["gameState"] = result["gameState"]
            game["resultFetchedAt"] = result["fetchedAt"]

            # Calculate if prediction was correct
            predicted_winner = game.get("modelFavorite", "home")
            actual_winner = result["winner"]
            game["predictionCorrect"] = predicted_winner == actual_winner

            updated_count += 1
            print(
                f"✅ {game['awayTeam']['abbrev']} @ {game['homeTeam']['abbrev']}: "
                f"{result['awayScore']}-{result['homeScore']} "
                f"({'✓' if game['predictionCorrect'] else '✗'})"
            )

    # Save updated predictions
    if updated_count > 0:
        archive_file = ARCHIVE_DIR / f"predictions_{date_str}.json"
        with open(archive_file, "w") as f:
            json.dump(predictions, f, indent=2)

    return total_count, updated_count


def generate_backtesting_report() -> None:
    """Generate comprehensive backtesting report from all archived predictions."""
    if not ARCHIVE_DIR.exists():
        print("⚠️  No archived predictions found")
        return

    all_games = []
    dates_processed = []

    # Load all archives with results
    for archive_file in sorted(ARCHIVE_DIR.glob("predictions_*.json")):
        try:
            with open(archive_file) as f:
                data = json.load(f)

            date = data.get("originalDate") or archive_file.stem.split("_")[-1]
            games = data.get("games", [])

            # Only include games with results
            games_with_results = [g for g in games if g.get("actualWinner")]

            if games_with_results:
                dates_processed.append(date)
                all_games.extend(games_with_results)

        except Exception as e:
            print(f"⚠️  Failed to load {archive_file}: {e}")
            continue

    if not all_games:
        print("ℹ️  No games with results found yet")
        return

    # Calculate overall metrics
    total_games = len(all_games)
    correct_predictions = sum(1 for g in all_games if g.get("predictionCorrect"))
    accuracy = correct_predictions / total_games if total_games > 0 else 0

    # Breakdown by confidence grade
    grade_stats = {}
    for grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C"]:
        grade_games = [g for g in all_games if g.get("confidenceGrade") == grade]
        if grade_games:
            correct = sum(1 for g in grade_games if g.get("predictionCorrect"))
            grade_stats[grade] = {
                "grade": grade,
                "games": len(grade_games),
                "correct": correct,
                "accuracy": correct / len(grade_games),
                "avgEdge": sum(abs(g.get("edge", 0)) for g in grade_games)
                / len(grade_games),
            }

    # Breakdown by team
    team_stats = {}
    for game in all_games:
        for team_key in ["homeTeam", "awayTeam"]:
            team = game.get(team_key, {}).get("abbrev")
            if not team:
                continue

            if team not in team_stats:
                team_stats[team] = {"games": 0, "correct": 0}

            team_stats[team]["games"] += 1
            if game.get("predictionCorrect"):
                team_stats[team]["correct"] += 1

    # Calculate team accuracy
    team_performance = [
        {
            "team": team,
            "games": stats["games"],
            "correct": stats["correct"],
            "accuracy": stats["correct"] / stats["games"],
        }
        for team, stats in team_stats.items()
        if stats["games"] >= 3  # Min 3 games
    ]
    team_performance.sort(key=lambda x: x["accuracy"], reverse=True)

    # Rolling accuracy (last 7/30 days)
    sorted_games = sorted(all_games, key=lambda g: g.get("gameDate", ""))
    last_7_days = sorted_games[-50:] if len(sorted_games) >= 50 else sorted_games
    last_30_days = sorted_games[-200:] if len(sorted_games) >= 200 else sorted_games

    last_7_correct = sum(1 for g in last_7_days if g.get("predictionCorrect"))
    last_30_correct = sum(1 for g in last_30_days if g.get("predictionCorrect"))

    # Generate report
    report = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "datesAnalyzed": len(dates_processed),
        "dateRange": {
            "start": dates_processed[0] if dates_processed else None,
            "end": dates_processed[-1] if dates_processed else None,
        },
        "overall": {
            "totalGames": total_games,
            "correctPredictions": correct_predictions,
            "accuracy": accuracy,
            "last7Days": {
                "games": len(last_7_days),
                "correct": last_7_correct,
                "accuracy": last_7_correct / len(last_7_days)
                if last_7_days
                else 0,
            },
            "last30Days": {
                "games": len(last_30_days),
                "correct": last_30_correct,
                "accuracy": last_30_correct / len(last_30_days)
                if last_30_days
                else 0,
            },
        },
        "byConfidence": list(grade_stats.values()),
        "byTeam": team_performance[:10],  # Top 10 teams
        "worstTeams": sorted(team_performance, key=lambda x: x["accuracy"])[:5],
    }

    # Save report
    BACKTESTING_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(BACKTESTING_REPORT, "w") as f:
        json.dump(report, f, indent=2)

    print(f"\n📊 Generated backtesting report → {BACKTESTING_REPORT}")
    print(f"   Total games: {total_games}")
    print(f"   Accuracy: {accuracy:.1%}")
    print(f"   Last 7 days: {last_7_correct}/{len(last_7_days)} ({last_7_correct/len(last_7_days)*100 if last_7_days else 0:.1f}%)")


def main() -> None:
    args = parse_args()

    # Determine date to fetch
    if args.date:
        target_date = datetime.strptime(args.date, "%Y-%m-%d").date()
    else:
        # Default to yesterday (games from yesterday should be complete)
        target_date = (datetime.now() - timedelta(days=1)).date()

    print(f"🔍 Fetching results starting from {target_date}")
    print(f"   Checking back {args.days_back} days for any missing results")

    total_updated = 0
    total_games = 0

    # Check multiple days back (in case we missed some)
    for days_back in range(args.days_back):
        check_date = target_date - timedelta(days=days_back)
        date_str = check_date.strftime("%Y-%m-%d")

        print(f"\n📅 Checking {date_str}...")

        # Load archived predictions
        predictions = load_archived_predictions(date_str)

        if not predictions:
            print(f"   ℹ️  No archived predictions found")
            continue

        # Update with results
        games_count, updated_count = update_predictions_with_results(
            predictions, date_str
        )

        total_games += games_count
        total_updated += updated_count

        if updated_count > 0:
            print(f"   ✅ Updated {updated_count}/{games_count} games")
        else:
            print(f"   ℹ️  No new results (already up to date)")

    # Generate comprehensive report
    print("\n" + "=" * 70)
    print("📊 GENERATING BACKTESTING REPORT")
    print("=" * 70)

    generate_backtesting_report()

    print("\n" + "=" * 70)
    print("✅ RESULTS FETCH COMPLETE")
    print(f"   Total games checked: {total_games}")
    print(f"   Newly updated: {total_updated}")
    print("=" * 70)


if __name__ == "__main__":
    main()
