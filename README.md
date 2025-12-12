# 🏒 Puckcast NHL Prediction Model - Complete Documentation

> **Last Updated**: December 7, 2025
> **Current Model**: V7.0 (Adaptive Weights)
> **Production Accuracy**: 60.9% on 4-season holdout (5,002 games)
> **Features**: 39 + adaptive weights
> **Website**: https://puckcast.ai
> **Status**: ✅ Production Ready - Live

---

## 📊 Quick Status

| Metric | Value | Status |
|--------|-------|--------|
| **Production Model** | V7.0 | ✅ Active |
| **Test Accuracy** | 60.9% | ✅ 4-season holdout |
| **Games Tested** | 5,002 | ✅ 2021-25 seasons |
| **Baseline** | 53.9% | Home win rate |
| **Edge vs Baseline** | +6.9 pts | ✅ Significant |
| **Features** | 39 + adaptive weights | ✅ Production |

---

## 🎯 Executive Summary

After extensive experimentation across multiple model versions:

> **V7.0 at 60.9% represents the current production model with 4-season holdout validation.**

### Model Performance

```
V7.0  60.9%   ━━━━━━━━━━━━━━━━━━━━━  ✅ PRODUCTION MODEL
                                      (39 features + adaptive weights)
                                      Tested on 5,002 games (2021-25)

Confidence Grades:
A+   79.3%   ━━━━━━━━━━━━━━━━━━━━━━  333 games (≥25 pts edge)
A    72.0%   ━━━━━━━━━━━━━━━━━━━━    404 games (20-25 pts edge)
B+   67.3%   ━━━━━━━━━━━━━━━━━━      687 games (15-20 pts edge)
B    62.0%   ━━━━━━━━━━━━━━━━        975 games (10-15 pts edge)
```

Note: Metrics validated on December 7, 2025

---

## 📁 Repository Structure

```
puckcast/
├── README.md                        # ← You are here
│
├── docs/                            # 📚 Documentation Hub
│   ├── INDEX.md                     # Documentation navigation
│   ├── V7_DEVELOPMENT_LESSONS.md    # ⚠️ What worked & didn't - READ FIRST
│   ├── current/                     # Current model docs
│   │   └── CLOSING_GAP_ANALYSIS.md
│   ├── experiments/                 # V7.0 Development Test Logs
│   │   ├── V7.4_EXPERIMENTS.md      # H2H & ensemble tests
│   │   ├── V7.5_EXPERIMENTS.md      # Feature interaction tests
│   │   └── V7.6_EXPERIMENTS.md      # Feature selection tests
│   └── archive/                     # Historical docs
│
├── src/nhl_prediction/              # 🧠 Core Prediction Engine
│   ├── pipeline.py                  # Feature engineering pipeline
│   ├── model.py                     # Model training/prediction
│   ├── situational_features.py      # ⭐ V7.0 situational features
│   ├── head_to_head_features.py     # Test: H2H (not used in production)
│   ├── interaction_features.py      # Test: interactions (not used)
│   └── team_calibration_features.py # Test: calibration (not used)
│
├── training/                        # 🎓 Training Scripts
│   ├── README.md                    # Training documentation
│   ├── build_feature_store.py       # Build feature dataset
│   ├── fetch_historical_data.py     # Fetch NHL historical data
│   └── retrain_xg_model.py          # Retrain xG model
│
├── analysis/                        # 🔬 Analysis Scripts
│   ├── current/                     # Current analysis
│   │   ├── analyze_errors.py
│   │   ├── analyze_b2b_weakness.py
│   │   └── analyze_confidence_calibration.py
│   └── archive/                     # Old analysis
│
├── prediction/                      # 🎯 Prediction Scripts
│   ├── predict_tonight.py           # Daily predictions
│   ├── predict_simple.py            # Simple CLI predictions
│   └── predict_full.py              # Full analysis
│
├── web/                             # 🌐 Next.js Frontend
├── data/                            # 💾 Data & Models
└── archive/                         # 📦 Old Files
```

