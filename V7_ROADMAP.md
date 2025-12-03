# 🚀 Puckcast V7.0 Roadmap - Pushing Beyond 62% Accuracy

**Current Status (V6.3):**
- Test Accuracy: 59.92% (baseline: 53.74%)
- Log Loss: 0.6761
- ROC-AUC: 0.6350
- A+ Predictions: 68.01% accuracy

**V7.0 Targets:**
- Test Accuracy: **62%+** (+2.1pp improvement)
- Log Loss: **≤0.670** (-0.006 improvement)
- ROC-AUC: **0.650+**
- A+ Predictions: **70%+**

---

## 🎯 High-Impact Improvements (Ordered by Expected Gain)

### 1. Individual Goalie Tracking (Expected: +0.8-1.2%)

**Current State:**
- Team-level goaltending only (team_save_pct, team_gsax_per_60)
- No tracking of which goalie is actually starting

**V7.0 Enhancement:**
- Track individual goalie stats per game
- Key metrics:
  - Individual GSA (Goals Saved Above Expected)
  - Individual save percentage by shot type (high-danger, rush, etc.)
  - Goalie vs specific opponents
  - Recent form (last 3/5/10 starts)
  - Rest days for goalies

**Implementation:**
- Integrate with `data/feeds/starters.json` (already available)
- Build goalie history database from NHL API
- Add features:
  - `starting_goalie_gsa_last_5`
  - `starting_goalie_save_pct_vs_opponent`
  - `starting_goalie_high_danger_save_pct`
  - `goalie_matchup_diff` (starter GSA home - starter GSA away)

**Files to Modify:**
- `src/nhl_prediction/goalie_features.py` - expand from team to individual
- New: `src/nhl_prediction/goalie_tracker.py` - track individual performance
- `src/nhl_prediction/pipeline.py` - integrate goalie matchup features

---

### 2. Feature Pruning & Optimization (Expected: +0.3-0.5%)

**Current State:**
- 204 features, many may have low/zero importance
- Potential overfitting from noise features

**V7.0 Enhancement:**
- Generate feature importance from current model
- Remove features with coefficient < 0.05
- Focus on high-signal features:
  - Goal differential metrics (top in importance)
  - Rolling high-danger shots (proven valuable)
  - xG metrics (custom model advantage)
  - B2B and rest factors (strong signal)
  - Shot quality differentials

**Implementation Steps:**
1. Run feature importance analysis on V6.3 model
2. Identify bottom 20% of features
3. Remove and retrain
4. A/B test: 204 features vs pruned set
5. Keep whichever performs better

**Expected Result:**
- Reduce to ~150-170 high-quality features
- Less overfitting, better generalization
- Improved log-loss through reduced noise

---

### 3. Enhanced Shot Quality Model (Expected: +0.2-0.4%)

**Current xG Model:**
- Features: distance, angle, shot_type, rush, period, zone, rebound
- Accuracy: 94.6% train, 95.3% validation

**V7.0 Enhancements:**

**A. Pre-Shot Movement:**
- Track player speed before shot
- Detect one-timers (pass to immediate shot)
- Skating vs stationary shots

**B. Traffic & Screening:**
- Number of players between shooter and goalie
- Screened shots (defender within 2ft of shot line)
- Deflections and tip-ins

**C. Shot Context:**
- Time since last shot in sequence
- Shot off rush with speed
- Odd-man rush situations (2-on-1, 3-on-2)

**D. Goalie Context:**
- Goalie position (out of net, screened)
- Goalie fatigue (shots faced in period)

**Implementation:**
- Enhance `src/nhl_prediction/native_ingest.py`
- New `ShotFeatures` fields:
  - `has_traffic: bool`
  - `is_one_timer: bool`
  - `odd_man_rush: bool`
  - `goalie_screened: bool`

---

### 4. Advanced Rolling Window Features (Expected: +0.2-0.3%)

**Current State:**
- Basic rolling windows: 3, 5, 10 games
- Features: xG, shots, goals, wins

**Analysis from Feature Importance:**
- `rolling_high_danger_shots_5_diff` is #3 most important (0.291)
- `rolling_goal_diff_10_diff` is #2 most important (0.311)
- `rolling_xg_for_5_diff` is important (0.210)

**V7.0 Enhancements:**

**A. Momentum-Weighted Rolling:**
- Weight recent games more: [0.4, 0.3, 0.2, 0.1] for last 4 games
- Capture hot/cold streaks better
- Formula: `momentum_xg = 0.4*game_1 + 0.3*game_2 + 0.2*game_3 + 0.1*game_4`

**B. Opponent-Adjusted Rolling:**
- Adjust stats by opponent strength
- Weight performance vs strong teams higher
- `rolling_xg_vs_top10_teams`

