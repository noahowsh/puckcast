# 🏒 PUCKCAST FEATURE DICTIONARY
## Complete Guide to All 204 Prediction Features

**Last Updated:** November 20, 2025
**Model Version:** 2.0
**Total Features:** 204
**Recommended Subset:** Top 50 (75% reduction, +0.81pp accuracy gain)

---

## 📊 QUICK STATS

| Metric | Value |
|--------|-------|
| Total Features | 204 |
| Feature Categories | 17 |
| Zero-Importance Features | 44 (can be removed) |
| Top 10 Features Account For | ~15% of model weight |
| Top 50 Features Account For | ~60% of model weight |

---

## 🎯 FEATURE CATEGORIES BY IMPORTANCE

Features ranked by average importance within category:

| Rank | Category | Count | Avg Importance | Top Feature |
|------|----------|-------|----------------|-------------|
| 1 | **Season Progress** | 2 | 0.02653 | games_played_prior_away |
| 2 | **High-Danger Shots** | 3 | 0.01533 | rolling_high_danger_shots_3_diff |
| 3 | **Goal Differential** | 5 | 0.01032 | rolling_goal_diff_10_diff |
| 4 | **Shot Volume** | 9 | 0.01013 | shotsFor_roll_10_diff |
| 5 | **Schedule/Rest** | 23 | 0.00987 | is_b2b_diff |
| 6 | **Streaks/Travel** | 6 | 0.00774 | consecutive_home_prior_away |
| 7 | **Expected Goals (xG)** | 17 | 0.00426 | rolling_xg_for_3_diff |
| 8 | **Goalie Performance** | 14 | 0.00392 | goalie_rolling_gsa_diff |
| 9 | **Team Goaltending** | 6 | 0.00313 | rolling_gsax_10_diff |
| 10 | **Team Identity** | 62 | 0.00309 | home_team_28 (Utah) |
| 11 | **Elo Rating** | 2 | 0.00275 | elo_diff_pre |
| 12 | **Possession Metrics** | 6 | 0.00136 | rolling_corsi_5_diff |
| 13 | **Faceoffs** | 3 | 0.00136 | rolling_faceoff_5_diff |
| 14 | **Other (Win %)** | 5 | 0.00119 | rolling_win_pct_3_diff |
| 15 | **Altitude** | 6 | 0.00084 | is_high_altitude_home |
| 16 | **Momentum** | 1 | 0.00071 | momentum_win_pct_diff |
| 17 | **Line Combinations** | 10 | 0.00000 | ❌ Zero importance |
| 17 | **Season Points %** | 4 | 0.00000 | ❌ Zero importance |
| 17 | **Special Teams** | 20 | 0.00000 | ❌ Zero importance |
| 17 | **Penalties** | 2 | 0.00000 | ❌ Zero importance |
| 17 | **Rebounds** | 6 | 0.00000 | ❌ Zero importance |

**Key Insight:** Top 6 categories account for 70% of predictive power!

---

## 🏆 TOP 50 FEATURES (Recommended Feature Set)

Using only these 50 features provides +0.81pp accuracy gain over using all 204!

### Rank 1-10: Elite Predictors

| # | Feature | Importance | Category | Description |
|---|---------|------------|----------|-------------|
| 1 | `rolling_high_danger_shots_3_diff` | 0.0317 | High-Danger Shots | Differential in high-danger shots (last 3 games) |
| 2 | `games_played_prior_away` | 0.0266 | Season Progress | Away team games played this season |
| 3 | `games_played_prior_home` | 0.0265 | Season Progress | Home team games played this season |
| 4 | `is_b2b_diff` | 0.0263 | Schedule/Rest | Back-to-back differential (home B2B - away B2B) |
| 5 | `goalie_rolling_gsa_diff` | 0.0258 | Goalie Performance | Differential in goalie GSA (Goals Saved Above expected) |
| 6 | `shotsFor_roll_10_diff` | 0.0165 | Shot Volume | Differential in shots for (last 10 games) |
| 7 | `rest_away_one_day` | 0.0163 | Schedule/Rest | Away team on 1 day rest (binary) |
| 8 | `games_last_3d_diff` | 0.0162 | Schedule/Rest | Games in last 3 days differential |
| 9 | `season_shot_margin_diff` | 0.0160 | Shot Volume | Season shot differential margin |
| 10 | `rolling_goal_diff_10_diff` | 0.0157 | Goal Differential | Goal differential (last 10 games) |

