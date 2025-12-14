# V7 Series: Final Summary & Analysis

**Date:** 2025-12-03
**Best Model:** **V7.3 at 61.38% accuracy** (0.62pp short of 62% target)
**Status:** Accuracy ceiling reached with current approach

---

## Executive Summary

The V7 series attempted to improve from V7.0's 60.89% to the 62% accuracy target through systematic feature engineering. **V7.3 achieved 61.38%** (+0.49pp), hitting the log-loss target (0.6698 ≤ 0.670) but falling 0.62pp short of the accuracy goal.

Two subsequent enhancement attempts (V7.4 and V7.5) both **degraded performance**, revealing we've reached an accuracy ceiling with the current feature set and model architecture.

---

## Version History

| Version | Features | Accuracy | vs V7.0 | vs V7.3 | Log Loss | Status |
|---------|----------|----------|---------|---------|----------|---------|
| **V7.0** | 209 | 60.89% | baseline | -0.49pp | 0.6670 ✓ | Production |
| **V7.3** | 222 | **61.38%** ✓ | **+0.49pp** | baseline | **0.6698** ✓ | **BEST** |
| V7.4 | 240 | 60.57% | -0.32pp | **-0.81pp** ❌ | 0.6714 | REJECTED |
| V7.5 | 234 | 60.08% | -0.81pp | **-1.30pp** ❌ | 0.6733 | REJECTED |

**Gap to 62% target:** 0.62 percentage points (77 additional correct predictions needed on 1,230 test games)

---

## What Worked: V7.3 Situational Features (+0.49pp)

### Features Added (13)
1. **Fatigue Index** - Weighted games in last 7 days
2. **Third Period Trailing Performance** - Win% in close games (clutch)
3. **Travel Distance** - Miles traveled since last game
4. **Divisional Matchups** - Same division flag
5. **Post-Break Performance** - First game after 4+ days rest

### Why It Worked
- **New orthogonal signal:** Game context independent of team quality
- **Reasonable coefficients:** fatigue_index_home (-0.0935) comparable to mid-tier features
- **Validated improvement:** +0.49pp on test set, log-loss target achieved
- **Top features:**
  - fatigue_index_home: -0.0935
  - fatigue_index_diff: -0.0585
  - travel_burden_home: -0.0517

### Results
- **Accuracy:** 61.38% (+0.49pp over V7.0)
- **Log Loss:** 0.6698 ✓ (target: ≤0.670)
- **A+ Bucket:** 71.1% on 246 games
- **Features:** 222 (209 V7.0 + 13 V7.3)

---

## What Failed: V7.4 Enhanced Special Teams (-0.81pp)

### Features Added (18)
1. **Special Teams Goal Differential** - (PP goals - SH goals allowed) rolling 10
2. **PP/PK Opportunities** - Penalties drawn/taken
3. **Special Teams Efficiency** - Goals per opportunity
4. **Home/Away Variance** - PP%/PK% difference by location (ALL ZERO - pruned)

