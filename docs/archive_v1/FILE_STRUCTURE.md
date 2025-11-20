# 📁 FILE STRUCTURE & ARCHITECTURE

**Complete guide to understanding the codebase organization**

---

## 🗂️ PROJECT OVERVIEW

```
NHLpredictionmodel/
├── 📊 Data Files (CSV)
├── 🐍 Python Scripts (Model & Prediction)
├── 🎨 Dashboard Files (Streamlit)
├── 📚 Documentation (Markdown)
├── 🗄️ Source Code (src/)
└── 📦 Archived Files (archive/)
```

**Total Files:** ~50  
**Lines of Code:** ~5,000+  
**Main Language:** Python  
**Framework:** Streamlit (Dashboard), scikit-learn (ML)

---

## 📊 DATA FILES

### **`data/moneypuck_all_games.csv`**
**Purpose:** Historical NHL game data (2007-2025)  
**Size:** ~220,000 lines  
**Source:** MoneyPuck.com  
**Contains:**
- Game dates, teams, scores
- Advanced metrics (xGoals, Corsi, Fenwick)
- Shot quality (high/medium/low danger)
- Score-adjusted metrics

**Key Columns:**
```
season, game_id, date, team, opp
home_or_away, gameScore, xGoalsFor, xGoalsAgainst
corsiFor, corsiAgainst, fenwickFor, fenwickAgainst
shotsOnGoalFor, shotsOnGoalAgainst
highDangerShotsFor, mediumDangerShotsFor, lowDangerShotsFor
```

**Used By:**
- `data_ingest.py` (loads this)
- `pipeline.py` (processes this)
- `model.py` (trains on this)

---

### **`data/moneypuck_goalies.csv`**
**Purpose:** Goaltender statistics by game  
**Source:** MoneyPuck.com  
**Contains:**
- Goalie names, teams, dates
- Save percentage
- Goals Saved Above Expected (GSAx)
- Shots faced, goals allowed

**Key Columns:**
```
season, game_id, date, team, name
xGoals, goals, shotsOnGoal, savePercentage
xGoalsAgainst60, goalsAgainst60
```

**Used By:**
- `data_ingest.py` (loads and merges with games)
- `features.py` (calculates rolling goalie stats)

---

### **`predictions_YYYY-MM-DD.csv`**
**Purpose:** Daily prediction outputs  
**Created By:** `predict_full.py`  
**Format:**
```csv
date,away_team,home_team,away_prob,home_prob,pred_winner,confidence
2025-11-10,BOS,TOR,0.42,0.58,TOR,8.0
```

**Columns:**
- `date`: Game date
- `away_team`: Away team abbreviation
- `home_team`: Home team abbreviation
- `away_prob`: Away team win probability (0-1)
- `home_prob`: Home team win probability (0-1)
- `pred_winner`: Predicted winner (team abbr)
- `confidence`: Edge % (|home_prob - 0.5| * 100)

**Used By:**
- `dashboard_billion.py` (reads for display)

---

## 🐍 PYTHON SCRIPTS (Root Level)

### **`predict_full.py`** ⭐ KEY FILE
**Purpose:** Generate predictions for any date  
**Lines:** ~220  
**Usage:**
```bash
python predict_full.py              # Today
python predict_full.py 2025-11-15   # Specific date
```

**What it does:**
1. Loads historical data (MoneyPuck)
2. Builds full dataset with 141 features
3. Trains model on 2021-2024 seasons
4. Fetches today's schedule from NHL API
5. Generates predictions for each game
6. Saves to CSV file
7. Displays formatted output

**Dependencies:**
- `src.nhl_prediction.pipeline`
- `src.nhl_prediction.model`
- `src.nhl_prediction.nhl_api`
- `typer` (CLI)
- `rich` (pretty printing)

---

### **`predict_tonight.py`**
**Purpose:** Simplified quick predictions  
**Lines:** ~137  
**Usage:**
```bash
python predict_tonight.py
```

**Difference from predict_full.py:**
- Simpler output
- No CSV export
- Faster execution
- Less detailed stats

---

### **`dashboard.py`** (Legacy)
**Purpose:** Original Streamlit dashboard  
**Status:** Superseded by `dashboard_billion.py`  
**Lines:** ~800  
**Note:** Still functional, but not recommended

---

### **`dashboard_billion.py`** ⭐ KEY FILE
**Purpose:** Elite production dashboard  
**Lines:** 2,110  
**Usage:**
```bash
streamlit run dashboard_billion.py
```

**Pages (7 total):**
1. 🏠 Command Center
2. 🎯 Today's Predictions
3. 💰 Betting Simulator
4. 📈 Performance Analytics
5. 🔬 Deep Analysis
6. 🏆 Leaderboards
7. ❓ Help

