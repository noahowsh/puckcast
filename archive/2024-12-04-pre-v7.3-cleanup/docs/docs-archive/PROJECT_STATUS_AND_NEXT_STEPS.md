# NHL Prediction Model - Project Status & Next Steps
**Last Updated:** November 10, 2025

---

## 🎯 **CURRENT STATUS**

### ✅ **What's Completed (Phase 1-3)**

#### **1. Data Pipeline**
- ✅ MoneyPuck data integration (220K+ games, 2008-2025)
- ✅ NHL API integration for real-time schedules
- ✅ Team mapping and data normalization
- ✅ Data cleaning and validation

#### **2. Feature Engineering (135 features)**
- ✅ Rolling averages (3, 5, 10 games)
- ✅ Expected Goals (xG) metrics
- ✅ Shot quality (high/medium/low danger)
- ✅ Possession metrics (Corsi, Fenwick)
- ✅ Momentum indicators
- ✅ Rest and scheduling factors
- ✅ Elo rating system
- ✅ Home/away differentials

#### **3. Model Development**
- ✅ Logistic Regression baseline
- ✅ Histogram Gradient Boosting
- ✅ Temporal validation (no data leakage)
- ✅ Calibration curves
- ✅ Feature importance analysis

#### **4. Model Performance**
| Metric | Value |
|--------|-------|
| **Accuracy** | 59.3% (baseline: 55.7%) |
| **Log Loss** | 0.665 |
| **Brier Score** | 0.237 |
| **ROC-AUC** | 0.649 |

#### **5. Visualization & Analysis**
- ✅ 6 comprehensive visualization types
- ✅ Calibration analysis
- ✅ Team performance heatmaps
- ✅ Feature correlation analysis
- ✅ Prediction confidence analysis

#### **6. Deployment**
- ✅ Streamlit dashboard (`streamlit_app.py`)
- ✅ Command-line prediction tools
- ✅ `predict_full.py` - predict any date
- ✅ `predict_tonight.py` - tonight's games only

---

## 📂 **ESSENTIAL FILES**

### **Core Scripts**
```
predict_tonight.py       → Quick predictions for tonight's games
predict_full.py          → Full predictions for any date
streamlit_app.py         → Interactive dashboard
create_visualizations.py → Generate analysis charts
```

### **Key Documentation**
```
README.md                     → Project overview
docs/group_report_2.md        → Main project report
docs/betting_integration_plan.md → Future work roadmap
docs/NHL_API_DOCUMENTATION.md → API reference
```

### **Source Code**
```
src/nhl_prediction/
  ├── data_ingest.py    → Load MoneyPuck + NHL API
  ├── features.py       → Feature engineering
  ├── pipeline.py       → Build dataset
  ├── model.py          → Train & evaluate
  ├── nhl_api.py        → NHL API client
  └── betting.py        → Betting utilities (Phase 4)
```

---

## 🧹 **CLEANUP RECOMMENDATIONS**

### **Files to Archive/Delete**
These were working documents during development - keep for reference or delete:

```
CLEAN_VERIFICATION.md           → Archive
MODEL_IMPROVEMENTS_V2.md        → Archive
MONEYPUCK_MIGRATION.md          → Archive
NHL_API_IMPLEMENTATION_SUMMARY.md → Keep (useful reference)
PROJECT_OVERVIEW.md             → Merge into README, then delete
QUICK_SUMMARY.md                → Delete (superseded by this file)
REPORT_SECTION_FINAL_PHASE.md   → Archive (copy to group report)
START_HERE.md                   → Delete (superseded by README)
XGOALS_VERIFICATION.md          → Archive
predict_today.py                → Delete (superseded by predict_tonight.py)
predictions_2025-11-10.csv      → Keep for now, clean up old predictions later
```

### **Suggested Cleanup Commands**
```bash
# Create archive folder
mkdir -p docs/archive

# Move working docs to archive
mv CLEAN_VERIFICATION.md docs/archive/
mv MODEL_IMPROVEMENTS_V2.md docs/archive/
mv MONEYPUCK_MIGRATION.md docs/archive/
mv PROJECT_OVERVIEW.md docs/archive/
mv QUICK_SUMMARY.md docs/archive/
mv REPORT_SECTION_FINAL_PHASE.md docs/archive/
mv START_HERE.md docs/archive/
mv XGOALS_VERIFICATION.md docs/archive/

# Delete superseded scripts
rm predict_today.py
```

---

## 🚀 **NEXT STEPS - PHASE 4: BETTING INTEGRATION**

### **Goal**
Answer the question: **"Can this model generate positive ROI from betting?"**

---

### **Phase 4.1: Odds Data Collection (1-2 weeks)**

#### **Option 1: Manual Collection (Easiest)**
- Use DraftKings, FanDuel, or BetMGM websites
- Manually record odds for each game before they start
- Track for 20-30 games to build dataset
- **Pros:** Simple, free, guaranteed data
- **Cons:** Time-consuming, manual entry

#### **Option 2: Odds API Integration**
- Use The Odds API (theoddsapi.com)
  - Free tier: 500 requests/month
  - Sufficient for ~15-20 games/day for 1 month
- **Pros:** Automated, real-time
- **Cons:** API key required, rate limits

**Recommendation:** Start with Option 1 (manual) for 10-15 games while setting up Option 2.

---

### **Phase 4.2: Betting Strategy Implementation (1 week)**

