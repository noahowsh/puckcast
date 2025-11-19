"""Feature engineering helpers for NHL game prediction - PRE-GAME ONLY."""

from __future__ import annotations

from typing import Iterable, Sequence

import numpy as np
import pandas as pd

ROLL_WINDOWS: Sequence[int] = (3, 5, 10)


def _lagged_rolling(group: pd.Series, window: int, min_periods: int = 1) -> pd.Series:
    """
    Compute rolling average using ONLY prior games.
    
    CRITICAL: .shift(1) ensures current game is EXCLUDED.
    This is ESSENTIAL for pre-game prediction.
    """
    return group.shift(1).rolling(window, min_periods=min_periods).mean()


ALTITUDE_FEET_BY_TEAM: dict[int, float] = {
    1: 30.0,    # NJD (Newark, NJ)
    2: 10.0,    # NYI
    3: 33.0,    # NYR
    4: 39.0,    # PHI
    5: 758.0,   # PIT
    6: 141.0,   # BOS
    7: 600.0,   # BUF
    8: 21.0,    # MTL
    9: 65.0,    # OTT
    10: 76.0,   # TOR
    12: 37.0,   # CAR
    13: 15.0,   # FLA
    14: 8.0,    # TBL
    15: 52.0,   # WSH
    16: 594.0,  # CHI
    17: 594.0,  # DET
    18: 597.0,  # NSH
    19: 572.0,  # STL
    20: 3585.0, # CGY
    21: 5280.0, # COL
    22: 2372.0, # EDM
    23: 10.0,   # VAN
    24: 50.0,   # ANA
    25: 430.0,  # DAL
    26: 305.0,  # LAK
    28: 85.0,   # SJS
    29: 764.0,  # CBJ
    30: 840.0,  # MIN
    52: 760.0,  # WPG
    54: 2000.0, # VGK
    55: 22.0,   # SEA
    68: 4300.0, # UTA
}

HIGH_ALTITUDE_THRESHOLD = 2000.0


def _lagged_streak(series: pd.Series) -> pd.Series:
    """Count consecutive True values observed before the current game."""
    streaks: list[int] = []
    current = 0
    for value in series.fillna(False):
        streaks.append(current)
        current = current + 1 if value else 0
    return pd.Series(streaks, index=series.index)