**Key Features:**
- 30+ widgets and visualizations
- 15+ Altair charts
- Custom CSS animations
- Real-time calculations
- Caching for performance
- Error handling

**Dependencies:**
- `streamlit`
- `pandas`, `numpy`
- `altair` (charts)
- `src.nhl_prediction.*` (model)

**Technical Details:**
- Uses `@st.cache_data` for performance
- Custom CSS with glassmorphism
- Responsive design
- ~1GB memory usage with full dataset

---

### **`create_visualizations.py`**
**Purpose:** Generate static visualizations  
**Lines:** ~639  
**Usage:**
```bash
python create_visualizations.py
```

**Creates:**
1. Calibration curves
2. ROC curves
3. Feature importance charts
4. Confusion matrices
5. Team performance heatmaps
6. Betting ROI curves

**Saves to:** `docs/images/` or current directory

**Note:** Mostly for report generation, not daily use

---

## 🗄️ SOURCE CODE (`src/nhl_prediction/`)

### **`src/nhl_prediction/data_ingest.py`**
**Purpose:** Load and preprocess data  
**Key Functions:**
- `fetch_all_games(seasons)` - Load MoneyPuck games
- `fetch_goalie_stats(seasons)` - Load goalie data
- `merge_goalie_stats()` - Combine games + goalies

**Process:**
1. Read CSV files
2. Parse dates
3. Standardize team names
4. Handle missing values
5. Merge datasets

---

### **`src/nhl_prediction/features.py`**
**Purpose:** Feature engineering  
**Key Functions:**
- `calculate_elo_ratings()` - Team strength
- `calculate_rolling_averages()` - Recent form
- `calculate_rest_features()` - Back-to-back games
- `calculate_goalie_features()` - Goaltending quality

**Creates 141 features:**
- Elo ratings (2 features)
- Rolling averages (100+ features)
  - 3, 5, 10 game windows
  - xGoals, Corsi, Fenwick, shots
  - High/medium/low danger shots
- Rest features (5 features)
  - `is_b2b_home`, `is_b2b_away`
  - `is_b2b_diff`, `home_b2b`, `away_b2b`
- Goalie features (10+ features)
  - Save %, GSAx/60
  - Rolling goalie stats
- Differential features (20+ features)
  - Home - Away for all metrics

---

### **`src/nhl_prediction/pipeline.py`**
**Purpose:** End-to-end data pipeline  
**Key Functions:**
- `build_dataset(seasons)` - Full pipeline
- Returns: `Dataset` object with features, target, games

**Process:**
1. Load data (data_ingest)
2. Calculate Elo (features)
3. Calculate rolling stats (features)
4. Calculate rest features (features)
5. Calculate goalie features (features)
6. Create differentials
7. Remove NaN rows
8. Return structured dataset

**Dataset Object:**
```python
Dataset(
    features: pd.DataFrame,  # 141 columns
    target: pd.Series,       # home_win (0/1)
    games: pd.DataFrame      # metadata (teams, dates)
)
```

---

### **`src/nhl_prediction/model.py`**
**Purpose:** ML model training and evaluation  
**Key Functions:**
- `create_baseline_model()` - Logistic Regression
- `fit_model()` - Train model
- `evaluate_model()` - Calculate metrics
- `calculate_feature_importance()` - Top features

**Model Details:**
- Algorithm: Logistic Regression
- Regularization: C=1.0
- Solver: lbfgs
- Max iterations: 1000
- Class weight: balanced

**Metrics Calculated:**
- Accuracy
- ROC-AUC
- Log Loss
- Brier Score
- Confusion Matrix
- Feature Importance

---

### **`src/nhl_prediction/nhl_api.py`**
**Purpose:** Interact with NHL Stats API  
**Key Functions:**
- `fetch_schedule(date)` - Get day's games
- `fetch_starting_goalies(date)` - Get confirmed goalies
- `get_team_abbreviation()` - Standardize names

**API Endpoints:**
- Schedule: `https://api-web.nhle.com/v1/schedule/{date}`
- Team info: NHL Stats API

**Returns:**
```python
[
    {
        'date': '2025-11-10',
        'away_team': 'BOS',
        'home_team': 'TOR',
        'game_id': 2025020XXX
    },
    ...
]
```

**Note:** Only for schedules, not game data (uses MoneyPuck for that)

---

## 📚 DOCUMENTATION FILES

### **`README.md`**
**Purpose:** Main project documentation  
**Lines:** ~412  
**Contains:**
- Project overview
- Installation instructions
- Usage examples
- Technical details
- Model architecture

**Audience:** Developers, instructors, collaborators

---

