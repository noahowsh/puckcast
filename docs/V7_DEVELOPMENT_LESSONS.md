# V7.0 Development Lessons Learned

> **Purpose**: Document what worked, what didn't, and why — so we don't repeat mistakes.
> **Last Updated**: December 7, 2025

---

## 🎯 Final Result: V7.0 Production Model

| Metric | Value |
|--------|-------|
| Accuracy | 60.9% |
| Test Games | 5,002 (4-season holdout) |
| Features | 39 curated + adaptive weights |
| Architecture | Logistic Regression + Isotonic Calibration |

---

## ✅ What Worked

### 1. Situational Features (V7.3 experiments)
**Added +0.25pp accuracy**

Features that improved the model:
- `is_b2b_home`, `is_b2b_away` - Back-to-back detection
- `rest_days_diff` - Rest advantage
- `games_last_3d_diff`, `games_last_6d_diff` - Fatigue accumulation
- `travel_distance_diff` - Travel burden
- `is_divisional` - Divisional game flag

**Why it worked**: These capture real-world factors that affect team performance beyond raw stats.

### 2. Adaptive Elo Home Advantage
**Key innovation in V7.0**

```
Dynamic home ice adjustment based on league-wide home win rate
- Window: 100 games rolling average
- Scale: 700 Elo points
- Adapts to structural shifts (COVID, rule changes)
```

**Why it worked**: Home ice advantage changed significantly post-COVID (~54% → ~52%). Static Elo couldn't adapt; dynamic Elo did.

### 3. League Home Win Rate as Feature
**`league_hw_100` - Rolling 100-game league home win rate**

**Why it worked**: Gives the model awareness of current league conditions rather than assuming historical averages.

### 4. Feature Curation (39 from 209)
**Reduced from 209 features to 39**

Kept only features with:
- Clear predictive signal
- Low multicollinearity
- Stable across seasons

**Why it worked**: Simpler models generalize better. More features = more noise.

---

## ❌ What Failed (Don't Repeat)

### 1. Head-to-Head Features ❌
**V7.4 experiments - REJECTED**

Tested:
- `h2h_home_win_pct` - Historical H2H record
- `h2h_goal_diff` - Average goal differential in matchup
- `h2h_recent_*` - Recent matchup stats

**Results**: 60.00% accuracy (worse than baseline)

**Why it failed**:
1. **Multicollinearity** - H2H stats highly correlated with team strength
2. **Small sample sizes** - Teams play 2-4x per year
3. **Roster turnover** - Historical matchups irrelevant after trades

**Lesson**: Don't add features that measure the same thing as existing features.

### 2. Feature Interactions ❌
**V7.5 experiments - REJECTED**

Tested:
- `elo_x_rest` - Elo × rest days interaction
- `fatigue_x_travel` - Fatigue × travel interaction
- Polynomial features

**Results**: 60.08% accuracy (no improvement)

**Why it failed**:
1. **Overfitting** - Interactions fit training noise, not signal
2. **Logistic regression handles this naturally** - Coefficients already capture relationships
3. **Increased variance** - More parameters = less stable predictions

**Lesson**: Logistic regression doesn't benefit from manual feature interactions.

### 3. Team-Specific Calibration ❌
**V7.6 experiments - REJECTED**

Tested:
- Per-team probability adjustments
- Team-specific coefficients
- "Hard to predict" team flags

**Results**: 60.73% accuracy (marginal, not robust)

**Why it failed**:
1. **Weak signal** - Team unpredictability varies by season
2. **Data leakage risk** - Calibrating on test data
3. **Overfitting** - 32 teams × limited games = sparse data

**Lesson**: Global model works better than team-specific adjustments.

### 4. LightGBM / XGBoost ❌
**V7.4 alternative models - REJECTED**

**Results**: Similar or worse accuracy, much harder to interpret

**Why it failed**:
1. **Overfitting** - Tree models memorize training patterns
2. **Calibration issues** - Probabilities not well-calibrated
3. **Complexity** - Hyperparameter tuning nightmare

**Lesson**: For this problem size (~5000 games), logistic regression > boosted trees.

### 5. Expanded Training Windows ❌
**8-season vs 4-season training**

**Results**: 4-season window performs better

**Why it failed**:
1. **Game evolution** - NHL play style changes over time
2. **Diminishing returns** - Older data adds noise, not signal
3. **Elo drift** - Old ratings less relevant to current teams

**Lesson**: More data isn't always better. Recent data > historical data.

### 6. Goalie-Specific Features ❌
**V7.1 experiments - Limited benefit**

Tested:
- Confirmed starter predictions
- Goalie GSAx history
- Goalie fatigue tracking

**Results**: ~0.1pp improvement, high maintenance cost

**Why it's complicated**:
1. **Unreliable starter info** - Goalies announced 30min before puck drop
2. **Small effect size** - Team strength dominates goalie effect
3. **Data pipeline complexity** - Scraping, verification, errors

**Lesson**: Goalie features have small ROI relative to maintenance burden.

---

## 📊 Feature Importance (V7.0 Production)

Top 10 most important features:
1. `elo_diff_pre` - Pre-game Elo difference
2. `elo_expectation_home` - Expected win probability from Elo
3. `rolling_win_pct_10_diff` - 10-game rolling win % difference
4. `league_hw_100` - League home win rate
5. `season_win_pct_diff` - Season win % difference
6. `rolling_goal_diff_10_diff` - 10-game goal differential
7. `rest_days_diff` - Rest advantage
8. `rolling_xg_diff_5_diff` - 5-game xG differential
9. `is_b2b_away` - Away team on back-to-back
10. `corsi_for_pct_5_diff` - 5-game Corsi differential

**Takeaway**: Elo and rolling stats dominate. Situational features add marginal value.

---

## 🔑 Key Principles

### 1. Simplicity Wins
- 39 features beat 209 features
- Logistic regression beats gradient boosting
- Global model beats team-specific models

### 2. Test on Holdout Data
- Always use true out-of-sample testing
- 4-season rolling holdout prevents leakage
- Don't tune on test data

### 3. Skepticism About New Features
Before adding a feature, ask:
1. Does it measure something the model doesn't already know?
2. Is the signal stable across seasons?
3. Is it worth the data pipeline complexity?

### 4. Early Season Performance
- Model accuracy is ~7pp worse Oct-Nov vs Mar-Apr
- Elo ratings need ~20 games to stabilize
- Don't panic at early season results

---

## 📁 Archived Experiments

Full experiment scripts preserved in:
```
archive/2024-12-07-v7-development-experiments/training/
```

See `MANIFEST.md` in that directory for details on each script.

---

## 🚫 What NOT To Try Again

| Approach | Why It Failed |
|----------|---------------|
| Head-to-head features | Multicollinearity, small samples |
| Feature interactions | Overfitting |
| Team-specific calibration | Weak signal, data leakage |
| Gradient boosting models | Overfitting, calibration issues |
| 8+ season training windows | Old data adds noise |
| Complex goalie tracking | High maintenance, small effect |

---

## ✨ Future Directions (Worth Exploring)

See [vFutures.md](vFutures.md) for roadmap, but promising areas:

1. **In-game model** - Live win probability during games
2. **Playoff model** - Different dynamics than regular season
3. **Injury integration** - If reliable data source found
4. **Betting market calibration** - Compare to Vegas lines

---

**Remember**: The goal is 60%+ accuracy with minimal complexity. Resist the urge to over-engineer.