#### **4.2.1: Odds Conversion**
```python
# Already implemented in src/nhl_prediction/betting.py
american_to_implied_prob(odds)  # Convert -110 → 0.524
remove_vig(home_odds, away_odds)  # Get true probabilities
```

#### **4.2.2: Value Detection**
```python
# Compare model prediction to market odds
model_prob = 0.65  # Model says 65% win chance
market_prob = 0.55  # Market implies 55% win chance
edge = model_prob - market_prob  # +10% edge → BET!
```

#### **4.2.3: Betting Strategies**

**Strategy 1: Threshold Betting**
- Only bet when model edge > threshold (e.g., 5%)
- Fixed stake per bet
- **Simple, easy to track**

**Strategy 2: Kelly Criterion**
- Bet size proportional to edge
- `bet_fraction = (model_prob * odds - 1) / (odds - 1)`
- **Optimal long-term growth, requires discipline**

---

### **Phase 4.3: Live Tracking & Evaluation (2-4 weeks)**

#### **Metrics to Track**
| Metric | Target |
|--------|--------|
| **ROI** | > 5% (break even ~0%) |
| **Win Rate** | Model-dependent (aim: 52%+) |
| **Sharpe Ratio** | > 0.5 (risk-adjusted return) |
| **Max Drawdown** | < 20% (largest losing streak) |
| **# of Bets** | 30+ (minimum for significance) |

#### **Tracking Spreadsheet Template**
```
Date | Away | Home | Model_Prob | Odds | Market_Prob | Edge | Bet? | Stake | Result | Profit
-----|------|------|------------|------|-------------|------|------|-------|--------|-------
11/10| NYI  | NJD  | 0.569      | +150 | 0.400       | 0.169| YES  | $10   | WIN    | +$15
11/10| CBJ  | EDM  | 0.358      | +280 | 0.263       | 0.095| YES  | $5    | LOSS   | -$5
```

---

### **Phase 4.4: Analysis & Reporting (1 week)**

#### **Questions to Answer**
1. **Is the model profitable?**
   - ROI calculation
   - Statistical significance testing

2. **Which bet types work best?**
   - Favorites vs underdogs
   - Home vs away
   - High confidence vs medium confidence

3. **What's the optimal strategy?**
   - Threshold level (5%? 10%?)
   - Kelly fraction (full? half?)
   - Bankroll management

4. **Model improvements needed?**
   - Which features are most valuable for betting?
   - Do we need goalie data? Injuries?

---

## 📊 **FINAL DELIVERABLES**

### **For Group Report**
1. **Executive Summary** (1 page)
   - Problem statement
   - Approach
   - Results
   - Business implications

2. **Technical Section** (3-5 pages)
   - Data sources and pipeline
   - Feature engineering (135 features)
   - Model architecture and validation
   - Performance metrics

3. **Betting Analysis** (2-3 pages)
   - Market comparison
   - ROI results
   - Risk analysis
   - Recommendations

4. **Appendix**
   - Code samples
   - Visualizations
   - Feature importance tables
   - API documentation

---

## 🎓 **GRADING CRITERIA (ENSURE COVERAGE)**

### **Technical Depth** (40%)
- ✅ Advanced feature engineering
- ✅ Multiple model types compared
- ✅ Proper validation (no data leakage)
- ✅ Calibration and statistical analysis

### **Business Application** (30%)
- ⏳ Clear use case (betting ROI)
- ⏳ Market analysis
- ⏳ Risk assessment
- ⏳ Actionable recommendations

### **Communication** (20%)
- ✅ Professional documentation
- ✅ Effective visualizations
- ⏳ Clear write-up
- ✅ Code organization

### **Innovation** (10%)
- ✅ NHL API integration for real-time predictions
- ✅ Advanced metrics (xG, Corsi, Fenwick)
- ✅ Elo rating system
- ⏳ Novel betting strategy analysis

---

## ⏰ **RECOMMENDED TIMELINE**

**Week 1 (Nov 11-17):**
- Clean up project files
- Finalize group report draft (technical sections)
- Start manual odds collection (5-10 games)

**Week 2 (Nov 18-24):**
- Continue odds collection (20+ total games)
- Implement betting strategy code
- Run backtests on collected data

**Week 3 (Nov 25-Dec 1):**
- Live betting simulation (paper trading)
- Analyze results
- Write betting section of report

**Week 4 (Dec 2-8):**
- Finalize report
- Create presentation
- Polish visualizations

---

## 📝 **IMMEDIATE NEXT ACTIONS**

1. **[TODAY]** Run cleanup commands above
2. **[TODAY]** Update `docs/group_report_2.md` with current status
3. **[THIS WEEK]** Manually track odds for next 10 games
4. **[THIS WEEK]** Set up automated odds collection (The Odds API)
5. **[NEXT WEEK]** Implement betting simulation code
6. **[ONGOING]** Track all predictions vs actual results

---

## 🔗 **USEFUL LINKS**

- **The Odds API:** https://theoddsapi.com/
- **DraftKings:** https://sportsbook.draftkings.com/
- **MoneyPuck Data:** https://moneypuck.com/data.htm
- **NHL API:** https://api-web.nhle.com/

---

**Questions? Check:**
- `README.md` - Project overview
- `docs/betting_integration_plan.md` - Detailed betting roadmap
- `docs/NHL_API_DOCUMENTATION.md` - API reference

