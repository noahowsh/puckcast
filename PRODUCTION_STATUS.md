# 🏒 Puckcast.ai - Production Status & Active Files

> **Last Updated**: December 7, 2025
> **Model Version**: V7.0 (Adaptive Weights)
> **Website**: https://puckcast.ai
> **Status**: ✅ **PRODUCTION - LIVE**

---

## 📊 Production Model Stats

| Metric | Value |
|--------|-------|
| **Model** | V7.0 Adaptive Weights |
| **Accuracy** | 60.9% (4-season holdout) |
| **Games Tested** | 5,002 |
| **Features** | 39 + adaptive weights |
| **Test Set** | 4-season holdout (2021-25) |
| **Baseline** | 53.9% (home win rate) |
| **Edge vs Baseline** | +6.9 pts |
| **Brier Score** | 0.2317 |
| **Log Loss** | 0.6554 |

---

## 🎯 Active Production Files

### **Core Prediction System**

#### `prediction/predict_full.py`
- **Status**: ✅ PRODUCTION
- **Purpose**: Daily prediction generation with V7.0 model
- **Updates**: December 2025
- **Features**: 39 + adaptive weights
- **Output**: Generates `todaysPredictions.json` for frontend

#### `prediction/predict_simple.py`
- **Status**: ✅ Active
- **Purpose**: CLI-based quick predictions
- **Use Case**: Manual/ad-hoc predictions

#### `prediction/predict_tonight.py`
- **Status**: ✅ Active
- **Purpose**: Simplified daily prediction script
- **Use Case**: Automated daily runs

---

### **Model Training**

#### `training/train_v7_adaptive.py`
- **Status**: ✅ PRODUCTION
- **Last Updated**: December 2025
- **Purpose**: Training script for V7.0 model with adaptive weights
- **Results**: 60.9% accuracy on 4-season holdout (5,002 games)
- **Training Time**: ~5-10 minutes on local machine
- **Output**: Trained model pickle file

---

### **Core Python Modules** (`src/nhl_prediction/`)

#### `pipeline.py`
- **Status**: ✅ Production
- **Purpose**: Feature engineering pipeline
- **Features Generated**: 213 baseline features
- **Last Updated**: December 2024

#### `situational_features.py`
- **Status**: ✅ Production - V7.0 Core
- **Purpose**: V7.0 situational feature generation
- **Features**: Part of 39-feature core set with adaptive weights

#### `model.py`
- **Status**: ✅ Production
- **Purpose**: Model training and prediction logic
- **Algorithms**: Logistic Regression, Isotonic Calibration

#### `nhl_api.py`
- **Status**: ✅ Production
- **Purpose**: NHL API client for live game data
- **Functions**:
  - `fetch_schedule()` - Get game schedules
  - `fetch_future_games()` - Get upcoming games
  - `fetch_todays_games()` - Today's games only

#### `data_ingest.py` & `native_ingest.py`
- **Status**: ✅ Production
- **Purpose**: Historical NHL data ingestion
- **Use**: Training data preparation

#### `features.py`
- **Status**: ✅ Production
- **Purpose**: Feature extraction and engineering helpers

---

### **Frontend** (`web/`)

#### Data Files (`web/src/data/`)
- `modelInsights.json` - V7.0 model statistics and confidence buckets
- `todaysPredictions.json` - Daily predictions (10 games on Dec 4)
- `currentStandings.json` - NHL standings
- `goaliePulse.json` - Goalie statistics
- `startingGoalies.json` - Confirmed starting goalies
- `playerInjuries.json` - Injury reports
- `lineCombos.json` - Line combinations

#### Pages (`web/src/app/`)
- `/` - Home/Overview page
- `/predictions` - Daily predictions slate (clickable cards)
- `/matchup/[gameId]` - H2H matchup detail with team comparison
- `/performance` - Model performance metrics
- `/leaderboards` - Power rankings
- `/teams` - Team index
- `/teams/[abbrev]` - Individual team pages (with PP/PK stats)

#### Components (`web/src/components/`)
- `SiteFooter.tsx` - Footer with V7.0 version
- `TeamCrest.tsx` - Team logos
- `PageHeader.tsx` - Page headers
- `StatCard.tsx` - Stat display cards

---

### **Scripts** (`scripts/`)

#### Active Production Scripts:
- `refresh_site_data.py` - Updates all frontend data files
- `fetch_current_standings.py` - NHL standings refresh
- `fetch_starting_goalies.py` - Goalie confirmations
- `fetch_injuries.py` - Player injury updates
- `generate_goalie_pulse.py` - Goalie stats generation
- `validate_predictions.py` - Prediction data validation
- `validate_data_schemas.py` - Schema validation

#### Automation Scripts (GitHub Actions):
- **Not yet set up** - Future: Daily automated prediction generation

---

### **Analysis Scripts** (`analysis/`)

