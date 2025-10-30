"""Feature engineering helpers for NHL game prediction."""

from __future__ import annotations

from typing import Iterable

import numpy as np
import pandas as pd


def engineer_team_features(logs: pd.DataFrame, rolling_windows: Iterable[int] = (5, 10)) -> pd.DataFrame:
    """Add pre-game team features using expanding and rolling statistics."""
    logs = logs.copy()
    numeric_columns = [
        "goalsFor",
        "goalsAgainst",
        "powerPlayPct",
        "penaltyKillPct",
        "shotsForPerGame",
        "shotsAgainstPerGame",
        "faceoffWinPct",
    ]
    for column in numeric_columns:
        logs[column] = pd.to_numeric(logs[column], errors="coerce")

    logs["goal_diff"] = logs["goalsFor"] - logs["goalsAgainst"]
    logs["win"] = (logs["goalsFor"] > logs["goalsAgainst"]).astype(int)

    logs.sort_values(["teamId", "seasonId", "gameDate", "gameId"], inplace=True)

    group = logs.groupby(["teamId", "seasonId"], sort=False)
    logs["games_played_prior"] = group.cumcount()

    wins_cumsum = group["win"].cumsum()
    goal_diff_cumsum = group["goal_diff"].cumsum()

    denom = logs["games_played_prior"].replace(0, np.nan)
    logs["season_win_pct"] = wins_cumsum.shift(1) / denom
    logs["season_goal_diff_avg"] = goal_diff_cumsum.shift(1) / denom

    logs["days_since_last_game"] = group["gameDate"].diff().dt.days

    def _rolling_mean(series: pd.Series, window: int) -> pd.Series:
        return series.shift(1).rolling(window, min_periods=1).mean()

    for window in rolling_windows:
        logs[f"rolling_win_pct_{window}"] = group["win"].transform(lambda s, w=window: _rolling_mean(s, w))
        logs[f"rolling_goal_diff_{window}"] = group["goal_diff"].transform(lambda s, w=window: _rolling_mean(s, w))
        logs[f"rolling_pp_pct_{window}"] = (
            group["powerPlayPct"].transform(lambda s, w=window: _rolling_mean(s, w)) / 100.0
        )
        logs[f"rolling_pk_pct_{window}"] = (
            group["penaltyKillPct"].transform(lambda s, w=window: _rolling_mean(s, w)) / 100.0
        )
        logs[f"rolling_faceoff_{window}"] = group["faceoffWinPct"].transform(lambda s, w=window: _rolling_mean(s, w))

    shot_attempt_margin = logs["shotsForPerGame"] - logs["shotsAgainstPerGame"]
    logs["shot_margin_last_game"] = shot_attempt_margin.shift(1)
    avg_shots_for = group["shotsForPerGame"].transform(lambda s: s.shift().expanding(min_periods=1).mean())
    avg_shots_against = group["shotsAgainstPerGame"].transform(lambda s: s.shift().expanding(min_periods=1).mean())
    logs["season_shot_margin"] = avg_shots_for - avg_shots_against

    # Replace inf coming from division by zero when no prior games exist.
    logs.replace([np.inf, -np.inf], np.nan, inplace=True)

    return logs
