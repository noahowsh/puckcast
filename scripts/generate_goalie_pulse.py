#!/usr/bin/env python3
"""
Generate goaliePulse.json with goalie performance trends and insights.

This script fetches goalie stats from the NHL API and generates a JSON file
with rolling performance metrics, trends, and insights for the web frontend.
"""

from __future__ import annotations

import argparse
import json
import ssl
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

import sys

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from nhl_prediction.nhl_api import fetch_schedule  # noqa: E402

OUTPUT_PATH = REPO_ROOT / "web" / "src" / "data" / "goaliePulse.json"
SEASON_ID = "20252026"
GOALIE_STATS_URL = "https://api.nhle.com/stats/rest/en/goalie/summary"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate goalie pulse data with performance trends and insights."
    )
    parser.add_argument("--date", required=True, help="Date string (YYYY-MM-DD).")
    parser.add_argument("--season", default=SEASON_ID, help="Season ID (e.g., 20252026).")
    return parser.parse_args()


def fetch_goalie_stats(season_id: str) -> list[dict[str, Any]]:
    """Fetch goalie stats from NHL API for the given season."""
    query = quote_plus(f"seasonId={season_id} and gameTypeId=2")
    url = f"{GOALIE_STATS_URL}?cayenneExp={query}&limit=100"
    req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
    context = ssl._create_unverified_context()

    try:
        with urlopen(req, timeout=30, context=context) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("data", [])
    except Exception as e:
        print(f"⚠️  Failed to fetch goalie stats: {e}")
        return []


def calculate_trend(gaa: float, save_pct: float, games_played: int) -> str:
    """Determine goalie trend based on recent performance."""
    if games_played < 3:
        return "emerging"
    if save_pct >= 0.920 and gaa <= 2.5:
        return "surging"
    elif save_pct >= 0.910 and gaa <= 2.8:
        return "steady"
    elif save_pct >= 0.900:
        return "stable"
    elif save_pct >= 0.890:
        return "cooling"
    else:
        return "struggling"


def generate_strengths(save_pct: float, gaa: float, wins: int) -> list[str]:
    """Generate strength descriptions based on stats."""
    strengths = []
    if save_pct >= 0.920:
        strengths.append("Elite save percentage")
    if gaa <= 2.3:
        strengths.append("Exceptional goals against average")
    if wins >= 10:
        strengths.append("Proven winner")
    if save_pct >= 0.915:
        strengths.append("Strong rebound control")
    if not strengths:
        strengths.append("Solid fundamentals")
    return strengths[:2]


def generate_watchouts(save_pct: float, gaa: float, losses: int) -> list[str]:
    """Generate watchout descriptions based on stats."""
    watchouts = []
    if gaa >= 3.0:
        watchouts.append("High goals against")
    if save_pct < 0.900:
        watchouts.append("Below-average save percentage")
    if losses >= 5:
        watchouts.append("Inconsistent results")
    if not watchouts:
        watchouts.append("Limited recent data")
    return watchouts[:2]


def generate_note(
    goalie_name: str, team: str, trend: str, save_pct: float, gaa: float
) -> str:
    """Generate a descriptive note about the goalie's performance."""
    if trend == "surging":
        return f"{goalie_name} is playing at an elite level with a {save_pct:.3f} save percentage, providing {team} with a strong defensive anchor."
    elif trend == "steady":
        return f"Consistent performance from {goalie_name} with a {gaa:.2f} GAA — reliable starter for {team}."
    elif trend == "cooling":
        return f"{goalie_name} has been giving up more goals recently ({gaa:.2f} GAA) — {team} may need tighter defense."
    elif trend == "struggling":
        return f"{goalie_name} facing challenges with a {save_pct:.3f} save % — {team} looking for improved form."
    else:
        return f"{goalie_name} showing promise with limited sample size — monitor progression closely."


