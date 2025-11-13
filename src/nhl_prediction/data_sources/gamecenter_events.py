"""Utilities to extract structured shot events from Gamecenter play-by-play."""

from __future__ import annotations

import math
from typing import Dict, Iterable, List, Tuple

import pandas as pd

SHOT_EVENT_TYPES = {"shot-on-goal", "goal", "missed-shot"}


def _parse_situation(code: str | None) -> Tuple[int | None, int | None, int | None, int | None]:
    if not code or len(code) < 4:
        return None, None, None, None
    try:
        return int(code[0]), int(code[1]), int(code[2]), int(code[3])
    except ValueError:
        return None, None, None, None


def _calc_distance(x_coord: float | None, y_coord: float | None) -> float | None:
    if x_coord is None or y_coord is None:
        return None
    # NHL rinks: 89 feet from center ice to goal line.
    delta_x = 89 - abs(x_coord)
    delta_y = y_coord
    return float(math.hypot(delta_x, delta_y))


def _calc_angle(x_coord: float | None, y_coord: float | None) -> float | None:
    if x_coord is None or y_coord is None:
        return None
    delta_x = max(1.0, 89 - abs(x_coord))
    return float(math.degrees(math.atan2(abs(y_coord), delta_x)))


def _seconds_elapsed(period: int, clock: str) -> int | None:
    try:
        minutes, seconds = map(int, clock.split(":"))
    except Exception:
        return None
    return (period - 1) * 20 * 60 + minutes * 60 + seconds


def extract_shot_events(pbp: Dict) -> pd.DataFrame:
    """Return a DataFrame of unblocked shot attempts (shots on goal, misses, goals)."""
    plays: List[Dict] = pbp.get("plays", [])
    if not plays:
        return pd.DataFrame()

    home_team_id = pbp["homeTeam"]["id"]
    away_team_id = pbp["awayTeam"]["id"]

    events: List[Dict] = []
    home_score = 0
    away_score = 0

    for play in sorted(plays, key=lambda p: p.get("sortOrder", 0)):
        type_key = play.get("typeDescKey")
        details = play.get("details", {}) or {}

        event_owner = details.get("eventOwnerTeamId")
        if type_key in SHOT_EVENT_TYPES:
            period = play.get("periodDescriptor", {}).get("number", 0)
            clock = play.get("timeInPeriod", "00:00")
            x_coord = details.get("xCoord")
            y_coord = details.get("yCoord")
            home_goalie, home_skaters, away_skaters, away_goalie = _parse_situation(play.get("situationCode"))
            seconds = _seconds_elapsed(period, clock)
            score_diff_before = home_score - away_score

            shooting_team_is_home = event_owner == home_team_id
            shooting_skaters = home_skaters if shooting_team_is_home else away_skaters
            defending_skaters = away_skaters if shooting_team_is_home else home_skaters
            shooting_goalie = home_goalie if shooting_team_is_home else away_goalie

            events.append(
                {
                    "gameId": pbp.get("id"),
                    "season": pbp.get("season"),
                    "eventId": play.get("eventId"),
                    "period": period,
                    "clock": clock,
                    "seconds_elapsed": seconds,
                    "event_type": type_key,
                    "is_goal": 1 if type_key == "goal" else 0,
                    "x_coord": x_coord,
                    "y_coord": y_coord,
                    "distance_ft": _calc_distance(x_coord, y_coord),
                    "angle_deg": _calc_angle(x_coord, y_coord),
                    "shot_type": details.get("shotType", "unknown"),
                    "shooting_player_id": details.get("shootingPlayerId") or details.get("scoringPlayerId"),
                    "goalie_id": details.get("goalieInNetId"),
                    "team_id": event_owner,
                    "is_home_team": 1 if shooting_team_is_home else 0,
                    "home_score_before": home_score,
                    "away_score_before": away_score,
                    "score_diff_before": score_diff_before,
                    "shooting_skaters": shooting_skaters,
                    "defending_skaters": defending_skaters,
                    "shooting_goalie": shooting_goalie,
                    "is_empty_net": 1 if (shooting_goalie == 0) else 0,
                    "reason": details.get("reason"),
                }
            )

        if type_key == "goal":
            if event_owner == home_team_id:
                home_score += 1
            elif event_owner == away_team_id:
                away_score += 1

    df = pd.DataFrame(events)
    if df.empty:
        return df
    df = df.dropna(subset=["distance_ft", "angle_deg", "seconds_elapsed"])
    df.reset_index(drop=True, inplace=True)
    return df