### Rank 11-20: Strong Predictors

| # | Feature | Importance | Category | Description |
|---|---------|------------|----------|-------------|
| 11 | `rest_days_away` | 0.0154 | Schedule/Rest | Days since away team's last game |
| 12 | `away_b2b` | 0.0153 | Schedule/Rest | Away team on back-to-back |
| 13 | `rest_away_b2b` | 0.0153 | Schedule/Rest | Away team on B2B (binary) |
| 14 | `is_b2b_home` | 0.0143 | Schedule/Rest | Home team on back-to-back |
| 15 | `rest_diff` | 0.0143 | Schedule/Rest | Rest days differential (home - away) |
| 16 | `rest_days_diff` | 0.0143 | Schedule/Rest | Rest days differential |
| 17 | `rolling_goal_diff_3_diff` | 0.0130 | Goal Differential | Goal differential (last 3 games) |
| 18 | `shotsAgainst_roll_10_diff` | 0.0129 | Shot Volume | Differential in shots against (last 10 games) |
| 19 | `shotsFor_roll_3_diff` | 0.0126 | Shot Volume | Differential in shots for (last 3 games) |
| 20 | `rolling_xg_for_3_diff` | 0.0120 | Expected Goals | xGoals for differential (last 3 games) |

### Rank 21-30: Good Predictors

| # | Feature | Importance | Category | Description |
|---|---------|------------|----------|-------------|
| 21 | `is_b2b_away` | 0.0120 | Schedule/Rest | Away team on B2B |
| 22 | `goalie_rest_days_diff` | 0.0116 | Goalie Performance | Goalie rest days differential |
| 23 | `season_goal_diff_avg_diff` | 0.0114 | Goal Differential | Season goal diff average differential |
| 24 | `home_team_28` | 0.0107 | Team Identity | Utah Hockey Club (Team ID 28) |
| 25 | `rolling_xg_for_5_diff` | 0.0104 | Expected Goals | xGoals for differential (last 5 games) |
| 26 | `rest_home_one_day` | 0.0103 | Schedule/Rest | Home team on 1 day rest |
| 27 | `goalie_trend_score_diff` | 0.0101 | Goalie Performance | Goalie form trend differential |
| 28 | `shotsAgainst_roll_3_diff` | 0.0098 | Shot Volume | Shots against differential (last 3 games) |
| 29 | `momentum_goal_diff_diff` | 0.0096 | Goal Differential | Recent momentum goal differential |
| 30 | `consecutive_home_prior_away` | 0.0096 | Streaks/Travel | Away team's consecutive home games |

### Rank 31-40: Moderate Predictors

| # | Feature | Importance | Category | Description |
|---|---------|------------|----------|-------------|
| 31 | `consecutive_away_prior_home` | 0.0088 | Streaks/Travel | Home team's consecutive away games |
| 32 | `travel_burden_home` | 0.0088 | Streaks/Travel | Home team travel burden |
| 33 | `games_last_3d_away` | 0.0087 | Schedule/Rest | Away team games in last 3 days |
| 34 | `shot_margin_last_game_diff` | 0.0084 | Shot Volume | Last game shot margin differential |
| 35 | `rest_home_b2b` | 0.0084 | Schedule/Rest | Home team on B2B |
| 36 | `home_b2b` | 0.0084 | Schedule/Rest | Home B2B (binary) |
| 37 | `momentum_shot_margin_diff` | 0.0076 | Shot Volume | Momentum shot margin differential |
| 38 | `games_last_3d_home` | 0.0074 | Schedule/Rest | Home team games in last 3 days |
| 39 | `goalie_start_likelihood_diff` | 0.0074 | Goalie Performance | Starting goalie likelihood differential |
| 40 | `home_team_30` | 0.0073 | Team Identity | Minnesota Wild (Team ID 30) |

### Rank 41-50: Useful Predictors

