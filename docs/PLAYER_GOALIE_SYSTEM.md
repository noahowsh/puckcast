# Puckcast Player & Goalie Data System

## Overview

This document describes the player statistics, lineup projection, and starting goalie detection systems implemented in Puckcast. The system aggregates data from multiple sources (NHL API, Daily Faceoff, ESPN) to provide comprehensive team and player information to website visitors.

---

## Architecture

```
EXTERNAL DATA SOURCES
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│  NHL Stats API          Daily Faceoff         ESPN          │
│  • Player/Goalie stats  • Goalie confirmations • Injuries   │
│  • Game schedules       • Status levels                     │
│  • Starting lineups     • Performance data                  │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                    PYTHON SCRAPERS                           │
│  starting_goalie_scraper.py  →  startingGoalies.json        │
│  generate_goalie_pulse.py    →  goaliePulse.json            │
│  injuryService.ts (ESPN)     →  injuries.json               │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                  TYPESCRIPT SERVICES                         │
│  playerHub.ts              startingGoalieService.ts         │
│  lineupService.ts          injuryService.ts                 │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                   REACT COMPONENTS                           │
│  StartingGoalieDisplay.tsx    LineupDisplay.tsx             │
│  PlayerStatsTable.tsx         PlayerCard.tsx                │
└─────────────────────────────────────────────────────────────┘
        │
        ▼
┌─────────────────────────────────────────────────────────────┐
│                      TEAM PAGES                              │
│              /teams/[abbrev]/page.tsx                        │
│  Shows: Goalie situation, Projected lineup, Player stats    │
└─────────────────────────────────────────────────────────────┘
```

---

## Data Files

| File | Location | Purpose | Updated By |
|------|----------|---------|-----------|
| `startingGoalies.json` | `web/src/data/` | Game-by-game starting goalie confirmations with status | `starting_goalie_scraper.py` |
| `goaliePulse.json` | `web/src/data/` | Goalie performance metrics, trends, start likelihood | `generate_goalie_pulse.py` |
| `injuries.json` | `web/src/data/` | Team injury reports | `injuryService.ts` |

---

## Starting Goalie Detection System

### Data Source Priority

1. **Daily Faceoff (Primary)** - Industry standard for goalie confirmations
   - Status levels: confirmed, expected, probable, unconfirmed
   - Confidence mapping:
     - `confirmed`: 99%
     - `expected`: 85%
     - `likely`: 75%
     - `probable`: 65%
     - `unconfirmed`: 40%
     - `unknown`: 30%

2. **NHL API (Secondary)** - Official confirmation 1-2 hours before game
   - Only used if game state is `FUT` or `PRE` (prevents data leakage)
   - Confidence: 100% when confirmed

3. **goaliePulse.json (Fallback)** - Statistical predictions
   - Uses `startLikelihood` from performance analysis
   - Status: `predicted` (60% confidence)

### Python Scraper

**File:** `src/nhl_prediction/starting_goalie_scraper.py`

**Key Features:**
- Multi-method HTML parsing for Daily Faceoff:
  1. Next.js `__NEXT_DATA__` JSON extraction
  2. Embedded JSON in script tags
  3. HTML structure parsing (fallback)
- Team name to abbreviation mapping (32 NHL teams)
- Rate limiting to avoid API hammering
- SQLite database for historical tracking

**Usage:**
```bash
python src/nhl_prediction/starting_goalie_scraper.py
```

**Output Format (startingGoalies.json):**
```json
{
  "generatedAt": "2025-12-08T15:00:00Z",
  "date": "2025-12-08",
  "games": [
    {
      "gameId": "2025020500",
      "homeTeam": "TOR",
      "awayTeam": "BOS",
      "homeGoalie": "Joseph Woll",
      "awayGoalie": "Jeremy Swayman",
      "homeStatus": "confirmed",
      "awayStatus": "expected",
      "source": "daily_faceoff",
      "confidence": 0.92
    }
  ]
}
```

### TypeScript Service

**File:** `web/src/lib/startingGoalieService.ts`

**Key Functions:**
- `getTeamGoalies(teamAbbrev)` - Returns starter and backup for a team
- `getGameGoalieReport(gameId)` - Full goalie matchup for a game
- `getDailyGoalieReport(date?)` - All games for a date
- `getTeamExpectedStarter(teamAbbrev)` - Most likely starter
- `isGoalieDataStale()` - Checks if data is >4 hours old
- `clearGoalieCache()` - Forces data refresh

**Status Handling:**
The service gracefully handles missing status fields for backwards compatibility:
```typescript
gameData.homeStatus || "unknown"  // Falls back to "unknown" if missing
```

---

## Lineup Projection System

### Player Ranking Algorithm

**File:** `web/src/lib/lineupService.ts`

Players are ranked by weighted score:
- **Time on Ice:** 40% (most important - coaches play best players more)
- **Total Points:** 25%
- **Points per Game:** 20%
- **Plus/Minus:** 10%
- **Games Played:** 5%

