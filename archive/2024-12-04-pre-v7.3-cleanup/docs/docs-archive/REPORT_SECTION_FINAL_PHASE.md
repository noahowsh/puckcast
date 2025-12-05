# Progress Report Section: Model Development & Next Steps

## CRITICAL: Data Leakage Prevention - xGoals Verification

### **Is xGoals Pre-Game Available?**

**Answer: YES** - When used correctly with temporal lagging.

**xGoals Calculation Timing:**
- Expected Goals (xG) is calculated **AFTER each game completes**
- MoneyPuck assigns xG value to each shot based on location, type, and situation
- Data is published to database after game ends

**How We Prevent Data Leakage:**
We use xGoals from **PRIOR games only** via `.shift(1)` temporal lagging:

```python
def _lagged_rolling(group: pd.Series, window: int) -> pd.Series:
    return group.shift(1).rolling(window).mean()
    #           ↑ THIS EXCLUDES CURRENT GAME!
```

**Example - Predicting Game 10:**
```
Game 1-9: xGoals = [2.3, 1.8, 2.7, 2.1, 3.0, 2.4, 1.9, 2.5, 2.8]  ← Known
Game 10:  xGoals = ???  ← UNKNOWN (hasn't happened yet!)

Feature for Game 10:
rolling_xg_for_5 = avg(Games 5,6,7,8,9) = 2.52  ← Uses 5-9 via .shift(1)
```

**Verification:**
- ✅ All features use `.shift(1)` for lagging
- ✅ Early-season Game 1: Features are 0/NaN (correct - no history)
- ✅ Can predict tonight's games using only completed games' data
- ✅ NO data leakage - verified in code

**Comparison to Other Stats:**
xGoals is identical to actual goals in terms of availability:
- Goals: Available after game → We use `.shift(1)` → Prior games only ✅
- xGoals: Available after game → We use `.shift(1)` → Prior games only ✅
- xGoals is just a BETTER version of goals (quality-adjusted)

---

## Model Performance - Version 2 (With xGoals)

### **Current Model Metrics (2023-24 Test Season):**

**Overall Performance:**
- **Test Accuracy:** 58.70%
- **Test Log Loss:** 0.6842
- **Test Brier Score:** 0.2437
- **Test ROC-AUC:** 0.6228

**Feature Count:**
- **Total Features:** 133
- **xGoals Features:** 13 (NEW)
- **Possession Features (Corsi/Fenwick):** 6 (NEW)
- **Shot Quality Features:** 3 (NEW)
- **Removed:** 8 broken PP/PK features

### **TOP 30 MOST IMPORTANT FEATURES:**

| Rank | Feature | Coefficient | Type |
|------|---------|-------------|------|
| 1 | `season_goal_diff_avg_diff` | 0.33 | Season Performance |
| 2 | `rolling_goal_diff_10_diff` | -0.31 | Recent Form |
| 3 | `rolling_high_danger_shots_5_diff` | 0.29 | **🆕 Shot Quality** |
| 4 | `is_b2b_home` | -0.24 | Rest/Fatigue |
| 5 | `shotsAgainst_roll_10_diff` | -0.23 | Shot Volume |
| 6 | `season_win_pct_diff` | -0.21 | Season Performance |
| 7 | `rolling_xg_for_5_diff` | -0.21 | **🆕 xGoals** |
| 8 | `shotsFor_roll_3_diff` | 0.19 | Shot Volume |
| 9 | `games_played_prior_away` | 0.19 | Season Progress |
| 10 | `rolling_corsi_5_diff` | -0.17 | **🆕 Possession** |
| 11 | `rolling_win_pct_10_diff` | 0.17 | Recent Form |
| 12 | `games_played_prior_home` | -0.17 | Season Progress |
| 13 | `is_b2b_away` | -0.16 | Rest/Fatigue |
| 14 | `rolling_xg_against_5_diff` | -0.16 | **🆕 xGoals** |
| 15 | `home_team_28` | -0.15 | Team Identity |
| 16 | `rolling_high_danger_shots_3_diff` | -0.15 | **🆕 Shot Quality** |
| 17 | `home_team_10` | 0.14 | Team Identity |
| 18 | `away_team_6` | -0.14 | Team Identity |
| 19 | `rolling_xg_for_3_diff` | 0.13 | **🆕 xGoals** |
| 20 | `rolling_goal_diff_5_diff` | 0.13 | Recent Form |
| ... | ... | ... | ... |
| 27 | `rolling_xg_against_10_diff` | 0.11 | **🆕 xGoals** |
| 30 | `rolling_fenwick_10_diff` | -0.11 | **🆕 Possession** |