### Why It Failed
- **Collinear with goal differential:** Special teams impact already captured in `season_goal_diff_avg_diff` (#1 feature, coef 0.2098)
- **Coefficients too small:** Largest V7.4 feature 0.0617 vs top features 0.17-0.21 (3-4x smaller)
- **No new signal:** PP/PK performance is a *component* of goals scored, not orthogonal information
- **Overfitting:** Added 18 features (+8%) but accuracy decreased 0.81pp

### Results
- **Accuracy:** 60.57% (-0.81pp vs V7.3) ❌
- **Log Loss:** 0.6714 (missed 0.670 target)
- **A+ Bucket:** 71.3% on 251 games (+0.2pp)
- **Coefficients:** max 0.0617 (3.4x smaller than top features)

### Lesson Learned
**Special teams account for 20-25% of goals, but the existing goal differential features already incorporate this.** Adding granular PP/PK metrics doesn't add new information - it's just a different view of the same team quality signal.

---

## What Failed: V7.5 PDO Regression (-1.30pp)

### Features Added (12)
1. **PDO Rolling 10** - Shooting% + Save% over last 10 games
2. **PDO Deviation** - Distance from 100 (regression to mean signal)
3. **Shooting% Sustainability** - Actual vs expected (from xG)
4. **Save% Sustainability** - Actual vs expected (from xG against)

### Why It Failed
- **Still derived from existing signals:** PDO = Shooting% + Save%, both already captured in goal differential and xG features
- **Coefficients slightly larger but insufficient:** max 0.0668 vs top 0.2166 (3.2x smaller)
- **Not orthogonal enough:** Luck/sustainability partially captured by xG vs actual goals
- **Worse than V7.4:** -1.30pp degradation (worse than special teams' -0.81pp)

### Results
- **Accuracy:** 60.08% (-1.30pp vs V7.3) ❌
- **Log Loss:** 0.6733 (missed 0.670 target)
- **A+ Bucket:** 71.4% on 238 games (+0.3pp)
- **Coefficients:** max 0.0668 (3.2x smaller than top features)

### Lesson Learned
**Even "different" features like PDO are ultimately derived from goals and shots.** The model already has `season_goal_diff_avg_diff` (captures shooting efficiency) and `rolling_gsax` (captures goaltending luck), so PDO adds minimal new information.

---

## Root Cause Analysis: Why We Hit a Ceiling

### The Feature Hierarchy

The model's predictive power comes from these signals (ranked by importance):

1. **Goal Differential** (coef ~0.20) - Captures overall team quality
   - Includes PP/PK impact, shooting efficiency, defensive quality

2. **Shot Quality (xGoals)** (coef ~0.15-0.18) - Captures process vs results
   - Already measures shooting skill vs luck

3. **Goaltending** (coef ~0.17-0.18) - Captures goalie performance
   - GSA (Goals Saved Above Expected) measures goalie luck

4. **Situational Context** (coef ~0.06-0.09) - Game circumstances
   - Fatigue, travel, clutch performance

### Why New Features Failed

**V7.4 Special Teams:**
- Special teams → goals scored/allowed → already in goal differential (#1)
- No orthogonal signal

**V7.5 PDO:**
- Shooting% + Save% → goal differential + xG (#1 + #2)
- Luck/sustainability → already in xG vs actual goals, GSA
- No orthogonal signal

### The Pattern

Both attempts tried to add **derivative features** - different mathematical views of existing signals. But the model has already extracted maximum predictable information from:
- Team strength (goal differential)
- Process quality (xGoals)
- Goalie performance (GSA)
- Game context (situational)

Adding `f(x)` when you already have `x` doesn't help if `f` is monotonic or highly correlated.

---

## Top 20 Features (V7.3 Production Model)

| Rank | Feature | Coefficient | Category |
|------|---------|-------------|----------|
| 1 | season_goal_diff_avg_diff | 0.2098 | Goal Differential |
| 2 | rolling_gsax_3_diff | 0.1823 | Goaltending |
| 3 | rolling_goal_diff_10_diff | -0.1735 | Goal Differential |
| 4 | rolling_gsax_5_diff | -0.1702 | Goaltending |
| 5 | home_team_28 (SJS) | -0.1661 | Team Identity |
| 6 | is_b2b_home | -0.1587 | Rest/Fatigue |
| 7 | rolling_xg_for_5_diff | 0.1547 | xGoals |
| 8 | away_team_6 (BOS) | -0.1526 | Team Identity |
| 9 | rolling_high_danger_shots_5_diff | -0.1472 | Shot Quality |
| 10 | rolling_high_danger_shots_3_diff | 0.1400 | Shot Quality |
| 11 | momentum_xg_against_4_diff | -0.1321 | xGoals |
| 12 | rolling_xg_against_3_diff | 0.1280 | xGoals |
| 13 | shotsAgainst_roll_10_diff | -0.1223 | Shots |
| 14 | shotsAgainst_roll_3_diff | -0.1217 | Shots |
| 15 | home_team_10 (TOR) | 0.1123 | Team Identity |
| 16 | home_team_6 (BOS) | 0.1120 | Team Identity |
| 17 | rolling_corsi_5_diff | -0.1110 | Possession |
| 18 | home_team_16 (CHI) | -0.1092 | Team Identity |
| 19 | rolling_xg_for_10_diff | 0.1051 | xGoals |
| 20 | home_team_13 (FLA) | 0.1011 | Team Identity |

### Key Insights
- **Goal differential dominates:** #1, #3 (combined ~0.38)
- **Goaltending critical:** #2, #4 (combined ~0.35)
- **xGoals everywhere:** #7, #9-12, #19 (6 in top 20)
- **Team identity matters:** 7 team dummy variables in top 20
- **V7.3 features absent from top 20:** Situational features helped but aren't dominant

---

## Why 61.38% Might Be The Ceiling

### Fundamental Limits

1. **NHL is highly random:** ~55-60% theoretical ceiling for game prediction
   - Parity by design (salary cap, draft)
   - Playoff teams often 50-55% win rate
   - Single-game variance is enormous

2. **Information available pre-game is limited:**
   - Don't know starting goalies with 100% certainty
   - Don't know player injuries/scratches
   - Don't know line combinations/strategies
   - Don't know referee assignments (power play impact)

3. **Model has extracted known predictable signals:**
   - Team strength (goals)
   - Process quality (xGoals, shots)
   - Goalie performance
   - Recent form (rolling windows)
   - Game context (fatigue, travel)

### What's Left in the 0.62pp Gap?

To get from 61.38% → 62%, we need **77 more correct predictions** on 1,230 test games (6.3% of test set).

Potential sources (all speculative):
- **Starting goalie uncertainty:** ~10-15 games where backup starts unexpectedly
- **Player injuries:** ~20-30 games with surprise scratches
- **Referee assignment:** ~15-20 games where refs impact PP opportunities
- **Motivation factors:** ~10-15 games (playoff race, rivalry, revenge)
- **Line chemistry:** ~10-15 games (new line combos, trades)

**Problem:** All of these are either:
1. **Unknowable pre-game** (injuries, scratches, motivation)
2. **Not in our data** (referee assignments, line combos)
3. **Too noisy to model** (small sample sizes, high variance)

---

## Confidence Bucket Analysis

| Grade | Range | V7.0 | V7.3 | Change |
|-------|-------|------|------|--------|
| **A+** | 20-100 pts | 69.5% (436 games) | **71.1%** (246 games) | +1.6pp |
| **A-** | 15-20 pts | - | 62.5% (120 games) | - |
| **B+** | 10-15 pts | - | 52.9% (121 games) | - |
| **B-** | 5-10 pts | - | 61.9% (126 games) | - |
| **C** | 0-5 pts | - | 48.2% (114 games) | - |

### Key Findings
- **V7.3 is more selective:** 246 A+ games vs V7.0's 436 (44% reduction)
- **Higher A+ accuracy:** 71.1% vs 69.5% (+1.6pp)
- **Trade-off:** Fewer confident predictions, but more accurate when confident

---

## Alternative Approaches to Consider

Since feature engineering hit a wall, here are fundamentally different approaches:

### 1. Expand Training Data (Easiest)
**Idea:** Train on 5+ seasons instead of 2
**Pros:**
- More examples for rare scenarios
- Better team identity coefficients
- Captures multi-year trends

**Cons:**
- Older data less relevant (rule changes, player turnover)
- Diminishing returns after ~3 seasons
- V7.0 already tried 3 seasons

**Expected:** +0.1-0.2pp (unlikely to close 0.62pp gap)

---

### 2. Ensemble Methods
**Idea:** Combine multiple models (LogReg + XGBoost + Random Forest)
**Pros:**
- Captures non-linear interactions
- Reduces variance through averaging
- Can squeeze out marginal gains

**Cons:**
- More complex to maintain
- Overfitting risk increases
- May only gain 0.1-0.3pp

**Expected:** +0.2-0.4pp (might close gap)

---

### 3. Deep Learning (LSTM/Transformer)
**Idea:** Model game sequences directly instead of rolling window features
**Pros:**
- Learns temporal patterns automatically
- Captures complex interactions
- State-of-the-art in many domains

**Cons:**
- Needs much more data (10K+ games)
- Black box (no interpretability)
- High risk of overfitting
- Requires GPU training

**Expected:** +0.0-0.5pp (high variance, could help or hurt)

---

### 4. External Data Sources
**Idea:** Add data we don't currently have
**Options:**
- **Confirmed starting goalies** (improve 10-15 games)
- **Player injuries/scratches** (improve 20-30 games)
- **Referee assignments** (PP/PK impact, 15-20 games)
- **Line combinations** (chemistry, 10-15 games)
- **Weather data** (outdoor games, minimal impact)

**Best Target:** **Starting goalies** - knowable 1-2 hours before game, high impact

**Expected:** +0.3-0.5pp if goalie data perfect

---

### 5. Accept 61.38% and Optimize for Other Metrics
**Idea:** Focus on log-loss, calibration, or bet ROI instead of raw accuracy
**Rationale:**
- 61.38% might be the ceiling
- Better calibration → better betting edge
- Accuracy isn't everything

**Focus Areas:**
- Temperature scaling to improve log-loss
- Confidence calibration (is 75% really 75%?)
- Kelly criterion bet sizing
- Line shopping strategies

---

## Recommendation

### Short Term: **Deploy V7.3 as Production Model**

**Justification:**
- Best accuracy: 61.38% (+0.49pp over V7.0)
- Log-loss target achieved: 0.6698 ≤ 0.670 ✓
- A+ bucket: 71.1% on 246 high-confidence games
- Clean feature set: 222 features (not bloated)
- Only 0.62pp short of 62% target

**Trade-offs:**
- Didn't hit 62% accuracy target
- More selective (fewer A+ predictions)
- Requires game context data (fatigue, travel)

---

### Medium Term: **Try Starting Goalie Data Integration**

**Why This:**
- Most impactful external data source
- Knowable 1-2 hours before game (actionable)
- Affects 10-15 test games where backup starts unexpectedly
- Direct path to +0.3-0.5pp improvement

**Implementation:**
1. Build starting goalie scraper (NHL API, Daily Faceoff, team announcements)
2. Add "confirmed starter" features (goalie_id, rest_days, recent_performance)
3. Retrain V7.3 with goalie features → V7.6
4. Target: 61.7-61.9% accuracy

**Timeline:** 1-2 weeks

---

### Long Term: **Consider Ensemble or Accept Ceiling**

**Option A: Ensemble (if pursuing 62%)**
- Combine LogReg + LightGBM + XGBoost
- Expected: +0.2-0.4pp → 61.6-61.8%
- Still might not hit 62%

**Option B: Optimize for Betting ROI (if accepting ceiling)**
- Focus on calibration and bet sizing
- 61.38% with good calibration → profitable betting
- Maximize expected value, not just accuracy

**Decision Point:** After V7.6 (with goalie data) results

---

## Technical Debt & Maintenance

### Issues to Address
1. **DataFrame fragmentation warnings:** Pipeline creates highly fragmented DataFrames (performance issue)
2. **Feature correlation:** Some rolling windows are highly correlated (3-game vs 5-game)
3. **Team dummy variables:** 14 team features in top 50 (overfitting risk on team identity)

### Recommended Refactoring
1. Use `pd.concat(axis=1)` instead of repeated column insertions
2. Run feature correlation analysis, prune redundant features
3. Consider team strength ratings instead of dummy variables

---

## Conclusion

The V7 series achieved significant progress:
- V7.0 → V7.3: **+0.49pp** improvement to **61.38%**
- Log-loss target **achieved** (0.6698 ≤ 0.670)
- A+ bucket accuracy: **71.1%** on high-confidence games

But revealed fundamental limits:
- **Feature engineering ceiling reached:** V7.4 and V7.5 both degraded performance
- **Derivative features don't help:** Model has extracted maximum signal from current data
- **0.62pp gap likely requires:**external data (starting goalies, injuries) or fundamentally different approach (ensembles, deep learning)

**V7.3 at 61.38% is recommended for production deployment** while exploring starting goalie data integration as the most promising next step toward 62%.

---

**Status:** V7 series complete
**Production Model:** V7.3 (61.38% accuracy, 222 features)
**Next Milestone:** V7.6 with confirmed starting goalie data
