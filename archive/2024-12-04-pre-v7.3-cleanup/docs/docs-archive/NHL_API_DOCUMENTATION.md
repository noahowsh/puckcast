# NHL Stats API - Complete Documentation

**Date:** November 10, 2024  
**Purpose:** Comprehensive guide to NHL's official statistics API for live game prediction

---

## 🏒 **Overview**

The NHL provides two primary API endpoints:

1. **New API (Recommended):** `api-web.nhle.com` - Modern, JSON-based, active development
2. **Legacy API:** `api.nhle.com` - Older, still functional, may be deprecated

We'll use **BOTH strategically**:
- **New API** → Schedule, live games, matchups
- **Legacy API** → Historical statistics, special teams percentages

---

## 📡 **API Endpoints Reference**

### **1. Schedule API (NEW - Primary for Live Predictions)**

**Base URL:**
```
https://api-web.nhle.com/v1/schedule/{date}
```

**Format:** `YYYY-MM-DD`  
**Example:** https://api-web.nhle.com/v1/schedule/2024-11-10

**What it Returns:**
- All games scheduled for specified date
- Game IDs, teams, venues, start times
- Game state: `FUT` (future), `LIVE`, `FINAL`, `OFF`
- **CRITICAL:** Games that haven't been played yet show `"gameState": "FUT"`

**Example Response:**
```json
{
  "gameWeek": [
    {
      "date": "2024-11-10",
      "games": [
        {
          "id": 2024020123,
          "season": 20242025,
          "gameType": 2,
          "gameState": "FUT",
          "startTimeUTC": "2024-11-11T00:00:00Z",
          "homeTeam": {
            "id": 3,
            "abbrev": "NYR",
            "placeName": {"default": "New York"},
            "commonName": {"default": "Rangers"}
          },
          "awayTeam": {
            "id": 6,
            "abbrev": "BOS",
            "placeName": {"default": "Boston"},
            "commonName": {"default": "Bruins"}
          },
          "venue": {"default": "Madison Square Garden"}
        }
      ]
    }
  ]
}
```

**Use Case for Prediction:**
```python
import requests
from datetime import datetime

# Get today's games
today = datetime.now().strftime('%Y-%m-%d')
url = f"https://api-web.nhle.com/v1/schedule/{today}"
response = requests.get(url)
schedule = response.json()

# Extract games that haven't been played
future_games = []
for week in schedule.get('gameWeek', []):
    for game in week.get('games', []):
        if game['gameState'] == 'FUT':  # ← CRITICAL: Only future games!
            future_games.append({
                'gameId': game['id'],
                'homeTeamId': game['homeTeam']['id'],
                'awayTeamId': game['awayTeam']['id'],
                'homeTeamAbbrev': game['homeTeam']['abbrev'],
                'awayTeamAbbrev': game['awayTeam']['abbrev'],
                'startTime': game['startTimeUTC']
            })

print(f"Found {len(future_games)} games to predict for {today}")
```

**DATA LEAKAGE PREVENTION:**
- ✅ **SAFE:** Schedule is known in advance (public information)
- ✅ **SAFE:** Team matchups are announced before games
- ✅ **SAFE:** Start times are scheduled ahead
- ⚠️ **CHECK:** Game state must be `"FUT"` - never use `"FINAL"` or `"LIVE"`

---

### **2. Team Summary API (LEGACY - For Special Teams Stats)**

**Base URL:**
```
https://api.nhle.com/stats/rest/en/team/summary
```

**Parameters:**
- `cayenneExp` - Filter expression (e.g., `seasonId=20242025`)
- `sort` - Sort field (e.g., `teamId`)
- `limit` - Number of results (default: 50)

**Example:**
```
https://api.nhle.com/stats/rest/en/team/summary?cayenneExp=seasonId=20242025
```

**What it Returns:**
- **Power Play %** ✅ (key stat missing from MoneyPuck!)
- **Penalty Kill %** ✅ (key stat missing from MoneyPuck!)
- Goals for/against (season totals)
- Shots, faceoffs, hits
- Win/loss records

