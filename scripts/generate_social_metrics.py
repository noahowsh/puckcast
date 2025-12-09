#!/usr/bin/env python3
"""
Generate socialMetrics.json with comprehensive team-level stats for Instagram content.

This script fetches and computes all metrics needed for social media graphics:
- Team strength metrics (xG, PDO, luck scores)
- Rolling form data
- Week-over-week trend deltas
- Ranking data for leaderboards

Output: web/src/data/socialMetrics.json
"""

from __future__ import annotations

import argparse
import json
import ssl
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "web" / "src" / "data" / "socialMetrics.json"
STANDINGS_PATH = REPO_ROOT / "web" / "src" / "data" / "currentStandings.json"
POWER_INDEX_PATH = REPO_ROOT / "web" / "src" / "data" / "powerIndexSnapshot.json"
GOALIE_PULSE_PATH = REPO_ROOT / "web" / "src" / "data" / "goaliePulse.json"

SEASON_ID = "20252026"
TEAM_STATS_URL = "https://api.nhle.com/stats/rest/en/team/summary"
TEAM_REALTIME_URL = "https://api.nhle.com/stats/rest/en/team/realtime"
TEAM_FACEOFF_URL = "https://api.nhle.com/stats/rest/en/team/faceoffpercentages"
TEAM_PENALTY_URL = "https://api.nhle.com/stats/rest/en/team/penaltykilltime"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate comprehensive social metrics for Instagram content."
    )
    parser.add_argument("--season", default=SEASON_ID, help="Season ID (e.g., 20252026).")
    return parser.parse_args()


def fetch_api_data(url: str, season_id: str) -> list[dict[str, Any]]:
    """Fetch data from NHL Stats API."""
    query = quote_plus(f"seasonId={season_id}")
    full_url = f"{url}?cayenneExp={query}"
    req = Request(full_url, headers={"User-Agent": "Mozilla/5.0"})
    context = ssl._create_unverified_context()

    try:
        with urlopen(req, timeout=30, context=context) as response:
            payload = json.loads(response.read().decode("utf-8"))
            return payload.get("data", [])
    except Exception as e:
        print(f"  Failed to fetch from {url}: {e}")
        return []


def load_standings() -> dict[str, dict]:
    """Load current standings data."""
    if not STANDINGS_PATH.exists():
        return {}
    try:
        data = json.loads(STANDINGS_PATH.read_text())
        return {t["abbrev"]: t for t in data.get("teams", [])}
    except Exception:
        return {}


def load_power_index() -> dict[str, dict]:
    """Load power index snapshot."""
    if not POWER_INDEX_PATH.exists():
        return {}
    try:
        data = json.loads(POWER_INDEX_PATH.read_text())
        return data.get("previousRankings", {})
    except Exception:
        return {}


def load_goalie_pulse() -> list[dict]:
    """Load goalie pulse data."""
    if not GOALIE_PULSE_PATH.exists():
        return []
    try:
        data = json.loads(GOALIE_PULSE_PATH.read_text())
        return data.get("goalies", [])
    except Exception:
        return []


def calculate_pdo(shooting_pct: float, save_pct: float) -> float:
    """Calculate PDO (shooting% + save%)."""
    return shooting_pct + save_pct


