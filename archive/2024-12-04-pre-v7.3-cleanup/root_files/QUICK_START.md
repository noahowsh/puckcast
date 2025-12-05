# NHL Prediction Model - Quick Start Guide

**Last Updated:** November 10, 2025

---

## 🚀 **Get Tonight's Predictions (3 Steps)**

### **Step 1: Generate Predictions**
```bash
python predict_full.py
```
This loads the model and predicts ALL games for today.

### **Step 2: View Tonight's Games Only**
```bash
python predict_tonight.py
```
This filters to show only games starting tonight.

### **Step 3: Review Results**
```
🏒 TONIGHT'S NHL GAME PREDICTIONS
================================================================================

📅 Monday, November 10, 2025

1️⃣  Fetching tonight's games from NHL API...
   ✅ Found 4 games tonight:

      1. NYI @ NJD (07:00 PM ET)
      2. NSH @ NYR (07:00 PM ET)
      3. CBJ @ EDM (08:30 PM ET)
      4. FLA @ VGK (10:00 PM ET)
```

---

## 📊 **Other Commands**

### **Train & Evaluate Model**
```bash
cd src/nhl_prediction
python train.py --seasons 2022 2023 2024
```

### **Launch Dashboard**
```bash
streamlit run streamlit_app.py
```

### **Create Visualizations**
```bash
python create_visualizations.py
```

### **Predict Specific Date**
```bash
python predict_full.py 2025-11-15
python predict_tonight.py 2025-11-15
```

---

## 📁 **File Structure**

```
NHLpredictionmodel/
├── predict_tonight.py          ← Quick: tonight's games
├── predict_full.py             ← Full: all games for a date
├── streamlit_app.py            ← Interactive dashboard
├── create_visualizations.py    ← Generate charts
│
├── data/
│   ├── moneypuck_all_games.csv ← Historical game data
│   └── nhl_teams.csv           ← Team mappings
│
├── src/nhl_prediction/
│   ├── data_ingest.py          ← Load data
│   ├── features.py             ← Feature engineering
│   ├── pipeline.py             ← Build dataset
│   ├── model.py                ← Train/evaluate models
│   ├── nhl_api.py              ← NHL API client
│   └── betting.py              ← Betting utilities
│
├── docs/
│   ├── group_report_2.md       ← Main project report
│   ├── LATEST_UPDATE_FOR_REPORT.md ← Recent updates
│   └── betting_integration_plan.md ← Phase 4 roadmap
│
└── reports/
    ├── visualizations/         ← Charts and graphs
    └── predictions_*.csv       ← Saved predictions
```

---

## 🔄 **Update MoneyPuck Data**

MoneyPuck data needs manual updates. To get the latest:

```bash
# Download latest from MoneyPuck
cd data
curl -O "https://moneypuck.com/moneypuck/playerData/careers/gameByGame/all_teams.csv"

# Rename to expected filename
mv all_teams.csv moneypuck_all_games.csv

# Verify latest games
python -c "
import pandas as pd
df = pd.read_csv('moneypuck_all_games.csv')
df['gameDate'] = pd.to_datetime(df['gameDate'], format='%Y%m%d')
print(f'Latest game: {df[\"gameDate\"].max()}')
"
```

**Update Frequency:** Weekly during season (MoneyPuck updates ~1-2 days after games)

---

## 🎯 **Next Steps (Phase 4)**

1. **Manual Odds Tracking**
   - Track predictions vs actual results
   - Record betting odds from DraftKings/FanDuel
   - Build 30+ game sample

2. **Automated Odds**
   - Sign up for The Odds API (theoddsapi.com)
   - Free tier: 500 requests/month
   - Integrate into prediction pipeline

3. **ROI Analysis**
   - Calculate betting returns
   - Test different strategies (threshold, Kelly)
   - Evaluate statistical significance

---

## ❓ **Troubleshooting**

### **"No games found"**
- Check date format: `YYYY-MM-DD`
- NHL API returns empty for off-season/All-Star break

### **"Game not found in MoneyPuck data"**
- MoneyPuck lags 1-2 days
- Update CSV with latest data
- Today's games won't be in yesterday's CSV

### **"Module not found"**
- Install requirements: `pip install -r requirements.txt`
- Ensure you're in project root directory

---

## 📧 **Support**

- Documentation: `docs/`
- API Reference: `docs/NHL_API_DOCUMENTATION.md`
- Project Status: `PROJECT_STATUS_AND_NEXT_STEPS.md`