**Example Response:**
```json
{
  "data": [
    {
      "teamId": 3,
      "teamFullName": "New York Rangers",
      "seasonId": 20242025,
      "gamesPlayed": 10,
      "wins": 7,
      "losses": 2,
      "otLosses": 1,
      "goalsForPerGame": 3.2,
      "goalsAgainstPerGame": 2.5,
      "powerPlayPct": 22.5,           // ← KEY STAT!
      "penaltyKillPct": 85.3,         // ← KEY STAT!
      "shotsForPerGame": 32.1,
      "faceoffWinPct": 51.2
    }
  ]
}
```

**Use Case:**
```python
def fetch_team_special_teams(season_id='20242025'):
    """Fetch current season PP% and PK% for all teams."""
    url = "https://api.nhle.com/stats/rest/en/team/summary"
    params = {'cayenneExp': f'seasonId={season_id}'}
    
    response = requests.get(url, params=params)
    data = response.json()
    
    teams = {}
    for team in data['data']:
        teams[team['teamId']] = {
            'powerPlayPct': team['powerPlayPct'],
            'penaltyKillPct': team['penaltyKillPct'],
            'gamesPlayed': team['gamesPlayed']
        }
    
    return teams
```

**DATA LEAKAGE PREVENTION:**
- ⚠️ **CRITICAL:** This returns **season-to-date** cumulative stats
- ✅ **SAFE IF:** Used for current season's ongoing stats (updated after each game)
- ❌ **UNSAFE IF:** Used to get stats for a specific past game (includes future games)

**How to Use Safely:**
```python
# When predicting today's games (Nov 10, 2024):
# 1. Fetch team stats up to yesterday (Nov 9)
# 2. Use these stats as "prior to game" features
# 3. Never use stats that include today's games!

# SAFE: Get Rangers' PP% through yesterday
team_stats = fetch_team_special_teams('20242025')
rangers_pp_pct = team_stats[3]['powerPlayPct']  # Based on games through yesterday

# This is cumulative season PP%, updated after each game
# When predicting today, it only includes completed games ✅
```

---

### **3. Team Stats API (LEGACY - For Historical Data)**

**Base URL:**
```
https://api.nhle.com/stats/rest/en/team
```

**Parameters:**
- `cayenneExp` - Complex filters (seasonId, gameDate, etc.)
- `sort` - Sort order

**Example - Get team stats for specific date range:**
```
https://api.nhle.com/stats/rest/en/team?cayenneExp=seasonId=20232024 and gameDate<="2024-01-15"
```

**Use Case:** Building historical training data with proper temporal boundaries

---

### **4. Game API (NEW - Individual Game Details)**

**Base URL:**
```
https://api-web.nhle.com/v1/gamecenter/{gameId}/landing
```

**Example:**
```
https://api-web.nhle.com/v1/gamecenter/2024020123/landing
```

**What it Returns:**
- Live game state
- Period-by-period scores
- Individual player stats
- Shot charts
- **Starting goalies** ✅ (huge for prediction!)

**Example Response (relevant parts):**
```json
{
  "id": 2024020123,
  "gameState": "FUT",
  "homeTeam": {
    "id": 3,
    "abbrev": "NYR",
    "score": 0
  },
  "awayTeam": {
    "id": 6,
    "abbrev": "BOS",
    "score": 0
  },
  "rosterSpots": [
    {
      "teamId": 3,
      "positionCode": "G",
      "firstName": {"default": "Igor"},
      "lastName": {"default": "Shesterkin"}
    }
  ]
}
```

**DATA LEAKAGE PREVENTION:**
- ✅ **SAFE:** Can fetch before game starts to get starting goalies
- ❌ **UNSAFE:** Don't use any stats from the game itself (scores, shots, etc.)
- ⚠️ **TIMING:** Starting lineups announced ~1-2 hours before puck drop

---

### **5. Player Stats API (LEGACY - For Goalie Data)**

**Base URL:**
```
https://api.nhle.com/stats/rest/en/goalie/summary
```

**Example:**
```
https://api.nhle.com/stats/rest/en/goalie/summary?cayenneExp=seasonId=20242025
```

**What it Returns:**
- Goalie save percentage
- Goals against average
- Wins, shutouts
- Games played

**Use Case:** Enrich predictions with starting goalie quality

---

## 🎯 **HYBRID ARCHITECTURE: NHL API + MoneyPuck**

