"""
V7.3 Situational Context Features

Adds 5 high-impact features that capture game context:
1. Fatigue Index - Games in last 7 days (weighted)
2. Third Period Trailing Performance - Win% when behind entering 3rd
3. Travel Distance - Miles traveled since last game
4. Divisional Matchups - Same division flag
5. Post-Break Performance - First game after 4+ days rest
"""

from __future__ import annotations

import logging
from typing import Dict, Tuple

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

LOGGER = logging.getLogger(__name__)

# NHL team locations (lat, lon) for travel distance calculation
NHL_TEAM_LOCATIONS = {
    'ANA': (33.8078, -117.8765),  # Anaheim
    'ARI': (33.4484, -112.0740),  # Arizona (now Utah, but using PHX for historical)
    'BOS': (42.3662, -71.0621),   # Boston
    'BUF': (42.8750, -78.8761),   # Buffalo
    'CAR': (35.8031, -78.7219),   # Carolina
    'CBJ': (39.9690, -82.9910),   # Columbus
    'CGY': (51.0375, -114.0519),  # Calgary
    'CHI': (41.8807, -87.6742),   # Chicago
    'COL': (39.7487, -105.0077),  # Colorado
    'DAL': (32.7905, -96.8103),   # Dallas
    'DET': (42.3410, -83.0550),   # Detroit
    'EDM': (53.5467, -113.4969),  # Edmonton
    'FLA': (26.1583, -80.3256),   # Florida
    'LAK': (34.0430, -118.2673),  # LA Kings
    'MIN': (44.9447, -93.1012),   # Minnesota
    'MTL': (45.4961, -73.5693),   # Montreal
    'NJD': (40.7334, -74.1711),   # New Jersey
    'NSH': (36.1590, -86.7784),   # Nashville
    'NYI': (40.7225, -73.5907),   # NY Islanders
    'NYR': (40.7505, -73.9934),   # NY Rangers
    'OTT': (45.2968, -75.9270),   # Ottawa
    'PHI': (39.9012, -75.1720),   # Philadelphia
    'PIT': (40.4394, -79.9894),   # Pittsburgh
    'SEA': (47.6221, -122.3540),  # Seattle
    'SJS': (37.3327, -121.9010),  # San Jose
    'STL': (38.6266, -90.2025),   # St. Louis
    'TBL': (27.9425, -82.4518),   # Tampa Bay
    'TOR': (43.6435, -79.3791),   # Toronto
    'VAN': (49.2778, -123.1089),  # Vancouver
    'VGK': (36.0909, -115.1833),  # Vegas
    'WPG': (49.8928, -97.1436),   # Winnipeg
    'WSH': (38.8981, -77.0209),   # Washington
}

# NHL Divisions (2021-22 onwards, after COVID realignment)
NHL_DIVISIONS = {
    'Atlantic': ['BOS', 'BUF', 'DET', 'FLA', 'MTL', 'OTT', 'TBL', 'TOR'],
    'Metropolitan': ['CAR', 'CBJ', 'NJD', 'NYI', 'NYR', 'PHI', 'PIT', 'WSH'],
    'Central': ['ARI', 'CHI', 'COL', 'DAL', 'MIN', 'NSH', 'STL', 'WPG'],
    'Pacific': ['ANA', 'CGY', 'EDM', 'LAK', 'SEA', 'SJS', 'VAN', 'VGK'],
}


