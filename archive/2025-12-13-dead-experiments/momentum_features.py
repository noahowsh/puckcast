"""
V7.0 Momentum-Weighted Rolling Window Features

Expected Impact: +0.2-0.3% accuracy

Weights recent games more heavily to capture hot/cold streaks better than
simple averages. Top features like rolling_goal_diff and rolling_high_danger_shots
get momentum-weighted versions.

Default weighting: [0.4, 0.3, 0.2, 0.1] for last 4 games
- Most recent game: 40% weight
- 2nd most recent: 30% weight
- 3rd most recent: 20% weight
- 4th most recent: 10% weight
"""

import pandas as pd
import numpy as np
from typing import List, Optional
import logging

LOGGER = logging.getLogger(__name__)


# Default momentum weights (most recent to oldest)
DEFAULT_MOMENTUM_WEIGHTS = [0.4, 0.3, 0.2, 0.1]


def compute_momentum_weighted_avg(
    values: List[float],
    weights: Optional[List[float]] = None
) -> float:
    """
    Compute weighted average with recent games weighted more heavily.

    Args:
        values: List of values (most recent last)
        weights: Optional weight vector (most recent first)
                 Default: [0.4, 0.3, 0.2, 0.1]

    Returns:
        Weighted average favoring recent performance
    """
    if weights is None:
        weights = DEFAULT_MOMENTUM_WEIGHTS

    if len(values) == 0:
        return 0.0

    # Pad with zeros if not enough history
    if len(values) < len(weights):
        values = [0.0] * (len(weights) - len(values)) + values

    # Take last N values matching weight vector
    recent_values = values[-len(weights):]

    # Reverse values so most recent is first (matches weight order)
    recent_values = list(reversed(recent_values))

    # Compute weighted average
    weighted_sum = sum(v * w for v, w in zip(recent_values, weights))

    return weighted_sum


def add_momentum_features(games_df: pd.DataFrame) -> pd.DataFrame:
    """
    Add momentum-weighted rolling features to game logs.

    Adds momentum versions of key metrics:
    - momentum_xg_for_4: xG for (momentum-weighted last 4)
    - momentum_xg_against_4: xG against (momentum-weighted last 4)
    - momentum_goal_diff_4: Goal differential (momentum-weighted last 4)
    - momentum_high_danger_shots_4: High-danger shots (momentum-weighted last 4)
    - momentum_win_pct_4: Win % (momentum-weighted last 4)

    Args:
        games_df: Team game logs with gameDate, team columns

    Returns:
        Enhanced DataFrame with momentum features
    """
    if games_df.empty:
        return games_df

    games_df = games_df.copy()

    # Initialize momentum columns
    momentum_features = [
        'momentum_xg_for_4',
        'momentum_xg_against_4',
        'momentum_goal_diff_4',
        'momentum_high_danger_shots_4',
        'momentum_win_pct_4'
    ]

    for feature in momentum_features:
        games_df[feature] = 0.0

    # Process each team separately
    for team in games_df['team'].unique():
        team_mask = games_df['team'] == team
        team_games = games_df[team_mask].sort_values('gameDate').copy()

        # Skip if not enough games
        if len(team_games) == 0:
            continue

        # xG for
        if 'xGoalsFor' in team_games.columns:
            xg_values = team_games['xGoalsFor'].fillna(0).tolist()
            momentum_xg = [
                compute_momentum_weighted_avg(xg_values[:i+1])
                for i in range(len(xg_values))
            ]
            games_df.loc[team_games.index, 'momentum_xg_for_4'] = momentum_xg

        # xG against
        if 'xGoalsAgainst' in team_games.columns:
            xga_values = team_games['xGoalsAgainst'].fillna(0).tolist()
            momentum_xga = [
                compute_momentum_weighted_avg(xga_values[:i+1])
                for i in range(len(xga_values))
            ]
            games_df.loc[team_games.index, 'momentum_xg_against_4'] = momentum_xga

        # Goal differential
        if 'goalsFor' in team_games.columns and 'goalsAgainst' in team_games.columns:
            gd_values = (
                team_games['goalsFor'].fillna(0) - team_games['goalsAgainst'].fillna(0)
            ).tolist()
            momentum_gd = [
                compute_momentum_weighted_avg(gd_values[:i+1])
                for i in range(len(gd_values))
            ]
            games_df.loc[team_games.index, 'momentum_goal_diff_4'] = momentum_gd

        # High-danger shots
        if 'high_danger_shotsFor' in team_games.columns:
            hd_values = team_games['high_danger_shotsFor'].fillna(0).tolist()
            momentum_hd = [
                compute_momentum_weighted_avg(hd_values[:i+1])
                for i in range(len(hd_values))
            ]
            games_df.loc[team_games.index, 'momentum_high_danger_shots_4'] = momentum_hd

        # Win percentage (1 for win, 0 for loss)
        if 'won' in team_games.columns:
            win_values = team_games['won'].fillna(0).tolist()
            momentum_win = [
                compute_momentum_weighted_avg(win_values[:i+1])
                for i in range(len(win_values))
            ]
            games_df.loc[team_games.index, 'momentum_win_pct_4'] = momentum_win

    LOGGER.info(f"Added {len(momentum_features)} momentum-weighted features")

    return games_df


def create_momentum_matchup_features(games: pd.DataFrame) -> pd.DataFrame:
    """
    Create momentum-based differential features for home vs away matchups.

    Adds:
    - momentum_xg_for_diff
    - momentum_xg_against_diff
    - momentum_goal_diff_diff
    - momentum_high_danger_diff
    - momentum_win_pct_diff

    Args:
        games: DataFrame with home/away momentum features

    Returns:
        DataFrame with momentum differential features
    """
    games = games.copy()

    # Map momentum features to home/away
    momentum_base_features = [
        'momentum_xg_for_4',
        'momentum_xg_against_4',
        'momentum_goal_diff_4',
        'momentum_high_danger_shots_4',
        'momentum_win_pct_4'
    ]

    for base_feature in momentum_base_features:
        home_col = f"{base_feature}_home"
        away_col = f"{base_feature}_away"
        diff_col = base_feature.replace('_4', '_diff')

        if home_col in games.columns and away_col in games.columns:
            games[diff_col] = games[home_col] - games[away_col]

    momentum_diff_count = len([c for c in games.columns if 'momentum_' in c and '_diff' in c])
    LOGGER.info(f"Created {momentum_diff_count} momentum differential features")

    return games


__all__ = [
    'compute_momentum_weighted_avg',
    'add_momentum_features',
    'create_momentum_matchup_features',
]