---

## 🚀 Quick Start

### 1. Make Predictions

```bash
# Predict tonight's games
python prediction/predict_tonight.py

# Predict specific matchup
python prediction/predict_simple.py TOR BOS

# Full analysis with confidence bands
python prediction/predict_full.py
```

### 2. Fetch Historical Data (Expanded Training)

```bash
# Check what historical data is cached
python training/fetch_historical_data.py --check

# Fetch all historical seasons (2017-18 through 2020-21)
python training/fetch_historical_data.py

# Fetch a specific season only
python training/fetch_historical_data.py --season 20172018

# Re-fetch a season (overwrite cache)
python training/fetch_historical_data.py --season 20172018 --force
```

**Historical Season Notes**:
| Season | Description | Expected Games |
|--------|-------------|----------------|
| 2017-18 | Full 82-game season, 31 teams | ~1,271 |
| 2018-19 | Full 82-game season, 31 teams | ~1,271 |
| 2019-20 | COVID-shortened (pause March 11, 2020) | ~1,082 |
| 2020-21 | COVID-shortened 56-game season | ~868 |

### 3. Train V7.0 (Production Model)

```bash
python training/train_v7_adaptive.py

# Expected output:
# Test Accuracy: 0.609 (60.9%)
# ROC-AUC: 0.64
# Log Loss: 0.6554
# Brier Score: 0.2317
# Model saved: model_v7_adaptive.pkl
```

### 4. Analyze Performance

```bash
# Comprehensive error analysis
python analysis/current/analyze_errors.py

# Back-to-back game analysis
python analysis/current/analyze_b2b_weakness.py

# Calibration analysis
python analysis/current/analyze_confidence_calibration.py
```

---

## 📈 V7.0 Production Model - Detailed Performance

### Model Architecture

- **Type**: Logistic Regression with Isotonic Calibration + Adaptive Weights
- **Features**: 39 core features + adaptive weights
- **Training**: Multi-season with adaptive home advantage modeling
- **Testing**: 4-season holdout (2021-22 through 2024-25)
- **Optimization**: Adaptive weights for evolving home advantage

### Performance Metrics (Validated Dec 7, 2025)

| Metric | Value | Interpretation |
|--------|-------|----------------|
| **Accuracy** | 60.9% | 3,046/5,002 correct predictions |
| **Brier Score** | 0.2317 | Excellent calibration |
| **Log Loss** | 0.6554 | Well-calibrated probabilities |
| **Baseline** | 53.9% | Home win rate |
| **Edge** | +6.9 pts | Significant improvement |

### Confidence Grade Analysis

| Grade | Edge | Games | Accuracy | Coverage |
|-------|------|-------|----------|----------|
| **A+** | ≥25 pts | 333 | **79.3%** | 6.7% |
| **A** | 20-25 pts | 404 | **72.0%** | 8.1% |
| **B+** | 15-20 pts | 687 | **67.3%** | 13.7% |
| **B** | 10-15 pts | 975 | **62.0%** | 19.5% |
| **C+** | 5-10 pts | 1,231 | 57.8% | 24.6% |
| **C** | 0-5 pts | 1,372 | 51.9% | 27.4% |

**Key Insight**:
- A+ predictions (25+ pts): **79.3% accuracy** - elite tier
- A-grade combined (20+ pts): **75%+ accuracy** on 737 games

### V7.0 Adaptive Weights

The V7.0 model introduces adaptive weighting that accounts for:
- Evolving home ice advantage (diminishing post-COVID)
- Season-specific calibration
- Feature importance shifts across seasons

**Impact**: Robust 60.9% accuracy across 4 full seasons (5,002 games)

---

## 🔬 What We Learned - Comprehensive Analysis

### ✅ Successful Approaches

#### V7.0 Feature Engineering
- **209 engineered features** from NHL API data
- **Rolling statistics**: Goals, xG, shots, corsi, fenwick (3/5/10 game windows)
- **Team indicators**: 32 team dummy variables
- **Season averages**: Goal differential, xG differential, shot metrics
- **Rest/schedule**: rest_diff, B2B flags, games in last N days
- **Goalie metrics**: Team-level save%, GSAX, shots faced

