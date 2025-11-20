# Roadmap to Hockey Prediction Excellence

## 📍 WHERE WE ARE NOW

### Current Status (Post-Overhaul)
**Model Architecture:**
- 141 engineered features
- 6 seasons training data (2017-2023)
- Sample weighting (0.85 decay)
- Full 2023-24 test set

**Expected Baseline Performance:**
- Test Accuracy: ~59% (vs 53% random)
- ROC-AUC: ~0.62
- Brier Score: ~0.24

**What We Have:**
✅ Custom xG model (94.8% accuracy)
✅ All advanced metrics (Corsi, Fenwick, GSAx)
✅ 2x more training data
✅ Sample weighting system
✅ Robust feature engineering pipeline

**What We DON'T Have Yet:**
❌ Actual performance metrics with new config
❌ Feature importance analysis
❌ Player-level features
❌ Lineup quality metrics
❌ Goalie-specific context (who's starting)
❌ Injury/roster tracking
❌ Advanced xG features (rebounds, screens, rush shots)

---

## 🎯 THE PLAN: Road to 65%+ Accuracy

### PHASE 1: Measure & Optimize (Week 1)
**Goal: Establish baseline and quick wins**

#### Step 1: Train & Benchmark Current System
```bash
python -m src.nhl_prediction.train
```

**Collect:**
- Test accuracy on 2023-24
- ROC-AUC, log loss, Brier score
- Feature importance rankings
- Where predictions fail most

**Expected gain:** Baseline measurement + 0-2% from more data

#### Step 2: Feature Importance Analysis
```python
# Identify top 20 most important features
# Drop bottom 20% least important features
# Retrain and measure impact
```

**Expected gain:** +0.5-1% from noise reduction

#### Step 3: Tune Decay Factor
Try different sample weights:
- 0.80 (more aggressive recency)
- 0.85 (current)
- 0.90 (gentler)
- 0.95 (minimal)

**Expected gain:** +0.3-0.8% from optimal weighting

**Phase 1 Target: 60-61% accuracy**

---

### PHASE 2: Enhanced xG Model (Week 2-3)
**Goal: Improve shot quality prediction**

#### Upgrade 1: More Training Data
- Use full 2021-22 season (~1,200 games)
- ~300K shots instead of 23K
- Train on multiple seasons

**Expected gain:** +5% xG accuracy → better derived features

#### Upgrade 2: Advanced Shot Features
Add to xG model:
- **Rebound flag**: Was previous event a save? (2-3x goal probability)
- **Rush shot**: Shot within 5 seconds of zone entry
- **Traffic**: Defenders between shooter and goalie
- **Deflection/Tip**: Different shot trajectory
- **Empty net**: Goalie pulled (100% xG)
- **Shot sequence**: 2nd/3rd shot in quick succession

**Expected gain:** +1-2% overall accuracy (better xG → better features)

#### Upgrade 3: Situation-Specific xG
Separate models for:
- 5v5 (even strength)
- Power play (5v4, 5v3)
- Shorthanded (4v5)

**Expected gain:** +0.5-1% from situational accuracy

**Phase 2 Target: 61-63% accuracy**

---

### PHASE 3: Goaltending Context (Week 4)
**Goal: Know who's in net before game starts**

#### Feature Set: Day-of Goalie Context
Already partially implemented! Need to expand:

**Current (from your codebase):**
- `data/feeds/starters.json` - Day-of starting goalies
- `data/feeds/injuries.json` - Player injury status

**Enhance with:**
```python
# For each game, add:
- starting_goalie_save_pct (season-to-date)
- starting_goalie_gsax_per_60
- starting_goalie_recent_form (last 5 games)
- backup_goalie_flag (is backup playing?)
- goalie_rest_days (days since last start)
- goalie_vs_opponent_history (career vs this team)
```

**Expected gain:** +1-2% (goalie quality is HUGE)

**Phase 3 Target: 62-65% accuracy**

---

### PHASE 4: Roster & Lineup Quality (Week 5-6)
**Goal: Account for who's playing**

#### Feature Set: Injury Impact
```python
# From injuries.json:
- num_injuries_forwards
- num_injuries_defense
- num_injuries_top_line (top 6 forwards)
- num_injuries_top_pair (top 4 defense)
- total_cap_hit_injured ($ value of injured players)
```

#### Feature Set: Lineup Quality
```python
# Aggregate player stats:
- top_6_forwards_pts_per_game
- top_4_defense_rating
- power_play_unit_quality
- penalty_kill_unit_quality
- team_avg_age (fatigue factor)
- team_travel_distance (back-to-backs, road trips)
```

**Expected gain:** +1-2% from roster context

**Phase 4 Target: 63-67% accuracy**

---

### PHASE 5: Advanced Features (Week 7-8)
**Goal: Capture subtle patterns**

#### Feature Set: Momentum & Streaks
```python
# Current form beyond rolling averages:
- win_streak (consecutive wins)
- losing_streak (consecutive losses)
- home_win_streak / road_win_streak
- points_last_10_games
- goal_differential_last_5
- comeback_wins (resilience metric)
```

#### Feature Set: Matchup History
```python
# Head-to-head:
- h2h_wins_last_3_seasons
- h2h_avg_goals_for
- h2h_avg_goals_against
- division_rival_flag (extra intensity)
- playoff_position_battle (late season importance)
```

#### Feature Set: Schedule & Fatigue
```python
# Rest & travel:
- days_rest (0 = back-to-back, 1 = normal, 2+ = rested)
- opponent_days_rest
- rest_advantage (home_rest - away_rest)
- miles_traveled_last_7_days
- timezone_changes
- home_stand_game_number (1st, 2nd, 3rd of homestand)
```

**Expected gain:** +1-2% from contextual awareness

**Phase 5 Target: 64-69% accuracy**

---

### PHASE 6: Ensemble & Meta-Learning (Week 9-10)
**Goal: Combine multiple models**

#### Strategy 1: Model Stacking
```python
# Train multiple models:
- Logistic Regression (baseline)
- Histogram Gradient Boosting (current best)
- Random Forest
- XGBoost
- Neural Network (MLP)

# Stack predictions:
meta_model = LogisticRegression()
meta_model.fit(stacked_predictions, true_labels)
```

**Expected gain:** +0.5-1.5% from ensemble diversity

#### Strategy 2: Situation-Specific Models
```python
# Separate models for:
- Even matchups (close in standings)
- Mismatches (big difference)
- Playoff teams vs non-playoff
- Early season vs late season
- Division games vs conference games
```

**Expected gain:** +0.5-1% from specialization

**Phase 6 Target: 65-70% accuracy**

---

## 🚀 QUICK WINS (Do First!)

### 1. Train Current System & Get Baseline
**Time: 5 minutes**
```bash
python -m src.nhl_prediction.train > results_baseline.txt
```

This tells us:
- Current accuracy with 6 seasons + sample weights
- Which features matter most
- Where we're already at

### 2. Add Starting Goalie Features
**Time: 2-3 hours**

You already have `data/feeds/starters.json`! Just need to:
- Parse it in `features.py`
- Join goalie stats by goalie ID
- Add features: save%, GSAx, recent form

**Likely gain: +1-2% accuracy** (huge bang for buck!)

### 3. Improve xG with Rebounds
**Time: 2-3 hours**

Add one feature to xG model:
```python
# In native_ingest.py:
is_rebound = (
    prev_event_type == "shot-on-goal" and
    time_since_prev < 3  # seconds
)
```

Rebounds have 2-3x higher goal probability.

**Likely gain: +0.5-1% accuracy**

### 4. Tune Decay Factor
**Time: 30 minutes**

Try: `decay_factor=0.80` (prioritize recent seasons more)

**Likely gain: +0.3-0.8% accuracy**

---

## 📊 FEATURE PRIORITY MATRIX

| Feature Category | Implementation Time | Expected Gain | Priority |
|-----------------|---------------------|---------------|----------|
| **Starting Goalies** | 2-3 hours | +1-2% | 🔥 CRITICAL |
| **Rebound Detection** | 2-3 hours | +0.5-1% | 🔥 HIGH |
| **Tune Decay Factor** | 30 min | +0.3-0.8% | 🔥 HIGH |
| **Feature Selection** | 1 hour | +0.5-1% | ⭐ MEDIUM |
| **Injury Tracking** | 4-6 hours | +1-2% | ⭐ MEDIUM |
| **Full xG Training** | 2 hours | +0.5-1% | ⭐ MEDIUM |
| **Momentum Features** | 3-4 hours | +0.5-1% | ⭐ MEDIUM |
| **Rest/Schedule** | 4-6 hours | +0.5-1.5% | 💡 LOW |
| **H2H History** | 3-4 hours | +0.3-0.8% | 💡 LOW |
| **Ensemble Models** | 8-10 hours | +0.5-1.5% | 💡 FUTURE |

---

## 🎯 REALISTIC ACCURACY TARGETS

**Current (estimated): 59-60%**
- Baseline with more data

**After Quick Wins (1 week): 61-62%**
- Starting goalies
- Rebound detection
- Tuned decay

**After xG Improvements (2-3 weeks): 62-63%**
- Better xG model
- More training data
- Advanced shot features

**After Roster Context (4-6 weeks): 64-66%**
- Injury tracking
- Lineup quality
- Goalie context

**After Advanced Features (8-10 weeks): 65-68%**
- Momentum
- Schedule
- Matchup history

**After Ensemble (12 weeks): 66-70%**
- Multiple models
- Situation-specific predictors
- Meta-learning

---

## 💪 MY RECOMMENDATION: Start Here

### This Week
1. **Train current model** - Get baseline (5 min)
2. **Add starting goalie features** - Biggest bang for buck (3 hours)
3. **Add rebound detection to xG** - Easy, high impact (2 hours)
4. **Tune decay factor** - Quick optimization (30 min)

**Expected: 61-63% accuracy by end of week**

### Next Week
5. **Train xG on full season** - Better foundation (2 hours)
6. **Add injury tracking** - Roster context (6 hours)
7. **Feature importance analysis** - Clean up noise (2 hours)

**Expected: 63-65% accuracy by week 2**

### Week 3-4
8. **Advanced xG features** - Rush shots, traffic, etc. (8 hours)
9. **Momentum features** - Streaks, recent form (4 hours)
10. **Schedule features** - Rest, travel, B2B (6 hours)

**Expected: 65-67% accuracy by week 4**

---

## 🔥 THE PATH TO 70%+

Getting above 70% requires:
- Everything above ✅
- Player-level models (individual effects)
- Line combination tracking
- Real-time betting market data
- Weather for outdoor/cold arenas
- Referee tendencies (penalty calling)
- Advanced stats (zone entries/exits, transition play)

This is **professional sports betting territory**. 65-68% is excellent for a personal project!

---

## 📈 HOW TO TRACK PROGRESS

Create a results log:
```python
# results_tracker.py
results = {
    "baseline": {"accuracy": 0.59, "roc_auc": 0.62, "log_loss": 0.68},
    "v1_goalies": {"accuracy": 0.61, "roc_auc": 0.64, "log_loss": 0.66},
    "v2_rebounds": {"accuracy": 0.62, "roc_auc": 0.65, "log_loss": 0.65},
    # ... track every change
}
```

Always test on same holdout (2023-24 season) for fair comparison.

---

## 🎓 KEY INSIGHTS

**What Matters Most:**
1. **Goaltending** - Who's in net is 30-40% of the game
2. **Recent Form** - Last 10 games >> season average
3. **Injuries** - Missing top players swings odds 5-10%
4. **Shot Quality** - xG > raw shot counts
5. **Rest** - Back-to-backs matter a lot

**What Matters Less:**
- Historical head-to-head (small sample)
- Division rivalry (media hype)
- Jersey colors, day of week, etc.

**Diminishing Returns:**
- 50% → 60%: Relatively easy (basic features)
- 60% → 65%: Medium difficulty (good features)
- 65% → 70%: Hard (advanced context)
- 70%+: Very hard (professional level)

---

## ✅ LET'S DO THIS

Ready to start with:
1. Train baseline (5 min)
2. Add starting goalies (3 hours)
3. Add rebounds (2 hours)

Should we begin? 🚀