### **`docs/group_report_2.md`** ⭐ KEY FILE
**Purpose:** Academic group project report  
**Lines:** ~1,126  
**Contains:**
- Executive Summary
- Introduction & Objectives
- Data Sources
- Feature Engineering (detailed)
- Model Development
- Evaluation & Results
- Challenges & Solutions
- Reflection & Learnings
- Future Work
- Conclusion

**Audience:** Instructors, grading, submission

**Key Sections:**
1. **Executive Summary** - High-level overview
2. **Feature Engineering** - 141 features explained
3. **Model Development** - Algorithm choice
4. **Evaluation** - 59.2% accuracy, metrics
5. **Reflection** - What we learned
6. **Future Work** - Betting integration plans

---

### **`USER_GUIDE.md`** ⭐ KEY FILE
**Purpose:** Complete user documentation  
**Lines:** ~800  
**Contains:**
- Installation guide
- Daily workflows
- Dashboard page-by-page guide
- Prediction interpretation
- Betting strategies
- Troubleshooting
- FAQ
- Advanced usage

**Audience:** End users, daily users

---

### **`QUICK_REFERENCE_CARD.md`**
**Purpose:** Cheat sheet for daily use  
**Lines:** ~300  
**Contains:**
- Essential commands
- Dashboard navigation
- Confidence levels
- Model stats
- Pro tips
- Troubleshooting

**Audience:** Daily users who need quick answers

---

### **`TESTING_CHECKLIST.md`**
**Purpose:** Comprehensive testing guide  
**Lines:** ~400  
**Contains:**
- 25 test sections
- Pre-flight checks
- Core model testing
- Dashboard testing (all 7 pages)
- Stress testing
- Data integrity checks
- Acceptance criteria

**Audience:** Developers, QA, before deployment

---

### **`FILE_STRUCTURE.md`** (This File)
**Purpose:** Architecture documentation  
**Contains:**
- File descriptions
- Code organization
- Dependencies
- Data flow
- Technical specs

**Audience:** New developers, collaborators

---

## 📦 ARCHIVED FILES (`archive/`)

**Contains:**
- Old reports
- Deprecated scripts
- Historical documentation
- Testing artifacts

**Examples:**
- `DASHBOARD_ENHANCEMENTS.md`
- `DASHBOARD_COMPLETE.md`
- Old prediction scripts
- Test files

**Purpose:** Keep main directory clean while preserving history

---

## 🔄 DATA FLOW

### **Training Flow**
```
1. data/moneypuck_all_games.csv
   ↓
2. data_ingest.py → Load & preprocess
   ↓
3. features.py → Engineer 141 features
   ↓
4. pipeline.py → Combine everything
   ↓
5. model.py → Train Logistic Regression
   ↓
6. Save trained model (in memory)
```

### **Prediction Flow**
```
1. nhl_api.py → Fetch today's schedule
   ↓
2. pipeline.py → Load historical + build features
   ↓
3. model.py → Load trained model
   ↓
4. For each game:
   - Build feature vector
   - Predict probability
   - Calculate confidence
   ↓
5. Save to predictions_YYYY-MM-DD.csv
```

### **Dashboard Flow**
```
1. dashboard_billion.py starts
   ↓
2. Load predictions_YYYY-MM-DD.csv
   ↓
3. Load historical data (for analytics)
   ↓
4. Build dataset (for feature analysis)
   ↓
5. Train model (for coefficients)
   ↓
6. Cache everything
   ↓
7. Render pages based on user navigation
```

---

## 🔗 DEPENDENCIES

### **External Python Packages**
```
pandas          # Data manipulation
numpy           # Numerical operations
scikit-learn    # Machine learning
streamlit       # Dashboard
altair          # Interactive charts
requests        # API calls
typer           # CLI (predict_full.py)
rich            # Pretty printing
matplotlib      # Static visualizations (optional)
```

### **Internal Dependencies**
```
predict_full.py
├── src.nhl_prediction.pipeline
├── src.nhl_prediction.model
├── src.nhl_prediction.nhl_api
└── typer, rich

dashboard_billion.py
├── src.nhl_prediction.pipeline
├── src.nhl_prediction.model
├── src.nhl_prediction.features
└── streamlit, altair, pandas

pipeline.py
├── data_ingest.py
└── features.py

features.py
└── (standalone)

model.py
└── scikit-learn
```

---

## 📏 CODE METRICS

**Lines of Code by File:**
```
dashboard_billion.py        2,110 lines
group_report_2.md          1,126 lines
USER_GUIDE.md                800 lines
create_visualizations.py     639 lines
README.md                    412 lines
QUICK_REFERENCE_CARD.md      300 lines
predict_full.py              220 lines
predict_tonight.py           137 lines
features.py                  ~300 lines
pipeline.py                  ~200 lines
model.py                     ~150 lines
data_ingest.py              ~150 lines
nhl_api.py                   ~100 lines
```