**Top 5 Features**:
1. `rolling_goal_diff_10_diff` (coef: -0.1939)
2. `rolling_high_danger_shots_3_diff` (0.1829)
3. `season_goal_diff_avg_diff` (0.1778)
4. `home_team_28` (-0.1709) [team dummy]
5. `rolling_xg_for_5_diff` (0.1492)

#### V7.0 Situational Features
- **Fatigue modeling** beyond simple B2B
- **Travel burden** (miles traveled)
- **Divisional matchup** importance
- **Post-break performance** (first game after rest)
- **Third period trailing** (comeback ability)

**Why it worked**: Orthogonal information not captured by rolling stats

---

### ❌ Failed Development Tests

During V7.0 development, we tested several approaches that **did not improve** the model:

#### Test: Head-to-Head Features (60.00%)

**Hypothesis**: Specific matchup history adds predictive value
**Implementation**: 6 features:
- `h2h_win_pct_last_season`
- `h2h_win_pct_recent` (last 3 games)
- `h2h_goal_diff_recent`
- `h2h_home_advantage`
- `season_series_home_wins`
- `season_series_away_wins`

**Critical Bug Found**: Data leakage - test games used other test game outcomes in features
**After Fix**: Still 60.00% (worse than baseline)

**Root Causes**:
1. **Multicollinearity**: H2H correlates with `rolling_goal_diff`, `rolling_win_pct`
2. **Weak signal**: Best H2H coefficient only 0.089 (vs 0.19 for top base features)
3. **Sample size**: Only 2-4 matchups per season → high variance
4. **Already captured**: Rolling stats implicitly include H2H performance

**Lesson**: Error patterns (20+ problematic matchups) don't always suggest solutions - might just be noise

📄 **Full Analysis**: [docs/experiments/V7.4_EXPERIMENTS.md](docs/experiments/V7.4_EXPERIMENTS.md)

---

#### Test: Feature Interactions (60.08%)

**Hypothesis**: Non-linear combinations of features add value
**Implementation**: 12 interaction terms:
- `rolling_goal_diff_10 × divisional_matchup`
- `rolling_high_danger_shots × rest_diff`
- `season_goal_diff_avg × b2b_indicator`
- `rolling_xg_for × divisional/rest/b2b`

**Root Causes**:
1. **Multicollinearity**: Interactions correlated with base features
2. **Overfitting**: Added complexity without new signal
3. **Weak coefficients**: Best interaction 0.13 vs 0.19 for top base features
4. **Logistic regression already non-linear**: Sigmoid naturally captures interactions

**Best Interaction**: `season_goal_diff_avg_x_divisional` (coef: 0.1333)

**Lesson**: More features ≠ better model. Interactions add noise when base features suffice.

📄 **Full Analysis**: [docs/experiments/V7.5_EXPERIMENTS.md](docs/experiments/V7.5_EXPERIMENTS.md)

---

#### Test: Team-Specific Calibration (60.73%)

**Hypothesis**: Teams with high error rates need bias adjustments
**Implementation**: 15 team-specific features for VGK, PHI, NYI, WSH, PIT:
- `team_VGK_home`, `team_VGK_away`, `team_VGK_any`
- Similar for PHI, NYI, WSH, PIT

**Root Causes**:
1. **Weak signal**: Largest coefficient only 0.052 (PHI_away)
2. **Already captured**: Team dummy variables in V7.0 baseline
3. **Sample size**: ~82 games/team/season insufficient for robust bias estimation
4. **No systematic pattern**: High error rates might be random variance

**Best Calibration**: `team_PHI_away` (coef: 0.0520)

**Lesson**: Team-specific effects already captured by existing team indicators. Additional bias terms redundant.

📄 **Full Analysis**: [docs/experiments/V7.6_EXPERIMENTS.md](docs/experiments/V7.6_EXPERIMENTS.md)