**NEW Features in Top 30:**
- 🆕 **xGoals:** 4 features (ranks 7, 14, 19, 27)
- 🆕 **Possession:** 1 feature (rank 10)
- 🆕 **Shot Quality:** 2 features (ranks 3, 16)
- 🆕 **TOTAL:** 7 out of 30 top features are newly added

### **Key Findings:**

1. **Shot Quality is #3 Most Important!**
   - `rolling_high_danger_shots_5_diff` has very high importance
   - Validates MoneyPuck's shot danger classification

2. **xGoals Features are Highly Predictive:**
   - 4 xGoals features in top 30 (top 23%)
   - `rolling_xg_for_5_diff` is #7 (comparable to season goal differential)

3. **Faceoffs Dropped in Importance:**
   - Old model: Faceoffs were #1-3
   - New model: Not in top 30
   - Reason: xGoals and shot quality capture same underlying signal (puck possession)

4. **Rest/Fatigue Still Critical:**
   - `is_b2b_home` is #4 (back-to-back games hurt)
   - `is_b2b_away` is #13
   - Validates importance of schedule analysis

5. **Removed Broken Features:**
   - Old model had PP/PK% as #2 (but all zeros!)
   - Removal cleaned up model noise
   - xGoals provides better shot quality signal

---

## Model Challenges & Improvements Needed

### **Challenge: Accuracy Decreased from V1**

**V1 Model (With Broken PP/PK):** 62.18% accuracy  
**V2 Model (With xGoals):** 58.70% accuracy  
**Difference:** -3.48 percentage points ⚠️

### **Why Did Accuracy Drop?**

**Hypothesis 1: Removed "Lucky" Features**
- Old PP/PK features (all zeros) may have accidentally captured something useful
- Model was overfitting to noise that happened to correlate
- New model is cleaner but lost that accidental signal

**Hypothesis 2: Feature Interactions**
- xGoals features may need non-linear interactions
- Logistic Regression is linear - may not capture xGoals complexity
- HistGradientBoosting might perform better

**Hypothesis 3: Feature Scale Differences**
- xGoals on different scale than goals (0-5 vs 0-8)
- May need better feature engineering or normalization

**Hypothesis 4: Need Hyperparameter Tuning**
- Model trained with default C=1.0
- New features may need different regularization

### **Next Steps to Improve Performance:**

**IMMEDIATE (This Week):**

1. **Try HistGradientBoosting Classifier** ⭐
   - Can capture non-linear xGoals interactions
   - Expected: +2-4% accuracy improvement
   - Already implemented in codebase

2. **Hyperparameter Tuning**
   - Grid search for optimal C (Logistic Regression)
   - Grid search for HistGB parameters (learning_rate, max_depth, etc.)
   - Expected: +1-2% accuracy improvement

3. **Feature Engineering Round 2**
   - Add xGoals differential features (xG_for - xG_against)
   - Add xG over/under performance (goals - xGoals)
   - Add interaction terms (xGoals × rest days)
   - Expected: +1-2% accuracy improvement

4. **Calibration Analysis**
   - Check if probabilities are well-calibrated
   - Apply isotonic regression or Platt scaling
   - Expected: Better betting decisions (same accuracy, better probabilities)

**MEDIUM TERM (Next 2 Weeks):**

5. **Add Goalie Features** 🎯 (BIGGEST OPPORTUNITY)
   - Starting goalie save percentage
   - Goalie rest days (back-to-back starts)
   - Elite goalie indicator (Shesterkin, Vasilevskiy, etc.)
   - Expected: +3-5% accuracy improvement (HUGE!)

6. **5v5 Situation-Specific Features**
   - MoneyPuck has even-strength data separate
   - 5v5 performance more predictive than overall
   - Filter xGoals to 5v5 situations only
   - Expected: +1-2% accuracy improvement

7. **Score-Adjusted Metrics**
   - MoneyPuck provides score-adjusted stats
   - Accounts for teams trailing shooting more
   - More accurate reflection of team strength
   - Expected: +0.5-1% accuracy improvement

**LONG TERM (Final Phase):**

8. **Model Ensemble**
   - Combine Logistic Regression + HistGB + XGBoost
   - Weighted average of predictions
   - Expected: +1-3% accuracy improvement

9. **Deep Learning (Optional - If Time Permits)**
   - LSTM for sequential game history
   - Attention mechanism for important games
   - Expected: +2-4% accuracy improvement (but high complexity)

10. **Live Validation**
    - Paper trade current season (2024-25)
    - Compare predictions to actual results
    - Monitor model drift and recalibrate

---

## Final Phase: Betting Market Integration

### **Phase 1: Data Collection (Week 1)**

**Objective:** Obtain historical betting odds for model validation

