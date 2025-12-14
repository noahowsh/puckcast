#!/usr/bin/env python3
"""
Generate prediction results linking predictions to actual outcomes.

This script:
1. Fetches game results from the NHL API
2. Matches them with archived predictions
3. Computes accuracy metrics
4. Generates social-ready "model receipts" content

Output: web/src/data/predictionResults.json
"""

from __future__ import annotations

import argparse
import json
import ssl
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "web" / "src" / "data" / "predictionResults.json"
ARCHIVE_DIR = REPO_ROOT / "data" / "archive" / "predictions"
SCHEDULE_API = "https://api-web.nhle.com/v1/schedule"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate prediction results with accuracy metrics."
    )
    parser.add_argument(
        "--date",
        help="Date to check results for (YYYY-MM-DD). Defaults to yesterday.",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=7,
        help="Number of days to include in results. Default: 7",
    )
    return parser.parse_args()


def fetch_schedule(date: str) -> list[dict]:
    """Fetch schedule/results from NHL API."""
    url = f"{SCHEDULE_API}/{date}"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    context = ssl._create_unverified_context()

    try:
        with urlopen(req, timeout=30, context=context) as response:
            data = json.loads(response.read().decode("utf-8"))
            games = []
            for week in data.get("gameWeek", []):
                for game in week.get("games", []):
                    games.append(game)
            return games
    except Exception as e:
        print(f"  Failed to fetch schedule for {date}: {e}")
        return []


def load_archived_predictions(date: str) -> dict | None:
    """Load archived predictions for a specific date."""
    archive_file = ARCHIVE_DIR / f"predictions_{date}.json"
    if not archive_file.exists():
        return None
    try:
        return json.loads(archive_file.read_text())
    except Exception:
        return None


def match_predictions_to_results(
    predictions: dict, results: list[dict]
) -> list[dict]:
    """Match prediction records to actual game results."""
    matched = []

    pred_games = predictions.get("games", [])
    pred_by_id = {str(g.get("id")): g for g in pred_games}

    for result in results:
        game_id = str(result.get("id"))
        game_state = result.get("gameState", "")

        # Only process completed games
        if game_state not in ["FINAL", "OFF"]:
            continue

        prediction = pred_by_id.get(game_id)
        if not prediction:
            continue

        # Extract result info
        home_team = result.get("homeTeam", {})
        away_team = result.get("awayTeam", {})
        home_score = home_team.get("score", 0)
        away_score = away_team.get("score", 0)

        home_abbrev = home_team.get("abbrev", "")
        away_abbrev = away_team.get("abbrev", "")

        # Determine winner
        home_won = home_score > away_score
        was_overtime = result.get("periodDescriptor", {}).get("periodType", "") in ["OT", "SO"]

        # Check prediction accuracy
        pred_home_prob = prediction.get("homeWinProb", 0.5)
        pred_away_prob = prediction.get("awayWinProb", 0.5)
        model_favored_home = pred_home_prob > pred_away_prob
        confidence_grade = prediction.get("confidenceGrade", "C")
        edge = prediction.get("edge", 0)

        # Was prediction correct?
        correct = (model_favored_home and home_won) or (not model_favored_home and not home_won)

        # Calculate "deserved it more" metric
        # Higher prediction confidence + larger margin = more deserved
        win_margin = abs(home_score - away_score)
        prediction_strength = abs(pred_home_prob - 0.5)

        matched.append({
            "gameId": game_id,
            "date": result.get("gameDate", predictions.get("originalDate", "")),

            # Teams
            "homeTeam": home_abbrev,
            "awayTeam": away_abbrev,
            "homeScore": home_score,
            "awayScore": away_score,
            "winner": home_abbrev if home_won else away_abbrev,
            "loser": away_abbrev if home_won else home_abbrev,
            "wasOvertime": was_overtime,

            # Prediction details
            "predictedHomeProb": round(pred_home_prob, 3),
            "predictedAwayProb": round(pred_away_prob, 3),
            "modelFavorite": home_abbrev if model_favored_home else away_abbrev,
            "modelUnderdog": away_abbrev if model_favored_home else home_abbrev,
            "confidenceGrade": confidence_grade,
            "edge": round(edge, 3),

            # Result metrics
            "correct": correct,
            "upset": not correct and abs(edge) >= 0.1,  # Wrong on strong pick
            "closeCall": abs(pred_home_prob - 0.5) < 0.1,  # Near toss-up
            "bigHit": correct and abs(edge) >= 0.15,  # Right on strong pick

            # Margin info
            "goalMargin": win_margin,
            "predictionStrength": round(prediction_strength, 3),
        })

    return matched


