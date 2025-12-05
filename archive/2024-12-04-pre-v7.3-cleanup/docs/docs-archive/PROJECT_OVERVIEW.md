# NHL Win Probability Model - Project Overview

**Ultimate Goal:** Develop a model that predicts NHL game outcomes with sufficient accuracy to identify +EV (positive expected value) betting opportunities and achieve positive ROI when compared against betting markets.

---

## 🎯 Core Mission

This is **not** just an academic exercise in achieving high accuracy. The end goal is:

1. **Predict win probabilities** for NHL games using only pre-game information
2. **Compare model probabilities** to betting market implied probabilities
3. **Identify market inefficiencies** where our model disagrees with the market
4. **Simulate betting strategies** to determine if edge translates to positive ROI
5. **Validate rigorously** to distinguish skill from luck

**Success Metric:** Sustainable positive ROI when betting on games where model probability significantly exceeds market probability.

---

## 📊 Current Status

### ✅ **Phase 1: Foundation (COMPLETE)**

**Data Pipeline:**
- ✅ MoneyPuck data ingestion (115MB, 220K+ game records)
- ✅ Game-by-game statistics with advanced metrics (xG, shot quality)
- ✅ Clean, organized, zero data leakage

**Feature Engineering:**
- ✅ 128 features across 7 families
- ✅ Rolling windows (3, 5, 10 games)
- ✅ Elo rating system
- ✅ Rest and scheduling metrics
- ✅ Special teams matchups
- ✅ All features properly lagged (no future information)

**Model Development:**
- ✅ Logistic Regression baseline
- ✅ Histogram Gradient Boosting (advanced)
- ✅ Hyperparameter tuning with validation set
- ✅ Probability calibration (isotonic regression)
- ✅ Comprehensive evaluation metrics

**Current Performance:**
- **Accuracy:** 62.18% on 2023-24 test season
- **ROC-AUC:** 0.657
- **Baseline:** 54.5% (always predict home team)
- **Improvement:** +7.7 percentage points over baseline

**Deployment:**
- ✅ Interactive Streamlit dashboard
- ✅ Command-line training interface
- ✅ Exportable predictions
- ✅ Comprehensive visualizations

---

### 🚧 **Phase 2: Betting Integration (IN PROGRESS)**

**Goal:** Determine if model predictions can beat betting markets.

**Implementation Plan:**
1. **Obtain betting odds** for 2023-24 season (historical closing lines)
2. **Convert odds to probabilities** (remove bookmaker vig)
3. **Compare model vs market** (Brier score, calibration, correlation)
4. **Simulate betting strategies:**
   - Threshold betting (bet when edge > X%)
   - Kelly Criterion (optimal bet sizing)
   - Selective high-confidence betting
5. **Calculate ROI metrics:**
   - Overall return on investment
   - Win rate vs breakeven rate
   - Sharpe ratio (risk-adjusted returns)
   - Maximum drawdown
6. **Validate on 2024-25 season** (true out-of-sample test)

**See:** `docs/betting_integration_plan.md` for complete roadmap

---

### 🔮 **Phase 3: Optimization (FUTURE)**

If Phase 2 shows potential edge:

1. **Enhance features** with MoneyPuck xG data
2. **Model ensembles** (combine multiple models)
3. **Live deployment** (weekly data updates)
4. **Real-time tracking** (paper trading)
5. **Continuous validation** (guard against model drift)

---

## 💡 **Key Differentiators**

### Why This Model Might Have Edge

1. **Professional Data:** MoneyPuck's xG and shot quality (markets may undervalue)
2. **Faceoff Importance:** Model's top features are faceoff differentials (often overlooked)
3. **Schedule Congestion:** Back-to-backs, rest differentials (market may underestimate)
4. **Rigorous Features:** 128 engineered features vs basic stats
5. **No Leakage:** Truly pre-game only (markets sometimes use unofficial info)

### Why It Might Not

1. **Market Efficiency:** Betting markets aggregate wisdom of millions
2. **Sample Size:** 3 seasons may not be enough to distinguish skill from luck
3. **Overfitting Risk:** 128 features on 3,690 games - danger of memorizing noise
4. **Market Adaptation:** If edge exists, it may disappear as markets learn

