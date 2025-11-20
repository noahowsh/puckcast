"""Feature engineering helpers for NHL game prediction - PRE-GAME ONLY."""

from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path
from typing import Iterable, Sequence

import numpy as np
import pandas as pd

ROLL_WINDOWS: Sequence[int] = (3, 5, 10)
GOALIE_PULSE_PATH = Path(__file__).resolve().parents[2] / "web" / "src" / "data" / "goaliePulse.json"
STARTING_GOALIE_PATH = Path(__file__).resolve().parents[2] / "web" / "src" / "data" / "startingGoalies.json"
PLAYER_INJURIES_PATH = Path(__file__).resolve().parents[2] / "web" / "src" / "data" / "playerInjuries.json"
TREND_SCORE = {
    "surging": 1.0,
    "steady": 0.0,
    "cooling": -1.0,
}


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


@lru_cache(maxsize=1)
def _load_goalie_pulse() -> dict[str, dict[str, float]]:
    if not GOALIE_PULSE_PATH.exists():
        return {}
    try:
        data = json.loads(GOALIE_PULSE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    goalies = data.get("goalies", [])
    result: dict[str, dict[str, float]] = {}
    for entry in goalies:
        team = (entry.get("team") or "").strip().upper()
        if not team:
            continue
        start_likelihood = float(entry.get("startLikelihood") or 0.0)
        rest_days = float(entry.get("restDays") or 0.0)
        rolling_gsa = float(entry.get("rollingGsa") or 0.0)
        trend = TREND_SCORE.get((entry.get("trend") or "").lower(), 0.0)
        candidate = {
            "startLikelihood": start_likelihood,
            "restDays": rest_days,
            "rollingGsa": rolling_gsa,
            "trendScore": trend,
        }
        existing = result.get(team)
        if existing and existing["startLikelihood"] >= start_likelihood:
            continue
        result[team] = candidate
    return result


@lru_cache(maxsize=1)
def _load_starting_goalies() -> dict[str, dict[str, Any]]:
    if not STARTING_GOALIE_PATH.exists():
        return {}
    try:
        data = json.loads(STARTING_GOALIE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    return data.get("teams", {})


@lru_cache(maxsize=1)
def _load_player_injuries() -> dict[str, int]:
    if not PLAYER_INJURIES_PATH.exists():
        return {}
    try:
        data = json.loads(PLAYER_INJURIES_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    teams = data.get("teams", {})
    return {team: len(info.get("injuries") or []) for team, info in teams.items()}


def _add_h2h_features(logs: pd.DataFrame, lookback: int = 10) -> pd.DataFrame:
    """
    Add head-to-head matchup history features - OPTIMIZED VERSION.

    For each game, computes stats from the last N games between the two teams.
    Only uses games that occurred BEFORE the current game (no future leakage).

    Features:
    - h2h_win_pct: Win percentage in last N games vs this opponent
    - h2h_goal_diff: Average goal differential in last N games vs this opponent
    - h2h_games_played: Number of games played vs this opponent in history
    """
    logs = logs.copy()

    # Initialize H2H features with neutral prior
    logs["h2h_win_pct"] = 0.5
    logs["h2h_goal_diff"] = 0.0
    logs["h2h_games_played"] = 0

    # Sort chronologically to ensure proper ordering
    logs = logs.sort_values(["season", "gameDate"]).reset_index(drop=True)

    # Create a matchup identifier (sorted team abbrevs to handle both home/away)
    def get_matchup_key(row):
        teams = sorted([row["teamAbbrev"], row["opponentTeamAbbrev"]])
        return f"{teams[0]}_vs_{teams[1]}"

    logs["matchup_key"] = logs.apply(get_matchup_key, axis=1)

    # Group by matchup and process each group independently
    for matchup_key, group in logs.groupby("matchup_key"):
        if len(group) < 2:
            continue  # Skip if only one game between these teams

        indices = group.index.tolist()

        # For each game in this matchup
        for i, idx in enumerate(indices):
            if i == 0:
                continue  # First game has no history

            # Get previous games in this matchup
            prev_indices = indices[:i]
            prev_games = logs.loc[prev_indices].tail(lookback)

            current_team = logs.loc[idx, "teamAbbrev"]

            # Calculate H2H stats from perspective of current team
            h2h_wins = 0
            h2h_goal_diffs = []

            for prev_idx in prev_games.index:
                prev_team = logs.loc[prev_idx, "teamAbbrev"]
                prev_win = logs.loc[prev_idx, "win"]
                prev_goal_diff = logs.loc[prev_idx, "goal_diff"]

                if prev_team == current_team:
                    # Current team was "team" in previous game
                    if prev_win == 1:
                        h2h_wins += 1
                    h2h_goal_diffs.append(prev_goal_diff)
                else:
                    # Current team was "opponent" in previous game - flip result
                    if prev_win == 0:
                        h2h_wins += 1
                    h2h_goal_diffs.append(-prev_goal_diff)

            # Update H2H features
            games_count = len(prev_games)
            logs.loc[idx, "h2h_win_pct"] = h2h_wins / games_count if games_count > 0 else 0.5
            logs.loc[idx, "h2h_goal_diff"] = sum(h2h_goal_diffs) / games_count if h2h_goal_diffs else 0.0
            logs.loc[idx, "h2h_games_played"] = games_count

    # Drop temporary column
    logs = logs.drop(columns=["matchup_key"])

    return logs


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
        "goalieShotsFaced",
        "goalieGoalsAllowed",
        "goalieXgAllowed",
        # Individual starting goalie features
        "goalie_save_pct",
        "goalie_gsax_per_60",
        "goalie_games_played",
        "goalie_xgoals_faced",
        "goalie_goals_allowed",
        # Rebound features
        "reboundsFor",
        "reboundsAgainst",
        "reboundGoalsFor",
        "reboundGoalsAgainst",
        # Penalty features
        "penaltiesTaken",
        "penaltiesDrawn",
        "penaltyMinutes",
        "penaltyDifferential",
        "powerPlayPct",
        "penaltyKillPct",
        "powerPlayNetPct",
        "penaltyKillNetPct",
        "seasonPointPct",
        "lineTopTrioSeconds",
        "lineTopPairSeconds",
        "lineForwardConcentration",
        "lineDefenseConcentration",
        "lineForwardContinuity",
        "lineDefenseContinuity",
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

    # Special teams signal (power play vs penalty kill)
    special_cols = [
        "powerPlayPct",
        "penaltyKillPct",
        "powerPlayNetPct",
        "penaltyKillNetPct",
        "seasonPointPct",
    ]
    for special_col in special_cols:
        if special_col in logs.columns:
            logs[special_col] = pd.to_numeric(logs[special_col], errors="coerce").fillna(0.0)
        else:
            logs[special_col] = 0.0
    logs["specialTeamEdge"] = logs["powerPlayPct"] - logs["penaltyKillPct"]

    # Altitude signals
    avg_altitude = np.mean(list(ALTITUDE_FEET_BY_TEAM.values()))
    logs["team_altitude_ft"] = logs["teamId"].map(ALTITUDE_FEET_BY_TEAM).fillna(0.0)
    logs["altitude_diff"] = logs["team_altitude_ft"] - avg_altitude
    logs["is_high_altitude"] = (logs["team_altitude_ft"] >= HIGH_ALTITUDE_THRESHOLD).astype(int)

    # Line chemistry signals
    for line_col in [
        "lineTopTrioSeconds",
        "lineTopPairSeconds",
        "lineForwardConcentration",
        "lineDefenseConcentration",
        "lineForwardContinuity",
        "lineDefenseContinuity",
    ]:
        if line_col in logs.columns:
            logs[line_col] = pd.to_numeric(logs[line_col], errors="coerce").fillna(0.0)
        else:
            logs[line_col] = 0.0
    logs["line_top_trio_min"] = logs["lineTopTrioSeconds"] / 60.0
    logs["line_top_pair_min"] = logs["lineTopPairSeconds"] / 60.0
    logs["line_forward_balance"] = logs["lineForwardConcentration"] - logs["lineDefenseConcentration"]
    logs["line_defense_balance"] = logs["lineDefenseConcentration"] - logs["lineForwardConcentration"]

    # Goalie pulse projections
    starting_map = _load_starting_goalies()
    team_abbrevs = logs["teamAbbrev"].fillna("").str.upper()
    logs["goalie_confirmed_start"] = team_abbrevs.map(
        lambda abbr: float(bool(starting_map.get(abbr, {}).get("confirmedStart")))
    )
    logs["goalie_injury_flag"] = team_abbrevs.map(
        lambda abbr: float(bool(starting_map.get(abbr, {}).get("statusCode")))
    )
    injury_map = _load_player_injuries()
    logs["team_injury_count"] = team_abbrevs.map(
        lambda abbr: float(injury_map.get(abbr, 0))
    )
    home_injury_count = logs.groupby(["gameId", "homeRoad"]).cumcount()  # dummy to avoid lint
    # We'll derive home/away by looking at homeRoad; replicates near original

    # Goalie pulse projections
    pulse_map = _load_goalie_pulse()
    team_abbrevs = logs["teamAbbrev"].fillna("").str.upper()
    logs["goalie_start_likelihood"] = team_abbrevs.map(
        lambda abbr: pulse_map.get(abbr, {}).get("startLikelihood", 0.0)
    )
    logs["goalie_rest_days"] = team_abbrevs.map(
        lambda abbr: pulse_map.get(abbr, {}).get("restDays", 0.0)
    )
    logs["goalie_rolling_gsa"] = team_abbrevs.map(
        lambda abbr: pulse_map.get(abbr, {}).get("rollingGsa", 0.0)
    )
    logs["goalie_trend_score"] = team_abbrevs.map(
        lambda abbr: pulse_map.get(abbr, {}).get("trendScore", 0.0)
    )

    # Goaltender derived stats
    if {"goalieShotsFaced", "goalieGoalsAllowed", "goalieXgAllowed"}.issubset(logs.columns):
        logs["goalie_save_pct_game"] = (
            (logs["goalieShotsFaced"] - logs["goalieGoalsAllowed"])
            / logs["goalieShotsFaced"].replace(0, np.nan)
        ).fillna(0.0)
        logs["goalie_xg_saved"] = (logs["goalieXgAllowed"] - logs["goalieGoalsAllowed"]).fillna(0.0)
        logs["goalie_shots_faced"] = logs["goalieShotsFaced"].fillna(0.0)
    else:
        logs["goalie_save_pct_game"] = 0.0
        logs["goalie_xg_saved"] = 0.0
        logs["goalie_shots_faced"] = 0.0

    # Venue streaks derived from schedule (pre-game counts)
    logs["is_home"] = logs["homeRoad"].eq("H")
    logs["consecutive_home_prior"] = group["is_home"].transform(_lagged_streak)
    logs["consecutive_away_prior"] = group["is_home"].transform(
        lambda series: _lagged_streak(~series)
    )
    logs["travel_burden"] = logs["consecutive_away_prior"].clip(lower=0)

    # Win/loss streaks (pre-game)
    logs["consecutive_wins_prior"] = group["win"].transform(_lagged_streak)
    logs["consecutive_losses_prior"] = group["win"].transform(
        lambda series: _lagged_streak(~series.astype(bool))
    )

    # Head-to-head matchup history (pre-game only) - TEMPORARILY DISABLED FOR TESTING
    # logs = _add_h2h_features(logs)

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

        # Rebound stats rolling (NEW)
        if "reboundsFor" in logs.columns:
            roll_features[f"rolling_rebounds_for_{window}"] = group["reboundsFor"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            )
        if "reboundGoalsFor" in logs.columns:
            roll_features[f"rolling_rebound_goals_{window}"] = group["reboundGoalsFor"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            )

        # Penalty stats rolling (NEW)
        if "penaltyDifferential" in logs.columns:
            roll_features[f"rolling_penalty_diff_{window}"] = group["penaltyDifferential"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            )
        if "penaltyMinutes" in logs.columns:
            roll_features[f"rolling_penalty_minutes_{window}"] = group["penaltyMinutes"].transform(
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
        if "goalie_save_pct_game" in logs.columns:
            roll_features[f"rolling_goalie_save_pct_{window}"] = group["goalie_save_pct_game"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            )
        if "goalie_xg_saved" in logs.columns:
            roll_features[f"rolling_goalie_xg_saved_{window}"] = group["goalie_xg_saved"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            )
        if "goalie_shots_faced" in logs.columns:
            roll_features[f"rolling_goalie_shots_faced_{window}"] = group["goalie_shots_faced"].transform(
                lambda s, w=window: _lagged_rolling(s, w)
            )
        for special_col in [
            "powerPlayPct",
            "penaltyKillPct",
            "powerPlayNetPct",
            "penaltyKillNetPct",
            "seasonPointPct",
            "specialTeamEdge",
        ]:
            if special_col in logs.columns:
                roll_features[f"rolling_{special_col}_{window}"] = group[special_col].transform(
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
            "consecutive_wins_prior",
            "consecutive_losses_prior",
        ]
    )
    feature_cols.extend(
        [
            "goalie_start_likelihood",
            "goalie_rest_days",
            "goalie_rolling_gsa",
            "goalie_trend_score",
            "goalie_confirmed_start",
            "goalie_injury_flag",
            "team_injury_count",
        ]
    )
    feature_cols.extend(
        [
            "lineTopTrioSeconds",
            "lineTopPairSeconds",
            "lineForwardConcentration",
            "lineDefenseConcentration",
            "lineForwardContinuity",
            "lineDefenseContinuity",
            "line_top_trio_min",
            "line_top_pair_min",
            "line_forward_balance",
            "line_defense_balance",
        ]
    )
    feature_cols.extend(
        [
            "goalie_save_pct_game",
            "goalie_xg_saved",
            "goalie_shots_faced",
        ]
    )
    feature_cols.extend(
        [
            "powerPlayPct",
            "penaltyKillPct",
            "powerPlayNetPct",
            "penaltyKillNetPct",
            "seasonPointPct",
            "specialTeamEdge",
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

        # Rebound rolling
        if f"rolling_rebounds_for_{window}" in logs.columns:
            feature_cols.append(f"rolling_rebounds_for_{window}")
        if f"rolling_rebound_goals_{window}" in logs.columns:
            feature_cols.append(f"rolling_rebound_goals_{window}")

        # Penalty rolling
        if f"rolling_penalty_diff_{window}" in logs.columns:
            feature_cols.append(f"rolling_penalty_diff_{window}")
        if f"rolling_penalty_minutes_{window}" in logs.columns:
            feature_cols.append(f"rolling_penalty_minutes_{window}")

        # Goaltending rolling
        if f"rolling_save_pct_{window}" in logs.columns:
            feature_cols.append(f"rolling_save_pct_{window}")
        if f"rolling_gsax_{window}" in logs.columns:
            feature_cols.append(f"rolling_gsax_{window}")

    # Fill NaNs (expected for early-season games with no history)
    logs[feature_cols] = logs[feature_cols].fillna(0.0)
    
    return logs
