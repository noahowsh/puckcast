#!/usr/bin/env python3
"""
Generate explanations for individual game predictions.

This script analyzes the key factors influencing a prediction and generates
human-readable explanations.
"""

import argparse
import json
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS_FILE = REPO_ROOT / "web" / "src" / "data" / "todaysPredictions.json"
MODEL_INSIGHTS = REPO_ROOT / "web" / "src" / "data" / "modelInsights.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explain why the model made a specific prediction."
    )
    parser.add_argument(
        "--game-id",
        help="Game ID to explain (e.g., 2025020315)",
    )
    parser.add_argument(
        "--teams",
        nargs=2,
        help="Team abbreviations (e.g., TOR MTL)",
    )
    return parser.parse_args()


def load_predictions() -> Dict[str, Any]:
    """Load today's predictions."""
    if not PREDICTIONS_FILE.exists():
        raise FileNotFoundError(f"Predictions file not found: {PREDICTIONS_FILE}")

    with open(PREDICTIONS_FILE) as f:
        return json.load(f)


def find_game(predictions: Dict[str, Any], game_id: str | None, teams: List[str] | None) -> Dict[str, Any] | None:
    """Find a specific game in predictions."""
    games = predictions.get("games", [])

    if game_id:
        for game in games:
            if str(game.get("id")) == str(game_id):
                return game

    if teams and len(teams) == 2:
        team1, team2 = [t.upper() for t in teams]
        for game in games:
            home = game.get("homeTeam", {}).get("abbrev", "").upper()
            away = game.get("awayTeam", {}).get("abbrev", "").upper()

            if (home == team1 and away == team2) or (home == team2 and away == team1):
                return game

    return None


def analyze_confidence(game: Dict[str, Any]) -> List[str]:
    """Analyze confidence level and edge."""
    factors = []

    edge = abs(game.get("edge", 0)) * 100
    grade = game.get("confidenceGrade", "C")
    home_prob = game.get("homeWinProb", 0.5) * 100
    away_prob = game.get("awayWinProb", 0.5) * 100

    if grade[0] == "A":
        factors.append(f"**High confidence prediction** ({grade} grade)")
        factors.append(f"Model has strong conviction with {edge:.1f} point edge")
    elif grade[0] == "B":
        factors.append(f"**Moderate confidence** ({grade} grade)")
        factors.append(f"Model sees clear advantage with {edge:.1f} point edge")
    else:
        factors.append(f"**Low confidence** ({grade} grade)")
        factors.append(f"Game is close to 50/50 — only {edge:.1f} point edge")

    # Identify favorite
    if home_prob > away_prob:
        factors.append(f"Home team favored at {home_prob:.1f}% vs {away_prob:.1f}%")
    else:
        factors.append(f"Away team favored at {away_prob:.1f}% vs {home_prob:.1f}%")

    return factors


def analyze_special_teams(game: Dict[str, Any]) -> List[str]:
    """Analyze special teams matchup."""
    factors = []

    special_teams = game.get("specialTeams")
    if not special_teams:
        return factors

    home_split = special_teams.get("home", {})
    away_split = special_teams.get("away", {})

    home_diff = home_split.get("diff")
    away_diff = away_split.get("diff")

    if home_diff is not None and abs(home_diff) >= 3:
        if home_diff > 0:
            factors.append(
                f"**Home special teams advantage**: {home_diff:+.1f} pts (PP vs opponent PK)"
            )
        else:
            factors.append(
                f"**Home special teams disadvantage**: {home_diff:+.1f} pts"
            )

    if away_diff is not None and abs(away_diff) >= 3:
        if away_diff > 0:
            factors.append(
                f"**Away special teams advantage**: {away_diff:+.1f} pts (PP vs opponent PK)"
            )
        else:
            factors.append(
                f"**Away special teams disadvantage**: {away_diff:+.1f} pts"
            )

    return factors


def analyze_goalie_matchup(game: Dict[str, Any]) -> List[str]:
    """Analyze goalie matchup if available."""
    factors = []

    projected_goalies = game.get("projectedGoalies")
    if not projected_goalies:
        return factors

    home_goalie = projected_goalies.get("home")
    away_goalie = projected_goalies.get("away")

    if home_goalie:
        name = home_goalie.get("name", "Unknown")
        likelihood = home_goalie.get("startLikelihood", 0) * 100
        if likelihood >= 75:
            factors.append(f"**Home goalie**: {name} (confirmed starter)")

    if away_goalie:
        name = away_goalie.get("name", "Unknown")
        likelihood = away_goalie.get("startLikelihood", 0) * 100
        if likelihood >= 75:
            factors.append(f"**Away goalie**: {name} (confirmed starter)")

    return factors