**Critical:** We must be **brutally honest** about results. If model doesn't beat market, that's valuable negative result - markets are efficient.

---

## 📈 **Data Quality**

### Source: MoneyPuck

**Why MoneyPuck > NHL Official Data:**
- **xGoals (xG):** Shot quality metrics (location, type, game state)
- **Shot danger classification:** High/medium/low danger breakdowns
- **Corsi & Fenwick:** Possession metrics (shot attempts)
- **Score-adjusted stats:** Context-aware (teams trailing shoot more)
- **Professional maintenance:** Used by NHL analysts, media, researchers

**Data File:** `data/moneypuck_all_games.csv`
- 115MB, 220,000+ team-game records
- Coverage: 2008-2024 seasons
- Update: Manual download from MoneyPuck.com

**Verification:**
✅ No NHL API dependencies
✅ Zero data leakage (all features pre-game only)
✅ Clean, standardized schema
✅ 42 xGoals-related columns available
✅ Chronological ordering preserved

---

## 🎲 **Betting Market Context**

### Why This Is Hard

**Professional sportsbooks:**
- Employ PhDs in statistics
- Have massive datasets
- React to sharp money instantly
- Adjust odds based on injury news, weather, etc.

**Typical sports betting ROI:**
- Break-even: -4% to 0% (paying vig)
- Good: 2-5% ROI
- Excellent: 5-10% ROI
- Suspicious: >10% (likely overfitting)

**NHL Specifics:**
- High variance sport (low scoring, hot goalies)
- Even best handicappers struggle to achieve >55% win rate
- Home ice advantage ~54-55% win rate
- Vig means need >52.4% win rate to break even on 50-50 games

### What We're Testing

**Hypothesis:** MoneyPuck's advanced metrics (xG, shot quality) capture signal that betting markets don't fully price in.

**Test:** Do games where our model disagrees significantly with market odds show positive EV?

**Validation:** Must hold up on 2024-25 season (true blind test).

---

## 📊 **Model Pipeline**

```
MoneyPuck CSV (115MB)
    ↓
load_moneypuck_data()
  - Filter: team-level, regular season, "all" situation
    ↓
fetch_multi_season_logs()
  - Extract seasons: 2021-22, 2022-23, 2023-24
    ↓
engineer_team_features()
  - Rolling stats (3, 5, 10 games)
  - Lagged cumulative (season-to-date)
  - Momentum (recent vs season average)
  - Rest & scheduling (back-to-backs, congestion)
    ↓
build_game_dataframe()
  - Merge home/away into matchups
  - Compute target (home_win)
    ↓
_add_elo_features()
  - Dynamic ratings updated after each game
    ↓
build_dataset()
  - Compute differentials (home - away)
  - One-hot encode teams
  - Final feature matrix: 128 features
    ↓
compare_models()
  - Train/validation/test split
  - Tune hyperparameters
  - Calibrate probabilities
  - Select best model
    ↓
OUTPUT: Win probabilities for each game
```

---

## 🔬 **Validation Rigor**

### Data Leakage Prevention

**Every feature is pre-game only:**
```python
# ✓ Correct: uses games BEFORE current
logs['season_win_pct'] = group['win'].cumsum().shift(1) / games_played_prior

# ✓ Correct: rolling window starts with shift(1)
logs['rolling_win_pct_5'] = group['win'].shift(1).rolling(5).mean()

# ✗ Wrong: includes current game
logs['season_win_pct'] = group['win'].cumsum() / group.cumcount()
```

**Manual verification:**
- Early-season games have zeros/nulls (expected - no history)
- Feature values match hand calculations for sample games
- Elo ratings never use post-game information

### Temporal Splitting

**Training:** 2021-22, 2022-23 seasons
**Validation:** 2022-23 (last training season for hyperparameter tuning)
**Test:** 2023-24 (held-out, never seen during training)

**Critical:** NO random shuffling. Games are chronologically split to simulate real deployment.

### Overfitting Guards

1. **Regularization:** L2 penalty in Logistic Regression
2. **Validation tuning:** Hyperparameters selected on validation set
3. **Multiple metrics:** Not just accuracy (log loss, Brier, ROC-AUC, calibration)
4. **Future test:** Will validate on 2024-25 season

---