| # | Feature | Importance | Category | Description |
|---|---------|------------|----------|-------------|
| 41 | `home_team_20` | 0.0072 | Team Identity | Calgary Flames (Team ID 20) |
| 42 | `rolling_high_danger_shots_10_diff` | 0.0072 | High-Danger Shots | High-danger shots differential (last 10 games) |
| 43 | `consecutive_home_prior_home` | 0.0072 | Streaks/Travel | Home team consecutive home games |
| 44 | `rolling_xg_against_3_diff` | 0.0071 | Expected Goals | xGoals against differential (last 3 games) |
| 45 | `rolling_high_danger_shots_5_diff` | 0.0071 | High-Danger Shots | High-danger shots differential (last 5 games) |
| 46 | `rolling_xg_for_10_diff` | 0.0070 | Expected Goals | xGoals for differential (last 10 games) |
| 47 | `season_xg_diff_avg_diff` | 0.0066 | Expected Goals | Season xG differential average |
| 48 | `rolling_xg_diff_5_diff` | 0.0063 | Expected Goals | xGoals differential (last 5 games) |
| 49 | `games_last_6d_home` | 0.0062 | Schedule/Rest | Home team games in last 6 days |
| 50 | `elo_expectation_home_away` | 0.0062 | Elo Rating | Elo-based win probability differential |

**Performance:** Using ONLY these 50 features → **60.24% accuracy** (+0.81pp over all 204!)

---

## 📖 FEATURE CALCULATION METHODS

### 1. Differential Features (`_diff` suffix)

**Format:** `{metric}_diff`
**Calculation:** `home_value - away_value`
**Example:** `rest_days_diff = rest_days_home - rest_days_away`

**Purpose:** Compares home vs away advantage for any metric

**Positive value** = home team advantage
**Negative value** = away team advantage

---

### 2. Rolling Window Features (`rolling_` prefix)

**Format:** `rolling_{metric}_{window}_diff`
**Calculation:** Lagged rolling average over N previous games
**Windows:** 3, 5, 10 games

**Example:**
```python
rolling_goal_diff_3 = mean(goal_diff from games t-4, t-3, t-2)  # NOT including current game t-1
# Then: rolling_goal_diff_3_diff = home_rolling_goal_diff_3 - away_rolling_goal_diff_3
```

**Critical:** Uses `.shift(1)` to avoid future leakage - current game NOT included

---

### 3. Season Aggregate Features (`season_` prefix)

**Format:** `season_{metric}_avg_diff`
**Calculation:** Season-to-date average (all games before current)

**Example:**
```python
season_goal_diff_avg = mean(goal_diff for all games this season before current game)
season_goal_diff_avg_diff = home_season_goal_diff_avg - away_season_goal_diff_avg
```

---

### 4. High-Danger Shots

**Definition:** Shots from prime scoring areas

**Zone:**
- Distance < 25 feet from goal
- Angle < 45 degrees from center
- "Royal Road" / slot area

**Calculation:**
```python
for shot in game:
    if shot.distance < 25 and abs(shot.angle) < 45:
        high_danger_shots += 1
```

**Why important:** 2-3x higher goal probability than perimeter shots

---

### 5. Expected Goals (xG)

**Model:** Custom gradient boosting classifier (94.8% accuracy)

**Input Features:**
- Shot distance (feet)
- Shot angle (degrees)
- Shot type (Wrist, Slap, Snap, Backhand, Deflected, Tip-In, Wrap-around)
- Is rebound (shot within 3 seconds of previous shot)

**Training Data:** 23,000+ shots from 2021-22 season

**Output:** Probability of goal (0.0 to 1.0)

**Example:**
- Wrist shot from slot (15 ft, 10°): xG = 0.15 (15% goal probability)
- Perimeter slap shot (40 ft, 45°): xG = 0.03 (3% goal probability)

---

### 6. Goalie Stats Saved Above (GSA)

**Formula:**
```
GSA = Actual Saves - Expected Saves
    = (Shots - Goals) - Sum(xG for all shots faced)
```

**Normalization:** Per 60 minutes
```
GSAx/60 = (GSA / Minutes Played) * 60
```

