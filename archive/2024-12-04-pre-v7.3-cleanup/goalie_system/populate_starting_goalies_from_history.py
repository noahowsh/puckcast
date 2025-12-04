#!/usr/bin/env python3
"""
Populate starting_goalies database from historical game boxscores.

This script:
1. Loads all games from our cached parquet files (2021-2024)
2. Fetches boxscores (using cache) to see which goalies played
3. Identifies the starter as the goalie with the most TOI (>30 mins)
4. Populates starting_goalies table for use in V7.1 training

CRITICAL: Uses actual game results, so we must ensure proper train/test split:
- Build the database from ALL seasons (2021-2024)
- V7.1 training script uses goalie_tracker_train_only.pkl (only 2021-2023)
- When predicting test games, only uses goalie performance from BEFORE the test game date
- This prevents data leakage while allowing us to know who actually started
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Dict, Any, Optional
import logging
import sys

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nhl_prediction.data_sources.gamecenter import GamecenterClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
DB_PATH = PROJECT_ROOT / "data" / "starting_goalies.db"

SEASONS = ["20212022", "20222023", "20232024"]


def init_database():
    """Initialize starting_goalies database with schema."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Drop existing table if it exists
    cursor.execute("DROP TABLE IF EXISTS starting_goalies")

    # Create table
    cursor.execute("""
        CREATE TABLE starting_goalies (
            game_id INTEGER PRIMARY KEY,
            game_date TEXT NOT NULL,
            away_team TEXT NOT NULL,
            home_team TEXT NOT NULL,
            away_starter_id INTEGER,
            away_starter_name TEXT,
            away_starter_toi INTEGER,
            home_starter_id INTEGER,
            home_starter_name TEXT,
            home_starter_toi INTEGER,
            populated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()
    LOGGER.info(f"✓ Database initialized: {DB_PATH}")


def identify_starter(goalies: list) -> Optional[Dict[str, Any]]:
    """
    Identify the starting goalie from a list of goalies who played.

    Starter is defined as the goalie with the most TOI (typically >30 mins).

    Args:
        goalies: List of goalie dicts with 'playerId', 'name', 'toi'

    Returns:
        Dict with starter info or None if no clear starter
    """
    if not goalies:
        return None

    # Convert TOI to seconds and find goalie with most ice time
    max_toi_seconds = 0
    starter = None

    for goalie in goalies:
        toi_str = goalie.get('toi', '00:00')
        try:
            mins, secs = toi_str.split(':')
            toi_seconds = int(mins) * 60 + int(secs)
        except:
            toi_seconds = 0

        # Starter typically plays >30 minutes (1800 seconds)
        if toi_seconds > max_toi_seconds and toi_seconds >= 600:  # At least 10 mins
            max_toi_seconds = toi_seconds
            name = goalie.get('name', {})
            starter = {
                'player_id': goalie.get('playerId'),
                'name': name.get('default', 'Unknown'),
                'toi_seconds': toi_seconds
            }

    return starter


def extract_starters_from_boxscore(boxscore: Dict[str, Any], game_id: str) -> Optional[Dict[str, Any]]:
    """
    Extract starting goalies from boxscore.

    Returns dict with:
        - away_starter_id
        - away_starter_name
        - away_starter_toi
        - home_starter_id
        - home_starter_name
        - home_starter_toi
    """
    try:
        player_stats = boxscore.get("playerByGameStats", {})

        # Away team
        away_data = player_stats.get("awayTeam", {})
        away_goalies = away_data.get("goalies", [])
        away_starter = identify_starter(away_goalies)

        # Home team
        home_data = player_stats.get("homeTeam", {})
        home_goalies = home_data.get("goalies", [])
        home_starter = identify_starter(home_goalies)

        return {
            'away_starter_id': away_starter['player_id'] if away_starter else None,
            'away_starter_name': away_starter['name'] if away_starter else None,
            'away_starter_toi': away_starter['toi_seconds'] if away_starter else 0,
            'home_starter_id': home_starter['player_id'] if home_starter else None,
            'home_starter_name': home_starter['name'] if home_starter else None,
            'home_starter_toi': home_starter['toi_seconds'] if home_starter else 0,
        }

    except Exception as e:
        LOGGER.error(f"Error extracting starters from game {game_id}: {e}")
        return None


def populate_database():
    """Populate starting_goalies database from all historical games."""
    LOGGER.info("=" * 80)
    LOGGER.info("Populating Starting Goalies Database from Historical Games")
    LOGGER.info("=" * 80)

    # Initialize database
    init_database()

    # Load all games
    all_games = []
    for season in SEASONS:
        parquet_path = CACHE_DIR / f"native_logs_{season}.parquet"
        if not parquet_path.exists():
            LOGGER.warning(f"Parquet file not found: {parquet_path}")
            continue

        df = pd.read_parquet(parquet_path)
        # Get unique games (each game appears twice, once per team)
        games = df[['gameId', 'gameDate', 'teamAbbrev', 'homeRoad']].copy()
        all_games.append(games)
        LOGGER.info(f"Season {season}: {len(df)} team-games ({len(df)//2} matchups)")

    # Combine and create matchups
    all_games_df = pd.concat(all_games, ignore_index=True)

    # Create game matchups (home/away pairs)
    home_games = all_games_df[all_games_df['homeRoad'] == 'H'][['gameId', 'gameDate', 'teamAbbrev']].copy()
    away_games = all_games_df[all_games_df['homeRoad'] == 'A'][['gameId', 'teamAbbrev']].copy()

    home_games.rename(columns={'teamAbbrev': 'home_team'}, inplace=True)
    away_games.rename(columns={'teamAbbrev': 'away_team'}, inplace=True)

    matchups = home_games.merge(away_games, on='gameId')
    matchups = matchups.drop_duplicates(subset=['gameId'])

    total_games = len(matchups)
    LOGGER.info(f"\nTotal unique matchups: {total_games}")
    LOGGER.info(f"Fetching boxscores to identify starters...\n")

    # Fetch boxscores and populate database
    client = GamecenterClient()
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    games_processed = 0
    starters_found = 0

    for idx, row in matchups.iterrows():
        game_id = str(row['gameId'])
        game_date = str(row['gameDate'])
        away_team = row['away_team']
        home_team = row['home_team']

        if games_processed % 100 == 0 and games_processed > 0:
            LOGGER.info(f"Progress: {games_processed}/{total_games} games, {starters_found} with starters identified")

        try:
            # Fetch boxscore (uses cache if available)
            boxscore = client.get_boxscore(game_id)

            # Extract starters
            starters = extract_starters_from_boxscore(boxscore, game_id)

            if starters:
                # Insert into database
                cursor.execute("""
                    INSERT INTO starting_goalies (
                        game_id, game_date, away_team, home_team,
                        away_starter_id, away_starter_name, away_starter_toi,
                        home_starter_id, home_starter_name, home_starter_toi
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    game_id, game_date, away_team, home_team,
                    starters['away_starter_id'], starters['away_starter_name'], starters['away_starter_toi'],
                    starters['home_starter_id'], starters['home_starter_name'], starters['home_starter_toi']
                ))

                if starters['away_starter_id'] and starters['home_starter_id']:
                    starters_found += 1

            games_processed += 1

        except Exception as e:
            LOGGER.error(f"Error processing game {game_id}: {e}")
            continue

    # Commit all inserts
    conn.commit()
    conn.close()

    LOGGER.info(f"\n" + "=" * 80)
    LOGGER.info(f"Database Population Complete!")
    LOGGER.info(f"=" * 80)
    LOGGER.info(f"Games processed: {games_processed}/{total_games}")
    LOGGER.info(f"Games with both starters: {starters_found}")
    LOGGER.info(f"Coverage: {starters_found/games_processed*100:.1f}%")
    LOGGER.info(f"Database: {DB_PATH}")

    # Show sample data
    LOGGER.info(f"\nSample starting goalies:")
    conn = sqlite3.connect(DB_PATH)
    sample = pd.read_sql_query("""
        SELECT game_date, away_team, home_team, away_starter_name, home_starter_name
        FROM starting_goalies
        ORDER BY game_date DESC
        LIMIT 10
    """, conn)
    conn.close()

    print(sample.to_string(index=False))
    LOGGER.info(f"\n✓ Starting goalies database ready for V7.1 training!")


if __name__ == "__main__":
    populate_database()