def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points on Earth (in miles).
    Uses Haversine formula.
    """
    # Earth radius in miles
    R = 3959.0

    # Convert to radians
    lat1_rad = np.radians(lat1)
    lat2_rad = np.radians(lat2)
    dlon = np.radians(lon2 - lon1)
    dlat = np.radians(lat2 - lat1)

    # Haversine formula
    a = np.sin(dlat / 2)**2 + np.cos(lat1_rad) * np.cos(lat2_rad) * np.sin(dlon / 2)**2
    c = 2 * np.arcsin(np.sqrt(a))

    return R * c


def get_team_division(team_abbrev: str) -> str:
    """Get division for a team."""
    for division, teams in NHL_DIVISIONS.items():
        if team_abbrev in teams:
            return division
    return "Unknown"


def add_situational_features(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add all 5 V7.3 situational context features to games dataframe.

    Features added:
    1. fatigue_index_home/away - Weighted games count in last 7 days
    2. third_period_trailing_perf_home/away - Win% when behind entering 3rd
    3. travel_distance_home/away - Miles traveled since last game
    4. divisional_matchup - Same division flag
    5. post_break_game_home/away - First game after 4+ days rest

    Plus differential features for each.
    """
    games = games.copy()

    LOGGER.info("Adding V7.3 situational context features...")

    # Feature 1: Fatigue Index
    LOGGER.info("  [1/5] Computing fatigue index...")
    games = _add_fatigue_index(games)

    # Feature 2: Third Period Trailing Performance
    LOGGER.info("  [2/5] Computing third period trailing performance...")
    games = _add_third_period_trailing_perf(games)

    # Feature 3: Travel Distance
    LOGGER.info("  [3/5] Computing travel distance...")
    games = _add_travel_distance(games)

    # Feature 4: Divisional Matchups
    LOGGER.info("  [4/5] Adding divisional matchup flag...")
    games = _add_divisional_matchup(games)

    # Feature 5: Post-Break Performance
    LOGGER.info("  [5/5] Adding post-break game flag...")
    games = _add_post_break_flag(games)

    LOGGER.info(f"✓ Added {len([c for c in games.columns if any(x in c for x in ['fatigue', 'trailing', 'travel', 'divisional', 'break'])])} V7.3 situational features")

    return games


