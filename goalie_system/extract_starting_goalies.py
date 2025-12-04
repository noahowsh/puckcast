#!/usr/bin/env python3
"""Extract starting goalie assignments from NHL API boxscores."""

import json
import logging
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

CACHE_DIR = Path("data/raw/web_v1")
DB_PATH = Path("data/starting_goalies.db")


def get_starting_goalies(boxscore_data: dict) -> Tuple[Optional[int], Optional[int]]:
    """
    Extract starting goalie IDs from boxscore.

    Returns:
        (away_starter_id, home_starter_id) or (None, None) if not found
    """
    away_starter_id = None
    home_starter_id = None

    player_stats = boxscore_data.get("playerByGameStats", {})

    # Away team starter
    away_goalies = player_stats.get("awayTeam", {}).get("goalies", [])
    for goalie in away_goalies:
        if goalie.get("starter") is True:
            away_starter_id = goalie.get("playerId")
            break

    # Home team starter
    home_goalies = player_stats.get("homeTeam", {}).get("goalies", [])
    for goalie in home_goalies:
        if goalie.get("starter") is True:
            home_starter_id = goalie.get("playerId")
            break

    return away_starter_id, home_starter_id


def create_database():
    """Create starting_goalies database table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS starting_goalies (
            game_id INTEGER PRIMARY KEY,
            away_starter_id INTEGER,
            home_starter_id INTEGER,
            away_starter_name TEXT,
            home_starter_name TEXT,
            season TEXT,
            UNIQUE(game_id)
        )
    """)

    conn.commit()
    return conn


def process_boxscore(boxscore_path: Path, cursor: sqlite3.Cursor) -> bool:
    """Process a single boxscore file and insert starting goalies."""
    try:
        with open(boxscore_path) as f:
            data = json.load(f)

        game_id = int(boxscore_path.stem.replace("_boxscore", ""))
        season = str(game_id)[:4]

        away_starter_id, home_starter_id = get_starting_goalies(data)

        if not away_starter_id or not home_starter_id:
            LOGGER.warning(f"Game {game_id}: Missing starter (away={away_starter_id}, home={home_starter_id})")
            return False

        # Get goalie names
        player_stats = data.get("playerByGameStats", {})

        away_starter_name = None
        for goalie in player_stats.get("awayTeam", {}).get("goalies", []):
            if goalie.get("playerId") == away_starter_id:
                away_starter_name = goalie.get("name", {}).get("default", "Unknown")
                break

        home_starter_name = None
        for goalie in player_stats.get("homeTeam", {}).get("goalies", []):
            if goalie.get("playerId") == home_starter_id:
                home_starter_name = goalie.get("name", {}).get("default", "Unknown")
                break

        cursor.execute("""
            INSERT OR REPLACE INTO starting_goalies
            (game_id, away_starter_id, home_starter_id, away_starter_name, home_starter_name, season)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (game_id, away_starter_id, home_starter_id, away_starter_name, home_starter_name, season))

        return True

    except Exception as e:
        LOGGER.error(f"Error processing {boxscore_path}: {e}")
        return False


def main():
    """Extract starting goalies from all cached boxscores."""
    LOGGER.info("Creating database...")
    conn = create_database()
    cursor = conn.cursor()

    # Find all boxscore files
    boxscore_files = []
    for season_dir in CACHE_DIR.glob("20*"):
        boxscore_files.extend(season_dir.glob("*_boxscore.json"))

    LOGGER.info(f"Found {len(boxscore_files)} boxscore files")

    processed = 0
    success = 0

    for i, boxscore_path in enumerate(boxscore_files, 1):
        if i % 100 == 0:
            LOGGER.info(f"Progress: {i}/{len(boxscore_files)} ({i/len(boxscore_files)*100:.1f}%)")
            conn.commit()

        if process_boxscore(boxscore_path, cursor):
            success += 1
        processed += 1

    conn.commit()

    # Summary
    cursor.execute("SELECT COUNT(*) FROM starting_goalies")
    total_games = cursor.fetchone()[0]

    cursor.execute("SELECT season, COUNT(*) FROM starting_goalies GROUP BY season ORDER BY season")
    season_counts = cursor.fetchall()

    LOGGER.info(f"\n{'='*60}")
    LOGGER.info(f"Extraction complete!")
    LOGGER.info(f"Total boxscores processed: {processed}")
    LOGGER.info(f"Successfully extracted starters: {success}")
    LOGGER.info(f"Total games in database: {total_games}")
    LOGGER.info(f"\nBreakdown by season:")
    for season, count in season_counts:
        LOGGER.info(f"  {season}: {count} games")
    LOGGER.info(f"{'='*60}")

    # Show sample
    cursor.execute("""
        SELECT game_id, away_starter_name, home_starter_name
        FROM starting_goalies
        ORDER BY game_id DESC
        LIMIT 5
    """)
    LOGGER.info(f"\nSample (most recent 5 games):")
    for game_id, away_name, home_name in cursor.fetchall():
        LOGGER.info(f"  {game_id}: {away_name} @ {home_name}")

    conn.close()
    LOGGER.info(f"\nDatabase saved to: {DB_PATH}")


if __name__ == "__main__":
    main()
