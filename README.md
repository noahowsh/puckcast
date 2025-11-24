# 🏒 Puckcast - NHL Game Prediction System

**Version:** 2.0
**Accuracy:** 60.89% (vs 53.7% baseline)
**Status:** Active Development

Puckcast is a machine learning system that predicts NHL game outcomes using 204 engineered features including advanced metrics like Expected Goals (xG), goalie performance, schedule fatigue, and Elo ratings.

---

## 🚀 Quick Start

### Predict today (web feed)
```bash
python3 predict_full.py      # calibrated full run (slower)
```

### Run the web app
```bash
cd web
npm install
npm run dev                  # http://localhost:3000
```

### Train / analyze
```bash
python3 -m src.nhl_prediction.train          # train model
python3 analysis/feature_importance_analysis.py
python3 analysis/hyperparameter_tuning.py
```

---

## 📊 Current Performance

| Metric | Value |
|--------|-------|
| **Test Accuracy** | 60.89% |
| **ROC-AUC** | 0.6421 |
| **Log Loss** | 0.6594 |
| **Baseline (Random)** | 50.0% |
| **Baseline (Home Team)** | 53.7% |
| **Edge over Random** | **+10.89pp** |

**Training Data:** 3 seasons (2021-2024), 3,690 games
**Model:** Logistic Regression (C=0.001, decay=0.85)
**Features:** 204 total → 50 recommended (top performers)

**Data feeds powering the site**
- `web/src/data/todaysPredictions.json` (updated by `predict_full.py`)
- `web/src/data/currentStandings.json`, `goaliePulse.json`, `modelInsights.json`
- Next-game lookup for power board: `web/src/app/api/next-games` (calls NHL schedule API)

## 🔐 Secrets / Env
- X/Twitter automation: `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET` (optional `TWITTER_BEARER_TOKEN`).
- Google Analytics: gtag `G-ZSYWJKWQM3` is embedded in `web/src/app/layout.tsx`.

---

## 📁 Project Structure (cleaned)

```
puckcast/
├── README.md                # ← You are here
├── src/nhl_prediction/      # Core prediction engine
├── analysis/                # Active analysis scripts/results
├── web/                     # Next.js site (app, data feeds, assets)
├── scripts/                 # Automation/data helpers (+ run_daily.sh)
├── data/                    # Model/data assets (xg_model.pkl, cache)
├── docs/                    # Current docs + indexes
├── archive/                 # Legacy docs/dashboards
├── temp_outputs/            # Temp files (ignored)
├── requirements.txt         # Python deps
├── runtime.txt              # Runtime pin
└── model_v6_6seasons.pkl    # Pretrained model
```

---

## 🎯 Key Features

### 1. Advanced Metrics
- **Expected Goals (xG):** Custom model (94.8% accuracy) using shot location, type, rebounds
- **High-Danger Shots:** Royal Road/slot tracking
- **Goalie GSAx:** Goals Saved Above Expected

### 2. Schedule Intelligence
- Back-to-back detection
- Rest day advantages
- Travel burden tracking
- Schedule density (games in 3/6 days)

### 3. Team Strength
- Elo ratings (margin-adjusted)
- Rolling performance windows (3/5/10 games)
- Season-to-date aggregates
- Momentum indicators

### 4. Goalie Tracking
- Individual goalie stats (500 goalie-seasons)
- Starting goalie likelihood
- Recent form trends
- Rest patterns

### 5. Shot Quality
- Shannon entropy for shot diversity
- Shot type breakdown
- Rebound detection and tracking
- Danger zone analysis

---

## 📖 Documentation

### Essential Reading

| Document | Purpose | Audience |
|----------|---------|----------|
| **[FEATURE_DICTIONARY.md](FEATURE_DICTIONARY.md)** | Complete guide to all 204 features | Everyone |
| **[COMPREHENSIVE_AUDIT_V2.md](COMPREHENSIVE_AUDIT_V2.md)** | Full system audit, inventory | Developers |
| **[V2_OPTIMIZATION_RESULTS.md](V2_OPTIMIZATION_RESULTS.md)** | Latest optimization results | Data Scientists |

### Feature Documentation

**[FEATURE_DICTIONARY.md](FEATURE_DICTIONARY.md)** includes:
- All 204 features ranked by importance
- Detailed calculations and formulas
- Feature categories and groups
- Top 50 recommended features
- Zero-importance features to remove
- Best practices for feature engineering

### Analysis Results

**[V2_OPTIMIZATION_RESULTS.md](V2_OPTIMIZATION_RESULTS.md)** includes:
- Feature importance analysis
- Hyperparameter tuning (60 configurations)
- Top 50 features provide +0.81pp gain
- Optimal settings: C=1.0, decay=1.0

---

## 🧠 Model Architecture

