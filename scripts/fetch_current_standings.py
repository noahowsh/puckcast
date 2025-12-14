#!/usr/bin/env python3
"""
Fetch current NHL standings from the stats REST endpoint and persist them to the web bundle.
"""

from __future__ import annotations

import csv
import json
import ssl
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = ROOT / "web" / "src" / "data" / "currentStandings.json"
TEAM_MAP_PATH = ROOT / "data" / "nhl_teams.csv"
SEASON_ID = "20252026"
STATS_BASE = "https://api.nhle.com/stats/rest/en/team/summary"


def load_team_map() -> dict[int, dict[str, str]]:
  mapping: dict[int, dict[str, str]] = {}
  with TEAM_MAP_PATH.open() as handle:
    reader = csv.DictReader(handle)
    for row in reader:
      try:
        team_id = int(row["teamId"])
      except (ValueError, KeyError):
        continue
      mapping[team_id] = {"abbrev": row.get("triCode", "").strip(), "fullName": row.get("fullName", "").strip()}
  return mapping


def fetch_summary(season_id: str) -> dict:
  query = quote_plus(f"seasonId={season_id}")
  url = f"{STATS_BASE}?cayenneExp={query}"
  req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
  context = ssl._create_unverified_context()
  with urlopen(req, timeout=30, context=context) as response:
    return json.loads(response.read().decode("utf-8"))


def main() -> None:
  team_map = load_team_map()
  payload = fetch_summary(SEASON_ID)
  data = payload.get("data", [])

  simplified = []
  for item in data:
    team_id = int(item.get("teamId"))
    mapping = team_map.get(team_id, {})
    abbrev = mapping.get("abbrev") or (item.get("teamFullName", "")[:3].upper())
    record = {
      "team": item.get("teamFullName"),
      "abbrev": abbrev,
      "wins": item.get("wins"),
      "losses": item.get("losses"),
      "ot": item.get("otLosses"),
      "points": item.get("points"),
      "gamesPlayed": item.get("gamesPlayed"),
      "pointPctg": item.get("pointPct"),
      "goalDifferential": (item.get("goalsFor") or 0) - (item.get("goalsAgainst") or 0),
      "goalsForPerGame": item.get("goalsForPerGame"),
      "goalsAgainstPerGame": item.get("goalsAgainstPerGame"),
      "shotsForPerGame": item.get("shotsForPerGame"),
      "shotsAgainstPerGame": item.get("shotsAgainstPerGame"),
      "powerPlayPct": item.get("powerPlayPct"),
      "penaltyKillPct": item.get("penaltyKillPct"),
      "seasonId": item.get("seasonId"),
    }
    simplified.append(record)

  simplified.sort(key=lambda t: (t["points"], t["wins"], t["goalDifferential"]), reverse=True)
  output = {
    "generatedAt": datetime.now(timezone.utc).isoformat(),
    "seasonId": SEASON_ID,
    "teams": simplified,
  }

  OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
  OUTPUT_PATH.write_text(json.dumps(output, indent=2))
  print(f"Wrote {OUTPUT_PATH} ({len(simplified)} teams)")


if __name__ == "__main__":
  main()
