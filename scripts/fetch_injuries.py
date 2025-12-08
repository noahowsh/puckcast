#!/usr/bin/env python3
"""Fetch NHL injury data from DailyFaceoff and ESPN.

This script scrapes DailyFaceoff's team line combination pages which include
comprehensive injury data for each team. Falls back to ESPN if needed.

DailyFaceoff provides more complete IR data than ESPN alone.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import requests
from bs4 import BeautifulSoup

ESPN_INJURIES_URL = "https://www.espn.com/nhl/injuries"
DAILYFACEOFF_BASE_URL = "https://www.dailyfaceoff.com/teams"
OUTPUT_PATH = Path(__file__).resolve().parents[1] / "web" / "src" / "data" / "injuries.json"

# DailyFaceoff team slugs
TEAM_SLUGS = {
    "ANA": "anaheim-ducks",
    "BOS": "boston-bruins",
    "BUF": "buffalo-sabres",
    "CGY": "calgary-flames",
    "CAR": "carolina-hurricanes",
    "CHI": "chicago-blackhawks",
    "COL": "colorado-avalanche",
    "CBJ": "columbus-blue-jackets",
    "DAL": "dallas-stars",
    "DET": "detroit-red-wings",
    "EDM": "edmonton-oilers",
    "FLA": "florida-panthers",
    "LAK": "los-angeles-kings",
    "MIN": "minnesota-wild",
    "MTL": "montreal-canadiens",
    "NSH": "nashville-predators",
    "NJD": "new-jersey-devils",
    "NYI": "new-york-islanders",
    "NYR": "new-york-rangers",
    "OTT": "ottawa-senators",
    "PHI": "philadelphia-flyers",
    "PIT": "pittsburgh-penguins",
    "SJS": "san-jose-sharks",
    "SEA": "seattle-kraken",
    "STL": "st-louis-blues",
    "TBL": "tampa-bay-lightning",
    "TOR": "toronto-maple-leafs",
    "UTA": "utah-hockey-club",
    "VAN": "vancouver-canucks",
    "VGK": "vegas-golden-knights",
    "WSH": "washington-capitals",
    "WPG": "winnipeg-jets",
}

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
    """Parse injury status text into status code and isOut flag.

    Returns (status, isOut) where:
    - isOut=True means definitely not playing (IR, OUT, suspended)
    - isOut=False means might play (DTD, GTD, questionable, probable)
    """
    lower = status_text.lower().strip()

    # Day-to-day / Game-time decision - uncertain, might play
    if "day-to-day" in lower or "dtd" in lower or "d2d" in lower:
        return "DTD", False
    if "gtd" in lower or "game time" in lower or "game-time" in lower:
        return "GTD", False
    if "questionable" in lower:
        return "questionable", False
    if "probable" in lower:
        return "probable", False

    # Definitely out
    if "out" in lower and "day-to-day" not in lower:
        return "OUT", True
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
    if "inj" in lower:
        return "INJ", True

    # Default: if they're listed, assume they're out
    return "OUT", True


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


def scrape_dailyfaceoff_team(team_abbrev: str, slug: str, timeout: float) -> list[dict[str, Any]]:
    """Scrape injuries for a single team from DailyFaceoff."""
    url = f"{DAILYFACEOFF_BASE_URL}/{slug}/line-combinations/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Connection": "keep-alive",
    }

    try:
        response = requests.get(url, headers=headers, timeout=timeout)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"  ⚠️  Failed to fetch {team_abbrev}: {e}")
        return []

    soup = BeautifulSoup(response.text, "html.parser")
    injuries = []
    now = datetime.utcnow().isoformat() + "Z"

    # DailyFaceoff structure: Look for injury cards/sections
    # They have player cards with injury status badges (IR, DTD, OUT)

    # Method 1: Look for injury section
    injury_section = soup.find("section", class_=re.compile(r"injur", re.I))
    if not injury_section:
        # Try finding by heading
        injury_heading = soup.find(string=re.compile(r"injur", re.I))
        if injury_heading:
            injury_section = injury_heading.find_parent("section") or injury_heading.find_parent("div")

    # Method 2: Look for player cards with injury status anywhere on page
    # DailyFaceoff uses status badges like "IR", "DTD", "OUT", "GTD" (Game Time Decision)
    status_badges = soup.find_all(string=re.compile(r"^\s*(IR|DTD|D2D|OUT|IR-LT|IR-NR|LTIR|GTD|INJURED|INJ)\s*$", re.I))

    for badge in status_badges:
        # Find the parent player card
        player_card = badge.find_parent(class_=re.compile(r"player|card", re.I))
        if not player_card:
            # Try going up a few levels
            parent = badge.parent
            for _ in range(5):
                if parent is None:
                    break
                if parent.name in ("a", "div", "li") and parent.get("href") or parent.find("a"):
                    player_card = parent
                    break
                parent = parent.parent

        if not player_card:
            continue

        # Extract player name
        player_name = None
        # Look for player name in links or specific elements
        name_link = player_card.find("a", href=re.compile(r"/players/"))
        if name_link:
            player_name = name_link.get_text(strip=True)
        else:
            # Try finding any text that looks like a name
            text_elements = player_card.find_all(text=True)
            for text in text_elements:
                text = text.strip()
                # Skip status badges and empty text
                if text and text.upper() not in ("IR", "DTD", "OUT", "IR-LT", "IR-NR", ""):
                    # Check if it looks like a name (has space, reasonable length)
                    if " " in text and 5 < len(text) < 50:
                        player_name = text
                        break

        if not player_name:
            continue

        # Get status
        status_text = badge.strip().upper()
        status, is_out = parse_status(status_text)

        # Try to determine position from context
        position = "L"  # Default to forward
        pos_match = player_card.find(string=re.compile(r"^\s*(C|LW|RW|D|G|F|W)\s*$", re.I))
        if pos_match:
            position = normalize_position(pos_match.strip())

        # Look for injury description in nearby text or tooltips
        injury_desc = ""
        tooltip = player_card.get("title") or player_card.get("data-tooltip")
        if tooltip:
            injury_desc = tooltip

        injury = {
            "playerId": generate_player_id(player_name, team_abbrev),
            "playerName": player_name,
            "teamAbbrev": team_abbrev,
            "position": position,
            "status": status,
            "injuryType": parse_injury_type(injury_desc or status_text),
            "injuryDescription": injury_desc or status_text,
            "dateInjured": None,
            "expectedReturn": None,
            "lastUpdated": now,
            "isOut": is_out,
        }
        injuries.append(injury)

    # Method 3: Parse the full page for any player with injury status
    # Look for elements containing both a player name link and status badge
    all_player_links = soup.find_all("a", href=re.compile(r"/players/"))
    for link in all_player_links:
        player_name = link.get_text(strip=True)
        if not player_name or len(player_name) < 3:
            continue

        # Check nearby elements for status
        parent = link.parent
        for _ in range(3):
            if parent is None:
                break
            status_elem = parent.find(string=re.compile(r"^\s*(IR|DTD|D2D|OUT|IR-LT|IR-NR|LTIR|GTD|INJURED|INJ)\s*$", re.I))
            if status_elem:
                status_text = status_elem.strip().upper()
                status, is_out = parse_status(status_text)

                # Check if we already have this player
                if any(i["playerName"] == player_name for i in injuries):
                    break

                # Try to get position
                position = "L"
                pos_elem = parent.find(string=re.compile(r"^\s*(C|LW|RW|D|G)\s*$", re.I))
                if pos_elem:
                    position = normalize_position(pos_elem.strip())

                injury = {
                    "playerId": generate_player_id(player_name, team_abbrev),
                    "playerName": player_name,
                    "teamAbbrev": team_abbrev,
                    "position": position,
                    "status": status,
                    "injuryType": parse_injury_type(status_text),
                    "injuryDescription": status_text,
                    "dateInjured": None,
                    "expectedReturn": None,
                    "lastUpdated": now,
                    "isOut": is_out,
                }
                injuries.append(injury)
                break
            parent = parent.parent

    return injuries


def scrape_dailyfaceoff_all(timeout: float) -> dict[str, Any]:
    """Scrape injuries from DailyFaceoff for all teams."""
    teams: dict[str, Any] = {}
    now = datetime.utcnow().isoformat() + "Z"

    print("📋 Scraping DailyFaceoff for all teams...")

    for team_abbrev, slug in TEAM_SLUGS.items():
        print(f"  Fetching {team_abbrev}...")
        injuries = scrape_dailyfaceoff_team(team_abbrev, slug, timeout)

        # Get team name from slug
        team_name = slug.replace("-", " ").title()

        forwards_out = sum(1 for i in injuries if i["isOut"] and is_forward(i["position"]))
        defensemen_out = sum(1 for i in injuries if i["isOut"] and i["position"] == "D")
        goalies_out = sum(1 for i in injuries if i["isOut"] and i["position"] == "G")

        teams[team_abbrev] = {
            "teamAbbrev": team_abbrev,
            "teamName": team_name,
            "injuries": injuries,
            "totalOut": sum(1 for i in injuries if i["isOut"]),
            "forwardsOut": forwards_out,
            "defensemenOut": defensemen_out,
            "goaliesOut": goalies_out,
            "impactRating": 0,  # Will calculate later
            "lastUpdated": now,
        }

        # Be polite - don't hammer the server
        time.sleep(0.5)

    return teams


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


def merge_injury_data(primary: dict[str, Any], secondary: dict[str, Any]) -> dict[str, Any]:
    """Merge injury data from two sources, preferring primary but adding unique entries from secondary."""
    merged = {}
    now = datetime.utcnow().isoformat() + "Z"

    all_abbrevs = set(primary.keys()) | set(secondary.keys())

    for abbrev in all_abbrevs:
        primary_team = primary.get(abbrev, {})
        secondary_team = secondary.get(abbrev, {})

        # Start with primary injuries
        injuries = list(primary_team.get("injuries", []))
        existing_names = {i["playerName"].lower() for i in injuries}

        # Add unique injuries from secondary source
        for injury in secondary_team.get("injuries", []):
            if injury["playerName"].lower() not in existing_names:
                injuries.append(injury)
                existing_names.add(injury["playerName"].lower())

        # Recalculate stats
        forwards_out = sum(1 for i in injuries if i["isOut"] and is_forward(i["position"]))
        defensemen_out = sum(1 for i in injuries if i["isOut"] and i["position"] == "D")
        goalies_out = sum(1 for i in injuries if i["isOut"] and i["position"] == "G")
        total_out = sum(1 for i in injuries if i["isOut"])

        # Calculate impact
        impact = 0
        for inj in injuries:
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

        team_name = primary_team.get("teamName") or secondary_team.get("teamName") or abbrev

        merged[abbrev] = {
            "teamAbbrev": abbrev,
            "teamName": team_name,
            "injuries": injuries,
            "totalOut": total_out,
            "forwardsOut": forwards_out,
            "defensemenOut": defensemen_out,
            "goaliesOut": goalies_out,
            "impactRating": min(100, impact),
            "lastUpdated": now,
        }

    return merged


def build_report(teams: dict[str, Any], source: str = "ESPN") -> dict[str, Any]:
    """Build the final injury report."""
    now = datetime.utcnow().isoformat() + "Z"
    total_injuries = sum(len(t.get("injuries", [])) for t in teams.values())

    return {
        "updatedAt": now,
        "source": source,
        "teams": teams,
        "totalInjuries": total_injuries,
        "recentChanges": [],
    }


def main() -> None:
    args = parse_args()

    print(f"🏒 Fetching NHL injuries...")

    # Try DailyFaceoff first (more complete data)
    df_teams = {}
    try:
        df_teams = scrape_dailyfaceoff_all(args.timeout)
        df_count = sum(len(t.get("injuries", [])) for t in df_teams.values())
        print(f"  ✅ DailyFaceoff: {df_count} injuries found")
    except Exception as e:
        print(f"  ⚠️  DailyFaceoff scraping failed: {e}")

    # Also get ESPN data (has return dates)
    print("\n📋 Scraping ESPN for additional data...")
    espn_teams = scrape_espn_injuries(args.timeout)
    espn_count = sum(len(t.get("injuries", [])) for t in espn_teams.values())
    print(f"  ✅ ESPN: {espn_count} injuries found")

    # Merge the data, preferring DailyFaceoff but adding ESPN's return dates
    if df_teams:
        # Use DailyFaceoff as primary, ESPN as secondary
        teams = merge_injury_data(df_teams, espn_teams)
        source = "DailyFaceoff + ESPN"
    else:
        teams = espn_teams
        source = "ESPN"

    if not teams:
        print("⚠️  No injury data scraped from any source.")
        print("    Generating empty template for all teams...")

    teams = ensure_all_teams(teams)
    report = build_report(teams, source)

    # Write output
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2))

    injury_count = report["totalInjuries"]
    teams_with_injuries = sum(1 for t in teams.values() if t.get("injuries"))

    print(f"✅ Wrote {injury_count} injuries across {teams_with_injuries} teams → {args.output}")


if __name__ == "__main__":
    main()