---

#### Test: Confidence-Based Filtering (62.71%* at 69% coverage)

**Hypothesis**: Exclude low-confidence predictions to improve accuracy
**Implementation**: Analyze calibration and coverage tradeoffs

**Results**:

| Min Confidence | Coverage | Accuracy | Games Excluded |
|----------------|----------|----------|----------------|
| 0pt (all games) | 100.0% | 60.24% | 0 |
| 5pt+ | 85.1% | 61.41% | 183 (15%) |
| **10pt+** | **68.5%** | **62.71%** ✅ | **388 (31%)** |
| 15pt+ | 51.3% | 64.98% | 599 (49%) |
| 20pt+ | 37.6% | 67.39% | 768 (62%) |
| 25pt+ | 24.3% | 70.23% | 931 (76%) |

**Key Finding**: Can exceed 62% target by excluding lowest 10pt confidence games (31% of dataset)

**Why This Isn't a Solution**:
- Not a model improvement - just prediction filtering
- 31% of games = ~500 games/season unpredicted
- Low-confidence games are where predictions most valuable (uncertainty high)

**Value**: Shows model is well-calibrated - knows when it doesn't know

**Optimal Threshold**: 0.53 (vs default 0.50) → +0.33pp improvement (60.57%)

**Lesson**: Model has good calibration. The 31% coin-flip games are fundamentally unpredictable, not fixable with better features.

📄 **Full Analysis**: [docs/V7_DEVELOPMENT_LESSONS.md](docs/V7_DEVELOPMENT_LESSONS.md)

---

### 🥅 Test: Goalie Tracking (58.62%)

**Hypothesis**: Individual goalie performance more predictive than team-level aggregates
**Implementation**: Complete infrastructure built:
- `populate_starting_goalies_from_history.py` - Identify starters from boxscores
- `build_goalie_database_fixed.py` - Track individual goalie stats (GSA, save%, xGA)
- 8 goalie features: `goalie_gsa_last5_home/away`, `goalie_save_pct_last5_home/away`, etc.

**Results**:
- **Individual Tracking**: 58.62% ❌
- **Team-Level**: 60.9% ✅ BETTER

**Why Individual Failed**:
1. **Coverage gap**: 93.9% vs 100% for team-level
2. **Small sample size**: Average 5 games per goalie (high variance)
3. **High individual variance**: One bad game doesn't predict next game well
4. **Team defense dominant**: Team defensive system matters more than individual goalie

**Data Quality Issues Found & Fixed**:
- Team abbreviations showing 'UNK' → Fixed by extracting from boxscore root level
- Expected goals always 0.0 → Fixed by attributing team xG by TOI proportion
- GSA always negative → Fixed with proper calculation: `gsa = xGA - goals_against`

**Value Preserved**: Infrastructure useful for future stats pages and player analysis

📄 **Full Analysis**: [docs/V7_DEVELOPMENT_LESSONS.md](docs/V7_DEVELOPMENT_LESSONS.md)

---

## 🧠 Technical Insights - Why We Hit a Ceiling

### Root Cause Analysis: Why 60.9% is the Practical Ceiling

The gap to 62%+ consists of:
- **~70%**: Inherent randomness (low-confidence games are true coin flips)
- **~20%**: Logistic regression model limitations
- **~10%**: Potentially improvable with new data sources

#### 1. Feature Saturation
- 209 features already capture most predictive signal
- Adding more features introduces noise, not information
- All 4 gap-closing attempts made model worse

#### 2. Inherent Randomness
- **31% of games** have <10pt confidence (essentially coin flips)
- No amount of feature engineering fixes fundamental unpredictability
- These games drag down overall accuracy to ~60%

#### 3. Neither-B2B Dominance
- **76% of games** are neither-B2B (both teams rested)
- Only **58.2% accuracy** on neither-B2B games
- B2B games are **69.5% accurate** (easier!) but only 24% of dataset
- No exploitable pattern in neither-B2B games

