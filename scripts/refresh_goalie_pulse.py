#!/usr/bin/env python3
"""Build goalie pulse JSON with automated stats."""

from __future__ import annotations

import argparse
import json
import sys
import time
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
from zoneinfo import ZoneInfo
import urllib.parse

import requests

REPO_ROOT = Path(__file__).resolve().parents[1]
OUTPUT_PATH = REPO_ROOT / "web" / "src" / "data" / "goaliePulse.json"
SEASON_START_MONTH = 7  # July transitions
ET_TZ = ZoneInfo("America/New_York")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "puckcast-goalie-refresh/1.0"})

# Adjust path to import existing helpers
sys.path.insert(0, str(REPO_ROOT))
from src.nhl_prediction.nhl_api import fetch_future_games  # type: ignore


@dataclass
class GoalieSummary:
    player_id: int
    name: str
    team: str
    games_played: int
    wins: int
    losses: int
    ot_losses: int
    save_pct: float
    gaa: float
    shots_against: int


@dataclass
class GoalieProfile:
    summary: GoalieSummary
    last_start: Optional[date]
    rest_days: Optional[int]
    last_opponent: Optional[str]
    rolling_save_pct: Optional[float]
    rolling_shots: Optional[int]
    start_likelihood: Optional[float]

    def trend_label(self) -> str:
        if self.rolling_save_pct is None:
            return "steady"
        delta = self.rolling_save_pct - self.summary.save_pct
        if delta >= 0.02:
            return "surging"
        if delta <= -0.02:
            return "fatigue watch"
        return "steady"


def infer_season_id(target_date: date) -> str:
    start_year = target_date.year if target_date.month >= SEASON_START_MONTH else target_date.year - 1
    return f"{start_year}{start_year + 1}"


def fetch_goalie_summary(season_id: str) -> list[GoalieSummary]:
    query = urllib.parse.quote(f"seasonId={season_id} and gameTypeId=2")
    url = f"https://api.nhle.com/stats/rest/en/goalie/summary?isAggregate=false&isGame=false&limit=-1&cayenneExp={query}"
    resp = SESSION.get(url, timeout=30)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    summaries: list[GoalieSummary] = []
    for item in data:
        try:
            summaries.append(
                GoalieSummary(
                    player_id=int(item["playerId"]),
                    name=str(item["goalieFullName"]),
                    team=str(item.get("teamAbbrevs", "UNK")),
                    games_played=int(item.get("gamesPlayed", 0)),
                    wins=int(item.get("wins", 0)),
                    losses=int(item.get("losses", 0)),
                    ot_losses=int(item.get("otLosses", 0) or 0),
                    save_pct=float(item.get("savePct", 0.0) or 0.0),
                    gaa=float(item.get("goalsAgainstAverage", 0.0) or 0.0),
                    shots_against=int(item.get("shotsAgainst", 0) or 0),
                )
            )
        except (TypeError, ValueError):
            continue
    return summaries


def fetch_game_log(player_id: int, season_id: str) -> list[dict[str, Any]]:
    url = f"https://api-web.nhle.com/v1/player/{player_id}/game-log/{season_id}/2"
    resp = SESSION.get(url, timeout=20)
    resp.raise_for_status()
    payload = resp.json()
    log = payload.get("gameLog", [])
    return sorted(log, key=lambda x: x.get("gameDate", ""), reverse=True)


def compute_profile(summary: GoalieSummary, season_id: str, target_date: date) -> GoalieProfile:
    try:
        log = fetch_game_log(summary.player_id, season_id)
    except requests.RequestException:
        log = []
    last_start: Optional[date] = None
    last_opponent: Optional[str] = None
    rolling_save_pct: Optional[float] = None
    rolling_shots: Optional[int] = None
    start_likelihood: Optional[float] = None
    if log:
        team_override = log[0].get("teamAbbrev")
        if team_override:
            summary.team = str(team_override)
        try:
            last_start = datetime.strptime(log[0]["gameDate"], "%Y-%m-%d").date()
        except Exception:
            last_start = None
        last_opponent = log[0].get("opponentAbbrev")
        recent = log[:3]
        shots = sum(int(g.get("shotsAgainst", 0) or 0) for g in recent)
        goals = sum(int(g.get("goalsAgainst", 0) or 0) for g in recent)
        if shots > 0:
            rolling_save_pct = (shots - goals) / shots
            rolling_shots = shots
        recent_starts = log[:5]
        if recent_starts:
            start_likelihood = sum(int(g.get("gamesStarted", 0) or 0) for g in recent_starts) / len(recent_starts)
    rest_days: Optional[int]
    if last_start:
        rest_days = max((target_date - last_start).days, 0)
    else:
        rest_days = None
    return GoalieProfile(
        summary=summary,
        last_start=last_start,
        rest_days=rest_days,
        last_opponent=last_opponent,
        rolling_save_pct=rolling_save_pct,
        rolling_shots=rolling_shots,
        start_likelihood=start_likelihood,
    )


