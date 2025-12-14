# ⚡ QUICK REFERENCE CARD - NHL PREDICTION MODEL

**Print this out or keep it handy for daily use!**

---

## 🚀 DAILY COMMANDS

```bash
# Generate today's predictions
python predict_full.py

# Open dashboard
streamlit run dashboard_billion.py

# Predictions for specific date
python predict_full.py 2025-11-15
```

---

## 📊 DASHBOARD PAGES (7 TOTAL)

| Icon | Page | Use For |
|------|------|---------|
| 🏠 | Command Center | Quick overview, system status |
| 🎯 | Today's Predictions | Detailed game analysis |
| 💰 | Betting Simulator | ROI testing, strategy comparison |
| 📈 | Performance Analytics | Model health, calibration |
| 🔬 | Deep Analysis | Feature insights, correlations |
| 🏆 | Leaderboards | Team rankings, streaks, matchups |
| ❓ | Help | Documentation, tips |

---

## 🎯 CONFIDENCE LEVELS

| Edge | Meaning | Action |
|------|---------|--------|
| 0-5% | Toss-up | ⚠️ Avoid |
| 5-10% | Slight favorite | 📊 Consider |
| 10-15% | Moderate | ✅ Reasonable bet |
| 15-20% | Strong | ✅ Good bet |
| 20%+ | Very strong | 🔥 Best bets |

---

## 📈 MODEL STATS (MEMORIZE THESE)

```
Accuracy:      59.2%  (Test set)
Baseline:      53.1%  (Home team wins)
Edge:          +6.1%  (vs baseline)
ROC-AUC:       0.624  (Discrimination)
Brier Score:   0.241  (Calibration)
Log Loss:      0.675  (Confidence)
Features:      141    (Engineered)
Training:      3,690  (Games 2021-2024)
```

---

## 🔥 TOP 5 FEATURES

1. **is_b2b_diff** - Back-to-back game differential (fatigue)
2. **rolling_corsi_10_diff** - Possession (shot attempts)
3. **elo_diff_pre** - Team strength differential
4. **rolling_high_danger_shots** - Shot quality
5. **rolling_save_pct_diff** - Goaltending quality

---

## 💰 BETTING STRATEGIES

### **🎯 Threshold (Conservative)**
- Only bet high confidence games
- Set threshold (recommend 60%)
- Best for: Beginners, risk-averse

### **🧮 Kelly Criterion (Optimal)**
- Bet size proportional to edge
- Use 0.25 Kelly fraction (recommend)
- Best for: Experienced, bankroll management

### **🎲 All Games (Baseline)**
- Bet every game (flat betting)
- Best for: Comparison, high volume

---

## 🏆 QUICK CHECKS

### **Morning Routine (5 min)**
1. ✅ Run: `python predict_full.py`
2. ✅ Open: `streamlit run dashboard_billion.py`
3. ✅ Check: Command Center → Today's games count
4. ✅ Review: Today's Predictions → High confidence games
5. ✅ Scan: Leaderboards → Hot/cold streaks

### **Before Betting**
- [ ] Confidence >15%?
- [ ] Team on hot streak? (Leaderboards)
- [ ] Good matchup? (Leaderboards)
- [ ] Top-ranked team? (Performance Analytics)
- [ ] Your analysis agrees?

### **Red Flags (Avoid)**
- ❌ Confidence <5%
- ❌ Team on cold streak
- ❌ Worst matchup
- ❌ Bottom-ranked team
- ❌ Recent injury news (check separately!)

---

## 🔧 TROUBLESHOOTING

| Problem | Solution |
|---------|----------|
| Dashboard won't start | Kill port: `lsof -ti:8501 \| xargs kill -9` |
| Module not found | Install: `pip install streamlit pandas numpy scikit-learn altair` |
| No predictions | Run: `python predict_full.py` |
| Slow performance | Clear cache: `streamlit cache clear` |
| Wrong predictions shown | Refresh: Press `r` in browser |

---

## 📁 KEY FILES

```
dashboard_billion.py          # Main dashboard (2,110 lines)
predict_full.py              # Prediction script
predictions_YYYY-MM-DD.csv   # Daily outputs
data/moneypuck_all_games.csv # Historical data
group_report_2.md            # Project report
USER_GUIDE.md                # Full documentation
```

---

## 💡 PRO TIPS

