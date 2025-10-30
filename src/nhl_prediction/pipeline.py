"""High-level dataset preparation for NHL prediction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, Tuple, List

import pandas as pd

from .data_ingest import build_game_dataframe, fetch_multi_season_logs
from .features import engineer_team_features


@dataclass(frozen=True)
class Dataset:
    games: pd.DataFrame
    features: pd.DataFrame
    target: pd.Series


def build_dataset(seasons: Iterable[str]) -> Dataset:
    """Fetch data, engineer features, and prepare modelling matrix."""
    raw_logs = fetch_multi_season_logs(seasons)
    enriched_logs = engineer_team_features(raw_logs)
    games = build_game_dataframe(enriched_logs)

    # Filter out games without prior info (season openers).
    valid = (games["games_played_prior_home"] > 0) & (games["games_played_prior_away"] > 0)
    games = games.loc[valid].copy()

    feature_bases = [
        "season_win_pct",
        "season_goal_diff_avg",
        "season_shot_margin",
        "rolling_win_pct_5",
        "rolling_win_pct_10",
        "rolling_goal_diff_5",
        "rolling_goal_diff_10",
        "rolling_pp_pct_5",
        "rolling_pk_pct_5",
        "rolling_faceoff_5",
        "games_played_prior",
        "days_since_last_game",
    ]

    feature_columns: List[str] = []
    for base in feature_bases:
        home_col = f"{base}_home"
        away_col = f"{base}_away"
        if home_col in games.columns and away_col in games.columns:
            diff_col = f"{base}_diff"
            games[diff_col] = games[home_col] - games[away_col]
            feature_columns.append(diff_col)

    # Situational features that mix home vs away metrics.
    if {"rolling_pp_pct_5_home", "rolling_pk_pct_5_away"} <= set(games.columns):
        games["special_teams_matchup"] = (
            games["rolling_pp_pct_5_home"] - games["rolling_pk_pct_5_away"]
        )
        feature_columns.append("special_teams_matchup")
    if {"rolling_pp_pct_5_away", "rolling_pk_pct_5_home"} <= set(games.columns):
        games["special_teams_matchup_inverse"] = (
            games["rolling_pk_pct_5_home"] - games["rolling_pp_pct_5_away"]
        )
        feature_columns.append("special_teams_matchup_inverse")

    features = games[feature_columns].fillna(0.0)
    target = games["home_win"]
    return Dataset(games=games, features=features, target=target)
