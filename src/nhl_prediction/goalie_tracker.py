"""
Individual Goalie Performance Tracker for V7.0

Tracks individual goalie stats from NHL API play-by-play data.
This is the #1 priority for V7.0 - expected +0.8-1.2% accuracy improvement.

Key metrics:
- Goals Saved Above Expected (GSA)
- Save percentage overall and by shot type
- High-danger save percentage
- Rush shot save percentage
- Recent form (last 3/5/10 games)
- Performance vs specific opponents
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Optional
from collections import defaultdict
import logging

LOGGER = logging.getLogger(__name__)


class GoalieTracker:
    """Track individual goalie performance across games."""

    def __init__(self):
        """Initialize goalie tracker with empty history."""
        self.goalie_games = defaultdict(list)  # goalie_id -> list of game stats
        self.goalie_info = {}  # goalie_id -> {name, team, etc}

    def add_game(
        self,
        goalie_id: int,
        game_id: str,
        game_date: str,
        team: str,
        opponent: str,
        saves: int,
        shots_against: int,
        goals_against: int,
        high_danger_saves: int = 0,
        high_danger_shots: int = 0,
        rush_saves: int = 0,
        rush_shots: int = 0,
        expected_goals_against: float = 0.0,
        toi_seconds: int = 3600
    ):
        """
        Add a game to goalie's history.

        Args:
            goalie_id: NHL API goalie ID
            game_id: Game identifier
            game_date: Date in YYYY-MM-DD format
            team: Goalie's team abbreviation
            opponent: Opponent team abbreviation
            saves: Total saves
            shots_against: Total shots faced
            goals_against: Goals allowed
            high_danger_saves: Saves on high-danger shots
            high_danger_shots: High-danger shots faced
            rush_saves: Saves on rush shots
            rush_shots: Rush shots faced
            expected_goals_against: xG against (from our xG model)
            toi_seconds: Time on ice in seconds
        """
        save_pct = saves / shots_against if shots_against > 0 else 0.0
        hd_save_pct = high_danger_saves / high_danger_shots if high_danger_shots > 0 else 0.0
        rush_save_pct = rush_saves / rush_shots if rush_shots > 0 else 0.0

        # Calculate GSA (Goals Saved Above Expected)
        gsa = expected_goals_against - goals_against

        game_stats = {
            'game_id': game_id,
            'game_date': game_date,
            'team': team,
            'opponent': opponent,
            'saves': saves,
            'shots_against': shots_against,
            'goals_against': goals_against,
            'save_pct': save_pct,
            'high_danger_saves': high_danger_saves,
            'high_danger_shots': high_danger_shots,
            'hd_save_pct': hd_save_pct,
            'rush_saves': rush_saves,
            'rush_shots': rush_shots,
            'rush_save_pct': rush_save_pct,
            'expected_goals_against': expected_goals_against,
            'gsa': gsa,
            'toi_seconds': toi_seconds
        }

        self.goalie_games[goalie_id].append(game_stats)

    def get_recent_form(
        self,
        goalie_id: int,
        before_date: str,
        last_n_games: int = 5
    ) -> Dict[str, float]:
        """
        Get goalie's recent form before a specific date.

        Args:
            goalie_id: NHL API goalie ID
            before_date: Only consider games before this date
            last_n_games: Number of recent games to average

        Returns:
            Dict with averaged stats from recent games
        """
        if goalie_id not in self.goalie_games:
            return self._default_stats()

        # Filter games before date and sort by date
        games = [
            g for g in self.goalie_games[goalie_id]
            if g['game_date'] < before_date
        ]
        games.sort(key=lambda x: x['game_date'], reverse=True)

        # Take last N games
        recent_games = games[:last_n_games]

        if not recent_games:
            return self._default_stats()

        # Calculate averages
        return {
            'games_played': len(recent_games),
            'save_pct': np.mean([g['save_pct'] for g in recent_games]),
            'shots_against_avg': np.mean([g['shots_against'] for g in recent_games]),
            'goals_against_avg': np.mean([g['goals_against'] for g in recent_games]),
            'hd_save_pct': np.mean([g['hd_save_pct'] for g in recent_games if g['high_danger_shots'] > 0] or [0.0]),
            'rush_save_pct': np.mean([g['rush_save_pct'] for g in recent_games if g['rush_shots'] > 0] or [0.0]),
            'gsa_avg': np.mean([g['gsa'] for g in recent_games]),
            'gsa_total': sum([g['gsa'] for g in recent_games])
        }

    def get_vs_opponent(
        self,
        goalie_id: int,
        opponent: str,
        before_date: str,
        min_games: int = 3
    ) -> Dict[str, float]:
        """
        Get goalie's historical performance vs specific opponent.

        Args:
            goalie_id: NHL API goalie ID
            opponent: Opponent team abbreviation
            before_date: Only consider games before this date
            min_games: Minimum games required for meaningful stats

        Returns:
            Dict with stats vs opponent (or defaults if < min_games)
        """
        if goalie_id not in self.goalie_games:
            return self._default_stats()

        # Filter games vs opponent before date
        vs_games = [
            g for g in self.goalie_games[goalie_id]
            if g['opponent'] == opponent and g['game_date'] < before_date
        ]

        if len(vs_games) < min_games:
            # Not enough history, return league average
            return self._default_stats()

        return {
            'games_played': len(vs_games),
            'save_pct': np.mean([g['save_pct'] for g in vs_games]),
            'goals_against_avg': np.mean([g['goals_against'] for g in vs_games]),
            'gsa_avg': np.mean([g['gsa'] for g in vs_games])
        }

    def get_season_stats(
        self,
        goalie_id: int,
        season: str,
        before_date: Optional[str] = None
    ) -> Dict[str, float]:
        """
        Get goalie's season totals.

        Args:
            goalie_id: NHL API goalie ID
            season: Season ID (e.g., '20232024')
            before_date: Optional cutoff date

        Returns:
            Dict with season stats
        """
        if goalie_id not in self.goalie_games:
            return self._default_stats()

        # Filter games in season
        season_games = [
            g for g in self.goalie_games[goalie_id]
            if season in g['game_id']  # game_id starts with season
        ]

        if before_date:
            season_games = [g for g in season_games if g['game_date'] < before_date]

        if not season_games:
            return self._default_stats()

        total_saves = sum([g['saves'] for g in season_games])
        total_shots = sum([g['shots_against'] for g in season_games])
        total_gsa = sum([g['gsa'] for g in season_games])

        return {
            'games_played': len(season_games),
            'save_pct': total_saves / total_shots if total_shots > 0 else 0.0,
            'saves_total': total_saves,
            'shots_against_total': total_shots,
            'gsa_total': total_gsa,
            'gsa_avg': total_gsa / len(season_games)
        }

    def _default_stats(self) -> Dict[str, float]:
        """Return default/league average stats when data unavailable."""
        return {
            'games_played': 0,
            'save_pct': 0.910,  # League average
            'hd_save_pct': 0.850,  # Estimated league average
            'rush_save_pct': 0.880,  # Estimated league average
            'gsa_avg': 0.0,
            'gsa_total': 0.0,
            'goals_against_avg': 3.0,
            'shots_against_avg': 30.0
        }


def extract_goalie_stats_from_game(game_data: dict, xg_model) -> List[dict]:
    """
    Extract goalie stats from NHL API game play-by-play data.

    Args:
        game_data: Play-by-play data from NHL API
        xg_model: Trained xG model for calculating expected goals

    Returns:
        List of dicts with goalie stats (one per goalie who played)
    """
    # This will be implemented to parse play-by-play and extract:
    # - Which goalies played
    # - Shots faced by each
    # - Goals allowed
    # - Shot types (high-danger, rush, etc.)
    # - xG against each goalie

    # Placeholder for now - will integrate with native_ingest.py
    return []


def build_goalie_database(seasons: List[str], cache_dir: str = "data/goalie_cache") -> GoalieTracker:
    """
    Build comprehensive goalie database from multiple seasons.

    Args:
        seasons: List of season IDs to process
        cache_dir: Directory to cache goalie data

    Returns:
        GoalieTracker with all goalie games loaded
    """
    import os
    from pathlib import Path

    cache_path = Path(cache_dir)
    cache_path.mkdir(parents=True, exist_ok=True)

    tracker = GoalieTracker()

    # Check for cached data
    cache_file = cache_path / f"goalie_db_{'_'.join(seasons)}.pkl"
    if cache_file.exists():
        import pickle
        LOGGER.info(f"Loading goalie database from cache: {cache_file}")
        with open(cache_file, 'rb') as f:
            return pickle.load(f)

    # Build from scratch
    LOGGER.info(f"Building goalie database for seasons: {seasons}")

    # This will integrate with native_ingest.py to process all games
    # For now, return empty tracker

    # Cache for future use
    import pickle
    with open(cache_file, 'wb') as f:
        pickle.dump(tracker, f)

    LOGGER.info(f"Goalie database cached to: {cache_file}")
    return tracker
