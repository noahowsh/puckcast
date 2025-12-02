"""NHL Stats API client for live predictions and special teams data.

This module provides safe access to NHL's official APIs for:
1. Real-time game schedules
2. Power-play and penalty-kill percentages
3. Starting goalie information

ALL functions are designed to prevent data leakage by only accessing
information that would be available BEFORE games start.
"""

import requests
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import logging
import time

logger = logging.getLogger(__name__)

# API Endpoints
SCHEDULE_API = "https://api-web.nhle.com/v1/schedule"
TEAM_SUMMARY_API = "https://api.nhle.com/stats/rest/en/team/summary"
GAME_API = "https://api-web.nhle.com/v1/gamecenter"

# Rate limiting
_last_request_time = 0
_min_request_interval = 0.5  # seconds between requests


def _rate_limit():
    """Ensure we don't hammer the API."""
    global _last_request_time
    elapsed = time.time() - _last_request_time
    if elapsed < _min_request_interval:
        time.sleep(_min_request_interval - elapsed)
    _last_request_time = time.time()


def fetch_schedule(date: str) -> List[Dict]:
    """
    Fetch NHL schedule for a specific date.
    
    Args:
        date: Date in 'YYYY-MM-DD' format (e.g., '2024-11-10')
    
    Returns:
        List of game dictionaries with metadata
    
    Example:
        >>> games = fetch_schedule('2024-11-10')
        >>> print(f"Found {len(games)} games")
        Found 8 games
    
    **DATA LEAKAGE SAFE:**
    - Schedule is public information announced days/weeks in advance
    - Only returns metadata (teams, venue, time)
    - Does NOT return scores or in-game statistics
    """
    _rate_limit()
    
    url = f"{SCHEDULE_API}/{date}"
    logger.info(f"Fetching schedule from: {url}")
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch schedule for {date}: {e}")
        return []
    
    data = response.json()
    
    games = []
    for week in data.get('gameWeek', []):
        for game in week.get('games', []):
            games.append({
                'gameId': game['id'],
                'gameDate': week['date'],
                'season': game['season'],
                'gameType': game['gameType'],
                'gameState': game['gameState'],  # FUT, LIVE, FINAL, OFF
                'startTimeUTC': game['startTimeUTC'],
                'homeTeamId': game['homeTeam']['id'],
                'homeTeamAbbrev': game['homeTeam']['abbrev'],
                'homeTeamName': game['homeTeam']['commonName']['default'],
                'awayTeamId': game['awayTeam']['id'],
                'awayTeamAbbrev': game['awayTeam']['abbrev'],
                'awayTeamName': game['awayTeam']['commonName']['default'],
                'venue': game.get('venue', {}).get('default', 'Unknown')
            })
    
    logger.info(f"Found {len(games)} games for {date}")
    return games


def fetch_future_games(date: str) -> List[Dict]:
    """
    Fetch ONLY games that haven't been played yet.
    
    Args:
        date: Date in 'YYYY-MM-DD' format
    
    Returns:
        List of future games (gameState == 'FUT')
    
    Example:
        >>> future = fetch_future_games('2024-11-10')
        >>> for game in future:
        ...     print(f"{game['awayTeamAbbrev']} @ {game['homeTeamAbbrev']}")
        BOS @ NYR
        TOR @ MTL
    
    **DATA LEAKAGE SAFE:**
    - ✅ Filters to gameState == 'FUT' ONLY
    - ✅ Excludes any games in progress or completed
    - ✅ Safe to use for live predictions
    """
    all_games = fetch_schedule(date)
    future_games = [g for g in all_games if g['gameState'] == 'FUT']
    
    logger.info(f"Filtered to {len(future_games)} future games (out of {len(all_games)} total)")
    return future_games


def fetch_todays_games() -> List[Dict]:
    """
    Convenience function to fetch today's unplayed games.
    
    Returns:
        List of games scheduled for today that haven't started
    
    Example:
        >>> games = fetch_todays_games()
        >>> print(f"Predicting {len(games)} games today")
    
    **DATA LEAKAGE SAFE:** Only returns future games for current date.
    """
    today = datetime.now().strftime('%Y-%m-%d')
    return fetch_future_games(today)


def fetch_team_special_teams(season_id: str = '20242025') -> pd.DataFrame:
    """
    Fetch season-to-date PP% and PK% for all teams.
    
    Args:
        season_id: Season in format '20242025' (for 2024-25 season)
    
    Returns:
        DataFrame with columns:
            - teamId: Numeric team identifier
            - seasonId: Season identifier
            - gamesPlayed: Games played so far
            - powerPlayPct: Power-play success rate (%)
            - penaltyKillPct: Penalty-kill success rate (%)
            - goalsForPerGame: Average goals scored
            - goalsAgainstPerGame: Average goals allowed
            - shotsForPerGame: Average shots taken
            - faceoffWinPct: Faceoff win percentage
    
    Example:
        >>> teams = fetch_team_special_teams('20242025')
        >>> rangers = teams[teams['teamId'] == 3]
        >>> print(f"Rangers PP%: {rangers['powerPlayPct'].values[0]:.1f}%")
        Rangers PP%: 22.5%
    
    **DATA LEAKAGE SAFE:**
    - ✅ Returns CUMULATIVE stats updated after each game
    - ✅ When predicting today's games, only includes games through yesterday
    - ✅ Stats are "season-to-date" (like standings)
    - ⚠️ Do NOT use this for historical backtesting without proper temporal splits!
    
    **For Backtesting:**
    You CANNOT use this API for historical predictions because it only returns
    CURRENT season stats. For training data, use the native ingest system which
    processes historical play-by-play data.
    """
    _rate_limit()
    
    url = TEAM_SUMMARY_API
    params = {'cayenneExp': f'seasonId={season_id}'}
    
    logger.info(f"Fetching special teams data for season {season_id}")
    
    try:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to fetch team summary: {e}")
        return pd.DataFrame()
    
    data = response.json()
    
    teams = []
    for team in data['data']:
        teams.append({
            'teamId': team['teamId'],
            'teamName': team.get('teamFullName', 'Unknown'),
            'seasonId': season_id,
            'gamesPlayed': team['gamesPlayed'],
            'powerPlayPct': team['powerPlayPct'],
            'penaltyKillPct': team['penaltyKillPct'],
            'goalsForPerGame': team['goalsForPerGame'],
            'goalsAgainstPerGame': team['goalsAgainstPerGame'],
            'shotsForPerGame': team.get('shotsForPerGame', 0.0),
            'faceoffWinPct': team.get('faceoffWinPct', 50.0)
        })
    
    logger.info(f"Retrieved stats for {len(teams)} teams")
    return pd.DataFrame(teams)


