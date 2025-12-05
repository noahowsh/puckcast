# NHL Predictive Model Taxonomy

This document describes the core data entities, relationships, and feature families used to build the NHL game prediction pipeline.

---

## 1. Entities

### Team (`data/nhl_teams.csv`)
Static reference for all active NHL franchises.

**Attributes:**
- `teamId`: Numeric NHL identifier (e.g., 3 for Rangers)
- `triCode`: Three-letter abbreviation (e.g., `NYR`)
- `fullName` / `commonName` / `placeName`: Display names
- `divisionId`: Numeric division key
  - 15 → Pacific
  - 16 → Central
  - 17 → Atlantic
  - 18 → Metropolitan
- `conferenceId`: Derived from division
  - 15/16 → Western
  - 17/18 → Eastern
- `firstSeasonId`: ISO date of franchise inaugural season
- `officialSiteUrl`: Team website

**Purpose:** Mapping between MoneyPuck abbreviations and numeric IDs for model features.

---

### Game
A single NHL regular season game.

**Identifiers:**
- `gameId`: Unique MoneyPuck game identifier
- `gameDate`: Date of game (YYYY-MM-DD)
- `seasonId`: Season in format `20232024` (for 2023-24 season)

**Attributes:**
- `home_score`, `away_score`: Final scores
- `home_win`: Binary target (1 if home team won, 0 if away won)
- `teamId_home`, `teamId_away`: Numeric team IDs

---

### Team-Game Record
One row per team per game from MoneyPuck.

**Source:** `data/moneypuck_all_games.csv`

**Core Stats:**
- Goals for/against
- Shots for/against
- Faceoffs won
- Penalties
- Special teams opportunities

**Advanced Stats (MoneyPuck):**
- `xGoalsFor`, `xGoalsAgainst`: Expected goals based on shot quality
- `highDangerShotsFor`, `highDangerShotsAgainst`: High-danger shot counts
- `highDangerxGoalsFor`: xG from high-danger shots only
- `corsiPercentage`: Shot attempt share (all shots, blocked, and missed)
- `fenwickPercentage`: Unblocked shot attempt share
- `scoreAdjustedShotsAttemptsFor`: Context-adjusted shot attempts

---

## 2. Relationships

### Team ⟷ Game
- Many-to-many through `homeTeamId` and `awayTeamId`
- Each game has exactly one home team and one away team
- Each team plays ~82 games per regular season

### Game ⟷ Team-Game Records
- One game = two team-game records (home and away perspectives)
- Merged in `build_game_dataframe()` to create one row per game with home/away splits

### Team ⟷ Season
- Each team has cumulative season stats (wins, losses, points)
- Computed using `.cumsum()` on chronologically-ordered game logs

---

## 3. Feature Families

Our model uses 129 engineered features organized into families:

### 3.1. Team Strength (Season-to-Date)
Cumulative performance metrics up to (but not including) current game:

- **Win Percentage:** Proportion of games won so far
- **Goal Differential:** Average goals for minus goals against
- **Points Metrics:** NHL standings points, point percentage
- **Shot Metrics:** Shots for/against per game averages

**Key:** All are **lagged** - computed using games *before* current game only.

---

### 3.2. Recent Form (Rolling Windows)
Statistics over last N games (3, 5, or 10):

For each window size `w ∈ {3, 5, 10}`:
- `rolling_win_pct_{w}`: Win rate over last w games
- `rolling_goal_diff_{w}`: Average goal margin
- `rolling_pp_pct_{w}`: Power-play efficiency
- `rolling_pk_pct_{w}`: Penalty-kill efficiency
- `rolling_faceoff_{w}`: Faceoff win percentage
- `shotsFor_roll_{w}`, `shotsAgainst_roll_{w}`: Shot averages

**Implementation:**
```python
group['rolling_win_pct_5'] = group['win'].shift(1).rolling(5).mean()
```

**Key:** `.shift(1)` ensures we don't include the current game.

---

### 3.3. Momentum Indicators
Difference between recent form and season average:

\[
\text{momentum\_win\_pct} = \text{rolling\_win\_pct\_5} - \text{season\_win\_pct}
\]

Positive momentum → team performing better recently than their season average.

Similar for goal differential and shot margin.

---

### 3.4. Rest & Scheduling
NHL's compressed schedule creates fatigue effects:

