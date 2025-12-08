"""
Starting Goalie Scraper - V7.7 Enhancement

Real-time starting goalie information with multi-source fallback:
1. Daily Faceoff (earliest confirmations, industry standard) - PRIMARY
2. NHL API (confirmed starters 1-2 hours before game) - SECONDARY
3. goaliePulse.json (predicted starters with likelihood) - FALLBACK

DATA LEAKAGE PROTECTION:
- Only uses pre-game information (gameState must be 'FUT' or 'PRE')
- Stores timestamps to track when starters were confirmed
- For historical backtesting, uses starting goalie database (post-game verified)

USAGE:
- Run throughout the day for Daily Faceoff updates
- Run 1-2 hours before games for NHL API confirmed starters
- Updates multiple times daily as more info becomes available
"""

from __future__ import annotations

import json
import logging
import re
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pandas as pd
import requests
from bs4 import BeautifulSoup

LOGGER = logging.getLogger(__name__)

# File paths
PROJECT_ROOT = Path(__file__).resolve().parents[2]
GOALIE_PULSE_PATH = PROJECT_ROOT / "web" / "src" / "data" / "goaliePulse.json"
STARTING_GOALIES_JSON = PROJECT_ROOT / "web" / "src" / "data" / "startingGoalies.json"
STARTING_GOALIES_DB = PROJECT_ROOT / "data" / "starting_goalies.db"

# NHL API endpoints
SCHEDULE_API = "https://api-web.nhle.com/v1/schedule"
GAME_API = "https://api-web.nhle.com/v1/gamecenter"

# Daily Faceoff (primary source for goalie confirmations)
DAILY_FACEOFF_URL = "https://www.dailyfaceoff.com/starting-goalies/"

# Team name to abbreviation mapping (Daily Faceoff uses full names)
TEAM_NAME_TO_ABBREV = {
    "Anaheim Ducks": "ANA", "Arizona Coyotes": "ARI", "Boston Bruins": "BOS",
    "Buffalo Sabres": "BUF", "Calgary Flames": "CGY", "Carolina Hurricanes": "CAR",
    "Chicago Blackhawks": "CHI", "Colorado Avalanche": "COL", "Columbus Blue Jackets": "CBJ",
    "Dallas Stars": "DAL", "Detroit Red Wings": "DET", "Edmonton Oilers": "EDM",
    "Florida Panthers": "FLA", "Los Angeles Kings": "LAK", "Minnesota Wild": "MIN",
    "Montreal Canadiens": "MTL", "Nashville Predators": "NSH", "New Jersey Devils": "NJD",
    "New York Islanders": "NYI", "New York Rangers": "NYR", "Ottawa Senators": "OTT",
    "Philadelphia Flyers": "PHI", "Pittsburgh Penguins": "PIT", "San Jose Sharks": "SJS",
    "Seattle Kraken": "SEA", "St. Louis Blues": "STL", "Tampa Bay Lightning": "TBL",
    "Toronto Maple Leafs": "TOR", "Utah Hockey Club": "UTA", "Vancouver Canucks": "VAN",
    "Vegas Golden Knights": "VGK", "Washington Capitals": "WSH", "Winnipeg Jets": "WPG",
}