def _add_fatigue_index(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add fatigue index: weighted count of games in last 7 days.

    Weights: More recent games weighted higher
    - Yesterday: 1.0
    - 2 days ago: 0.8
    - 3 days ago: 0.6
    - 4 days ago: 0.4
    - 5 days ago: 0.3
    - 6 days ago: 0.2
    - 7 days ago: 0.1
    """
    games['fatigue_index_home'] = 0.0
    games['fatigue_index_away'] = 0.0

    # Sort by date for rolling window
    games = games.sort_values('gameDate')

    # Group by team and calculate fatigue for each game
    for team_side in ['home', 'away']:
        team_col = f'teamAbbrev_{team_side}'

        for team in games[team_col].unique():
            team_games = games[games[team_col] == team].copy()

            for idx, row in team_games.iterrows():
                game_date = pd.to_datetime(row['gameDate'])

                # Look back 7 days
                recent_games = team_games[
                    (team_games['gameDate'] < row['gameDate']) &
                    (pd.to_datetime(team_games['gameDate']) >= game_date - timedelta(days=7))
                ]

                if len(recent_games) == 0:
                    continue

                # Calculate weighted fatigue
                fatigue = 0.0
                for _, prev_game in recent_games.iterrows():
                    days_ago = (game_date - pd.to_datetime(prev_game['gameDate'])).days
                    if days_ago == 1:
                        weight = 1.0
                    elif days_ago == 2:
                        weight = 0.8
                    elif days_ago == 3:
                        weight = 0.6
                    elif days_ago == 4:
                        weight = 0.4
                    elif days_ago == 5:
                        weight = 0.3
                    elif days_ago == 6:
                        weight = 0.2
                    elif days_ago == 7:
                        weight = 0.1
                    else:
                        weight = 0.0

                    fatigue += weight

                games.at[idx, f'fatigue_index_{team_side}'] = fatigue

    # Add differential
    games['fatigue_index_diff'] = games['fatigue_index_home'] - games['fatigue_index_away']

    return games


def _add_third_period_trailing_perf(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add third period trailing performance: rolling win% when behind entering 3rd period.

    Uses last 20 games where team was trailing entering 3rd period.
    """
    games['third_period_trailing_perf_home'] = 0.5  # Default: 50%
    games['third_period_trailing_perf_away'] = 0.5

    # Note: We don't have period-by-period score data in current dataset
    # This would require play-by-play data analysis
    # For now, use a proxy: games where team was losing by 1 goal and came back
    # This is a simplified version - in production would need full period data

    games = games.sort_values('gameDate')

    for team_side in ['home', 'away']:
        team_col = f'teamAbbrev_{team_side}'

        # Calculate comeback win rate (proxy for 3rd period trailing performance)
        for team in games[team_col].unique():
            team_games = games[games[team_col] == team].copy()

            for idx, row in team_games.iterrows():
                # Look back at last 20 games
                prev_games = team_games[team_games['gameDate'] < row['gameDate']].tail(20)

                if len(prev_games) < 5:  # Need minimum sample
                    continue

                # Count close games won (proxy for clutch performance)
                # Use goal differential as proxy: positive = won, negative = lost
                if team_side == 'home':
                    close_wins = prev_games[
                        (prev_games['goalsFor_home'] - prev_games['goalsAgainst_home'] > 0) &
                        (abs(prev_games['goalsFor_home'] - prev_games['goalsAgainst_home']) <= 1)
                    ]
                    close_games = prev_games[
                        abs(prev_games['goalsFor_home'] - prev_games['goalsAgainst_home']) <= 1
                    ]
                else:
                    close_wins = prev_games[
                        (prev_games['goalsFor_away'] - prev_games['goalsAgainst_away'] > 0) &
                        (abs(prev_games['goalsFor_away'] - prev_games['goalsAgainst_away']) <= 1)
                    ]
                    close_games = prev_games[
                        abs(prev_games['goalsFor_away'] - prev_games['goalsAgainst_away']) <= 1
                    ]

                if len(close_games) > 0:
                    trailing_perf = len(close_wins) / len(close_games)
                    games.at[idx, f'third_period_trailing_perf_{team_side}'] = trailing_perf

    # Add differential
    games['third_period_trailing_perf_diff'] = (
        games['third_period_trailing_perf_home'] - games['third_period_trailing_perf_away']
    )

    return games


def _add_travel_distance(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add travel distance: miles traveled since last game.

    Calculates great circle distance between previous game city and current game city.
    """
    games['travel_distance_home'] = 0.0
    games['travel_distance_away'] = 0.0

    games = games.sort_values('gameDate')

    for team_side in ['home', 'away']:
        team_col = f'teamAbbrev_{team_side}'

        for team in games[team_col].unique():
            if team not in NHL_TEAM_LOCATIONS:
                continue

            team_games = games[games[team_col] == team].copy()

            prev_location = None
            for idx, row in team_games.iterrows():
                # Current game location
                if team_side == 'home':
                    current_location = NHL_TEAM_LOCATIONS[team]
                else:
                    # Away team - game is at opponent's arena
                    home_team = row['teamAbbrev_home']
                    current_location = NHL_TEAM_LOCATIONS.get(home_team, NHL_TEAM_LOCATIONS[team])

                # Calculate distance from previous game
                if prev_location is not None:
                    distance = calculate_haversine_distance(
                        prev_location[0], prev_location[1],
                        current_location[0], current_location[1]
                    )
                    games.at[idx, f'travel_distance_{team_side}'] = distance

                prev_location = current_location

    # Add differential
    games['travel_distance_diff'] = games['travel_distance_home'] - games['travel_distance_away']

    return games


def _add_divisional_matchup(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add divisional matchup flag: 1 if same division, 0 otherwise.
    """
    games['divisional_matchup'] = 0

    for idx, row in games.iterrows():
        home_team = row['teamAbbrev_home']
        away_team = row['teamAbbrev_away']

        home_div = get_team_division(home_team)
        away_div = get_team_division(away_team)

        if home_div == away_div and home_div != "Unknown":
            games.at[idx, 'divisional_matchup'] = 1

    return games


def _add_post_break_flag(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add post-break flag: 1 if first game after 4+ days rest, 0 otherwise.
    """
    games['post_break_game_home'] = 0
    games['post_break_game_away'] = 0

    # Use existing rest_days columns if available
    if 'rest_days_home' in games.columns and 'rest_days_away' in games.columns:
        games['post_break_game_home'] = (games['rest_days_home'] >= 4).astype(int)
        games['post_break_game_away'] = (games['rest_days_away'] >= 4).astype(int)

    # Add differential
    games['post_break_game_diff'] = games['post_break_game_home'] - games['post_break_game_away']

    return games


__all__ = [
    'add_situational_features',
]