def generate_explanation(game: Dict[str, Any]) -> str:
    """Generate full explanation for a game."""
    home_team = game.get("homeTeam", {})
    away_team = game.get("awayTeam", {})

    home_name = home_team.get("name", home_team.get("abbrev", "Home"))
    away_name = away_team.get("name", away_team.get("abbrev", "Away"))

    explanation = f"""
╔════════════════════════════════════════════════════════════╗
║          PREDICTION EXPLANATION                             ║
╚════════════════════════════════════════════════════════════╝

**Matchup:** {away_name} @ {home_name}
**Game ID:** {game.get('id')}
**Date:** {game.get('gameDate')}

{game.get('summary', '')}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 🎯 Confidence Analysis

"""

    # Add confidence factors
    confidence_factors = analyze_confidence(game)
    for factor in confidence_factors:
        explanation += f"• {factor}\n"

    # Add special teams analysis
    special_teams_factors = analyze_special_teams(game)
    if special_teams_factors:
        explanation += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        explanation += "## ⚡ Special Teams Matchup\n\n"
        for factor in special_teams_factors:
            explanation += f"• {factor}\n"

    # Add goalie analysis
    goalie_factors = analyze_goalie_matchup(game)
    if goalie_factors:
        explanation += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        explanation += "## 🥅 Goalie Matchup\n\n"
        for factor in goalie_factors:
            explanation += f"• {factor}\n"

    # Add feature importance (if available)
    explanation += "\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n"
    explanation += "## 📈 Key Factors Considered\n\n"
    explanation += """
The V6.0 model analyzes 141+ features to make this prediction:

• **Recent Form**: Rolling 3/5/10 game win rates, goal differentials
• **Goalie Performance**: Save %, goals saved above expected, rest days
• **Schedule Factors**: Back-to-backs, rest advantages, travel burden
• **Team Strength**: Season stats, power rankings, home/away splits
• **Shot Quality**: Expected goals (xG), high-danger chances, Corsi/Fenwick
• **Special Teams**: Power play % vs opponent penalty kill %
• **Line Composition**: Top line usage, defensive pair strength
• **Injuries**: Key player absences and their impact

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

## 📊 How To Use This Prediction

"""

    grade = game.get("confidenceGrade", "C")

    if grade[0] == "A":
        explanation += """
**High confidence picks** (A-grade) have historically won at rates significantly
above baseline. These are the model's strongest recommendations.

✅ Recommended action: Strong consideration for betting/analysis
⚠️  Past performance: A-grade picks typically hit 70%+ accuracy
"""
    elif grade[0] == "B":
        explanation += """
**Moderate confidence picks** (B-grade) show clear edges but with more variance.
These are solid predictions but not slam dunks.

✅ Recommended action: Good value picks
⚠️  Past performance: B-grade picks typically hit 60-65% accuracy
"""
    else:
        explanation += """
**Low confidence picks** (C-grade) are close to 50/50. The model sees slight
edges but significant uncertainty.

⚠️  Recommended action: Proceed with caution or skip
⚠️  Past performance: C-grade picks are near coin-flip accuracy
"""

    explanation += """
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

**Model:** V6.0 Logistic Regression with 141+ features
**Training:** 3 seasons (2021-2024), ~3,690 games
**Overall Accuracy:** 60.89% (vs 53.7% baseline)

🏒 Puckcast.AI - 100% independent, NHL official APIs only
"""

    return explanation


def main() -> None:
    args = parse_args()

    if not args.game_id and not args.teams:
        print("❌ Error: Must provide --game-id or --teams")
        print("\nUsage:")
        print("  python explain_prediction.py --game-id 2025020315")
        print("  python explain_prediction.py --teams TOR MTL")
        return

    # Load predictions
    try:
        predictions = load_predictions()
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return

    # Find game
    game = find_game(predictions, args.game_id, args.teams)

    if not game:
        print(f"❌ Game not found")
        print(f"\nAvailable games today:")
        for g in predictions.get("games", []):
            home = g.get("homeTeam", {}).get("abbrev", "?")
            away = g.get("awayTeam", {}).get("abbrev", "?")
            gid = g.get("id", "?")
            print(f"  {away} @ {home} (ID: {gid})")
        return

    # Generate explanation
    explanation = generate_explanation(game)

    # Print
    print(explanation)


if __name__ == "__main__":
    main()
