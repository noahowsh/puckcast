#!/usr/bin/env python3
"""Fetch day-of starting goalies from RotoWire and NHL API.

RotoWire provides confirmed/expected starting goalie information via a simple
JSON API endpoint. This script fetches that data and supplements with NHL API
schedule information.

Usage:
    python fetch_starting_goalies.py [--date YYYY-MM-DD]
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

import requests

# RotoWire JSON API endpoint (discovered via page analysis)
ROTOWIRE_API = "https://www.rotowire.com/hockey/tables/projected-goalies.php"

# NHL API endpoints
NHL_SCHEDULE_API = "https://api-web.nhle.com/v1/schedule"
NHL_GAME_API = "https://api-web.nhle.com/v1/gamecenter"

OUTPUT_PATH = Path(__file__).resolve().parents[1] / "web" / "src" / "data" / "startingGoalies.json"

# Team abbreviation normalization (RotoWire uses some non-standard abbreviations)
TEAM_NORMALIZE = {
    "MON": "MTL",  # Montreal
    "TAM": "TBL",  # Tampa Bay
    "LAS": "VGK",  # Vegas
    "SAN": "SJS",  # San Jose
    "NAS": "NSH",  # Nashville
    "ANA": "ANA",
    "ARI": "ARI",
    "BOS": "BOS",
    "BUF": "BUF",
    "CGY": "CGY",
    "CAR": "CAR",
    "CHI": "CHI",
    "COL": "COL",
    "CBJ": "CBJ",
    "DAL": "DAL",
    "DET": "DET",
    "EDM": "EDM",
    "FLA": "FLA",
    "LAK": "LAK",
    "MIN": "MIN",
    "MTL": "MTL",
    "NSH": "NSH",
    "NJD": "NJD",
    "NYI": "NYI",
    "NYR": "NYR",
    "OTT": "OTT",
    "PHI": "PHI",
    "PIT": "PIT",
    "SJS": "SJS",
    "SEA": "SEA",
    "STL": "STL",
    "TBL": "TBL",
    "TOR": "TOR",
    "UTA": "UTA",
    "VAN": "VAN",
    "VGK": "VGK",
    "WSH": "WSH",
    "WPG": "WPG",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch NHL starting goalies from RotoWire.")
    parser.add_argument("--date", help="Date string (YYYY-MM-DD), defaults to today.")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP request timeout (seconds).")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Output file path.")
    parser.add_argument("--debug", action="store_true", help="Enable debug output.")
    return parser.parse_args()


def normalize_team(abbrev: str) -> str:
    """Normalize team abbreviation to standard NHL format."""
    return TEAM_NORMALIZE.get(abbrev.upper(), abbrev.upper())


def fetch_rotowire_goalies(date: str, timeout: float, debug: bool = False) -> dict[str, Any]:
    """Fetch starting goalies from RotoWire JSON API."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "X-Requested-With": "XMLHttpRequest",
        "Referer": "https://www.rotowire.com/hockey/starting-goalies.php",
    }

    url = f"{ROTOWIRE_API}?date={date}"

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        if debug:
            print(f"  RotoWire returned {len(data)} games")

        return data
    except requests.RequestException as e:
        print(f"  ⚠️  RotoWire fetch failed: {e}")
        return []
    except json.JSONDecodeError as e:
        print(f"  ⚠️  RotoWire returned invalid JSON: {e}")
        return []


def fetch_nhl_schedule(date: str, timeout: float) -> list[dict[str, Any]]:
    """Fetch NHL schedule for schedule metadata (game times, IDs)."""
    headers = {
        "User-Agent": "Mozilla/5.0 (compatible; PuckCast/1.0; +https://puckcast.ai)",
        "Accept": "application/json",
    }

    url = f"{NHL_SCHEDULE_API}/{date}"

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
        data = response.json()

        games = []
        for week in data.get("gameWeek", []):
            for game in week.get("games", []):
                games.append({
                    "gameId": str(game["id"]),
                    "gameDate": week["date"],
                    "gameState": game["gameState"],
                    "startTimeUTC": game["startTimeUTC"],
                    "homeTeam": game["homeTeam"]["abbrev"],
                    "awayTeam": game["awayTeam"]["abbrev"],
                })
        return games
    except requests.RequestException as e:
        print(f"  ⚠️  NHL schedule fetch failed: {e}")
        return []


def build_goalie_entry(
    team: str,
    player_name: str | None,
    player_id: str | int | None,
    status: str,
    source: str,
) -> dict[str, Any]:
    """Build a standardized goalie entry."""
    now = datetime.utcnow().isoformat() + "Z"

    is_confirmed = status.lower() == "confirmed"
    is_expected = status.lower() == "expected"
    is_likely = status.lower() == "likely"

    if is_confirmed:
        status_code = "confirmed"
    elif is_expected:
        status_code = "expected"
    elif is_likely:
        status_code = "likely"
    elif player_name:
        status_code = "probable"
    else:
        status_code = "TBD"

    return {
        "team": team,
        "playerId": int(player_id) if player_id else None,
        "goalieName": player_name,
        "confirmedStart": is_confirmed,
        "statusCode": status_code,
        "statusDescription": f"From {source}: {status}" if status else f"From {source}",
        "lastUpdated": now,
    }