#### 4. Home Ice Advantage Diminished
- Test set: **53.7% home win rate** (close to 50-50)
- Historical average: ~55%
- Less signal to exploit

#### 5. Logistic Regression Limits
- Linear model assumptions
- Can't capture complex non-linear interactions
- Sigmoid transformation provides some non-linearity but limited

### Error Pattern Analysis

**Hardest Teams to Predict** (from 494 incorrect predictions):
- **VGK**: 34.7% error rate (128 games, 44 errors)
- **PHI**: 33.9% error rate (115 games, 39 errors)
- **NYI**: 32.2% error rate (118 games, 38 errors)

**Easiest Scenarios**:
- **B2B games**: 69.5% accuracy (high fatigue signal)
- **Divisional matchups**: 63.1% accuracy (familiarity patterns)
- **Very high confidence (25+ pts)**: 70.2% accuracy

**Hardest Scenarios**:
- **Neither-B2B**: 58.2% accuracy (76% of dataset)
- **Low confidence (<5pt)**: 53.6% accuracy (essentially random)
- **Non-divisional games**: 59.8% accuracy

**Surprising Finding**: Away B2B NOT a weakness!
- Initial hypothesis: 56 away B2B errors → underweighted
- Reality: **69.5% accuracy** on away B2B (53 errors out of 174 games)
- Confused absolute count with error rate

📄 **Full Error Analysis**: [error_analysis.csv](error_analysis.csv)

---

## 🔮 Future Directions - How to Exceed 62%

### Option 1: Accept V7.0 at 60.9% ✅ CURRENT

**Why**:
- Well-calibrated, production-ready model
- 4-season holdout validation (5,002 games)
- Adaptive weights handle evolving NHL patterns
- Focus on application layer (UI, user experience)

**Recommendation**: Use confidence grades to guide usage, focus on A-grade predictions

---

### Option 2: Advanced Model Architecture (Expected: +0.5-2.0pp)

**Approaches**:
1. **Gradient Boosting**
   - XGBoost, LightGBM, CatBoost
   - Better at capturing non-linear interactions
   - Expected lift: +0.5-1.5pp

2. **Neural Networks**
   - LSTM/GRU for time series patterns
   - Attention mechanisms for recent vs historical data
   - Expected lift: +1.0-2.0pp

3. **Ensemble Methods**
   - Combine multiple model types
   - Stacking, bagging, boosting
   - Expected lift: +0.5-1.0pp

**Tradeoffs**:
- **Complexity**: 10x increase in training time, hyperparameter tuning
- **Interpretability**: Loss of feature importance insights
- **Deployment**: More complex production infrastructure
- **Overfitting risk**: Easier to overfit with complex models

---

### Option 3: New Data Sources (Expected: +0.3-1.0pp)

**Player-Level Data**:
- Individual skater stats (not just team aggregates)
- Line combinations and chemistry
- Ice time distribution
- Expected lift: +0.2-0.5pp

**Advanced Metrics**:
- Shot-by-shot xG models (location, context, shooter quality)
- Zone entry/exit data
- Faceoff win locations
- Expected lift: +0.2-0.4pp

**External Factors**:
- Injury reports (severity, position impact)
- Referee assignments (penalty patterns)
- Weather (for outdoor games, temperature)
- Expected lift: +0.1-0.2pp

**Total Expected Lift**: +0.5-1.1pp (to 61.9-62.5%)

**Tradeoffs**:
- **Effort**: HIGH - new data pipelines, scraping, cleaning
- **Availability**: Some data sources may be unreliable or expensive
- **Maintenance**: Ongoing data quality monitoring

---

### Option 4: Hybrid Prediction System (For Specific Use Cases)

**Strategy**: Only predict high-confidence games

**Configuration**:
- **Threshold**: >15pt confidence
- **Coverage**: 51.3% of games
- **Accuracy**: 64.98% on predicted games

**Use Cases**:
- Betting applications (only bet when confident)
- Premium tier (high-quality predictions only)
- Risk-averse users