### Lineup Structure

```typescript
interface TeamLineup {
  forwards: LineupPlayer[];           // All forwards, ranked
  defensemen: LineupPlayer[];         // All defensemen, ranked
  goalies: GoalieLineup[];            // All goalies, ranked
  projectedForwards: LineupPlayer[];  // Top 12 healthy forwards
  projectedDefensemen: LineupPlayer[];// Top 6 healthy defensemen
  projectedGoalies: GoalieLineup[];   // Starter + backup
  healthyScratches: LineupPlayer[];   // Healthy but not starting
  lineupStrength: LineupStrengthMetrics;
}
```

### Strength Metrics

```typescript
interface LineupStrengthMetrics {
  overallQuality: number;      // 0-100 combined score
  offensiveStrength: number;   // Forward scoring power
  defensiveStrength: number;   // Defenseman performance
  goalieStrength: number;      // Weighted: 70% starter, 30% backup
  injuryImpact: number;        // Negative adjustment for missing players
  percentOfFullStrength: number; // Current vs fully healthy
}
```

---

## React Components

### StartingGoalieDisplay.tsx

| Component | Purpose |
|-----------|---------|
| `StatusBadge` | Shows confirmation status with color coding |
| `ConfidenceMeter` | Visual progress bar for confidence % |
| `GoalieStarterCard` | Compact goalie display with name/status |
| `TeamGoalieSituationCard` | Full starter + backup analysis |
| `GoalieMatchupCard` | Head-to-head game comparison |

### LineupDisplay.tsx

| Component | Purpose |
|-----------|---------|
| `LineupStrengthCard` | Ring chart with overall quality score |
| `ProjectedLineupDisplay` | Shows starters, scratches, injured |
| `LineupSummaryBadge` | Compact strength indicator |

---

## Team Page Integration

**File:** `web/src/app/teams/[abbrev]/page.tsx`

The team page fetches data in parallel:
```typescript
const [roster, projectedLineup, goalieInfo] = await Promise.all([
  fetchTeamRoster(teamData.abbrev),
  buildProjectedLineup(teamData.abbrev),
  getTeamGoalies(teamData.abbrev),
]);
```

**Sections Displayed:**
1. Team header with logo and power ranking
2. Standings position and division info
3. Goaltending Situation card (starter + backup with status)
4. Projected Lineup with strength metrics
5. Player stats tables (skaters and goalies)

---

## Update Schedule

| Time (ET) | Action | Script |
|-----------|--------|--------|
| 8-9 AM | First goalie check | `starting_goalie_scraper.py` |
| 11 AM-12 PM | Post morning skates (most confirmations) | `starting_goalie_scraper.py` |
| 3-4 PM | Afternoon update | `starting_goalie_scraper.py` |
| Before games | Final confirmation | `starting_goalie_scraper.py` |

---

## Future Model Integration

The data collected can enhance ML predictions with features like:

```python
# Goalie quality features
features['home_goalie_gsa'] = home_goalie.gsaRolling
features['home_goalie_sv_pct'] = home_goalie.savePct
features['goalie_advantage'] = home_gsa - away_gsa

# Confirmation features
features['both_goalies_confirmed'] = 1 if both confirmed else 0
features['confirmation_confidence'] = (home_conf + away_conf) / 2

# Lineup strength features
features['home_lineup_quality'] = lineup.lineupStrength.overallQuality / 100
features['home_injury_impact'] = lineup.lineupStrength.injuryImpact
features['home_pct_full_strength'] = lineup.lineupStrength.percentOfFullStrength / 100
```

---

## File Reference

### Python
- `src/nhl_prediction/starting_goalie_scraper.py` - Multi-source goalie scraper
- `scripts/generate_goalie_pulse.py` - Performance metrics generator
- `scripts/fetch_starting_goalies.py` - Legacy NHL API scraper

### TypeScript Services
- `web/src/lib/startingGoalieService.ts` - Goalie data aggregation
- `web/src/lib/lineupService.ts` - Lineup projection
- `web/src/lib/injuryService.ts` - Injury tracking
- `web/src/lib/playerHub.ts` - NHL API integration
- `web/src/lib/data.ts` - Data file imports

### Types
- `web/src/types/startingGoalie.ts` - Goalie types and helpers
- `web/src/types/lineup.ts` - Lineup types
- `web/src/types/player.ts` - Player types

### Components
- `web/src/components/StartingGoalieDisplay.tsx`
- `web/src/components/LineupDisplay.tsx`
- `web/src/components/PlayerStatsTable.tsx`

### Pages
- `web/src/app/teams/[abbrev]/page.tsx` - Team dashboard

---

## Version History

- **V7.7** (2025-12-08): Added Daily Faceoff as primary goalie confirmation source
  - New `homeStatus`/`awayStatus` fields in JSON output
  - Multi-method HTML parsing for Daily Faceoff
  - Status-based confidence mapping
  - Backwards compatible with old JSON format
