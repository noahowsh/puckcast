# 🚀 FUTURE IMPROVEMENTS & ROADMAP

**Status:** Ideas & Potential Features  
**Created:** November 10, 2025  
**Last Updated:** November 10, 2025

---

## 📋 OVERVIEW

This document tracks potential improvements and future features for the NHL Prediction Model. Each item is ranked by **impact** and **effort** to help prioritize development.

---

## 🎯 QUICK WINS (High Impact, Low Effort)

### **1. INJURY DATA INTEGRATION** 🏥 ⭐ HIGHEST PRIORITY
**Status:** Not Started  
**Impact:** 🔥🔥🔥🔥🔥 (Could boost accuracy by 3-5%)  
**Effort:** ⏱️⏱️ (2-3 hours)  
**Priority:** P0 (Critical)

**Description:**
Scrape daily injury reports and adjust predictions based on missing players.

**Data Sources:**
- NHL.com injury reports
- DailyFaceoff.com
- RotoBaller

**Implementation:**
- [ ] Create `src/nhl_prediction/injuries.py`
- [ ] Scrape injury data daily
- [ ] Adjust Elo/features for missing players
- [ ] Add injury alerts to dashboard
- [ ] Flag games with key injuries
- [ ] Weight by player importance (stars vs 4th liners)

**Dashboard Changes:**
- Add "🏥 Injury Report" widget
- Show injury alerts on game cards
- Flag high-impact injuries (red warning)

**Expected Outcome:**
- 3-5% accuracy improvement
- Better day-of predictions
- Avoid betting on injured-team games

---

### **2. SPORTSBOOK ODDS COMPARISON** 💰 ⭐ HIGH VALUE
**Status:** Not Started  
**Impact:** 🔥🔥🔥🔥 (Find +EV bets)  
**Effort:** ⏱️⏱️⏱️ (3-4 hours)  
**Priority:** P0 (Critical)

**Description:**
Pull real odds from sportsbooks, compare to model predictions, identify value bets.

**Data Sources:**
- The Odds API (free tier: 500 requests/month)
- SportsbookReview
- Covers.com

**Implementation:**
- [ ] Sign up for The Odds API
- [ ] Create `src/nhl_prediction/odds.py`
- [ ] Fetch odds for today's games
- [ ] Calculate implied probability (remove vig)
- [ ] Compare to model probability
- [ ] Highlight value bets (>5% edge)
- [ ] Add "Value Bet Alert" section

**Dashboard Changes:**
- Add "💰 Value Bets" page or section
- Show market odds vs model odds
- Calculate EV (Expected Value)
- Rank by value potential

**Formula:**
```
Edge = Model_Probability - Implied_Probability
EV = (Edge * Odds) - (1 - Edge)
```

**Expected Outcome:**
- Identify +EV bets automatically
- Learn from market disagreements
- Potential for profitable betting

---

### **3. STARTING GOALIE ALERTS** 🥅
**Status:** Not Started  
**Impact:** 🔥🔥🔥 (Goalie quality = huge impact)  
**Effort:** ⏱️⏱️ (1-2 hours)  
**Priority:** P1 (High)

**Description:**
Auto-fetch confirmed starting goalies throughout the day.

**Data Sources:**
- DailyFaceoff.com (most reliable)
- NHL.com (official, but late)
- Twitter API (team accounts)

**Implementation:**
- [ ] Scrape DailyFaceoff at 10 AM, 2 PM, 4 PM
- [ ] Update predictions if starter changes
- [ ] Flag backup vs elite goalie matchups
- [ ] Show goalie stats in dashboard

**Dashboard Changes:**
- Add "🥅 Goalie Matchup" to game cards
- Show save %, GSAx for confirmed starters
- Alert if elite/backup goalie starting unexpectedly

**Expected Outcome:**
- Better day-of confidence
- Avoid betting when elite goalie sits
- Target games with backup goalies

---

### **4. AUTOMATED DAILY RUNS** ⏰
**Status:** Not Started  
**Impact:** 🔥🔥 (Quality of life)  
**Effort:** ⏱️ (30 minutes)  
**Priority:** P2 (Medium)

**Description:**
Set up automated predictions every morning at 6 AM.