### Pipeline Flow
```
NHL API Data
    ↓
Native Ingestion (play-by-play parsing)
    ↓
xG Model (shot quality prediction)
    ↓
Feature Engineering (204 features)
    ↓
Elo Calculations
    ↓
Goalie Features
    ↓
Game Dataframe (home vs away differentials)
    ↓
Train/Test Split (chronological)
    ↓
Logistic Regression + HistGradientBoosting
    ↓
Predictions
```

### Key Components

**Data Sources:**
- NHL Gamecenter API (play-by-play)
- GoaliePulse (goalie stats)
- Custom xG model

**Models:**
1. **xG Model:** Gradient Boosting (94.8% accuracy, 23K shots)
2. **Game Prediction:** Logistic Regression (60.89% accuracy)

**Feature Engineering:**
- 204 total features
- 17 categories
- Differentials (home - away)
- Rolling windows (3/5/10 games)
- Season aggregates
- Elo ratings

---

## 📊 Feature Importance (Top 10)

| Rank | Feature | Importance | Category |
|------|---------|------------|----------|
| 1 | rolling_high_danger_shots_3_diff | 0.0317 | Shot Quality |
| 2 | games_played_prior_away | 0.0266 | Season Progress |
| 3 | games_played_prior_home | 0.0265 | Season Progress |
| 4 | is_b2b_diff | 0.0263 | Schedule/Rest |
| 5 | goalie_rolling_gsa_diff | 0.0258 | Goalie Performance |
| 6 | shotsFor_roll_10_diff | 0.0165 | Shot Volume |
| 7 | rest_away_one_day | 0.0163 | Schedule/Rest |
| 8 | games_last_3d_diff | 0.0162 | Schedule/Rest |
| 9 | season_shot_margin_diff | 0.0160 | Shot Volume |
| 10 | rolling_goal_diff_10_diff | 0.0157 | Goal Differential |

**Key Insight:** Schedule/Rest features dominate (6 of top 20)

See [FEATURE_DICTIONARY.md](FEATURE_DICTIONARY.md) for complete rankings.

---

## 🚀 Roadmap to V2.0 Launch

### Current Status: 60.89% Accuracy

**Phase 1: Completed ✅**
- [x] Feature importance analysis
- [x] Hyperparameter optimization
- [x] Top 50 feature identification
- [x] Baseline restoration

**Phase 2: In Progress 🔄**
- [ ] Implement top 50 features
- [ ] Expand to 6 seasons (2018-2024)
- [ ] Target: 62-64% accuracy

**Phase 3: Planned ⏳**
- [ ] Real-time goalie confirmations
- [ ] Injury impact weighting
- [ ] Betting odds integration
- [ ] Target: 65-66% accuracy

**Phase 4: Launch 🎯**
- [ ] Deploy to Vercel
- [ ] Public API
- [ ] Stripe payments
- [ ] Target: 65-68% accuracy

---

## 🔧 Development

### Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Verify installation
python3 -c "from src.nhl_prediction.pipeline import build_dataset; print('✓ Setup OK')"
```

### Run Tests
```bash
# Feature importance
python3 analysis/feature_importance_analysis.py

# Hyperparameter tuning
python3 analysis/hyperparameter_tuning.py
```

### Data Pipeline
```bash
# Fetch and cache data
python3 -m src.nhl_prediction.train

# Cached data stored in: data/cache/
```

---

## 📈 Performance Tracking

### Model Versions

| Version | Accuracy | Date | Key Changes |
|---------|----------|------|-------------|
| 1.0 | 53.0% | Oct 2025 | Initial MoneyPuck data |
| 1.5 | 57.5% | Nov 2025 | Native NHL API, xG model |
| 1.8 | 59.2% | Nov 2025 | Goalie features, penalties |
| 1.9 | 60.89% | Nov 2025 | Optimized features, rebound detection |
| **2.0** | **60.89%** | **Nov 2025** | **Baseline restoration** ← Current |

**Target for Public Launch:** 65-68%

---

## 💡 Key Learnings

### What Works ✅
1. **Schedule/Rest features** - Most important category
2. **Shot quality > quantity** - High-danger shots #1 feature
3. **Goalie performance** - GSAx highly predictive
4. **Short-term form** - 3-game windows beat 10-game
5. **Less is more** - 50 features beat 204!

### What Doesn't Work ❌
1. **Line combinations** - Zero importance
2. **Too many rolling windows** - Redundant signal
3. **Special teams rolling** - Changes too slowly
4. **H2H with 3 seasons** - Insufficient data
5. **Travel distance** - Signal too weak

---

## 📞 Support

**Issues:** GitHub Issues (when public)
**Documentation:** See `/docs` folder
**Analysis:** See `/analysis` folder

---

## 📄 License

MIT License - See LICENSE file

---

## 🙏 Acknowledgments

- **NHL Gamecenter API** - Play-by-play data
- **GoaliePulse** - Goalie statistics
- **MoneyPuck** - Initial xG model inspiration

---

**Ready to predict some hockey? Run `python3 predict_tonight.py` to get started!** 🏒
