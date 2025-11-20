#!/usr/bin/env python3
"""
Validate data file schemas to ensure data integrity.
"""

import json
import sys
from pathlib import Path
from typing import Any, Dict

REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = REPO_ROOT / "web" / "src" / "data"


def validate_predictions(data: Dict[str, Any]) -> list[str]:
    """Validate todaysPredictions.json schema."""
    errors = []

    if "generatedAt" not in data:
        errors.append("Missing 'generatedAt' field")

    if "games" not in data:
        errors.append("Missing 'games' field")
        return errors

    games = data["games"]
    if not isinstance(games, list):
        errors.append("'games' must be a list")
        return errors

    required_game_fields = [
        "id", "gameDate", "homeTeam", "awayTeam",
        "homeWinProb", "awayWinProb", "confidenceGrade", "summary"
    ]

    for i, game in enumerate(games):
        for field in required_game_fields:
            if field not in game:
                errors.append(f"Game {i}: missing required field '{field}'")

        # Validate team structure
        for team_key in ["homeTeam", "awayTeam"]:
            if team_key in game:
                team = game[team_key]
                if not isinstance(team, dict):
                    errors.append(f"Game {i}: {team_key} must be an object")
                elif "name" not in team or "abbrev" not in team:
                    errors.append(f"Game {i}: {team_key} missing name or abbrev")

    return errors


def validate_model_insights(data: Dict[str, Any]) -> list[str]:
    """Validate modelInsights.json schema."""
    errors = []

    required_fields = ["generatedAt", "overall", "strategies", "confidenceBuckets"]

    for field in required_fields:
        if field not in data:
            errors.append(f"Missing required field '{field}'")

    if "overall" in data:
        overall = data["overall"]
        required_metrics = ["games", "accuracy", "baseline"]
        for metric in required_metrics:
            if metric not in overall:
                errors.append(f"'overall' missing '{metric}'")

    return errors


def validate_standings(data: Dict[str, Any]) -> list[str]:
    """Validate currentStandings.json schema."""
    errors = []

    if "teams" not in data:
        errors.append("Missing 'teams' field")
        return errors

    teams = data["teams"]
    if not isinstance(teams, list):
        errors.append("'teams' must be a list")
        return errors

    required_team_fields = ["team", "abbrev", "wins", "losses", "points"]

    for i, team in enumerate(teams):
        for field in required_team_fields:
            if field not in team:
                errors.append(f"Team {i}: missing required field '{field}'")

    return errors


def validate_goalie_pulse(data: Dict[str, Any]) -> list[str]:
    """Validate goaliePulse.json schema."""
    errors = []

    if "goalies" not in data:
        errors.append("Missing 'goalies' field")
        return errors

    goalies = data["goalies"]
    if not isinstance(goalies, list):
        errors.append("'goalies' must be a list")
        return errors

    required_goalie_fields = [
        "name", "team", "rollingGsa", "seasonGsa",
        "startLikelihood", "trend"
    ]

    for i, goalie in enumerate(goalies):
        for field in required_goalie_fields:
            if field not in goalie:
                errors.append(f"Goalie {i}: missing required field '{field}'")

        # Validate ranges
        if "startLikelihood" in goalie:
            likelihood = goalie["startLikelihood"]
            if not (0 <= likelihood <= 1):
                errors.append(f"Goalie {i}: startLikelihood out of range [0,1]")

    return errors


def main() -> int:
    """Run all validations."""
    validators = {
        "todaysPredictions.json": validate_predictions,
        "modelInsights.json": validate_model_insights,
        "currentStandings.json": validate_standings,
        "goaliePulse.json": validate_goalie_pulse,
    }

    all_errors = []

    for filename, validator in validators.items():
        file_path = DATA_DIR / filename

        if not file_path.exists():
            print(f"⚠️  {filename} not found (skipping)")
            continue

        print(f"🔍 Validating {filename}...")

        try:
            with open(file_path) as f:
                data = json.load(f)

            errors = validator(data)

            if errors:
                print(f"❌ {filename} has {len(errors)} error(s):")
                for error in errors:
                    print(f"  - {error}")
                all_errors.extend(errors)
            else:
                print(f"✅ {filename} is valid")

        except json.JSONDecodeError as e:
            print(f"❌ {filename} has invalid JSON: {e}")
            all_errors.append(f"{filename}: Invalid JSON")
        except Exception as e:
            print(f"❌ {filename} validation failed: {e}")
            all_errors.append(f"{filename}: {e}")

    print("\n" + "=" * 60)
    if all_errors:
        print(f"❌ Validation failed with {len(all_errors)} total error(s)")
        return 1
    else:
        print("✅ All data files passed validation")
        return 0


if __name__ == "__main__":
    sys.exit(main())
