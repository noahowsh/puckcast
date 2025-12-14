# Puckcast Model Sauce

> **The Complete Technical Breakdown of V7.0**
>
> Everything we do to predict NHL games, explained in plain English.

---

## The Core Algorithm

We use **Logistic Regression** with a StandardScaler preprocessing step. Why Logistic Regression instead of fancy deep learning or complex ensembles? Because:

1. It works well for binary outcomes (home win vs away win)
2. It's interpretable - we can see exactly what features matter
3. It doesn't overfit as easily on 5,000 games of training data
4. We tested ensembles (LR + XGBoost blends) and they didn't improve holdout accuracy

The model outputs a probability between 0 and 1 for each game, representing the chance the home team wins.

---

## Validated Performance

| Metric | Value | Note |
|--------|-------|------|
| **Test Accuracy** | 60.86% | 3,044 correct / 5,002 games |
| **Games Tested** | 5,002 | 4 full seasons (2021-22 through 2024-25) |
| **Baseline** | 53.92% | Just picking home team every game |
| **Edge Over Baseline** | +6.94 pts | Model advantage vs naive strategy |
| **Log Loss** | 0.6554 | Probability calibration metric |
| **Brier Score** | 0.2317 | Lower is better (perfect = 0) |

---

## The 39 Features

V7.0 uses exactly 39 curated features. Each feature is a "difference" value comparing home team to away team. Here's what they are in plain English:

### League-Wide Context (1 feature)

| Feature | What It Measures |
|---------|------------------|
| `league_hw_100` | Rolling 100-game league-wide home win rate. Captures structural shifts in home advantage across the NHL. |

### Team Strength - Elo Ratings (2 features)

| Feature | What It Measures |
|---------|------------------|
| `elo_diff_pre` | Difference in pre-game Elo ratings. Higher = stronger team on paper. |
| `elo_expectation_home` | Expected win probability based on Elo differential. |

Elo ratings carry over between seasons with regression to mean (stronger teams start closer to average after summer).

### Recent Form - Win Percentage (3 features)

| Feature | What It Measures |
|---------|------------------|
| `rolling_win_pct_10_diff` | Win % difference over last 10 games |
| `rolling_win_pct_5_diff` | Win % difference over last 5 games |
| `rolling_win_pct_3_diff` | Win % difference over last 3 games |

Why all three windows? Different patterns emerge at different time scales. A team on a 3-game hot streak might be different from sustained 10-game dominance.

### Goal Differential (3 features)

| Feature | What It Measures |
|---------|------------------|
| `rolling_goal_diff_10_diff` | Goal differential per game over last 10 |
| `rolling_goal_diff_5_diff` | Goal differential per game over last 5 |
| `rolling_goal_diff_3_diff` | Goal differential per game over last 3 |

Goal differential captures "how much" a team is winning, not just whether they win.

### Expected Goals (xG) (3 features)

| Feature | What It Measures |
|---------|------------------|
| `rolling_xg_diff_10_diff` | xG differential over last 10 games |
| `rolling_xg_diff_5_diff` | xG differential over last 5 games |
| `rolling_xg_diff_3_diff` | xG differential over last 3 games |

Expected goals measure shot quality, not just quantity. A team generating high-danger chances is doing something right even if the puck isn't going in.

### Possession Metrics (5 features)

| Feature | What It Measures |
|---------|------------------|
| `rolling_corsi_10_diff` | Corsi differential (all shot attempts) over 10 games |
| `rolling_corsi_5_diff` | Corsi differential over 5 games |
| `rolling_corsi_3_diff` | Corsi differential over 3 games |
| `rolling_fenwick_10_diff` | Fenwick differential (unblocked shots) over 10 games |
| `rolling_fenwick_5_diff` | Fenwick differential over 5 games |

Teams that control shot attempts tend to win more over time, even if individual games are noisy.

### Season Aggregates (4 features)