def calculate_luck_score(
    goals_for_per_game: float,
    goals_against_per_game: float,
    shots_for_per_game: float,
    shots_against_per_game: float,
) -> dict:
    """
    Calculate luck-adjusted metrics.

    Returns:
        - shooting_pct: Actual shooting percentage
        - expected_shooting_pct: League average ~9%
        - luck_goals_for: Goals above/below expected
        - save_pct: Calculated save percentage
        - expected_save_pct: League average ~90.5%
        - luck_goals_against: Goals against above/below expected
        - total_luck_score: Combined luck metric (positive = lucky)
    """
    LEAGUE_AVG_SHOOTING_PCT = 0.09  # ~9%
    LEAGUE_AVG_SAVE_PCT = 0.905  # ~90.5%

    # Calculate actual shooting percentage
    shooting_pct = (goals_for_per_game / shots_for_per_game) if shots_for_per_game > 0 else 0.09

    # Calculate actual save percentage
    goals_against = goals_against_per_game
    shots_against = shots_against_per_game
    save_pct = 1 - (goals_against / shots_against) if shots_against > 0 else 0.905

    # Expected goals based on league average percentages
    expected_goals_for = shots_for_per_game * LEAGUE_AVG_SHOOTING_PCT
    expected_goals_against = shots_against_per_game * (1 - LEAGUE_AVG_SAVE_PCT)

    # Luck calculations (per game)
    luck_goals_for = goals_for_per_game - expected_goals_for  # Positive = scoring above expected
    luck_goals_against = expected_goals_against - goals_against_per_game  # Positive = allowing fewer than expected

    # Total luck score (positive = team is lucky/overperforming)
    total_luck_score = luck_goals_for + luck_goals_against

    return {
        "shootingPct": round(shooting_pct * 100, 2),
        "savePct": round(save_pct * 100, 2),
        "pdo": round((shooting_pct + save_pct) * 100, 1),
        "expectedGoalsFor": round(expected_goals_for, 2),
        "expectedGoalsAgainst": round(expected_goals_against, 2),
        "luckGoalsFor": round(luck_goals_for, 2),
        "luckGoalsAgainst": round(luck_goals_against, 2),
        "totalLuckScore": round(total_luck_score, 2),
    }


def compute_trend_description(delta: float, metric_name: str) -> str:
    """Generate a human-readable trend description."""
    if abs(delta) < 0.5:
        return f"{metric_name} stable"
    elif delta > 2:
        return f"{metric_name} surging"
    elif delta > 0.5:
        return f"{metric_name} rising"
    elif delta < -2:
        return f"{metric_name} plummeting"
    else:
        return f"{metric_name} declining"


def build_team_metrics(season_id: str) -> list[dict]:
    """Build comprehensive team metrics from all sources."""
    print("Fetching team summary stats...")
    summary_data = fetch_api_data(TEAM_STATS_URL, season_id)

    print("Fetching realtime stats...")
    realtime_data = fetch_api_data(TEAM_REALTIME_URL, season_id)

    print("Fetching faceoff stats...")
    faceoff_data = fetch_api_data(TEAM_FACEOFF_URL, season_id)

    # Index by team ID for joining
    realtime_by_id = {r.get("teamId"): r for r in realtime_data}
    faceoff_by_id = {f.get("teamId"): f for f in faceoff_data}

    # Load existing data for deltas
    standings = load_standings()
    power_index = load_power_index()

    teams = []
    for item in summary_data:
        team_id = item.get("teamId")
        team_name = item.get("teamFullName", "Unknown")

        # Extract abbreviation from team name or use lookup
        abbrev = team_name[:3].upper()
        for std_team in standings.values():
            if std_team.get("team") == team_name:
                abbrev = std_team.get("abbrev", abbrev)
                break

        # Core stats
        games_played = item.get("gamesPlayed", 0)
        wins = item.get("wins", 0)
        losses = item.get("losses", 0)
        ot_losses = item.get("otLosses", 0)
        points = item.get("points", 0)

        goals_for = item.get("goalsFor", 0)
        goals_against = item.get("goalsAgainst", 0)
        goals_for_pg = item.get("goalsForPerGame", 0)
        goals_against_pg = item.get("goalsAgainstPerGame", 0)

        shots_for_pg = item.get("shotsForPerGame", 0)
        shots_against_pg = item.get("shotsAgainstPerGame", 0)

        pp_pct = item.get("powerPlayPct", 0) or 0
        pk_pct = item.get("penaltyKillPct", 0) or 0

        # Faceoffs
        faceoff_pct = item.get("faceoffWinPct", 50.0) or 50.0

        # Get realtime data (hits, blocks, etc.)
        realtime = realtime_by_id.get(team_id, {})
        hits_pg = realtime.get("hitsPerGame", 0)
        blocked_pg = realtime.get("blockedShotsPerGame", 0)
        takeaways = realtime.get("takeaways", 0)
        giveaways = realtime.get("giveaways", 0)

        # Calculate derived metrics
        goal_diff = goals_for - goals_against
        goal_diff_pg = goals_for_pg - goals_against_pg
        point_pct = (points / (games_played * 2)) if games_played > 0 else 0

        # Luck and PDO calculations
        luck_metrics = calculate_luck_score(
            goals_for_pg, goals_against_pg, shots_for_pg, shots_against_pg
        )

        # Shot differential
        shot_diff_pg = shots_for_pg - shots_against_pg

        # Special teams edge
        special_teams_edge = pp_pct - (100 - pk_pct) if pp_pct and pk_pct else 0

        # Possession proxy (shots for / total shots)
        total_shots = shots_for_pg + shots_against_pg
        shot_share = (shots_for_pg / total_shots * 100) if total_shots > 0 else 50.0

        # Get power index ranking and delta
        pi_data = power_index.get(abbrev, {})
        power_rank = pi_data.get("rank", 16)

        # Build team entry
        team_entry = {
            "teamId": team_id,
            "team": team_name,
            "abbrev": abbrev,

            # Record
            "gamesPlayed": games_played,
            "wins": wins,
            "losses": losses,
            "otLosses": ot_losses,
            "points": points,
            "pointPct": round(point_pct, 3),

            # Goals
            "goalsFor": goals_for,
            "goalsAgainst": goals_against,
            "goalDifferential": goal_diff,
            "goalsForPerGame": round(goals_for_pg, 2),
            "goalsAgainstPerGame": round(goals_against_pg, 2),
            "goalDiffPerGame": round(goal_diff_pg, 2),

            # Shots
            "shotsForPerGame": round(shots_for_pg, 1),
            "shotsAgainstPerGame": round(shots_against_pg, 1),
            "shotDiffPerGame": round(shot_diff_pg, 1),
            "shotShare": round(shot_share, 1),

            # Special Teams
            "powerPlayPct": round(pp_pct, 1),
            "penaltyKillPct": round(pk_pct, 1),
            "specialTeamsEdge": round(special_teams_edge, 1),

            # Faceoffs
            "faceoffPct": round(faceoff_pct, 1),

            # Physical play
            "hitsPerGame": round(hits_pg, 1),
            "blockedShotsPerGame": round(blocked_pg, 1),
            "takeaways": takeaways,
            "giveaways": giveaways,
            "turnoverDiff": takeaways - giveaways,

            # Luck & PDO metrics
            "shootingPct": luck_metrics["shootingPct"],
            "savePct": luck_metrics["savePct"],
            "pdo": luck_metrics["pdo"],
            "luckGoalsFor": luck_metrics["luckGoalsFor"],
            "luckGoalsAgainst": luck_metrics["luckGoalsAgainst"],
            "totalLuckScore": luck_metrics["totalLuckScore"],

            # Rankings
            "powerRank": power_rank,
        }

        teams.append(team_entry)

    # Sort by points (descending)
    teams.sort(key=lambda t: (t["points"], t["wins"], t["goalDifferential"]), reverse=True)

    # Add overall rank
    for i, team in enumerate(teams):
        team["standingsRank"] = i + 1

    return teams