**Implementation:**
```bash
# Add to crontab
crontab -e

# Add this line (runs at 6 AM daily)
0 6 * * * cd /path/to/NHLpredictionmodel && /usr/bin/python3 predict_full.py >> logs/predictions.log 2>&1

# Optional: Send email notification
0 6 * * * cd /path/to/NHLpredictionmodel && /usr/bin/python3 predict_full.py && echo "Predictions ready" | mail -s "NHL Predictions" your@email.com
```

**Expected Outcome:**
- Never forget to run predictions
- Wake up to ready predictions
- Consistent daily workflow

---

## 🏗️ MEDIUM PROJECTS (High Impact, Medium Effort)

### **5. BET TRACKING SYSTEM** 📊 ⭐ PORTFOLIO PIECE
**Status:** Not Started  
**Impact:** 🔥🔥🔥🔥 (Learn what works)  
**Effort:** ⏱️⏱️⏱️⏱️ (4-6 hours)  
**Priority:** P1 (High)

**Description:**
Track actual bets and results over time to calculate real ROI.

**Features:**
- [ ] Log bets (date, team, odds, stake, result)
- [ ] Calculate real ROI, Sharpe ratio, max drawdown
- [ ] Track by strategy (threshold, Kelly, all games)
- [ ] Track by confidence level
- [ ] Track by team, day of week, matchup
- [ ] Visualize profit curve
- [ ] Compare paper trading vs real bets

**Schema:**
```sql
bets (
  id, date, game_id, 
  predicted_team, predicted_prob,
  bet_team, odds, stake,
  result, profit,
  strategy, confidence_level
)
```

**Dashboard Page:**
- "💰 Bet Tracker"
- Add bet form
- Performance dashboard
- Best/worst bets table
- Profit curve chart
- ROI by strategy/confidence
- Win rate trends

**Expected Outcome:**
- Understand actual edge
- Learn which strategies work
- Professional portfolio piece
- Data-driven betting decisions

---

### **6. LIVE SCORE UPDATES** 🔴
**Status:** Not Started  
**Impact:** 🔥🔥🔥 (Engagement)  
**Effort:** ⏱️⏱️⏱️ (3-4 hours)  
**Priority:** P2 (Medium)

**Description:**
Show live scores for today's games in dashboard.

**Implementation:**
- [ ] Poll NHL API every 5 minutes
- [ ] Update dashboard with live scores
- [ ] Show period, time remaining
- [ ] Show running record for the day
- [ ] Final scores for past days
- [ ] Compare predictions to results

**Dashboard Changes:**
- Add "🔴 Live Scores" widget to Command Center
- Green checkmark for correct predictions
- Red X for incorrect predictions
- Show daily win rate (updating live)

**Expected Outcome:**
- Track predictions in real-time
- Celebrate wins immediately
- Learn from losses
- Engagement and excitement

---

### **7. MOBILE-RESPONSIVE VERSION** 📱
**Status:** Not Started  
**Impact:** 🔥🔥 (Accessibility)  
**Effort:** ⏱️⏱️ (2-3 hours)  
**Priority:** P2 (Medium)

**Description:**
Optimize dashboard for mobile viewing.

**Implementation:**
- [ ] Responsive CSS (Streamlit handles most)
- [ ] Collapse sidebar on mobile
- [ ] Simplify charts for small screens
- [ ] Touch-friendly buttons
- [ ] Test on iPhone, Android, iPad

**Changes:**
- Stack metric cards vertically on mobile
- Simplify tables (fewer columns)
- Larger tap targets
- Horizontal scrolling for wide tables

**Expected Outcome:**
- Check predictions on-the-go
- Better user experience
- More accessible

---

### **8. CONFIDENCE ALERTS** 🔔
**Status:** Not Started  
**Impact:** 🔥🔥🔥 (Convenience)  
**Effort:** ⏱️⏱️⏱️ (2-3 hours)  
**Priority:** P2 (Medium)

**Description:**
Get notified for high-confidence games.

**Types:**
1. **Email:** Daily prediction summary (all games)
2. **SMS:** High confidence only (>20% edge)
3. **Slack:** Post to channel
4. **Discord:** Bot integration
5. **Push:** Mobile notifications