**Tasks:**
1. **Find Betting Odds Source:**
   - Option A: Scrape OddsPortal.com (free, historical data)
   - Option B: Purchase from SportsOddsHistory.com (~$100 for NHL season)
   - Option C: Use OddsAPI (free tier: 500 requests/month)

2. **Download 2023-24 Betting Odds:**
   - Moneyline odds (home/away)
   - Over/Under totals (optional)
   - Opening lines + closing lines

3. **Data Cleaning:**
   - Convert American odds to implied probabilities
   - Remove vig (bookmaker's margin)
   - Match odds to our games by date + teams

**Deliverable:** CSV with columns: `[gameId, gameDate, home_team, away_team, home_odds, away_odds, home_prob_fair, away_prob_fair]`

---

### **Phase 2: Model-Market Comparison (Week 2)**

**Objective:** Determine if our model has edge over betting markets

**Tasks:**
1. **Calculate Market Probabilities:**
   ```python
   # American odds to implied probability
   def odds_to_prob(odds):
       if odds > 0:
           return 100 / (odds + 100)
       else:
           return abs(odds) / (abs(odds) + 100)
   
   # Remove vig (make probabilities sum to 1.0)
   def remove_vig(prob_home, prob_away):
       total = prob_home + prob_away
       return prob_home / total, prob_away / total
   ```

2. **Compare Calibration:**
   - Model Brier Score vs Market Brier Score
   - Which is better calibrated?

3. **Identify Disagreements:**
   - Find games where |model_prob - market_prob| > 5%
   - Example: Model says 65% home win, market says 55%
   - These are betting opportunities!

4. **Analyze Edge by Feature:**
   - Do we beat market on high xGoals games?
   - Do we beat market on back-to-back games?
   - Where is our advantage?

**Deliverable:** Analysis report showing:
- Model vs Market calibration comparison
- List of games with biggest disagreements
- Feature-specific edge analysis

---

### **Phase 3: Betting Simulation (Week 3)**

**Objective:** Simulate betting strategies to estimate ROI

**Strategy 1: Threshold Betting**
```python
# Only bet when model is confident AND disagrees with market
def threshold_strategy(model_prob, market_prob, threshold=0.05):
    edge = model_prob - market_prob
    if abs(edge) > threshold:
        # Bet on team with higher model probability
        return 'BET' if edge > 0 else 'NO_BET'
    return 'NO_BET'
```

**Strategy 2: Kelly Criterion**
```python
# Optimal bet sizing based on edge
def kelly_bet_size(model_prob, market_prob, bankroll, kelly_fraction=0.25):
    # Kelly formula: (p*odds - 1) / (odds - 1)
    odds = market_prob_to_odds(market_prob)
    kelly_pct = (model_prob * odds - 1) / (odds - 1)
    
    # Fractional Kelly (25% to reduce variance)
    bet_size = bankroll * kelly_pct * kelly_fraction
    return max(0, bet_size)  # Never bet negative
```

**Metrics to Track:**
- **ROI:** Return on investment percentage
- **Win Rate:** Proportion of bets won
- **Sharpe Ratio:** Risk-adjusted return
- **Max Drawdown:** Largest losing streak
- **Profit Factor:** Gross wins / Gross losses

**Deliverable:** Simulation results showing:
- ROI by strategy (threshold vs Kelly)
- ROI by confidence level (high/medium/low)
- ROI by feature (xGoals games, B2B games, etc.)
- Bankroll curve over season
- Risk metrics (Sharpe, drawdown)

---

### **Phase 4: Live Validation (Week 4 + Ongoing)**

**Objective:** Test model on current season (2024-25) with paper trading

**Setup:**
1. **Weekly Model Updates:**
   - Every Monday: Download latest MoneyPuck data
   - Retrain model with updated data
   - Generate predictions for upcoming week

2. **Paper Trading Process:**
   ```python
   # Example: Predict Tuesday's games on Monday night
   
   # 1. Get today's games (not yet played)
   todays_games = get_games_for_date('2024-11-11')
   
   # 2. Get betting odds from OddsAPI
   odds = fetch_odds_for_date('2024-11-11')
   
   # 3. Generate model predictions
   predictions = model.predict_proba(todays_games_features)
   
   # 4. Identify betting opportunities
   opportunities = find_edge(predictions, odds, threshold=0.05)
   
   # 5. Log recommended bets (DO NOT actually bet yet!)
   log_paper_trades(opportunities, date='2024-11-11')
   
   # 6. Next day: Record actual results
   update_paper_trade_results('2024-11-11')
   ```

3. **Track Performance:**
   - Weekly ROI updates
   - Cumulative profit/loss tracking
   - Compare to:
     - Always bet home
     - Always bet favorite
     - Random betting
     - Professional handicapper results (if available)

4. **Model Monitoring:**
   - Watch for accuracy drift
   - Recalibrate if Brier score increases >10%
   - Investigate large losses (were they bad luck or model error?)

**Deliverable:** Live performance dashboard showing:
- Weekly prediction accuracy
- Cumulative ROI curve
- Win/loss breakdown
- Best/worst predictions
- Model calibration over time

---

### **Phase 5: Final Report & Recommendations**

**Objective:** Synthesize findings and provide final recommendations

**Report Sections:**

1. **Executive Summary**
   - Model performance summary
   - Betting simulation results
   - ROI estimates (conservative, expected, optimistic)
   - Final recommendation (bet or not bet)

2. **Model Performance**
   - Accuracy metrics (train/validation/test)
   - Calibration analysis
   - Feature importance rankings
   - Comparison to baseline/benchmark

3. **Market Analysis**
   - Model vs market calibration
   - Where model has edge
   - Where model struggles
   - Feature-specific advantages

4. **Betting Simulation Results**
   - ROI by strategy
   - Risk metrics (Sharpe, drawdown)
   - Optimal bet sizing
   - Confidence thresholds

5. **Live Validation Results** (if completed)
   - Paper trading performance
   - Accuracy on current season
   - Model stability over time

6. **Recommendations**
   - **If ROI > 5%:** "Model shows strong edge - recommend live betting with strict bankroll management"
   - **If ROI 2-5%:** "Model shows modest edge - recommend small-scale betting or continued paper trading"
   - **If ROI 0-2%:** "Model roughly matches market - recommend paper trading only, continue improving"
   - **If ROI < 0%:** "Market is better calibrated - DO NOT bet, use as learning exercise only"

7. **Future Improvements**
   - Prioritized list of enhancements
   - Expected impact of each
   - Implementation difficulty

8. **Lessons Learned**
   - What worked well
   - What didn't work
   - Surprises/unexpected findings
   - Skills developed

**Deliverable:** Final report (PDF) + presentation slides

---

## Timeline Summary

| Week | Phase | Key Deliverables |
|------|-------|------------------|
| 1 | Model Improvement | HistGB model, hyperparameter tuning, improved accuracy |
| 2 | Odds Collection | Historical odds CSV, cleaned and matched to games |
| 3 | Model-Market Comparison | Calibration analysis, edge identification |
| 4 | Betting Simulation | ROI estimates, strategy comparison, risk metrics |
| 5+ | Live Validation (Optional) | Paper trading results, live accuracy tracking |
| Final | Report & Presentation | Complete report, recommendations, lessons learned |

---

## Critical Success Factors

### **For Academic Success:**
✅ Demonstrate rigorous methodology
✅ Proper temporal validation (no data leakage)
✅ Clear documentation of all steps
✅ Honest reporting of results (even if negative)
✅ Thoughtful analysis of failures and successes

### **For Betting Success (Stretch Goal):**
✅ Model accuracy > 57% (above baseline)
✅ Better calibration than markets
✅ Consistent edge identification
✅ Positive ROI in simulations
✅ Stable performance over time

---

## Key Risks & Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| **Market is too efficient** | No betting edge | Focus on model quality for academic credit, learn from comparison |
| **Data leakage introduces bias** | Overestimated performance | Triple-check all features use .shift(1), verify with early-season checks |
| **Model overfits to training data** | Poor test performance | Strict temporal validation, regularization, cross-validation |
| **Betting odds unavailable** | Can't validate vs market | Use alternative sources, consider synthesizing from historical spreads |
| **Model accuracy drops on new data** | Unreliable predictions | Weekly recalibration, monitor drift, retrain regularly |

---

## Conclusion

We have successfully:
1. ✅ Built a clean prediction pipeline with NO data leakage
2. ✅ Integrated MoneyPuck's advanced analytics (xGoals, shot quality)
3. ✅ Verified all features are pre-game available
4. ✅ Identified top predictive features (shot quality #3, xGoals #7)
5. ✅ Removed broken features (PP/PK zeros)

**Current Status:**
- Model accuracy: 58.70% (needs improvement)
- Feature quality: High (xGoals, shot quality working)
- Data leakage: ✅ None - fully verified
- Ready for: Hyperparameter tuning + HistGB model

**Next Immediate Steps:**
1. Train HistGradientBoosting model (expected +3-5% accuracy)
2. Tune hyperparameters with grid search
3. Add goalie features (biggest opportunity)
4. Proceed to betting market integration once accuracy > 60%

**The foundation is solid - now we optimize and validate against the market!** 🚀