def compute_accuracy_metrics(results: list[dict]) -> dict:
    """Compute accuracy statistics from matched results."""
    if not results:
        return {
            "totalGames": 0,
            "correct": 0,
            "incorrect": 0,
            "accuracy": 0,
        }

    total = len(results)
    correct = sum(1 for r in results if r["correct"])
    incorrect = total - correct

    # By confidence grade
    by_grade = {}
    for grade in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-"]:
        grade_results = [r for r in results if r["confidenceGrade"] == grade]
        if grade_results:
            grade_correct = sum(1 for r in grade_results if r["correct"])
            by_grade[grade] = {
                "total": len(grade_results),
                "correct": grade_correct,
                "accuracy": round(grade_correct / len(grade_results), 3),
            }

    # High confidence (A/B grades)
    high_conf = [r for r in results if r["confidenceGrade"][0] in ["A", "B"]]
    high_conf_correct = sum(1 for r in high_conf if r["correct"])

    # Upsets and big hits
    upsets = [r for r in results if r.get("upset")]
    big_hits = [r for r in results if r.get("bigHit")]

    return {
        "totalGames": total,
        "correct": correct,
        "incorrect": incorrect,
        "accuracy": round(correct / total, 3) if total > 0 else 0,

        "highConfidenceGames": len(high_conf),
        "highConfidenceCorrect": high_conf_correct,
        "highConfidenceAccuracy": round(high_conf_correct / len(high_conf), 3) if high_conf else 0,

        "byGrade": by_grade,

        "upsets": len(upsets),
        "bigHits": len(big_hits),
    }


def generate_social_content(results: list[dict], metrics: dict) -> dict:
    """Generate social media ready content from results."""

    # Best hits (correct predictions with highest edge)
    hits = sorted(
        [r for r in results if r["correct"]],
        key=lambda x: abs(x["edge"]),
        reverse=True,
    )[:5]

    # Worst misses (incorrect predictions with highest edge)
    misses = sorted(
        [r for r in results if not r["correct"]],
        key=lambda x: abs(x["edge"]),
        reverse=True,
    )[:5]

    # Biggest upsets (model was confident but wrong)
    upsets = [r for r in results if r.get("upset")]

    # Close games the model got right
    close_calls_correct = [
        r for r in results
        if r.get("closeCall") and r["correct"]
    ]

    return {
        "headline": f"Model went {metrics['correct']}-{metrics['incorrect']} ({metrics['accuracy']*100:.1f}%)",
        "highConfHeadline": f"High confidence: {metrics['highConfidenceCorrect']}/{metrics['highConfidenceGames']} ({metrics['highConfidenceAccuracy']*100:.1f}%)",

        "topHits": [
            {
                "matchup": f"{r['awayTeam']} @ {r['homeTeam']}",
                "result": f"{r['winner']} won {max(r['homeScore'], r['awayScore'])}-{min(r['homeScore'], r['awayScore'])}",
                "prediction": f"Model had {r['modelFavorite']} at {max(r['predictedHomeProb'], r['predictedAwayProb'])*100:.0f}%",
                "grade": r["confidenceGrade"],
            }
            for r in hits
        ],

        "bigMisses": [
            {
                "matchup": f"{r['awayTeam']} @ {r['homeTeam']}",
                "result": f"{r['winner']} won {max(r['homeScore'], r['awayScore'])}-{min(r['homeScore'], r['awayScore'])}",
                "prediction": f"Model had {r['modelFavorite']} at {max(r['predictedHomeProb'], r['predictedAwayProb'])*100:.0f}%",
                "grade": r["confidenceGrade"],
            }
            for r in misses
        ],

        "upsetCount": len(upsets),
        "closeCallsCorrect": len(close_calls_correct),
    }


def build_prediction_results(days: int, target_date: str | None = None) -> dict:
    """Build the complete prediction results payload."""
    if target_date:
        end_date = datetime.strptime(target_date, "%Y-%m-%d")
    else:
        # Default to yesterday (most recent completed day)
        end_date = datetime.now() - timedelta(days=1)

    all_matched = []
    dates_processed = []

    for i in range(days):
        check_date = end_date - timedelta(days=i)
        date_str = check_date.strftime("%Y-%m-%d")

        print(f"  Checking {date_str}...")

        # Load predictions
        predictions = load_archived_predictions(date_str)
        if not predictions:
            print(f"    No archived predictions for {date_str}")
            continue

        # Fetch results
        results = fetch_schedule(date_str)
        if not results:
            print(f"    No results for {date_str}")
            continue

        # Match predictions to results
        matched = match_predictions_to_results(predictions, results)
        if matched:
            all_matched.extend(matched)
            dates_processed.append(date_str)
            print(f"    Matched {len(matched)} games")

    # Compute metrics
    metrics = compute_accuracy_metrics(all_matched)

    # Generate social content
    social_content = generate_social_content(all_matched, metrics)

    # Sort by date (most recent first)
    all_matched.sort(key=lambda x: x["date"], reverse=True)

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "daysIncluded": len(dates_processed),
        "dateRange": {
            "start": min(dates_processed) if dates_processed else None,
            "end": max(dates_processed) if dates_processed else None,
        },

        # Summary metrics
        "metrics": metrics,

        # All matched results
        "results": all_matched,

        # Social-ready content
        "socialContent": social_content,
    }


def main() -> None:
    args = parse_args()

    print("=" * 70)
    print("PUCKCAST PREDICTION RESULTS GENERATOR")
    print("=" * 70)

    payload = build_prediction_results(days=args.days, target_date=args.date)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))

    print(f"\n Wrote prediction results to {OUTPUT_PATH}")
    print(f"   Games matched: {len(payload['results'])}")
    print(f"   Accuracy: {payload['metrics']['accuracy']*100:.1f}%")
    print(f"   Days included: {payload['daysIncluded']}")


if __name__ == "__main__":
    main()
