"""High-level dataset preparation for NHL prediction."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Dict

import numpy as np
import pandas as pd

from .data_ingest import build_game_dataframe, fetch_multi_season_logs
from .features import ROLL_WINDOWS, engineer_team_features


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
    games = _add_elo_features(games)

    rolling_windows = ROLL_WINDOWS
    feature_bases: List[str] = [
        "season_win_pct",
        "season_goal_diff_avg",
        "season_shot_margin",
        "shot_margin_last_game",
        "momentum_win_pct",
        "momentum_goal_diff",
        "momentum_shot_margin",
        "rest_days",
        "is_b2b",
        "games_last_3d",
        "games_last_6d",
        "lineTopTrioSeconds",
        "lineTopPairSeconds",
        "lineForwardConcentration",
        "lineForwardContinuity",
        "lineDefenseConcentration",
        "lineDefenseContinuity",
        "line_top_trio_min",
        "line_top_pair_min",
        "line_forward_balance",
        "line_defense_balance",
        "powerPlayPct",
        "penaltyKillPct",
        "powerPlayNetPct",
        "penaltyKillNetPct",
        "seasonPointPct",
        "specialTeamEdge",
        "goalie_save_pct_game",
        "goalie_xg_saved",
        "goalie_shots_faced",
        "goalie_confirmed_start",
        "goalie_injury_flag",
        "goalie_start_likelihood",
        "goalie_rest_days",
        "goalie_rolling_gsa",
        "goalie_trend_score",
        "team_injury_count",
        # NEW: xGoals season averages
        "season_xg_for_avg",
        "season_xg_against_avg",
        "season_xg_diff_avg",
        "momentum_xg",
        # V7.0: Momentum-weighted rolling features
        "momentum_xg_for_4",
        "momentum_xg_against_4",
        "momentum_goal_diff_4",
        "momentum_high_danger_shots_4",
        "momentum_win_rate_4",
    ]

    for window in rolling_windows:
        feature_bases.extend(
            [
                f"rolling_win_pct_{window}",
                f"rolling_goal_diff_{window}",
                f"rolling_faceoff_{window}",
                f"shotsFor_roll_{window}",
                f"shotsAgainst_roll_{window}",
                # NEW: xGoals rolling windows
                f"rolling_xg_for_{window}",
                f"rolling_xg_against_{window}",
                f"rolling_xg_diff_{window}",
                # NEW: Possession metrics
                f"rolling_corsi_{window}",
                f"rolling_fenwick_{window}",
                # NEW: High danger shots
                f"rolling_high_danger_shots_{window}",
                # NEW: Goaltending metrics
                f"rolling_save_pct_{window}",
                f"rolling_gsax_{window}",
                f"rolling_goalie_save_pct_{window}",
                f"rolling_goalie_xg_saved_{window}",
                f"rolling_goalie_shots_faced_{window}",
                f"rolling_powerPlayPct_{window}",
                f"rolling_penaltyKillPct_{window}",
                f"rolling_powerPlayNetPct_{window}",
                f"rolling_penaltyKillNetPct_{window}",
                f"rolling_seasonPointPct_{window}",
                f"rolling_specialTeamEdge_{window}",
                # NEW: Rebound features (MoneyPuck-inspired)
                f"rolling_rebounds_for_{window}",
                f"rolling_rebound_goals_{window}",
                # NEW: Penalty differential
                f"rolling_penalty_diff_{window}",
                # NEW: Rush features (MoneyPuck-inspired)
                f"rolling_rush_shots_{window}",
                f"rolling_rush_goals_{window}",
                # NEW: High danger xG (more refined than shots)
                f"rolling_hd_xg_for_{window}",
                f"rolling_hd_xg_against_{window}",
                # NEW: Turnover differential
                f"rolling_turnover_diff_{window}",
            ]
        )

    feature_columns: List[str] = []
    for base in feature_bases:
        home_col = f"{base}_home"
        away_col = f"{base}_away"
        if home_col in games.columns and away_col in games.columns:
            if np.issubdtype(games[home_col].dtype, np.number) and np.issubdtype(games[away_col].dtype, np.number):
                diff_col = f"{base}_diff"
                games[diff_col] = games[home_col] - games[away_col]
                feature_columns.append(diff_col)

    additional_features = [
        "games_played_prior_home",
        "games_played_prior_away",
        "rest_days_home",
        "rest_days_away",
        "games_last_3d_home",
        "games_last_3d_away",
        "games_last_6d_home",
        "games_last_6d_away",
        "is_b2b_home",
        "is_b2b_away",
        "elo_diff_pre",
        "elo_expectation_home",
        "team_altitude_ft_home",
        "team_altitude_ft_away",
        "altitude_diff_home",
        "altitude_diff_away",
        "is_high_altitude_home",
        "is_high_altitude_away",
        "consecutive_home_prior_home",
        "consecutive_home_prior_away",
        "consecutive_away_prior_home",
        "consecutive_away_prior_away",
        "travel_burden_home",
        "travel_burden_away",
    ]
    for feat in additional_features:
        if feat in games.columns:
            feature_columns.append(feat)

    # NOTE: Special teams matchup features removed because MoneyPuck doesn't provide
    # game-by-game PP%/PK%. Would need season-long calculation which isn't accurate.
    # xGoals features provide better shot quality signal anyway.

    # Rest-based features.
    def _rest_bucket(days: float) -> str:
        if pd.isna(days):
            return "no_prev"
        if days <= 1:
            return "b2b"
        if days == 2:
            return "one_day"
        if days == 3:
            return "two_days"
        return "three_plus"

    games["rest_bucket_home"] = games["rest_days_home"].apply(_rest_bucket)
    games["rest_bucket_away"] = games["rest_days_away"].apply(_rest_bucket)
    games["rest_diff"] = games["rest_days_home"] - games["rest_days_away"]
    games["home_b2b"] = (games["rest_bucket_home"] == "b2b").astype(int)
    games["away_b2b"] = (games["rest_bucket_away"] == "b2b").astype(int)
    feature_columns.extend(["rest_diff", "home_b2b", "away_b2b"])

    games = pd.get_dummies(
        games,
        columns=["rest_bucket_home", "rest_bucket_away"],
        prefix=["rest_home", "rest_away"],
        dtype=int,
    )
    rest_dummy_cols = [
        col for col in games.columns if col.startswith("rest_home_") or col.startswith("rest_away_")
    ]
    feature_columns.extend(rest_dummy_cols)

    home_team_dummies = pd.get_dummies(games["teamId_home"], prefix="home_team", dtype=int)
    away_team_dummies = pd.get_dummies(games["teamId_away"], prefix="away_team", dtype=int)
    games = pd.concat([games, home_team_dummies, away_team_dummies], axis=1)
    feature_columns.extend(home_team_dummies.columns.tolist())
    feature_columns.extend(away_team_dummies.columns.tolist())

    features = games[feature_columns].fillna(0.0)
    target = games["home_win"]
    return Dataset(games=games, features=features, target=target)


def _add_elo_features(
    games: pd.DataFrame,
    base_rating: float = 1500.0,
    k_factor: float = 10.0,
    home_advantage: float = 30.0,
) -> pd.DataFrame:
    """Compute pre-game Elo ratings per team per season."""
    games = games.sort_values("gameDate").copy()
    elo_home: List[float] = []
    elo_away: List[float] = []
    expected_home_probs: List[float] = []

    current_season: str | None = None
    ratings: Dict[int, float] = {}

    for _, row in games.iterrows():
        season = row["seasonId"]
        if season != current_season:
            current_season = season
            ratings = {}

        home_id = int(row["teamId_home"])
        away_id = int(row["teamId_away"])

        home_rating = ratings.get(home_id, base_rating)
        away_rating = ratings.get(away_id, base_rating)

        elo_home.append(home_rating)
        elo_away.append(away_rating)

        expected_home = 1.0 / (1.0 + 10 ** ((away_rating - (home_rating + home_advantage)) / 400))
        expected_home_probs.append(expected_home)

        outcome_home = 1.0 if row["home_win"] == 1 else 0.0
        goal_diff = row["home_score"] - row["away_score"]
        margin = max(abs(goal_diff), 1)
        multiplier = np.log(margin + 1) * (2.2 / ((abs(home_rating - away_rating) * 0.001) + 2.2))
        delta = k_factor * multiplier * (outcome_home - expected_home)

        ratings[home_id] = home_rating + delta
        ratings[away_id] = away_rating - delta

    games["elo_home_pre"] = elo_home
    games["elo_away_pre"] = elo_away
    games["elo_diff_pre"] = games["elo_home_pre"] - games["elo_away_pre"]
    games["elo_expectation_home"] = expected_home_probs
    return games
