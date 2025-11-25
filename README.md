# 🏒 Puckcast - NHL Game Prediction System

**Version:** 6.2  
**Model:** Logistic Regression (isotonic-calibrated) on 206 engineered features  
**Training Window:** 3 most recent seasons (auto-advances; currently 2023–2026)  
**Current holdout (from `web/src/data/modelInsights.json`):** 59.3% accuracy vs 53.7% baseline, log loss 0.676, Brier 0.240  
**Status:** Active Development

Puckcast predicts NHL outcomes using MoneyPuck team-game logs, custom feature engineering (rest/travel, xG, special teams, goalie form, Elo), and a calibrated logistic model. The Next.js site consumes the exported JSON payloads for the daily slate.

---

## 🚀 Quick Start

### Predict today (web feed)
```bash
python3 predict_full.py      # generates predictions_YYYY-MM-DD.csv + web/src/data/todaysPredictions.json
```

### Run the web app
```bash
cd web
npm install
npm run dev                  # http://localhost:3000
```

### Train / analyze (advanced)
```bash
# Full dataset build + training utilities live under src/nhl_prediction
python3 analysis/feature_importance_analysis.py   # optional, requires cached data
# Training entrypoints are currently prediction-focused; historical backtests use scripts/fetch_results.py + archives
```

---

## 📊 Current Performance (live payload)

- Accuracy: **59.3%** (holdout in `modelInsights.json`)
- Baseline (home team rate): **53.7%**
- Log loss: **0.676**
- Brier: **0.240**
- Avg edge: **16.1 pts** (vs coin flip)

Feeds powering the site:
- `web/src/data/todaysPredictions.json` (daily slate, updated by `predict_full.py` + actions)
- `web/src/data/modelInsights.json` (holdout metrics, confidence buckets)
- `web/src/data/currentStandings.json`, `goaliePulse.json`
- Next-game lookup for the power board: `web/src/app/api/next-games` (NHL schedule API)

## 🔐 Secrets / Env
- X/Twitter automation: `TWITTER_API_KEY`, `TWITTER_API_SECRET`, `TWITTER_ACCESS_TOKEN`, `TWITTER_ACCESS_SECRET` (optional `TWITTER_BEARER_TOKEN`).
- Google Analytics: gtag `G-ZSYWJKWQM3` is embedded in `web/src/app/layout.tsx`.

---

## 📁 Project Structure (current)

```
puckcast/
├── README.md                # ← You are here
├── src/nhl_prediction/      # Core prediction engine (pipeline, features, model helpers, NHL API client)
├── analysis/                # Analysis scripts/results (feature importance, hyperparam sweeps)
├── web/                     # Next.js site (app router, components, data feeds in web/src/data)
├── scripts/                 # Automation helpers (Twitter posting, validation, backtesting)
├── data/                    # Static assets (MoneyPuck, team metadata), archives of predictions/results
├── docs/                    # Current docs + roadmap (see docs/INDEX.md)
├── archive/                 # Legacy docs/dashboards
├── requirements.txt         # Python deps
├── runtime.txt              # Runtime pin (Heroku/Render style)
└── model_v6_6seasons.pkl    # Pretrained model artifact
```

---

## 🎯 Model + Features (current)

- **Features:** 206 engineered features (differentials and dummies) built from MoneyPuck team-game logs:
  - Rest/travel: rest buckets, b2b flags, games in last 3/6 days, travel burden, altitude.
  - Performance windows: rolling win%, goal diff, shots/corsi/fenwick, xG, special teams proxies.
  - Goalie form: rolling save%, GSAX, shots faced, start likelihood, rest days.
  - Elo: margin-adjusted Elo with home-ice baked in.
  - Team IDs as dummies for capture of residual strength.
- **Model:** Logistic Regression (StandardScaler + LBFGS), hyperparameter C tuned on penultimate season; isotonic calibration on the most recent validation season.
- **Edge definition:** `(favorite_prob - 0.5)`; grades map to bands (C <2 pts, C+ 2–3, B- 4–6, B 7–9, B+ 10–13, A- 15–20, A+ ≥20).
- **Output:** Raw probabilities are used for display and edge/grade; calibrated probs retained in the payload for analysis.

---

## 📖 Documentation

## 📖 Documentation (pointers)

- **docs/INDEX.md** – current doc map and where to look.
- **docs/ROOT_MAP.md** – high-level system map.
- **docs/puckcast7_plan.md** – roadmap toward 7.0 (updated with calibration refresh notes).
- **scripts/README.md** – helper scripts, validation, archives.
- Legacy/archived docs live under `docs/archive` and `archive/`.

---

## 🧠 Pipeline (current)

```
MoneyPuck team-game logs (3 seasons) + team metadata
    ↓
Feature engineering (rest/travel, rolling stats, xG, Elo, goalie form, dummies)
    ↓
Train logistic regression (chronological split; last season for validation)
    ↓
Isotonic calibration on validation season
    ↓
Predict future schedule (fetch_schedule/fetch_future_games)
    ↓
Export CSV + web/src/data/todaysPredictions.json
```

Notes:
- Raw probs drive edge/grades; calibrated probs also exported.
- Archives: `data/archive/predictions/predictions_YYYY-MM-DD.json` + CSV for backtests.

## 🤖 Automation (GitHub Actions)

- `scheduled-data-refresh.yml` – predictions/standings/goalie pulse/model insights (AM/PM) with rebase-before-push.
- `daily-predictions.yml` – morning prediction run (may be redundant; see refresh).
- `fetch-results.yml` – pulls final scores, updates archives/backtesting (creates placeholder report if none).
- `twitter-daily.yml` – 4-slot X posting (morning slate, team highlight, prior-day results recap, tomorrow tease).

## 🌐 Frontend

- Next.js (app router) under `web/`.
- Data fed via `web/src/data/*.json` generated by scripts/actions.
- Edge and grades on the site use raw probabilities (edge = |prob - 0.5|).

## ⚡ Quick Facts

- Current slate data: `web/src/data/todaysPredictions.json` (regenerated each run).
- Confidence ladder bands: 0–5 (C), 5–10 (B-), 10–15 (B+), 15–20 (A-), 20+ (A+).
- Version badge on site footer: v6.2.
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