1. **Always check injury reports** - Model doesn't know about injuries
2. **Verify starting goalies** - Can change last minute
3. **Focus on 15%+ edge** - Best risk/reward
4. **Track your results** - Know what works for you
5. **Small bets while learning** - $1-5 until proven
6. **Check hot streaks** - Leaderboards tab 2
7. **Use "Why This Prediction?"** - Understand reasoning
8. **Compare strategies** - Betting Simulator
9. **Review calibration** - Performance Analytics tab 1
10. **Trust but verify** - Add your own analysis

---

## 📊 INTERPRETATION GUIDE

### **Win Probabilities**
- **52%:** Coin flip, tiny edge
- **55%:** Slight favorite
- **58%:** Moderate confidence
- **62%:** Strong pick
- **65%+:** Very confident

### **ROC-AUC (0.624)**
- 0.50 = Random guessing
- 0.60 = Decent
- **0.62 = Good** ✅ (We're here!)
- 0.70 = Excellent
- 1.00 = Perfect

### **Brier Score (0.241)**
- 0.00 = Perfect
- **0.24 = Good** ✅ (We're here!)
- 0.25 = Baseline
- 0.50 = Random

---

## 🎯 BETTING BANKROLL GUIDE

| Confidence | Kelly 0.25 | Conservative |
|------------|------------|--------------|
| 0-5% edge | $0-1 | Skip |
| 5-10% edge | $1-2 | $1 |
| 10-15% edge | $2-3 | $2 |
| 15-20% edge | $3-4 | $3 |
| 20%+ edge | $4-5 | $5 |

*Based on $100 bankroll*

---

## ⚡ KEYBOARD SHORTCUTS (Dashboard)

- **`r`** - Refresh dashboard
- **`Cmd+K`** - Search (in some browsers)
- **`Cmd+W`** - Close tab
- **`Cmd+R`** - Hard refresh
- **`Esc`** - Close expanders

---

## 📞 WHEN THINGS GO WRONG

**Dashboard Frozen?**
1. Check terminal for errors
2. Press `r` to refresh
3. `Cmd+Shift+R` to hard refresh
4. Restart dashboard

**Predictions Wrong Date?**
1. Check what day it is
2. Run `python predict_full.py` again
3. Refresh dashboard

**Numbers Don't Make Sense?**
1. Check if data is up to date
2. Verify predictions file exists
3. Look at terminal output
4. Review USER_GUIDE.md

---

## 🎓 QUICK STATS FOR PRESENTATIONS

**Opening:**
> "Built ML model predicting NHL games with 59.2% accuracy, beating 53.1% baseline by 6.1 percentage points using 141 engineered features across 3,690 historical games."

**Dashboard:**
> "Created billion-dollar quality dashboard with 7 pages, 30+ features, betting simulator, team rankings, and real-time analytics."

**Key Insights:**
> "Top predictor: Back-to-back games (fatigue). Model is well-calibrated (Brier: 0.241) with good discrimination (ROC-AUC: 0.624)."

---

## ✅ DAILY CHECKLIST

**Every Morning:**
- [ ] Generate predictions (`python predict_full.py`)
- [ ] Open dashboard
- [ ] Check game count (Command Center)
- [ ] Review high confidence picks (Today's Predictions)
- [ ] Check hot streaks (Leaderboards)
- [ ] Note any red flags
- [ ] Make decisions
- [ ] Track results

**Weekly:**
- [ ] Calculate ROI
- [ ] Review which strategies worked
- [ ] Check team rankings changes
- [ ] Analyze mistakes
- [ ] Adjust approach

---

## 🔥 EMERGENCY CONTACTS

**Dashboard not working?**
→ Check USER_GUIDE.md - Troubleshooting section

**Don't understand metrics?**
→ Check USER_GUIDE.md - Understanding Predictions section

**Want to modify model?**
→ Check code comments in `src/nhl_prediction/`

**Need help presenting?**
→ Check "Quick Stats for Presentations" above

---

## 💎 GOLDEN RULES

1. **Model is a tool, not a crystal ball**
2. **Always add your own analysis**
3. **Never bet more than you can afford to lose**
4. **Track everything**
5. **Start small, scale slowly**
6. **Trust the process, not single games**
7. **Confidence >15% for betting**
8. **Check injuries separately**
9. **Focus on edges, not wins**
10. **Have fun!** 🏒

---

**QUICK REFERENCE v2.0**  
**Last Updated:** November 10, 2025  

**Print this • Share this • Use this daily!**

---

## 📱 MOBILE-FRIENDLY VERSION

**Can't remember everything? Remember these 3:**

```
1. python predict_full.py
2. streamlit run dashboard_billion.py
3. Check confidence >15% before betting
```

**That's it! 🚀**