**Total:** ~6,644 lines of code + documentation

---

## 🎯 KEY FILES FOR DIFFERENT TASKS

### **Daily Predictions**
- `predict_full.py` ⭐
- `src/nhl_prediction/nhl_api.py`
- `data/moneypuck_all_games.csv`

### **Dashboard Usage**
- `dashboard_billion.py` ⭐
- `predictions_YYYY-MM-DD.csv`
- `data/moneypuck_all_games.csv`

### **Model Development**
- `src/nhl_prediction/model.py` ⭐
- `src/nhl_prediction/features.py` ⭐
- `src/nhl_prediction/pipeline.py`

### **Academic Report**
- `docs/group_report_2.md` ⭐
- `create_visualizations.py`

### **User Documentation**
- `USER_GUIDE.md` ⭐
- `QUICK_REFERENCE_CARD.md`
- `README.md`

### **Testing**
- `TESTING_CHECKLIST.md` ⭐

---

## 🧱 ARCHITECTURE PRINCIPLES

**1. Modularity**
- Separate files for data, features, model, API
- Easy to modify one part without breaking others

**2. Pipeline-Based**
- Clear data flow: ingest → features → model → predictions
- Reproducible results

**3. Caching**
- Dashboard uses `@st.cache_data` for performance
- Predictions saved to CSV (no re-calculation needed)

**4. Documentation**
- Every major component has documentation
- Code comments for complex logic
- User guides for end users

**5. Separation of Concerns**
- Data loading: `data_ingest.py`
- Feature engineering: `features.py`
- ML model: `model.py`
- API interaction: `nhl_api.py`
- Orchestration: `pipeline.py`
- User interface: `dashboard_billion.py`

---

## 🔮 FUTURE ADDITIONS

**Potential New Files:**
- `src/nhl_prediction/betting.py` - Betting logic
- `src/nhl_prediction/injuries.py` - Injury data scraping
- `tests/test_*.py` - Unit tests
- `requirements.txt` - Package versions
- `config.yaml` - Configuration settings
- `api/server.py` - REST API (for deployment)

---

## 📝 NAMING CONVENTIONS

**Files:**
- Lowercase with underscores: `predict_full.py`
- Descriptive names: `create_visualizations.py`
- Documentation: ALL_CAPS.md or TitleCase.md

**Functions:**
- Snake case: `fetch_all_games()`
- Verb-first: `calculate_elo_ratings()`
- Descriptive: `build_dataset()`

**Variables:**
- Snake case: `home_win_prob`
- Descriptive: `rolling_corsi_10_diff`
- Boolean prefix: `is_b2b_home`

**Classes:**
- Pascal case: `Dataset`
- Noun-based: `GamePredictor`

---

## 🎓 LEARNING THE CODEBASE

**For New Users:**
1. Read `README.md`
2. Read `USER_GUIDE.md`
3. Run `predict_full.py`
4. Open `dashboard_billion.py`

**For Developers:**
1. Read `FILE_STRUCTURE.md` (this file)
2. Read `src/nhl_prediction/pipeline.py`
3. Review `src/nhl_prediction/features.py`
4. Study `src/nhl_prediction/model.py`
5. Trace data flow

**For Modifying Model:**
1. Understand `features.py` (feature engineering)
2. Modify or add features
3. Update `model.py` (if changing algorithm)
4. Test with `predict_full.py`
5. Verify in `dashboard_billion.py`

---

## 🚀 DEPLOYMENT CONSIDERATIONS

**For Production:**
- Move to `requirements.txt` for packages
- Add logging (`logging` module)
- Environment variables for API keys
- Database for historical predictions
- Scheduled jobs (cron) for daily predictions
- Docker container for deployment
- CI/CD pipeline

**For Sharing:**
- Include `requirements.txt`
- Provide sample data
- Clear README instructions
- Document API keys needed (NHL API is public)

---

## ✅ FILE CHECKLIST

**Before Submission/Deployment:**
- [ ] All scripts run without errors
- [ ] Documentation is up-to-date
- [ ] No hardcoded paths (use relative)
- [ ] No API keys in code (use environment vars)
- [ ] README has clear instructions
- [ ] Group report is complete
- [ ] Dashboard works on fresh machine
- [ ] Predictions generate correctly
- [ ] All dependencies listed

---

**FILE STRUCTURE DOCUMENTATION v2.0**  
**Last Updated:** November 10, 2025  
**Status:** Complete

**Now you understand the entire codebase architecture!** 📚✨