def compute_leaderboards(teams: list[dict]) -> dict:
    """Compute various leaderboard rankings."""

    def top_n(metric: str, n: int = 5, reverse: bool = True) -> list[dict]:
        sorted_teams = sorted(teams, key=lambda t: t.get(metric, 0), reverse=reverse)
        return [
            {"rank": i + 1, "team": t["abbrev"], "value": t.get(metric, 0)}
            for i, t in enumerate(sorted_teams[:n])
        ]

    def bottom_n(metric: str, n: int = 5) -> list[dict]:
        return top_n(metric, n, reverse=False)

    return {
        # Best offenses
        "topScoring": top_n("goalsForPerGame"),
        "topShotShare": top_n("shotShare"),
        "topPowerPlay": top_n("powerPlayPct"),

        # Best defenses
        "bestGoalsAgainst": bottom_n("goalsAgainstPerGame"),
        "bestPenaltyKill": top_n("penaltyKillPct"),
        "bestSavePct": top_n("savePct"),

        # Luck leaderboards
        "luckiest": top_n("totalLuckScore"),
        "unluckiest": bottom_n("totalLuckScore"),

        # PDO leaderboards
        "highestPdo": top_n("pdo"),
        "lowestPdo": bottom_n("pdo"),

        # Goal differential
        "bestGoalDiff": top_n("goalDifferential"),
        "worstGoalDiff": bottom_n("goalDifferential"),

        # Faceoffs
        "bestFaceoffs": top_n("faceoffPct"),

        # Physical play
        "mostPhysical": top_n("hitsPerGame"),
    }