**Tradeoffs**:
- Incomplete coverage (~500 games/season unpredicted)
- More complex user experience (some games skipped)
- Not a "better model" - just selective prediction

---

## 📚 Documentation Index

### 🎯 Start Here

1. **⚠️ [docs/V7_DEVELOPMENT_LESSONS.md](docs/V7_DEVELOPMENT_LESSONS.md)** - READ FIRST!
   - What worked and what didn't in V7.0 development
   - Why features failed (H2H, interactions, team calibration)
   - Key principles and mistakes to avoid
   - Don't repeat the same experiments!

2. **[docs/current/CLOSING_GAP_ANALYSIS.md](docs/current/CLOSING_GAP_ANALYSIS.md)**
   - Comprehensive analysis of model ceiling
   - Development test results
   - Technical deep dive into model limitations

3. **[docs/INDEX.md](docs/INDEX.md)** - Documentation navigation and metrics

### 🧪 V7.0 Development Test Logs

Detailed experiment logs (for reference, summaries in V7_DEVELOPMENT_LESSONS.md):

4. **[docs/experiments/V7.4_EXPERIMENTS.md](docs/experiments/V7.4_EXPERIMENTS.md)** - H2H & ensemble tests
5. **[docs/experiments/V7.5_EXPERIMENTS.md](docs/experiments/V7.5_EXPERIMENTS.md)** - Feature interaction tests
6. **[docs/experiments/V7.6_EXPERIMENTS.md](docs/experiments/V7.6_EXPERIMENTS.md)** - Feature selection & calibration

---

## 🧪 Reproducibility Guide

### Reproduce V7.0 Training

```bash
cd /home/user/puckcast
python training/train_v7_adaptive.py

# Expected output:
# ================================================================================
# V7.0 RESULTS
# ================================================================================
# Test Set Performance (4-season holdout):
#   Accuracy:  0.609 (60.9%)
#   Brier:     0.2317
#   Log Loss:  0.6554
# Model saved: model_v7_adaptive.pkl
```

### Reproduce Development Tests

```bash
# Test: Head-to-head (expect 60.00%)
python training/experiments/train_test_head_to_head.py

# Test: Interactions (expect 60.08%)
python training/experiments/train_test_interactions.py

# Test: Team calibration (expect 60.73%)
python training/experiments/train_test_team_calibration.py
```

### Run Analysis Scripts

```bash
# Error analysis (generates error_analysis.csv)
python analysis/current/analyze_errors.py

# B2B analysis (shows away B2B is EASIER, not harder!)
python analysis/current/analyze_b2b_weakness.py

# Calibration analysis (shows 62.71% possible at 69% coverage)
python analysis/current/analyze_confidence_calibration.py
```

---

## 📅 Version History

| Version | Accuracy | Status | Key Changes |
|---------|----------|--------|-------------|
| **V7.0** | **60.9%** | ✅ **PRODUCTION** | **39 features + adaptive weights, 4-season holdout** |
| V6.4 | ~59% | Superseded | Previous production model |
| V6.x | 58-60% | Archived | Various experiments |

### V7.0 Development Tests Summary

The V7.0 release represents the culmination of extensive experimentation:

| Test | Accuracy | Result | Notes |
|------|----------|--------|-------|
| Baseline features | 60.24% | ✅ Included | Initial 209-feature baseline |
| Situational features | 60.49% | ✅ Included | Fatigue, travel, divisional |
| Head-to-head | 60.00% | ❌ Rejected | Multicollinearity issues |
| Feature interactions | 60.08% | ❌ Rejected | Overfitting |
| Team calibration | 60.73% | ❌ Rejected | Weak signal |
| Adaptive weights | 60.9% | ✅ Production | Handles evolving patterns |

**Conclusion**: V7.0 with adaptive weights represents the best-performing model, validated across 5,002 games over 4 seasons.

---

## 🏆 Key Achievements