**Example:**
- Goalie faces 30 shots with combined xG = 2.8
- Allows 2 goals
- GSA = 28 saves - 27.2 expected saves = +0.8 goals saved above expected

---

### 7. Elo Ratings

**Base Rating:** 1500
**Home Advantage:** +30 Elo points
**K-Factor:** 10 (update rate)

**Update Formula:**
```python
expected_home_win = 1 / (1 + 10^((away_elo - (home_elo + 30)) / 400))
margin_multiplier = log(|goal_diff| + 1) * (2.2 / (|elo_diff| * 0.001 + 2.2))
delta = K * margin_multiplier * (actual_outcome - expected_outcome)

home_elo_new = home_elo_old + delta
away_elo_new = away_elo_old - delta
```

**Margin-of-Victory Adjustment:** Bigger wins = bigger Elo swings

**Reset:** Ratings reset to 1500 at start of each season

---

### 8. Back-to-Back (B2B) Detection

**Definition:** Game with 0 days rest (played yesterday)

**Binary Flags:**
- `is_b2b_home` = 1 if home team played yesterday, else 0
- `is_b2b_away` = 1 if away team played yesterday, else 0
- `is_b2b_diff` = is_b2b_home - is_b2b_away

**Rest Buckets:**
- "b2b" = 0 days
- "one_day" = 1 day
- "two_days" = 2 days
- "three_plus" = 3+ days

**Why important:** B2B teams win ~40% vs 55% normal rest

---

### 9. Team Identity Features (`home_team_X`, `away_team_X`)

**Format:** One-hot encoded team IDs

**Example:**
- `home_team_28 = 1` if home team is Utah (ID 28), else 0
- `away_team_28 = 1` if away team is Utah (ID 28), else 0

**Purpose:** Captures team-specific effects not captured by other features

**Most Important Teams:**
- Team 28 (Utah): +1.07% importance
- Team 30 (Minnesota): +0.73% importance
- Team 20 (Calgary): +0.72% importance

---

### 10. Momentum Features

**Window:** Last 5 games (shorter than rolling windows)

**Metrics:**
- `momentum_win_pct` = wins / games (last 5)
- `momentum_goal_diff` = avg goal differential (last 5)
- `momentum_shot_margin` = avg shot differential (last 5)
- `momentum_xg` = avg xG differential (last 5)

**Purpose:** Capture recent hot/cold streaks

---

## 🗑️ ZERO-IMPORTANCE FEATURES (Can Remove)

These 44 features have **exactly 0.0000 importance** and can be safely removed:

### Line Combinations (10 features) - ALL ZERO
- lineForwardContinuity_diff
- lineForwardConcentration_diff
- lineDefenseContinuity_diff
- lineDefenseConcentration_diff
- line_forward_balance_diff
- line_defense_balance_diff
- lineTopTrioSeconds_diff
- lineTopPairSeconds_diff
- line_top_trio_min_diff
- line_top_pair_min_diff

### Special Teams Rolling Windows (20 features) - ALL ZERO
- rolling_powerPlayPct_5_diff
- rolling_powerPlayPct_10_diff
- rolling_penaltyKillPct_5_diff
- rolling_penaltyKillPct_10_diff
- rolling_powerPlayNetPct_5_diff
- rolling_powerPlayNetPct_10_diff
- rolling_penaltyKillNetPct_5_diff
- rolling_penaltyKillNetPct_10_diff
- rolling_specialTeamEdge_5_diff
- rolling_specialTeamEdge_10_diff
- (and 10 more...)

### Season Points % (4 features) - ALL ZERO
- seasonPointPct_diff
- rolling_seasonPointPct_3_diff
- rolling_seasonPointPct_5_diff
- rolling_seasonPointPct_10_diff

### Rebounds (6 features) - ALL ZERO
- All rolling rebound metrics at 5/10 game windows

### Goalie Team-Level (4 features) - NEAR ZERO
- rolling_goalie_save_pct_5_diff
- rolling_goalie_save_pct_10_diff
- rolling_goalie_xg_saved_5_diff
- rolling_goalie_xg_saved_10_diff

