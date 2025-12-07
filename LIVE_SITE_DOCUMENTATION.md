# 🏒 Puckcast.ai - Live Site Documentation

> **Last Updated**: December 7, 2025
> **Model Version**: V8.2 (60.9% accuracy - 4-season holdout)
> **Deployment**: https://puckcast.ai
> **Status**: ✅ Production Ready

---

## 📋 Table of Contents

1. [Site Overview](#site-overview)
2. [Navigation & Global Layout](#navigation--global-layout)
3. [Page 1: Overview (Homepage)](#page-1-overview-homepage)
4. [Page 2: Predictions](#page-2-predictions)
5. [Page 2b: Matchup Detail (H2H)](#page-2b-matchup-detail-h2h)
6. [Page 3: Power Rankings](#page-3-power-rankings)
7. [Page 4: Performance](#page-4-performance)
8. [Page 5: Teams](#page-5-teams)
9. [Data Sources](#data-sources)
10. [Calculations & Formulas](#calculations--formulas)

---

## Site Overview

### Live Pages in Navigation (5 Total + Matchup Detail)
1. **Overview** (`/`) - Homepage with today's slate and power index preview
2. **Predictions** (`/predictions`) - Full game board with sortable predictions
3. **Power Rankings** (`/leaderboards`) - 32-team power index table
4. **Performance** (`/performance`) - Model validation and accuracy metrics
5. **Teams** (`/teams`) - Team index + individual team pages (`/teams/[abbrev]`)
6. **Matchup Detail** (`/matchup/[gameId]`) - H2H comparison (linked from predictions)

### Technology Stack
- **Framework**: Next.js 16 + React 19
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS v4 + Custom CSS
- **Fonts**: Epilogue (headings), Plus Jakarta Sans (body)
- **Hosting**: Vercel
- **Analytics**: Google Analytics 4 (G-ZSYWJKWQM3)
- **Data**: Static JSON files + Server-side NHL API fetches

---

## Navigation & Global Layout

### Navigation Bar (SiteNav)
**File**: `web/src/components/SiteNav.tsx`

**Navigation Links** (left to right):
1. Overview → `/`
2. Predictions → `/predictions`
3. Power Rankings → `/leaderboards`
4. Performance → `/performance`
5. Teams → `/teams`

**Actions**:
- "Follow on X" button → https://x.com/puckcastai
- Mobile hamburger menu (responsive drawer)

### Global Layout
**File**: `web/src/app/layout.tsx`

**Components**:
- Fixed navigation bar (64px height)
- Main content area with padding
- Footer with V8.2 version indicator
- Background gradient effects (cyan/emerald radials)

**Meta Tags**:
- Title: "Puckcast | NHL Predictions + Analytics"
- Description: "Data-driven NHL predictions powered by the official NHL API with 60%+ accuracy..."
- OpenGraph image: `/puckcastsocial.png` (1200x630)

---

## Page 1: Overview (Homepage)

**Route**: `/`
**File**: `web/src/app/page.tsx`

### Section 1: Hero (Two-Column)

#### Left Column

**Live Badge**:
- Display: "Live [timestamp] ET"
- Source: `todaysPredictions.json` → `generatedAt`
- Format: America/New_York timezone
- Example: "Live Dec 4, 5:30 PM ET"

**Heading**: "Predict the game before it's played."

**CTA Buttons**:
1. "View today's predictions" → `/predictions`
2. "Follow us for daily updates" → https://x.com/puckcastai

**Stat Tiles** (3):

1. **Model accuracy**
   - Value: "61.4%"
   - Source: `modelInsights.json` → `overall.accuracy`
   - Calculation: `(accuracy * 100).toFixed(1)`
   - Detail: "+7.6 pts vs baseline"
   - Detail calc: `((accuracy - baseline) * 100).toFixed(1)`

2. **Slate ready**
   - Value: "10 games" or "Off-day"
   - Source: `todaysPredictions.json` → `games.length`
   - Detail: Update timestamp

3. **Average edge**
   - Value: "18.5 pts"
   - Source: `modelInsights.json` → `overall.avgEdge`
   - Calculation: `(avgEdge * 100).toFixed(1)`
   - Detail: "Probability gap per matchup"

#### Right Column - Tonight's Signal Panel

**Panel Title**: "Sharpest edges before puck drop"

**Top 3 Edge Cards**:
- Source: `todaysPredictions.json` → `games`
- Sorting: By `Math.abs(edge)` descending, limit 3
- Each card shows:
  - Away crest @ Home crest
  - Start time (e.g., "7:00 PM ET")
  - Model favorite team name
  - Win probability (e.g., "56.0%")
  - Letter grade badge (A+, A, B+, B, C+, C)
  - Edge meter (visual bar)

**Grade Calculation**:
```typescript
pts = Math.abs(edge) * 100
if pts >= 25: return "A+"
if pts >= 20: return "A"
if pts >= 15: return "B+"
if pts >= 10: return "B"
if pts >= 5:  return "C+"
return "C"
```

**Upset Radar** (conditional):
- Filter: `modelFavorite === "away"` AND `awayWinProb >= 0.55`
- Sort: By `awayWinProb` descending
- Limit: Top 3
- Display: Road team @ Home team with probability

---

### Section 2: How Puckcast Keeps You Ahead

**Bento Grid** (3 feature cards):

1. **Edge-first cards**
   - Description: Every matchup shows lean, probability, edge bar, grade
   - Pills: "Edge + grade", "Goalie & rest baked in"

2. **Ticker for line moves** (highlighted)
   - Description: Auto-refreshing feed surfaces probability shifts
   - Pills: "Lineup-aware", "Goalie confirmation"

3. **Who's real vs the standings**
   - Description: Weekly blend to spot risers and sliders
   - Pills: "Movement calls", "Next opponent"

---

### Section 3: Puckcast Power Index

**Layout**: Two-column (left text, right list)

#### Left Column

**Title**: "Puckcast Power Index"

**Facts** (2 stat boxes):

1. **Biggest riser**
   - Value: Team name
   - Detail: "+3 spots"
   - Source: Calculated from standings vs power rank
   - Calculation: `standingsRank - powerRank` (positive only)

2. **Biggest slider**
   - Value: Team name
   - Detail: "-5 spots"
   - Calculation: `standingsRank - powerRank` (negative only)

**CTA**: "View full power board" → `/leaderboards`

#### Right Column - Top 5 Power List

**Source**: Calculated from `currentStandings.json` + `todaysPredictions.json`

**Each Team Shows**:
- Power rank (e.g., "#1")
- Team name
- Team crest
- Movement: "+3" (green), "-2" (red), "Even" (neutral)
- Record (e.g., "25-10-3")
- Points

**Power Score Formula**:
```typescript
powerScore = Math.round(
  points * 1.15 +
  pointPctg * 120 +
  goalDifferential * 1.6 +
  goalsForPerGame * 14 +
  goalsAgainstPerGame * -12 +
  (shotsForPerGame - shotsAgainstPerGame) * 1.2
)
```

---

## Page 2: Predictions

**Route**: `/predictions`
**File**: `web/src/app/predictions/page.tsx`

### Section 1: Hero (Two-Column)

#### Left Column

**Pills**:
- Game count: "10 games live" or "Off day"
- Update: "Updated Dec 4, 5:30 PM ET"

**Heading**: "Tonight's predictions, rebuilt."

#### Right Column - Stat Tiles (4)

1. **Holdout accuracy**
   - Value: "61.4%"
   - Source: `modelInsights.json` → `overall.accuracy`
   - Detail: "Baseline 53.7%"

2. **Average edge**
   - Value: Calculated from today's slate
   - Source: `todaysPredictions.json` → `games`
   - Calculation:
     ```typescript
     edges = games.map(g => Math.abs(g.edge))
     avgEdge = sum(edges) / edges.length
     display = (avgEdge * 100).toFixed(1) + " pts"
     ```

3. **A grades**
   - Value: Count of A+/A predictions
   - Filter: `games.filter(g => getPredictionGrade(g.edge).label.includes("A")).length`
   - Detail: B grade count

4. **Toss ups**
   - Value: Count with <2 pts edge
   - Filter: `games.filter(g => Math.abs(g.edge) < 0.02).length`

**CTAs**:
- "View model receipts" → `/performance`
- "Power index" → `/leaderboards`

---

### Section 2: Tonight's Board

**Sort Tabs**:
1. **Edge first**: Sort by `Math.abs(edge)` descending
2. **By start time**: Sort by `startTimeUtc` ascending

**Prediction Rows** (each game):

**Top Section**:
- Away crest @ Home crest
- Start time + indicator chip ("Home tilt" or "Road lean")

**Body Section**:
- Model favorite name
- Win probability (e.g., "56.0%")
- Letter grade badge
- Edge in points (e.g., "6.0 pts edge")

**Edge Meter**: Visual bar showing magnitude

**Footer**:
- Confidence score (raw decimal)
- Full matchup text

---

### Section 3: Right Rail

#### Confidence Ladder Card

**Title**: "Holdout accuracy by band"

**Source**: `modelInsights.json` → `confidenceBuckets`

**Display**: 6 buckets reversed (A+ at top)

**Each Bucket**:
- Edge range (e.g., "25+ pts")
- Letter grade badge
- Game count
- Accuracy bar
- Accuracy percentage

**Buckets**:
1. A+: 25+ pts, 70.2%, 299 games
2. A: 20-25 pts, 62.2%, 164 games
3. B+: 15-20 pts, 60.0%, 211 games
4. B: 10-15 pts, 55.9%, 205 games
5. C+: 5-10 pts, 56.1%, 212 games
6. C: 0-5 pts, 52.4%, 139 games

#### Live Ticker Card

**Title**: "Live ticker"
- Description: Updates refresh explanation
- Last refresh timestamp
- CTA: "Return to overview" → `/`

#### Upset Radar Card (conditional)

**Display**: Only if upset games exist
- Same filter as homepage
- Top 3 away favorites

---

## Page 2b: Matchup Detail (H2H)

**Route**: `/matchup/[gameId]`
**File**: `web/src/app/matchup/[gameId]/page.tsx`

### Access
Click any prediction card on `/predictions` to view detailed matchup.

### Section 1: Header
- Away team vs Home team with circular crests
- Win probability bar with team colors
- Team records and standings ranks

### Section 2: Model Pick Banner
- Model favorite team logo and name
- Grade (A+ through C)
- Edge points
- Win probability percentage
- Summary text

### Section 3: Team Comparison Stats
8 comparison bars with team-colored fills:
1. **Points** - League standings points
2. **Point %** - Points percentage
3. **Goal Diff** - Goal differential
4. **Goals/Game** - Offensive output
5. **Goals Against** - Defensive rating
6. **Power Score** - Puckcast composite rating
7. **Power Play %** - PP efficiency
8. **Penalty Kill %** - PK efficiency

Each stat shows leader highlighting and proportional bar widths.

### Section 4: Projected Goalies
- Goalie name, record, rest days (if available)
- Team-colored card borders

### Section 5: Team Links
- Links to individual team pages for both teams

---

## Page 3: Power Rankings

**Route**: `/leaderboards`
**File**: `web/src/app/leaderboards/page.tsx`

### Section 1: Hero (Two-Column)

#### Left Column

**Pills**:
- "Puckcast Power Index"
- Update timestamp

**Heading**: "The analytics snapshot of who's real."

#### Right Panel - Stat Tiles (4)

1. **Current #1**
   - Value: Top team name
   - Detail: Rank and record

2. **Biggest riser**
   - Value: Team name
   - Detail: "+X spots"

3. **Biggest slider**
   - Value: Team name
   - Detail: "-X spots"

4. **Refresh cadence**
   - Value: "Weekly"
   - Detail: Last update time

---

### Section 2: Power Board Table

**Component**: `PowerBoardClient` (interactive)

**Data Sources**:
- `currentStandings.json` (32 teams)
- `todaysPredictions.json` (model accuracy)
- NHL API (next games)

**Table Columns** (8):

1. **Power Rank** (#1-32)
   - Sorted by power score

2. **Movement**
   - Format: "+3", "-2", "Even"
   - Calculation: `standingsRank - powerRank`
   - Colors: Green (up), Red (down), Neutral (even)

3. **Team**
   - Logo, name, abbreviation

4. **Record**
   - Format: "W-L-OT"
   - Source: `currentStandings.json`

5. **Points**
   - Current standings points

6. **Goal Differential**
   - Format: "+32" or "-15"
   - Color: Green/red

7. **Model Win Rate**
   - Display: "56.5%"
   - Average win probability

8. **Next Opponent**
   - Opponent, date, time
   - Source: NHL API schedule
   - Lookahead: 14 days

---

## Page 4: Performance

**Route**: `/performance`
**File**: `web/src/app/performance/page.tsx`

### Section 1: Hero (Two-Column)

#### Left Column

**Pills**: "Model accuracy", "Holdout proof"

**Heading**: "Does the model work?"

**Answer**: "Yes. Calibrated on official NHL data across 1,230 holdout games..."

**Stat Tiles** (4):

1. **Test accuracy**
   - Value: "61.4%"
   - Detail: "+7.6 pts vs baseline"

2. **Baseline**
   - Value: "53.7%"
   - Detail: "Home/away prior"

3. **Avg edge**
   - Value: "18.5 pts"
   - Detail: "Probability gap per game"

4. **Holdout size**
   - Value: "1,230"
   - Detail: "755 correct · 475 incorrect"
   - Calculation:
     - Correct: `Math.round(accuracy * games)`
     - Incorrect: `Math.round((1 - accuracy) * games)`

#### Right Panel - Metrics (4)

1. **Log loss**: "0.664" (lower is better)
2. **A-grade hit rate**: "67.1%"
3. **Best strategy**: "Elite picks (25+ pts)"
4. **Historical bankroll**: "+255u"

---

### Section 2: Confidence Calibration

**Title**: "Accuracy by edge band"

**Grid**: 6 cards (reverse order)

**Each Card**:
- Edge range label
- Letter grade badge
- Accuracy percentage (large)
- Game count
- Accuracy meter

---

### Section 3: Strategy Receipts

**Table**: 4 strategies

**Columns**:
1. **Strategy**: Name + note
2. **Win Rate**: Percentage
3. **ROI/Bet**: `((units / bets) * 100).toFixed(1)%`
4. **Total Units**: "+255u" or "-50u" (colored)
5. **Bets**: Count

**Strategies**:
1. All predictions: 1,230 bets, 61.4%, +255u
2. A-tier picks (20+ pts): 463 bets, 67.1%, +164u
3. Elite picks (25+ pts): 299 bets, 70.2%, +121u
4. A+ and A only: 463 bets, 67.1%, +164u

**Disclaimer**: Amber-bordered box explaining transparency

---

## Page 5: Teams

**Route**: `/teams`
**File**: `web/src/app/teams/page.tsx`

### Teams Index Page

**Pills**: "Team Index", "All 32 teams"

**Heading**: "Find your team."

**Grid**: 3 columns (desktop), responsive

**Each Team Card**:
- Team logo
- Team name
- Record (e.g., "25-10-3")
- Points chip
- Model win % chip
- Link: `/teams/[abbrev]` (lowercase)

**Sorting**: Alphabetical by name

**Data Sources**:
- `currentStandings.json`
- `todaysPredictions.json`

---

### Individual Team Pages

**Route**: `/teams/[abbrev]`
**File**: `web/src/app/teams/[abbrev]/page.tsx`
**Examples**: `/teams/wpg`, `/teams/bos`

#### Section 1: Hero (Two-Column)

**Left Column**:

**Pills**: "Team profile", Team name

**Heading**: "#[rank] · [Team Name]"

**Stat Tiles** (4):

1. **Power score**
   - Value: Number (e.g., "217")
   - Detail: "#1 in the model"

2. **Record**
   - Value: "25-10-3"
   - Detail: "Points 53"

3. **Model win %**
   - Value: "56.5%"
   - Detail: "Avg edge 12.3 pts"

4. **Movement**
   - Value: "+3", "-2", "Even"
   - Detail: "vs standings #4"

**Right Column**:

- Team logo
- Power score

**Strengths/Weaknesses** (auto-generated):
- Based on avgProb, avgEdge, favoriteRate
- Strengths if avgProb > 0.55, avgEdge > 0.12, etc.
- Weaknesses if avgProb < 0.5, avgEdge < 0.08, etc.

**Next Game**:
- "vs [opponent] on [date]"

---

#### Section 2: Model Analysis

**Card**: "How the model sees this team"
- Description paragraph explaining power rank

---

#### Section 3: Upcoming Games

**Title**: "Upcoming games"

**Source**: `todaysPredictions.json` filtered by team

**Each Game Card**:

**Left**:
- Opponent logo
- "vs" or "@" opponent
- Date, time
- Venue

**Right**:
- Win probability chip
- Edge chip (colored):
  - Green: Positive
  - Red: Negative
- Confidence grade

**Empty State**: "No upcoming games scheduled"

---

#### Section 4: Team Statistics

**Grid 1** (4 cards):
1. Goals per game (offense)
2. Goals against per game (defense)
3. Goal differential (colored)
4. Point percentage

**Grid 2** (2 cards):
1. **Shooting**: Shots for/against, differential
2. **Record breakdown**: Wins (green), Losses (red), OT (amber)

---

#### Section 5: Special Teams

**Grid** (2 cards):
1. **Power Play %** - PP efficiency with league rank (#1-32)
2. **Penalty Kill %** - PK efficiency with league rank (#1-32)

---

#### Section 6: Team Goalies (conditional)

**Display**: Only if team has goalies in `goaliePulse.json`

**Source**: `goaliePulse.json` → `goalies` filtered by team

**Each Goalie Card**:

**Header**:
- Name
- Trend badge: "surging" (emerald), "steady" (blue), "fresh" (cyan), "fatigue watch" (amber)

**Metrics** (4):
- Season GSAx
- Rolling GSAx
- Rest days
- Start likelihood

**Analysis**:
- Strengths (emerald text)
- Watch-outs (amber text)

---

## Data Sources

### Static JSON Files

**Location**: `web/src/data/`

#### 1. todaysPredictions.json
- **Size**: ~6.6 KB
- **Update**: Daily 11:00 AM UTC (6:00 AM ET)
- **Generator**: `prediction/predict_full.py`
- **Used on**: Overview, Predictions, Power Rankings, Teams

**Structure**:
```json
{
  "generatedAt": "2025-12-04T17:30:16Z",
  "games": [{
    "id": "2025020426",
    "homeTeam": {"name": "Bruins", "abbrev": "BOS"},
    "awayTeam": {"name": "Blues", "abbrev": "STL"},
    "homeWinProb": 0.4405,
    "awayWinProb": 0.5595,
    "edge": -0.06,
    "confidenceGrade": "B-",
    "modelFavorite": "away"
  }]
}
```

---

#### 2. modelInsights.json
- **Size**: ~22 KB
- **Update**: Weekly (after retraining)
- **Generator**: `training/train_v7_3_situational.py`
- **Used on**: Overview, Predictions, Performance, Power Rankings

**Key Fields**:
- `overall`: accuracy, baseline, brier, logLoss, avgEdge, games
- `confidenceBuckets`: 6 buckets with label, grade, accuracy, count
- `strategies`: 4 strategies with bets, winRate, units
- `bankrollSeries`: Time series data

---

#### 3. currentStandings.json
- **Size**: ~13 KB
- **Update**: Daily
- **Used on**: Overview, Power Rankings, Teams

**Structure**:
```json
{
  "teams": [{
    "team": "Winnipeg Jets",
    "abbrev": "WPG",
    "wins": 25,
    "losses": 10,
    "ot": 3,
    "points": 53,
    "pointPctg": 0.697,
    "goalDifferential": 32,
    "goalsForPerGame": 3.5,
    "goalsAgainstPerGame": 2.6,
    "powerPlayPct": 0.245,
    "penaltyKillPct": 0.823
  }]
}
```

---

#### 4. goaliePulse.json
- **Size**: ~15 KB
- **Update**: Daily or as needed
- **Used on**: Teams (individual pages)

**Structure**:
```json
{
  "goalies": [{
    "name": "Connor Hellebuyck",
    "team": "WPG",
    "trend": "surging",
    "startLikelihood": 0.85,
    "restDays": 2,
    "rollingGsa": 2.3,
    "seasonGsa": 15.7,
    "strengths": ["Elite positioning"],
    "watchouts": ["Struggles vs speed"]
  }]
}
```

---

### Live API Calls

#### NHL Schedule API
- **Endpoint**: `https://statsapi.web.nhl.com/api/v1/schedule`
- **Used on**: Power Rankings (next games)
- **Cache**: No store
- **Lookahead**: 14 days

---

## Calculations & Formulas

### Power Score
**Location**: `web/src/lib/current.ts`

```typescript
powerScore = Math.round(
  points * 1.15 +
  pointPctg * 120 +
  goalDifferential * 1.6 +
  goalsForPerGame * 14 +
  goalsAgainstPerGame * -12 +
  (shotsForPerGame - shotsAgainstPerGame) * 1.2
)
```

**Example** (Winnipeg Jets):
```
53*1.15 + 0.697*120 + 32*1.6 + 3.5*14 + 2.6*-12 + (31.2-28.1)*1.2
= 60.95 + 83.64 + 51.2 + 49 - 31.2 + 3.72
= 217
```

---

### Edge Calculation

```typescript
edge = homeWinProb - 0.5
edgePts = Math.abs(edge) * 100
```

**Examples**:
- homeWinProb = 0.56 → edge = +0.06 → 6.0 pts
- homeWinProb = 0.44 → edge = -0.06 → 6.0 pts

---

### Confidence Grades

```typescript
pts = Math.abs(edge) * 100
if pts >= 25: return "A+"
if pts >= 20: return "A"
if pts >= 15: return "B+"
if pts >= 10: return "B"
if pts >= 5:  return "C+"
return "C"
```

---

### Movement

```typescript
movement = standingsRank - powerRank
```

- Positive = Riser (higher in power than standings)
- Negative = Slider (lower in power than standings)
- Zero = No difference

---

### Accuracy Metrics

**Overall**:
```typescript
accuracy = correctPredictions / totalGames
// V7.3: 755 / 1230 = 60.49%
```

**Edge Over Baseline**:
```typescript
edge = (accuracy - baseline) * 100
// V7.3: (0.6138 - 0.5374) * 100 = 7.64 pts
```

**Bucket Accuracy**:
```typescript
bucketAccuracy = correctInBucket / gamesInBucket
// A+: 210 / 299 = 70.2%
```

---

## Update Schedule

### Daily (Automated)
**Time**: 11:00 AM UTC (6:00 AM ET)
**Process**:
1. `prediction/predict_full.py` via GitHub Actions
2. Fetch NHL API data (3 seasons)
3. Build 220 features
4. Generate predictions
5. Output to JSON
6. Auto-deploy to Vercel

**Files**:
- `todaysPredictions.json`
- `currentStandings.json`

### Weekly (Manual)
**Files**:
- `modelInsights.json` (if retrained)
- `goaliePulse.json` (analysis updates)

---

## Browser Support

**Tested**:
- Chrome 120+ ✅
- Firefox 121+ ✅
- Safari 17+ ✅
- Edge 120+ ✅
- Mobile (iOS/Android) ✅

**Breakpoints**:
- Mobile: <640px
- Tablet: 640-1024px
- Desktop: 1024px+

---

**End of Documentation**