def engineer_team_features(logs: pd.DataFrame, rolling_windows: Iterable[int] = ROLL_WINDOWS) -> pd.DataFrame:
    """
    Create lagged features using ONLY information available BEFORE each game.
    
    **CRITICAL FOR LIVE PREDICTION:**
    - All features use .shift(1) to exclude current game
    - No future information leaks into features
    - Early-season games get zeros/NaNs (expected - no history)
    
    For predicting upcoming games, this ensures we only use data that would
    actually be known before puck drop.
    """
    logs = logs.copy()

    # Ensure numeric types
    numeric_columns = [
        "goalsFor",
        "goalsAgainst",
        "shotsForPerGame",
        "shotsAgainstPerGame",
        "faceoffWinPct",
        "xGoalsFor",
        "xGoalsAgainst",
        "xGoalsPercentage",
        "highDangerShotsFor",
        "highDangerShotsAgainst",
        "highDangerxGoalsFor",
        "highDangerxGoalsAgainst",
        "corsiPercentage",
        "fenwickPercentage",
        "team_save_pct",
        "team_gsax_per_60",
    ]
    for column in numeric_columns:
        if column in logs.columns:
            logs[column] = pd.to_numeric(logs[column], errors="coerce")

    # Basic derived stats (from current game - will be lagged later)
    logs["goal_diff"] = logs["goalsFor"] - logs["goalsAgainst"]
    logs["win"] = (logs["goal_diff"] > 0).astype(int)
    
    # xGoals derived stats
    if "xGoalsFor" in logs.columns:
        logs["xg_diff"] = logs["xGoalsFor"] - logs["xGoalsAgainst"]
        logs["goals_vs_xg"] = logs["goalsFor"] - logs["xGoalsFor"]  # Over/under-performing
        logs["xg_margin"] = (logs["xGoalsFor"] - logs["xGoalsAgainst"]) / (logs["xGoalsFor"] + logs["xGoalsAgainst"]).replace(0, np.nan)
    
    # Shot quality
    if "highDangerxGoalsFor" in logs.columns and "xGoalsFor" in logs.columns:
        logs["high_danger_xg_share"] = logs["highDangerxGoalsFor"] / logs["xGoalsFor"].replace(0, np.nan)

    # CRITICAL: Sort chronologically for proper lagging
    logs.sort_values(["teamId", "seasonId", "gameDate", "gameId"], inplace=True)

    # Group by team-season for cumulative and rolling stats
    group = logs.groupby(["teamId", "seasonId"], sort=False)
    
    # Games played BEFORE current game
    logs["games_played_prior"] = group.cumcount()

    # Season-to-date averages (LAGGED - excludes current game)
    denom = logs["games_played_prior"].replace(0, np.nan)
    logs["season_win_pct"] = group["win"].cumsum().shift(1) / denom
    logs["season_goal_diff_avg"] = group["goal_diff"].cumsum().shift(1) / denom
    
    # xGoals season averages
    if "xGoalsFor" in logs.columns:
        logs["season_xg_for_avg"] = group["xGoalsFor"].cumsum().shift(1) / denom
        logs["season_xg_against_avg"] = group["xGoalsAgainst"].cumsum().shift(1) / denom
        logs["season_xg_diff_avg"] = logs["season_xg_for_avg"] - logs["season_xg_against_avg"]

    # Rest metrics (TRULY PRE-GAME: based on schedule)
    logs["rest_days"] = group["gameDate"].diff().dt.days
    logs["is_b2b"] = logs["rest_days"].fillna(10).le(1).astype(int)

    # Altitude signals
    avg_altitude = np.mean(list(ALTITUDE_FEET_BY_TEAM.values()))
    logs["team_altitude_ft"] = logs["teamId"].map(ALTITUDE_FEET_BY_TEAM).fillna(0.0)
    logs["altitude_diff"] = logs["team_altitude_ft"] - avg_altitude
    logs["is_high_altitude"] = (logs["team_altitude_ft"] >= HIGH_ALTITUDE_THRESHOLD).astype(int)

    # Venue streaks derived from schedule (pre-game counts)
    logs["is_home"] = logs["homeRoad"].eq("H")
    logs["consecutive_home_prior"] = group["is_home"].transform(_lagged_streak)
    logs["consecutive_away_prior"] = group["is_home"].transform(
        lambda series: _lagged_streak(~series)
    )
    logs["travel_burden"] = logs["consecutive_away_prior"].clip(lower=0)

    # Rolling statistics (ALL LAGGED)
    roll_features: dict[str, pd.Series] = {}
    
    for window in rolling_windows:
        # Core stats
        roll_features[f"rolling_win_pct_{window}"] = group["win"].transform(
            lambda s, w=window: _lagged_rolling(s, w)
        )
        roll_features[f"rolling_goal_diff_{window}"] = group["goal_diff"].transform(
            lambda s, w=window: _lagged_rolling(s, w)
        )
        
        # Faceoffs (CRITICAL PREDICTOR)
        roll_features[f"rolling_faceoff_{window}"] = group["faceoffWinPct"].transform(
            lambda s, w=window: _lagged_rolling(s, w)
        ) / 100.0
        
        # Shots
        roll_features[f"shotsFor_roll_{window}"] = group["shotsForPerGame"].transform(
            lambda s, w=window: _lagged_rolling(s, w)
        )
        roll_features[f"shotsAgainst_roll_{window}"] = group["shotsAgainstPerGame"].transform(
            lambda s, w=window: _lagged_rolling(s, w)
        )
        
        # xGoals rolling (NEW - using MoneyPuck data!)
        if "xGoalsFor" in logs.columns:
            roll_features[f"rolling_xg_for_{window}"] = group["xGoalsFor"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            )
            roll_features[f"rolling_xg_against_{window}"] = group["xGoalsAgainst"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            )
            roll_features[f"rolling_xg_diff_{window}"] = group["xg_diff"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            )
        
        # Possession metrics rolling (NEW)
        if "corsiPercentage" in logs.columns:
            roll_features[f"rolling_corsi_{window}"] = group["corsiPercentage"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            ) / 100.0
        
        if "fenwickPercentage" in logs.columns:
            roll_features[f"rolling_fenwick_{window}"] = group["fenwickPercentage"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            ) / 100.0
        
        # High danger shots rolling (NEW)
        if "highDangerShotsFor" in logs.columns:
            roll_features[f"rolling_high_danger_shots_{window}"] = group["highDangerShotsFor"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            )
        
        # Goaltending rolling (NEW - Season aggregate gets rolling average for stability)
        if "team_save_pct" in logs.columns:
            roll_features[f"rolling_save_pct_{window}"] = group["team_save_pct"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            )
        
        if "team_gsax_per_60" in logs.columns:
            roll_features[f"rolling_gsax_{window}"] = group["team_gsax_per_60"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            )

    logs = logs.assign(**roll_features)

    # Shot margin trends
    logs["shot_margin"] = logs["shotsForPerGame"] - logs["shotsAgainstPerGame"]
    team_group = logs.groupby(["teamId", "seasonId"], sort=False)
    logs["shot_margin_last_game"] = team_group["shot_margin"].shift(1)
    logs["season_shot_margin"] = team_group["shot_margin"].transform(
        lambda s: s.shift(1).expanding(min_periods=1).mean()
    )

    # Momentum indicators (recent vs season average)
    logs["momentum_win_pct"] = logs["rolling_win_pct_5"] - logs["season_win_pct"]
    logs["momentum_goal_diff"] = logs["rolling_goal_diff_5"] - logs["season_goal_diff_avg"]
    logs["momentum_shot_margin"] = logs["shot_margin_last_game"] - logs["season_shot_margin"]
    
    # xGoals momentum (NEW)
    if "rolling_xg_diff_5" in logs.columns and "season_xg_diff_avg" in logs.columns:
        logs["momentum_xg"] = logs["rolling_xg_diff_5"] - logs["season_xg_diff_avg"]

    # Schedule congestion indicators (PRE-GAME: based on known schedule)
    gap = logs.groupby("teamId", sort=False)["rest_days"]
    recent_one_day = gap.transform(lambda s: s.fillna(10).le(1).astype(int))
    logs["games_last_3d"] = (recent_one_day + recent_one_day.shift(1).fillna(0)).clip(0, 3)
    recent_two_day = gap.transform(lambda s: s.fillna(10).le(2).astype(int))
    logs["games_last_6d"] = (
        recent_two_day
        + recent_two_day.shift(1).fillna(0)
        + recent_two_day.shift(2).fillna(0)
        + recent_two_day.shift(3).fillna(0)
    ).clip(0, 4)

    # List of ALL features (for fillna)
    feature_cols = [
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
    ]
    feature_cols.extend(
        [
            "team_altitude_ft",
            "altitude_diff",
            "is_high_altitude",
            "consecutive_home_prior",
            "consecutive_away_prior",
            "travel_burden",
        ]
    )
    
    # Add xGoals features if available
    if "season_xg_for_avg" in logs.columns:
        feature_cols.extend([
            "season_xg_for_avg",
            "season_xg_against_avg",
            "season_xg_diff_avg",
            "momentum_xg",
        ])

    # Add rolling window features
    for window in rolling_windows:
        feature_cols.extend([
            f"rolling_win_pct_{window}",
            f"rolling_goal_diff_{window}",
            f"rolling_faceoff_{window}",
            f"shotsFor_roll_{window}",
            f"shotsAgainst_roll_{window}",
        ])
        
        # xGoals rolling
        if f"rolling_xg_for_{window}" in logs.columns:
            feature_cols.extend([
                f"rolling_xg_for_{window}",
                f"rolling_xg_against_{window}",
                f"rolling_xg_diff_{window}",
            ])
        
        # Possession rolling
        if f"rolling_corsi_{window}" in logs.columns:
            feature_cols.append(f"rolling_corsi_{window}")
        if f"rolling_fenwick_{window}" in logs.columns:
            feature_cols.append(f"rolling_fenwick_{window}")
        
        # High danger rolling
        if f"rolling_high_danger_shots_{window}" in logs.columns:
            feature_cols.append(f"rolling_high_danger_shots_{window}")
        
        # Goaltending rolling
        if f"rolling_save_pct_{window}" in logs.columns:
            feature_cols.append(f"rolling_save_pct_{window}")
        if f"rolling_gsax_{window}" in logs.columns:
            feature_cols.append(f"rolling_gsax_{window}")

    # Fill NaNs (expected for early-season games with no history)
    logs[feature_cols] = logs[feature_cols].fillna(0.0)
    
    return logs
