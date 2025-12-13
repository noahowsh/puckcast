#!/usr/bin/env python3
"""Generate playerInjuries.json from injuries.json + today's predictions.

This script combines the comprehensive injury data with today's game schedule
to create a game-specific injury mapping used by the frontend.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
INJURIES_PATH = REPO_ROOT / "web" / "src" / "data" / "injuries.json"
PREDICTIONS_PATH = REPO_ROOT / "web" / "src" / "data" / "todaysPredictions.json"
OUTPUT_PATH = REPO_ROOT / "web" / "src" / "data" / "playerInjuries.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate player injuries for today's games.")
    parser.add_argument("--date", help="Target date (YYYY-MM-DD), defaults to today.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Output path.")
    return parser.parse_args()


def load_injuries() -> dict:
    """Load injuries data."""
    if not INJURIES_PATH.exists():
        print(f"  Warning: {INJURIES_PATH} not found")
        return {"teams": {}}

    with open(INJURIES_PATH) as f:
        return json.load(f)


def load_predictions() -> dict:
    """Load today's predictions to get game schedule."""
    if not PREDICTIONS_PATH.exists():
        print(f"  Warning: {PREDICTIONS_PATH} not found")
        return {"games": []}

    with open(PREDICTIONS_PATH) as f:
        return json.load(f)


def get_team_injuries(injuries_data: dict, team_abbrev: str) -> list:
    """Get injuries for a specific team."""
    team_data = injuries_data.get("teams", {}).get(team_abbrev, {})
    return team_data.get("injuries", [])


def format_injury_for_game(injury: dict, team_abbrev: str) -> dict:
    """Format injury record for the game context.

    Maps to TypeScript PlayerInjuryEntry type:
    - team: string
    - playerId?: number | null
    - name?: string | null
    - statusCode?: string | null
    - statusDescription?: string | null
    - position?: string | null
    """
    return {
        "team": team_abbrev,
        "playerId": injury.get("playerId"),
        "name": injury.get("playerName"),
        "statusCode": injury.get("status"),
        "statusDescription": injury.get("injuryDescription"),
        "position": injury.get("position"),
    }


def main() -> None:
    args = parse_args()

    target_date = args.date or datetime.now().strftime("%Y-%m-%d")
    print(f"Generating player injuries for {target_date}...")

    # Load data
    injuries_data = load_injuries()
    predictions_data = load_predictions()

    games = predictions_data.get("games", [])

    if not games:
        print("  No games found in predictions")

    # Build game-specific injury data
    game_injuries = []
    teams_data = {}

    for game in games:
        game_id = game.get("id", "") or game.get("gameId", "")
        game_date = game.get("gameDate", target_date)

        # Handle both object format {"name": "...", "abbrev": "STL"} and plain string
        home_team_data = game.get("homeTeam", {})
        away_team_data = game.get("awayTeam", {})

        if isinstance(home_team_data, dict):
            home_team = home_team_data.get("abbrev", "")
        else:
            home_team = home_team_data or ""

        if isinstance(away_team_data, dict):
            away_team = away_team_data.get("abbrev", "")
        else:
            away_team = away_team_data or ""

        # Get injuries for each team
        home_injuries = [
            format_injury_for_game(inj, home_team)
            for inj in get_team_injuries(injuries_data, home_team)
        ]
        away_injuries = [
            format_injury_for_game(inj, away_team)
            for inj in get_team_injuries(injuries_data, away_team)
        ]

        game_injuries.append({
            "gameId": game_id,
            "date": game_date,
            "home": home_team,
            "away": away_team,
            "homeInjuries": home_injuries,
            "awayInjuries": away_injuries,
        })

        # Also track team-level data - must match TypeScript type: { injuries: PlayerInjuryEntry[] }
        if home_team and home_team not in teams_data:
            teams_data[home_team] = {
                "injuries": home_injuries,
            }
        if away_team and away_team not in teams_data:
            teams_data[away_team] = {
                "injuries": away_injuries,
            }

    # Build output
    output = {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "date": target_date,
        "teams": teams_data,
        "games": game_injuries,
    }

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with open(args.output, "w") as f:
        json.dump(output, f, indent=2)

    print(f"  Wrote {len(game_injuries)} games with injury data to {args.output}")


if __name__ == "__main__":
    main()