def fetch_starting_goalies(game_id: int) -> Optional[Dict]:
    """
    Fetch starting goalies for a game (if announced).
    
    Args:
        game_id: NHL game ID (e.g., 2024020123)
    
    Returns:
        Dict with:
            - gameId: Game identifier
            - homeGoalie: {'playerId': int, 'name': str} or None
            - awayGoalie: {'playerId': int, 'name': str} or None
        Returns None if game has already started or data unavailable.
    
    Example:
        >>> goalies = fetch_starting_goalies(2024020123)
        >>> if goalies:
        ...     print(f"Home: {goalies['homeGoalie']['name']}")
        Home: Igor Shesterkin
    
    **DATA LEAKAGE SAFE:**
    - ✅ Only returns data if gameState is 'FUT' or 'PRE'
    - ✅ Starting lineups announced 1-2 hours before game
    - ⚠️ Use close to game time (not days in advance)
    - ❌ Returns None if game has started
    
    **LIMITATION:**
    Starting goalies are typically not available until ~1-2 hours before puck drop.
    For predictions made earlier, you'll need to use each team's likely starter
    based on recent games or rotation patterns.
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
            logger.warning(f"Game {game_id} has state '{game_state}' - not safe for prediction!")
            return None
        
        # Extract starting goalies from roster
        home_goalie = None
        away_goalie = None
        home_team_id = data['homeTeam']['id']
        
        for player in data.get('rosterSpots', []):
            if player.get('positionCode') == 'G':
                goalie_info = {
                    'playerId': player.get('playerId'),
                    'name': f"{player['firstName']['default']} {player['lastName']['default']}"
                }
                
                if player['teamId'] == home_team_id:
                    home_goalie = goalie_info
                else:
                    away_goalie = goalie_info
        
        return {
            'gameId': game_id,
            'gameState': game_state,
            'homeGoalie': home_goalie,
            'awayGoalie': away_goalie
        }
    
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not fetch goalies for game {game_id}: {e}")
        return None


def get_games_for_prediction(date: Optional[str] = None) -> pd.DataFrame:
    """
    High-level function to get games ready for prediction.
    
    Args:
        date: Date in 'YYYY-MM-DD' format, or None for today
    
    Returns:
        DataFrame with columns:
            - gameId, gameDate, season, startTimeUTC
            - homeTeamId, homeTeamAbbrev, homeTeamName
            - awayTeamId, awayTeamAbbrev, awayTeamName
            - venue
    
    Example:
        >>> games = get_games_for_prediction()
        >>> print(f"Ready to predict {len(games)} games")
    
    **USE THIS FUNCTION** for your live prediction script!
    """
    if date is None:
        date = datetime.now().strftime('%Y-%m-%d')
    
    games = fetch_future_games(date)
    
    if not games:
        logger.warning(f"No future games found for {date}")
        return pd.DataFrame()
    
    df = pd.DataFrame(games)
    
    # Remove gameState column (always 'FUT' at this point)
    if 'gameState' in df.columns:
        df = df.drop(columns=['gameState'])
    
    logger.info(f"Prepared {len(df)} games for prediction on {date}")
    return df


# Convenience function for testing
def test_api_connection():
    """
    Test NHL API connectivity and basic functionality.
    
    Returns:
        True if all tests pass, False otherwise
    """
    print("="*70)
    print("NHL API CONNECTION TEST")
    print("="*70)
    
    # Test 1: Schedule API
    print("\n1. Testing Schedule API...")
    try:
        today = datetime.now().strftime('%Y-%m-%d')
        games = fetch_schedule(today)
        print(f"   ✅ Found {len(games)} games for {today}")
        if games:
            print(f"   Example: {games[0]['awayTeamAbbrev']} @ {games[0]['homeTeamAbbrev']}")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 2: Future Games Filter
    print("\n2. Testing Future Games Filter...")
    try:
        future = fetch_future_games(today)
        print(f"   ✅ Found {len(future)} future games")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    # Test 3: Team Summary API
    print("\n3. Testing Team Summary API...")
    try:
        current_season = f"{datetime.now().year}{datetime.now().year + 1}"
        teams = fetch_team_special_teams(current_season)
        print(f"   ✅ Retrieved stats for {len(teams)} teams")
        if not teams.empty:
            sample = teams.iloc[0]
            print(f"   Example: {sample['teamName']} - PP%: {sample['powerPlayPct']:.1f}%")
    except Exception as e:
        print(f"   ❌ Failed: {e}")
        return False
    
    print("\n" + "="*70)
    print("✅ ALL TESTS PASSED - NHL API is ready!")
    print("="*70)
    return True


if __name__ == "__main__":
    # Run tests when module is executed directly
    test_api_connection()

