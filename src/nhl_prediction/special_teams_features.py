"""
V7.4 Enhanced Special Teams Features

Extracts power play and penalty kill performance metrics from play-by-play data.

WHY THESE FEATURES MATTER:
- Special teams account for 20-25% of goals scored in NHL
- Current model has ALL 16 PP%/PK% features at ZERO coefficient (pruned)
- Raw percentages are collinear with goal differential
- These enhanced features capture IMPACT (goals, opportunities) not just percentages

FEATURES CREATED (6):
1. special_teams_goal_diff_rolling - (PP goals - SH goals against) last 10 games
2. pp_opportunities_rolling - Power play chances last 10 games
3. pk_opportunities_rolling - Times shorthanded last 10 games
4. special_teams_efficiency_diff - Efficiency vs opportunity count
5. pp_home_away_variance - PP% difference home vs away
6. pk_home_away_variance - PK% difference home vs away
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, List, Tuple

import pandas as pd
import numpy as np
from collections import defaultdict

LOGGER = logging.getLogger(__name__)


def _parse_situation_code(code: str) -> Dict[str, bool]:
    """
    Parse NHL situation code to determine game state.

    Format: ABCD where
    - A = Away skaters
    - B = Home skaters
    - C = Strength state (5=even, 4=PP, etc.)
    - D = ? (usually 1 or 5)

    Example: "1551" = 5v5 even strength
             "1541" = 5v4 power play
             "1451" = 4v5 shorthanded
    """
    if not code or len(code) < 3:
        return {"is_even_strength": True, "is_power_play": False}

    away_skaters = int(code[0])
    home_skaters = int(code[1])

    is_even = away_skaters == home_skaters
    is_pp = not is_even

    return {
        "is_even_strength": is_even,
        "is_power_play": is_pp,
        "away_skaters": away_skaters,
        "home_skaters": home_skaters,
    }


def extract_special_teams_goals(games: pd.DataFrame) -> pd.DataFrame:
    """
    Extract power play and shorthanded goals from play-by-play data.

    For each game, counts:
    - PP goals scored (home/away)
    - SH goals scored (home/away)
    - SH goals allowed (home/away) - opponent PP goals
    - Total penalties taken (home/away) - proxy for PK opportunities
    - Total penalties drawn (home/away) - proxy for PP opportunities

    Args:
        games: DataFrame with gameId, teamId_home, teamId_away columns

    Returns:
        DataFrame with special teams stats added:
        - pp_goals_home, pp_goals_away
        - sh_goals_home, sh_goals_away
        - sh_goals_allowed_home, sh_goals_allowed_away
        - penalties_taken_home, penalties_taken_away
        - penalties_drawn_home, penalties_drawn_away
    """
    from .data_sources.gamecenter import get_default_client

    games = games.copy()

    # Initialize columns
    games['pp_goals_home'] = 0
    games['pp_goals_away'] = 0
    games['sh_goals_home'] = 0
    games['sh_goals_away'] = 0
    games['sh_goals_allowed_home'] = 0
    games['sh_goals_allowed_away'] = 0
    games['penalties_taken_home'] = 0
    games['penalties_taken_away'] = 0
    games['penalties_drawn_home'] = 0
    games['penalties_drawn_away'] = 0

    client = get_default_client()

    LOGGER.info(f"Extracting special teams goals from {len(games)} games...")

    for idx, row in games.iterrows():
        if idx % 200 == 0:
            LOGGER.info(f"  Processing game {idx+1}/{len(games)}")

        game_id = row['gameId']
        home_team_id = row['teamId_home']
        away_team_id = row['teamId_away']

        try:
            pbp = client.get_play_by_play(game_id)
            plays = pbp.get('plays', [])

            pp_goals_home = 0
            pp_goals_away = 0
            sh_goals_home = 0
            sh_goals_away = 0
            penalties_home = 0
            penalties_away = 0

            for play in plays:
                type_key = play.get('typeDescKey', '')
                details = play.get('details', {})
                event_owner = details.get('eventOwnerTeamId')
                situation_code = play.get('situationCode', '1551')
                situation = _parse_situation_code(situation_code)

                # Skip if no event owner
                if not event_owner:
                    continue

                # GOALS - check if power play or shorthanded
                if type_key == 'goal':
                    # Determine which team scored
                    scoring_team = event_owner
                    defending_team = away_team_id if scoring_team == home_team_id else home_team_id

                    if situation['is_power_play']:
                        # Power play situation - determine who has advantage
                        away_skaters = situation.get('away_skaters', 5)
                        home_skaters = situation.get('home_skaters', 5)

                        if scoring_team == home_team_id:
                            if home_skaters > away_skaters:
                                # Home team scored on PP
                                pp_goals_home += 1
                                sh_goals_away += 1  # Away team allowed goal while SH
                            elif away_skaters > home_skaters:
                                # Home team scored SH goal
                                sh_goals_home += 1
                                pp_goals_away += 0  # Away team PP did not score
                        else:  # Away team scored
                            if away_skaters > home_skaters:
                                # Away team scored on PP
                                pp_goals_away += 1
                                sh_goals_home += 1  # Home team allowed goal while SH
                            elif home_skaters > away_skaters:
                                # Away team scored SH goal
                                sh_goals_away += 1
                                pp_goals_home += 0  # Home team PP did not score

                # PENALTIES - track opportunities
                if type_key == 'penalty':
                    penalized_team = event_owner

                    if penalized_team == home_team_id:
                        penalties_home += 1
                    else:
                        penalties_away += 1

            # Store results
            games.at[idx, 'pp_goals_home'] = pp_goals_home
            games.at[idx, 'pp_goals_away'] = pp_goals_away
            games.at[idx, 'sh_goals_home'] = sh_goals_home
            games.at[idx, 'sh_goals_away'] = sh_goals_away
            games.at[idx, 'sh_goals_allowed_home'] = sh_goals_home  # SH goals allowed = opponent PP goals against us
            games.at[idx, 'sh_goals_allowed_away'] = sh_goals_away
            games.at[idx, 'penalties_taken_home'] = penalties_home
            games.at[idx, 'penalties_taken_away'] = penalties_away
            games.at[idx, 'penalties_drawn_home'] = penalties_away  # We draw penalties that opponents take
            games.at[idx, 'penalties_drawn_away'] = penalties_home

        except Exception as e:
            LOGGER.warning(f"  Failed to extract special teams for game {game_id}: {e}")
            continue

    LOGGER.info("✓ Special teams goals extracted")

    return games


def add_special_teams_features(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add all 6 V7.4 enhanced special teams features.

    Features added:
    1. special_teams_goal_diff_rolling - (PP goals - SH goals allowed) last 10
    2. pp_opportunities_rolling - Penalties drawn last 10 games
    3. pk_opportunities_rolling - Penalties taken last 10 games
    4. special_teams_efficiency_diff - (PP goals/PP opps) - (SH allowed/PK opps)
    5. pp_home_away_variance - PP% difference home vs away
    6. pk_home_away_variance - PK% difference home vs away

    Args:
        games: DataFrame with game data

    Returns:
        DataFrame with special teams features added
    """
    games = games.copy()

    LOGGER.info("Adding V7.4 enhanced special teams features...")

    # Step 1: Extract special teams goals from play-by-play
    LOGGER.info("  [1/6] Extracting special teams goals from play-by-play...")
    games = extract_special_teams_goals(games)

    # Step 2: Create rolling features
    LOGGER.info("  [2/6] Computing rolling special teams metrics...")
    games = _add_special_teams_rolling(games)

    # Step 3: Efficiency metrics
    LOGGER.info("  [3/6] Computing special teams efficiency...")
    games = _add_special_teams_efficiency(games)

    # Step 4: Home/away variance
    LOGGER.info("  [4/6] Computing home/away variance...")
    games = _add_home_away_variance(games)

    LOGGER.info(f"✓ Added {len([c for c in games.columns if 'special_teams' in c or 'pp_' in c or 'pk_' in c])} V7.4 special teams features")

    return games


