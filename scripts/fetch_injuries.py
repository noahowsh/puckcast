#!/usr/bin/env python3
"""Fetch NHL injury data from ESPN and write to injuries.json.

This script scrapes ESPN's NHL injuries page and creates a structured
JSON file for use by the web frontend.

Note: Rotowire was considered but requires JavaScript rendering.
ESPN provides reliable HTML that can be scraped directly.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

ESPN_INJURIES_URL = "https://www.espn.com/nhl/injuries"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "web" / "src" / "data" / "injuries.json"

# Team name to abbreviation mapping
TEAM_NAME_TO_ABBREV = {
    "Anaheim Ducks": "ANA",
    "Arizona Coyotes": "ARI",
    "Boston Bruins": "BOS",
    "Buffalo Sabres": "BUF",
    "Calgary Flames": "CGY",
    "Carolina Hurricanes": "CAR",
    "Chicago Blackhawks": "CHI",
    "Colorado Avalanche": "COL",
    "Columbus Blue Jackets": "CBJ",
    "Dallas Stars": "DAL",
    "Detroit Red Wings": "DET",
    "Edmonton Oilers": "EDM",
    "Florida Panthers": "FLA",
    "Los Angeles Kings": "LAK",
    "Minnesota Wild": "MIN",
    "Montreal Canadiens": "MTL",
    "Montréal Canadiens": "MTL",
    "Nashville Predators": "NSH",
    "New Jersey Devils": "NJD",
    "New York Islanders": "NYI",
    "New York Rangers": "NYR",
    "Ottawa Senators": "OTT",
    "Philadelphia Flyers": "PHI",
    "Pittsburgh Penguins": "PIT",
    "San Jose Sharks": "SJS",
    "Seattle Kraken": "SEA",
    "St. Louis Blues": "STL",
    "Tampa Bay Lightning": "TBL",
    "Toronto Maple Leafs": "TOR",
    "Utah Hockey Club": "UTA",
    "Vancouver Canucks": "VAN",
    "Vegas Golden Knights": "VGK",
    "Washington Capitals": "WSH",
    "Winnipeg Jets": "WPG",
}

# All 32 NHL teams
ALL_TEAMS = list(set(TEAM_NAME_TO_ABBREV.values()))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch NHL injuries from ESPN.")
    parser.add_argument("--date", help="Target date (YYYY-MM-DD), used for logging only.")
    parser.add_argument("--timeout", type=float, default=15.0, help="HTTP timeout.")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH, help="Output file path.")
    return parser.parse_args()


def get_team_abbrev(team_name: str) -> str | None:
    """Convert team name to abbreviation."""
    if team_name in TEAM_NAME_TO_ABBREV:
        return TEAM_NAME_TO_ABBREV[team_name]

    # Try partial matching
    team_lower = team_name.lower()
    for name, abbrev in TEAM_NAME_TO_ABBREV.items():
        if name.lower() in team_lower or team_lower in name.lower():
            return abbrev

    return None


def parse_status(status_text: str) -> tuple[str, bool]:
    """Parse injury status text into status code and isOut flag."""
    lower = status_text.lower().strip()

    if "day-to-day" in lower or "dtd" in lower:
        return "day-to-day", False
    if "questionable" in lower:
        return "questionable", False
    if "probable" in lower:
        return "probable", False
    if "out" in lower and "day-to-day" not in lower:
        return "out", True
    if "ir-lt" in lower or "long-term" in lower or "ltir" in lower:
        return "IR-LT", True
    if "ir-nr" in lower:
        return "IR-NR", True
    if "ir" in lower or "injured reserve" in lower:
        return "IR", True
    if "suspended" in lower:
        return "suspended", True
    if "personal" in lower:
        return "personal", True

    # Default: if they're listed, assume they're out
    return "out", True


def parse_injury_type(description: str) -> str:
    """Parse injury description into injury type."""
    lower = description.lower()

    if "upper body" in lower or "upper-body" in lower:
        return "upper-body"
    if "lower body" in lower or "lower-body" in lower:
        return "lower-body"
    if "concussion" in lower:
        return "concussion"
    if "head" in lower:
        return "head"
    if "knee" in lower:
        return "knee"
    if "ankle" in lower:
        return "ankle"
    if "shoulder" in lower:
        return "shoulder"
    if "back" in lower:
        return "back"
    if "hand" in lower:
        return "hand"
    if "wrist" in lower:
        return "wrist"
    if "groin" in lower:
        return "groin"
    if "hip" in lower:
        return "hip"
    if "foot" in lower:
        return "foot"
    if "leg" in lower:
        return "leg"
    if "arm" in lower:
        return "arm"
    if "illness" in lower or "flu" in lower or "sick" in lower:
        return "illness"
    if "undisclosed" in lower:
        return "undisclosed"

    return "other"


def normalize_position(pos: str) -> str:
    """Normalize position code."""
    upper = pos.upper().strip()
    if upper in ("LW", "RW", "W", "F"):
        return "L"  # Left wing as default forward
    if upper in ("C", "L", "R", "D", "G"):
        return upper
    return "L"  # Default to forward


def generate_player_id(name: str, team: str) -> int:
    """Generate deterministic player ID from name and team."""
    combined = f"{name}{team}"
    hash_value = 0
    for char in combined:
        hash_value = ((hash_value << 5) - hash_value) + ord(char)
        hash_value = hash_value & 0xFFFFFFFF  # Keep as 32-bit
    return hash_value


def is_forward(position: str) -> bool:
    """Check if position is a forward position."""
    return position.upper() in ("C", "L", "R", "LW", "RW", "W", "F")


def scrape_espn_injuries(timeout: float) -> dict[str, Any]:
    """Scrape ESPN NHL injuries page."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    try:
        response = requests.get(ESPN_INJURIES_URL, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"❌ Failed to fetch ESPN injuries: {e}")
        return {}

    soup = BeautifulSoup(response.text, "html.parser")
    teams: dict[str, Any] = {}
    now = datetime.utcnow().isoformat() + "Z"

    # ESPN structure: each team has a ResponsiveTable div with:
    # - div.Table__Title containing team name
    # - table with player rows
    # Find all tables and look for their associated team title

    all_tables = soup.find_all("table")

    for table in all_tables:
        # Find the team name from Table__Title sibling
        responsive_table = table.find_parent(class_="ResponsiveTable")
        if not responsive_table:
            continue

        title_div = responsive_table.find(class_="Table__Title")
        if not title_div:
            continue

        team_name = title_div.get_text(strip=True)
        team_abbrev = get_team_abbrev(team_name)

        if not team_abbrev:
            continue

        # Initialize team entry if needed
        if team_abbrev not in teams:
            teams[team_abbrev] = {
                "teamAbbrev": team_abbrev,
                "teamName": team_name,
                "injuries": [],
                "totalOut": 0,
                "forwardsOut": 0,
                "defensemenOut": 0,
                "goaliesOut": 0,
                "impactRating": 0,
                "lastUpdated": now,
            }

        # Parse player rows from this table
        rows = table.find_all("tr")
        for row in rows:
            cells = row.find_all("td")
            if len(cells) < 3:
                continue

            name_cell = cells[0].get_text(strip=True)
            # Skip header rows
            if name_cell.lower() in ("name", "player", ""):
                continue

            pos_text = cells[1].get_text(strip=True) if len(cells) > 1 else ""
            # Column 2 is typically "Est. Return Date"
            return_date = cells[2].get_text(strip=True) if len(cells) > 2 else ""
            # Column 3 is "Status"
            status_text = cells[3].get_text(strip=True) if len(cells) > 3 else ""

            if not name_cell:
                continue

            # Combine return date and status for parsing
            combined_status = f"{status_text} {return_date}".strip()
            status, is_out = parse_status(combined_status)
            position = normalize_position(pos_text)
            injury_type = parse_injury_type(status_text or return_date)

            injury = {
                "playerId": generate_player_id(name_cell, team_abbrev),
                "playerName": name_cell,
                "teamAbbrev": team_abbrev,
                "position": position,
                "status": status,
                "injuryType": injury_type,
                "injuryDescription": status_text or return_date,
                "dateInjured": None,
                "expectedReturn": return_date if return_date and return_date.lower() not in ("out", "day-to-day") else None,
                "lastUpdated": now,
                "isOut": is_out,
            }

            teams[team_abbrev]["injuries"].append(injury)

            if is_out:
                teams[team_abbrev]["totalOut"] += 1
                if is_forward(position):
                    teams[team_abbrev]["forwardsOut"] += 1
                elif position == "D":
                    teams[team_abbrev]["defensemenOut"] += 1
                elif position == "G":
                    teams[team_abbrev]["goaliesOut"] += 1

    # Calculate impact ratings
    for team_data in teams.values():
        impact = 0
        for inj in team_data["injuries"]:
            if not inj["isOut"]:
                continue
            pos = inj["position"]
            if pos == "G":
                impact += 25
            elif pos == "D":
                impact += 15
            else:
                impact += 10

            if inj["status"] == "IR-LT":
                impact += 5
            elif inj["status"] == "IR":
                impact += 3

        team_data["impactRating"] = min(100, impact)

    return teams