| Feature | What It Measures |
|---------|------------------|
| `season_win_pct_diff` | Full season win percentage difference |
| `season_goal_diff_avg_diff` | Season-long goal differential per game |
| `season_xg_diff_avg_diff` | Season-long xG differential |
| `season_shot_margin_diff` | Season-long shot attempt margin |

These capture the "true talent" level averaged over more games than rolling windows.

### Rest and Schedule (5 features)

| Feature | What It Measures |
|---------|------------------|
| `rest_diff` | Days of rest difference (home - away) |
| `is_b2b_home` | Home team playing back-to-back (1 or 0) |
| `is_b2b_away` | Away team playing back-to-back (1 or 0) |
| `games_last_6d_home` | Home team's game density over last 6 days |
| `games_last_3d_home` | Home team's game density over last 3 days |

Fatigue is real. A team on no rest vs a rested opponent has a measurable disadvantage.

### Goaltending (6 features)

| Feature | What It Measures |
|---------|------------------|
| `rolling_save_pct_10_diff` | Save percentage differential over 10 games |
| `rolling_save_pct_5_diff` | Save percentage differential over 5 games |
| `rolling_save_pct_3_diff` | Save percentage differential over 3 games |
| `rolling_gsax_5_diff` | Goals Saved Above Expected over 5 games |
| `rolling_gsax_10_diff` | Goals Saved Above Expected over 10 games |
| `goalie_trend_score_diff` | Combined goalie form indicator |

Goaltending is the most volatile position in hockey. We use multiple windows to smooth noise.

### Momentum Indicators (3 features)

| Feature | What It Measures |
|---------|------------------|
| `momentum_win_pct_diff` | Recent win rate momentum |
| `momentum_goal_diff_diff` | Recent goal scoring momentum |
| `momentum_xg_diff` | Recent expected goals momentum |

Momentum captures whether a team is improving or declining recently.

### Shot Quality (2 features)

| Feature | What It Measures |
|---------|------------------|
| `rolling_high_danger_shots_5_diff` | High-danger shot attempts over 5 games |
| `rolling_high_danger_shots_10_diff` | High-danger shot attempts over 10 games |

Shots from the slot and crease are worth more than shots from the point.

### Volume & Possession Extras (2 features)

| Feature | What It Measures |
|---------|------------------|
| `shotsFor_roll_10_diff` | Shot volume trend over 10 games |
| `rolling_faceoff_5_diff` | Faceoff win rate over 5 games |

Faceoffs translate to possession time.

---

## Adaptive Sample Weights

**Problem:** NHL home advantage isn't static. The 2024-25 season had 56.2% home win rate vs historical 53.5%. If we train on data with unusual home advantage, the model might overlearn that pattern.

**Solution:** We calculate sample weights that down-weight games from anomalous seasons:

```
deviation = abs(season_home_win_rate - 0.535)
weight = 1.0 / (1.0 + deviation * 5)
```

A season with 56% home win rate (0.03 deviation) gets weight ~0.87 instead of 1.0.

This prevents the model from thinking "home teams always win more" just because of one weird season.

---

## Dynamic Threshold

**Standard approach:** Predict home win if probability > 50%

**Our approach:** Adjust the threshold based on current league conditions.

```
threshold = 0.5 + (0.535 - rolling_league_hw_50) * 0.5
```

**Examples:**
- League home win rate = 53.5% (normal): threshold = 0.500
- League home win rate = 52.0% (low): threshold = 0.5075 (pick home less often)
- League home win rate = 56.0% (high): threshold = 0.4875 (pick home more often)

The threshold is clamped between 0.45 and 0.55 to prevent extreme swings.

---

## Confidence Grading System

We convert raw edge (probability minus 0.50) into letter grades:

| Grade | Edge Range | Historical Accuracy | Games |
|-------|------------|---------------------|-------|
| **A+** | 25+ pts | 79.28% | 333 |
| **A** | 20-25 pts | 72.03% | 404 |
| **B+** | 15-20 pts | 67.25% | 687 |
| **B** | 10-15 pts | 61.95% | 975 |
| **C+** | 5-10 pts | 57.76% | 1,231 |
| **C** | 0-5 pts | 51.90% | 1,372 |

