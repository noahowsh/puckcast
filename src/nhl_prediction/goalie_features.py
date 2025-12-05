"""Individual starting goalie features for game prediction.

V7.0 ENHANCEMENT: Individual goalie tracking replaces team-level metrics.
This is the #1 priority improvement, expected +0.8-1.2% accuracy.

Features individual goalie stats:
- Goals Saved Above Expected (GSA) - recent form
- Save percentage by shot type (overall, high-danger, rush)
- Performance vs specific opponents
- Recent form (last 3/5/10 starts)

Data source: GoalieTracker from NHL API play-by-play
"""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional
from pathlib import Path

import pandas as pd
import numpy as np

# Import V7.0 goalie tracker
try:
    from .goalie_tracker import GoalieTracker, build_goalie_database
except ImportError:
    # Fallback if goalie_tracker not available
    GoalieTracker = None
    build_goalie_database = None

LOGGER = logging.getLogger(__name__)


def enhance_with_goalie_features(
    team_logs: pd.DataFrame,
    goalie_tracker: Optional[GoalieTracker] = None,
    starting_goalies: Optional[Dict] = None
) -> pd.DataFrame:
    """
    V7.0: Add individual goalie features to team logs.

    If goalie_tracker is provided, adds individual goalie stats.
    Otherwise, falls back to team-level metrics.

    Args:
        team_logs: DataFrame with team-level game logs
        goalie_tracker: Optional GoalieTracker with individual stats
        starting_goalies: Optional dict mapping {game_date: {team: goalie_id}}

    Returns:
        Enhanced DataFrame with goalie features
    """
    # V7.0: Individual goalie features
    if goalie_tracker is not None and starting_goalies is not None:
        LOGGER.info("V7.0: Adding individual goalie features")
        return _add_individual_goalie_features(team_logs, goalie_tracker, starting_goalies)

    # V6.3 fallback: Team-level only
    LOGGER.info("Using team-level goalie features (V6.3 mode)")
    return team_logs


def _add_individual_goalie_features(
    team_logs: pd.DataFrame,
    tracker: GoalieTracker,
    starting_goalies: Dict
) -> pd.DataFrame:
    """
    Add individual starting goalie features.

    New features added:
    - goalie_gsa_last5_home/away: GSA avg over last 5 starts
    - goalie_save_pct_last5_home/away: Overall save %
    - goalie_hd_save_pct_last5_home/away: High-danger save %
    - goalie_vs_opp_save_pct_home/away: Historical vs opponent
    - goalie_gsa_diff: Matchup quality (home GSA - away GSA)
    - goalie_quality_diff: Save % differential

    Args:
        team_logs: Team game logs
        tracker: GoalieTracker with goalie history
        starting_goalies: Starting goalie assignments

    Returns:
        DataFrame with individual goalie features
    """
    # Initialize new columns
    goalie_features = [
        'goalie_gsa_last5_home', 'goalie_gsa_last5_away',
        'goalie_save_pct_last5_home', 'goalie_save_pct_last5_away',
        'goalie_hd_save_pct_last5_home', 'goalie_hd_save_pct_last5_away',
        'goalie_vs_opp_save_pct_home', 'goalie_vs_opp_save_pct_away',
        'goalie_games_played_last5_home', 'goalie_games_played_last5_away'
    ]

    for feature in goalie_features:
        team_logs[feature] = 0.0

    features_added = 0

    # Process each game
    for idx, row in team_logs.iterrows():
        game_date = str(row.get('gameDate', ''))
        home_team = str(row.get('teamAbbrev_home', ''))
        away_team = str(row.get('teamAbbrev_away', ''))

        # Get starting goalies for this game
        game_starters = starting_goalies.get(game_date, {})
        home_goalie_id = game_starters.get(home_team)
        away_goalie_id = game_starters.get(away_team)

        # Home goalie features
        if home_goalie_id:
            home_recent = tracker.get_recent_form(home_goalie_id, game_date, last_n_games=5)
            team_logs.at[idx, 'goalie_gsa_last5_home'] = home_recent.get('gsa_avg', 0.0)
            team_logs.at[idx, 'goalie_save_pct_last5_home'] = home_recent.get('save_pct', 0.910)
            team_logs.at[idx, 'goalie_hd_save_pct_last5_home'] = home_recent.get('hd_save_pct', 0.850)
            team_logs.at[idx, 'goalie_games_played_last5_home'] = home_recent.get('games_played', 0)

            # vs opponent
            home_vs_away = tracker.get_vs_opponent(home_goalie_id, away_team, game_date)
            team_logs.at[idx, 'goalie_vs_opp_save_pct_home'] = home_vs_away.get('save_pct', 0.910)

            features_added += 1

        # Away goalie features
        if away_goalie_id:
            away_recent = tracker.get_recent_form(away_goalie_id, game_date, last_n_games=5)
            team_logs.at[idx, 'goalie_gsa_last5_away'] = away_recent.get('gsa_avg', 0.0)
            team_logs.at[idx, 'goalie_save_pct_last5_away'] = away_recent.get('save_pct', 0.910)
            team_logs.at[idx, 'goalie_hd_save_pct_last5_away'] = away_recent.get('hd_save_pct', 0.850)
            team_logs.at[idx, 'goalie_games_played_last5_away'] = away_recent.get('games_played', 0)

            # vs opponent
            away_vs_home = tracker.get_vs_opponent(away_goalie_id, home_team, game_date)
            team_logs.at[idx, 'goalie_vs_opp_save_pct_away'] = away_vs_home.get('save_pct', 0.910)

            features_added += 1

    # Add differential features
    team_logs['goalie_gsa_diff'] = (
        team_logs['goalie_gsa_last5_home'] - team_logs['goalie_gsa_last5_away']
    )
    team_logs['goalie_quality_diff'] = (
        team_logs['goalie_save_pct_last5_home'] - team_logs['goalie_save_pct_last5_away']
    )
    team_logs['goalie_hd_quality_diff'] = (
        team_logs['goalie_hd_save_pct_last5_home'] - team_logs['goalie_hd_save_pct_last5_away']
    )

    LOGGER.info(f"Added individual goalie features for {features_added} goalie assignments")
    LOGGER.info(f"Total goalie features: {len([c for c in team_logs.columns if 'goalie' in c.lower()])}")

    return team_logs


def create_goalie_matchup_features(games: pd.DataFrame) -> pd.DataFrame:
    """
    Create goalie vs goalie matchup features for prediction.

    Builds differential features between opposing goalies.

    Args:
        games: DataFrame with home/away goalie features

    Returns:
        DataFrame with matchup features added
    """
    games = games.copy()

    # Goalie quality differential (home - away)
    if 'team_save_pct_home' in games.columns and 'team_save_pct_away' in games.columns:
        games['goalie_save_pct_diff'] = (
            games['team_save_pct_home'] - games['team_save_pct_away']
        )

    if 'team_gsax_per_60_home' in games.columns and 'team_gsax_per_60_away' in games.columns:
        games['goalie_gsax_diff'] = (
            games['team_gsax_per_60_home'] - games['team_gsax_per_60_away']
        )

    LOGGER.info(f"Created {sum(1 for c in games.columns if 'goalie' in c and 'diff' in c)} goalie matchup features")

    return games


__all__ = [
    'enhance_with_goalie_features',
    'create_goalie_matchup_features',
]
