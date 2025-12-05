# Betting Integration Plan - NHL Prediction Model

**Objective:** Integrate sports betting odds, convert to implied probabilities, compare against our model predictions, and simulate betting strategies to evaluate potential ROI.

---

## Table of Contents
1. [Overview](#overview)
2. [Obtaining Betting Odds Data](#obtaining-betting-odds-data)
3. [Converting Odds to Probabilities](#converting-odds-to-probabilities)
4. [Model Comparison Framework](#model-comparison-framework)
5. [Betting Strategy Simulation](#betting-strategy-simulation)
6. [ROI Analysis](#roi-analysis)
7. [Implementation Plan](#implementation-plan)
8. [Risk Management](#risk-management)

---

## Overview

### What We're Building

A comprehensive betting analysis system that:
1. **Fetches** historical betting odds for NHL games
2. **Converts** odds to implied probabilities (accounting for bookmaker vig)
3. **Compares** our model's probabilities vs market probabilities
4. **Identifies** +EV (positive expected value) betting opportunities
5. **Simulates** betting strategies over historical data
6. **Calculates** ROI, Sharpe ratio, and drawdown metrics
7. **Visualizes** performance vs "betting the model blindly" vs "selective betting"

### Key Concepts

**Expected Value (EV):**
```
EV = (Win Probability × Profit if Win) - (Loss Probability × Stake)
```

**Positive EV occurs when:**
```
Model Probability > Market Implied Probability (after removing vig)
```

**The Efficient Market Hypothesis:**
- Betting markets aggregate information from millions of bettors
- Hard to consistently beat (like stock markets)
- Our edge must come from **superior information** (our features) or **market inefficiencies**

---

## Obtaining Betting Odds Data

### Data Sources

#### Option 1: **The Odds API** (Recommended - Free Tier Available)
- **URL:** https://the-odds-api.com/
- **Free Tier:** 500 requests/month
- **Coverage:** Major sportsbooks (DraftKings, FanDuel, BetMGM, etc.)
- **Historical Data:** Available for purchase or via archive
- **Formats:** Moneyline (American odds), Decimal, Fractional

**Example API Call:**
```python
import requests

API_KEY = 'your_api_key'
SPORT = 'icehockey_nhl'
REGION = 'us'  # or 'us', 'uk', 'au'
MARKET = 'h2h'  # head-to-head (moneyline)

url = f'https://api.the-odds-api.com/v4/sports/{SPORT}/odds/'
params = {
    'apiKey': API_KEY,
    'regions': REGION,
    'markets': MARKET,
    'oddsFormat': 'american',  # or 'decimal'
}

response = requests.get(url, params=params)
odds_data = response.json()
```

#### Option 2: **Sportradar API**
- More comprehensive but expensive
- Official NHL data partner

#### Option 3: **Web Scraping (Legal Gray Area)**
- Sites like OddsPortal.com archive historical odds
- Requires careful scraping etiquette and robots.txt compliance
- May violate terms of service

#### Option 4: **Manual Historical Data**
- Kaggle datasets with historical NHL betting odds
- Search for "NHL betting odds historical dataset"

### Data We Need

For each game in our test set (2023-24 season):
- **Game ID / Date / Teams**
- **Home Team Moneyline Odds** (e.g., -150)
- **Away Team Moneyline Odds** (e.g., +130)
- **Timestamp** of odds (closing line is most important)
- **Sportsbook** (average multiple books for best estimate)

### Ideal Odds Timing

- **Opening Line:** First odds posted (days before game) - less accurate
- **Closing Line:** Final odds before puck drop - **most accurate** (incorporates all information)

We should use **closing line** for comparison, as it represents the market's best estimate.

---

## Converting Odds to Probabilities

### American Odds Format

Most US sportsbooks use American odds:
- **Negative odds (favorite):** -150 means bet $150 to win $100
- **Positive odds (underdog):** +130 means bet $100 to win $130

### Conversion Formulas

#### American Odds → Implied Probability

**For negative odds (favorites):**
```python
def american_to_prob_favorite(odds):
    """
    odds: negative integer (e.g., -150)
    returns: implied probability
    """
    return abs(odds) / (abs(odds) + 100)

# Example: -150 → 150 / (150 + 100) = 0.60 (60%)
```

**For positive odds (underdogs):**
```python
def american_to_prob_underdog(odds):
    """
    odds: positive integer (e.g., +130)
    returns: implied probability
    """
    return 100 / (odds + 100)

# Example: +130 → 100 / (130 + 100) = 0.4348 (43.48%)
```

**Combined function:**
```python
def american_to_probability(odds):
    """Convert American odds to implied probability."""
    if odds < 0:
        # Favorite
        return abs(odds) / (abs(odds) + 100)
    else:
        # Underdog
        return 100 / (odds + 100)
```

### The "Vig" Problem (Overround)

Bookmakers build in a profit margin (vig/juice). Example:

```
Home Team: -150 (60% implied)
Away Team: +130 (43.48% implied)
Total: 60% + 43.48% = 103.48%
```

Total > 100% → bookmaker's edge is 3.48%

### Removing the Vig (True Probabilities)

**Method 1: Proportional Adjustment**
```python
def remove_vig_proportional(prob_home, prob_away):
    """
    Remove vig by proportionally scaling probabilities to sum to 1.
    """
    total = prob_home + prob_away
    true_prob_home = prob_home / total
    true_prob_away = prob_away / total
    return true_prob_home, true_prob_away

# Example:
# prob_home = 0.60, prob_away = 0.4348
# total = 1.0348
# true_home = 0.60 / 1.0348 = 0.5799 (57.99%)
# true_away = 0.4348 / 1.0348 = 0.4201 (42.01%)
```

**Method 2: Additive Adjustment**
```python
def remove_vig_additive(prob_home, prob_away):
    """
    Remove vig by subtracting half the overround from each probability.
    """
    overround = (prob_home + prob_away) - 1.0
    true_prob_home = prob_home - (overround / 2)
    true_prob_away = prob_away - (overround / 2)
    return true_prob_home, true_prob_away
```

**Method 3: Power Method (Shin's Method - Most Accurate)**
More complex but accounts for informed vs uninformed bettors. For simplicity, use Method 1.

### Implementation

```python
import pandas as pd

def process_betting_odds(odds_df):
    """
    odds_df: DataFrame with columns ['game_id', 'home_odds', 'away_odds']
    returns: DataFrame with true market probabilities
    """
    # Convert American odds to raw probabilities
    odds_df['home_prob_raw'] = odds_df['home_odds'].apply(american_to_probability)
    odds_df['away_prob_raw'] = odds_df['away_odds'].apply(american_to_probability)
    
    # Calculate vig
    odds_df['total_prob'] = odds_df['home_prob_raw'] + odds_df['away_prob_raw']
    odds_df['vig_percent'] = (odds_df['total_prob'] - 1.0) * 100
    
    # Remove vig (proportional method)
    odds_df['market_prob_home'] = odds_df['home_prob_raw'] / odds_df['total_prob']
    odds_df['market_prob_away'] = odds_df['away_prob_raw'] / odds_df['total_prob']
    
    return odds_df
```

---

## Model Comparison Framework

### Metrics to Track

#### 1. **Calibration Comparison**
Plot calibration curves for:
- Our model probabilities
- Market probabilities (after removing vig)

Market should be well-calibrated (efficient market hypothesis).

#### 2. **Brier Score Comparison**
```python
from sklearn.metrics import brier_score_loss

model_brier = brier_score_loss(y_true, model_probs)
market_brier = brier_score_loss(y_true, market_probs)

print(f"Model Brier Score: {model_brier:.4f}")
print(f"Market Brier Score: {market_brier:.4f}")
```

**Lower is better.** Market will likely have lower Brier score (they're very good).

#### 3. **Log Loss Comparison**
```python
from sklearn.metrics import log_loss

model_ll = log_loss(y_true, model_probs)
market_ll = log_loss(y_true, market_probs)
```

#### 4. **Probability Difference Distribution**
```python
prob_diff = model_probs - market_probs

# Analyze:
# - Mean difference (systematic bias?)
# - Std of difference (how often do we disagree?)
# - Games where |diff| > threshold (betting opportunities)
```

### Identifying Edge

**Our model has an edge when:**
```python
# For betting on home team to win:
edge_home = model_prob_home - market_prob_home

# Positive edge → model thinks home team more likely to win than market does
# Negative edge → model thinks home team less likely to win
```

**Visualization:**
```python
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 6))
plt.scatter(market_probs, model_probs, alpha=0.5)
plt.plot([0, 1], [0, 1], 'r--', label='Perfect Agreement')
plt.xlabel('Market Probability (Home Win)')
plt.ylabel('Model Probability (Home Win)')
plt.title('Model vs Market Probability Comparison')
plt.legend()
plt.grid(alpha=0.3)
plt.show()
```

Points above the red line = model more bullish than market (potential home bets)
Points below the red line = model more bearish than market (potential away bets)

---

## Betting Strategy Simulation

### Strategy 1: Threshold-Based Betting

**Concept:** Only bet when our edge exceeds a threshold.

```python
def simulate_threshold_betting(games_df, edge_threshold=0.05, bet_size=100):
    """
    games_df: DataFrame with columns:
        - model_prob_home: our model's probability
        - market_prob_home: market probability (vig removed)
        - home_odds: American odds for home team
        - away_odds: American odds for away team
        - home_win: actual outcome (1 or 0)
    
    edge_threshold: minimum probability edge to place bet (e.g., 0.05 = 5%)
    bet_size: fixed stake per bet in dollars
    
    returns: betting results DataFrame
    """
    results = []
    bankroll = 0
    
    for idx, game in games_df.iterrows():
        edge_home = game['model_prob_home'] - game['market_prob_home']
        edge_away = (1 - game['model_prob_home']) - (1 - game['market_prob_home'])
        
        bet_placed = None
        profit = 0
        
        # Check if we have sufficient edge on home team
        if edge_home >= edge_threshold:
            bet_placed = 'home'
            if game['home_win'] == 1:
                # Win: calculate payout from American odds
                if game['home_odds'] < 0:
                    profit = bet_size * (100 / abs(game['home_odds']))
                else:
                    profit = bet_size * (game['home_odds'] / 100)
            else:
                # Loss
                profit = -bet_size
        
        # Check if we have sufficient edge on away team
        elif edge_away >= edge_threshold:
            bet_placed = 'away'
            if game['home_win'] == 0:
                # Win
                if game['away_odds'] < 0:
                    profit = bet_size * (100 / abs(game['away_odds']))
                else:
                    profit = bet_size * (game['away_odds'] / 100)
            else:
                # Loss
                profit = -bet_size
        
        if bet_placed:
            bankroll += profit
            results.append({
                'game_id': game.get('game_id', idx),
                'bet_on': bet_placed,
                'edge': edge_home if bet_placed == 'home' else edge_away,
                'model_prob': game['model_prob_home'] if bet_placed == 'home' else (1 - game['model_prob_home']),
                'market_prob': game['market_prob_home'] if bet_placed == 'home' else (1 - game['market_prob_home']),
                'odds': game['home_odds'] if bet_placed == 'home' else game['away_odds'],
                'outcome': 'win' if profit > 0 else 'loss',
                'profit': profit,
                'cumulative_profit': bankroll,
            })
    
    return pd.DataFrame(results), bankroll
```

### Strategy 2: Kelly Criterion (Optimal Bet Sizing)

**Concept:** Bet a fraction of bankroll proportional to your edge.

**Kelly Formula:**
```
Kelly Fraction = (p × b - q) / b

where:
p = model probability of winning
q = 1 - p (probability of losing)
b = decimal odds - 1 (net odds received)
```

**Implementation:**
```python
def kelly_criterion(model_prob, odds):
    """
    Calculate optimal bet size using Kelly Criterion.
    
    model_prob: your model's win probability
    odds: American odds
    
    returns: fraction of bankroll to bet (0 to 1)
    """
    # Convert American odds to decimal
    if odds < 0:
        decimal_odds = 1 + (100 / abs(odds))
    else:
        decimal_odds = 1 + (odds / 100)
    
    b = decimal_odds - 1  # net odds
    p = model_prob
    q = 1 - p
    
    kelly_frac = (p * b - q) / b
    
    # Never bet more than Kelly suggests, often bet less (fractional Kelly)
    # Many professionals use 0.25 to 0.5 of Kelly to reduce variance
    return max(0, kelly_frac)  # Don't bet if Kelly is negative

def simulate_kelly_betting(games_df, kelly_fraction=0.25, starting_bankroll=10000):
    """
    Simulate betting using fractional Kelly criterion.
    
    kelly_fraction: fraction of Kelly to bet (0.25 = "quarter Kelly")
    """
    bankroll = starting_bankroll
    results = []
    
    for idx, game in games_df.iterrows():
        # Calculate edge for both sides
        edge_home = game['model_prob_home'] - game['market_prob_home']
        edge_away = (1 - game['model_prob_home']) - (1 - game['market_prob_home'])
        
        bet_placed = None
        bet_size = 0
        
        # Determine which side (if any) to bet
        if edge_home > 0:
            kelly = kelly_criterion(game['model_prob_home'], game['home_odds'])
            bet_size = bankroll * kelly * kelly_fraction
            if bet_size >= 1:  # Minimum $1 bet
                bet_placed = 'home'
                odds = game['home_odds']
                win_condition = game['home_win'] == 1
        
        elif edge_away > 0:
            kelly = kelly_criterion(1 - game['model_prob_home'], game['away_odds'])
            bet_size = bankroll * kelly * kelly_fraction
            if bet_size >= 1:
                bet_placed = 'away'
                odds = game['away_odds']
                win_condition = game['home_win'] == 0
        
        if bet_placed and bet_size > 0:
            # Calculate profit
            if win_condition:
                if odds < 0:
                    profit = bet_size * (100 / abs(odds))
                else:
                    profit = bet_size * (odds / 100)
            else:
                profit = -bet_size
            
            bankroll += profit
            
            results.append({
                'game_id': game.get('game_id', idx),
                'bet_on': bet_placed,
                'bet_size': bet_size,
                'odds': odds,
                'outcome': 'win' if profit > 0 else 'loss',
                'profit': profit,
                'bankroll': bankroll,
                'roi': ((bankroll - starting_bankroll) / starting_bankroll) * 100,
            })
    
    return pd.DataFrame(results), bankroll
```

### Strategy 3: Selective High-Confidence Betting

**Concept:** Only bet on games where:
1. Model probability is high (> 60% or 65%)
2. Edge over market is substantial (> 5-10%)
3. Model confidence is strong (calibration suggests reliability at this probability range)

---

## ROI Analysis

### Key Metrics to Report

#### 1. **Overall ROI**
```python
total_wagered = len(bets_df) * bet_size  # for fixed betting
total_profit = bets_df['profit'].sum()
roi = (total_profit / total_wagered) * 100

print(f"Total Bets: {len(bets_df)}")
print(f"Total Wagered: ${total_wagered:,.2f}")
print(f"Total Profit: ${total_profit:,.2f}")
print(f"ROI: {roi:.2f}%")
```

**Benchmarks:**
- Break-even: ~0% ROI (after vig, slightly negative)
- Decent: 2-5% ROI
- Excellent: 5-10% ROI
- Suspicious/Unsustainable: >10% ROI (may be overfitting or luck)

#### 2. **Win Rate**
```python
win_rate = (bets_df['outcome'] == 'win').mean() * 100
print(f"Win Rate: {win_rate:.2f}%")
```

**Context:** Due to vig, need >52.4% win rate on evenly matched games to break even.

#### 3. **Sharpe Ratio** (Risk-Adjusted Returns)
```python
returns = bets_df['profit'] / bet_size  # return per bet
sharpe = returns.mean() / returns.std() * np.sqrt(len(bets_df))
print(f"Sharpe Ratio: {sharpe:.3f}")
```

Higher Sharpe = better risk-adjusted performance.

#### 4. **Maximum Drawdown**
```python
cumulative = bets_df['cumulative_profit'].values
running_max = np.maximum.accumulate(cumulative)
drawdown = running_max - cumulative
max_drawdown = drawdown.max()

print(f"Max Drawdown: ${max_drawdown:,.2f}")
```

How much you'd lose during worst losing streak.

#### 5. **Profit by Edge Bucket**
```python
bets_df['edge_bucket'] = pd.cut(bets_df['edge'], 
                                  bins=[0, 0.05, 0.10, 0.15, 1.0],
                                  labels=['0-5%', '5-10%', '10-15%', '15%+'])

profit_by_edge = bets_df.groupby('edge_bucket')['profit'].agg(['sum', 'mean', 'count'])
print(profit_by_edge)
```

Does larger edge correlate with higher profit? (It should!)

#### 6. **Performance vs Random Betting**
```python
# Simulate random betting (same number of bets, random selection)
random_roi = simulate_random_betting(games_df, n_bets=len(bets_df))
print(f"Random Betting ROI: {random_roi:.2f}%")
print(f"Our Strategy ROI: {roi:.2f}%")
print(f"Outperformance: {roi - random_roi:.2f}%")
```

### Visualization Suite

```python
import matplotlib.pyplot as plt
import seaborn as sns

def plot_betting_performance(bets_df):
    """Create comprehensive betting performance dashboard."""
    
    fig, axes = plt.subplots(2, 3, figsize=(18, 10))
    
    # 1. Cumulative Profit
    axes[0, 0].plot(bets_df['cumulative_profit'], linewidth=2)
    axes[0, 0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    axes[0, 0].set_title('Cumulative Profit Over Time')
    axes[0, 0].set_xlabel('Bet Number')
    axes[0, 0].set_ylabel('Profit ($)')
    axes[0, 0].grid(alpha=0.3)
    
    # 2. Win/Loss Distribution
    outcome_counts = bets_df['outcome'].value_counts()
    axes[0, 1].bar(outcome_counts.index, outcome_counts.values, color=['green', 'red'])
    axes[0, 1].set_title('Win/Loss Distribution')
    axes[0, 1].set_ylabel('Count')
    
    # 3. Profit by Edge
    sns.boxplot(data=bets_df, x='edge_bucket', y='profit', ax=axes[0, 2])
    axes[0, 2].set_title('Profit Distribution by Edge Size')
    axes[0, 2].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    
    # 4. ROI by Month (if date available)
    if 'game_date' in bets_df.columns:
        bets_df['month'] = pd.to_datetime(bets_df['game_date']).dt.to_period('M')
        monthly_roi = bets_df.groupby('month').apply(
            lambda x: (x['profit'].sum() / (len(x) * 100)) * 100
        )
        axes[1, 0].bar(range(len(monthly_roi)), monthly_roi.values)
        axes[1, 0].set_title('ROI by Month')
        axes[1, 0].set_ylabel('ROI (%)')
        axes[1, 0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    
    # 5. Model vs Market Probability (for bets placed)
    axes[1, 1].scatter(bets_df['market_prob'], bets_df['model_prob'], 
                       c=bets_df['profit'], cmap='RdYlGn', alpha=0.6)
    axes[1, 1].plot([0, 1], [0, 1], 'r--', alpha=0.5)
    axes[1, 1].set_xlabel('Market Probability')
    axes[1, 1].set_ylabel('Model Probability')
    axes[1, 1].set_title('Bets Placed: Model vs Market')
    
    # 6. Profit Distribution
    axes[1, 2].hist(bets_df['profit'], bins=30, edgecolor='black', alpha=0.7)
    axes[1, 2].axvline(x=0, color='r', linestyle='--', linewidth=2)
    axes[1, 2].set_title('Profit Distribution per Bet')
    axes[1, 2].set_xlabel('Profit ($)')
    axes[1, 2].set_ylabel('Frequency')
    
    plt.tight_layout()
    plt.savefig('reports/betting_performance.png', dpi=150)
    plt.show()
```

---

## Implementation Plan

### Phase 1: Data Acquisition (Week 1)
- [ ] Sign up for The Odds API (or alternative)
- [ ] Fetch historical odds for 2023-24 season
- [ ] Create `data/betting_odds_20232024.csv`
- [ ] Validate odds data quality (no missing games, reasonable vig)

### Phase 2: Integration (Week 2)
- [ ] Create `src/nhl_prediction/betting.py` module
- [ ] Implement odds conversion functions
- [ ] Implement vig removal
- [ ] Merge betting odds with model predictions
- [ ] Create comparison visualizations

### Phase 3: Strategy Simulation (Week 3)
- [ ] Implement threshold betting strategy
- [ ] Implement Kelly criterion betting
- [ ] Implement high-confidence selective betting
- [ ] Run simulations on test set
- [ ] Calculate all ROI metrics

### Phase 4: Analysis & Reporting (Week 4)
- [ ] Generate betting performance dashboard
- [ ] Write betting analysis section for report
- [ ] Create presentation slides with key findings
- [ ] Add betting tab to Streamlit dashboard (optional)

### Phase 5: Validation & Testing (Ongoing)
- [ ] Check for look-ahead bias (are we using closing odds correctly?)
- [ ] Verify calculations (manually check a few bets)
- [ ] Sensitivity analysis (different thresholds, Kelly fractions)
- [ ] Compare against published betting strategies/benchmarks

---

## Risk Management

### Important Disclaimers

**1. Past Performance ≠ Future Results**
- 2023-24 results don't guarantee 2024-25 success
- Markets adapt, your edge may disappear
- NHL landscape changes (trades, injuries, rule changes)

**2. Sample Size Matters**
- 1 season (~1300 games) may not be enough to distinguish skill from luck
- Need multiple seasons to validate strategy
- Variance is high in sports betting

**3. Market Efficiency**
- Betting markets are VERY efficient
- If it seems too good to be true, it probably is
- Be skeptical of high ROI claims

**4. Practical Limitations**
- Betting limits (books limit winning players)
- Odds movement (closing line might not be available)
- Transaction costs (deposits, withdrawals)
- Legal restrictions (varies by jurisdiction)

### Overfitting Checks

**Red Flags:**
- ROI > 10% (extremely rare, likely overfit)
- Win rate > 60% consistently (suspicious)
- Strategy works on test set but fails on new data

**Validation:**
- Walk-forward testing (retrain monthly, test on next month)
- Out-of-sample testing on 2024-25 season (true blind test)
- Compare against market benchmarks (closing line value)

### Responsible Gambling Note

**If implementing with real money:**
- Only bet what you can afford to lose
- Set strict bankroll limits
- Track all bets meticulously
- Stop if showing signs of problem gambling
- This is for educational/research purposes

---

## Expected Outcomes

### Realistic Expectations

**Scenario 1: Model Has No Edge**
- ROI ≈ -4% to -5% (paying the vig)
- Win rate ≈ 50-52%
- **Conclusion:** Market is efficient, our features don't add value

**Scenario 2: Model Has Small Edge**
- ROI ≈ 1-3%
- Win rate ≈ 53-54%
- **Conclusion:** Modest edge, potentially profitable with scale and discipline

**Scenario 3: Model Has Real Edge**
- ROI ≈ 4-8%
- Win rate ≈ 55-57%
- **Conclusion:** Genuine predictive advantage (rare!)

**Scenario 4: Overfitting**
- ROI > 10% on test set
- ROI < 0% on new season
- **Conclusion:** Model memorized test set, not generalizable

### What We'll Learn (Regardless of ROI)

1. **Market Calibration:** How well do betting markets predict outcomes?
2. **Feature Value:** Do our engineered features (faceoffs, rest, etc.) provide information beyond market prices?
3. **Modeling Skills:** Experience with real-world evaluation (not just academic metrics)
4. **Domain Knowledge:** Deep understanding of what drives NHL outcomes

---

## Next Steps - Action Items

### Immediate (This Week)
1. **Research betting odds sources**
   - Evaluate The Odds API vs alternatives
   - Check for free historical data repositories
   
2. **Create data schema**
   - Design `betting_odds` table structure
   - Plan data merge strategy with existing predictions

### Short Term (Next 2 Weeks)
3. **Implement core functions**
   - Odds conversion utilities
   - Vig removal
   - Betting simulation engine

4. **Run initial analysis**
   - Model vs market comparison
   - Threshold betting simulation (5%, 10% edge)

### Medium Term (Next Month)
5. **Comprehensive evaluation**
   - Multiple strategies
   - Full ROI reporting
   - Visualizations

6. **Update project report**
   - Add "Betting Analysis" section
   - Include findings and insights

### Long Term (Ongoing)
7. **Live validation** (optional)
   - Paper trade 2024-25 season
   - Compare real-time predictions vs market
   - Track actual ROI

---

## Code Structure

Proposed new file: `src/nhl_prediction/betting.py`

```python
"""
Betting analysis utilities for NHL prediction model.
"""

# Odds conversion
def american_to_probability(odds: float) -> float: ...
def remove_vig_proportional(p_home: float, p_away: float) -> tuple[float, float]: ...

# Strategy simulation
def simulate_threshold_betting(games: pd.DataFrame, threshold: float) -> pd.DataFrame: ...
def simulate_kelly_betting(games: pd.DataFrame, kelly_frac: float) -> pd.DataFrame: ...

# Analysis
def calculate_roi_metrics(bets: pd.DataFrame) -> dict: ...
def compare_model_vs_market(predictions: pd.DataFrame, odds: pd.DataFrame) -> dict: ...

# Visualization
def plot_betting_performance(bets: pd.DataFrame) -> None: ...
def plot_model_vs_market(predictions: pd.DataFrame) -> None: ...
```

---

## Conclusion

This betting integration will transform your project from a prediction model into a **complete decision-support system**. Even if the ROI is neutral/negative, you'll gain invaluable insights into:
- How your model compares to aggregated market wisdom
- Which features provide unique information
- The efficiency of sports betting markets
- Real-world model evaluation beyond accuracy scores

**The goal isn't just to make money (though that would be nice!), but to rigorously evaluate your model against the toughest benchmark: the betting market.**

Let's build this systematically and see what we discover!