**Implementation:**
- [ ] Add notification settings to dashboard
- [ ] Email: Use `smtplib` or SendGrid
- [ ] SMS: Use Twilio
- [ ] Slack: Use webhooks
- [ ] Discord: Use bot API

**Example Email:**
```
Subject: NHL Predictions - Nov 10, 2025 (4 Games)

High Confidence Picks (>15% edge):
🔥 TOR vs BOS: TOR 58% (8% edge)

All Games:
- NYI @ NYR: NYR 52% (2% edge)
- BOS @ TOR: TOR 58% (8% edge)
...

View full analysis: [Dashboard Link]
```

**Expected Outcome:**
- Never miss strong picks
- Mobile alerts for on-the-go
- Professional touch

---

## 🚀 BIG PROJECTS (Very High Impact, High Effort)

### **9. PLAYER-LEVEL ANALYSIS** 👤 ⭐ GAME CHANGER
**Status:** Not Started  
**Impact:** 🔥🔥🔥🔥🔥 (Could boost accuracy 5-10%)  
**Effort:** ⏱️⏱️⏱️⏱️⏱️⏱️ (15-20 hours)  
**Priority:** P1 (High, but time-intensive)

**Description:**
Track individual player stats, predict based on lineups and injuries.

**Why:**
- Team stats mask individual impacts
- Star player absence = huge impact
- Line combinations matter
- Defensive pairings matter

**Data to Track:**
- Top line vs bottom line performance
- Star player on/off ice stats
- Line combinations (chemistry)
- Defensive pairings
- Player injuries/absences
- Recent player form (hot/cold streaks)

**Data Sources:**
- MoneyPuck (player-level xG, Corsi)
- Evolving-Hockey (RAPM, WAR)
- NaturalStatTrick (on/off ice)
- NHL API (player stats)

**Implementation:**
- [ ] Create player database
- [ ] Track player stats over time
- [ ] Scrape daily lineups
- [ ] Adjust team features based on lineup
- [ ] Weight by player importance (TOI, WAR)
- [ ] Model player chemistry

**Features:**
- `star_player_playing` (binary)
- `top_line_xg_rate`
- `top_pair_def_rating`
- `lineup_chemistry_score`

**Complexity:** High (requires player tracking)

**Expected Outcome:**
- 5-10% accuracy boost
- Better injury adjustments
- Lineup-specific predictions
- Professional-grade model

---

### **10. DEEP LEARNING MODEL** 🧠
**Status:** Not Started  
**Impact:** 🔥🔥🔥🔥 (Potentially +2-5% accuracy)  
**Effort:** ⏱️⏱️⏱️⏱️⏱️ (10-15 hours)  
**Priority:** P2 (Research project)

**Description:**
Try neural network instead of Logistic Regression.

**Approaches:**
1. **LSTM (Long Short-Term Memory):**
   - Time series patterns
   - Sequential game data
   - Learn momentum, streaks

2. **Transformer:**
   - Attention mechanism
   - Focus on important features
   - Better than LSTM for some tasks

3. **Ensemble:**
   - Combine DL + Logistic Regression
   - Average predictions
   - Best of both worlds

**Libraries:**
- TensorFlow / Keras
- PyTorch
- scikit-learn (for comparison)

**Process:**
- [ ] Prepare time series data
- [ ] Build LSTM model
- [ ] Hyperparameter tuning
- [ ] Compare to Logistic Regression
- [ ] Keep if better, discard if worse

**Risk:** Might not beat current model (DL needs more data)

**Expected Outcome:**
- Learn deep learning
- Potentially 2-5% improvement
- Research experience
- Portfolio talking point

---

### **11. PUBLIC WEBSITE / API** 🌐 ⭐ PORTFOLIO GOLD
**Status:** Not Started  
**Impact:** 🔥🔥🔥🔥🔥 (Career value)  
**Effort:** ⏱️⏱️⏱️⏱️⏱️⏱️ (8-12 hours)  
**Priority:** P1 (High for portfolio)

**Description:**
Deploy to cloud, make public, potential monetization.

**Features:**
- Public dashboard (no local setup needed)
- API endpoints for predictions
- User accounts (track bets)
- Subscription tiers
- Analytics dashboard