**Why zero importance?**
1. **Line combinations:** Too granular, captured by team performance metrics
2. **Special teams rolling:** Duplicated by season aggregates, changes too slowly
3. **Season points %:** Redundant with win %
4. **Rebounds:** Signal absorbed by xG and shot quality metrics

---

## 📋 COMPLETE ALPHABETICAL FEATURE LIST

### A
- `altitude_diff_away` - Altitude differential for away team
- `altitude_diff_home` - Altitude differential for home team
- `away_b2b` - Away team on back-to-back (binary)
- `away_team_X` - Away team one-hot encodings (32 teams)

### C
- `consecutive_away_prior_away` - Away team's consecutive away games
- `consecutive_away_prior_home` - Home team's consecutive away games
- `consecutive_home_prior_away` - Away team's consecutive home games
- `consecutive_home_prior_home` - Home team's consecutive home games

### E
- `elo_diff_pre` - Pre-game Elo rating differential (home - away)
- `elo_expectation_home` - Elo-based home win probability
- `elo_expectation_home_away` - Elo expectation differential

### G
- `games_last_3d_away` - Away team games in last 3 days
- `games_last_3d_diff` - Games in last 3 days differential
- `games_last_3d_home` - Home team games in last 3 days
- `games_last_6d_away` - Away team games in last 6 days
- `games_last_6d_diff` - Games in last 6 days differential
- `games_last_6d_home` - Home team games in last 6 days
- `games_played_prior_away` - Away team games played this season ⭐ #2
- `games_played_prior_home` - Home team games played this season ⭐ #3
- `goalie_confirmed_start_diff` - Goalie start confirmation differential
- `goalie_games_played_diff` - Goalie games played differential
- `goalie_injury_flag_diff` - Goalie injury status differential
- `goalie_rest_days_diff` - Goalie rest days differential ⭐ #22
- `goalie_rolling_gsa_diff` - Goalie GSA differential ⭐ #5
- `goalie_save_pct_diff` - Goalie save % differential
- `goalie_save_pct_game_diff` - Goalie game save % differential
- `goalie_shots_faced_diff` - Goalie shots faced differential
- `goalie_start_likelihood_diff` - Goalie start likelihood differential
- `goalie_trend_score_diff` - Goalie trend differential ⭐ #27
- `goalie_xg_saved_diff` - Goalie xG saved differential
- `goalie_xgoals_faced_diff` - Goalie xG faced differential

### H
- `home_b2b` - Home team on back-to-back (binary)
- `home_team_X` - Home team one-hot encodings (32 teams)

### I
- `is_b2b_away` - Away team B2B flag
- `is_b2b_diff` - B2B differential ⭐ #4
- `is_b2b_home` - Home team B2B flag ⭐ #14
- `is_high_altitude_away` - Away team at high altitude
- `is_high_altitude_diff` - Altitude differential
- `is_high_altitude_home` - Home team at high altitude

### L
- `line_defense_balance_diff` - Defense balance differential ❌ ZERO
- `line_forward_balance_diff` - Forward balance differential ❌ ZERO
- `lineDefenseContinuity_diff` - Defense continuity differential ❌ ZERO
- `lineForwardContinuity_diff` - Forward continuity differential ❌ ZERO
- (8 more line combination features - all zero importance)

### M
- `momentum_goal_diff_diff` - Momentum goal diff differential ⭐ #29
- `momentum_shot_margin_diff` - Momentum shot margin differential
- `momentum_win_pct_diff` - Momentum win % differential
- `momentum_xg_diff` - Momentum xG differential

### P
- `penaltyKillNetPct_diff` - Penalty kill net % differential ❌ ZERO
- `penaltyKillPct_diff` - Penalty kill % differential ❌ ZERO
- `powerPlayNetPct_diff` - Power play net % differential ❌ ZERO
- `powerPlayPct_diff` - Power play % differential ❌ ZERO