def ensure_all_teams(teams: dict[str, Any]) -> dict[str, Any]:
    """Ensure all 32 NHL teams have entries."""
    now = datetime.utcnow().isoformat() + "Z"

    for abbrev in ALL_TEAMS:
        if abbrev not in teams:
            # Find the team name
            team_name = next(
                (name for name, a in TEAM_NAME_TO_ABBREV.items() if a == abbrev),
                abbrev
            )
            teams[abbrev] = {
                "teamAbbrev": abbrev,
                "teamName": team_name,
                "injuries": [],
                "totalOut": 0,
                "forwardsOut": 0,
                "defensemenOut": 0,
                "goaliesOut": 0,
                "impactRating": 0,
                "lastUpdated": now,
            }

    return teams


def build_report(teams: dict[str, Any]) -> dict[str, Any]:
    """Build the final injury report."""
    now = datetime.utcnow().isoformat() + "Z"
    total_injuries = sum(len(t.get("injuries", [])) for t in teams.values())

    return {
        "updatedAt": now,
        "source": "ESPN",
        "teams": teams,
        "totalInjuries": total_injuries,
        "recentChanges": [],
    }


def main() -> None:
    args = parse_args()

    print(f"🏒 Fetching NHL injuries from ESPN...")

    teams = scrape_espn_injuries(args.timeout)

    if not teams:
        print("⚠️  No injury data scraped, ESPN might have changed their page structure.")
        print("    Generating empty template for all teams...")

    teams = ensure_all_teams(teams)
    report = build_report(teams)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))

    injury_count = report["totalInjuries"]
    teams_with_injuries = sum(1 for t in teams.values() if t.get("injuries"))

    print(f"✅ Wrote {injury_count} injuries across {teams_with_injuries} teams → {args.output}")


if __name__ == "__main__":
    main()
