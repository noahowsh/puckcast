#!/usr/bin/env python3
"""Fetch day-of starting goalies from RotoWire and NHL API.

This script attempts to fetch starting goalie confirmations from RotoWire
(requires Playwright for JavaScript rendering), falling back to the NHL API.

Usage:
    python fetch_starting_goalies.py [--date YYYY-MM-DD] [--use-rotowire]
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# Try to import Playwright (optional dependency)
try:
    from playwright.sync_api import sync_playwright
    HAS_PLAYWRIGHT = True
except ImportError:
    HAS_PLAYWRIGHT = False

NHL_SCHEDULE_API = "https://api-web.nhle.com/v1/schedule"
NHL_GAME_API = "https://api-web.nhle.com/v1/gamecenter"
ROTOWIRE_URL = "https://www.rotowire.com/hockey/starting-goalies.php"

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "web" / "src" / "data" / "startingGoalies.json"

# Team name normalization for RotoWire parsing
TEAM_NAME_MAP = {
    "anaheim": "ANA", "ducks": "ANA",
    "arizona": "ARI", "coyotes": "ARI",
    "boston": "BOS", "bruins": "BOS",
    "buffalo": "BUF", "sabres": "BUF",
    "calgary": "CGY", "flames": "CGY",
    "carolina": "CAR", "hurricanes": "CAR",
    "chicago": "CHI", "blackhawks": "CHI",
    "colorado": "COL", "avalanche": "COL",
    "columbus": "CBJ", "blue jackets": "CBJ",
    "dallas": "DAL", "stars": "DAL",
    "detroit": "DET", "red wings": "DET",
    "edmonton": "EDM", "oilers": "EDM",
    "florida": "FLA", "panthers": "FLA",
    "los angeles": "LAK", "kings": "LAK",
    "minnesota": "MIN", "wild": "MIN",
    "montreal": "MTL", "canadiens": "MTL",
    "nashville": "NSH", "predators": "NSH",
    "new jersey": "NJD", "devils": "NJD",
    "ny islanders": "NYI", "islanders": "NYI",
    "ny rangers": "NYR", "rangers": "NYR",
    "ottawa": "OTT", "senators": "OTT",
    "philadelphia": "PHI", "flyers": "PHI",
    "pittsburgh": "PIT", "penguins": "PIT",
    "san jose": "SJS", "sharks": "SJS",
    "seattle": "SEA", "kraken": "SEA",
    "st. louis": "STL", "blues": "STL",
    "tampa bay": "TBL", "lightning": "TBL",
    "toronto": "TOR", "maple leafs": "TOR",
    "utah": "UTA", "utah hockey club": "UTA",
    "vancouver": "VAN", "canucks": "VAN",
    "vegas": "VGK", "golden knights": "VGK",
    "washington": "WSH", "capitals": "WSH",
    "winnipeg": "WPG", "jets": "WPG",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch NHL starting goalies.")
    parser.add_argument("--date", help="Date string (YYYY-MM-DD), defaults to today.")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP request timeout (seconds).")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Output file path.")
    parser.add_argument("--use-rotowire", action="store_true", help="Try RotoWire first (requires Playwright).")
    parser.add_argument("--debug", action="store_true", help="Enable debug output.")
    return parser.parse_args()


def normalize_team_name(name: str) -> str | None:
    """Convert team name to standard abbreviation."""
    name_lower = name.lower().strip()
    return TEAM_NAME_MAP.get(name_lower)


def generate_player_id(name: str, team: str) -> int:
    """Generate deterministic player ID from name and team."""
    combined = f"{name}{team}"
    hash_value = 0
    for char in combined:
        hash_value = ((hash_value << 5) - hash_value) + ord(char)
        hash_value = hash_value & 0xFFFFFFFF
    return hash_value


def fetch_rotowire_goalies(debug: bool = False) -> dict[str, dict[str, Any]]:
    """Fetch starting goalies from RotoWire using Playwright."""
    if not HAS_PLAYWRIGHT:
        print("  ⚠️  Playwright not installed. Install with: pip install playwright && playwright install chromium")
        return {}

    print("  Fetching from RotoWire (using Playwright)...")
    goalies = {}
    now = datetime.utcnow().isoformat() + "Z"

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.goto(ROTOWIRE_URL, timeout=30000)

            # Wait for the content to load
            page.wait_for_selector(".lineup-card", timeout=10000)

            # Get all lineup cards (each represents a game)
            cards = page.query_selector_all(".lineup-card")

            for card in cards:
                try:
                    # Get team names
                    teams = card.query_selector_all(".lineup-card__team-name")
                    if len(teams) < 2:
                        continue

                    away_team = normalize_team_name(teams[0].inner_text())
                    home_team = normalize_team_name(teams[1].inner_text())

                    # Get goalie info
                    goalie_elements = card.query_selector_all(".lineup-card__player-link")
                    statuses = card.query_selector_all(".lineup-card__status")

                    for i, (team_abbrev, is_home) in enumerate([(away_team, False), (home_team, True)]):
                        if not team_abbrev or i >= len(goalie_elements):
                            continue

                        goalie_name = goalie_elements[i].inner_text().strip()
                        status_text = statuses[i].inner_text().strip() if i < len(statuses) else ""

                        is_confirmed = "confirmed" in status_text.lower()
                        is_expected = "expected" in status_text.lower()
                        is_likely = "likely" in status_text.lower()

                        if goalie_name and goalie_name.lower() != "tbd":
                            goalies[team_abbrev] = {
                                "team": team_abbrev,
                                "playerId": generate_player_id(goalie_name, team_abbrev),
                                "goalieName": goalie_name,
                                "confirmedStart": is_confirmed,
                                "statusCode": "confirmed" if is_confirmed else "expected" if is_expected else "likely" if is_likely else "probable",
                                "statusDescription": f"From RotoWire: {status_text}" if status_text else "From RotoWire",
                                "lastUpdated": now,
                            }
                            if debug:
                                print(f"    {team_abbrev}: {goalie_name} ({status_text})")
                except Exception as e:
                    if debug:
                        print(f"    Error parsing card: {e}")
                    continue

            browser.close()

    except Exception as e:
        print(f"  ⚠️  RotoWire fetch failed: {e}")
        return {}

    print(f"  ✓ Found {len(goalies)} goalies from RotoWire")
    return goalies


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

    # Method 1: Check matchup data (most reliable for pre-game)
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

    # Method 2: Check for goalies in roster spots
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


def build_payload(date: str, timeout: float, use_rotowire: bool = False, debug: bool = False) -> dict[str, Any]:
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

    # Try RotoWire first if requested
    rotowire_goalies = {}
    if use_rotowire:
        rotowire_goalies = fetch_rotowire_goalies(debug=debug)
        if rotowire_goalies:
            payload["source"] = "RotoWire + NHL API"

    for game in games:
        game_id = game["gameId"]
        game_state = game["gameState"]

        # Only process future or pre-game states
        if game_state not in ["FUT", "PRE"]:
            continue

        print(f"  Fetching game {game_id}: {game['awayTeamAbbrev']} @ {game['homeTeamAbbrev']}...")

        game_details = fetch_game_details(game_id, timeout)

        # Get goalie info from NHL API
        home_goalie = extract_goalie_info(game_details, "home") if game_details else None
        away_goalie = extract_goalie_info(game_details, "away") if game_details else None

        # Override with RotoWire data if available
        home_abbrev = game["homeTeamAbbrev"]
        away_abbrev = game["awayTeamAbbrev"]

        if home_abbrev in rotowire_goalies:
            home_goalie = rotowire_goalies[home_abbrev]
        if away_abbrev in rotowire_goalies:
            away_goalie = rotowire_goalies[away_abbrev]

        # Default goalie info if not found
        if not home_goalie:
            home_goalie = {
                "team": home_abbrev,
                "confirmedStart": False,
                "statusCode": "TBD",
                "statusDescription": "Not announced",
                "lastUpdated": now,
            }
        if not away_goalie:
            away_goalie = {
                "team": away_abbrev,
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
            "homeTeam": home_abbrev,
            "awayTeam": away_abbrev,
            "homeGoalie": home_goalie,
            "awayGoalie": away_goalie,
        })

    return payload


def main() -> None:
    args = parse_args()

    date = args.date or datetime.now().strftime("%Y-%m-%d")
    print(f"🥅 Fetching NHL starting goalies for {date}...")

    if args.use_rotowire:
        if not HAS_PLAYWRIGHT:
            print("⚠️  --use-rotowire requires Playwright. Install with:")
            print("   pip install playwright && playwright install chromium")
        else:
            print("  Using RotoWire as primary source...")

    payload = build_payload(date, args.timeout, use_rotowire=args.use_rotowire, debug=args.debug)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2))

    teams_count = len(payload["teams"])
    games_count = len(payload["games"])
    confirmed = sum(1 for t in payload["teams"].values() if t.get("confirmedStart"))

    print(f"✅ Wrote {teams_count} goalies ({confirmed} confirmed) across {games_count} games → {args.output}")
    print(f"   Source: {payload['source']}")


if __name__ == "__main__":
    main()