- `rest_days`: Days since previous game
- `is_b2b`: Binary flag for back-to-back games (≤1 day rest)
- `games_last_3d`: Number of games in last 3 days
- `games_last_6d`: Number of games in last 6 days
- `rest_bucket`: Categorical variable
  - "b2b" (0-1 days)
  - "one_day" (2 days)
  - "two_days" (3 days)
  - "three_plus" (3+ days)

**Impact:** Back-to-backs reduce win probability, especially for away teams.

---

### 3.5. Elo Rating System
Dynamic team strength rating updated after each game:

**Algorithm:**
1. Initialize all teams at 1500 each season
2. Add +30 home ice advantage to home team
3. Compute expected outcome:
   \[
   E_{\text{home}} = \frac{1}{1 + 10^{(\text{Elo}_{\text{away}} - (\text{Elo}_{\text{home}} + 30))/400}}
   \]
4. Update ratings based on outcome and margin:
   \[
   \Delta = K \cdot \text{margin\_multiplier} \cdot (\text{actual} - E_{\text{home}})
   \]
   where margin multiplier accounts for blowouts

**Features:**
- `elo_home_pre`, `elo_away_pre`: Pre-game Elo ratings
- `elo_diff_pre`: Home Elo - Away Elo
- `elo_expectation_home`: Elo-based win probability

---

### 3.6. Special Teams Matchups
Power-play and penalty-kill interactions:

- `special_teams_matchup`: Home PP% vs Away PK%
- `special_teams_matchup_inverse`: Home PK% vs Away PP%

**Rationale:** When penalties are called, matchup of PP vs PK units matters.

---

### 3.7. Team Identity Features
One-hot encoded team dummy variables:

- 32 features for `home_team_X`
- 32 features for `away_team_X`

**Purpose:** Captures:
- Roster quality differences
- Home ice advantage (varies by team/arena)
- Coaching and systems

**Limitation:** Doesn't generalize to expansion teams.

---

### 3.8. Differential Features
For most metrics, we compute **home minus away** difference:

\[
\text{feature\_diff} = \text{feature\_home} - \text{feature\_away}
\]

**Example:** 
- Home team 60% faceoff win rate
- Away team 45% faceoff win rate
- → `rolling_faceoff_5_diff = 0.15`

Model learns from relative advantage directly.

---

### 3.9. MoneyPuck Advanced Features (Available)

MoneyPuck provides metrics beyond basic stats:

**Expected Goals (xG):**
- `xGoalsFor`, `xGoalsAgainst`: Shot quality-adjusted goal expectation
- `xGoalsPercentage`: Share of xG in game

**Shot Quality:**
- `highDangerShotsFor`: Shots from high-danger areas
- `highDangerxGoalsFor`: xG from high-danger shots only
- `lowDanger`, `mediumDanger`: Shot breakdowns

**Possession:**
- `corsiPercentage`: All shot attempts share
- `fenwickPercentage`: Unblocked shot attempts share
- `shotAttemptsFor`: Total shot attempts (Corsi events)

**Score-Adjusted:**
- `scoreAdjustedShotsAttemptsFor`: Adjusts for score effects (teams trailing shoot more)

**Currently:** Not all MoneyPuck features are used - future enhancement opportunity!

---

## 4. Target Definition

**Binary Classification:** Predict home team win

\[
\text{home\_win} = \begin{cases}
1 & \text{if } \text{home\_score} > \text{away\_score} \\
0 & \text{otherwise}
\end{cases}
\]

**Includes:** Regulation, overtime, and shootout wins (all count as wins).

**Alternative Targets (Future):**
- Regulation win only (excluding OT/SO)
- Puck line cover (win by 2+ goals)
- Total goals over/under (requires regression)

---

## 5. Data Sources

### Primary: MoneyPuck
**URL:** https://moneypuck.com/

**Data File:** `data/moneypuck_all_games.csv`
- **Source:** https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv
- **Size:** ~115MB (220,000+ team-game records)
- **Coverage:** 2008-2024 seasons
- **Update Frequency:** Maintained by MoneyPuck team

**Advantages:**
- Professional-grade analytics
- Expected goals (xG) and shot quality
- Used by NHL analysts, media, researchers
- Free and publicly available

### Secondary: NHL Team Metadata
**File:** `data/nhl_teams.csv`
- Static reference for 32 active franchises
- Team IDs, names, divisions, conferences
- Used for mapping MoneyPuck abbreviations to numeric IDs

---

## 6. Modelling Workflow

### Pipeline Overview