def build_profiles(summaries: Iterable[GoalieSummary], season_id: str, target_date: date) -> dict[int, GoalieProfile]:
    profiles: dict[int, GoalieProfile] = {}
    for summary in summaries:
        profiles[summary.player_id] = compute_profile(summary, season_id, target_date)
        time.sleep(0.1)
    return profiles


def format_start_times(start_time_utc: str) -> tuple[str, str]:
    if not start_time_utc:
        return "", ""
    dt_utc = datetime.fromisoformat(start_time_utc.replace("Z", "+00:00"))
    dt_et = dt_utc.astimezone(ET_TZ)
    display = dt_et.strftime("%I:%M %p ET").lstrip("0")
    return dt_utc.isoformat(), display


def pick_starter(team_abbrev: str, profiles: dict[int, GoalieProfile]) -> Optional[GoalieProfile]:
    options = [p for p in profiles.values() if p.summary.team == team_abbrev]
    if not options:
        return None
    return max(options, key=lambda p: ((p.start_likelihood or 0.0), -(p.rest_days or 999)))


def serialize_goalie(profile: Optional[GoalieProfile]) -> Optional[dict[str, Any]]:
    if profile is None:
        return None
    summary = profile.summary
    record = f"{summary.wins}-{summary.losses}-{summary.ot_losses}" if summary.ot_losses else f"{summary.wins}-{summary.losses}"
    return {
        "playerId": summary.player_id,
        "name": summary.name,
        "team": summary.team,
        "record": record,
        "seasonSavePct": summary.save_pct,
        "seasonGaa": summary.gaa,
        "startLikelihood": profile.start_likelihood,
        "restDays": profile.rest_days,
        "lastStart": profile.last_start.isoformat() if profile.last_start else None,
        "lastOpponent": profile.last_opponent,
        "rollingSavePct": profile.rolling_save_pct,
        "rollingShots": profile.rolling_shots,
    }


def build_tonight_section(games: list[dict[str, Any]], profiles: dict[int, GoalieProfile]) -> dict[str, Any]:
    formatted_games = []
    for game in games:
        start_time_utc, start_time_et = format_start_times(game.get("startTimeUTC", ""))
        formatted_games.append(
            {
                "gameId": str(game.get("gameId")),
                "matchup": f"{game['awayTeamAbbrev']} @ {game['homeTeamAbbrev']}",
                "startTimeEt": start_time_et,
                "startTimeUtc": start_time_utc,
                "home": serialize_goalie(pick_starter(game['homeTeamAbbrev'], profiles)),
                "away": serialize_goalie(pick_starter(game['awayTeamAbbrev'], profiles)),
            }
        )
    return {"games": formatted_games}


