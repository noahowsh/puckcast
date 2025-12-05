"""
Starting Goalie Scraper - V7.6 Enhancement

Real-time starting goalie information with multi-source fallback:
1. NHL API (confirmed starters 1-2 hours before game) - PRIMARY
2. goaliePulse.json (predicted starters with likelihood) - FALLBACK
3. Daily Faceoff / Team announcements (future enhancement) - FUTURE

DATA LEAKAGE PROTECTION:
- Only uses pre-game information (gameState must be 'FUT' or 'PRE')
- Stores timestamps to track when starters were confirmed
- For historical backtesting, uses starting goalie database (post-game verified)

USAGE:
- Run 1-2 hours before games for confirmed starters
- Run earlier in day for probability-based predictions
- Updates multiple times daily as more info becomes available
"""

from __future__ import annotations

import json
import logging
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests

LOGGER = logging.getLogger(__name__)

# File paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOALIE_PULSE_PATH = PROJECT_ROOT / "web" / "src" / "data" / "goaliePulse.json"
STARTING_GOALIES_JSON = PROJECT_ROOT / "web" / "src" / "data" / "startingGoalies.json"
STARTING_GOALIES_DB = PROJECT_ROOT / "data" / "starting_goalies.db"

# NHL API endpoints
SCHEDULE_API = "https://api-web.nhle.com/v1/schedule"
GAME_API = "https://api-web.nhle.com/v1/gamecenter"

# Rate limiting
_LAST_REQUEST_TIME = 0
_MIN_REQUEST_INTERVAL = 0.5  # seconds


def _rate_limit():
    """Ensure we don't hammer the API."""
    import time
    global _LAST_REQUEST_TIME
    elapsed = time.time() - _LAST_REQUEST_TIME
    if elapsed < _MIN_REQUEST_INTERVAL:
        time.sleep(_MIN_REQUEST_INTERVAL - elapsed)
    _LAST_REQUEST_TIME = time.time()