```
1. INGEST
   ↓
   load_moneypuck_data()
   - Filter to team-level, regular season, "all" situation
   
2. STANDARDIZE
   ↓
   _standardize_moneypuck_columns()
   - Map MoneyPuck columns to expected schema
   - Convert team abbreviations to numeric IDs
   
3. ENGINEER FEATURES
   ↓
   engineer_team_features()
   - Compute rolling windows (3, 5, 10 games)
   - Create lagged cumulative stats
   - Calculate momentum indicators
   - Add rest and schedule metrics
   
4. BUILD MATCHUPS
   ↓
   build_game_dataframe()
   - Merge home and away team logs
   - Create one row per game
   - Compute target variable (home_win)
   
5. ADD ELO
   ↓
   _add_elo_features()
   - Compute pre-game Elo ratings
   - Update ratings after each game
   
6. CREATE FEATURE MATRIX
   ↓
   build_dataset()
   - Compute differentials (home - away)
   - One-hot encode teams
   - Create final feature matrix
   
7. TRAIN & EVALUATE
   ↓
   compare_models()
   - Split chronologically (train/val/test)
   - Tune hyperparameters
   - Calibrate probabilities
   - Select best model
```

---

## 7. Data Integrity & Validation

### No Data Leakage
**Critical principle:** Only use information available *before* each game.

**Implementation:**
- All cumulative stats use `.shift(1)` or `.cumsum().shift(1)`
- Rolling windows start with `.shift(1)`
- Elo ratings computed with pre-game values
- Manual validation: early-season games have zeros/nulls (expected)

**Test:**
```python
# For game on 2023-10-15
# Check that season_win_pct uses games through 2023-10-14 only
assert logs.loc[game_idx, 'games_played_prior'] == prior_games_count
```

### Temporal Ordering
Games are sorted chronologically:
```python
logs = logs.sort_values(['teamId', 'seasonId', 'gameDate', 'gameId'])
```

This ensures `.shift(1)` operations reference the correct prior game.

### Missing Data Handling
- **Early season:** Rolling windows have insufficient history → filled with zeros
- **Team abbreviation mismatches:** Old franchises dropped (e.g., Atlanta Thrashers)
- **Missing opponents:** Games dropped if opponent not in current 32 teams

---

## 8. Future Extensions

### 8.1. MoneyPuck xGoals Integration
Currently available but not fully utilized:

```python
# Potential features:
- xg_differential: xGoalsFor - xGoalsAgainst
- xg_vs_actual: goalsFor - xGoalsFor (over/under-performing)
- rolling_xg_5: Recent xG trends
- shot_quality_ratio: highDangerxGoals / xGoals
```

### 8.2. Situation-Specific Stats
MoneyPuck has 5v5, power-play, penalty-kill splits:

```python
# Load 5v5 data
df_5v5 = df[df['situation'] == '5on5']
# Use even-strength metrics separately
```

### 8.3. Score-Adjusted Metrics
Account for score effects (trailing teams shoot more):

```python
- scoreAdjustedShotsAttemptsFor
- scoreAdjustedUnblockedShotAttemptsFor
- scoreAdjustedTotalShotCreditFor
```

### 8.4. Betting Market Comparison
Ultimate goal: Compare model probabilities to betting odds.

See `docs/betting_integration_plan.md` for roadmap to:
1. Obtain closing line odds
2. Convert to probabilities (remove vig)
3. Identify +EV opportunities
4. Simulate betting strategies
5. Calculate ROI

**Success Metric:** Model probabilities more accurate than market-implied probabilities.

---

## 9. Key Takeaways

### What Makes This Model Different

1. **Professional Data:** MoneyPuck's xG and shot quality (not available in basic stats)
2. **No Leakage:** Rigorous temporal validation - all features are truly pre-game
3. **Comprehensive Features:** 129 features across 7 families
4. **Domain Knowledge:** Hockey-specific features (special teams matchups, back-to-backs)
5. **Clear Goal:** Not just accuracy - ultimate aim is beating betting markets

### Success Criteria

- ✅ **Accuracy > 56%:** Beat home advantage baseline (~54.5%)
- ✅ **Well-calibrated:** Predicted probabilities match observed frequencies
- ✅ **Feature importance:** Interpretable - understand what drives predictions
- ✅ **ROI positive:** When compared to betting markets (future validation)

---

**For detailed usage instructions, see `docs/usage.md`**  
**For betting integration plan, see `docs/betting_integration_plan.md`**