**C. Additional Rolling Metrics:**
- `rolling_rush_goal_pct_5` - rush shot success rate
- `rolling_high_danger_conversion_5` - finishing ability
- `rolling_takeaway_diff_5` - possession trend
- `rolling_save_pct_high_danger_5` - goalie quality trend

**Implementation:**
- `src/nhl_prediction/pipeline.py` - add momentum weighting function
- Add opponent strength database for adjustments

---

### 5. Probability Calibration Refinement (Expected: Log Loss -0.005 to -0.010)

**Current State:**
- Isotonic calibration on validation set
- Log loss: 0.6761 (target: ≤0.670)

**V7.0 Enhancements:**

**A. Temperature Scaling:**
- Learn optimal temperature parameter
- Better calibrate extreme probabilities
- Especially helpful for A+ predictions

**B. Beta Calibration:**
- More flexible than isotonic
- Better for edges of probability distribution
- Params: a, b, c for sigmoid transformation

**C. Multi-Level Calibration:**
- Separate calibration for different confidence levels
- High-confidence (>60%) vs low-confidence (<55%)
- Different calibration curves for each

**D. Platt Scaling:**
- Logistic regression on top of predictions
- Simple, effective for log-loss

**Implementation:**
- New: `src/nhl_prediction/calibration.py`
- Test all methods, keep best
- Focus on reducing log-loss while maintaining accuracy

---

### 6. Injury Impact Features (Expected: +0.1-0.2%)

**Current State:**
- `data/feeds/injuries.json` exists but not integrated

**V7.0 Enhancement:**
- Track key player injuries
- Focus on high-impact players:
  - Top-line forwards (1st line)
  - Top-pair defensemen (1st pair)
  - Starting goalies

**Key Features:**
- `top_scorer_out_home/away` (binary)
- `top_defenseman_out_home/away` (binary)
- `games_without_key_player` (count)
- `injury_impact_score` (weighted by player importance)

**Implementation:**
- Parse `data/feeds/injuries.json`
- Map players to lines/importance
- Add binary flags for key absences

---

### 7. Special Teams Matchup Refinement (Expected: +0.1-0.15%)

**Current Features:**
- Basic PP% and PK% differentials exist
- Not heavily weighted in current model

**V7.0 Enhancement:**
- Focus on recent special teams performance (last 10 games)
- Goalie-specific PK performance
- PP shooting talent vs PK goalie quality
- 5v3 and 4v4 situations

**New Features:**
- `pp_xg_for_last_10` - power play expected goals
- `pk_xg_against_last_10` - penalty kill expected goals against
- `special_teams_goalie_adjusted` - PP vs starting goalie PK%

---

## 📊 Feature Count Evolution

**V6.3 (Current):** 204 features
```
Base stats: ~60
Rolling windows (3/5/10): ~90
Differentials: ~40
Schedule/rest: ~10
Team embeddings: ~4
```

**V7.0 (Planned):** ~185 features (pruned, focused)
```
Base stats: ~50 (pruned low-importance)
Rolling windows (enhanced): ~70
Momentum-weighted rolling: ~20
Individual goalie: ~15
Advanced xG: ~10
Injury flags: ~8
Special teams: ~8
Team embeddings: ~4
```

---

## 🛠 Implementation Plan

### Phase 1: Analysis & Foundation (Week 1)
- [ ] Generate feature importance from V6.3 model
- [ ] Identify features to prune (bottom 20%)
- [ ] Design individual goalie tracking system
- [ ] Set up goalie history database structure

### Phase 2: Core Enhancements (Week 2)
- [ ] Implement individual goalie tracking
- [ ] Build goalie features (GSA, save%, vs opponents)
- [ ] Integrate with starting goalie data
- [ ] Test goalie features in isolation (+0.8-1.2% expected)

### Phase 3: Feature Engineering (Week 3)
- [ ] Implement momentum-weighted rolling windows
- [ ] Add opponent-adjusted metrics
- [ ] Enhance xG model with traffic/screening
- [ ] Add pre-shot movement detection

### Phase 4: Calibration & Refinement (Week 4)
- [ ] Implement temperature scaling
- [ ] Test beta calibration
- [ ] Multi-level calibration for different confidence ranges
- [ ] Optimize for log-loss reduction

### Phase 5: Integration & Testing (Week 5)
- [ ] Integrate injury impact features
- [ ] Refine special teams matchups
- [ ] Feature pruning and optimization
- [ ] Full model retraining

### Phase 6: Validation & Deployment (Week 6)
- [ ] Comprehensive evaluation on 2023-24 test set
- [ ] Verify >62% accuracy, ≤0.670 log-loss
- [ ] A/B test against V6.3
- [ ] Update documentation and deploy