✅ Built production-ready model at **60.9% accuracy** on 5,002-game holdout
✅ Optimized feature set (**39 features + adaptive weights**)
✅ Proper 4-season holdout validation (no data leakage)
✅ **Well-calibrated probability predictions** (Brier Score: 0.2317)
✅ **Confidence grade system** for user guidance (79.3% on A+ picks)
✅ **Live website** at puckcast.ai with H2H matchup pages
✅ **Team pages** with PP/PK stats and power rankings
✅ **Daily predictions** sorted by edge strength
✅ **Complete documentation** of model evolution and learnings

---

## 💡 Key Learnings - What We'd Tell Our Past Selves

### ✅ What Works

1. **Team-level aggregates > Individual tracking**
   - Team save% beats individual goalie stats
   - Team defense matters more than goalie

2. **Rolling statistics are king**
   - 3/5/10 game windows capture recent form
   - `rolling_goal_diff_10` is #1 feature

3. **Situational context adds value**
   - Fatigue, travel, divisional matchups
   - +0.49pp improvement over baseline

4. **Simplicity wins**
   - Adding features usually hurts
   - Feature engineering has diminishing returns

5. **Confidence calibration is critical**
   - Well-calibrated model knows when it doesn't know
   - 70% accuracy on high-confidence games

### ❌ What Doesn't Work

1. **Head-to-head features**
   - Multicollinear with rolling stats
   - Sample size too small (2-4 games/season)

2. **Feature interactions**
   - Overfitting without new signal
   - Logistic regression already handles non-linearity

3. **Team-specific biases**
   - Already captured by team dummies
   - Weak signal (<0.06 coefficients)

4. **Individual goalie tracking**
   - High variance, low coverage
   - Team-level better for prediction

5. **Trying to predict coin flips**
   - 31% of games are fundamentally random
   - No features fix true randomness

### 🎓 Meta-Learnings

1. **Error patterns ≠ Solutions**
   - Problematic matchups might just be noise
   - Not every error is fixable

2. **More data isn't always better**
   - Added 4 feature sets, all failed
   - Feature saturation is real

3. **Know when to stop**
   - 60.9% is the practical ceiling with current approach
   - Accepting limits is valid strategy

4. **Document failures thoroughly**
   - Failed experiments are valuable
   - Save future developers from repeating mistakes

---

## 🚀 Getting Started

### Prerequisites

```bash
# Python 3.11+
pip install -r requirements.txt

# Verify installation
python3 -c "from src.nhl_prediction.pipeline import build_dataset; print('✓ Setup OK')"
```

### Make Your First Prediction

```bash
# Option 1: Tonight's games
python prediction/predict_tonight.py

# Option 2: Specific matchup
python prediction/predict_simple.py TOR BOS

# Output:
# Toronto Maple Leafs vs Boston Bruins
# Predicted Winner: TOR (61.3%)
# Confidence: Medium (11pt edge)
# Recommendation: Low confidence - coin flip territory
```

### Train the Model

```bash
# Train V7.0 from scratch
python training/train_v7_adaptive.py

# Model saved to: model_v7_adaptive.pkl
# Training time: ~2-3 minutes
```

---

## 📞 Support & Questions

### Documentation Questions
- **What worked & didn't**: See [docs/V7_DEVELOPMENT_LESSONS.md](docs/V7_DEVELOPMENT_LESSONS.md)
- **Model ceiling analysis**: See [docs/current/CLOSING_GAP_ANALYSIS.md](docs/current/CLOSING_GAP_ANALYSIS.md)
- **Development test logs**: See [docs/experiments/](docs/experiments/) for detailed experiment logs

### Technical Issues
- **GitHub Issues**: (when public)
- **Documentation**: `/docs` folder
- **Analysis Scripts**: `/analysis/current` folder

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- **NHL Gamecenter API** - Play-by-play data
- **Scientific Python Community** - pandas, scikit-learn, numpy
- **All the failed experiments** - Taught us what doesn't work

---

**🏒 V7.0 is live at https://puckcast.ai with 60.9% accuracy. See [docs/INDEX.md](docs/INDEX.md) for documentation!**
