# Daily Prediction Commands - Quick Reference

**Updated:** November 10, 2025  
**Model Version:** v2.0 (with goaltending integration)  
**Accuracy:** 59.2%

---

## 🚀 Your Daily Command (EASIEST)

Just run this every day to get tonight's game predictions:

```bash
cd /Users/noahowsiany/Desktop/Predictive\ Model\ 3.3/NHLpredictionmodel
python predict_tonight.py
```

**What it does:**
1. Fetches tonight's games from NHL API
2. Loads pre-computed predictions
3. Shows clean, focused output (only games starting today)

**Output:**
- Game matchups with start times
- Win probabilities for each team
- Clear predictions (TOSS-UP, slight edge, or STRONG)

---

## 📊 Full Prediction Command (More Details)

For all games on a specific date (not just tonight):

```bash
# Today's games (default)
python predict_full.py

# Specific date
python predict_full.py 2025-11-15
```

**What it does:**
1. Fetches NHL schedule for the date
2. Loads 4 seasons of historical data (2021-2024)
3. Engineers 141 features (including goaltending)
4. Trains model on 5,002 historical games
5. Generates predictions for all games
6. Saves to CSV: `predictions_YYYY-MM-DD.csv`

**Output:**
- All games (up to 20)
- Win probabilities
- Confidence levels
- Saved CSV file

---

## 🔄 Typical Daily Workflow

### Option 1: Quick Check (Recommended)
```bash
cd /Users/noahowsiany/Desktop/Predictive\ Model\ 3.3/NHLpredictionmodel
python predict_tonight.py
```
Takes: ~5 seconds (loads pre-computed predictions)

### Option 2: Fresh Predictions
```bash
cd /Users/noahowsiany/Desktop/Predictive\ Model\ 3.3/NHLpredictionmodel
python predict_full.py     # Generate new predictions
python predict_tonight.py  # View tonight's games only
```
Takes: ~30-60 seconds (full model training + prediction)

---

## 📁 Output Files

After running `predict_full.py`, you'll get:

```
predictions_2025-11-10.csv
```

**Columns:**
- `game_id` - NHL game ID
- `date` - Game date
- `away_team` - Away team abbreviation
- `home_team` - Home team abbreviation
- `start_time` - Game start time
- `home_win_prob` - Home team win probability (0-1)
- `away_win_prob` - Away team win probability (0-1)
- `predicted_winner` - Team predicted to win
- `confidence` - Confidence level (0-1)

---

## ⚙️ What's Running Under The Hood

### Data Sources (Automatic)
1. **MoneyPuck CSV** (`data/moneypuck_all_games.csv`)
   - 220,000+ games (2008-2025)
   - Auto-updates with new games
   - Team stats, xGoals, Corsi, Fenwick

2. **MoneyPuck Goalie Data** (`data/team_goaltending.csv`)
   - Team goaltending quality
   - Save %, Goals Saved Above Expected
   - 2021-2025 seasons

3. **NHL Stats API** (Real-time)
   - Today's game schedule
   - Live game information

### Model (Automatic)
- **Algorithm:** Logistic Regression
- **Features:** 141 (team strength, momentum, rest, goaltending)
- **Training:** 3,690 games (2021-2024)
- **Accuracy:** 59.2% (professional range)

---

## 🎯 Reading the Predictions

### Confidence Levels

**TOSS-UP (< 5% confidence)**
```
Home Win: 48.3%  |  Away Win: 51.7%
⚖️  Prediction: TOSS-UP (too close to call)
```
→ Game is a coin flip, don't bet

**Slight Edge (5-20% confidence)**
```
Home Win: 57.1%  |  Away Win: 42.9%
📊 Prediction: NYR (slight 14% edge)
```
→ Model leans one way, but not strongly

**Strong Favorite (> 20% confidence)**
```
Home Win: 74.9%  |  Away Win: 25.1%
✅ Prediction: COL STRONG (50% edge)
```
→ Model is confident, good bet if odds are favorable

---

## 🔧 Troubleshooting

### "ModuleNotFoundError"
```bash
# Install dependencies
pip install -r requirements.txt
```

### "FileNotFoundError: data/moneypuck_all_games.csv"
```bash
# Make sure you're in the project directory
cd /Users/noahowsiany/Desktop/Predictive\ Model\ 3.3/NHLpredictionmodel
```

### "No games found for tonight"
- This is normal if there are no NHL games scheduled
- Try `python predict_full.py` to see full week's schedule

### Predictions seem old
- Run `python predict_full.py` to generate fresh predictions
- Model automatically uses latest available data

---

## 📊 Performance Tracking (Optional)

Want to track how well the model does? Compare predictions to actual results:

1. Run predictions before games
2. Save the CSV file
3. After games finish, check results on NHL.com
4. Calculate: (correct predictions) / (total games)

Expected accuracy: ~59% over large samples

---

## 🚀 Quick Command Summary

```bash
# Simplest: Tonight's games only
python predict_tonight.py

# Full: All games for today
python predict_full.py

# Full: All games for specific date
python predict_full.py 2025-11-15
```

**That's it!** The model handles everything else automatically.

---

## ✅ System Status

All systems verified and working:
- ✅ Data files present (115 MB MoneyPuck data)
- ✅ Goalie data integrated (141 features)
- ✅ Model training (59.2% accuracy)
- ✅ NHL API connection working
- ✅ Prediction scripts working
- ✅ CSV export working

**Status:** PRODUCTION READY 🚀

---

**Questions?** Check:
- `README.md` - Full project documentation
- `FINAL_STATUS.md` - Model performance summary
- `GOALIE_INTEGRATION_SUMMARY.md` - Latest improvements