**Tech Stack:**
- **Hosting:** Heroku (easy), AWS (scalable), DigitalOcean
- **Database:** PostgreSQL (users, bets, predictions)
- **Auth:** Firebase, Auth0, or custom
- **Domain:** nhlpredictions.com, hockeypicks.ai
- **CDN:** Cloudflare

**Monetization Tiers:**
1. **Free:**
   - Basic predictions (today's games)
   - Limited historical data

2. **Pro ($5/month):**
   - Full historical data
   - Bet tracking
   - Email/SMS alerts
   - Value bet highlights

3. **Elite ($20/month):**
   - API access
   - Custom models
   - Advanced analytics
   - Priority support

**Implementation:**
- [ ] Deploy dashboard to Heroku
- [ ] Set up PostgreSQL database
- [ ] Add user authentication
- [ ] Create subscription system (Stripe)
- [ ] Build API endpoints
- [ ] Add analytics tracking
- [ ] Marketing page

**API Endpoints:**
```
GET  /api/predictions/{date}
GET  /api/team/{team_abbr}/stats
POST /api/bet (track bet)
GET  /api/performance (user stats)
```

**Expected Outcome:**
- Impressive portfolio piece
- Potential income ($100-500/mo)
- Reach more users
- Career opportunities

---

### **12. MULTI-SPORT EXPANSION** 🏀⚾🏈
**Status:** Not Started  
**Impact:** 🔥🔥🔥🔥🔥 (Portfolio showcase)  
**Effort:** ⏱️⏱️⏱️⏱️⏱️⏱️⏱️⏱️ (20-30 hours per sport)  
**Priority:** P3 (Low, but impressive)

**Description:**
Apply same model to NBA, MLB, NFL.

**Same Principles:**
- Elo ratings
- Rolling averages
- Rest/scheduling
- Advanced metrics
- Home/away splits

**NBA:**
- Data: Basketball-Reference, NBA API
- Metrics: eFG%, TS%, ORtg, DRtg, Pace
- Key: Back-to-backs, travel, injuries

**MLB:**
- Data: Fangraphs, MLB API
- Metrics: wOBA, FIP, wRC+, DRS
- Key: Pitching matchups, bullpen, ballpark

**NFL:**
- Data: Pro-Football-Reference, ESPN
- Metrics: DVOA, EPA, success rate
- Key: Injuries, weather, coaching

**Implementation:**
- [ ] Choose sport (NBA easiest)
- [ ] Adapt data ingestion
- [ ] Adapt feature engineering
- [ ] Train sport-specific model
- [ ] Add to dashboard (multi-sport tabs)

**Expected Outcome:**
- Prove model generalizes
- Massive portfolio value
- Multiple income streams
- Professional data scientist showcase

---

## 🔬 RESEARCH PROJECTS (Learn & Improve)

### **13. A/B TESTING FEATURES**
**Status:** Not Started  
**Effort:** ⏱️⏱️ (2-3 hours)  

**Description:**
Test removing features to see impact on accuracy.

**Process:**
- [ ] Remove top feature, retrain, test
- [ ] Remove bottom 20 features, test
- [ ] Try only top 20 features
- [ ] Compare accuracy, log loss, Brier

**Goal:** Simplify model without losing accuracy

---

### **14. PLAYOFF MODEL**
**Status:** Not Started  
**Effort:** ⏱️⏱️⏱️⏱️ (4-6 hours)  

**Description:**
Separate model for playoffs (different dynamics).

**Why Playoffs Different:**
- Higher intensity
- Coaching adjustments
- Series context (up 3-1 vs down 0-3)
- Star players matter more
- Home ice advantage differs

**Features:**
- Series score (0-0, 1-0, etc.)
- Previous series performance
- Playoff experience
- Rest days (7-game series = fatigue)

---

### **15. SCORE PREDICTION**
**Status:** Not Started  
**Effort:** ⏱️⏱️⏱️⏱️⏱️ (6-8 hours)  

**Description:**
Predict actual score, not just win/loss.

**Why:**
- Over/under bets
- Total goals markets
- More granular predictions

**Approach:**
- Regression instead of classification
- Predict goals for home/away separately
- Use Poisson distribution

---

### **16. IN-GAME PREDICTION UPDATES**
**Status:** Not Started  
**Effort:** ⏱️⏱️⏱️⏱️⏱️⏱️ (8-10 hours)  

**Description:**
Update win probability during games (like ESPN).

**Inputs:**
- Current score
- Time remaining
- Shots on goal
- Power plays
- Goalie pulled

**Use Case:**
- Live betting
- Engagement
- Learn from in-game dynamics

---

## 📊 PRIORITY MATRIX

```
                    HIGH IMPACT
                        ↑
    Injury Data    |    Player-Level
    Odds Comparison|    Public Website
    Bet Tracker    |    Deep Learning
────────────────────┼────────────────────→
    Goalie Alerts  |    Score Prediction  HIGH
    Live Scores    |    Multi-Sport       EFFORT
    Automation     |    In-Game Updates
                    ↓
                 LOW EFFORT
```

---

## 🎯 RECOMMENDED ROADMAP

### **Phase 1: Quick Wins (Week 1)**
1. Injury Data Integration (2-3 hours)
2. Sportsbook Odds Comparison (3-4 hours)
3. Bet Tracking System (4-6 hours)

**Total Effort:** 10-13 hours  
**Expected Impact:** +3-5% accuracy, +EV identification

---

### **Phase 2: Polish (Week 2)**
4. Starting Goalie Alerts (1-2 hours)
5. Automated Daily Runs (30 min)
6. Live Score Updates (3-4 hours)
7. Confidence Alerts (2-3 hours)
8. Mobile Optimization (2-3 hours)

**Total Effort:** 9-12 hours  
**Expected Impact:** Professional polish, automation

---

### **Phase 3: Level Up (Weeks 3-6)**
9. Player-Level Analysis (15-20 hours) OR
10. Public Website Deployment (8-12 hours)

**Total Effort:** 15-20 hours  
**Expected Impact:** Transformative upgrade or portfolio piece

---

### **Phase 4: Research (Ongoing)**
- A/B test features
- Try deep learning
- Playoff model
- Multi-sport expansion

---

## 📈 EXPECTED OUTCOMES BY PHASE

**After Phase 1:**
- Model uses injury data ✅
- Finding +EV bets automatically ✅
- Tracking real performance ✅
- **Accuracy:** ~62-64% (from 59.2%)

**After Phase 2:**
- Fully automated ✅
- Real-time updates ✅
- Mobile-friendly ✅
- Professional-grade ✅

**After Phase 3:**
- Player-level predictions ✅
- Public website ✅
- Portfolio-ready ✅
- **Accuracy:** ~64-67% (if player-level)

---

## 💡 NOTES & IDEAS

### **Potential Collaborators:**
- Classmates (for development help)
- Sports betting communities (for testing)
- NHL analytics Twitter (for feedback)

### **Potential Competitions:**
- Kaggle NHL prediction competitions
- MIT Sloan Sports Analytics Conference
- NHL Analytics conference

### **Learning Resources:**
- Evolving-Hockey blog (NHL analytics)
- FiveThirtyEight (Elo methodology)
- MoneyPuck blog (xG insights)
- Sports betting forums (strategy)

---

## ✅ COMPLETED FEATURES

- [x] MoneyPuck data integration
- [x] NHL API integration
- [x] Elo rating system
- [x] 141 engineered features
- [x] Logistic Regression model
- [x] 59.2% test accuracy
- [x] Streamlit dashboard (7 pages)
- [x] Betting simulator (3 strategies)
- [x] Performance analytics
- [x] Deep analysis (correlations, distributions)
- [x] Leaderboards (team rankings, streaks)
- [x] Goalie data integration
- [x] Daily prediction script
- [x] Comprehensive documentation
- [x] Testing framework

---

## 🚀 NEXT STEPS

**Immediate (This Week):**
1. Rebrand with new name/logo ← CURRENT
2. Pick Phase 1 feature to start

**Short Term (Next Month):**
- Complete Phase 1 (Quick Wins)
- Start Phase 2 (Polish)

**Long Term (Next 3-6 Months):**
- Complete Phase 3 (Level Up)
- Consider Phase 4 (Research)

---

**FUTURE IMPROVEMENTS v1.0**  
**Last Updated:** November 10, 2025  
**Status:** Roadmap Ready

**Ready to build the future! 🚀**