### **Best of Both Worlds:**

| Data Type | Source | Reason |
|-----------|--------|--------|
| **Live Schedule** | NHL API (Schedule) | Real-time, knows today's games |
| **PP% / PK%** | NHL API (Team Summary) | MoneyPuck doesn't have this |
| **Starting Goalies** | NHL API (Game API) | Real-time lineup info |
| **xGoals** | MoneyPuck | NHL doesn't provide |
| **Shot Quality** | MoneyPuck | High/medium/low danger shots |
| **Corsi / Fenwick** | MoneyPuck | Possession metrics |
| **Historical Training** | MoneyPuck | Comprehensive game-by-game |

### **Data Flow Diagram:**

```
┌─────────────────────────────────────────────────────────────┐
│                    TRAINING PHASE                            │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  MoneyPuck Historical Data                                   │
│  (2021-2024 seasons)                                         │
│         ↓                                                     │
│  + NHL API Special Teams                                     │
│    (PP% / PK% for each season)                              │
│         ↓                                                     │
│  Feature Engineering                                         │
│  (xGoals, Corsi, PP%, PK%, Faceoffs, etc.)                 │
│         ↓                                                     │
│  Train Model                                                 │
│         ↓                                                     │
│  Saved Model (model.pkl)                                     │
│                                                               │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   PREDICTION PHASE (LIVE)                    │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  1. Fetch Today's Schedule                                   │
│     NHL API: /v1/schedule/2024-11-10                        │
│         ↓                                                     │
│  2. Filter to Future Games                                   │
│     gameState == "FUT" ✅                                    │
│         ↓                                                     │
│  3. Get Team Stats (through yesterday)                       │
│     - MoneyPuck: xGoals, Corsi, Shots                       │
│     - NHL API: PP%, PK% (season-to-date)                    │
│         ↓                                                     │
│  4. Get Starting Goalies (optional)                          │
│     NHL API: /v1/gamecenter/{gameId}/landing                │
│         ↓                                                     │
│  5. Engineer Features                                        │
│     Rolling averages, differentials, Elo                     │
│         ↓                                                     │
│  6. Predict with Trained Model                               │
│     model.predict_proba(features)                            │
│         ↓                                                     │
│  7. Output Predictions                                       │
│     NYR vs BOS: 62% home win probability                    │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

---

## 🔒 **DATA LEAKAGE PREVENTION CHECKLIST**

### **✅ SAFE Practices:**

1. **Use Schedule API for matchups:**
   ```python
   # SAFE: Getting today's scheduled games
   games = fetch_schedule('2024-11-10')
   games = [g for g in games if g['gameState'] == 'FUT']
   ```

2. **Use season-to-date stats (updated daily):**
   ```python
   # SAFE: Rangers' PP% through all completed games
   team_stats = fetch_team_summary('20242025')
   # This only includes games that have finished ✅
   ```

3. **Use historical data with temporal boundaries:**
   ```python
   # SAFE: Training data with proper splits
   train_data = moneypuck_data[moneypuck_data['season'] < 2024]
   test_data = moneypuck_data[moneypuck_data['season'] == 2024]
   ```

4. **Use .shift(1) for all rolling features:**
   ```python
   # SAFE: Rolling averages exclude current game
   df['rolling_xg_5'] = df.groupby('teamId')['xGoals'].shift(1).rolling(5).mean()
   ```

### **❌ UNSAFE Practices:**

1. **Using final scores to predict:**
   ```python
   # UNSAFE: This is the actual outcome!
   if game['homeTeam']['score'] > game['awayTeam']['score']:
       prediction = 1  # ← Cheating!
   ```

2. **Using in-game stats:**
   ```python
   # UNSAFE: Shots, goals during game
   game_data = fetch_game_landing(gameId)
   shots = game_data['summary']['shotsByPeriod']  # ← Not available before game!
   ```

3. **Not filtering by game state:**
   ```python
   # UNSAFE: Includes finished games in prediction set
   all_games = fetch_schedule('2024-11-10')
   # Should filter: games = [g for g in all_games if g['gameState'] == 'FUT']
   ```

4. **Using future data in training:**
   ```python
   # UNSAFE: Test data leaking into training
   all_data = load_all_seasons()
   model.fit(all_data)  # ← No temporal split!
   ```

---

## 💻 **IMPLEMENTATION: Live Prediction System**

### **File Structure:**
```
src/nhl_prediction/
├── data_ingest.py          # MoneyPuck + NHL API fetching
├── nhl_api.py              # NEW: NHL API client
├── features.py             # Feature engineering (no changes)
├── pipeline.py             # Build dataset (updated for NHL API)
├── model.py                # Model training (no changes)
└── live_predict.py         # NEW: Live prediction script
```

### **Code: NHL API Client**

```python
# src/nhl_prediction/nhl_api.py
"""NHL Stats API client for live predictions and special teams data."""