#### Active Analysis:
- `current/analyze_v7_3_errors.py` - Error analysis for V7.3
- `current/analyze_b2b_weakness.py` - Back-to-back game analysis
- `current/analyze_confidence_calibration.py` - Calibration analysis
- `feature_importance_analysis.py` - Feature rankings
- `hyperparameter_tuning.py` - Model optimization

---

### **Documentation** (`docs/`)

#### Active Documentation:
- `current/CLOSING_GAP_ANALYSIS.md` - Analysis of attempts to reach 62%
- `PUCKCAST_V7_SPEC.md` - V7 series specifications
- `INDEX.md` - Documentation index
- `ROOT_MAP.md` - Repository structure
- `AUTOMATION_SETUP.md` - Automation guide
- `GH_ACTIONS.md` - GitHub Actions setup

---

## 🗑️ Recently Archived (December 4, 2024)

All archived to: `archive/2024-12-04-pre-v7.3-cleanup/`

### Archived Experimental Features:
- `head_to_head_features.py` - V7.4 experiment (60.00% accuracy ❌)
- `interaction_features.py` - V7.5 experiment (60.08% accuracy ❌)
- `team_calibration_features.py` - V7.6 experiment (60.73% accuracy ❌)

### Archived Training Scripts:
- All V7.1, V7.2, V7.4, V7.5, V7.6 training scripts
- Old training experiments from `/training/archive/`
- Experimental training scripts from `/training/experiments/`

### Archived Docs:
- All `/docs/archive/` and `/docs/archive_v1/` content
- Old dashboard documentation
- Legacy project summaries and status files

### Archived Systems:
- `goalie_system/` - Old goalie database builders (replaced by native ingest)
- Legacy dashboard Python files
- Old visualization scripts

---

## 🚀 Deployment Status

### Frontend (puckcast.ai)
- **Status**: ✅ Live
- **Hosting**: [To be determined - Vercel/Netlify]
- **Updates**: Manual - Copy predictions to `web/src/data/`
- **Version**: v7.0 (shown in footer)

### Prediction Generation
- **Status**: ✅ Manual
- **Frequency**: Daily at ~11:00 AM UTC (6:00 AM ET)
- **Command**: `python prediction/predict_full.py`
- **Duration**: ~5-6 minutes (NHL API dependent)

### Data Refresh
- **Status**: ⚠️ Manual
- **Scripts**: `scripts/refresh_site_data.py`
- **Frequency**: As needed for standings/injuries/goalies

---

## 📝 Next Steps & Future Improvements

### Short Term (Week 1-2):
1. ✅ **DONE**: V7.3 model deployed to production
2. ✅ **DONE**: Frontend fully integrated with V7.3 stats
3. ⏳ **TODO**: Set up automated daily prediction generation
4. ⏳ **TODO**: Deploy to Vercel/Netlify with custom domain

### Medium Term (Month 1-2):
1. Implement GitHub Actions for automated predictions
2. Add X/Twitter integration for daily picks posting
3. Create comprehensive site documentation page
4. Add historical prediction tracking

### Long Term (3+ months):
1. Explore ensemble methods (V8.0)
2. Add neural network models (V8.1)
3. Implement real-time updates during games
4. Add user accounts and personalization

---

## 🔧 Maintenance Notes

### Daily Tasks:
- Run `python prediction/predict_full.py` at 11:00 AM UTC
- Copy `prediction/web/src/data/todaysPredictions.json` → `web/src/data/`
- Verify frontend displays predictions correctly

### Weekly Tasks:
- Update standings: `python scripts/fetch_current_standings.py`
- Refresh goalie stats: `python scripts/generate_goalie_pulse.py`
- Check injury updates: `python scripts/fetch_injuries.py`

### As-Needed Tasks:
- Retrain model if new seasons available: `python training/train_v7_adaptive.py`
- Update frontend content (About page, etc.)
- Validate prediction schemas: `python scripts/validate_predictions.py`

---

## 📊 Performance Benchmarks

### V7.0 Model Performance:
```
Test Set: 4-season holdout (5,002 games)
Overall Accuracy: 60.9%
Baseline (Home Win Rate): 53.9%
Improvement: +6.9 percentage points

Confidence Buckets:
A+ (25+ pts): 79.3% accuracy (333 games)
A  (20-25 pts): 72.0% accuracy (404 games)
B+ (15-20 pts): 67.3% accuracy (687 games)
B  (10-15 pts): 62.0% accuracy (975 games)
C+ (5-10 pts): 57.8% accuracy (1,231 games)
C  (0-5 pts): 51.9% accuracy (1,372 games)
```

### Calibration:
- **Brier Score**: 0.2317
- **Log Loss**: 0.6554
- **Features**: 39 + adaptive weights

---

## 📞 Contact & Support

- **Repository**: Private GitHub repo
- **Branch**: `claude/v7-beta-01111xrERXjGtBfF6RaMBsNr`
- **Owner**: OWSH Unlimited LLC
- **Website**: https://puckcast.ai
- **X/Twitter**: @puckcastai

---

**Document Version**: 2.0
**Last Audit**: December 7, 2025
**Next Review**: After V8 or major updates