---

## 📈 Expected Results

### Conservative Estimate:
```
Individual Goalie Tracking:  +0.8%   → 60.72%
Feature Pruning:             +0.3%   → 61.02%
Enhanced xG:                 +0.2%   → 61.22%
Rolling Window Refinement:   +0.2%   → 61.42%
Calibration:                 +0.1%   → 61.52%
Injury Features:             +0.1%   → 61.62%
Special Teams:               +0.1%   → 61.72%

Final: 61.7% accuracy, ~0.670 log-loss
```

### Optimistic Estimate:
```
Individual Goalie Tracking:  +1.2%   → 61.12%
Feature Pruning:             +0.5%   → 61.62%
Enhanced xG:                 +0.4%   → 62.02%
Rolling Window Refinement:   +0.3%   → 62.32%
Calibration:                 +0.2%   → 62.52%
Injury Features:             +0.2%   → 62.72%
Special Teams:               +0.15%  → 62.87%

Final: 62.9% accuracy, ~0.665 log-loss
```

### Realistic Target:
```
V7.0 Target: 62.0-62.5% accuracy
             0.665-0.670 log-loss
             0.655+ ROC-AUC
             70%+ A+ prediction accuracy
```

---

## 🎯 Success Criteria

**Must Have (V7.0 Release):**
- ✅ Individual goalie tracking implemented
- ✅ Test accuracy ≥ 62.0%
- ✅ Log loss ≤ 0.670
- ✅ Feature count optimized (<190)
- ✅ Enhanced xG model deployed

**Nice to Have:**
- ⭐ Injury integration complete
- ⭐ Momentum-weighted rolling implemented
- ⭐ Multi-level calibration active
- ⭐ A+ predictions at 70%+

**Stretch Goals:**
- 🚀 62.5%+ accuracy
- 🚀 0.665 log-loss
- 🚀 Ensemble model with multiple approaches

---

## 🔄 Risk Mitigation

**Risk:** Feature additions don't improve performance
- **Mitigation:** A/B test each feature group in isolation
- **Fallback:** Revert to V6.3 baseline

**Risk:** Overfitting with new features
- **Mitigation:** Strong validation framework, multiple test seasons
- **Fallback:** Increase regularization (lower C parameter)

**Risk:** Individual goalie data incomplete
- **Mitigation:** Build comprehensive goalie database first
- **Fallback:** Use team goaltending as before

**Risk:** Calibration worsens accuracy
- **Mitigation:** Optimize calibration separately from core model
- **Fallback:** Use isotonic calibration from V6.3

---

## 📁 New Files to Create

```
src/nhl_prediction/
  ├── goalie_tracker.py        # Individual goalie performance tracking
  ├── calibration.py            # Advanced calibration methods
  ├── momentum_features.py      # Momentum-weighted rolling windows
  └── injury_parser.py          # Parse and integrate injury data

data/
  ├── goalie_history/           # Individual goalie stats by game
  └── player_importance/        # Player impact ratings

analysis/
  └── v7_feature_importance.py  # V7.0 feature analysis

reports/
  └── v7_evaluation/            # V7.0 comprehensive results
```

---

## 💡 Key Insights for V7.0

1. **Goalie Tracking is Critical**
   - Currently missing #5 most important feature (per user's analysis)
   - Goaltending = 30-40% of game outcome
   - Biggest single improvement opportunity

2. **Less Can Be More**
   - Pruning weak features often improves generalization
   - Focus on high-signal, low-noise features
   - Reduces overfitting risk

3. **Rolling Windows Are Gold**
   - Top features in importance analysis
   - Capture recent form effectively
   - Enhanced weighting can squeeze out more signal

4. **Calibration Matters for Log-Loss**
   - Current 0.6761, target ≤0.670
   - Calibration won't hurt accuracy but will improve log-loss
   - Critical for probabilistic betting applications

5. **Iterative Testing is Essential**
   - Don't add all features at once
   - Test each improvement in isolation
   - Build confidence in each enhancement

---

## 🚀 Next Actions

**This Week:**
1. Generate V6.3 feature importance analysis
2. Design individual goalie tracking database schema
3. Prototype goalie feature extraction from NHL API
4. Identify bottom 20% features for pruning

**Priority Order:**
1. Individual goalie tracking (highest impact)
2. Feature pruning (quick win)
3. Enhanced rolling windows (proven value)
4. Calibration refinement (log-loss focus)
5. Advanced xG improvements (incremental)
6. Injury integration (nice-to-have)

---

**Let's push to 62%+ accuracy! 🏒🔥**