**Key insight:** A+ picks (25+ point edge) hit at nearly 80%. These are the high-conviction calls.

C-grade picks (under 5 points) are essentially coin flips at 52% - no meaningful edge.

---

## Training Methodology

### 4-Season Rolling Window

We always train on exactly 4 seasons of data (approximately 5,000 games). Why 4?

- **Too few seasons (1-2):** Not enough data, high variance
- **Too many seasons (5+):** Old data becomes stale, patterns evolve
- **4 seasons:** Sweet spot for recency vs sample size

### Leave-One-Season-Out Cross-Validation

To get unbiased accuracy estimates:

1. Train on seasons A, B, C
2. Test on season D
3. Rotate: Train on A, B, D → Test on C
4. Repeat for all combinations

This prevents data leakage (never test on data used for training) and gives robust holdout accuracy.

### Regularization Tuning

We tune the regularization strength (C parameter) on the final training season:

```python
candidate_cs = [0.005, 0.01, 0.02, 0.03, 0.05, 0.1, 0.3, 0.5, 1.0]
# Select C with lowest log loss on validation season
```

Lower C = more regularization = simpler model. Usually lands around C=0.02-0.05.

### Probability Calibration

Raw logistic regression probabilities can be overconfident. We apply **isotonic regression** calibration:

1. Fit calibrator on validation season probabilities vs actual outcomes
2. Apply calibrator to production predictions

This ensures that when we say "65% home win probability," historically those games really do result in ~65% home wins.

---

## Data Pipeline

### Sources

1. **NHL API** - Official game results, schedules, team IDs
2. **MoneyPuck** - Advanced stats (xG, Corsi, Fenwick, high-danger shots, GSAx)
3. **Computed** - Elo ratings, rolling windows, momentum indicators

### Feature Engineering

Every feature is computed as a **difference** (home minus away) to normalize for matchup context:

```
elo_diff_pre = home_elo - away_elo
rolling_win_pct_10_diff = home_rolling_win_pct_10 - away_rolling_win_pct_10
```

Rolling windows use `.shift(1)` to prevent data leakage (only use data available before game time).

---

## What Doesn't Work (Tested and Rejected)

| Approach | Result | Why |
|----------|--------|-----|
| XGBoost/LightGBM ensemble | No improvement | Overfits on 5k games |
| Deep neural networks | Worse accuracy | Not enough data |
| Individual goalie features | No improvement | Too much noise |
| Travel distance | No improvement | Already captured by rest |
| Weather/arena factors | No improvement | Indoor sport, small effect |
| Betting line features | N/A | Circular logic |
| Team-specific dummies | Overfits | 2.4pp variance between seasons |
| More than 39 features | Diminishing returns | Noise outweighs signal |

---

## Limitations

1. **Early season noise:** Oct-Nov accuracy is ~56-58% vs 64% by March/April. Elo ratings need ~20 games to stabilize.

2. **Injury information:** We don't incorporate lineup changes beyond starting goalie. A star player out can swing games.

3. **Motivation factors:** We don't model playoff clinching scenarios, tank incentives, or rivalry motivation.

4. **60.9% is near the ceiling:** With public data and no lineup info, this is roughly the best achievable without proprietary edges.

---

## Summary

V7.0 predicts NHL games at **60.86% accuracy** using:

- **39 curated features** covering team strength, recent form, possession, goaltending, and rest
- **Logistic Regression** with adaptive sample weights
- **Dynamic thresholds** that adjust to league-wide home advantage shifts
- **6-tier confidence grading** from C (coin flip) to A+ (79% accuracy)
- **4-season training window** with leave-one-season-out validation

The model is intentionally simple and robust. Complex approaches overfit. Boring works.

---

*Generated for V7.0 Launch - December 2025*