def compute_weekly_trends(teams: list[dict], power_index: dict) -> list[dict]:
    """Compute week-over-week trends for each team."""
    trends = []

    for team in teams:
        abbrev = team["abbrev"]
        pi_data = power_index.get(abbrev, {})

        prev_rank = pi_data.get("rank", team["standingsRank"])
        prev_points = pi_data.get("points", team["points"])
        prev_goal_diff = pi_data.get("goalDiff", team["goalDifferential"])
        prev_point_pct = pi_data.get("pointPct", team["pointPct"])

        rank_delta = prev_rank - team["standingsRank"]  # Positive = improved
        points_delta = team["points"] - prev_points
        goal_diff_delta = team["goalDifferential"] - prev_goal_diff
        point_pct_delta = team["pointPct"] - prev_point_pct

        # Determine trend direction
        if rank_delta > 3:
            trend_direction = "surging"
        elif rank_delta > 0:
            trend_direction = "rising"
        elif rank_delta < -3:
            trend_direction = "falling"
        elif rank_delta < 0:
            trend_direction = "slipping"
        else:
            trend_direction = "steady"

        trends.append({
            "abbrev": abbrev,
            "team": team["team"],
            "currentRank": team["standingsRank"],
            "previousRank": prev_rank,
            "rankDelta": rank_delta,
            "pointsDelta": points_delta,
            "goalDiffDelta": goal_diff_delta,
            "pointPctDelta": round(point_pct_delta, 3),
            "trendDirection": trend_direction,
        })

    return trends


def build_social_metrics(season_id: str) -> dict:
    """Build the complete social metrics payload."""
    print("Building social metrics...")

    teams = build_team_metrics(season_id)
    power_index = load_power_index()
    goalies = load_goalie_pulse()

    leaderboards = compute_leaderboards(teams)
    weekly_trends = compute_weekly_trends(teams, power_index)

    # Top risers and fallers
    trends_sorted = sorted(weekly_trends, key=lambda t: t["rankDelta"], reverse=True)
    top_risers = [t for t in trends_sorted[:5] if t["rankDelta"] > 0]
    top_fallers = [t for t in reversed(trends_sorted[-5:]) if t["rankDelta"] < 0]

    # Luck report
    teams_by_luck = sorted(teams, key=lambda t: t["totalLuckScore"], reverse=True)
    luckiest_teams = teams_by_luck[:5]
    unluckiest_teams = teams_by_luck[-5:]

    # Goalie leaderboard (from goalie pulse)
    goalie_leaders = sorted(goalies, key=lambda g: g.get("seasonGsa", 0), reverse=True)[:10]

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "seasonId": season_id,

        # Full team data
        "teams": teams,

        # Leaderboards for graphics
        "leaderboards": leaderboards,

        # Weekly trends
        "weeklyTrends": weekly_trends,
        "topRisers": top_risers,
        "topFallers": top_fallers,

        # Luck report
        "luckReport": {
            "luckiest": [
                {
                    "abbrev": t["abbrev"],
                    "team": t["team"],
                    "luckScore": t["totalLuckScore"],
                    "pdo": t["pdo"],
                }
                for t in luckiest_teams
            ],
            "unluckiest": [
                {
                    "abbrev": t["abbrev"],
                    "team": t["team"],
                    "luckScore": t["totalLuckScore"],
                    "pdo": t["pdo"],
                }
                for t in unluckiest_teams
            ],
        },

        # Goalie leaderboard
        "goalieLeaders": [
            {
                "name": g.get("name"),
                "team": g.get("team"),
                "seasonGsa": g.get("seasonGsa"),
                "rollingGsa": g.get("rollingGsa"),
                "trend": g.get("trend"),
            }
            for g in goalie_leaders
        ],
    }


def main() -> None:
    args = parse_args()

    print("=" * 70)
    print("PUCKCAST SOCIAL METRICS GENERATOR")
    print("=" * 70)

    payload = build_social_metrics(args.season)

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))

    print(f"\n Wrote social metrics to {OUTPUT_PATH}")
    print(f"   Teams: {len(payload['teams'])}")
    print(f"   Leaderboard categories: {len(payload['leaderboards'])}")
    print(f"   Weekly trends: {len(payload['weeklyTrends'])}")
    print(f"   Goalie leaders: {len(payload['goalieLeaders'])}")


if __name__ == "__main__":
    main()