def fetch_next_opponent(team_abbrev: str, target_date: str) -> str | None:
    """Fetch the next opponent for the given team on the target date."""
    try:
        games = fetch_schedule(target_date)
        for game in games:
            home = game.get("homeTeamAbbrev", "").upper()
            away = game.get("awayTeamAbbrev", "").upper()
            if home == team_abbrev.upper():
                return away
            elif away == team_abbrev.upper():
                return home
    except Exception:
        pass
    return None


def estimate_start_likelihood(
    games_played: int, wins: int, save_pct: float, trend: str
) -> float:
    """Estimate the likelihood of starting based on performance."""
    base = 0.6

    # Adjust based on games played (starter vs backup)
    if games_played >= 15:
        base += 0.2
    elif games_played >= 10:
        base += 0.1

    # Adjust based on save percentage
    if save_pct >= 0.920:
        base += 0.15
    elif save_pct >= 0.910:
        base += 0.1
    elif save_pct < 0.890:
        base -= 0.1

    # Adjust based on trend
    if trend == "surging":
        base += 0.1
    elif trend in ["cooling", "struggling"]:
        base -= 0.1

    return min(0.95, max(0.3, base))


def estimate_rest_days(games_played: int) -> int:
    """Estimate rest days (placeholder logic)."""
    # This is a simplification - in production, you'd track actual game dates
    if games_played >= 20:
        return 1
    elif games_played >= 10:
        return 2
    else:
        return 3


def build_goalie_pulse(target_date: str, season_id: str) -> dict[str, Any]:
    """Build the complete goalie pulse payload."""
    stats = fetch_goalie_stats(season_id)

    # Filter to active goalies with significant playing time
    filtered = [g for g in stats if g.get("gamesPlayed", 0) >= 3]

    # Sort by save percentage and limit to top 30
    filtered.sort(key=lambda x: x.get("savePct", 0), reverse=True)
    top_goalies = filtered[:30]

    goalies = []
    for stat in top_goalies:
        team = stat.get("teamAbbrevs", "UNK")
        if isinstance(team, str) and "/" in team:
            # Handle traded goalies - use most recent team
            team = team.split("/")[-1].strip()

        goalie_name = stat.get("goalieFullName", "Unknown")
        games_played = stat.get("gamesPlayed", 0)
        wins = stat.get("wins", 0)
        losses = stat.get("losses", 0)
        gaa = stat.get("goalsAgainstAverage", 3.0)
        save_pct = stat.get("savePct", 0.900)
        goals_saved_above_avg = stat.get("goalsAgainstAverage", 0)  # Approximation

        # Calculate rolling GSA (simplified - use season stats as proxy)
        season_gsa = (save_pct - 0.900) * games_played * 25  # Rough estimate
        rolling_gsa = season_gsa / max(games_played, 1) * 3  # Last 3 games approximation

        trend = calculate_trend(gaa, save_pct, games_played)
        strengths = generate_strengths(save_pct, gaa, wins)
        watchouts = generate_watchouts(save_pct, gaa, losses)
        note = generate_note(goalie_name, team, trend, save_pct, gaa)
        next_opponent = fetch_next_opponent(team, target_date)
        start_likelihood = estimate_start_likelihood(games_played, wins, save_pct, trend)
        rest_days = estimate_rest_days(games_played)

        goalies.append(
            {
                "name": goalie_name,
                "team": team,
                "rollingGsa": round(rolling_gsa, 1),
                "seasonGsa": round(season_gsa, 1),
                "restDays": rest_days,
                "startLikelihood": round(start_likelihood, 2),
                "trend": trend,
                "note": note,
                "strengths": strengths,
                "watchouts": watchouts,
                "nextOpponent": next_opponent,
            }
        )

    return {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "notes": "Goalie performance metrics calculated from NHL Stats API data. GSAx estimates based on save percentage above league average.",
        "goalies": goalies,
    }


def main() -> None:
    args = parse_args()
    payload = build_goalie_pulse(args.date, args.season)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"✅ Generated goalie pulse data → {OUTPUT_PATH}")
    print(f"   Found {len(payload['goalies'])} goalies with significant playing time")


if __name__ == "__main__":
    main()