class StartingGoalieScraper:
    """
    Scrapes and manages starting goalie information from multiple sources.

    Data Sources (in priority order):
    1. NHL API (confirmed starters, 1-2 hours before game)
    2. goaliePulse.json (predicted starters with likelihood)
    3. Historical database (for backtesting - post-game verified)
    """

    def __init__(self, db_path: Path = STARTING_GOALIES_DB):
        """Initialize scraper with database connection."""
        self.db_path = db_path
        self._ensure_db_exists()

    def _ensure_db_exists(self):
        """Create database schema if it doesn't exist."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Table: confirmed_starters (from NHL API)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS confirmed_starters (
                game_id TEXT,
                game_date TEXT,
                home_team TEXT,
                away_team TEXT,
                home_goalie_id INTEGER,
                home_goalie_name TEXT,
                away_goalie_id INTEGER,
                away_goalie_name TEXT,
                confirmed_at TIMESTAMP,
                source TEXT,  -- 'nhl_api', 'goalie_pulse', 'manual'
                PRIMARY KEY (game_id, confirmed_at)
            )
        """)

        # Table: goalie_predictions (from goaliePulse)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS goalie_predictions (
                game_date TEXT,
                team TEXT,
                goalie_name TEXT,
                start_likelihood REAL,
                rolling_gsa REAL,
                season_gsa REAL,
                rest_days INTEGER,
                trend TEXT,
                predicted_at TIMESTAMP,
                PRIMARY KEY (game_date, team, predicted_at)
            )
        """)

        conn.commit()
        conn.close()

    def fetch_todays_games(self, date: Optional[str] = None) -> List[Dict]:
        """
        Fetch today's NHL schedule.

        Args:
            date: Date in 'YYYY-MM-DD' format, or None for today

        Returns:
            List of game dictionaries with metadata
        """
        if date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        _rate_limit()

        url = f"{SCHEDULE_API}/{date}"
        LOGGER.info(f"Fetching schedule for {date}...")

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            LOGGER.error(f"Failed to fetch schedule: {e}")
            return []

        data = response.json()

        games = []
        for week in data.get('gameWeek', []):
            for game in week.get('games', []):
                # Only include regular season and playoff games
                if game['gameType'] not in [2, 3]:  # 2=regular, 3=playoffs
                    continue

                games.append({
                    'gameId': str(game['id']),
                    'gameDate': week['date'],
                    'season': game['season'],
                    'gameType': game['gameType'],
                    'gameState': game['gameState'],  # FUT, LIVE, FINAL, OFF
                    'startTimeUTC': game['startTimeUTC'],
                    'homeTeamId': game['homeTeam']['id'],
                    'homeTeamAbbrev': game['homeTeam']['abbrev'],
                    'awayTeamId': game['awayTeam']['id'],
                    'awayTeamAbbrev': game['awayTeam']['abbrev'],
                })

        LOGGER.info(f"Found {len(games)} games for {date}")
        return games

    def fetch_confirmed_starter(self, game_id: str) -> Optional[Dict]:
        """
        Fetch confirmed starting goalies from NHL API.

        CRITICAL: Only returns data if game hasn't started (gameState = 'FUT' or 'PRE')

        Args:
            game_id: NHL game ID (e.g., '2024020123')

        Returns:
            Dict with:
                - gameId, homeTeam, awayTeam
                - homeGoalie: {'playerId': int, 'name': str} or None
                - awayGoalie: {'playerId': int, 'name': str} or None
                - gameState: Current game state
            Returns None if game has started or data unavailable
        """
        _rate_limit()

        url = f"{GAME_API}/{game_id}/landing"

        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()

            # CRITICAL: Check game hasn't started
            game_state = data.get('gameState', 'UNKNOWN')
            if game_state not in ['FUT', 'PRE']:
                LOGGER.warning(f"Game {game_id} has state '{game_state}' - not safe for prediction!")
                return None

            # Extract starting goalies from roster/lineup
            home_goalie = None
            away_goalie = None
            home_team_id = data['homeTeam']['id']

            # Check rosterSpots for starting lineup
            for player in data.get('rosterSpots', []):
                if player.get('positionCode') != 'G':
                    continue

                goalie_info = {
                    'playerId': player.get('playerId'),
                    'name': f"{player.get('firstName', {}).get('default', '')} {player.get('lastName', {}).get('default', '')}".strip()
                }

                if player['teamId'] == home_team_id:
                    home_goalie = goalie_info
                else:
                    away_goalie = goalie_info

            return {
                'gameId': game_id,
                'gameState': game_state,
                'homeTeam': data['homeTeam']['abbrev'],
                'awayTeam': data['awayTeam']['abbrev'],
                'homeGoalie': home_goalie,
                'awayGoalie': away_goalie,
                'confirmedAt': datetime.now().isoformat()
            }

        except requests.exceptions.RequestException as e:
            LOGGER.warning(f"Could not fetch goalies for game {game_id}: {e}")
            return None

    def load_goalie_pulse_predictions(self) -> Dict[str, Dict]:
        """
        Load predicted starters from goaliePulse.json.

        Returns:
            Dict mapping team abbreviation to goalie prediction:
                {
                    'TOR': {
                        'name': 'Joseph Woll',
                        'startLikelihood': 0.7,
                        'rollingGsa': 1.4,
                        'seasonGsa': 2.8,
                        'restDays': 3,
                        'trend': 'steady'
                    }
                }
        """
        if not GOALIE_PULSE_PATH.exists():
            LOGGER.warning(f"goaliePulse.json not found at {GOALIE_PULSE_PATH}")
            return {}

        try:
            with open(GOALIE_PULSE_PATH, 'r') as f:
                data = json.load(f)

            predictions = {}
            for goalie in data.get('goalies', []):
                team = goalie.get('team', '').strip().upper()
                if not team:
                    continue

                # Only include if start likelihood is significant (> 0.3)
                likelihood = float(goalie.get('startLikelihood', 0.0))
                if likelihood < 0.3:
                    continue

                # If multiple goalies for same team, take highest likelihood
                if team in predictions and predictions[team]['startLikelihood'] >= likelihood:
                    continue

                predictions[team] = {
                    'name': goalie.get('name', ''),
                    'startLikelihood': likelihood,
                    'rollingGsa': float(goalie.get('rollingGsa', 0.0)),
                    'seasonGsa': float(goalie.get('seasonGsa', 0.0)),
                    'restDays': int(goalie.get('restDays', 0)),
                    'trend': goalie.get('trend', 'stable')
                }

            LOGGER.info(f"Loaded {len(predictions)} goalie predictions from goaliePulse.json")
            return predictions

        except (json.JSONDecodeError, OSError) as e:
            LOGGER.error(f"Failed to load goaliePulse.json: {e}")
            return {}

    def scrape_starters_for_date(self, date: Optional[str] = None) -> Dict[str, Dict]:
        """
        Scrape starting goalies for a specific date.

        Uses multi-source fallback:
        1. NHL API for confirmed starters (if available)
        2. goaliePulse for predicted starters (fallback)

        Args:
            date: Date in 'YYYY-MM-DD' format, or None for today

        Returns:
            Dict mapping game_id to starter info:
                {
                    '2024020123': {
                        'gameId': '2024020123',
                        'homeTeam': 'TOR',
                        'awayTeam': 'BOS',
                        'homeGoalie': {'playerId': 8477974, 'name': 'Joseph Woll'},
                        'awayGoalie': {'playerId': 8476792, 'name': 'Jeremy Swayman'},
                        'source': 'nhl_api',  # or 'goalie_pulse'
                        'confidence': 1.0  # 1.0 for confirmed, 0.3-0.95 for predicted
                    }
                }
        """
        # Get today's games
        games = self.fetch_todays_games(date)

        # Load goaliePulse predictions as fallback
        pulse_predictions = self.load_goalie_pulse_predictions()

        starters = {}

        for game in games:
            game_id = game['gameId']
            home_team = game['homeTeamAbbrev']
            away_team = game['awayTeamAbbrev']

            # Try to get confirmed starters from NHL API
            confirmed = self.fetch_confirmed_starter(game_id)

            if confirmed and (confirmed.get('homeGoalie') or confirmed.get('awayGoalie')):
                # We have confirmed starters
                starters[game_id] = {
                    'gameId': game_id,
                    'gameDate': game['gameDate'],
                    'homeTeam': home_team,
                    'awayTeam': away_team,
                    'homeGoalie': confirmed.get('homeGoalie'),
                    'awayGoalie': confirmed.get('awayGoalie'),
                    'source': 'nhl_api',
                    'confidence': 1.0,  # Confirmed
                    'gameState': confirmed.get('gameState')
                }
                LOGGER.info(f"✓ Confirmed starters for {home_team} vs {away_team}")

            else:
                # Fall back to goaliePulse predictions
                home_prediction = pulse_predictions.get(home_team)
                away_prediction = pulse_predictions.get(away_team)

                if home_prediction or away_prediction:
                    home_goalie = {
                        'playerId': None,  # Don't have ID from pulse
                        'name': home_prediction['name']
                    } if home_prediction else None

                    away_goalie = {
                        'playerId': None,
                        'name': away_prediction['name']
                    } if away_prediction else None

                    avg_confidence = (
                        (home_prediction['startLikelihood'] if home_prediction else 0.0) +
                        (away_prediction['startLikelihood'] if away_prediction else 0.0)
                    ) / 2.0

                    starters[game_id] = {
                        'gameId': game_id,
                        'gameDate': game['gameDate'],
                        'homeTeam': home_team,
                        'awayTeam': away_team,
                        'homeGoalie': home_goalie,
                        'awayGoalie': away_goalie,
                        'source': 'goalie_pulse',
                        'confidence': avg_confidence,
                        'gameState': game['gameState']
                    }
                    LOGGER.info(f"⚠ Using predicted starters for {home_team} vs {away_team} (confidence: {avg_confidence:.1%})")

                else:
                    LOGGER.warning(f"✗ No starter info available for {home_team} vs {away_team}")

        return starters

    def save_starters_to_db(self, starters: Dict[str, Dict]):
        """
        Save confirmed/predicted starters to database.

        Args:
            starters: Dict from scrape_starters_for_date()
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for game_id, info in starters.items():
            cursor.execute("""
                INSERT OR REPLACE INTO confirmed_starters
                (game_id, game_date, home_team, away_team,
                 home_goalie_id, home_goalie_name,
                 away_goalie_id, away_goalie_name,
                 confirmed_at, source)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                info['gameId'],
                info['gameDate'],
                info['homeTeam'],
                info['awayTeam'],
                info.get('homeGoalie', {}).get('playerId') if info.get('homeGoalie') else None,
                info.get('homeGoalie', {}).get('name') if info.get('homeGoalie') else None,
                info.get('awayGoalie', {}).get('playerId') if info.get('awayGoalie') else None,
                info.get('awayGoalie', {}).get('name') if info.get('awayGoalie') else None,
                datetime.now().isoformat(),
                info['source']
            ))

        conn.commit()
        conn.close()

        LOGGER.info(f"✓ Saved {len(starters)} starter records to database")

    def save_starters_to_json(self, starters: Dict[str, Dict], output_path: Path = STARTING_GOALIES_JSON):
        """
        Save starters to JSON file for web app.

        Args:
            starters: Dict from scrape_starters_for_date()
            output_path: Where to save JSON file
        """
        # Convert to web-friendly format
        output = {
            'generatedAt': datetime.now().isoformat(),
            'date': list(starters.values())[0]['gameDate'] if starters else datetime.now().strftime('%Y-%m-%d'),
            'games': [
                {
                    'gameId': info['gameId'],
                    'homeTeam': info['homeTeam'],
                    'awayTeam': info['awayTeam'],
                    'homeGoalie': info.get('homeGoalie', {}).get('name') if info.get('homeGoalie') else None,
                    'awayGoalie': info.get('awayGoalie', {}).get('name') if info.get('awayGoalie') else None,
                    'source': info['source'],
                    'confidence': info['confidence']
                }
                for info in starters.values()
            ]
        }

        with open(output_path, 'w') as f:
            json.dump(output, f, indent=2)

        LOGGER.info(f"✓ Saved starters to {output_path}")


def main():
    """Main function to scrape and save starting goalies."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')

    scraper = StartingGoalieScraper()

    # Scrape starters for today
    LOGGER.info("="*80)
    LOGGER.info("Starting Goalie Scraper - V7.6")
    LOGGER.info("="*80)

    starters = scraper.scrape_starters_for_date()

    if starters:
        LOGGER.info(f"\nFound starters for {len(starters)} games:")
        for game_id, info in starters.items():
            home = info['homeTeam']
            away = info['awayTeam']
            home_g = info.get('homeGoalie', {}).get('name', 'TBD') if info.get('homeGoalie') else 'TBD'
            away_g = info.get('awayGoalie', {}).get('name', 'TBD') if info.get('awayGoalie') else 'TBD'
            source = info['source']
            conf = info['confidence']

            LOGGER.info(f"  {away} @ {home}: {away_g} vs {home_g} ({source}, {conf:.0%})")

        # Save to database and JSON
        scraper.save_starters_to_db(starters)
        scraper.save_starters_to_json(starters)

        LOGGER.info("\n✓ Starting goalie scrape complete!")

    else:
        LOGGER.warning("No starters found for today")


if __name__ == "__main__":
    main()
