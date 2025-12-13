"""
V7.5 PDO Regression Features

PDO (Percentage Derivative of Offense) measures luck and sustainability.

WHAT IS PDO:
- PDO = Shooting% + Save% (in percentage points)
- Example: 10% shooting + 90% save = PDO of 100
- League average is ~100
- Teams with extreme PDO (>102 or <98) tend to regress to mean
- Proven predictive signal in hockey analytics

WHY PDO MATTERS:
- Different signal than goal differential (measures HOW you score, not just IF you score)
- High PDO = unsustainably lucky (likely to regress down)
- Low PDO = unlucky (likely to improve)
- Captures variance in shooting/save luck independent of shot quality

FEATURES CREATED (4):
1. pdo_rolling_10 - PDO from last 10 games
2. pdo_deviation - Distance from 100 (higher = more extreme, more regression)
3. shooting_pct_sustainability - Shooting% vs xG (luck in finishing)
4. save_pct_sustainability - Save% vs xG against (luck in goaltending)

Expected improvement: +0.2 to +0.4pp accuracy
"""

from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import numpy as np

LOGGER = logging.getLogger(__name__)


def add_pdo_features(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add all 4 V7.5 PDO regression features.

    Features added:
    1. pdo_rolling_10 - Rolling 10-game PDO
    2. pdo_deviation - Abs distance from 100
    3. shooting_pct_sustainability - Shooting% vs xG
    4. save_pct_sustainability - Save% vs xG against

    Args:
        games: DataFrame with game data

    Returns:
        DataFrame with PDO features added
    """
    games = games.copy()

    LOGGER.info("Adding V7.5 PDO regression features...")

    # Step 1: Calculate rolling PDO
    LOGGER.info("  [1/4] Computing rolling 10-game PDO...")
    games = _add_pdo_rolling(games)

    # Step 2: PDO deviation from 100
    LOGGER.info("  [2/4] Computing PDO deviation from 100...")
    games = _add_pdo_deviation(games)

    # Step 3: Shooting sustainability
    LOGGER.info("  [3/4] Computing shooting% sustainability...")
    games = _add_shooting_sustainability(games)

    # Step 4: Save sustainability
    LOGGER.info("  [4/4] Computing save% sustainability...")
    games = _add_save_sustainability(games)

    pdo_cols = [c for c in games.columns if 'pdo' in c or 'sustainability' in c]
    LOGGER.info(f"✓ Added {len(pdo_cols)} V7.5 PDO features")

    return games


def _add_pdo_rolling(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add rolling 10-game PDO for each team.

    PDO = Shooting% + Save%
    - Shooting% = Goals For / Shots For
    - Save% = (Shots Against - Goals Against) / Shots Against
    """
    games = games.sort_values('gameDate')

    # Initialize columns
    for side in ['home', 'away']:
        games[f'pdo_rolling_10_{side}'] = 100.0  # Default to league average

    # Calculate PDO for each team
    for team_side in ['home', 'away']:
        team_col = f'teamId_{team_side}'

        for team_id in games[team_col].unique():
            team_games = games[games[team_col] == team_id].copy()

            for idx, row in team_games.iterrows():
                # Get last 10 games BEFORE this game
                prev_games = team_games[team_games['gameDate'] < row['gameDate']].tail(10)

                if len(prev_games) < 3:  # Need minimum sample
                    continue

                # Calculate shooting%
                goals = prev_games[f'goalsFor_{team_side}'].sum()
                shots = prev_games[f'shotsForPerGame_{team_side}'].sum()
                shooting_pct = (goals / shots * 100) if shots > 0 else 10.0

                # Calculate save%
                goals_against = prev_games[f'goalsAgainst_{team_side}'].sum()
                shots_against = prev_games[f'shotsAgainstPerGame_{team_side}'].sum()
                save_pct = ((shots_against - goals_against) / shots_against * 100) if shots_against > 0 else 90.0

                # PDO = Shooting% + Save%
                pdo = shooting_pct + save_pct

                games.at[idx, f'pdo_rolling_10_{team_side}'] = pdo

    # Add differentials
    games['pdo_rolling_10_diff'] = games['pdo_rolling_10_home'] - games['pdo_rolling_10_away']

    return games


def _add_pdo_deviation(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add PDO deviation from 100.

    Higher deviation = more extreme = more likely to regress.
    This is the key predictive signal.
    """
    for side in ['home', 'away']:
        # Absolute deviation from 100
        games[f'pdo_deviation_{side}'] = abs(games[f'pdo_rolling_10_{side}'] - 100.0)

    # Differential (negative = home team more extreme, more likely to regress)
    games['pdo_deviation_diff'] = games['pdo_deviation_home'] - games['pdo_deviation_away']

    return games


def _add_shooting_sustainability(games: pd.DataFrame) -> pd.DataFrame:
    """
    Measure shooting% sustainability using xG.

    If Shooting% >> xG%, team is getting lucky (unsustainable).
    If Shooting% << xG%, team is unlucky (due for improvement).
    """
    games = games.sort_values('gameDate')

    # Initialize
    for side in ['home', 'away']:
        games[f'shooting_pct_sustainability_{side}'] = 0.0

    # Calculate for each team
    for team_side in ['home', 'away']:
        team_col = f'teamId_{team_side}'

        for team_id in games[team_col].unique():
            team_games = games[games[team_col] == team_id].copy()

            for idx, row in team_games.iterrows():
                # Get last 10 games
                prev_games = team_games[team_games['gameDate'] < row['gameDate']].tail(10)

                if len(prev_games) < 3:
                    continue

                # Actual shooting%
                goals = prev_games[f'goalsFor_{team_side}'].sum()
                shots = prev_games[f'shotsForPerGame_{team_side}'].sum()
                shooting_pct = (goals / shots * 100) if shots > 0 else 10.0

                # Expected shooting% from xG
                xg_col = f'xGoalsFor_{team_side}'
                if xg_col in prev_games.columns:
                    xg = prev_games[xg_col].sum()
                    expected_shooting_pct = (xg / shots * 100) if shots > 0 else 10.0

                    # Sustainability = Actual - Expected
                    # Positive = overperforming (lucky), negative = underperforming (unlucky)
                    sustainability = shooting_pct - expected_shooting_pct
                else:
                    sustainability = 0.0

                games.at[idx, f'shooting_pct_sustainability_{team_side}'] = sustainability

    # Differential
    games['shooting_pct_sustainability_diff'] = (
        games['shooting_pct_sustainability_home'] - games['shooting_pct_sustainability_away']
    )

    return games


def _add_save_sustainability(games: pd.DataFrame) -> pd.DataFrame:
    """
    Measure save% sustainability using xG against.

    If Save% >> Expected (from xG), goalie is getting lucky.
    If Save% << Expected, goalie is unlucky.
    """
    games = games.sort_values('gameDate')

    # Initialize
    for side in ['home', 'away']:
        games[f'save_pct_sustainability_{side}'] = 0.0

    # Calculate for each team
    for team_side in ['home', 'away']:
        team_col = f'teamId_{team_side}'

        for team_id in games[team_col].unique():
            team_games = games[games[team_col] == team_id].copy()

            for idx, row in team_games.iterrows():
                # Get last 10 games
                prev_games = team_games[team_games['gameDate'] < row['gameDate']].tail(10)

                if len(prev_games) < 3:
                    continue

                # Actual save%
                goals_against = prev_games[f'goalsAgainst_{team_side}'].sum()
                shots_against = prev_games[f'shotsAgainstPerGame_{team_side}'].sum()
                save_pct = ((shots_against - goals_against) / shots_against * 100) if shots_against > 0 else 90.0

                # Expected save% from xG against
                xga_col = f'xGoalsAgainst_{team_side}'
                if xga_col in prev_games.columns:
                    xga = prev_games[xga_col].sum()
                    expected_save_pct = ((shots_against - xga) / shots_against * 100) if shots_against > 0 else 90.0

                    # Sustainability = Actual - Expected
                    # Positive = overperforming (lucky), negative = underperforming (unlucky)
                    sustainability = save_pct - expected_save_pct
                else:
                    sustainability = 0.0

                games.at[idx, f'save_pct_sustainability_{side}'] = sustainability

    # Differential
    games['save_pct_sustainability_diff'] = (
        games['save_pct_sustainability_home'] - games['save_pct_sustainability_away']
    )

    return games


__all__ = [
    'add_pdo_features',
]
