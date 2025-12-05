#!/usr/bin/env python3
"""
EMERGENCY SIMPLE PREDICTIONS
Generate basic predictions without loading full dataset
"""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / 'src'))
from nhl_prediction.nhl_api import fetch_todays_games

def create_simple_predictions():
    """Create simple 50/50 predictions for all games."""
    print("🏒 Fetching today's games from NHL API...")

    games = fetch_todays_games()
    if not games:
        print("❌ No games found")
        return []

    print(f"✅ Found {len(games)} games")

    predictions = []
    for game in games:
        predictions.append({
            "id": str(game.get('gameId')),
            "gameDate": game.get('gameDate'),
            "startTimeEt": game.get('startTimeUTC'),  # Will be formatted
            "startTimeUtc": game.get('startTimeUTC'),
            "homeTeam": {
                "name": game.get('homeTeamName', ''),
                "abbrev": game.get('homeTeamAbbrev', '')
            },
            "awayTeam": {
                "name": game.get('awayTeamName', ''),
                "abbrev": game.get('awayTeamAbbrev', '')
            },
            "homeWinProb": 0.5,  # 50/50 for now
            "awayWinProb": 0.5,
            "confidenceScore": 0.0,
            "confidenceGrade": "C",
            "edge": 0.0,
            "summary": f"Game data available. Full predictions updating soon.",
            "modelFavorite": "home",
            "venue": game.get('venue'),
            "season": str(game.get('season', ''))
        })

    return predictions

def main():
    try:
        predictions = create_simple_predictions()

        payload = {
            "generatedAt": datetime.now(timezone.utc).isoformat(),
            "games": predictions
        }

        output_path = Path("web/src/data/todaysPredictions.json")
        output_path.write_text(json.dumps(payload, indent=2))

        print(f"\n✅ Exported {len(predictions)} games to {output_path}")

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
