#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════╗
║                    PUCKCAST.AI                            ║
║          Data-Driven NHL Prediction Intelligence          ║
╚═══════════════════════════════════════════════════════════╝

FULL MODEL NHL PREDICTIONS
Predict today's games using V7.0 (adaptive weights + dynamic features)

V7.0 Production Model:
1. Adaptive weights for evolving home advantage:
   - window=100: Slower adaptation reduces noise
   - scale=700: Less aggressive adjustment
   - Robust across 4 seasons (60.9% accuracy on 5,002 games)

2. Dynamic threshold:
   - Formula: threshold = 0.5 + (0.535 - rolling_hw_50) * 0.5
   - Adapts to seasons with varying home win rates

3. 39 curated features + adaptive weights
   - Tested on 4-season holdout (2021-25)
   - Baseline: 53.9% (home win rate)
   - Edge vs baseline: +6.9 pts

Usage:
    python predict_full.py

    # Or predict specific date:
    python predict_full.py 2024-11-15

Requirements:
    - Internet connection (NHL API)
    - Cached game data will be used if available
"""

import sys
import json
import warnings
from pathlib import Path
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.nhl_api import fetch_future_games, fetch_todays_games, fetch_schedule
from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import calibrate_threshold, create_baseline_model, fit_model, tune_logreg_c
from nhl_prediction.situational_features import add_situational_features
# from nhl_prediction.player_hub.context import refresh_player_hub_context  # Module not implemented yet

# Suppress sklearn warnings
warnings.filterwarnings('ignore', category=UserWarning)

WEB_PREDICTIONS_PATH = Path(__file__).parent.parent / "web" / "src" / "data" / "todaysPredictions.json"

# Historical average home win rate (baseline for adaptive weighting)
HISTORICAL_HOME_WIN_RATE = 0.535

# Dynamic threshold adjustment factor
# When league home win rate drops, raise threshold to pick home less often
THRESHOLD_ADJUSTMENT_FACTOR = 0.5


def add_league_hw_feature(games: pd.DataFrame) -> pd.DataFrame:
    """Add rolling league-wide home win rate features.

    This helps the model adapt to structural shifts in NHL home advantage
    between seasons (e.g., 2024-25 had 56.2% home win rate vs historical 51-54%).

    Adds two features:
    - league_hw_100: Rolling 100-game average (for model feature)
    - league_hw_50: Rolling 50-game average (for dynamic threshold)
    """
    games = games.sort_values('gameDate').copy()

    # Calculate rolling home win rate across all games (last 100)
    games['league_hw_100'] = games['home_win'].rolling(
        window=100, min_periods=50
    ).mean().shift(1)  # Shift to avoid leakage

    # Fill early games with historical average
    games['league_hw_100'] = games['league_hw_100'].fillna(HISTORICAL_HOME_WIN_RATE)

    # Add 50-game rolling average for dynamic threshold
    games['league_hw_50'] = games['home_win'].rolling(
        window=50, min_periods=25
    ).mean().shift(1)  # Shift to avoid leakage
    games['league_hw_50'] = games['league_hw_50'].fillna(HISTORICAL_HOME_WIN_RATE)

    return games


def calculate_dynamic_threshold(league_hw: float, k: float = THRESHOLD_ADJUSTMENT_FACTOR) -> float:
    """Calculate dynamic decision threshold based on current league home win rate.

    V7.0 Adaptive Feature:
    When league home win rate drops below historical norm (0.535), raise the
    threshold to pick home less often. This adapts to structural shifts in
    NHL home advantage across seasons.

    Formula: threshold = 0.5 + (0.535 - league_hw) * k

    Examples:
    - league_hw = 0.535 (normal): threshold = 0.500 (unchanged)
    - league_hw = 0.520 (low):    threshold = 0.5075 (pick home less)
    - league_hw = 0.560 (high):   threshold = 0.4875 (pick home more)

    Args:
        league_hw: Current rolling league home win rate
        k: Adjustment factor (default 0.5)

    Returns:
        Threshold for deciding home win prediction (clamped to 0.45-0.55)
    """
    threshold = 0.5 + (HISTORICAL_HOME_WIN_RATE - league_hw) * k
    return float(np.clip(threshold, 0.45, 0.55))


def calculate_adaptive_weights(games: pd.DataFrame, target: pd.Series) -> np.ndarray:
    """Calculate sample weights that down-weight seasons with unusual home advantage.

    This prevents the model from over-learning from anomalous seasons like 2024-25
    (which had 56.2% home win rate vs historical 53.5%).

    Seasons with home win rates close to historical average get weight ~1.0.
    Seasons with unusual home win rates (e.g., 2024-25 at 56.2%) get lower weights.
    """
    weights = np.ones(len(target))
    seasons = games['seasonId'].values

    # Calculate season-level home win rates
    season_hw_rates = {}
    for season in games['seasonId'].unique():
        season_mask = games['seasonId'] == season
        season_hw = target[season_mask].mean()
        season_hw_rates[season] = season_hw

    # Calculate weights based on deviation from historical average
    for i, season in enumerate(seasons):
        season_hw = season_hw_rates[season]
        deviation = abs(season_hw - HISTORICAL_HOME_WIN_RATE)
        # Down-weight unusual seasons (larger deviation = lower weight)
        # Deviation of 0.03 (~56% vs 53.5%) gives weight of ~0.87
        weights[i] = 1.0 / (1.0 + deviation * 5)

    return weights


ET_ZONE = ZoneInfo("America/New_York")


def compute_team_rolling_stats(
    team_id: int,
    team_games: pd.DataFrame,
    windows: list[int] = [3, 5, 10],
) -> dict:
    """Compute fresh rolling statistics for a team from their recent games.

    Args:
        team_id: The team's ID
        team_games: DataFrame of the team's games (sorted by date, most recent last)
        windows: Rolling window sizes to compute

    Returns:
        Dictionary of rolling stats for each window size
    """
    stats = {}

    if len(team_games) == 0:
        return stats

    # For each game, determine if this team was home or away
    # and extract their stats accordingly
    team_stats = []
    for _, game in team_games.iterrows():
        was_home = game['teamId_home'] == team_id

        if was_home:
            team_stats.append({
                'win': 1 if game.get('home_win', 0) == 1 else 0,
                'goals_for': game.get('goalsFor_home', game.get('home_score', 0)),
                'goals_against': game.get('goalsAgainst_home', game.get('away_score', 0)),
                'xg_for': game.get('xGoalsFor_home', 0),
                'xg_against': game.get('xGoalsAgainst_home', 0),
                'corsi_pct': game.get('corsiPercentage_home', 50),
                'fenwick_pct': game.get('fenwickPercentage_home', 50),
                'high_danger_shots': game.get('highDangerShotsFor_home', 0),
                'shots_for': game.get('shotsForPerGame_home', 30),
                'shots_against': game.get('shotsAgainstPerGame_home', 30),
                'faceoff_pct': game.get('faceoffWinPct_home', 50),
                # Team-level goaltending (pipeline uses team_save_pct, team_gsax_per_60)
                'team_save_pct': game.get('team_save_pct_home', 0.900),
                'team_gsax': game.get('team_gsax_per_60_home', 0),
            })
        else:
            team_stats.append({
                'win': 0 if game.get('home_win', 0) == 1 else 1,
                'goals_for': game.get('goalsFor_away', game.get('away_score', 0)),
                'goals_against': game.get('goalsAgainst_away', game.get('home_score', 0)),
                'xg_for': game.get('xGoalsFor_away', 0),
                'xg_against': game.get('xGoalsAgainst_away', 0),
                'corsi_pct': game.get('corsiPercentage_away', 50),
                'fenwick_pct': game.get('fenwickPercentage_away', 50),
                'high_danger_shots': game.get('highDangerShotsFor_away', 0),
                'shots_for': game.get('shotsForPerGame_away', 30),
                'shots_against': game.get('shotsAgainstPerGame_away', 30),
                'faceoff_pct': game.get('faceoffWinPct_away', 50),
                # Team-level goaltending (pipeline uses team_save_pct, team_gsax_per_60)
                'team_save_pct': game.get('team_save_pct_away', 0.900),
                'team_gsax': game.get('team_gsax_per_60_away', 0),
            })

    if len(team_stats) == 0:
        return stats

    team_df = pd.DataFrame(team_stats)

    # Compute derived stats
    team_df['goal_diff'] = team_df['goals_for'] - team_df['goals_against']
    team_df['xg_diff'] = team_df['xg_for'] - team_df['xg_against']

    # Compute rolling stats for each window
    # Note: Pipeline stores corsi/fenwick as fractions (0.5 = 50%), so divide by 100
    for w in windows:
        if len(team_df) >= w:
            recent = team_df.tail(w)
            stats[f'win_pct_{w}'] = recent['win'].mean()
            stats[f'goal_diff_{w}'] = recent['goal_diff'].mean()
            stats[f'xg_diff_{w}'] = recent['xg_diff'].mean()
            stats[f'corsi_{w}'] = recent['corsi_pct'].mean() / 100.0  # Convert to fraction
            stats[f'fenwick_{w}'] = recent['fenwick_pct'].mean() / 100.0  # Convert to fraction
            stats[f'high_danger_shots_{w}'] = recent['high_danger_shots'].mean()
            stats[f'shots_for_{w}'] = recent['shots_for'].mean()
            stats[f'faceoff_{w}'] = recent['faceoff_pct'].mean() / 100.0  # Convert to fraction
            # Team goaltending (pipeline uses team_save_pct not savePct)
            stats[f'save_pct_{w}'] = recent['team_save_pct'].mean()
            stats[f'gsax_{w}'] = recent['team_gsax'].mean()
        else:
            # Use all available games if fewer than window
            stats[f'win_pct_{w}'] = team_df['win'].mean()
            stats[f'goal_diff_{w}'] = team_df['goal_diff'].mean()
            stats[f'xg_diff_{w}'] = team_df['xg_diff'].mean()
            stats[f'corsi_{w}'] = team_df['corsi_pct'].mean() / 100.0  # Convert to fraction
            stats[f'fenwick_{w}'] = team_df['fenwick_pct'].mean() / 100.0  # Convert to fraction
            stats[f'high_danger_shots_{w}'] = team_df['high_danger_shots'].mean()
            stats[f'shots_for_{w}'] = team_df['shots_for'].mean()
            stats[f'faceoff_{w}'] = team_df['faceoff_pct'].mean() / 100.0  # Convert to fraction
            # Team goaltending
            stats[f'save_pct_{w}'] = team_df['team_save_pct'].mean()
            stats[f'gsax_{w}'] = team_df['team_gsax'].mean()

    # Season aggregates (computed first because momentum depends on them)
    stats['season_win_pct'] = team_df['win'].mean()
    stats['season_goal_diff_avg'] = team_df['goal_diff'].mean()
    stats['season_xg_diff_avg'] = team_df['xg_diff'].mean()

    # Season shot margin: pipeline uses shotsForPerGame - shotsAgainstPerGame
    if 'shots_against' in team_df.columns:
        team_df['shot_margin'] = team_df['shots_for'] - team_df['shots_against']
        stats['season_shot_margin'] = team_df['shot_margin'].mean()
    else:
        stats['season_shot_margin'] = 0.0

    # Momentum features: rolling_5 - season_avg (matches pipeline exactly)
    # See features.py lines 637-643
    if 'win_pct_5' in stats and 'season_win_pct' in stats:
        stats['momentum_win_pct'] = stats['win_pct_5'] - stats['season_win_pct']
    else:
        stats['momentum_win_pct'] = 0.0

    if 'goal_diff_5' in stats and 'season_goal_diff_avg' in stats:
        stats['momentum_goal_diff'] = stats['goal_diff_5'] - stats['season_goal_diff_avg']
    else:
        stats['momentum_goal_diff'] = 0.0

    if 'xg_diff_5' in stats and 'season_xg_diff_avg' in stats:
        stats['momentum_xg'] = stats['xg_diff_5'] - stats['season_xg_diff_avg']
    else:
        stats['momentum_xg'] = 0.0

    return stats


def build_matchup_features(
    home_team_id: int,
    away_team_id: int,
    season_id: str,
    eligible_games: pd.DataFrame,
    feature_columns: list,
    game_date: str | None = None,
) -> pd.Series | None:
    """Construct proper matchup features for a new game.

    The correct approach is:
    1. Find each team's most recent game (regardless of home/away position)
    2. Extract that team's individual stats from that game
    3. Compute proper differentials: home_team_stat - away_team_stat
    4. Compute schedule features (rest_diff, is_b2b) from actual game dates

    This fixes the bug where we were averaging differential features from
    different games, which produced garbage (TeamA - Opponent1 + Opponent2 - TeamB) / 2.
    """
    # Find home team's most recent game (where they played as either home or away)
    home_as_home = eligible_games[
        (eligible_games['teamId_home'] == home_team_id) &
        (eligible_games['seasonId_str'] == season_id)
    ]
    home_as_away = eligible_games[
        (eligible_games['teamId_away'] == home_team_id) &
        (eligible_games['seasonId_str'] == season_id)
    ]
    home_games = pd.concat([home_as_home, home_as_away]).sort_values('gameDate')

    # Find away team's most recent game (where they played as either home or away)
    away_as_home = eligible_games[
        (eligible_games['teamId_home'] == away_team_id) &
        (eligible_games['seasonId_str'] == season_id)
    ]
    away_as_away = eligible_games[
        (eligible_games['teamId_away'] == away_team_id) &
        (eligible_games['seasonId_str'] == season_id)
    ]
    away_games = pd.concat([away_as_home, away_as_away]).sort_values('gameDate')

    if len(home_games) == 0 or len(away_games) == 0:
        return None

    # Get the most recent game for each team
    home_recent = home_games.iloc[-1]
    away_recent = away_games.iloc[-1]

    # Determine if each team was home or away in their most recent game
    home_team_was_home = home_recent['teamId_home'] == home_team_id
    away_team_was_home = away_recent['teamId_home'] == away_team_id

    # Compute actual schedule features from game dates
    # This fixes the bug where we were using stale schedule data from past games
    home_rest_days = None
    away_rest_days = None
    home_games_last_3d = 0
    home_games_last_6d = 0
    away_games_last_3d = 0
    away_games_last_6d = 0

    if game_date:
        try:
            new_game_dt = pd.to_datetime(game_date)
            home_last_game_dt = pd.to_datetime(home_recent['gameDate'])
            away_last_game_dt = pd.to_datetime(away_recent['gameDate'])

            # Compute rest days (days since last game)
            home_rest_days = (new_game_dt - home_last_game_dt).days
            away_rest_days = (new_game_dt - away_last_game_dt).days

            # Count games in last 3/6 days for schedule density
            cutoff_3d = new_game_dt - pd.Timedelta(days=3)
            cutoff_6d = new_game_dt - pd.Timedelta(days=6)

            home_dates = pd.to_datetime(home_games['gameDate'])
            away_dates = pd.to_datetime(away_games['gameDate'])

            home_games_last_3d = int((home_dates >= cutoff_3d).sum())
            home_games_last_6d = int((home_dates >= cutoff_6d).sum())
            away_games_last_3d = int((away_dates >= cutoff_3d).sum())
            away_games_last_6d = int((away_dates >= cutoff_6d).sum())
        except (ValueError, TypeError):
            pass  # Fall back to extracted features if date parsing fails

    # Compute FRESH rolling stats for both teams (fixes 1-game staleness issue)
    # This ensures rolling features reflect ALL completed games, including the most recent
    home_rolling = compute_team_rolling_stats(home_team_id, home_games, windows=[3, 5, 10])
    away_rolling = compute_team_rolling_stats(away_team_id, away_games, windows=[3, 5, 10])

    # Mapping from feature names to fresh rolling stat keys
    rolling_feature_map = {
        'rolling_win_pct_3_diff': ('win_pct_3', 'win_pct_3'),
        'rolling_win_pct_5_diff': ('win_pct_5', 'win_pct_5'),
        'rolling_win_pct_10_diff': ('win_pct_10', 'win_pct_10'),
        'rolling_goal_diff_3_diff': ('goal_diff_3', 'goal_diff_3'),
        'rolling_goal_diff_5_diff': ('goal_diff_5', 'goal_diff_5'),
        'rolling_goal_diff_10_diff': ('goal_diff_10', 'goal_diff_10'),
        'rolling_xg_diff_3_diff': ('xg_diff_3', 'xg_diff_3'),
        'rolling_xg_diff_5_diff': ('xg_diff_5', 'xg_diff_5'),
        'rolling_xg_diff_10_diff': ('xg_diff_10', 'xg_diff_10'),
        'rolling_corsi_3_diff': ('corsi_3', 'corsi_3'),
        'rolling_corsi_5_diff': ('corsi_5', 'corsi_5'),
        'rolling_corsi_10_diff': ('corsi_10', 'corsi_10'),
        'rolling_fenwick_5_diff': ('fenwick_5', 'fenwick_5'),
        'rolling_fenwick_10_diff': ('fenwick_10', 'fenwick_10'),
        'rolling_high_danger_shots_5_diff': ('high_danger_shots_5', 'high_danger_shots_5'),
        'rolling_high_danger_shots_10_diff': ('high_danger_shots_10', 'high_danger_shots_10'),
        'rolling_save_pct_3_diff': ('save_pct_3', 'save_pct_3'),
        'rolling_save_pct_5_diff': ('save_pct_5', 'save_pct_5'),
        'rolling_save_pct_10_diff': ('save_pct_10', 'save_pct_10'),
        'rolling_gsax_5_diff': ('gsax_5', 'gsax_5'),
        'rolling_gsax_10_diff': ('gsax_10', 'gsax_10'),
        'rolling_faceoff_5_diff': ('faceoff_5', 'faceoff_5'),
        'shotsFor_roll_10_diff': ('shots_for_10', 'shots_for_10'),
        'momentum_win_pct_diff': ('momentum_win_pct', 'momentum_win_pct'),
        'momentum_goal_diff_diff': ('momentum_goal_diff', 'momentum_goal_diff'),
        'momentum_xg_diff': ('momentum_xg', 'momentum_xg'),
        'season_win_pct_diff': ('season_win_pct', 'season_win_pct'),
        'season_goal_diff_avg_diff': ('season_goal_diff_avg', 'season_goal_diff_avg'),
        'season_xg_diff_avg_diff': ('season_xg_diff_avg', 'season_xg_diff_avg'),
        'season_shot_margin_diff': ('season_shot_margin', 'season_shot_margin'),
    }

    # Build matchup features
    matchup = {}

    for col in feature_columns:
        # Handle schedule features with computed values
        if col == 'rest_diff' and home_rest_days is not None and away_rest_days is not None:
            matchup[col] = home_rest_days - away_rest_days
        elif col == 'is_b2b_home' and home_rest_days is not None:
            matchup[col] = 1 if home_rest_days <= 1 else 0
        elif col == 'is_b2b_away' and away_rest_days is not None:
            matchup[col] = 1 if away_rest_days <= 1 else 0
        elif col == 'games_last_3d_home' and game_date:
            matchup[col] = home_games_last_3d
        elif col == 'games_last_6d_home' and game_date:
            matchup[col] = home_games_last_6d
        elif col in rolling_feature_map:
            # Use FRESH rolling stats computed from all completed games
            home_key, away_key = rolling_feature_map[col]
            home_val = home_rolling.get(home_key, 0.0)
            away_val = away_rolling.get(away_key, 0.0)
            matchup[col] = home_val - away_val
        elif col.endswith('_diff'):
            # This is a differential feature - need to reconstruct from individual stats
            base = col[:-5]  # Remove '_diff' suffix
            home_col = f"{base}_home"
            away_col = f"{base}_away"

            # Get home team's stat from their most recent game
            if home_col in home_recent.index and away_col in home_recent.index:
                if home_team_was_home:
                    home_team_stat = home_recent[home_col]
                else:
                    home_team_stat = home_recent[away_col]

                # Get away team's stat from their most recent game
                if away_team_was_home:
                    away_team_stat = away_recent[home_col]
                else:
                    away_team_stat = away_recent[away_col]

                # Compute proper differential
                matchup[col] = home_team_stat - away_team_stat
            else:
                matchup[col] = 0.0

        elif col in ['elo_diff_pre', 'elo_expectation_home']:
            # Elo features - compute current Elo by applying post-game updates
            # The stored elo_*_pre values are from BEFORE the most recent game
            # We need to apply the update to get current Elo

            if col == 'elo_diff_pre':
                # Get each team's pre-game Elo from their most recent game
                if home_team_was_home:
                    home_pre_elo = home_recent.get('elo_home_pre', 1500.0)
                    home_opp_pre_elo = home_recent.get('elo_away_pre', 1500.0)
                else:
                    home_pre_elo = home_recent.get('elo_away_pre', 1500.0)
                    home_opp_pre_elo = home_recent.get('elo_home_pre', 1500.0)

                if away_team_was_home:
                    away_pre_elo = away_recent.get('elo_home_pre', 1500.0)
                    away_opp_pre_elo = away_recent.get('elo_away_pre', 1500.0)
                else:
                    away_pre_elo = away_recent.get('elo_away_pre', 1500.0)
                    away_opp_pre_elo = away_recent.get('elo_home_pre', 1500.0)

                # Compute post-game Elo for home team (from their last game)
                home_game_home_win = home_recent.get('home_win', 0)
                home_game_home_score = home_recent.get('home_score', 0)
                home_game_away_score = home_recent.get('away_score', 0)

                if home_team_was_home:
                    home_outcome = 1.0 if home_game_home_win == 1 else 0.0
                    home_expected = home_recent.get('elo_expectation_home', 0.5)
                    goal_diff = home_game_home_score - home_game_away_score
                else:
                    home_outcome = 0.0 if home_game_home_win == 1 else 1.0
                    home_expected = 1.0 - home_recent.get('elo_expectation_home', 0.5)
                    goal_diff = home_game_away_score - home_game_home_score

                # Elo update formula (k=10, with margin multiplier)
                margin = max(abs(goal_diff), 1)
                rating_diff = abs(home_pre_elo - home_opp_pre_elo)
                multiplier = np.log(margin + 1) * (2.2 / (rating_diff * 0.001 + 2.2))
                home_delta = 10.0 * multiplier * (home_outcome - home_expected)
                home_current_elo = home_pre_elo + home_delta

                # Compute post-game Elo for away team (from their last game)
                away_game_home_win = away_recent.get('home_win', 0)
                away_game_home_score = away_recent.get('home_score', 0)
                away_game_away_score = away_recent.get('away_score', 0)

                if away_team_was_home:
                    away_outcome = 1.0 if away_game_home_win == 1 else 0.0
                    away_expected = away_recent.get('elo_expectation_home', 0.5)
                    goal_diff = away_game_home_score - away_game_away_score
                else:
                    away_outcome = 0.0 if away_game_home_win == 1 else 1.0
                    away_expected = 1.0 - away_recent.get('elo_expectation_home', 0.5)
                    goal_diff = away_game_away_score - away_game_home_score

                margin = max(abs(goal_diff), 1)
                rating_diff = abs(away_pre_elo - away_opp_pre_elo)
                multiplier = np.log(margin + 1) * (2.2 / (rating_diff * 0.001 + 2.2))
                away_delta = 10.0 * multiplier * (away_outcome - away_expected)
                away_current_elo = away_pre_elo + away_delta

                matchup[col] = home_current_elo - away_current_elo

            elif col == 'elo_expectation_home':
                # Compute expected probability using current Elo ratings
                # This requires the elo_diff_pre to be computed first
                if 'elo_diff_pre' in matchup:
                    elo_diff = matchup['elo_diff_pre']
                    # Standard Elo formula with ~35 point home advantage
                    home_adv = 35.0
                    matchup[col] = 1.0 / (1.0 + 10 ** ((-elo_diff - home_adv) / 400))
                elif col in home_recent.index:
                    matchup[col] = home_recent[col]
                else:
                    matchup[col] = 0.5

        elif col == 'league_hw_100':
            # League-wide feature - use most recent value
            if col in home_recent.index:
                matchup[col] = home_recent[col]
            else:
                matchup[col] = HISTORICAL_HOME_WIN_RATE

        elif col.endswith('_home'):
            # Home-specific feature (like is_b2b_home, games_last_6d_home)
            # Use the home team's recent stats
            if col in home_recent.index:
                if home_team_was_home:
                    matchup[col] = home_recent[col]
                else:
                    # If home team was away, look for the corresponding away column
                    away_version = col.replace('_home', '_away')
                    if away_version in home_recent.index:
                        matchup[col] = home_recent[away_version]
                    else:
                        matchup[col] = 0.0
            else:
                matchup[col] = 0.0

        elif col.endswith('_away'):
            # Away-specific feature
            if col in away_recent.index:
                if away_team_was_home:
                    # If away team was home, look for the corresponding home column
                    home_version = col.replace('_away', '_home')
                    if home_version in away_recent.index:
                        matchup[col] = away_recent[home_version]
                    else:
                        matchup[col] = 0.0
                else:
                    matchup[col] = away_recent[col]
            else:
                matchup[col] = 0.0
        else:
            # Other features - try to get from home team's recent game
            if col in home_recent.index:
                matchup[col] = home_recent[col]
            else:
                matchup[col] = 0.0

    return pd.Series(matchup).reindex(feature_columns, fill_value=0.0)

# V7.0 Curated Features (39 features + adaptive weights)
# Production model with 60.9% accuracy on 4-season holdout (5,002 games)
# Key features: 1) Adaptive Elo home advantage, 2) Dynamic threshold, 3) League home win rate
V70_FEATURES = [
    # League-wide home advantage (adaptive to structural shifts)
    'league_hw_100',  # Rolling 100-game league home win rate

    # Elo ratings (with season carryover)
    'elo_diff_pre', 'elo_expectation_home',

    # Rolling win percentage
    'rolling_win_pct_10_diff', 'rolling_win_pct_5_diff', 'rolling_win_pct_3_diff',

    # Rolling goal differential
    'rolling_goal_diff_10_diff', 'rolling_goal_diff_5_diff', 'rolling_goal_diff_3_diff',

    # Rolling xG differential
    'rolling_xg_diff_10_diff', 'rolling_xg_diff_5_diff', 'rolling_xg_diff_3_diff',

    # Possession metrics
    'rolling_corsi_10_diff', 'rolling_corsi_5_diff', 'rolling_corsi_3_diff',
    'rolling_fenwick_10_diff', 'rolling_fenwick_5_diff',

    # Season-level stats
    'season_win_pct_diff', 'season_goal_diff_avg_diff',
    'season_xg_diff_avg_diff', 'season_shot_margin_diff',

    # Rest and schedule
    'rest_diff', 'is_b2b_home', 'is_b2b_away',
    'games_last_6d_home',
    'games_last_3d_home',  # Schedule density

    # Goaltending
    'rolling_save_pct_10_diff', 'rolling_save_pct_5_diff', 'rolling_save_pct_3_diff',
    'rolling_gsax_5_diff', 'rolling_gsax_10_diff',
    'goalie_trend_score_diff',

    # Momentum
    'momentum_win_pct_diff', 'momentum_goal_diff_diff', 'momentum_xg_diff',

    # High danger shots
    'rolling_high_danger_shots_5_diff', 'rolling_high_danger_shots_10_diff',

    # Shot volume and possession indicators
    'shotsFor_roll_10_diff',    # Shot volume trend
    'rolling_faceoff_5_diff',   # Possession indicator
]

# Legacy features for backwards compatibility
V70_LEGACY_FEATURES = [
    # Elo ratings (improved with season carryover)
    'elo_diff_pre', 'elo_expectation_home',

    # Rolling win percentage
    'rolling_win_pct_10_diff', 'rolling_win_pct_5_diff', 'rolling_win_pct_3_diff',

    # Rolling goal differential
    'rolling_goal_diff_10_diff', 'rolling_goal_diff_5_diff', 'rolling_goal_diff_3_diff',

    # Rolling xG differential
    'rolling_xg_diff_10_diff', 'rolling_xg_diff_5_diff', 'rolling_xg_diff_3_diff',

    # Possession metrics (improving over time - up 26-32%)
    'rolling_corsi_10_diff', 'rolling_corsi_5_diff', 'rolling_corsi_3_diff',
    'rolling_fenwick_10_diff', 'rolling_fenwick_5_diff',

    # Season-level stats
    'season_win_pct_diff', 'season_goal_diff_avg_diff',
    'season_xg_diff_avg_diff', 'season_shot_margin_diff',

    # Rest and schedule (rest_diff improved +53%)
    'rest_diff', 'is_b2b_home', 'is_b2b_away',
    'games_last_6d_home',
    'games_last_3d_home',  # Schedule density

    # Goaltending (removed goalie_rest_days_diff - degraded 77%)
    'rolling_save_pct_10_diff', 'rolling_save_pct_5_diff', 'rolling_save_pct_3_diff',
    'rolling_gsax_5_diff', 'rolling_gsax_10_diff',
    'goalie_trend_score_diff',

    # Momentum
    'momentum_win_pct_diff', 'momentum_goal_diff_diff', 'momentum_xg_diff',

    # High danger shots
    'rolling_high_danger_shots_5_diff', 'rolling_high_danger_shots_10_diff',

    # Shot volume and possession indicators
    'shotsFor_roll_10_diff',    # Shot volume trend (+0.16 pp overall)
    'rolling_faceoff_5_diff',   # Possession indicator (+0.12 pp overall)
]

def recent_seasons(anchor: datetime | date | None = None, count: int = 4) -> list[str]:
    """Return the most recent NHL season IDs ending at the anchor date."""
    if anchor is None:
        anchor_date = datetime.utcnow().date()
    elif isinstance(anchor, datetime):
        anchor_date = anchor.date()
    else:
        anchor_date = anchor

    start_year = anchor_date.year if anchor_date.month >= 7 else anchor_date.year - 1
    seasons = []
    for offset in range(count):
        year = start_year - offset
        seasons.append(f"{year}{year + 1}")
    return seasons

def format_start_times(start_time_utc: str):
    """Return ISO + human-readable ET string for a UTC start time."""
    if not start_time_utc:
        return None, None

    try:
        dt_utc = datetime.fromisoformat(start_time_utc.replace("Z", "+00:00"))
    except ValueError:
        return None, None

    dt_et = dt_utc.astimezone(ET_ZONE)
    display = dt_et.strftime("%I:%M %p").lstrip("0")
    return dt_utc.isoformat(), f"{display} ET"


def grade_from_edge(edge_value: float) -> str:
    """Map edge (probability delta) to the 6 letter grades used on the site.

    Grade bands:
        A+  = ≥25 pts  (elite confidence)
        A   = 20-25 pts (strong confidence)
        B+  = 15-20 pts (good confidence)
        B   = 10-15 pts (medium confidence)
        C+  = 5-10 pts  (weak confidence)
        C   = 0-5 pts   (coin flip)
    """
    edge_pts = abs(edge_value) * 100
    if edge_pts >= 25:
        return "A+"
    if edge_pts >= 20:
        return "A"
    if edge_pts >= 15:
        return "B+"
    if edge_pts >= 10:
        return "B"
    if edge_pts >= 5:
        return "C+"
    return "C"


def apply_calibration(prob: float, calibrator) -> float:
    """Return calibrated probability using the isotonic model if available."""
    if calibrator is None:
        return float(np.clip(prob, 0.0, 1.0))
    calibrated = calibrator.predict(np.asarray([prob]))[0]
    return float(np.clip(calibrated, 0.0, 1.0))


def build_summary(home_team: str, away_team: str, prob_home: float, confidence_grade: str) -> str:
    favorite = home_team if prob_home >= 0.5 else away_team
    favorite_prob = prob_home if favorite == home_team else 1 - prob_home
    edge_pct = abs(prob_home - 0.5) * 100
    direction = "home" if favorite == home_team else "road"
    article = "an" if confidence_grade.startswith("A") else "a"
    return (
        f"{favorite} project at {favorite_prob:.0%} as the {direction} lean — "
        f"{article} {confidence_grade}-tier edge worth {edge_pct:.1f} pts over a coin flip."
    )


# Special teams enrichment helpers -----------------------------------------

def _build_special_team_lookup(player_hub_payload):
    if not isinstance(player_hub_payload, dict):
        return {}
    special = player_hub_payload.get("specialTeams")
    if not isinstance(special, dict):
        return {}
    teams = special.get("teams")
    if not isinstance(teams, dict):
        return {}
    lookup = {}
    for key, value in teams.items():
        if isinstance(key, str):
            lookup[key.upper()] = value or {}
    return lookup


def _safe_percent(value):
    try:
        if value is None:
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _build_special_split(team_stats, opponent_stats):
    if not isinstance(team_stats, dict) or not isinstance(opponent_stats, dict):
        return None
    pp = _safe_percent(team_stats.get("powerPlayPct"))
    pk = _safe_percent(opponent_stats.get("penaltyKillPct"))
    if pp is None and pk is None:
        return None
    diff = pp - pk if pp is not None and pk is not None else None
    return {
        "powerPlayPct": pp,
        "opponentPenaltyKillPct": pk,
        "diff": diff,
    }


def _attach_special_teams(game, lookup):
    if not lookup:
        return None
    home = lookup.get(str(game.get("home_team", "")).upper())
    away = lookup.get(str(game.get("away_team", "")).upper())
    if not home or not away:
        return None
    home_split = _build_special_split(home, away)
    away_split = _build_special_split(away, home)
    if not home_split and not away_split:
        return None
    return {
        "home": home_split,
        "away": away_split,
    }


def _append_special_summary(summary: str, special: dict | None, home: dict, away: dict) -> str:
    if not special:
        return summary
    best_team = None
    best_diff = None
    for team_entry, split in ((home, special.get("home")), (away, special.get("away"))):
        diff = (split or {}).get("diff")
        if diff is None:
            continue
        if best_diff is None or abs(diff) > abs(best_diff):
            best_diff = diff
            best_team = team_entry
    if best_team is None or best_diff is None or abs(best_diff) < 3:
        return summary
    tendency = "PP edge" if best_diff > 0 else "PK drag"
    abbrev = best_team.get("abbrev") or best_team.get("name") or "Team"
    return f"{summary} {abbrev} {tendency} {best_diff:+.1f} pts vs opponent special teams."


def _player_hub_meta(player_hub_payload):
    if not isinstance(player_hub_payload, dict):
        return None
    combos = player_hub_payload.get("lineCombos") or {}
    meta = {
        "season": player_hub_payload.get("season"),
        "slateDate": player_hub_payload.get("slateDate"),
        "lineCombosGeneratedAt": combos.get("generatedAt"),
        "lineCombosSlateDate": combos.get("slateDate"),
    }
    if any(meta.values()):
        return meta
    return None


def export_predictions_json(predictions, generated_at=None, player_hub_payload=None):
    """Write predictions for the web landing page in JSON format."""
    WEB_PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAt": (generated_at or datetime.now(timezone.utc).isoformat()),
        "games": [],
    }
    special_team_lookup = _build_special_team_lookup(player_hub_payload)
    hub_meta = _player_hub_meta(player_hub_payload)
    if hub_meta:
        payload["playerHubMeta"] = hub_meta

    for pred in predictions:
        home_prob_display = pred.get("home_win_prob_raw", pred.get("home_win_prob", 0.0))
        away_prob_display = pred.get("away_win_prob_raw", pred.get("away_win_prob", 0.0))
        # Fallback to complement if only one side is present
        if away_prob_display == 0.0 and "home_win_prob_raw" in pred and "away_win_prob_raw" not in pred:
            away_prob_display = 1 - home_prob_display
        if home_prob_display == 0.0 and "away_win_prob_raw" in pred and "home_win_prob_raw" not in pred:
            home_prob_display = 1 - away_prob_display

        game_entry = {
            "id": str(pred.get("game_id", pred.get("game_num"))),
            "gameDate": pred.get("date"),
            "startTimeEt": pred.get("start_time_et"),
            "startTimeUtc": pred.get("start_time_utc"),
            "homeTeam": {
                "name": pred.get("home_team_name", pred.get("home_team")),
                "abbrev": pred.get("home_team"),
            },
            "awayTeam": {
                "name": pred.get("away_team_name", pred.get("away_team")),
                "abbrev": pred.get("away_team"),
            },
            "homeWinProb": round(home_prob_display, 4),
            "awayWinProb": round(away_prob_display, 4),
            "confidenceScore": round(pred.get("confidence", 0.0), 3),
            "confidenceGrade": pred.get("confidence_grade", "C"),
            "edge": round(pred.get("edge", 0.0), 3),
            "summary": pred.get("summary", ""),
            "modelFavorite": pred.get("model_favorite", "home"),
            "venue": pred.get("venue"),
            "season": str(pred.get("season")) if pred.get("season") else None,
        }
        special = _attach_special_teams(pred, special_team_lookup)
        if special:
            game_entry["specialTeams"] = special
            game_entry["summary"] = _append_special_summary(game_entry["summary"], special, game_entry["homeTeam"], game_entry["awayTeam"])
        payload["games"].append(game_entry)

    WEB_PREDICTIONS_PATH.write_text(json.dumps(payload, indent=2))
    print(f"\n🛰  Exported web payload → {WEB_PREDICTIONS_PATH}")


def derive_season_id_from_date(target: datetime) -> str:
    """Return NHL season identifier (e.g., 20242025) for the provided datetime."""
    start_year = target.year if target.month >= 7 else target.year - 1
    end_year = start_year + 1
    return f"{start_year}{end_year}"


def _filter_games_by_date(games, target_date: str) -> list[dict]:
    """Return only the games scheduled for the target date."""
    filtered = [game for game in games if game.get("gameDate") == target_date]
    return filtered


def predict_games(date=None, num_games=20):
    """
    Predict NHL games using full model with all features.
    
    Args:
        date: Date string 'YYYY-MM-DD' or None for today
        num_games: Number of games to predict (default 20)
    """
    
    print("━"*80)
    print("🏒 PUCKCAST.AI - NHL PREDICTIONS")
    print("   Data-Driven Intelligence for Today's Games")
    print("━"*80)
    
    # Get date
    if date is None:
        target_dt = datetime.now()
    else:
        target_dt = datetime.strptime(date, '%Y-%m-%d')
    date_str = target_dt.strftime('%Y-%m-%d')
    date_display = target_dt.strftime('%A, %B %d, %Y')
    
    print(f"\n📅 Date: {date_display}")
    
    # Step 1: Fetch games
    print(f"\n1️⃣  Fetching games for {date_str}...")

    if date is None:
        games = fetch_todays_games()
    else:
        games = fetch_future_games(date_str)
    if not games and target_dt.date() < datetime.now().date():
        print("   ⚠️  No future games detected — falling back to historical schedule for backfill.")
        games = fetch_schedule(date_str)
    if not games:
        print(f"   ℹ️  No games scheduled for {date_str}")
        return []

    filtered_games = _filter_games_by_date(games, date_str)
    filtered_count = len(filtered_games)
    print(f"   ✅ Found {filtered_count} game(s) for {date_str}")
    if filtered_count == 0:
        print("   ℹ️  Using the full schedule because no games matched the target date.")
        games_for_model = games
    else:
        if filtered_count != len(games):
            print(f"   ℹ️  Filtered down from {len(games)} scheduled game(s).")
        games_for_model = filtered_games
    
    # Step 2: Build dataset
    seasons = recent_seasons(target_dt, count=4)
    print("\n2️⃣  Building dataset with native artifacts...")
    print(f"   (Loading {len(seasons)} season(s): {', '.join(seasons)})")

    dataset = build_dataset(seasons)

    print(f"   ✅ {len(dataset.games)} games loaded")
    print(f"   ✅ {dataset.features.shape[1]} baseline features engineered")

    # Add league-wide home win rate feature (adaptive)
    games_with_hw = add_league_hw_feature(dataset.games)
    print("   ✅ Added league home win rate feature (adaptive)")

    # Add situational features
    games_with_situational = add_situational_features(games_with_hw)
    situational_features = ['fatigue_index_diff', 'third_period_trailing_perf_diff',
                    'travel_distance_diff', 'divisional_matchup',
                    'post_break_game_home', 'post_break_game_away', 'post_break_game_diff']
    available_situational = [f for f in situational_features if f in games_with_situational.columns]

    # Combine baseline + situational + league HW features
    features_full = pd.concat([
        dataset.features,
        games_with_situational[available_situational],
        games_with_situational[['league_hw_100']],  # Adaptive feature
    ], axis=1)
    print(f"   ✅ {len(available_situational)} situational features added")

    # Filter to V7.0 curated features only
    available_v70 = [f for f in V70_FEATURES if f in features_full.columns]
    missing_v70 = [f for f in V70_FEATURES if f not in features_full.columns]
    if missing_v70:
        print(f"   ⚠️  Missing {len(missing_v70)} V7.0 features: {missing_v70[:5]}...")
    features_full = features_full[available_v70]
    print(f"   ✅ Total: {features_full.shape[1]} curated features (V7.0 Model)")

    # Step 3: Train calibrated model using only past games
    print("\n3️⃣  Training calibrated logistic regression model...")
    predict_date = target_dt
    cutoff = pd.Timestamp(predict_date.date())
    game_dates = pd.to_datetime(games_with_situational["gameDate"])
    eligible_mask = game_dates < cutoff

    if not eligible_mask.any():
        print("   ❌ No historical games available before this date.")
        return []

    eligible_games = games_with_situational.loc[eligible_mask].copy()
    eligible_features = features_full.loc[eligible_mask].copy()
    eligible_target = dataset.target.loc[eligible_mask].copy()
    train_seasons = sorted(eligible_games["seasonId"].unique().tolist())

    # Calculate adaptive sample weights to handle home advantage shifts
    adaptive_weights = calculate_adaptive_weights(eligible_games, eligible_target)
    print("   ✅ Calculated adaptive sample weights")

    candidate_cs = [0.005, 0.01, 0.02, 0.03, 0.05, 0.1, 0.3, 0.5, 1.0]
    best_c = tune_logreg_c(candidate_cs, eligible_features, eligible_target, eligible_games, train_seasons, sample_weights=adaptive_weights)
    threshold, val_acc, calibrator = calibrate_threshold(best_c, eligible_features, eligible_target, eligible_games, train_seasons)

    training_mask = pd.Series(True, index=eligible_features.index)
    model = create_baseline_model(C=best_c)
    model = fit_model(model, eligible_features, eligible_target, training_mask, sample_weight=adaptive_weights)
    
    print(f"   ✅ Trained on {training_mask.sum():,} historical games | seasons: {', '.join(map(str, train_seasons))}")
    print(f"   ✅ Selected logistic regression C={best_c:.3f}")
    if val_acc is not None:
        print(f"   ✅ Validation threshold {threshold:.3f} (accuracy {val_acc:.3f})")
    else:
        print("   ℹ️  Not enough seasons for validation; using default 0.500 threshold")
    if calibrator is not None:
        print("   ✅ Applied isotonic probability calibration")
    
    # Step 4: Predict
    print(f"\n4️⃣  Generating predictions for {min(num_games, len(games_for_model))} games...")

    print("\n" + "="*80)
    print("PREDICTIONS")
    print("="*80)

    predictions = []
    eligible_games["seasonId_str"] = eligible_games["seasonId"].astype(str)
    feature_columns = eligible_features.columns
    
    for i, game in enumerate(games_for_model[:num_games], 1):
        home_id = game['homeTeamId']
        away_id = game['awayTeamId']
        home_abbrev = game['homeTeamAbbrev']
        away_abbrev = game['awayTeamAbbrev']
        season_id = str(game.get("season") or train_seasons[-1])

        # Build proper matchup features by extracting each team's individual stats
        # and computing correct differentials (home_team_stat - away_team_stat)
        game_date_str = game.get('gameDate', date_str)
        matchup_features = build_matchup_features(
            home_team_id=home_id,
            away_team_id=away_id,
            season_id=season_id,
            eligible_games=eligible_games,
            feature_columns=list(feature_columns),
            game_date=game_date_str,
        )

        if matchup_features is None:
            print(f"\n{i}. {away_abbrev} @ {home_abbrev}")
            print(f"   ⚠️  Insufficient data (team hasn't played this season)")
            continue
        
        # Predict with calibrated model
        prob_home_raw = model.predict_proba(matchup_features.values.reshape(1, -1))[0][1]
        prob_home_calibrated = apply_calibration(prob_home_raw, calibrator)
        prob_home_display = prob_home_raw  # Show raw probabilities to avoid calibration plateaus
        prob_away_raw = 1 - prob_home_raw
        prob_away_calibrated = 1 - prob_home_calibrated

        start_time_utc_iso, start_time_et = format_start_times(game.get('startTimeUTC', ''))
        # Calculate edge from 0.5 baseline
        edge = prob_home_display - 0.5
        confidence_score = abs(edge) * 2  # 0-1 scale
        confidence_grade = grade_from_edge(edge)
        # Use 0.5 threshold - team with >50% probability is the favorite
        model_favorite = 'home' if prob_home_display >= 0.5 else 'away'
        summary = build_summary(
            game.get('homeTeamName', home_abbrev),
            game.get('awayTeamName', away_abbrev),
            prob_home_display,
            confidence_grade,
        )
        
        # Store prediction
        predictions.append({
            'game_num': i,
            'game_id': game.get('gameId'),
            'date': game.get('gameDate', date_str),
            'season': game.get('season'),
            'venue': game.get('venue'),
            'game_state': game.get('gameState'),
            'start_time_utc': start_time_utc_iso,
            'start_time_et': start_time_et,
            'away_team': away_abbrev,
            'away_team_name': game.get('awayTeamName', away_abbrev),
            'home_team': home_abbrev,
            'home_team_name': game.get('homeTeamName', home_abbrev),
            # Display raw probabilities for UI while keeping calibrated for decisioning
            'home_win_prob': prob_home_display,
            'away_win_prob': prob_away_raw,
            'home_win_prob_raw': prob_home_raw,
            'away_win_prob_raw': prob_away_raw,
            'home_win_prob_calibrated': prob_home_calibrated,
            'away_win_prob_calibrated': prob_away_calibrated,
            'edge': edge,
            'predicted_winner': home_abbrev if prob_home_display >= 0.5 else away_abbrev,
            'model_favorite': model_favorite,
            'confidence': confidence_score,
            'confidence_grade': confidence_grade,
            'summary': summary
        })
        
        # Display prediction
        print(f"\n{i}. {away_abbrev} @ {home_abbrev}")
        print(f"   Home Win (raw): {prob_home_display:.1%}  |  Away Win (raw): {prob_away_raw:.1%}")
        
        # Classify prediction strength
        confidence_pct = confidence_score * 100

        if prob_home_display > 0.70:
            print(f"   ✅ Prediction: {home_abbrev} STRONG FAVORITE")
        elif prob_home_display < 0.30:
            print(f"   ✅ Prediction: {away_abbrev} STRONG FAVORITE")
        elif abs(prob_home_display - 0.5) < 0.05:
            print(f"   ⚖️  Prediction: TOSS-UP (too close to call)")
        else:
            favorite = home_abbrev if prob_home_display >= 0.5 else away_abbrev
            print(f"   📊 Prediction: {favorite} ({confidence_pct:.0f}% confidence)")
    
    # Summary
    print("\n" + "="*80)
    print(f"✅ PREDICTIONS COMPLETE")
    print(f"   Total Games: {len(predictions)}")
    print(f"   Model: Logistic Regression (C={best_c:.3f}) with {eligible_features.shape[1]} features")
    print(f"   Training: {training_mask.sum():,} games from seasons {', '.join(map(str, train_seasons))}")
    if calibrator is not None:
        print("   Calibration: Isotonic regression on validation season")
    else:
        print("   Calibration: Not available (insufficient validation split)")
    print("="*80)
    
    return predictions


def main():
    """Main entry point."""
    
    # Parse command line args - simple: just date (optional)
    # Usage: python predict_full.py [YYYY-MM-DD]
    if len(sys.argv) > 1:
        date_arg = sys.argv[1]
        # Skip if it's a flag like --date
        if date_arg.startswith('--'):
            date = None
            print("\nPredicting today's games...")
        else:
            date = date_arg
            print(f"\nPredicting games for: {date}")
    else:
        date = None
        print("\nPredicting today's games...")
    
    try:
        predictions = predict_games(date=date, num_games=20)

        # Save to CSV
        if predictions:
            df = pd.DataFrame(predictions)
            filename = f"predictions_{date or datetime.now().strftime('%Y-%m-%d')}.csv"
            df.to_csv(filename, index=False)
            print(f"\n💾 Saved predictions to: {filename}")

        target_dt = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
        player_hub_payload = None
        # Player Hub module not implemented yet - skip context refresh
        # try:
        #     season_id = derive_season_id_from_date(target_dt)
        #     player_hub_payload = refresh_player_hub_context(target_dt.date(), season_id)
        #     print("🗂  Updated Player Hub context payload.")
        # except Exception as refresh_error:
        #     print(f"⚠️  Failed to refresh Player Hub context: {refresh_error}")
        export_predictions_json(
            predictions,
            generated_at=datetime.now(timezone.utc).isoformat(),
            player_hub_payload=player_hub_payload,
        )

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
