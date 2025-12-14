#!/usr/bin/env python3
"""
Generate powerIndexSnapshot.json with computed rankings and week-over-week deltas.

This script creates a power index based on standings data and computes
movement trends automatically for social media content.

Output: web/src/data/powerIndexSnapshot.json
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "web" / "src" / "data" / "powerIndexSnapshot.json"
STANDINGS_PATH = REPO_ROOT / "web" / "src" / "data" / "currentStandings.json"
PREVIOUS_SNAPSHOT_PATH = OUTPUT_PATH  # We'll read the current file for previous week data


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate power index snapshot with computed deltas."
    )
    parser.add_argument(
        "--preserve-reasons",
        action="store_true",
        help="Preserve existing movement reasons (don't auto-generate)",
    )
    return parser.parse_args()


def load_standings() -> list[dict]:
    """Load current standings data."""
    if not STANDINGS_PATH.exists():
        print(f"  Standings file not found: {STANDINGS_PATH}")
        return []
    try:
        data = json.loads(STANDINGS_PATH.read_text())
        return data.get("teams", [])
    except Exception as e:
        print(f"  Error loading standings: {e}")
        return []


def load_previous_snapshot() -> dict:
    """Load previous power index snapshot for delta calculations."""
    if not PREVIOUS_SNAPSHOT_PATH.exists():
        return {}
    try:
        return json.loads(PREVIOUS_SNAPSHOT_PATH.read_text())
    except Exception:
        return {}


def generate_movement_reason(
    abbrev: str,
    rank: int,
    prev_rank: int,
    rank_delta: int,
    point_pct: float,
    goal_diff: int,
    recent_form: str = "",
) -> str:
    """Generate an automatic movement reason based on performance."""
    team_names = {
        "ANA": "Ducks", "BOS": "Bruins", "BUF": "Sabres", "CGY": "Flames",
        "CAR": "Hurricanes", "CHI": "Blackhawks", "COL": "Avalanche", "CBJ": "Blue Jackets",
        "DAL": "Stars", "DET": "Red Wings", "EDM": "Oilers", "FLA": "Panthers",
        "LAK": "Kings", "MIN": "Wild", "MTL": "Canadiens", "NSH": "Predators",
        "NJD": "Devils", "NYI": "Islanders", "NYR": "Rangers", "OTT": "Senators",
        "PHI": "Flyers", "PIT": "Penguins", "SJS": "Sharks", "SEA": "Kraken",
        "STL": "Blues", "TBL": "Lightning", "TOR": "Maple Leafs", "UTA": "Utah HC",
        "VAN": "Canucks", "VGK": "Golden Knights", "WSH": "Capitals", "WPG": "Jets",
    }

    team = team_names.get(abbrev, abbrev)

    # Top tier teams
    if rank <= 3:
        if rank_delta > 0:
            return f"Rising into elite tier with strong recent play"
        elif rank_delta < 0:
            return f"Slight dip but still among league's best"
        else:
            return f"Holding steady in top 3"

    # Rising teams
    if rank_delta >= 3:
        return f"Surging up {rank_delta} spots with excellent form"
    elif rank_delta >= 1:
        return f"Climbing the standings, building momentum"

    # Falling teams
    if rank_delta <= -3:
        return f"Struggling, dropped {abs(rank_delta)} spots this week"
    elif rank_delta <= -1:
        return f"Slight regression, looking to stabilize"

    # Stable teams
    if goal_diff > 10:
        return f"Solid goal differential (+{goal_diff}) driving results"
    elif goal_diff < -10:
        return f"Goal differential ({goal_diff}) limiting ceiling"
    elif point_pct >= 0.600:
        return f"Playoff pace at {point_pct:.3f} point percentage"
    elif point_pct >= 0.500:
        return f"Hovering around .500, looking for consistency"
    else:
        return f"Below playoff pace, need to turn things around"


def compute_tier(rank: int) -> str:
    """Assign a tier based on rank."""
    if rank <= 5:
        return "elite"
    elif rank <= 10:
        return "contender"
    elif rank <= 16:
        return "playoff"
    elif rank <= 24:
        return "bubble"
    else:
        return "lottery"


def build_power_index(preserve_reasons: bool = False) -> dict:
    """Build the complete power index payload."""
    standings = load_standings()
    previous = load_previous_snapshot()
    prev_rankings = previous.get("previousRankings", {})
    prev_reasons = previous.get("movementReasons", {})

    if not standings:
        print("  No standings data available")
        return previous  # Return existing data if we can't update

    # Sort by points, then wins, then goal differential
    standings.sort(
        key=lambda t: (t.get("points", 0), t.get("wins", 0), t.get("goalDifferential", 0)),
        reverse=True,
    )

    # Build current rankings
    current_rankings = {}
    movement_reasons = {}
    rankings_list = []

    for idx, team in enumerate(standings):
        abbrev = team.get("abbrev", "UNK")
        rank = idx + 1
        points = team.get("points", 0)
        goal_diff = team.get("goalDifferential", 0)
        point_pct = team.get("pointPctg", 0) or (points / (team.get("gamesPlayed", 1) * 2))
        wins = team.get("wins", 0)
        losses = team.get("losses", 0)
        ot = team.get("ot", 0)

        # Get previous rank for delta
        prev_data = prev_rankings.get(abbrev, {})
        prev_rank = prev_data.get("rank", rank)
        rank_delta = prev_rank - rank  # Positive = improved

        prev_points = prev_data.get("points", points)
        points_delta = points - prev_points

        prev_goal_diff = prev_data.get("goalDiff", goal_diff)
        goal_diff_delta = goal_diff - prev_goal_diff

        # Generate or preserve movement reason
        if preserve_reasons and abbrev in prev_reasons:
            reason = prev_reasons[abbrev]
        else:
            reason = generate_movement_reason(
                abbrev, rank, prev_rank, rank_delta, point_pct, goal_diff
            )

        current_rankings[abbrev] = {
            "rank": rank,
            "points": points,
            "goalDiff": goal_diff,
            "pointPct": round(point_pct, 3),
        }

        movement_reasons[abbrev] = reason

        # Build detailed list entry
        tier = compute_tier(rank)
        trend = "up" if rank_delta > 0 else "down" if rank_delta < 0 else "steady"

        rankings_list.append({
            "rank": rank,
            "abbrev": abbrev,
            "team": team.get("team", abbrev),
            "points": points,
            "record": f"{wins}-{losses}-{ot}",
            "goalDiff": goal_diff,
            "pointPct": round(point_pct, 3),
            "previousRank": prev_rank,
            "rankDelta": rank_delta,
            "pointsDelta": points_delta,
            "goalDiffDelta": goal_diff_delta,
            "tier": tier,
            "trend": trend,
            "reason": reason,
        })

    # Compute risers and fallers
    risers = sorted(
        [r for r in rankings_list if r["rankDelta"] > 0],
        key=lambda x: x["rankDelta"],
        reverse=True,
    )[:5]

    fallers = sorted(
        [r for r in rankings_list if r["rankDelta"] < 0],
        key=lambda x: x["rankDelta"],
    )[:5]

    # Date info
    today = datetime.now(timezone.utc)
    next_monday = today + timedelta(days=(7 - today.weekday()))

    return {
        "lastUpdated": today.strftime("%Y-%m-%d"),
        "nextUpdate": next_monday.strftime("%Y-%m-%d"),
        "weekOf": today.strftime("%b %d, %Y"),
        "generatedAt": today.isoformat(),

        # Previous week data (now the new current)
        "previousRankings": current_rankings,

        # Human-readable reasons
        "movementReasons": movement_reasons,

        # Detailed rankings list for social content
        "rankings": rankings_list,

        # Top movers for social content
        "topRisers": [
            {"rank": r["rank"], "abbrev": r["abbrev"], "delta": r["rankDelta"], "reason": r["reason"]}
            for r in risers
        ],
        "topFallers": [
            {"rank": r["rank"], "abbrev": r["abbrev"], "delta": r["rankDelta"], "reason": r["reason"]}
            for r in fallers
        ],

        # Tier breakdowns
        "tiers": {
            "elite": [r["abbrev"] for r in rankings_list if r["tier"] == "elite"],
            "contender": [r["abbrev"] for r in rankings_list if r["tier"] == "contender"],
            "playoff": [r["abbrev"] for r in rankings_list if r["tier"] == "playoff"],
            "bubble": [r["abbrev"] for r in rankings_list if r["tier"] == "bubble"],
            "lottery": [r["abbrev"] for r in rankings_list if r["tier"] == "lottery"],
        },
    }


def main() -> None:
    args = parse_args()

    print("=" * 70)
    print("PUCKCAST POWER INDEX GENERATOR")
    print("=" * 70)

    payload = build_power_index(preserve_reasons=args.preserve_reasons)

    if payload:
        OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT_PATH.write_text(json.dumps(payload, indent=2))

        print(f"\n Wrote power index to {OUTPUT_PATH}")
        print(f"   Teams ranked: {len(payload.get('rankings', []))}")
        print(f"   Top risers: {len(payload.get('topRisers', []))}")
        print(f"   Top fallers: {len(payload.get('topFallers', []))}")
    else:
        print("\n  Failed to generate power index")


if __name__ == "__main__":
    main()
