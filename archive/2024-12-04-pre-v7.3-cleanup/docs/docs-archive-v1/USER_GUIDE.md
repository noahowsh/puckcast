# 📚 NHL PREDICTION MODEL - USER GUIDE

**Welcome to your Billion-Dollar NHL Prediction Dashboard!**

This guide will help you use the system effectively, whether you're making daily predictions, analyzing model performance, or researching betting strategies.

---

## 🚀 QUICK START (30 SECONDS)

### **1. Make Today's Predictions**
```bash
python predict_full.py
```
**What it does:** Generates predictions for today's NHL games  
**Output:** Creates `predictions_YYYY-MM-DD.csv`

### **2. View Dashboard**
```bash
streamlit run dashboard_billion.py
```
**What it does:** Opens interactive web dashboard  
**Access:** Browser opens automatically to http://localhost:8501

### **3. Navigate**
Use the sidebar to explore 7 pages:
- 🏠 Command Center
- 🎯 Today's Predictions  
- 💰 Betting Simulator
- 📈 Performance Analytics
- 🔬 Deep Analysis
- 🏆 Leaderboards
- ❓ Help

---

## 📋 TABLE OF CONTENTS

1. [Installation & Setup](#installation--setup)
2. [Daily Prediction Workflow](#daily-prediction-workflow)
3. [Dashboard Guide](#dashboard-guide)
4. [Understanding Predictions](#understanding-predictions)
5. [Betting Analysis](#betting-analysis)
6. [Troubleshooting](#troubleshooting)
7. [FAQ](#faq)
8. [Advanced Usage](#advanced-usage)

---

## 💻 INSTALLATION & SETUP

### **Prerequisites**
- Python 3.8 or higher
- 2GB free disk space
- Internet connection (for NHL API)

### **First-Time Setup**

1. **Navigate to project directory:**
```bash
cd "/Users/noahowsiany/Desktop/Predictive Model 3.3/NHLpredictionmodel"
```

2. **Activate virtual environment (if you have one):**
```bash
source .venv/bin/activate  # macOS/Linux
# or
.venv\Scripts\activate  # Windows
```

3. **Install dependencies:**
```bash
pip install streamlit pandas numpy scikit-learn altair requests
```

4. **Verify setup:**
```bash
python -c "import streamlit, pandas, sklearn; print('✅ Setup complete!')"
```

---

## 🎯 DAILY PREDICTION WORKFLOW

### **Morning Routine (5 minutes)**

**Step 1: Generate Predictions**
```bash
python predict_full.py
```
**Expected output:**
```
🏒 NHL Game Predictions
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📊 Model Training Complete
✅ Training: 3,690 games (2021-2024)
✅ Features: 141 advanced metrics
✅ Accuracy: 59.2%

🎯 Today's Predictions (2025-11-10)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Game 1: NYI @ NYR
  🏠 NYR: 52% (Predicted Winner)
  ✈️  NYI: 48%
  📊 Confidence: 2% edge

[... more games ...]

✅ Predictions saved to: predictions_2025-11-10.csv
```

**Step 2: Review in Dashboard**
```bash
streamlit run dashboard_billion.py
```

**Step 3: Check These Pages**
1. **Command Center** → Quick overview
2. **Today's Predictions** → Detailed game analysis
3. **Leaderboards → Streak Tracker** → Hot/cold teams

---

## 📊 DASHBOARD GUIDE

### **🏠 PAGE 1: Command Center**

**Purpose:** High-level overview of system status

**What You'll See:**
- **Top KPI Bar:** Live status, accuracy, ROC-AUC, correct picks, features
- **Elite Metrics:** Brier score, log loss, edge vs baseline, training games
- **Top Features Chart:** Most important predictive factors
- **Today's Games Widget:** Quick preview (4 games)
- **Quick Stats:** Win rate with progress bar

**Use This When:**
- ✅ Starting your day
- ✅ Checking model health
- ✅ Quick status check
- ✅ Seeing today's game count

**Key Metrics Explained:**
- **Accuracy (59.2%):** How often we predict correctly
- **ROC-AUC (0.624):** Discrimination ability (0.5 = random, 1.0 = perfect)
- **Brier Score (0.241):** Calibration quality (lower = better)
- **Log Loss (0.675):** Prediction confidence accuracy

---

### **🎯 PAGE 2: Today's Predictions**

**Purpose:** Detailed analysis of today's NHL games

**What You'll See:**
- Filters (confidence slider, sorting)
- Game cards with:
  - Team names and probabilities
  - Confidence meters
  - Predicted winner
  - "Why This Prediction?" expander

**How to Use:**

**1. Filter Games**
- Adjust "Minimum Confidence" slider to see only strong picks
- Sort by confidence, home team, or game time

**2. Understand Predictions**
- Click "🔍 Why This Prediction?" on any game
- See top 10 features that influenced the prediction
- Green bars = helps home team
- Red bars = helps away team

**3. Identify Best Bets**
- Look for HIGH CONFIDENCE games (>20% edge)
- Check if favored team aligns with your analysis
- Use "Why" expander to validate reasoning

**Example Interpretation:**
```
Game: BOS @ TOR
Home (TOR): 62%
Away (BOS): 38%
Confidence: 12% edge

Interpretation:
- Moderate confidence pick
- Toronto favored at home
- 12% edge = reasonable bet
- Click expander to see why (likely Elo, rest, possession)
```

---

### **💰 PAGE 3: Betting Simulator**

**Purpose:** Test betting strategies and calculate ROI

**What You'll See:**
- Strategy selector (3 options)
- Parameter sliders
- 4 result cards (Bets, Win Rate, ROI, Profit)
- Profit curve chart
- Strategy explanations

**3 Strategies Explained:**

**1. Threshold Betting (🎯 Conservative)**
- **How it works:** Only bet on games with high confidence
- **Slider:** Confidence threshold (50-80%)
- **Best for:** Risk-averse bettors, beginners
- **Example:** At 60% threshold, only bet when model is 60%+ confident

**2. Kelly Criterion (🧮 Optimal)**
- **How it works:** Bet size proportional to edge
- **Slider:** Kelly fraction (0.1-1.0, recommend 0.25)
- **Best for:** Sophisticated bettors, bankroll management
- **Example:** Larger bets on high confidence, smaller on low

**3. All Games (🎲 Baseline)**
- **How it works:** Bet on every game (flat betting)
- **No slider:** Fixed $1 per game
- **Best for:** Comparison, high-volume approach

**How to Use:**

**Step 1: Select Strategy**
- Start with "Threshold" at 60% to see conservative results
- Try "Kelly" with 0.25 fraction for optimal sizing

**Step 2: Analyze Results**
- **Total Bets:** How many games qualified
- **Win Rate:** % of bets that won
- **ROI:** Return on investment (positive = profit)
- **Total Profit:** Net profit/loss in dollars

**Step 3: Compare**
- Switch strategies to see differences
- Find what works for your risk tolerance

**Profit Curve:**
- X-axis = Game number
- Y-axis = Cumulative profit
- Above zero line = profitable
- Below zero line = losing

---

### **📈 PAGE 4: Performance Analytics**

**Purpose:** Deep dive into model quality

**Tab 1: 📊 Calibration**

**What it shows:** How well predicted probabilities match reality

**Perfect calibration:**
- If we predict 60% → should win 60% of the time
- Red dashed line = perfect
- Our line should be close to red

**How to read:**
- Points above red = overconfident
- Points below red = underconfident
- Close to red = well calibrated ✅

**Tab 2: 🎯 Confidence Buckets**

**What it shows:** Accuracy by confidence level

**6 Confidence Levels:**
1. **0-5% edge:** Toss-ups (near 50/50)
2. **5-10% edge:** Slight favorites
3. **10-15% edge:** Moderate confidence
4. **15-20% edge:** Strong picks
5. **20%+ edge:** Very strong picks

**How to use:**
- Check if high confidence actually = high accuracy
- Identify which confidence levels are most reliable
- Use for betting thresholds

**Tab 3: 🏒 Team Performance**

**What it shows:** Which teams we predict best/worst

**Top 10 Teams:**
- Teams we predict most accurately
- Green progress bars
- Use for targeting bets

**Bottom 10 Teams:**
- Teams we struggle to predict
- Orange progress bars
- Use for avoiding bets

---

### **🔬 PAGE 5: Deep Analysis**

**Purpose:** Advanced feature engineering insights

**Tab 1: 🔗 Feature Correlations**

**What it shows:** Which features work together

**How to read:**
- Green bars = positive correlation (move together)
- Red bars = negative correlation (move opposite)
- Higher bars = stronger relationship

**Use cases:**
- Understand feature interactions
- Identify redundant features
- See what drives predictions

**Example:**
```
rolling_corsi_10_diff ↔ rolling_fenwick_10_diff
Correlation: +0.85 (strong positive)

Interpretation:
Teams with high Corsi (shot attempts) also have 
high Fenwick (unblocked shots) - makes sense!
```

**Tab 2: 📊 Feature Distributions**

**What it shows:** Statistical patterns of features

**How to use:**
1. Select a feature from dropdown
2. See box plot (Home Win vs Away Win)
3. Review statistical summary
4. Check histogram

**Box Plot Interpretation:**
- Box = middle 50% of values
- Line in box = median
- Whiskers = range
- Dots = outliers

**Use for:**
- Understanding feature ranges
- Spotting anomalies
- Validating data quality

**Tab 3: 🎯 Confidence Analysis**

**What it shows:** Confidence vs actual accuracy

**5 Confidence Buckets:**
- 0-5%, 5-10%, 10-15%, 15-20%, 20%+

**Bar Chart:**
- Height = actual accuracy
- Red line = baseline (53.1%)
- Compare to see which confidence levels beat baseline

**3 Insight Cards:**
1. **High Confidence:** Accuracy at 20%+ edge
2. **Low Confidence:** Accuracy at 0-5% edge
3. **Confidence Edge:** Improvement from low to high

**Use for:**
- Validating model calibration
- Setting betting thresholds
- Understanding confidence reliability

---

### **🏆 PAGE 6: Leaderboards**

**Purpose:** Rankings, streaks, and matchup analysis

**Tab 1: 🏆 Team Rankings**

**What it shows:** Which teams we predict best

**3 Summary Cards:**
- 🥇 Best Predicted Team
- 📊 Average Accuracy
- 📉 Most Unpredictable Team

**Complete Rankings:**
- 🥇🥈🥉 Medals for top 3
- #4, #5, etc. for rest
- Sortable (accuracy, games)
- Filterable (minimum games)

**How to use:**
- **For betting:** Focus on top-ranked teams
- **For avoiding:** Skip bottom-ranked teams
- **For analysis:** Understand model strengths

**Sort Options:**
1. **Accuracy (High→Low):** See best teams first
2. **Accuracy (Low→High):** See worst teams first
3. **Games Analyzed:** See most-analyzed teams

**Tab 2: 🔥 Streak Tracker**

**What it shows:** Current hot/cold prediction streaks

**Hot Streaks (Green Cards):**
- 3+ correct predictions in a row
- Shows recent accuracy
- Shows streak length
- Good for betting targets

**Cold Streaks (Pink Cards):**
- 3+ incorrect predictions in a row
- Shows recent accuracy
- Shows streak length
- Good for avoiding

**How to use:**
- **Morning check:** See which teams are hot
- **Betting decisions:** Favor hot teams
- **Risk management:** Avoid cold teams
- **Pattern recognition:** Track momentum

**Tab 3: 📊 Best/Worst Matchups**

**What it shows:** Specific team pairings we predict well/poorly

**Best Matchups (Left, Green):**
- Top 10 team pairings
- Highest accuracy
- Shows record (e.g., 4/5 correct)

**Worst Matchups (Right, Red):**
- Bottom 10 team pairings
- Lowest accuracy
- Shows record (e.g., 1/3 correct)

**Requires:** 2+ games per matchup for reliability

**How to use:**
- **For betting:** Target best matchups
- **For avoiding:** Skip worst matchups
- **For analysis:** Understand style matchups

**Example:**
```
Best Matchup: BOS @ TOR (5/5 correct = 100%)
Interpretation: We predict BOS at TOR very well!

Worst Matchup: NYI @ NYR (1/4 correct = 25%)
Interpretation: This matchup is unpredictable for us.
```

---

### **❓ PAGE 7: Help**

**Purpose:** Quick reference and documentation

**Contains:**
- Metric definitions
- Navigation guide
- Pro tips
- Troubleshooting
- Contact info

---

## 🎓 UNDERSTANDING PREDICTIONS

### **How Predictions Work**

**1. Model Trains on Historical Data**
- 3,690 games from 2021-2024 seasons
- 141 features per game
- Learns patterns of wins/losses

**2. Features Engineered**
- **Team Strength:** Elo ratings
- **Recent Form:** Rolling averages (3, 5, 10 games)
- **Rest & Scheduling:** Back-to-back games, days off
- **Advanced Stats:** Corsi, Fenwick, xGoals, shot quality
- **Goaltending:** Save %, GSAx

**3. Model Predicts**
- Calculates probability for each team
- Home win probability (e.g., 58%)
- Away win probability (e.g., 42%)

**4. Confidence Calculated**
- Edge = |Home % - 50%|
- Higher edge = more confident
- Low edge (<5%) = toss-up
- High edge (>20%) = strong pick

### **Feature Importance**

**Top 5 Predictive Features:**

**1. is_b2b_diff (Back-to-back differential)**
- Most important feature
- Fatigue significantly impacts performance
- Negative coefficient = B2B hurts win probability

**2. rolling_corsi_10_diff (Possession)**
- 10-game shot attempt differential
- Positive coefficient = good possession helps
- MoneyPuck's advanced metric

**3. elo_diff_pre (Team strength)**
- Elo rating difference
- Stronger team more likely to win
- Proven over many seasons

**4. rolling_high_danger_shots_diff**
- Recent high-danger scoring chances
- Shot quality > shot quantity
- MoneyPuck metric

**5. rolling_save_pct_diff (Goaltending)**
- Recent goaltender performance
- Good goalie = more wins
- GSAx also important

### **Interpreting Confidence**

| Confidence | Meaning | Betting Advice |
|------------|---------|----------------|
| 0-5% | Toss-up | Avoid or skip |
| 5-10% | Slight favorite | Small bet if aligned |
| 10-15% | Moderate confidence | Reasonable bet |
| 15-20% | Strong pick | Good bet |
| 20%+ | Very strong | Best bets |

### **Model Limitations**

**What the model CAN'T predict:**
- ❌ Injuries (not announced pre-game)
- ❌ Starting goalies (until confirmed)
- ❌ Line combinations (last-minute changes)
- ❌ Motivation/intangibles
- ❌ Weather (for outdoor games)
- ❌ Referee tendencies

**What the model DOES consider:**
- ✅ Historical team performance
- ✅ Recent form (rolling averages)
- ✅ Rest and scheduling
- ✅ Team strength (Elo)
- ✅ Shot quality and quantity
- ✅ Goaltending stats (historical)

**Best practices:**
1. Use model as starting point
2. Add your own analysis
3. Check injury reports separately
4. Confirm starting goalies
5. Consider recent news

---

## 💰 BETTING ANALYSIS

### **Strategy Recommendations**

**For Beginners:**
1. Start with **Threshold Betting** at 60%
2. Only bet high confidence games (15%+ edge)
3. Track results for 20+ games before increasing stakes
4. Use small bet sizes ($1-5)

**For Intermediate:**
1. Try **Kelly Criterion** with 0.25 fraction
2. Bet on 10%+ edge games
3. Track ROI and adjust
4. Consider bankroll management

**For Advanced:**
1. Combine model with your analysis
2. Use **Kelly Criterion** with 0.25-0.5 fraction
3. Focus on best matchups (from Leaderboards)
4. Avoid teams on cold streaks
5. Target hot streak teams

### **Risk Management**

**Bankroll Management:**
- Never bet more than 5% of bankroll per game
- Start with 1-2% for testing
- Increase only after proven success

**Diversification:**
- Don't bet same team every night
- Spread across multiple games
- Balance favorites and underdogs

**Tracking:**
- Keep detailed records
- Track by strategy, confidence level, team
- Calculate ROI weekly
- Adjust based on results

### **When to Bet vs. Avoid**

**BET when:**
- ✅ High confidence (15%+ edge)
- ✅ Team on hot streak (Leaderboards)
- ✅ Best matchup (Leaderboards)
- ✅ Top-ranked team (Team Performance)
- ✅ Model + your analysis align

**AVOID when:**
- ❌ Low confidence (<5% edge)
- ❌ Team on cold streak
- ❌ Worst matchup
- ❌ Bottom-ranked team
- ❌ Model contradicts your analysis
- ❌ Key injury news (check separately)

---

## 🔧 TROUBLESHOOTING

### **Common Issues**

**Problem:** Dashboard won't start
```bash
# Solution 1: Check if port is busy
lsof -ti:8501 | xargs kill -9  # Kill process on port 8501
streamlit run dashboard_billion.py

# Solution 2: Use different port
streamlit run dashboard_billion.py --server.port 8502
```

**Problem:** "Module not found" error
```bash
# Solution: Install missing packages
pip install streamlit pandas numpy scikit-learn altair requests

# Or install all at once
pip install -r requirements.txt  # If file exists
```

**Problem:** Predictions show 0 games
```bash
# Solution: Generate predictions first
python predict_full.py

# Or for specific date
python predict_full.py 2025-11-11
```

**Problem:** Dashboard shows old predictions
```bash
# Solution: Refresh data cache
# In dashboard, click "🔄 Refresh Data" in sidebar
# Or press 'r' key in browser
# Or restart dashboard
```

**Problem:** "Cannot hash argument 'data'" error
```bash
# Already fixed in dashboard_billion.py
# If using old version, update to latest
```

**Problem:** Dashboard is slow
```bash
# Solution 1: Clear cache
streamlit cache clear

# Solution 2: Reduce data size
# Edit dashboard to load less historical data

# Solution 3: Use more powerful machine
# Dashboard requires ~1GB RAM for full dataset
```

---

## ❓ FAQ

**Q: How accurate is the model?**
A: 59.2% on out-of-sample test data (2024-25 season). Baseline (always picking home team) is 53.1%, so we beat baseline by 6.1 percentage points.

**Q: Can I use this for real betting?**
A: Model is for educational/research purposes. If betting:
- Start small
- Track results
- Never bet more than you can afford to lose
- Check your local gambling laws

**Q: How often should I update predictions?**
A: Daily, in the morning before games. Model uses pre-game data only.

**Q: What sports books should I use?**
A: Model assumes -110 odds (American standard). Your actual odds may vary. Shop lines for best value.

**Q: Can I predict playoffs?**
A: Model trained on regular season only. Playoff dynamics different (intensity, coaching adjustments, etc.).

**Q: How do I improve the model?**
A: Advanced users can:
- Add more features
- Try different algorithms
- Tune hyperparameters
- Include injury data
- Add goalie matchup data

**Q: What if a starting goalie changes?**
A: Model uses historical team goaltending stats, not specific goalies. Check starting goalies separately and adjust confidence accordingly.

**Q: How do I export predictions?**
A: Predictions auto-save to CSV files (`predictions_YYYY-MM-DD.csv`). Open in Excel or any spreadsheet program.

**Q: Can I run this on a server?**
A: Yes! Use:
```bash
streamlit run dashboard_billion.py --server.port 8501 --server.address 0.0.0.0
```
Then access from other devices on your network.

**Q: Is the data updated automatically?**
A: MoneyPuck data must be manually updated. NHL API data is fetched real-time for schedules.

---

## 🚀 ADVANCED USAGE

### **Custom Date Predictions**
```bash
# Predict specific date
python predict_full.py 2025-11-15

# Predict tomorrow
python predict_full.py $(date -d "+1 day" +%Y-%m-%d)  # Linux/Mac
```

### **Batch Predictions**
```bash
# Predict next 7 days
for i in {0..6}; do
    python predict_full.py $(date -d "+$i day" +%Y-%m-%d)
done
```

### **Exporting Dashboard Data**
In dashboard, use browser's built-in tools:
- Right-click tables → Copy
- Right-click charts → Save image
- Browser print → Save as PDF

### **Automated Daily Runs**
Set up cron job (Linux/Mac):
```bash
# Edit crontab
crontab -e

# Add this line (runs at 6 AM daily)
0 6 * * * cd /path/to/project && python predict_full.py
```

### **Custom Threshold Analysis**
Modify betting simulator parameters in code to test:
- Different odds formats
- Custom Kelly fractions
- Multiple confidence thresholds simultaneously

---

## 📞 GETTING HELP

**Issues with dashboard:**
1. Check terminal for error messages
2. Try clearing cache (Cmd+Shift+R in browser)
3. Restart dashboard
4. Check Python version (need 3.8+)

**Issues with predictions:**
1. Verify data files exist
2. Check internet connection (for NHL API)
3. Try running with verbose flag (if available)

**For bugs or questions:**
- Review this guide
- Check TROUBLESHOOTING section
- Review code comments
- Ask your team/instructor

---

## 🎉 TIPS FOR SUCCESS

**Daily Workflow:**
1. **Morning:** Generate predictions (`python predict_full.py`)
2. **Review:** Open dashboard, check Command Center
3. **Analysis:** View Today's Predictions
4. **Research:** Check Leaderboards for hot teams
5. **Decision:** Use Betting Simulator to test strategies
6. **Track:** Record your picks and results

**For Presentations:**
1. Start with Command Center (show KPIs)
2. Navigate to Today's Predictions (explain a game)
3. Show Betting Simulator (demonstrate ROI)
4. Deep Analysis (show feature correlations)
5. Leaderboards (show team rankings)
6. Highlight accuracy (59.2% vs 53.1% baseline)

**For Academic Work:**
1. Document your process
2. Screenshot key dashboard pages
3. Reference specific metrics
4. Explain model limitations
5. Discuss ethical considerations (gambling)

---

## ✅ QUICK REFERENCE

### **Essential Commands**
```bash
# Daily predictions
python predict_full.py

# Start dashboard
streamlit run dashboard_billion.py

# Different port
streamlit run dashboard_billion.py --server.port 8502

# Clear cache
streamlit cache clear
```

### **Key Files**
- `dashboard_billion.py` - Main dashboard
- `predict_full.py` - Prediction script
- `predictions_*.csv` - Output files
- `data/moneypuck_all_games.csv` - Historical data
- `group_report_2.md` - Project report

### **Key Metrics**
- **Accuracy:** 59.2% (test set)
- **Baseline:** 53.1% (home team wins)
- **Edge:** +6.1 percentage points
- **ROC-AUC:** 0.624
- **Features:** 141
- **Training Games:** 3,690

---

## 📚 ADDITIONAL RESOURCES

**Learn More:**
- MoneyPuck.com - Advanced hockey analytics
- NHL.com/stats - Official NHL statistics
- Evolving-Hockey.com - Advanced metrics

**Model Concepts:**
- Logistic Regression (classification)
- Elo Ratings (team strength)
- Rolling Averages (recent form)
- Expected Goals (shot quality)
- Calibration (probability accuracy)

---

**USER GUIDE v2.0**  
**Last Updated:** November 10, 2025  
**Status:** Complete & Production Ready

**Enjoy your NHL Prediction Dashboard!** 🏒🎯💰