def _add_special_teams_rolling(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add rolling 10-game special teams metrics.

    Features:
    - special_teams_goal_diff_rolling - (PP goals - SH goals allowed)
    - pp_opportunities_rolling - Penalties drawn
    - pk_opportunities_rolling - Penalties taken
    """
    games = games.sort_values('gameDate')

    # Initialize columns
    for side in ['home', 'away']:
        games[f'special_teams_goal_diff_rolling_{side}'] = 0.0
        games[f'pp_opportunities_rolling_{side}'] = 0.0
        games[f'pk_opportunities_rolling_{side}'] = 0.0

    # Calculate rolling metrics for each team
    for team_side in ['home', 'away']:
        team_col = f'teamId_{team_side}'

        for team_id in games[team_col].unique():
            team_games = games[games[team_col] == team_id].copy()

            for idx, row in team_games.iterrows():
                # Get last 10 games BEFORE this game
                prev_games = team_games[team_games['gameDate'] < row['gameDate']].tail(10)

                if len(prev_games) == 0:
                    continue

                # Special teams goal differential
                pp_goals = prev_games[f'pp_goals_{team_side}'].sum()
                sh_goals_allowed = prev_games[f'sh_goals_allowed_{team_side}'].sum()
                st_goal_diff = pp_goals - sh_goals_allowed

                # Opportunities
                pp_opps = prev_games[f'penalties_drawn_{team_side}'].sum()
                pk_opps = prev_games[f'penalties_taken_{team_side}'].sum()

                games.at[idx, f'special_teams_goal_diff_rolling_{team_side}'] = st_goal_diff
                games.at[idx, f'pp_opportunities_rolling_{team_side}'] = pp_opps
                games.at[idx, f'pk_opportunities_rolling_{team_side}'] = pk_opps

    # Add differentials
    games['special_teams_goal_diff_rolling_diff'] = (
        games['special_teams_goal_diff_rolling_home'] - games['special_teams_goal_diff_rolling_away']
    )
    games['pp_opportunities_rolling_diff'] = (
        games['pp_opportunities_rolling_home'] - games['pp_opportunities_rolling_away']
    )
    games['pk_opportunities_rolling_diff'] = (
        games['pk_opportunities_rolling_home'] - games['pk_opportunities_rolling_away']
    )

    return games


def _add_special_teams_efficiency(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add special teams efficiency: (PP goals / PP opps) - (SH goals allowed / PK opps).

    This measures conversion rate, not just raw percentages.
    """
    for side in ['home', 'away']:
        # PP efficiency: PP goals / PP opportunities
        pp_eff = (
            games[f'special_teams_goal_diff_rolling_{side}'] /
            games[f'pp_opportunities_rolling_{side}'].replace(0, np.nan)
        ).fillna(0.0)

        # PK efficiency: SH goals allowed / PK opportunities
        # (Lower is better, so we'll negate it)
        pk_eff = -(
            games[f'sh_goals_allowed_{side}'] /
            games[f'pk_opportunities_rolling_{side}'].replace(0, np.nan)
        ).fillna(0.0)

        # Combined efficiency
        games[f'special_teams_efficiency_{side}'] = pp_eff + pk_eff

    # Differential
    games['special_teams_efficiency_diff'] = (
        games['special_teams_efficiency_home'] - games['special_teams_efficiency_away']
    )

    return games


def _add_home_away_variance(games: pd.DataFrame) -> pd.DataFrame:
    """
    Add PP%/PK% variance between home and away games.

    Some teams perform significantly better at home on special teams.
    """
    games = games.sort_values('gameDate')

    # Initialize
    for side in ['home', 'away']:
        games[f'pp_home_away_variance_{side}'] = 0.0
        games[f'pk_home_away_variance_{side}'] = 0.0

    # Calculate variance for each team
    for team_side in ['home', 'away']:
        team_col = f'teamId_{team_side}'

        for team_id in games[team_col].unique():
            team_games = games[games[team_col] == team_id].copy()

            for idx, row in team_games.iterrows():
                # Get last 20 games BEFORE this game
                prev_games = team_games[team_games['gameDate'] < row['gameDate']].tail(20)

                if len(prev_games) < 10:  # Need minimum sample
                    continue

                # Split by home/away
                home_mask = prev_games['teamId_home'] == team_id
                away_mask = prev_games['teamId_away'] == team_id

                home_prev = prev_games[home_mask]
                away_prev = prev_games[away_mask]

                if len(home_prev) < 3 or len(away_prev) < 3:
                    continue

                # Calculate PP% at home vs away
                if team_side == 'home':
                    pp_home = home_prev['pp_goals_home'].sum() / max(home_prev['penalties_drawn_home'].sum(), 1)
                    pp_away = away_prev['pp_goals_away'].sum() / max(away_prev['penalties_drawn_away'].sum(), 1)

                    pk_home = home_prev['sh_goals_allowed_home'].sum() / max(home_prev['penalties_taken_home'].sum(), 1)
                    pk_away = away_prev['sh_goals_allowed_away'].sum() / max(away_prev['penalties_taken_away'].sum(), 1)
                else:
                    pp_home = home_prev['pp_goals_home'].sum() / max(home_prev['penalties_drawn_home'].sum(), 1)
                    pp_away = away_prev['pp_goals_away'].sum() / max(away_prev['penalties_drawn_away'].sum(), 1)

                    pk_home = home_prev['sh_goals_allowed_home'].sum() / max(home_prev['penalties_taken_home'].sum(), 1)
                    pk_away = away_prev['sh_goals_allowed_away'].sum() / max(away_prev['penalties_taken_away'].sum(), 1)

                # Variance (difference)
                pp_variance = pp_home - pp_away
                pk_variance = pk_home - pk_away

                games.at[idx, f'pp_home_away_variance_{team_side}'] = pp_variance
                games.at[idx, f'pk_home_away_variance_{team_side}'] = pk_variance

    # Add differentials
    games['pp_home_away_variance_diff'] = (
        games['pp_home_away_variance_home'] - games['pp_home_away_variance_away']
    )
    games['pk_home_away_variance_diff'] = (
        games['pk_home_away_variance_home'] - games['pk_home_away_variance_away']
    )

    return games


__all__ = [
    'add_special_teams_features',
    'extract_special_teams_goals',
]
