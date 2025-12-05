# Betting Integration - Quick Start Guide

This directory contains documentation and code for integrating betting analysis into the NHL prediction model.

## 📁 Files Created

### Documentation
1. **`betting_integration_plan.md`** - Comprehensive 40+ page guide covering:
   - How to obtain betting odds data
   - Converting American odds to probabilities
   - Removing bookmaker vig
   - Betting simulation strategies (threshold, Kelly Criterion)
   - ROI analysis and metrics
   - Implementation timeline

### Code
2. **`../src/nhl_prediction/betting.py`** - Core betting utilities module:
   - `american_to_probability()` - Convert odds to probabilities
   - `remove_vig_proportional()` - Remove bookmaker overround
   - `process_betting_odds()` - Full odds processing pipeline
   - `kelly_criterion()` - Optimal bet sizing
   - `simulate_threshold_betting()` - Fixed stake strategy
   - `simulate_kelly_betting()` - Kelly Criterion strategy
   - `calculate_roi_metrics()` - Comprehensive performance metrics
   - `compare_model_vs_market()` - Model vs market comparison

3. **`../src/nhl_prediction/betting_example.py`** - Example usage script:
   - Demonstrates complete workflow
   - Creates visualizations
   - Runs multiple betting strategies
   - Generates performance report

## 🚀 Quick Start

### Step 1: Get Betting Odds Data

**Option A: The Odds API (Recommended)**
```bash
# Sign up at https://the-odds-api.com/
# Free tier: 500 requests/month

curl "https://api.the-odds-api.com/v4/sports/icehockey_nhl/odds/?apiKey=YOUR_API_KEY&regions=us&markets=h2h&oddsFormat=american"
```

**Option B: Historical Data**
- Search Kaggle for "NHL betting odds historical"
- Check OddsPortal.com (requires scraping)
- Purchase from sports data vendors

### Step 2: Format Your Data

Create `data/betting_odds_20232024.csv` with columns:
```
game_id,game_date,home_team,away_team,home_odds,away_odds,bookmaker
2023020001,2023-10-10,Tampa Bay Lightning,Nashville Predators,-150,+130,DraftKings
2023020002,2023-10-10,Pittsburgh Penguins,Chicago Blackhawks,-200,+175,DraftKings
...
```

### Step 3: Run Analysis

```python
# From project root
python -m nhl_prediction.betting_example
```

This will:
1. Load your model predictions
2. Process betting odds
3. Run multiple betting simulations
4. Generate comprehensive report
5. Create visualizations in `reports/betting_analysis.png`

### Step 4: Interpret Results

**Key Metrics to Check:**

✅ **ROI (Return on Investment)**
- Break-even: ~0%
- Good: 2-5%
- Excellent: 5-10%
- Suspicious: >10% (likely overfitting)

✅ **Win Rate**
- Need >52.4% on evenly-matched games to beat vig
- Your actual needed rate depends on odds distribution

✅ **Model vs Market**
- Brier Score: Lower is better
- If model > market: Market is more accurate
- If model < market: You might have an edge!

✅ **Sharpe Ratio**
- Measures risk-adjusted returns
- Higher is better (>1.0 is good)

## 📊 Expected Workflow

```
1. Obtain odds data (Week 1)
   ↓
2. Run betting_example.py to get baseline results
   ↓
3. Analyze which strategies perform best
   ↓
4. Tune thresholds/parameters
   ↓
5. Validate on new season (2024-25)
   ↓
6. Write up findings in report
```

## ⚠️ Important Notes

### Reality Check
- **Markets are very efficient** - don't expect huge ROI
- **Sample size matters** - 1 season isn't enough to prove skill vs luck
- **Overfitting risk** - if it seems too good to be true, it probably is

### Validation Strategy
1. **Backtest on 2023-24** (what you have predictions for)
2. **Paper trade 2024-25** (true out-of-sample test)
3. **Only trust results that hold up on new data**

### Academic Value
Even if ROI is negative, this analysis shows:
- How to evaluate ML models against real-world benchmarks
- Understanding of betting markets and efficiency
- Practical data science skills (simulation, risk metrics)
- Critical thinking about model limitations

## 🎯 Next Steps

### Immediate (This Week)
- [ ] Sign up for The Odds API or find historical data source
- [ ] Download/fetch odds for 2023-24 season
- [ ] Format data according to schema above

### Short Term (Next 2 Weeks)
- [ ] Run `betting_example.py` with real odds data
- [ ] Experiment with different edge thresholds (3%, 5%, 8%, 10%)
- [ ] Try different Kelly fractions (0.1, 0.25, 0.5)
- [ ] Analyze which games model got right/wrong vs market

### Medium Term (Next Month)
- [ ] Write betting analysis section for group report
- [ ] Create presentation slides with key findings
- [ ] Add betting tab to Streamlit dashboard (optional)
- [ ] Prepare for Q&A about methodology

### Long Term (Ongoing)
- [ ] Track 2024-25 season predictions vs odds
- [ ] Build automated daily prediction system
- [ ] Consider ensemble methods (combine model + market)

## 📚 Further Reading

### Betting Markets & Efficiency
- "The Wisdom of Crowds" by James Surowiecki
- "Taking Chances" by John Haigh (Chapter on sports betting)
- Academic papers on sports betting market efficiency

### Kelly Criterion
- Original paper: "A New Interpretation of Information Rate" (1956)
- "Fortune's Formula" by William Poundstone (popular science book)
- Fractional Kelly for risk management

### NHL Analytics
- "Hockey Abstract" series
- Articles on Evolving-Hockey.com
- Academic studies on NHL predictability

## 🤝 Questions?

If you're stuck:
1. Check `betting_integration_plan.md` for detailed explanations
2. Review code comments in `betting.py`
3. Run example with synthetic data first (as shown in `betting_example.py`)
4. Verify calculations manually for a few games

## 📈 Success Metrics

Your betting integration is successful if you can answer:

1. ✅ **How does our model compare to betting markets?**
   - Brier score comparison
   - Calibration comparison
   - Probability correlation

2. ✅ **Where does our model disagree with markets?**
   - Which features drive differences?
   - Are disagreements systematic?

3. ✅ **Could we theoretically profit?**
   - What ROI did simulations achieve?
   - How sensitive to thresholds/parameters?

4. ✅ **What did we learn?**
   - About model strengths/weaknesses
   - About NHL predictability
   - About betting market efficiency

Good luck! This is where your project gets really interesting! 🏒💰