def build_heat_check(profiles: dict[int, GoalieProfile]) -> dict[str, list[dict[str, Any]]]:
    qualified = [p for p in profiles.values() if p.summary.games_played >= 4 and p.rolling_save_pct is not None]
    for profile in qualified:
        profile.delta_save_pct = (profile.rolling_save_pct or 0) - profile.summary.save_pct  # type: ignore[attr-defined]
    surging = sorted(qualified, key=lambda p: getattr(p, "delta_save_pct", 0), reverse=True)[:4]
    cooling = sorted(qualified, key=lambda p: getattr(p, "delta_save_pct", 0))[:4]

    def pack(items: list[GoalieProfile]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        for p in items:
            out.append(
                {
                    "name": p.summary.name,
                    "team": p.summary.team,
                    "rollingSavePct": p.rolling_save_pct,
                    "seasonSavePct": p.summary.save_pct,
                    "deltaSavePct": getattr(p, "delta_save_pct", None),
                    "restDays": p.rest_days,
                    "lastOpponent": p.last_opponent,
                }
            )
        return out

    return {"surging": pack(surging), "cooling": pack(cooling)}


def build_rest_watch(profiles: dict[int, GoalieProfile]) -> list[dict[str, Any]]:
    eligible = [p for p in profiles.values() if p.rest_days is not None]
    ranked = sorted(eligible, key=lambda p: (p.rest_days or 0), reverse=True)[:6]
    return [
        {
            "name": p.summary.name,
            "team": p.summary.team,
            "restDays": p.rest_days,
            "lastStart": p.last_start.isoformat() if p.last_start else None,
            "startLikelihood": p.start_likelihood,
        }
        for p in ranked
    ]


def build_season_leaders(summaries: list[GoalieSummary]) -> list[dict[str, Any]]:
    qualified = [s for s in summaries if s.games_played >= 8 and s.shots_against >= 150]
    ranked = sorted(qualified, key=lambda s: s.save_pct, reverse=True)[:4]
    return [
        {
            "name": s.name,
            "team": s.team,
            "savePct": s.save_pct,
            "gaa": s.gaa,
            "games": s.games_played,
            "record": f"{s.wins}-{s.losses}-{s.ot_losses}" if s.ot_losses else f"{s.wins}-{s.losses}",
        }
        for s in ranked
    ]


def build_legacy_cards(games: list[dict[str, Any]], profiles: dict[int, GoalieProfile]) -> list[dict[str, Any]]:
    cards: list[dict[str, Any]] = []
    for game in games:
        for goalie, opponent in ((game.get("away"), game.get("home")), (game.get("home"), game.get("away"))):
            if not goalie:
                continue
            profile = profiles.get(goalie.get("playerId"))
            trend = profile.trend_label() if profile else "steady"
            opponent_team = opponent["team"] if opponent else "TBD"
            note = f"Facing {opponent_team} · rest {goalie.get('restDays', '—')}d"
            cards.append(
                {
                    "name": goalie["name"],
                    "team": goalie["team"],
                    "rollingGsa": round(((profile.rolling_save_pct if profile and profile.rolling_save_pct is not None else goalie.get("seasonSavePct", 0)) or 0) * 10, 2),
                    "seasonGsa": round(goalie.get("seasonSavePct", 0) * 10, 2),
                    "restDays": goalie.get("restDays", 0) or 0,
                    "startLikelihood": goalie.get("startLikelihood") or 0,
                    "trend": trend,
                    "note": note,
                    "strengths": [f"Record {goalie.get('record', '—')}", f"Rolling SV% {fmt_pct(goalie.get('rollingSavePct'))}"],
                    "watchouts": [f"Season GAA {goalie.get('seasonGaa', 0):.2f}"],
                    "nextOpponent": opponent_team,
                }
            )
    cards.sort(key=lambda card: card["startLikelihood"], reverse=True)
    return cards[:10]


def fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"{value * 100:.1f}%"


def main() -> None:
    parser = argparse.ArgumentParser(description="Refresh goalie pulse data.")
    parser.add_argument("--date", help="Target date YYYY-MM-DD (default: today)")
    args = parser.parse_args()
    target_date = date.fromisoformat(args.date) if args.date else datetime.now(ET_TZ).date()
    season_id = infer_season_id(target_date)

    summaries = fetch_goalie_summary(season_id)
    profiles = build_profiles(summaries, season_id, target_date)
    games = fetch_future_games(target_date.strftime("%Y-%m-%d"))
    tonight_section = build_tonight_section(games, profiles)

    payload = {
        "updatedAt": datetime.now(timezone.utc).isoformat(),
        "targetDate": target_date.isoformat(),
        "notes": f"Auto-generated {target_date.strftime('%B %d')} using NHL Stats feeds.",
        "tonight": tonight_section,
        "heatCheck": build_heat_check(profiles),
        "restWatch": build_rest_watch(profiles),
        "seasonLeaders": build_season_leaders(summaries),
        "goalies": build_legacy_cards(tonight_section["games"], profiles),
    }

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2))
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