### R
- `rest_away_b2b` - Away team B2B rest ⭐ #13
- `rest_away_one_day` - Away team 1-day rest ⭐ #7
- `rest_away_three_plus` - Away team 3+ days rest
- `rest_away_two_days` - Away team 2-day rest
- `rest_days_away` - Away team rest days ⭐ #11
- `rest_days_diff` - Rest days differential ⭐ #16
- `rest_days_home` - Home team rest days
- `rest_diff` - Rest differential ⭐ #15
- `rest_home_b2b` - Home team B2B rest
- `rest_home_one_day` - Home team 1-day rest ⭐ #26
- `rest_home_three_plus` - Home team 3+ days rest
- `rest_home_two_days` - Home team 2-day rest
- `rolling_corsi_X_diff` - Possession (Corsi) rolling differentials (3/5/10 windows)
- `rolling_faceoff_X_diff` - Faceoff % rolling differentials (3/5/10 windows)
- `rolling_fenwick_X_diff` - Possession (Fenwick) rolling differentials (3/5/10 windows)
- `rolling_goal_diff_X_diff` - Goal differential rolling (3/5/10 windows) ⭐ #10, #17
- `rolling_gsax_X_diff` - Team GSAx rolling differentials (3/5/10 windows)
- `rolling_high_danger_shots_X_diff` - High-danger shot rolling differentials ⭐ #1, #42, #45
- `rolling_save_pct_X_diff` - Team save % rolling differentials (3/5/10 windows)
- `rolling_win_pct_X_diff` - Win % rolling differentials (3/5/10 windows)
- `rolling_xg_against_X_diff` - xG against rolling differentials (3/5/10 windows)
- `rolling_xg_diff_X_diff` - xG differential rolling (3/5/10 windows)
- `rolling_xg_for_X_diff` - xG for rolling differentials (3/5/10 windows) ⭐ #20, #25

### S
- `season_goal_diff_avg_diff` - Season goal diff average differential ⭐ #23
- `season_shot_margin_diff` - Season shot margin differential ⭐ #9
- `season_win_pct_diff` - Season win % differential
- `season_xg_diff_avg_diff` - Season xG differential average ⭐ #47
- `seasonPointPct_diff` - Season points % differential ❌ ZERO
- `shot_margin_last_game_diff` - Last game shot margin differential
- `shotsAgainst_roll_X_diff` - Shots against rolling differentials (3/5/10 windows) ⭐ #18, #28
- `shotsFor_roll_X_diff` - Shots for rolling differentials (3/5/10 windows) ⭐ #6, #19
- `specialTeamEdge_diff` - Special teams edge differential ❌ ZERO

### T
- `team_altitude_ft_away` - Away team altitude
- `team_altitude_ft_home` - Home team altitude
- `team_injury_count_diff` - Injury count differential
- `travel_burden_away` - Away team travel burden
- `travel_burden_home` - Home team travel burden ⭐ #32

---

## 📈 FEATURE IMPORTANCE INSIGHTS

### What Drives Predictions?

**Top 3 Feature Types:**
1. **Schedule/Rest (23 features, 6 in top 20)** - Fatigue matters!
2. **Shot Quality (9 features, 3 in top 20)** - Quality > quantity
3. **Goalie Performance (14 features, 2 in top 20)** - Goaltending critical

### Rolling Window Performance

**Best Windows:**
- **3 games:** Best for recent form, hot/cold streaks
- **5 games:** Balanced view
- **10 games:** Good for stability, but often redundant

**Insight:** Shorter windows (3-game) generally outperform longer (10-game)

### Differential vs Absolute

**All top features are differentials** (`_diff` suffix)

**Why?** Model cares about **relative** strength, not absolute
- `rest_days_diff = 2` (home team 2 more rest days) is very predictive
- `rest_days_home = 3` (absolute) is less predictive

### Feature Redundancy

**Highly Correlated Feature Groups:**
- Season aggregates and rolling 10-game windows
- Multiple rest binary flags (b2b, one_day, etc.)
- Special teams % and Net %
- Team save % vs Goalie save %

**Pruning Strategy:** Keep best from each group, remove redundant

---

## 🎯 RECOMMENDED FEATURE SETS

### Minimal (Top 20 Features)
**Use Case:** Maximum speed, embedded systems
**Accuracy:** ~59.5% (slight drop)
**Features:** Top 20 from ranking

