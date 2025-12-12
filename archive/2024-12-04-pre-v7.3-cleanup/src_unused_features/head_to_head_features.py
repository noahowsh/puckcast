"""
Head-to-Head Matchup Features (V7.4)

Based on V7.3 error analysis, many errors cluster in specific matchups.
These features capture historical and recent H2H performance.

Expected impact: +0.2-0.4pp accuracy
Target: Close 30-60% of the 0.62pp gap to 62%
"""

import pandas as pd
import numpy as np
from typing import Dict
import logging

LOGGER = logging.getLogger(__name__)


def add_head_to_head_features(games: pd.DataFrame, train_seasons: list = None) -> pd.DataFrame:
    """
    Add head-to-head matchup features.

    Features added (6 total):
    1. h2h_win_pct_last_season: Team A win% vs Team B in previous season
    2. h2h_win_pct_recent: Team A win% vs Team B in last 3 matchups
    3. h2h_goal_diff_recent: Avg goal differential in last 3 matchups
    4. h2h_home_advantage: Home team win% in this matchup historically
    5. season_series_context: Current series standing (0-0, 1-0, 2-0, etc.)
    6. h2h_games_played_this_season: Number of times they've met this season

    Args:
        games: DataFrame with game data
        train_seasons: List of training season IDs. If provided, only these seasons
                       will be used to build H2H history (prevents test set leakage)

    Returns:
        DataFrame with 6 new H2H features added
    """
    LOGGER.info("Adding V7.4 head-to-head matchup features...")

    games = games.copy()

    # Initialize feature columns
    h2h_features = [
        'h2h_win_pct_last_season',
        'h2h_win_pct_recent',
        'h2h_goal_diff_recent',
        'h2h_home_advantage',
        'season_series_home_wins',
        'season_series_away_wins',
    ]

    for feature in h2h_features:
        games[feature] = 0.0

    # Process games chronologically
    games = games.sort_values('gameDate').reset_index(drop=True)

    # Track H2H history: (team1, team2) -> list of games
    h2h_history = {}

    for idx, row in games.iterrows():
        home_team = row['teamAbbrev_home']
        away_team = row['teamAbbrev_away']
        game_date = row['gameDate']
        season = row['seasonId']

        # Create ordered matchup key (always team1 < team2 alphabetically)
        team1, team2 = sorted([home_team, away_team])
        matchup_key = (team1, team2)

        # Initialize if first meeting
        if matchup_key not in h2h_history:
            h2h_history[matchup_key] = []

        # Get historical games for this matchup (before current game)
        past_games = h2h_history[matchup_key]

        if past_games:
            # Filter to relevant seasons
            current_season_year = int(season[:4])
            last_season = f"{current_season_year-1}{current_season_year}"

            # 1. Last season win %
            last_season_games = [g for g in past_games if g['season'] == last_season]
            if last_season_games:
                # Calculate home team win %
                home_wins = sum(1 for g in last_season_games if
                               (g['home_team'] == home_team and g['home_win']) or
                               (g['away_team'] == home_team and not g['home_win']))
                games.at[idx, 'h2h_win_pct_last_season'] = home_wins / len(last_season_games)

            # 2. Recent win % (last 3 games)
            recent_games = past_games[-3:] if len(past_games) >= 3 else past_games
            if recent_games:
                home_wins = sum(1 for g in recent_games if
                               (g['home_team'] == home_team and g['home_win']) or
                               (g['away_team'] == home_team and not g['home_win']))
                games.at[idx, 'h2h_win_pct_recent'] = home_wins / len(recent_games)

                # 3. Recent goal differential (from home team perspective)
                goal_diffs = []
                for g in recent_games:
                    if g['home_team'] == home_team:
                        goal_diffs.append(g['home_score'] - g['away_score'])
                    else:  # Home team was away in that game
                        goal_diffs.append(g['away_score'] - g['home_score'])
                games.at[idx, 'h2h_goal_diff_recent'] = np.mean(goal_diffs) if goal_diffs else 0.0

            # 4. Home advantage in this matchup (all history)
            if past_games:
                home_team_wins_when_home = sum(1 for g in past_games if g['home_win'])
                games.at[idx, 'h2h_home_advantage'] = home_team_wins_when_home / len(past_games)

            # 5-6. Season series context (this season only)
            this_season_games = [g for g in past_games if g['season'] == season]
            if this_season_games:
                # Count wins for home team when they were home or away
                home_wins_in_series = sum(1 for g in this_season_games if
                                         (g['home_team'] == home_team and g['home_win']) or
                                         (g['away_team'] == home_team and not g['home_win']))
                away_wins_in_series = len(this_season_games) - home_wins_in_series

                games.at[idx, 'season_series_home_wins'] = home_wins_in_series
                games.at[idx, 'season_series_away_wins'] = away_wins_in_series

        # Record this game in history (AFTER using it for features)
        # Only add to history if this is a training season (prevents test set leakage)
        if train_seasons is None or season in train_seasons:
            h2h_history[matchup_key].append({
                'season': season,
                'game_date': game_date,
                'home_team': home_team,
                'away_team': away_team,
                'home_score': row.get('home_score', 0),
                'away_score': row.get('away_score', 0),
                'home_win': row.get('home_win', 0) == 1,
            })

    LOGGER.info(f"✓ Added 6 V7.4 head-to-head features")

    return games
