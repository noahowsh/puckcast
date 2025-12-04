# 🏒 Puckcast.ai - Complete Live Site Documentation

> **Last Updated**: December 4, 2024 19:00 UTC
> **Model Version**: V7.3 Situational Features
> **Deployment**: https://puckcast.ai
> **Status**: ✅ Production Ready

---

## 📋 Table of Contents

1. [Site Architecture](#site-architecture)
2. [Navigation & Layout](#navigation--layout)
3. [Page-by-Page Breakdown](#page-by-page-breakdown)
4. [Data Sources & Updates](#data-sources--updates)
5. [Calculations & Formulas](#calculations--formulas)
6. [Component Library](#component-library)
7. [SEO & Meta Tags](#seo--meta-tags)

---

## Site Architecture

### Technology Stack
- **Frontend Framework**: Next.js 16 + React 19
- **Language**: TypeScript 5.x
- **Styling**: Tailwind CSS v4 + Custom CSS
- **Fonts**: Epilogue (display), Plus Jakarta Sans (body)
- **Hosting**: Vercel
- **Analytics**: Google Analytics 4 (ID: G-ZSYWJKWQM3)
- **Rendering**: Server-side rendering (SSR) with static JSON data

### File Structure
```
web/
├── src/
│   ├── app/                    # Next.js pages (App Router)
│   │   ├── page.tsx            # Homepage (/)
│   │   ├── predictions/        # Predictions page
│   │   ├── performance/        # Performance page
│   │   ├── leaderboards/       # Power rankings page
│   │   ├── goalies/            # Goalie intelligence page
│   │   ├── about/              # About page
│   │   ├── teams/              # Teams pages
│   │   └── layout.tsx          # Root layout
│   ├── components/             # React components
│   ├── data/                   # Static JSON data files
│   ├── lib/                    # Helper functions & calculations
│   ├── types/                  # TypeScript type definitions
│   └── styles/                 # CSS files
```

---

## Navigation & Layout

### Global Navigation (SiteNav Component)
**Location**: `web/src/components/SiteNav.tsx`

**Navigation Links** (5 primary):
1. **Overview** → `/` (Homepage)
2. **Predictions** → `/predictions`
3. **Power Rankings** → `/leaderboards`
4. **Performance** → `/performance`
5. **Teams** → `/teams` (placeholder for future team pages)

**Additional Actions**:
- "Follow on X" button → https://x.com/puckcastai
- Mobile hamburger menu (responsive navigation drawer)

### Global Layout (Root Layout)
**Location**: `web/src/app/layout.tsx`

**Elements**:
- **Background Effects**: Gradient overlays (radial gradients with cyan/emerald accents)
- **Navigation Bar**: Fixed at top, 64px height
- **Main Content**: Padding-top to clear navigation
- **Footer**: Version indicator (v7.3), copyright, legal notice

**SEO Metadata**:
- **Title**: "Puckcast | NHL Predictions + Analytics"
- **Description**: "Data-driven NHL predictions powered by the official NHL API with 60%+ accuracy. Advanced analytics, goalie tracking, and real-time game predictions."
- **OpenGraph Image**: `/puckcastsocial.png` (1200x630)
- **Favicon**: `/puckcastai.png`

**Analytics**:
- Google Analytics 4 script loaded via Next.js `<Script>` component
- Custom `<Analytics />` component for additional tracking

---

## Page-by-Page Breakdown

### 1. Homepage (`/`)
**File**: `web/src/app/page.tsx`

#### Sections

##### Hero Section
**Description**: Two-column layout with model stats and top edges

**Left Column** (Text):
- **Live Badge**: Shows update timestamp (e.g., "Live Dec 4, 6:30 PM ET")
  - **Source**: `predictionsPayload.generatedAt`
  - **Format**: `Intl.DateTimeFormat` with `America/New_York` timezone
- **Heading**: "Predict the game before it's played."
- **Subheading**: Mission statement about AI-powered predictions
- **CTAs**:
  - "View today's predictions" → `/predictions`
  - "Follow us for daily updates" → https://x.com/puckcastai

**Stat Tiles** (3):
1. **Model accuracy**
   - **Value**: `61.4%`
   - **Source**: `modelInsights.overall.accuracy`
   - **Detail**: `+7.6 pts vs baseline`
   - **Calculation**: `(accuracy - baseline) * 100`

2. **Slate ready**
   - **Value**: `10 games` (or "Off-day" if empty)
   - **Source**: `todaysPredictions.length`
   - **Detail**: Last update timestamp

3. **Average edge**
   - **Value**: `18.5 pts`
   - **Source**: `modelInsights.overall.avgEdge`
   - **Calculation**: `avgEdge * 100`

**Right Column** (Panel):
- **Panel Title**: "Tonight's signal - Sharpest edges before puck drop"
- **Edge Cards** (Top 3 by edge):
  - Shows away/home team crests
  - Start time
  - Model favorite team name
  - Win probability percentage
  - Letter grade (A+, A, B+, B, C+, C)
  - Edge meter (visual bar)
  - **Sorting**: Games sorted by `Math.abs(edge)` descending, limited to top 3

- **Upset Radar** (if available):
  - Shows games where away team is favored at 55%+
  - Displays road team, home team, win probability
  - **Filter**: `game.modelFavorite === "away" && game.awayWinProb >= 0.55`
  - Limited to top 3 by `awayWinProb`

##### "How Puckcast keeps you ahead" Section
**Description**: Bento grid with 3 feature cards

**Cards**:
1. **Edge-first cards**
   - Copy: Every matchup shows lean, win probability, edge bar, grade
   - Pills: "Edge + grade", "Goalie & rest baked in"

2. **Ticker for line moves** (highlighted card)
   - Copy: Auto-refreshing feed surfaces probability shifts
   - Pills: "Lineup-aware", "Goalie confirmation"

3. **Who's real vs the standings**
   - Copy: Weekly blend to spot risers and sliders
   - Pills: "Movement calls", "Next opponent"

##### Power Index Section
**Description**: Top 5 power rankings preview

**Left Side**:
- **Title**: "Puckcast Power Index"
- **Description**: Weekly blend of point pace, goal differential, model win rate
- **Facts**:
  - **Biggest Riser**: Shows team with highest positive movement
    - **Source**: Calculated from `powerIndex` (difference between standings rank and power rank)
  - **Biggest Slider**: Shows team with lowest negative movement
- **CTA**: "View full power board" → `/leaderboards`

**Right Side** (Power List):
- **Top 5 Teams** displayed as cards
- **Each Item Shows**:
  - Power rank (e.g., "#1")
  - Team name
  - Team crest
  - Movement indicator (+3, -2, Even)
    - **Color**: Green for positive, red for negative, neutral for even
  - Record (e.g., "25-10-3")
  - Points

**Data Sources**:
- **Standings**: `web/src/data/currentStandings.json`
- **Live Snapshots**: Built from today's predictions
- **Power Score**: Computed via `computeStandingsPowerScore()`

---

### 2. Predictions Page (`/predictions`)
**File**: `web/src/app/predictions/page.tsx`

#### Sections

##### Hero Section
**Description**: Two-column layout with slate info and model stats

**Left Column**:
- **Pills**:
  - Game count (e.g., "10 games live" or "Off day")
  - Last update timestamp
- **Heading**: "Tonight's predictions, rebuilt."
- **Description**: "Clean, confident, and fast" product statement

**Right Column** (Stat Tiles):
1. **Holdout accuracy**
   - **Value**: `61.4%`
   - **Source**: `modelInsights.overall.accuracy`
   - **Detail**: Baseline percentage

2. **Average edge**
   - **Value**: Calculated from today's predictions
   - **Calculation**: `Math.abs(game.edge)` averaged across all games
   - **Detail**: "Per matchup"

3. **A grades**
   - **Value**: Count of A+/A grade predictions
   - **Filter**: Games where grade label includes "A"
   - **Detail**: B grade count

4. **Toss ups**
   - **Value**: Count of games with <2 pts edge
   - **Filter**: `Math.abs(edge) < 0.02`
   - **Detail**: "Less than 2 pts edge"

**CTAs**:
- "View model receipts" → `/performance`
- "Power index" → `/leaderboards`

##### Tonight's Board Section
**Description**: Sortable list of all predictions

**Sort Options** (Tab Buttons):
1. **Edge first**: Sort by `Math.abs(edge)` descending
2. **By start time**: Sort by `startTimeUtc` ascending

**Prediction Rows** (for each game):
- **Team Display**:
  - Away team crest @ Home team crest
  - Start time
  - Home/road indicator chip
- **Model Lean**:
  - Favorite team name
  - Win probability percentage
- **Grade Display**:
  - Letter grade badge
  - Edge in points (e.g., "6.0 pts edge")
- **Edge Meter**: Visual bar showing edge strength
- **Footer**:
  - Confidence score (raw decimal)
  - Full matchup text

**Data Source**: `todaysPredictions` from `web/src/data/todaysPredictions.json`

##### Right Rail

**Confidence Ladder**:
- **Title**: "Holdout accuracy by band"
- **Display**: 6 buckets in reverse order (A+ to C)
- **Each Bucket Shows**:
  - Edge range (e.g., "25+ pts")
  - Letter grade badge
  - Game count
  - Accuracy bar (visual meter)
  - Accuracy percentage
- **Source**: `modelInsights.confidenceBuckets`

**Update Cadence Card**:
- **Title**: "Live ticker"
- **Description**: Explanation of real-time updates
- **Timestamp**: Last refresh time
- **CTA**: "Return to overview" → `/`

**Upset Radar** (if available):
- Same as homepage upset radar
- Shows top 3 road favorites

---

### 3. Performance Page (`/performance`)
**File**: `web/src/app/performance/page.tsx`

#### Sections

##### Hero Section
**Description**: Model validation proof

**Left Column**:
- **Pills**: "Model accuracy", "Holdout proof"
- **Heading**: "Does the model work?"
- **Answer**: "Yes." with validation details

**Stat Tiles** (4):
1. **Test accuracy**
   - **Value**: `61.4%`
   - **Source**: `modelInsights.overall.accuracy`
   - **Detail**: `+7.6 pts vs baseline`
   - **Calculation**: `((accuracy - baseline) * 100).toFixed(1)`

2. **Baseline**
   - **Value**: `53.7%`
   - **Source**: `modelInsights.overall.baseline`
   - **Detail**: "Home/away prior"

3. **Avg edge**
   - **Value**: `18.5 pts`
   - **Source**: `modelInsights.overall.avgEdge * 100`
   - **Detail**: "Probability gap per game"

4. **Holdout size**
   - **Value**: `1,230`
   - **Source**: `modelInsights.overall.games`
   - **Detail**: Correct/incorrect breakdown
   - **Calculation**:
     - Correct: `Math.round(accuracy * games)`
     - Incorrect: `Math.round((1 - accuracy) * games)`

**Right Panel** (4 Additional Metrics):
1. **Log loss**
   - **Value**: `0.664`
   - **Source**: `modelInsights.overall.logLoss`
   - **Detail**: "Lower is better"

2. **A-grade hit rate**
   - **Value**: Last bucket accuracy from `confidenceBuckets`
   - **Source**: `confidenceBuckets[confidenceBuckets.length - 1].accuracy`

3. **Best strategy**
   - **Value**: Strategy name with highest units
   - **Source**: `modelInsights.strategies` sorted by `units`
   - **Detail**: Unit count and win rate

4. **Historical bankroll**
   - **Value**: Final units from bankroll series
   - **Source**: `bankrollSeries[bankrollSeries.length - 1].units`
   - **Detail**: "Flat stakes, even money assumption"

##### Confidence Calibration Section
**Description**: 6-bucket accuracy display

**Title**: "Accuracy by edge band"
**Subtitle**: "V7.3 model with 216 features, official NHL API data, 1,230 holdout games"

**Grid Layout** (6 Cards):
- Displayed in reverse order (A+ to C)
- **Each Card Shows**:
  - Edge range label (e.g., "25+ pts")
  - Letter grade badge (A+, A, B+, B, C+, C)
  - Accuracy percentage (e.g., "70.2%")
  - Game count (e.g., "299 games")
  - Accuracy meter (visual bar)

**Source**: `modelInsights.confidenceBuckets`

##### Strategy Receipts Section
**Description**: Historical backtest results table

**Disclaimer**: "Historical backtest on the same holdout set. Not betting advice."

**Table Columns**:
1. **Strategy**: Name and description note
2. **Win Rate**: Percentage (calculated from `winRate`)
3. **ROI/Bet**: `(units / bets) * 100` formatted as percentage
4. **Total Units**: With +/- prefix, colored green (profit) or red (loss)
5. **Bets**: Total number of bets in strategy

**Strategies Displayed** (from `modelInsights.strategies`):
1. All predictions (V7.3 model)
2. A-tier picks (20+ pts)
3. Elite picks (25+ pts)
4. A+ and A only

**Color Coding**:
- Green text: Positive units (profitable)
- Red text: Negative units (unprofitable)

**Warning Box**:
- Amber border/background
- "Important disclaimer" about transparency and not being betting advice

---

### 4. Leaderboards Page (`/leaderboards`)
**File**: `web/src/app/leaderboards/page.tsx`

#### Sections

##### Hero Section
**Description**: Power Index introduction

**Left Column**:
- **Pills**: "Puckcast Power Index", Update timestamp
- **Heading**: "The analytics snapshot of who's real."
- **Description**: Explanation of power score methodology

**Right Panel** (4 Stat Tiles):
1. **Current #1**
   - Top team by power score
   - Shows team name, power rank, record

2. **Biggest riser**
   - Team with highest positive movement
   - Shows movement (+X spots)

3. **Biggest slider**
   - Team with lowest negative movement
   - Shows movement (-X spots)

4. **Refresh cadence**
   - "Weekly"
   - Last update timestamp

##### Power Board Section
**Description**: Full 32-team sortable table

**Component**: `PowerBoardClient` (client-side interactive table)
**Location**: `web/src/components/PowerBoardClient.tsx`

**Table Columns**:
1. **Power Rank** (#1-32)
   - Calculated by sorting teams by `powerScore`
   - **Power Score Formula**:
     ```
     pointComponent = points * 1.15
     pctComponent = pointPctg * 120
     diffComponent = goalDifferential * 1.6
     offense = goalsForPerGame * 14
     defense = goalsAgainstPerGame * -12
     possession = (shotsForPerGame - shotsAgainstPerGame) * 1.2
     powerScore = round(sum of above)
     ```

2. **Movement** (vs standings rank)
   - Green: Positive movement (higher in power than standings)
   - Red: Negative movement (lower in power than standings)
   - Neutral: No movement

3. **Team** (with crest)
   - Team name
   - Team abbreviation
   - Team logo/crest

4. **Record** (W-L-OT)
   - Wins, losses, overtime losses
   - Source: `currentStandings.json`

5. **Points**
   - Current standings points
   - Primary standings metric

6. **Goal Differential** (+/-)
   - Goals for minus goals against
   - Colored green (positive) or red (negative)

7. **Model Win Rate** (overlay)
   - Average win probability from V7.3 model
   - Shows team's predicted performance
   - Source: `teamModelAccuracy` or calculated from recent predictions

8. **Next Opponent**
   - Upcoming opponent abbreviation
   - Game date
   - Start time ET
   - **Data Source**: Live fetch from NHL API (`/api/v1/schedule`)
   - **Lookahead**: 14 days

**Data Sources**:
- **Standings**: `web/src/data/currentStandings.json` (32 teams)
- **Model Accuracy**: `modelInsights.teamPerformance` (if available)
- **Next Games**: Fetched server-side from NHL API
- **Snapshots**: Built from `todaysPredictions.json`

**Interactive Features**:
- Client-side sorting
- Responsive mobile layout
- Team logo display

---

### 5. Goalies Page (`/goalies`)
**File**: `web/src/app/goalies/page.tsx`

#### Sections

##### Header
**Component**: `PageHeader`
- **Title**: "Goalie Intelligence"
- **Description**: "Rolling GSAx, rest advantage, start-likelihood signals, and trending form for every NHL netminder."
- **Last Updated**: Timestamp from `goaliePulse.updatedAt`

##### Season Leaders Section
**Description**: Top 4 goalies by save percentage

**Data Source**: Live fetch from NHL API
- **API Endpoint**: `https://api.nhle.com/stats/rest/en/goalie/summary?isAggregate=true&limit=-1&cayenneExp=seasonId=20252026`
- **Cache**: Revalidate every 3600 seconds (1 hour)
- **Filter**: Minimum 5 games played
- **Sort**: By save percentage descending
- **Limit**: Top 4

**Stat Cards** (4):
- **Label**: "Top Save % #1" (through #4)
- **Value**: Save percentage (e.g., "92.5%")
- **Detail**: Games played and wins (e.g., "15 GP | 12 W")

##### Live Ticker Section
**Component**: `GoalieTicker`
- Auto-scrolling ticker with goalie updates
- Shows recent changes, confirmations, injuries
- **Source**: `web/src/data/goaliePulse.json`

##### Detailed Analysis Section
**Description**: Individual goalie cards in 2-column grid

**Data Source**: `web/src/data/goaliePulse.json` → `goalies` array

**Each Goalie Card Shows**:

1. **Header**:
   - Team logo
   - Goalie name (e.g., "Connor Hellebuyck")
   - Team abbreviation
   - Trend indicator:
     - **Surging** (green, "UP")
     - **Steady** (blue, "->")
     - **Fresh** (cyan, "NEW")
     - **Fatigue Watch** (amber, "WARN")
   - Start likelihood percentage (e.g., "85%")
   - Rest days (e.g., "+2d")

2. **GSAx Metrics** (2 stats):
   - **Rolling GSAx**:
     - Value (e.g., "+2.3")
     - Color: Green (positive) or red (negative)
     - Detail: "Last 3 starts"
   - **Season GSAx**:
     - Value (e.g., "+15.7")
     - Color: Green (positive) or red (negative)
     - Detail: "Full season"

3. **Analysis Note**:
   - Text paragraph with scouting report
   - Written by analyst (from `goaliePulse.json`)

4. **Strengths** (left column):
   - Bullet list with green checkmarks
   - Green background cards
   - Examples: "Elite positioning", "Strong glove hand"

5. **Watch-outs** (right column):
   - Bullet list with X icons
   - Neutral background cards
   - Examples: "Struggles with screens", "Below-average rebound control"

6. **Footer**:
   - Next opponent abbreviation
   - Next opponent logo

**Trend Definitions**:
- **Surging**: Hot streak, high recent performance
- **Steady**: Consistent performance
- **Fresh**: New to rotation or recently returned
- **Fatigue Watch**: Heavy workload, potential decline

---

### 6. About Page (`/about`)
**File**: `web/src/app/about/page.tsx`

#### Sections

##### Mission Statement
**Description**: Centered card with mission
- **Heading**: "Our mission"
- **Text**: Transparency and data-first storytelling statement

##### How the Model Works
**Description**: 4-card grid explaining methodology

**Cards**:
1. **Data collection**
   - Official NHL Stats API
   - 3 seasons (2021-2024)
   - Play-by-play, stats, xG, Corsi, situational splits

2. **Feature engineering**
   - 216 features (V7.3)
   - Elo, xG differential, GSAx, fatigue, comeback ability
   - Travel distance, divisional matchups, post-break performance

3. **Model training**
   - Logistic regression + isotonic calibration
   - 2,460 games from 2021-2023
   - Simple, interpretable, less overfitting

4. **Validation & testing**
   - Full 2023-24 season (1,230 games) held out
   - Strict separation for honest accuracy
   - V7.3 achieves 61.4%

##### 216 Features Explained
**Description**: 3-column grid of feature categories

**Columns**:
1. **Team metrics (209 baseline)**:
   - Elo ratings (offense & defense)
   - xG for/against (rolling windows)
   - Power play & penalty kill %
   - Corsi & Fenwick differentials
   - Shots for/against per game
   - Faceoff win percentage
   - High-danger shot differentials
   - Goal differential (season & rolling)

2. **V7.3 situational (7 new)**:
   - Fatigue index differential
   - Third-period trailing performance
   - Travel distance impact
   - Divisional matchup flag
   - Post-break game indicators
   - Rest advantage calculations
   - Comeback ability metrics

3. **Context factors**:
   - Home ice advantage
   - Back-to-back games
   - Days since last game
   - Recent form (L3, L5, L10)
   - Schedule strength
   - Goalie rest days

##### Performance Highlights
**Description**: 4 stat cards with V7.3 results

**Cards**:
1. **Test accuracy**: `61.4%` (+7.6 pts vs baseline)
2. **A+ confidence**: `70.2%` (25+ pt edges)
3. **Brier score**: `0.243` (Well calibrated)
4. **Test games**: `1,230` (2023-24 season)

##### Tech Stack
**Description**: 2 cards showing ML and frontend tech

**Machine Learning Card**:
- Python 3.11
- scikit-learn (logistic regression)
- pandas & numpy
- NHL Stats API (official data)

**Frontend Card**:
- Next.js 16 + TypeScript
- Tailwind CSS v4
- Vercel hosting

##### Known Limitations
**Description**: Amber-bordered card with honest limitations list

**Limitations**:
- Last-minute injuries (cannot predict surprise scratches)
- Intangibles (rivalry games, playoff emotions)
- Lineup changes (mid-game adjustments)
- Randomness (60% still loses 40% of the time)
- Future uncertainty (past ≠ guaranteed future)

##### FAQs
**Description**: Accordion-style expandable Q&A sections

**Questions**:
1. **How often do you update predictions?**
   - Daily at 11:00 AM UTC (6:00 AM ET)
   - Automated via GitHub Actions
   - Pulls latest NHL API stats
   - Recalculates all 216 features

2. **Do you sell picks or betting advice?**
   - No. Analytics and educational platform only
   - No picks sales, no betting advice, no wager cuts

3. **Is the source code open source?**
   - Yes. Available on GitHub
   - Training code, feature engineering, website frontend

4. **Why logistic regression instead of neural networks?**
   - Interpretability
   - Exposes feature coefficients
   - Less prone to overfitting
   - Knowing "why" matters

##### Contact Section
**Description**: Centered card with CTAs

**CTAs**:
- "Follow on X" → https://x.com/puckcastai
- "View on GitHub" → https://github.com/noahowsh/puckcast
- "Email us" → mailto:team@puckcast.ai

---

### 7. Teams Page (`/teams`)
**File**: `web/src/app/teams/page.tsx`

**Status**: Placeholder / Coming Soon
- Page exists in routing but not fully implemented
- Intended for team-specific analytics pages
- Will show individual team stats, schedules, predictions

---

## Data Sources & Updates

### JSON Data Files
**Location**: `web/src/data/`

#### 1. `todaysPredictions.json`
**Size**: ~6.6 KB
**Update Frequency**: Daily at 11:00 AM UTC (6:00 AM ET)
**Generator**: `prediction/predict_full.py` via GitHub Actions

**Structure**:
```json
{
  "generatedAt": "2025-12-04T17:30:16.659088+00:00",
  "games": [
    {
      "id": "2025020426",
      "gameDate": "2025-12-04",
      "startTimeEt": "7:00 PM ET",
      "startTimeUtc": "2025-12-05T00:00:00+00:00",
      "homeTeam": {
        "name": "Bruins",
        "abbrev": "BOS"
      },
      "awayTeam": {
        "name": "Blues",
        "abbrev": "STL"
      },
      "homeWinProb": 0.4405,
      "awayWinProb": 0.5595,
      "confidenceScore": 0.119,
      "confidenceGrade": "B-",
      "edge": -0.06,
      "summary": "Blues project at 56% as the road lean — a B--tier edge worth 6.0 pts over a coin flip.",
      "modelFavorite": "away",
      "venue": "TD Garden",
      "season": "20252026"
    }
  ]
}
```

**Used On**:
- Homepage (hero section, top edges, upset radar)
- Predictions page (all games, sorting, confidence ladder)
- Leaderboards page (team snapshots, next games)

---

#### 2. `modelInsights.json`
**Size**: ~22 KB
**Update Frequency**: After model retraining (manual, ~weekly)
**Generator**: `training/train_v7_3_situational.py`

**Structure**:
```json
{
  "generatedAt": "2024-12-04T12:00:00.000000+00:00",
  "modelVersion": "V7.3",
  "overall": {
    "games": 1230,
    "accuracy": 0.6138211382113821,
    "baseline": 0.5373983739837398,
    "homeWinRate": 0.5373983739837398,
    "brier": 0.2428,
    "logLoss": 0.6642,
    "avgEdge": 0.18456
  },
  "confidenceBuckets": [
    {
      "label": "25+ pts",
      "grade": "A+",
      "min": 0.25,
      "max": null,
      "accuracy": 0.7023411371237458,
      "count": 299,
      "coverage": 0.243089430894309
    },
    // ... 5 more buckets
  ],
  "strategies": [
    {
      "name": "All predictions",
      "bets": 1230,
      "winRate": 0.6138211382113821,
      "units": 255,
      "note": "V7.3 model with situational features",
      "avgEdge": 0.18456
    },
    // ... 3 more strategies
  ],
  "bankrollSeries": [
    { "game": 1, "units": 100 },
    // ... time series data
  ]
}
```

**Used On**:
- Homepage (model stats)
- Predictions page (confidence ladder, slate stats)
- Performance page (all metrics, confidence buckets, strategies)
- Leaderboards page (team model accuracy overlay)

---

#### 3. `currentStandings.json`
**Size**: ~13 KB
**Update Frequency**: Daily (NHL API sync)
**Generator**: Backend script or manual update

**Structure**:
```json
{
  "teams": [
    {
      "team": "Winnipeg Jets",
      "abbrev": "WPG",
      "wins": 25,
      "losses": 10,
      "ot": 3,
      "points": 53,
      "gamesPlayed": 38,
      "pointPctg": 0.697,
      "goalDifferential": 32,
      "goalsForPerGame": 3.5,
      "goalsAgainstPerGame": 2.6,
      "shotsForPerGame": 31.2,
      "shotsAgainstPerGame": 28.1
    }
    // ... 31 more teams
  ]
}
```

**Used On**:
- Homepage (power index calculations)
- Leaderboards page (all standings data, power score calculations)

---

#### 4. `goaliePulse.json`
**Size**: ~15 KB
**Update Frequency**: Daily or as needed
**Generator**: Manual curation or backend script

**Structure**:
```json
{
  "updatedAt": "2025-12-04T10:00:00.000000+00:00",
  "notes": "Latest goalie updates and confirmations",
  "goalies": [
    {
      "name": "Connor Hellebuyck",
      "team": "WPG",
      "trend": "surging",
      "startLikelihood": 0.85,
      "restDays": 2,
      "rollingGsa": 2.3,
      "seasonGsa": 15.7,
      "note": "Elite positioning and rebound control...",
      "strengths": [
        "Elite positioning",
        "Strong glove hand",
        "Excellent rebound control"
      ],
      "watchouts": [
        "Struggles vs speed",
        "Occasional lapses in concentration"
      ],
      "nextOpponent": "MIN"
    }
    // ... more goalies
  ]
}
```

**Used On**:
- Goalies page (all sections: ticker, season leaders comparison, detailed cards)

---

#### 5. `startingGoalies.json`
**Size**: ~12 KB
**Update Frequency**: Daily (morning & pre-game)
**Generator**: NHL API sync (`src/nhl_prediction/nhl_api.py`)

**Structure**:
```json
{
  "updatedAt": "2025-12-04T15:00:00.000000+00:00",
  "confirmations": [
    {
      "gameId": "2025020426",
      "homeGoalie": {
        "id": 8471469,
        "name": "Jeremy Swayman",
        "team": "BOS"
      },
      "awayGoalie": {
        "id": 8476412,
        "name": "Jordan Binnington",
        "team": "STL"
      },
      "confirmed": true
    }
    // ... more games
  ]
}
```

**Used On**:
- Predictions page (indirectly via model features)
- Goalies page (start likelihood calculations)

---

#### 6. `lineCombos.json`
**Size**: ~3.7 KB
**Update Frequency**: As needed (lineup changes)

**Purpose**: Tracks line combinations for teams
**Used On**: Reserved for future features (not actively displayed)

---

#### 7. `playerInjuries.json`
**Size**: ~7.5 KB
**Update Frequency**: Daily

**Purpose**: Injury reports for key players
**Used On**: Reserved for future features (not actively displayed on current pages)

---

#### 8. `backtestingReport.json`
**Size**: 75 bytes
**Update Frequency**: Manual

**Purpose**: Historical backtest results
**Used On**: Reserved for future features

---

### Live API Calls

#### NHL Schedule API
**Endpoint**: `https://statsapi.web.nhl.com/api/v1/schedule`
**Used On**: Leaderboards page (next games)
**Frequency**: Server-side fetch on page load
**Cache**: No store (always fresh)
**Lookahead**: 14 days from current date

#### NHL Goalie Summary API
**Endpoint**: `https://api.nhle.com/stats/rest/en/goalie/summary?isAggregate=true&limit=-1&cayenneExp=seasonId=20252026`
**Used On**: Goalies page (season leaders)
**Frequency**: Server-side fetch on page load
**Cache**: Revalidate every 3600 seconds (1 hour)

---

## Calculations & Formulas

### Power Score Calculation
**Location**: `web/src/lib/current.ts` → `computeStandingsPowerScore()`

**Formula**:
```typescript
powerScore = Math.round(
  (points * 1.15) +                              // Standings points weighted
  (pointPctg * 120) +                            // Point percentage (0-1 scale)
  (goalDifferential * 1.6) +                     // Goal diff heavily weighted
  (goalsForPerGame * 14) +                       // Offense component
  (goalsAgainstPerGame * -12) +                  // Defense component (negative)
  ((shotsForPerGame - shotsAgainstPerGame) * 1.2) // Possession proxy
)
```

**Example** (Winnipeg Jets):
```
Points: 53
Point %: 0.697
Goal Diff: +32
GF/G: 3.5
GA/G: 2.6
SF/G: 31.2
SA/G: 28.1

= (53 * 1.15) + (0.697 * 120) + (32 * 1.6) + (3.5 * 14) + (2.6 * -12) + ((31.2 - 28.1) * 1.2)
= 60.95 + 83.64 + 51.2 + 49 - 31.2 + 3.72
= 217.31 → 217 (rounded)
```

---

### Edge Calculation
**Location**: Model output from `prediction/predict_full.py`

**Formula**:
```python
edge = homeWinProb - 0.5  # For home team
# OR
edge = awayWinProb - 0.5  # For away team

# Signed edge (positive = home favored, negative = away favored)
edge_signed = homeWinProb - 0.5
```

**Display Conversion**:
```typescript
edgePts = Math.abs(edge) * 100
// Example: edge = 0.169 → 16.9 pts
```

---

### Confidence Grade Mapping
**Location**: `web/src/lib/prediction.ts` → `getPredictionGrade()`

**Thresholds**:
```typescript
pts = Math.abs(edge) * 100

if (pts >= 25) return "A+"   // Elite confidence
if (pts >= 20) return "A"    // Strong confidence
if (pts >= 15) return "B+"   // Good confidence
if (pts >= 10) return "B"    // Medium confidence
if (pts >= 5)  return "C+"   // Weak confidence
return "C"                   // Coin flip
```

**Examples**:
- Edge = 0.27 → 27.0 pts → **A+**
- Edge = 0.21 → 21.0 pts → **A**
- Edge = 0.17 → 17.0 pts → **B+**
- Edge = 0.12 → 12.0 pts → **B**
- Edge = 0.07 → 7.0 pts → **C+**
- Edge = 0.03 → 3.0 pts → **C**

---

### Team Snapshot Power Score
**Location**: `web/src/lib/current.ts` → Internal helper

**Formula**:
```typescript
powerScore = Math.round(
  (avgProb * 100) +           // Average win probability
  (avgEdge * 100 * 0.5)       // Average edge (half-weighted)
)
```

**Used For**: Sorting team snapshots on homepage power index preview

---

### Movement Calculation
**Location**: `web/src/app/page.tsx` and `/leaderboards/page.tsx`

**Formula**:
```typescript
movement = standingsRank - powerRank

// Positive movement = Team ranks higher in power than standings
// Negative movement = Team ranks lower in power than standings
// Zero = No difference
```

**Example**:
- Team ranked #5 in standings, #2 in power
- Movement = 5 - 2 = +3 (riser)

- Team ranked #3 in standings, #8 in power
- Movement = 3 - 8 = -5 (slider)

---

### Accuracy Metrics

#### Overall Accuracy
```typescript
accuracy = correctPredictions / totalGames
// V7.3: 755 correct / 1230 games = 0.6138 = 61.38%
```

#### Edge vs Baseline
```typescript
edgeOverBaseline = (accuracy - baseline) * 100
// V7.3: (0.6138 - 0.5374) * 100 = 7.64 pts
```

#### Bucket Accuracy
```typescript
bucketAccuracy = correctInBucket / gamesInBucket
// A+ bucket: 210 correct / 299 games = 0.7023 = 70.2%
```

#### Brier Score
```typescript
// Lower is better (0 = perfect, 1 = worst)
brierScore = (1/N) * Σ(predicted - actual)²
// V7.3: 0.2428
```

#### Log Loss
```typescript
// Lower is better
logLoss = -(1/N) * Σ[y*log(p) + (1-y)*log(1-p)]
// V7.3: 0.6642
```

---

## Component Library

### Reusable Components
**Location**: `web/src/components/`

#### 1. TeamCrest
**File**: `TeamCrest.tsx`
**Props**: `abbrev` (string)
**Purpose**: Displays team logo/crest
**Usage**: Everywhere team branding is needed

#### 2. TeamLogo
**File**: `TeamLogo.tsx`
**Props**: `teamAbbrev` (string), `size` ("xs" | "sm" | "md" | "lg")
**Purpose**: Sized team logo with fallback
**Usage**: Goalies page, team displays

#### 3. PredictionCard
**File**: `PredictionCard.tsx`
**Props**: `game` (Prediction object)
**Purpose**: Compact game prediction display
**Usage**: Homepage edge cards

#### 4. ConfidenceBadge
**File**: `ConfidenceBadge.tsx`
**Props**: `grade` (ConfidenceGrade), `size` ("sm" | "md" | "lg")
**Purpose**: Letter grade badge (A+, A, B+, B, C+, C)
**Usage**: Predictions page, performance page

#### 5. StatCard
**File**: `StatCard.tsx`
**Props**: `label`, `value`, `change` (optional)
**Purpose**: Metric display card
**Usage**: About page, goalies page

#### 6. PageHeader
**File**: `PageHeader.tsx`
**Props**: `title`, `description`, `icon` (optional)
**Purpose**: Consistent page header styling
**Usage**: About page, goalies page

#### 7. ProbabilityBar
**File**: `ProbabilityBar.tsx`
**Props**: `value` (0-1), `variant` ("home" | "away")
**Purpose**: Visual probability meter
**Usage**: Prediction displays

#### 8. GoalieTicker
**File**: `GoalieTicker.tsx`
**Props**: `initial` (GoaliePulse object)
**Purpose**: Auto-scrolling goalie updates
**Usage**: Goalies page

#### 9. PowerBoardClient
**File**: `PowerBoardClient.tsx`
**Props**: `rows` (LeaderboardRow[]), `initialNextGames`
**Purpose**: Interactive power rankings table
**Usage**: Leaderboards page

#### 10. SiteFooter
**File**: `SiteFooter.tsx`
**Props**: None
**Purpose**: Site-wide footer with version
**Usage**: Root layout

#### 11. SiteNav
**File**: `SiteNav.tsx`
**Props**: None
**Purpose**: Global navigation bar
**Usage**: Root layout

#### 12. Analytics
**File**: `Analytics.tsx`
**Props**: None
**Purpose**: Client-side analytics tracking
**Usage**: Root layout

#### 13. PageTransition
**File**: `PageTransition.tsx`
**Props**: `children` (ReactNode)
**Purpose**: Smooth page transitions
**Usage**: Root layout wrapper

#### 14. LoadingSpinner
**File**: `LoadingSpinner.tsx`
**Props**: `size` (optional)
**Purpose**: Loading indicator
**Usage**: Async data fetching states

---

## SEO & Meta Tags

### Global Metadata
**Location**: `web/src/app/layout.tsx`

**Title Template**: "Puckcast | NHL Predictions + Analytics"

**Description**:
> "Data-driven NHL predictions powered by the official NHL API with 60%+ accuracy. Advanced analytics, goalie tracking, and real-time game predictions."

**OpenGraph**:
```json
{
  "title": "Puckcast | NHL Predictions + Analytics",
  "description": "60%+ accurate NHL predictions using 216 engineered features from official NHL data. Win probabilities and betting insights for every matchup.",
  "type": "website",
  "url": "https://puckcast.ai",
  "images": [{
    "url": "/puckcastsocial.png",
    "width": 1200,
    "height": 630,
    "alt": "Puckcast social preview"
  }]
}
```

**Twitter Card**:
```json
{
  "card": "summary_large_image",
  "title": "Puckcast | NHL Predictions + Analytics",
  "description": "Data-driven NHL predictions with 60%+ accuracy. Powered by official NHL API and advanced machine learning.",
  "images": ["/puckcastsocial.png"]
}
```

**Favicon**: `/puckcastai.png` (44x44 PNG)

---

### Page-Specific Titles
- **Homepage**: "Puckcast | NHL Predictions + Analytics"
- **Predictions**: "Predictions | Puckcast"
- **Performance**: "Performance | Puckcast"
- **Leaderboards**: "Power Rankings | Puckcast"
- **Goalies**: "Goalie Intelligence | Puckcast"
- **About**: "About | Puckcast"

---

### Structured Data
**Location**: Future enhancement
**Recommended**: JSON-LD for:
- Sports events
- Predictions
- Organization info
- BreadcrumbList

---

## Update Schedule

### Daily Updates (Automated)
**Time**: 11:00 AM UTC (6:00 AM ET)
**Trigger**: GitHub Actions cron job
**Process**:
1. `prediction/predict_full.py` runs
2. Fetches latest NHL API data (3 seasons)
3. Builds 220 features (213 baseline + 7 situational)
4. Generates predictions for today's games
5. Outputs to `prediction/web/src/data/todaysPredictions.json`
6. Manual copy to `web/src/data/todaysPredictions.json`
7. Deploy to Vercel (auto-deploy on push)

### Weekly Updates (Manual)
**Frequency**: ~Once per week
**Files Updated**:
- `currentStandings.json` (standings sync)
- `goaliePulse.json` (goalie analysis updates)
- `modelInsights.json` (if model is retrained)

### Model Retraining (Periodic)
**Frequency**: As needed (major updates)
**Process**:
1. Run `training/train_v7_3_situational.py`
2. Generate new `modelInsights.json`
3. Update model version references
4. Deploy new model file
5. Update documentation

---

## Browser Support

### Tested Browsers
- Chrome 120+ ✅
- Firefox 121+ ✅
- Safari 17+ ✅
- Edge 120+ ✅

### Mobile Support
- iOS Safari 16+ ✅
- Chrome Mobile 120+ ✅
- Responsive breakpoints: 640px, 768px, 1024px, 1280px

---

## Performance Metrics

### Lighthouse Scores (Target)
- **Performance**: 90+
- **Accessibility**: 95+
- **Best Practices**: 90+
- **SEO**: 95+

### Page Load Times (Target)
- **First Contentful Paint (FCP)**: <1.5s
- **Largest Contentful Paint (LCP)**: <2.5s
- **Time to Interactive (TTI)**: <3.5s

---

## Deployment

### Platform
**Host**: Vercel
**Domain**: puckcast.ai
**SSL**: Auto-managed by Vercel

### Build Process
```bash
cd web
npm install
npm run build
# Outputs to web/.next/
```

### Environment Variables
- `NEXT_PUBLIC_GA_ID`: Google Analytics tracking ID
- (Add others as needed)

### CI/CD
**Trigger**: Push to main branch
**Process**:
1. Vercel detects push
2. Runs `npm run build`
3. Deploys to production
4. Updates DNS (instant)

---

## Future Enhancements

### Planned Features
1. **Team Pages** (`/teams/[abbrev]`)
   - Individual team analytics
   - Historical performance
   - Upcoming schedule with predictions
   - Roster analysis

2. **Real-time Updates**
   - WebSocket connection for live odds
   - Ticker with probability shifts
   - Goalie confirmations via API polling

3. **User Features**
   - Prediction tracking (save favorites)
   - Historical accuracy by user preferences
   - Email alerts for high-edge games

4. **Enhanced Analytics**
   - Head-to-head matchup history
   - Line combination impact analysis
   - Referee influence metrics
   - Venue-specific trends

5. **API Endpoints**
   - Public API for predictions
   - Webhook integrations
   - CSV/JSON exports

---

## Contact & Support

**Website**: https://puckcast.ai
**Twitter/X**: https://x.com/puckcastai
**GitHub**: https://github.com/noahowsh/puckcast
**Email**: team@puckcast.ai

---

## Change Log

### December 4, 2024 19:00 UTC
- ✅ V7.3 model fully integrated (220 features)
- ✅ 6-bucket confidence system implemented (A+, A, B+, B, C+, C)
- ✅ Real predictions from NHL API (10 games for 2025-12-04)
- ✅ Comprehensive repository cleanup (142 files archived)
- ✅ All frontend pages updated with correct V7.3 references
- ✅ Consistent letter grading across all pages
- ✅ PRODUCTION_STATUS.md created
- ✅ This documentation file created

---

**End of Documentation**