# Status to confidence mapping for Daily Faceoff
DF_STATUS_CONFIDENCE = {
    "confirmed": 0.99,
    "expected": 0.85,
    "likely": 0.75,
    "probable": 0.65,
    "unconfirmed": 0.40,
    "unknown": 0.30,
}

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

    def fetch_daily_faceoff_starters(self, date: Optional[str] = None) -> Dict[str, Dict]:
        """
        Fetch starting goalie confirmations from Daily Faceoff.

        Daily Faceoff is the industry standard for goalie confirmations.
        They track confirmations throughout the day and provide status levels:
        - Confirmed: Officially announced by team
        - Expected: Very likely based on patterns
        - Likely/Probable: Good chance
        - Unconfirmed: Not yet known

        Args:
            date: Date in 'YYYY-MM-DD' format, or None for today

        Returns:
            Dict mapping team abbreviation to goalie info:
                {
                    'TOR': {
                        'goalie': 'Joseph Woll',
                        'status': 'confirmed',  # confirmed/expected/probable/unconfirmed
                        'confidence': 0.99,
                        'record': '8-3-1',
                        'gaa': 2.15,
                        'sv_pct': 0.912,
                        'opponent': 'BOS'
                    }
                }
        """
        _rate_limit()

        url = DAILY_FACEOFF_URL
        if date:
            url = f"{DAILY_FACEOFF_URL}{date}"

        LOGGER.info(f"Fetching Daily Faceoff starters from {url}")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
            }
            response = requests.get(url, headers=headers, timeout=15)
            response.raise_for_status()

            return self._parse_daily_faceoff_html(response.text)

        except requests.exceptions.RequestException as e:
            LOGGER.warning(f"Failed to fetch Daily Faceoff: {e}")
            return {}

    def _parse_daily_faceoff_html(self, html: str) -> Dict[str, Dict]:
        """
        Parse Daily Faceoff HTML to extract goalie data.

        The page embeds JSON data with fields like:
        - homeGoalieName / awayGoalieName
        - homeNewsStrengthName / awayNewsStrengthName (status)
        - homeTeamName / awayTeamName
        - Stats: wins, losses, GAA, SV%, etc.
        """
        starters = {}

        try:
            soup = BeautifulSoup(html, 'html.parser')

            # Method 1: Look for __NEXT_DATA__ JSON (Next.js apps)
            next_data = soup.find('script', id='__NEXT_DATA__')
            if next_data:
                try:
                    data = json.loads(next_data.string)
                    games = self._extract_from_next_data(data)
                    if games:
                        return games
                except json.JSONDecodeError:
                    pass

            # Method 2: Look for embedded JSON in script tags
            for script in soup.find_all('script'):
                if script.string and 'homeGoalieName' in script.string:
                    # Try to extract JSON objects from script
                    json_matches = re.findall(r'\{[^{}]*"homeGoalieName"[^{}]*\}', script.string)
                    for match in json_matches:
                        try:
                            game_data = json.loads(match)
                            self._process_game_json(game_data, starters)
                        except json.JSONDecodeError:
                            continue

            # Method 3: Parse HTML structure directly
            if not starters:
                starters = self._parse_html_structure(soup)

        except Exception as e:
            LOGGER.warning(f"Error parsing Daily Faceoff HTML: {e}")

        LOGGER.info(f"Parsed {len(starters)} goalie confirmations from Daily Faceoff")
        return starters

    def _extract_from_next_data(self, data: Dict) -> Dict[str, Dict]:
        """Extract goalie data from Next.js __NEXT_DATA__ structure."""
        starters = {}

        try:
            # Navigate to the props containing game data
            props = data.get('props', {}).get('pageProps', {})
            games = props.get('games', props.get('matchups', []))

            if not isinstance(games, list):
                games = [games] if games else []

            for game in games:
                self._process_game_json(game, starters)

        except Exception as e:
            LOGGER.debug(f"Could not extract from __NEXT_DATA__: {e}")

        return starters

    def _process_game_json(self, game: Dict, starters: Dict):
        """Process a single game JSON object from Daily Faceoff."""
        try:
            home_team_name = game.get('homeTeamName', '')
            away_team_name = game.get('awayTeamName', '')

            home_abbrev = TEAM_NAME_TO_ABBREV.get(home_team_name)
            away_abbrev = TEAM_NAME_TO_ABBREV.get(away_team_name)

            # Home goalie
            if home_abbrev and game.get('homeGoalieName'):
                status = (game.get('homeNewsStrengthName', 'unknown') or 'unknown').lower()
                starters[home_abbrev] = {
                    'goalie': game['homeGoalieName'],
                    'status': status,
                    'confidence': DF_STATUS_CONFIDENCE.get(status, 0.5),
                    'record': f"{game.get('homeGoalieWins', 0)}-{game.get('homeGoalieLosses', 0)}-{game.get('homeGoalieOvertimeLosses', 0)}",
                    'gaa': float(game.get('homeGoalieGoalsAgainstAvg', 0) or 0),
                    'sv_pct': float(game.get('homeGoalieSavePercentage', 0) or 0),
                    'opponent': away_abbrev,
                    'rating': game.get('homeGoalieRating'),
                }

            # Away goalie
            if away_abbrev and game.get('awayGoalieName'):
                status = (game.get('awayNewsStrengthName', 'unknown') or 'unknown').lower()
                starters[away_abbrev] = {
                    'goalie': game['awayGoalieName'],
                    'status': status,
                    'confidence': DF_STATUS_CONFIDENCE.get(status, 0.5),
                    'record': f"{game.get('awayGoalieWins', 0)}-{game.get('awayGoalieLosses', 0)}-{game.get('awayGoalieOvertimeLosses', 0)}",
                    'gaa': float(game.get('awayGoalieGoalsAgainstAvg', 0) or 0),
                    'sv_pct': float(game.get('awayGoalieSavePercentage', 0) or 0),
                    'opponent': home_abbrev,
                    'rating': game.get('awayGoalieRating'),
                }

        except Exception as e:
            LOGGER.debug(f"Could not process game JSON: {e}")

    def _parse_html_structure(self, soup: BeautifulSoup) -> Dict[str, Dict]:
        """Fallback: Parse HTML structure directly for goalie info."""
        starters = {}

        # Look for common patterns in goalie cards
        # This is a fallback if JSON extraction fails
        goalie_cards = soup.find_all(['div', 'article'], class_=re.compile(r'goalie|starter|matchup', re.I))

        for card in goalie_cards:
            try:
                # Look for team name
                team_elem = card.find(class_=re.compile(r'team', re.I))
                if not team_elem:
                    continue

                team_text = team_elem.get_text(strip=True)
                team_abbrev = None
                for name, abbrev in TEAM_NAME_TO_ABBREV.items():
                    if name.lower() in team_text.lower() or abbrev.lower() in team_text.lower():
                        team_abbrev = abbrev
                        break

                if not team_abbrev:
                    continue

                # Look for goalie name
                name_elem = card.find(class_=re.compile(r'name|player', re.I))
                if not name_elem:
                    continue

                goalie_name = name_elem.get_text(strip=True)

                # Look for status
                status_elem = card.find(class_=re.compile(r'status|confirm', re.I))
                status = 'unknown'
                if status_elem:
                    status_text = status_elem.get_text(strip=True).lower()
                    for key in DF_STATUS_CONFIDENCE:
                        if key in status_text:
                            status = key
                            break

                starters[team_abbrev] = {
                    'goalie': goalie_name,
                    'status': status,
                    'confidence': DF_STATUS_CONFIDENCE.get(status, 0.5),
                }

            except Exception:
                continue

        return starters

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

        Uses multi-source fallback (priority order):
        1. Daily Faceoff (earliest confirmations, industry standard)
        2. NHL API (confirmed starters 1-2 hours before game)
        3. goaliePulse for predicted starters (fallback)

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
                        'source': 'daily_faceoff',  # or 'nhl_api', 'goalie_pulse'
                        'confidence': 0.99,
                        'homeStatus': 'confirmed',  # Daily Faceoff status
                        'awayStatus': 'confirmed'
                    }
                }
        """
        # Get today's games
        games = self.fetch_todays_games(date)

        # Fetch from all sources
        df_starters = self.fetch_daily_faceoff_starters(date)
        pulse_predictions = self.load_goalie_pulse_predictions()

        starters = {}

        for game in games:
            game_id = game['gameId']
            home_team = game['homeTeamAbbrev']
            away_team = game['awayTeamAbbrev']

            # SOURCE 1: Daily Faceoff (primary - they do the hard work of tracking confirmations)
            df_home = df_starters.get(home_team)
            df_away = df_starters.get(away_team)

            if df_home or df_away:
                home_goalie = None
                away_goalie = None
                home_status = 'unknown'
                away_status = 'unknown'
                home_conf = 0.0
                away_conf = 0.0

                if df_home:
                    home_goalie = {'playerId': None, 'name': df_home['goalie']}
                    home_status = df_home['status']
                    home_conf = df_home['confidence']

                if df_away:
                    away_goalie = {'playerId': None, 'name': df_away['goalie']}
                    away_status = df_away['status']
                    away_conf = df_away['confidence']

                avg_confidence = (home_conf + away_conf) / 2.0 if df_home and df_away else max(home_conf, away_conf)

                starters[game_id] = {
                    'gameId': game_id,
                    'gameDate': game['gameDate'],
                    'homeTeam': home_team,
                    'awayTeam': away_team,
                    'homeGoalie': home_goalie,
                    'awayGoalie': away_goalie,
                    'source': 'daily_faceoff',
                    'confidence': avg_confidence,
                    'homeStatus': home_status,
                    'awayStatus': away_status,
                    'gameState': game['gameState']
                }

                status_emoji = '✓' if home_status == 'confirmed' and away_status == 'confirmed' else '◐'
                LOGGER.info(f"{status_emoji} Daily Faceoff: {away_team} @ {home_team} - "
                          f"{df_away.get('goalie', 'TBD') if df_away else 'TBD'} ({away_status}) vs "
                          f"{df_home.get('goalie', 'TBD') if df_home else 'TBD'} ({home_status})")
                continue

            # SOURCE 2: NHL API (backup for games close to start)
            confirmed = self.fetch_confirmed_starter(game_id)

            if confirmed and (confirmed.get('homeGoalie') or confirmed.get('awayGoalie')):
                starters[game_id] = {
                    'gameId': game_id,
                    'gameDate': game['gameDate'],
                    'homeTeam': home_team,
                    'awayTeam': away_team,
                    'homeGoalie': confirmed.get('homeGoalie'),
                    'awayGoalie': confirmed.get('awayGoalie'),
                    'source': 'nhl_api',
                    'confidence': 1.0,
                    'homeStatus': 'confirmed',
                    'awayStatus': 'confirmed',
                    'gameState': confirmed.get('gameState')
                }
                LOGGER.info(f"✓ NHL API confirmed: {away_team} @ {home_team}")
                continue

            # SOURCE 3: goaliePulse predictions (fallback)
            home_prediction = pulse_predictions.get(home_team)
            away_prediction = pulse_predictions.get(away_team)

            if home_prediction or away_prediction:
                home_goalie = {
                    'playerId': None,
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
                    'homeStatus': 'predicted',
                    'awayStatus': 'predicted',
                    'gameState': game['gameState']
                }
                LOGGER.info(f"⚠ goaliePulse fallback: {away_team} @ {home_team} (confidence: {avg_confidence:.1%})")

            else:
                LOGGER.warning(f"✗ No starter info available for {away_team} @ {home_team}")

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
                    'homeStatus': info.get('homeStatus', 'unknown'),
                    'awayStatus': info.get('awayStatus', 'unknown'),
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
    LOGGER.info("Starting Goalie Scraper - V7.7 (Daily Faceoff Integration)")
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
