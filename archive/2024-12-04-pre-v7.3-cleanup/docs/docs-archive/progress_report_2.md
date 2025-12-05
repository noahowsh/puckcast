MGQ610 Sports Analytics  
Group 1 – The Underdogs  
Progress Report 2 (Python Migration & Expanded Modeling)  
Members: Natalie Brown, Bailey Hardick, Noah Owsiany, Jessica Souder, Kelsey Wagner  

---

### 1. What Changed Since Progress Report 1
- **Full code migration from R to Python**: Rebuilt the pipeline as a modular package (`src/nhl_prediction/`) with clear separation between data ingest, feature engineering, modeling, reporting, and betting utilities.
- **Expanded historical data coverage**: Instead of a single Kaggle season, we now ingest multi-season MoneyPuck game summaries (2021-22, 2022-23 for training and 2023-24 for testing), eliminating the data scarcity pain point.
- **Richer feature set**: Engineered 120+ lagged, rolling, and situational features per matchup (rest buckets, Elo ratings, special teams matchups, congestion indicators) to better capture team strength and context.
- **Model comparison framework**: Added automated comparison between a calibrated logistic regression baseline and a histogram-based gradient boosting model, each tuned with a chronological validation split.
- **Prediction analysis tooling**: Generated season-long predictions (`reports/predictions_20232024.csv`) plus calibration, confidence, and error diagnostics via `src/nhl_prediction/create_prediction_analysis.py`.

---

### 2. Updated Data Sources
| Source | Purpose | Status |
| --- | --- | --- |
| **MoneyPuck season aggregates** (`src/nhl_prediction/data_ingest.py`) | Primary game-by-game features (team goal share, special teams, shot metrics, rest) for 2021-24 seasons | Local CSV/Parquet downloads ingested and standardized |
| **Team metadata lookup** (`data/nhl_teams.csv`) | Stable mapping between MoneyPuck abbreviations, NHL IDs, divisions | Loaded at ingest to join opponents & conferences |
| **MoneyPuck + other historical odds repositories** | Supplemental advanced metrics & betting lines | Under evaluation; currently referenced for feature ideas |
| **Sportsbook odds archives / APIs** (`docs/betting_integration_plan.md`) | Closing line odds for ROI testing | Design finalized, implementation in progress |

---

### 3. Work Completed This Cycle
**Data engineering**
- `fetch_multi_season_logs()` now loads MoneyPuck exports for each season, normalizes column names, and ensures consistent typing and timestamp handling.
- `engineer_team_features()` adds lagged rolling averages for wins, goal differential, special teams, shot share, rest, congestion, and momentum deltas while preventing leakage (`shift(1)` everywhere).
- `build_game_dataframe()` pairs home/away teams into single rows and tags each observation with `home_win`, actual scores, and derived Elo ratings.

**Model development & evaluation**
- Added chronological train/validation/test splitting inside `train.py`, ensuring the final training season (2022-23) doubles as validation for hyperparameter tuning.
- Implemented tuning utilities (`tune_logreg_c`, `tune_histgb_params`) and a comparison routine that selects the better-performing model based on validation accuracy/log-loss and then reports calibrated probabilities.
- Current 2023-24 holdout metrics (from `reports/predictions_20232024.csv`): **Accuracy 62.2%**, **ROC-AUC 0.657**, **Log Loss 0.670**, **Brier 0.236**, vs. a 50.3% “always pick home” baseline.

**Visualization & reporting**
- Created reusable analysis plots (confidence buckets, calibration, probability distribution, error pie chart) saved to `reports/` for use in presentations.
- Produced a comprehensive `README` plus technical docs (`docs/taxonomy.md`, `docs/usage.md`) to onboard new contributors to the Python stack quickly.

**Betting workflow groundwork**
- Authored `docs/betting_integration_plan.md` detailing odds ingestion options, vig removal, +EV detection, bet sizing, and ROI metrics.
- Drafted `betting.py` scaffolding (value bet filters, Kelly sizing hooks) to plug in real odds once sourced.

---

### 4. Steps to Completion
1. **Finish odds ingestion (Week 1)**  
   - Select a historical odds source (Odds API archive or vetted Kaggle file) and map odds to `gameId`.  
   - Implement vig adjustment + implied probability columns inside a new odds ETL script.
2. **Integrate betting strategy module (Week 2)**  
   - Merge odds with model outputs, flag +EV games, and simulate unit-stake vs. fractional Kelly bets.  
   - Log bankroll trajectories, ROI, Sharpe, and drawdowns for report visuals.
3. **Model refinement & validation (Week 2)**  
   - Run feature ablation tests, try calibrated thresholds from validation (currently recommending ~0.62) on 2023-24 data, and export updated metrics.
4. **Deliverables & presentation (Week 3)**  
   - Update Streamlit dashboard with odds overlays, embed new plots, and finalize written report + slide deck tying insights to sports analytics/business impact.

---

### 5. Current Pain Points / Needs
- **Odds availability**: Closing-line data with consistent identifiers is harder to source than expected; evaluating whether to pay for Odds API history or rely on archived CSVs.
- **MoneyPuck refresh cadence**: Large file downloads need occasional manual updates; we plan to cache processed Parquet files so we are not re-parsing the raw CSVs each run.
- **Computation time**: Feature engineering plus gradient boosting on ~3K games is manageable but slow on laptops; may leverage caching of engineered logs to speed iteration.
- **Validation rigor**: Need to guard against overfitting when we re-tune after adding odds-derived features; plan to lock the 2023-24 season as the only test set and potentially reserve 2024 playoffs for final sanity checks.

---

### 6. Outlook
We achieved the big structural goals we set after Progress Report 1: richer data, a modern Python codebase, and materially better predictive power. The remaining focus is integrating betting market data so we can quantify whether our edge translates into sustainable positive expected value. Once odds are merged, we will run the ROI simulations outlined above and use those findings to drive the final narrative on market efficiency vs. our model.