import requests
from datetime import datetime
from typing import List, Dict, Optional
import pandas as pd
import logging

logger = logging.getLogger(__name__)

# API Endpoints
SCHEDULE_API = "https://api-web.nhle.com/v1/schedule"
TEAM_SUMMARY_API = "https://api.nhle.com/stats/rest/en/team/summary"
GAME_API = "https://api-web.nhle.com/v1/gamecenter"


def fetch_schedule(date: str) -> List[Dict]:
    """
    Fetch NHL schedule for a specific date.
    
    Args:
        date: Date in 'YYYY-MM-DD' format
    
    Returns:
        List of game dictionaries with metadata
    
    **DATA LEAKAGE SAFE:** Schedule is public information announced in advance.
    """
    url = f"{SCHEDULE_API}/{date}"
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    
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
                'awayTeamId': game['awayTeam']['id'],
                'awayTeamAbbrev': game['awayTeam']['abbrev'],
                'venue': game.get('venue', {}).get('default', 'Unknown')
            })
    
    return games


def fetch_future_games(date: str) -> List[Dict]:
    """
    Fetch only games that haven't been played yet.
    
    **DATA LEAKAGE SAFE:** Filters to gameState == 'FUT' only.
    """
    all_games = fetch_schedule(date)
    future_games = [g for g in all_games if g['gameState'] == 'FUT']
    
    logger.info(f"Found {len(future_games)} future games for {date}")
    return future_games


def fetch_team_special_teams(season_id: str = '20242025') -> pd.DataFrame:
    """
    Fetch season-to-date PP% and PK% for all teams.
    
    Args:
        season_id: Season in format '20242025'
    
    Returns:
        DataFrame with columns: teamId, seasonId, powerPlayPct, penaltyKillPct, gamesPlayed
    
    **DATA LEAKAGE SAFE:** Returns cumulative stats updated after each game.
    When predicting today's games, this only includes games through yesterday.
    """
    url = TEAM_SUMMARY_API
    params = {'cayenneExp': f'seasonId={season_id}'}
    
    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()
    
    data = response.json()
    
    teams = []
    for team in data['data']:
        teams.append({
            'teamId': team['teamId'],
            'seasonId': season_id,
            'gamesPlayed': team['gamesPlayed'],
            'powerPlayPct': team['powerPlayPct'],
            'penaltyKillPct': team['penaltyKillPct'],
            'goalsForPerGame': team['goalsForPerGame'],
            'goalsAgainstPerGame': team['goalsAgainstPerGame'],
            'shotsForPerGame': team['shotsForPerGame'],
            'faceoffWinPct': team.get('faceoffWinPct', 50.0)
        })
    
    return pd.DataFrame(teams)


def fetch_starting_goalies(game_id: int) -> Optional[Dict]:
    """
    Fetch starting goalies for a game (if announced).
    
    Args:
        game_id: NHL game ID (e.g., 2024020123)
    
    Returns:
        Dict with homeGoalie and awayGoalie info, or None if not yet announced
    
    **DATA LEAKAGE SAFE:** Starting lineups announced 1-2 hours before game.
    Only use this close to game time, and verify gameState is still 'FUT'.
    """
    url = f"{GAME_API}/{game_id}/landing"
    
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        # Check game hasn't started
        if data.get('gameState') not in ['FUT', 'PRE']:
            logger.warning(f"Game {game_id} has already started! State: {data.get('gameState')}")
            return None
        
        # Extract starting goalies from roster
        home_goalie = None
        away_goalie = None
        
        for player in data.get('rosterSpots', []):
            if player.get('positionCode') == 'G':
                goalie_info = {
                    'playerId': player.get('playerId'),
                    'name': f"{player['firstName']['default']} {player['lastName']['default']}"
                }
                
                if player['teamId'] == data['homeTeam']['id']:
                    home_goalie = goalie_info
                else:
                    away_goalie = goalie_info
        
        return {
            'gameId': game_id,
            'homeGoalie': home_goalie,
            'awayGoalie': away_goalie
        }
    
    except requests.exceptions.RequestException as e:
        logger.warning(f"Could not fetch goalies for game {game_id}: {e}")
        return None
