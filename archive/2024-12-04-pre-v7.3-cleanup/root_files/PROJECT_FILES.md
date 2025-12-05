# NHL Prediction Model - File Guide

**Last Updated:** November 10, 2025

---

## 📋 **ESSENTIAL FILES**

### **Main Documentation**
```
README.md                  → Project overview & setup
QUICK_START.md            → Quick commands reference
DASHBOARD_README.md       → Visualization dashboard guide
docs/group_report_2.md    → COMPLETE GROUP REPORT (includes latest updates)
```

### **Prediction Scripts**
```
predict_tonight.py        → Get tonight's game predictions (RECOMMENDED)
predict_full.py           → Generate predictions for any date
```

### **Dashboards**
```
streamlit_app.py          → Main interactive dashboard
visualization_dashboard.py → Alternative visualization dashboard
```

### **Utilities**
```
create_visualizations.py  → Generate analysis charts
requirements.txt          → Python dependencies
```

---

## 🗂️ **PROJECT STRUCTURE**

```
NHLpredictionmodel/
│
├── README.md                    ← Start here
├── QUICK_START.md               ← Quick commands
├── docs/group_report_2.md       ← YOUR GROUP REPORT
│
├── predict_tonight.py           ← Predict tonight's games
├── predict_full.py              ← Predict any date
├── streamlit_app.py             ← Dashboard
│
├── data/
│   ├── moneypuck_all_games.csv  ← Historical data (220K+ games)
│   └── nhl_teams.csv            ← Team mappings
│
├── src/nhl_prediction/
│   ├── data_ingest.py           ← Load data
│   ├── features.py              ← Feature engineering (135 features)
│   ├── pipeline.py              ← Build dataset
│   ├── model.py                 ← Train/evaluate models
│   ├── nhl_api.py               ← NHL API client
│   └── betting.py               ← Betting utilities (Phase 4)
│
├── reports/
│   ├── visualizations/          ← Charts & graphs
│   └── predictions_*.csv        ← Saved predictions
│
└── docs/archive/                ← Old working documents (16 files)
```

---

## 🚀 **QUICK COMMANDS**

### **Get Tonight's Predictions**
```bash
python predict_full.py       # Generate predictions
python predict_tonight.py    # Show only tonight's games
```

### **Launch Dashboard**
```bash
streamlit run streamlit_app.py
```

### **Train Model**
```bash
cd src/nhl_prediction
python train.py --seasons 2022 2023 2024
```

### **Create Visualizations**
```bash
python create_visualizations.py
```

---

## 📝 **FOR YOUR GROUP REPORT**

**THE ONLY FILE YOU NEED:**
- `docs/group_report_2.md`

This file contains:
- ✅ Complete technical documentation
- ✅ Model development and evaluation
- ✅ Feature engineering details
- ✅ Results and visualizations
- ✅ **NEW: Appendix A with real-time prediction system (Nov 10 update)**

**What was cleaned up:**
- 16 working documents moved to `docs/archive/`
- Only essential files remain in root directory
- All updates merged into single group report

---

## 📦 **ARCHIVED FILES**

Located in `docs/archive/` (kept for reference, not needed for submission):

```
betting_integration_plan.md       → Phase 4 roadmap
betting_readme.md                 → Betting module guide
CLEAN_VERIFICATION.md             → Data verification notes
MODEL_IMPROVEMENTS_V2.md          → Model iteration notes
MONEYPUCK_MIGRATION.md            → Migration documentation
NHL_API_DOCUMENTATION.md          → Detailed API reference
NHL_API_IMPLEMENTATION_SUMMARY.md → API implementation notes
progress_report_2.md              → Progress update
PROJECT_OVERVIEW.md               → Early overview
PROJECT_STATUS_AND_NEXT_STEPS.md  → Status document
QUICK_SUMMARY.md                  → Quick summary
REPORT_SECTION_FINAL_PHASE.md     → Phase planning
START_HERE.md                     → Old start guide
taxonomy.md                       → Data entity descriptions
usage.md                          → Usage instructions
XGOALS_VERIFICATION.md            → xGoals timing verification
```

**Note:** These are working documents from development. All important content has been merged into `group_report_2.md`.

---

## 🎯 **NEXT STEPS**

### **This Week:**
1. Review `docs/group_report_2.md` (your complete report)
2. Add team member names and details
3. Start tracking predictions vs actual results

### **Phase 4 (Next 3 weeks):**
1. Collect betting odds for 30+ games
2. Calculate ROI
3. Complete final report section

---

## ❓ **Questions?**

- **Setup:** See `README.md`
- **Commands:** See `QUICK_START.md`
- **Report:** See `docs/group_report_2.md`
- **Archive:** See `docs/archive/` for old working docs

