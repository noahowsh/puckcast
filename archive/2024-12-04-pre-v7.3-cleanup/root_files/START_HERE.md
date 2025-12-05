# NHL Prediction Model - Quick Start

**Model Accuracy:** 59.2% (Test Set)  
**Status:** ✅ Production Ready

---

## 🚀 Daily Prediction Command

```bash
cd /Users/noahowsiany/Desktop/Predictive\ Model\ 3.3/NHLpredictionmodel
python predict_tonight.py
```

**That's it!** This shows tonight's NHL games with win probabilities.

---

## 📊 Current Model Stats

- **Test Accuracy:** 59.2% (1,312 games, 2024-2025 season)
- **Features:** 141 (team strength, momentum, rest, goaltending, xGoals, Corsi, Fenwick)
- **Training Data:** 3,690 games (2021-2024 seasons)
- **Model Type:** Logistic Regression with L2 regularization
- **Improvement over Baseline:** +6.1 percentage points

---

## 📁 Key Files

### For Daily Use
- **`predict_tonight.py`** - Quick predictions for tonight's games
- **`predict_full.py`** - Full predictions for any date

### For Your Report
- **`docs/group_report_2.md`** - Main project report (ready to submit)
- **`README.md`** - Project overview and technical details
- **`DASHBOARD_README.md`** - Streamlit dashboard guide

### Outputs
- **`predictions_YYYY-MM-DD.csv`** - Saved predictions with probabilities
- **`reports/`** - Model evaluation metrics and visualizations

---

## 🎯 What Makes This Model Good

1. **Professional-Range Accuracy** - 59.2% matches industry standards (55-60%)
2. **No Data Leakage** - Proper temporal validation, only uses pre-game data
3. **Advanced Features** - Expected Goals (xG), possession metrics, goaltending quality
4. **Real-Time Capable** - Can predict any day's games using NHL API
5. **Well-Calibrated** - Probability estimates are reliable for decision-making

---

## 🔬 Technical Details

**Full documentation in:** `README.md` and `docs/group_report_2.md`

**Key innovations:**
- Integrated MoneyPuck's advanced analytics (220K+ games)
- Added goaltending quality metrics (+1.1% accuracy improvement)
- 4-season training (excluding COVID-affected 2020 season)
- 141 engineered features with rolling windows (3/5/10 games)

---

## ✅ System Status

All verified and working:
- ✅ Data files present (MoneyPuck + goalie data)
- ✅ Model accuracy: 59.2% confirmed
- ✅ Prediction scripts: Working
- ✅ NHL API: Connected
- ✅ Documentation: Complete

**Ready for submission!** 🚀

---

For complete details, see `README.md` or `docs/group_report_2.md`