### Optimal (Top 50 Features) ⭐ RECOMMENDED
**Use Case:** Best accuracy-to-complexity ratio
**Accuracy:** 60.24% (+0.81pp over full set!)
**Features:** Top 50 from ranking
**Training:** 75% faster than full set

### Standard (Top 100 Features)
**Use Case:** Balanced approach
**Accuracy:** ~59.6%
**Features:** Top 100 from ranking

### Full (All 204 Features)
**Use Case:** Maximum information, no pruning
**Accuracy:** 59.43% (baseline with this test split)
**Features:** All features
**Note:** More features ≠ better performance!

---

## 🔧 FEATURE ENGINEERING BEST PRACTICES

### 1. Always Use Differentials for Game Predictions
```python
# Good
feature = home_metric - away_metric

# Bad (for game prediction)
features = [home_metric, away_metric]  # Let model learn the diff
```

### 2. Lag All Rolling Features
```python
# Good - no future leakage
rolling = series.shift(1).rolling(window).mean()

# Bad - includes current game!
rolling = series.rolling(window).mean()
```

### 3. Group Correlated Features
- Test one from each group
- Remove redundant features
- Keep most important

### 4. Consider Feature Interactions
Current model uses only main effects. Future: interaction terms
```python
# Potential high-value interactions
is_b2b_diff * rest_diff  # Compound rest advantage
goalie_gsa * is_b2b_home  # Tired goalie on B2B
```

### 5. Window Size Matters
- **3 games:** Recent form, streaks
- **5 games:** Balanced
- **10 games:** Stable trends
- **Season:** Long-term strength

**Rule:** Start with 3-game, add longer if uncorrelated

---

## 📚 DATA SOURCES

### NHL Gamecenter API
- Play-by-play data
- Shot locations, types
- Goalie stats
- Schedule information

### GoaliePulse
- Individual goalie season stats
- GSAx calculations
- 500 goalie-season records
- 168 unique goalies

### Engineered In-House
- xG model (custom gradient boosting)
- Elo ratings (margin-adjusted)
- Rolling window calculations
- High-danger zone classification

---

## 🔄 FEATURE UPDATE FREQUENCY

| Feature Type | Update Frequency |
|--------------|------------------|
| Season aggregates | After each game |
| Rolling windows | After each game |
| Elo ratings | After each game |
| Goalie stats | Weekly (from GoaliePulse) |
| Team rosters | Daily |
| Injuries | Daily |
| Rest days | Daily |

---

## 📊 FEATURE STATISTICS

| Statistic | Value |
|-----------|-------|
| Mean feature importance | 0.00238 |
| Median feature importance | 0.00020 |
| Std dev importance | 0.00441 |
| Max importance | 0.03167 (rolling_high_danger_shots_3_diff) |
| Min importance | 0.00000 (44 features) |
| Features in top 10% | 20 features |
| Features in top 25% | 51 features |
| Features in top 50% | 102 features |

**Distribution:** Highly skewed - top 10% of features account for ~40% of total importance!

---

## ✅ QUICK REFERENCE

### Feature Name Patterns

| Pattern | Meaning | Example |
|---------|---------|---------|
| `_diff` | Home - Away differential | `rest_days_diff` |
| `rolling_X_Y` | Rolling window (Y games) | `rolling_xg_for_3` |
| `season_X` | Season-to-date aggregate | `season_goal_diff_avg` |
| `momentum_X` | Last 5 games (short window) | `momentum_win_pct` |
| `goalie_X` | Individual goalie stat | `goalie_rolling_gsa` |
| `is_X` | Binary flag | `is_b2b_home` |
| `home_team_X` | Team one-hot encoding | `home_team_28` |
| `_home` / `_away` | Team-specific value | `rest_days_home` |

### Calculation Shortcuts

**Differential:**
```python
{metric}_diff = {metric}_home - {metric}_away
```

**Rolling (lagged):**
```python
rolling_{metric}_{window} = shift(1).rolling(window).mean()
```

**Season aggregate:**
```python
season_{metric}_avg = mean(all games before current)
```

---

**Last Updated:** November 20, 2025
**Source Code:** `src/nhl_prediction/features.py`
**Analysis:** `analysis/feature_importance_rankings.csv`
**Model Version:** 2.0
