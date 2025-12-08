#!/usr/bin/env python3
"""Fetch day-of starting goalies from the NHL API.

This script fetches game data and probable starters from the NHL's
modern API endpoint.

Note: Rotowire was considered but requires JavaScript rendering.
The NHL API provides reliable data that can be fetched directly.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

NHL_SCHEDULE_API = "https://api-web.nhle.com/v1/schedule"
NHL_GAME_API = "https://api-web.nhle.com/v1/gamecenter"

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "web" / "src" / "data" / "startingGoalies.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch NHL starting goalies from NHL API.")
    parser.add_argument("--date", help="Date string (YYYY-MM-DD), defaults to today.")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP request timeout (seconds).")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Output file path.")
    return parser.parse_args()


def generate_player_id(name: str, team: str) -> int:
    """Generate deterministic player ID from name and team."""
    combined = f"{name}{team}"
    hash_value = 0
    for char in combined:
        hash_value = ((hash_value << 5) - hash_value) + ord(char)
        hash_value = hash_value & 0xFFFFFFFF
    return hash_value


def fetch_schedule(date: str, timeout: float) -> list[dict[str, Any]]:
    """Fetch NHL schedule for a specific date."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PuckCast/1.0; +https://puckcast.ai)",
        "Accept": "application/json",
    }

    url = f"{NHL_SCHEDULE_API}/{date}"

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Failed to fetch schedule for {date}: {e}")
        return []

    data = response.json()
    games = []

    for week in data.get("gameWeek", []):
        for game in week.get("games", []):
            games.append({
                "gameId": game["id"],
                "gameDate": week["date"],
                "gameState": game["gameState"],
                "startTimeUTC": game["startTimeUTC"],
                "homeTeamId": game["homeTeam"]["id"],
                "homeTeamAbbrev": game["homeTeam"]["abbrev"],
                "homeTeamName": game["homeTeam"].get("commonName", {}).get("default", ""),
                "awayTeamId": game["awayTeam"]["id"],
                "awayTeamAbbrev": game["awayTeam"]["abbrev"],
                "awayTeamName": game["awayTeam"].get("commonName", {}).get("default", ""),
            })

    return games


def fetch_game_details(game_id: int, timeout: float) -> dict[str, Any] | None:
    """Fetch detailed game data including probable starters."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PuckCast/1.0; +https://puckcast.ai)",
        "Accept": "application/json",
    }

    url = f"{NHL_GAME_API}/{game_id}/landing"

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"  ⚠️  Could not fetch game {game_id}: {e}")
        return None


def extract_goalie_info(game_data: dict[str, Any], side: str) -> dict[str, Any] | None:
    """Extract goalie information from game data."""
    if not game_data:
        return None

    now = datetime.utcnow().isoformat() + "Z"
    team_data = game_data.get(f"{side}Team", {})
    team_abbrev = team_data.get("abbrev", "")

    # Try to get starting goalie from various places in the API response
    # The NHL API structure can vary, so we try multiple approaches

    # Method 1: Check for goalies in roster spots
    roster = game_data.get("rosterSpots", [])
    for player in roster:
        if player.get("positionCode") == "G":
            team_id = player.get("teamId")
            if team_id == team_data.get("id"):
                first_name = player.get("firstName", {}).get("default", "")
                last_name = player.get("lastName", {}).get("default", "")
                player_name = f"{first_name} {last_name}".strip()

                if player_name:
                    return {
                        "team": team_abbrev,
                        "playerId": player.get("playerId") or generate_player_id(player_name, team_abbrev),
                        "goalieName": player_name,
                        "confirmedStart": True,
                        "statusCode": "confirmed",
                        "statusDescription": "From NHL API roster",
                        "lastUpdated": now,
                    }

    # Method 2: Check matchup data
    matchup = game_data.get("matchup", {})
    if matchup:
        goalie_comparison = matchup.get("goalieComparison", {})
        side_key = f"{side}Team"
        if side_key in goalie_comparison:
            goalie_data = goalie_comparison[side_key]
            player_name = goalie_data.get("name", {}).get("default", "")
            if player_name:
                return {
                    "team": team_abbrev,
                    "playerId": goalie_data.get("playerId") or generate_player_id(player_name, team_abbrev),
                    "goalieName": player_name,
                    "confirmedStart": True,
                    "statusCode": "confirmed",
                    "statusDescription": "From NHL API matchup",
                    "lastUpdated": now,
                }

    # If no goalie found, return unconfirmed status
    return {
        "team": team_abbrev,
        "playerId": None,
        "goalieName": None,
        "confirmedStart": False,
        "statusCode": "TBD",
        "statusDescription": "Not yet announced",
        "lastUpdated": now,
    }


def build_payload(date: str, timeout: float) -> dict[str, Any]:
    """Build the starting goalies payload."""
    games = fetch_schedule(date, timeout)
    now = datetime.utcnow().isoformat() + "Z"

    payload = {
        "generatedAt": now,
        "source": "NHL API",
        "date": date,
        "teams": {},
        "games": [],
    }

    for game in games:
        game_id = game["gameId"]
        game_state = game["gameState"]

        # Only process future or pre-game states
        if game_state not in ["FUT", "PRE"]:
            continue

        print(f"  Fetching game {game_id}: {game['awayTeamAbbrev']} @ {game['homeTeamAbbrev']}...")

        game_details = fetch_game_details(game_id, timeout)

        home_goalie = extract_goalie_info(game_details, "home") if game_details else None
        away_goalie = extract_goalie_info(game_details, "away") if game_details else None

        # Default goalie info if not found
        if not home_goalie:
            home_goalie = {
                "team": game["homeTeamAbbrev"],
                "confirmedStart": False,
                "statusCode": "TBD",
                "statusDescription": "Not announced",
                "lastUpdated": now,
            }
        if not away_goalie:
            away_goalie = {
                "team": game["awayTeamAbbrev"],
                "confirmedStart": False,
                "statusCode": "TBD",
                "statusDescription": "Not announced",
                "lastUpdated": now,
            }

        # Add to teams dict
        if home_goalie and home_goalie.get("team"):
            payload["teams"][home_goalie["team"]] = home_goalie
        if away_goalie and away_goalie.get("team"):
            payload["teams"][away_goalie["team"]] = away_goalie

        # Add game entry
        payload["games"].append({
            "gameId": str(game_id),
            "gameDate": game["gameDate"],
            "startTimeUTC": game["startTimeUTC"],
            "homeTeam": game["homeTeamAbbrev"],
            "awayTeam": game["awayTeamAbbrev"],
            "homeGoalie": home_goalie,
            "awayGoalie": away_goalie,
        })

    return payload


def main() -> None:
    args = parse_args()

    date = args.date or datetime.now().strftime("%Y-%m-%d")
    print(f"🥅 Fetching NHL starting goalies for {date}...")

    payload = build_payload(date, args.timeout)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2))

    teams_count = len(payload["teams"])
    games_count = len(payload["games"])
    confirmed = sum(1 for t in payload["teams"].values() if t.get("confirmedStart"))

    print(f"✅ Wrote {teams_count} goalies ({confirmed} confirmed) across {games_count} games → {args.output}")


if __name__ == "__main__":
    main()