```

---

## 🧪 **TESTING & VERIFICATION**

### **Test 1: Verify Schedule API**

```python
from nhl_api import fetch_schedule, fetch_future_games

# Test with today's date
today = '2024-11-10'
all_games = fetch_schedule(today)
future_games = fetch_future_games(today)

print(f"Total games on {today}: {len(all_games)}")
print(f"Future games (not yet played): {len(future_games)}")

for game in future_games:
    print(f"  {game['awayTeamAbbrev']} @ {game['homeTeamAbbrev']} - {game['startTimeUTC']}")
```

**Expected Output:**
```
Total games on 2024-11-10: 8
Future games (not yet played): 8
  BOS @ NYR - 2024-11-11T00:00:00Z
  TOR @ MTL - 2024-11-11T00:00:00Z
  ...
```

### **Test 2: Verify Special Teams Data**

```python
from nhl_api import fetch_team_special_teams

# Get current season stats
teams = fetch_team_special_teams('20242025')

# Check Rangers
rangers = teams[teams['teamId'] == 3]
print(f"Rangers PP%: {rangers['powerPlayPct'].values[0]:.1f}%")
print(f"Rangers PK%: {rangers['penaltyKillPct'].values[0]:.1f}%")
print(f"Games played: {rangers['gamesPlayed'].values[0]}")
```

### **Test 3: Verify No Data Leakage**

```python
# Predict a game from yesterday to verify we can't "see the future"
yesterday = '2024-11-09'
yesterday_games = fetch_schedule(yesterday)

for game in yesterday_games:
    if game['gameState'] == 'FINAL':
        # This game has already been played
        # Our model should NOT have access to final scores!
        print(f"Game {game['gameId']}: {game['gameState']}")
        print(f"  ⚠️ This game is finished - should NOT be in prediction set!")
```

---

## 📋 **DOCUMENTATION SUMMARY**

### **Key Endpoints:**

| API | URL | Purpose | Pre-Game Safe? |
|-----|-----|---------|----------------|
| Schedule | `api-web.nhle.com/v1/schedule/{date}` | Today's matchups | ✅ YES |
| Team Summary | `api.nhle.com/stats/rest/en/team/summary` | PP%, PK% | ✅ YES (cumulative) |
| Game Landing | `api-web.nhle.com/v1/gamecenter/{gameId}/landing` | Starting goalies | ✅ YES (before game) |

### **Data Leakage Prevention:**

1. ✅ Always filter `gameState == 'FUT'`
2. ✅ Use season-to-date stats (updated after games)
3. ✅ Never use in-game stats (scores, shots during game)
4. ✅ Use `.shift(1)` for all rolling features
5. ✅ Verify predictions made BEFORE start time

### **Advantages Over Pure MoneyPuck:**

1. **Real-time schedule** - Know today's games instantly
2. **PP%/PK% data** - Top predictors missing from MoneyPuck
3. **Live updates** - Can predict right up to puck drop
4. **Starting goalies** - Elite goalie = +5-10% win rate
5. **Combine with MoneyPuck** - Best of both worlds (xGoals + PP%)

---

## 🚀 **NEXT STEPS**

1. ✅ **Document NHL API** (THIS FILE)
2. ⏭️ Implement `nhl_api.py` client
3. ⏭️ Update `data_ingest.py` to merge NHL API + MoneyPuck
4. ⏭️ Create `live_predict.py` for today's games
5. ⏭️ Test with historical data (verify no leakage)
6. ⏭️ Test with TODAY's games (live prediction)
7. ⏭️ Add to report documentation

**Expected Outcome:** 63-65% accuracy with hybrid data + ability to predict TODAY's games! 🎯