## 🎯 **Next Steps (Betting Integration)**

### Week 1: Data Acquisition
- [ ] Sign up for The Odds API or find historical odds source
- [ ] Download closing line odds for 2023-24 season
- [ ] Map odds to gameIds
- [ ] Validate data quality (no missing games)

### Week 2: Model-Market Comparison
- [ ] Convert American odds to probabilities
- [ ] Remove bookmaker vig (overround)
- [ ] Compare Brier scores (model vs market)
- [ ] Analyze where model disagrees with market

### Week 3: Betting Simulation
- [ ] Implement threshold betting strategy (5%, 10% edge)
- [ ] Implement Kelly Criterion bet sizing
- [ ] Run simulations on 2023-24 data
- [ ] Calculate ROI, win rate, Sharpe ratio, drawdown

### Week 4: Reporting
- [ ] Generate betting performance visualizations
- [ ] Update group report with findings
- [ ] Prepare presentation slides
- [ ] Document insights (what worked, what didn't)

### Ongoing: Live Validation
- [ ] Track 2024-25 season (paper trading)
- [ ] Compare predictions to actual outcomes
- [ ] Monitor model drift
- [ ] Refine features if needed

---

## 📋 **Success Criteria**

### Academic Success
✅ **Achieved:**
- Prediction accuracy significantly above baseline
- Well-calibrated probabilities
- Interpretable feature importance
- Rigorous validation methodology
- Professional documentation

### Betting Success (TBD)
**Target:**
- ROI > 2% on simulated betting (2023-24 test season)
- Win rate > 53% (accounting for vig)
- Edge holds on 2024-25 season (live validation)

**Reality Check:**
- If ROI < 0%: Markets are efficient, model has no edge (expected outcome!)
- If ROI 0-2%: Small edge, marginal profitability
- If ROI 2-5%: Meaningful edge, potentially profitable
- If ROI > 5%: Suspicious, likely overfitting

---

## 🎓 **Learning Value**

**Regardless of ROI outcome, this project demonstrates:**

1. **End-to-end ML pipeline** (data → features → models → deployment)
2. **Real-world validation** (against professional betting markets)
3. **Domain expertise** (hockey-specific features and insights)
4. **Statistical rigor** (preventing data leakage, temporal validation)
5. **Critical thinking** (questioning results, understanding limitations)
6. **Professional data sources** (MoneyPuck, industry-standard)

**Portfolio value:**
- "Built NHL prediction model that achieved X% accuracy"
- "Validated model against betting markets to test real-world performance"
- "Processed 115MB dataset with 220K records, engineered 128 features"
- "Deployed interactive dashboard with Streamlit"

---

## 📚 **Documentation**

- **`README.md`** - Quick start guide
- **`docs/taxonomy.md`** - Data schema and feature definitions
- **`docs/usage.md`** - Detailed usage instructions
- **`docs/group_report_2.md`** - Comprehensive project report
- **`docs/betting_integration_plan.md`** - Betting analysis roadmap (40+ pages)
- **`MONEYPUCK_MIGRATION.md`** - Migration from NHL API to MoneyPuck
- **`PROJECT_OVERVIEW.md`** - This document

---

## 🚀 **Running the Project**

### Quick Test
```bash
python -c "from src.nhl_prediction.pipeline import build_dataset; 
dataset = build_dataset(['20232024']); 
print(f'{len(dataset.games)} games, {dataset.features.shape[1]} features')"
```

### Train Models
```bash
python -m nhl_prediction.train \
    --train-seasons 20212022 --train-seasons 20222023 \
    --test-season 20232024
```

### Launch Dashboard
```bash
streamlit run streamlit_app.py
```

---

## 🎯 **The Bottom Line**

**We've built a sophisticated NHL prediction model using professional-grade data. Now we need to answer the hard question:**

**Can our model find edges that betting markets miss?**

**If yes:** We've created real value - our features capture signal markets don't fully price.

**If no:** We've learned markets are extremely efficient - valuable lesson about real-world ML.

**Either way, we've built something impressive. Let's find out which it is! 🏒**

---

**Last Updated:** November 10, 2024
**Status:** Phase 1 complete, Phase 2 in progress
**Next Milestone:** Obtain betting odds and run ROI simulations