def build_payload(date: str, timeout: float, debug: bool = False) -> dict[str, Any]:
    """Build the starting goalies payload from RotoWire and NHL data."""
    now = datetime.utcnow().isoformat() + "Z"

    payload = {
        "generatedAt": now,
        "source": "RotoWire",
        "date": date,
        "teams": {},
        "games": [],
    }

    # Fetch RotoWire data (primary source for goalie confirmations)
    print("  Fetching RotoWire starting goalies...")
    rotowire_games = fetch_rotowire_goalies(date, timeout, debug)

    if not rotowire_games:
        print("  ⚠️  No data from RotoWire, falling back to NHL API only")
        payload["source"] = "NHL API"

    # Fetch NHL schedule for game IDs and times
    print("  Fetching NHL schedule...")
    nhl_games = fetch_nhl_schedule(date, timeout)

    # Create lookup by team matchup
    nhl_game_lookup = {}
    for game in nhl_games:
        key = f"{game['awayTeam']}@{game['homeTeam']}"
        nhl_game_lookup[key] = game

    # Process RotoWire games
    for rw_game in rotowire_games:
        home_team = normalize_team(rw_game.get("hometeam", ""))
        away_team = normalize_team(rw_game.get("visitteam", ""))

        if not home_team or not away_team:
            continue

        # Build goalie entries
        home_goalie = build_goalie_entry(
            team=home_team,
            player_name=rw_game.get("homePlayer"),
            player_id=rw_game.get("homePlayerID"),
            status=rw_game.get("homeStatus", ""),
            source="RotoWire",
        )

        away_goalie = build_goalie_entry(
            team=away_team,
            player_name=rw_game.get("visitPlayer"),
            player_id=rw_game.get("visitPlayerID"),
            status=rw_game.get("visitStatus", ""),
            source="RotoWire",
        )

        # Add to teams dict
        payload["teams"][home_team] = home_goalie
        payload["teams"][away_team] = away_goalie

        # Find matching NHL game for metadata
        matchup_key = f"{away_team}@{home_team}"
        nhl_game = nhl_game_lookup.get(matchup_key, {})

        # Add game entry
        game_entry = {
            "gameId": nhl_game.get("gameId", ""),
            "gameDate": date,
            "startTimeUTC": nhl_game.get("startTimeUTC", ""),
            "startTimeET": rw_game.get("gamedate", ""),
            "homeTeam": home_team,
            "awayTeam": away_team,
            "homeGoalie": home_goalie,
            "awayGoalie": away_goalie,
        }
        payload["games"].append(game_entry)

        if debug:
            home_status = home_goalie["statusCode"]
            away_status = away_goalie["statusCode"]
            print(f"    {away_team} @ {home_team}: {away_goalie['goalieName']} ({away_status}) vs {home_goalie['goalieName']} ({home_status})")

    # Add any NHL games not in RotoWire (rare but possible)
    processed_matchups = {f"{g['awayTeam']}@{g['homeTeam']}" for g in payload["games"]}
    for nhl_game in nhl_games:
        if nhl_game["gameState"] not in ["FUT", "PRE"]:
            continue

        matchup_key = f"{nhl_game['awayTeam']}@{nhl_game['homeTeam']}"
        if matchup_key in processed_matchups:
            continue

        # Game not in RotoWire, create TBD entries
        home_goalie = build_goalie_entry(
            team=nhl_game["homeTeam"],
            player_name=None,
            player_id=None,
            status="TBD",
            source="NHL API",
        )
        away_goalie = build_goalie_entry(
            team=nhl_game["awayTeam"],
            player_name=None,
            player_id=None,
            status="TBD",
            source="NHL API",
        )

        if nhl_game["homeTeam"] not in payload["teams"]:
            payload["teams"][nhl_game["homeTeam"]] = home_goalie
        if nhl_game["awayTeam"] not in payload["teams"]:
            payload["teams"][nhl_game["awayTeam"]] = away_goalie

        payload["games"].append({
            "gameId": nhl_game["gameId"],
            "gameDate": nhl_game["gameDate"],
            "startTimeUTC": nhl_game["startTimeUTC"],
            "homeTeam": nhl_game["homeTeam"],
            "awayTeam": nhl_game["awayTeam"],
            "homeGoalie": home_goalie,
            "awayGoalie": away_goalie,
        })

    return payload


def main() -> None:
    args = parse_args()

    date = args.date or datetime.now().strftime("%Y-%m-%d")
    print(f"🥅 Fetching NHL starting goalies for {date}...")

    payload = build_payload(date, args.timeout, debug=args.debug)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(payload, indent=2))

    teams_count = len(payload["teams"])
    games_count = len(payload["games"])
    confirmed = sum(1 for t in payload["teams"].values() if t.get("confirmedStart"))
    expected = sum(1 for t in payload["teams"].values() if t.get("statusCode") == "expected")

    print(f"✅ Wrote {teams_count} goalies ({confirmed} confirmed, {expected} expected) across {games_count} games")
    print(f"   Source: {payload['source']}")
    print(f"   Output: {args.output}")


if __name__ == "__main__":
    main()
