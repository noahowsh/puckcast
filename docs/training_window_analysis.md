# Training Window Analysis

**Date:** December 6, 2025
**Model:** V8.0 Enhanced
**Data:** 8 seasons (2017-18 to 2024-25), 9,739 games

## Summary

After extensive testing, we determined that **4 seasons** with **Elo season carryover** is the optimal configuration for the V8.0 model.

**Production Choice:** 4 seasons + optimized Elo (HA=35, carry=0.5) + feature cleanup = **61.4% accuracy**
**Previous (V7.9):** 4 seasons, no Elo carryover = 60.4% accuracy

## Test Results

### Fixed Training Window Comparison

Tested across all possible test seasons with rolling forward validation:

| Window | Avg Accuracy | Avg AUC | Avg LogLoss | Std Dev | # Tests |
|--------|-------------|---------|-------------|---------|---------|
| 2 seasons | 59.20% | 0.6221 | 0.6664 | ±2.15% | 6 |
| **3 seasons** | **60.34%** | 0.6370 | 0.6614 | ±1.12% | 5 |
| **4 seasons** | 60.24% | **0.6427** | **0.6584** | ±1.41% | 4 |
| 5 seasons | 59.50% | 0.6353 | 0.6611 | ±0.48% | 3 |
| 6 seasons | 59.77% | 0.6261 | 0.6631 | ±0.39% | 2 |

### Key Findings

1. **3 seasons = Best accuracy** (60.34%)
2. **4 seasons = Best calibration** (LogLoss: 0.6584, AUC: 0.6427)
3. **2 seasons = Too volatile** (±2.15% variance, worst log loss)
4. **5+ seasons = Diminishing returns** (older data adds noise)

### Performance by Test Season

| Test Season | 2-season | 3-season | 4-season | 5-season |
|-------------|----------|----------|----------|----------|
| 2019-20 | 56.28% | -- | -- | -- |
| 2020-21 | 56.53% | 60.47% | -- | -- |
| 2021-22 | 62.36% | 62.44% | 62.60% | -- |
| 2022-23 | 59.76% | 59.84% | 59.35% | 59.27% |
| 2023-24 | 60.08% | 59.76% | 60.00% | 60.16% |
| 2024-25 | 60.21% | 59.22% | 58.99% | 59.07% |

### COVID Season Impact

- **2019-20** and **2020-21** were COVID-affected seasons
- Excluding them showed minimal impact (±0.08pp)
- Decided to keep them in training data for volume

## Recommendation

### For Production (Current Choice)
```
Training Window: 4 seasons
Example: To predict 2024-25, train on 2020-21, 2021-22, 2022-23, 2023-24
```

**Rationale:**
- Best log loss (0.6584) = better calibrated probabilities
- Best AUC (0.6427) = better discrimination
- Good accuracy (60.24%)

### Backup Option
```
Training Window: 3 seasons
Example: To predict 2024-25, train on 2021-22, 2022-23, 2023-24
```

**Rationale:**
- Highest accuracy (60.34%)
- Lower variance than 2 seasons
- Slightly worse calibration than 4 seasons

## Files Created

| File | Purpose |
|------|---------|
| `data/feature_store.parquet` | Pre-computed features (260 cols, 9,203 games) |
| `data/cache/native_logs_*.parquet` | Raw game data by season |
| `training/build_feature_store.py` | Builds feature store |
| `training/compare_fast.py` | Fast model comparison (~0.5s vs 24+ min) |
| `training/compare_expanded_training.py` | Tests varying training sizes |

## Speed Improvement

Feature store enables ~3000x faster model testing:
- **Before:** ~24 minutes for full comparison
- **After:** ~0.5 seconds

## V8.0 Elo Improvement (December 2025)

### Problem Identified

Elo correlation with outcomes dropped significantly over time:
- 2021-22: 0.253 correlation
- 2024-25: 0.154 correlation (-39% drop)

This was due to:
1. **Increased league parity** - Elo spread compressed 17%
2. **Full season reset** - Each season started from scratch, losing valuable team information

### Solution: Season Carryover

Instead of resetting Elo ratings to 1500 each season, carry over 50% of the deviation from mean:

```python
# New rating = base + carryover * (old_rating - base)
new_rating = 1500 + 0.5 * (prev_rating - 1500)
```

### Results

| Configuration | Avg Accuracy | Log Loss |
|--------------|--------------|----------|
| K=10, HA=30, carry=0 (old) | 59.07% | 0.6582 |
| K=10, HA=30, carry=0.5 | 60.38% | -- |
| K=10, HA=35, carry=0.5 | 60.56% | -- |
| **Full model (HA=35, carry=0.5)** | **61.20%** | **0.6545** |

### Implementation

Updated `src/nhl_prediction/pipeline.py` `_add_elo_features()` function:
- Added `season_carryover` parameter (default 0.5)
- Updated `home_advantage` default to 35.0 (from 30.0)
- Previous season ratings regress 50% toward 1500 at season start

## Feature Degradation Analysis (December 2025)

### Features with Significant Degradation (>20% correlation drop)

| Feature | 2021-22 | 2024-25 | Change |
|---------|---------|---------|--------|
| **goalie_rest_days_diff** | 0.084 | 0.019 | **-77%** |
| elo_expectation_home | 0.249 | 0.154 | -38% (fixed) |
| season_win_pct_diff | 0.189 | 0.125 | -34% |
| goalie_trend_score_diff | 0.093 | 0.062 | -34% |
| season_goal_diff_avg_diff | 0.207 | 0.138 | -33% |

### Features that Improved

| Feature | 2021-22 | 2024-25 | Change |
|---------|---------|---------|--------|
| rolling_corsi_5_diff | 0.104 | 0.138 | **+32%** |
| rolling_fenwick_5_diff | 0.114 | 0.144 | **+26%** |
| rest_diff | 0.047 | 0.072 | **+53%** |

### Key Insight: Possession Metrics Rising

As league parity increases, **underlying performance metrics (Corsi, Fenwick)** are becoming MORE predictive while **outcome-based metrics (wins, goals)** are becoming LESS predictive.

## Goalie Rest Feature Removal

### Analysis

The `goalie_rest_days_diff` feature showed the most severe degradation (-77%). Deep analysis revealed:

1. **Effect collapsed**: In 2021-22, teams with big rest advantage won 69.2% vs 40.8% (28pp gap). In 2024-25, it's 73.1% vs 64.8% (8pp gap).

2. **Redundant with team rest**: Goalie rest was 1.77x more predictive than team rest in 2021-22, but dropped to 0.26x by 2024-25.

3. **Adding it hurts**: When tested, removing the feature improved accuracy:

| Configuration | Accuracy | Log Loss |
|--------------|----------|----------|
| With goalie_rest_days_diff | 61.20% | 0.6545 |
| **Without goalie_rest_days_diff** | **61.40%** | **0.6543** |

### Recommendation

Remove `goalie_rest_days_diff` from the feature set. The `rest_diff` feature (which is improving) captures the relevant signal.

## Final V8.0 Configuration

```python
# Elo settings
home_advantage = 35.0  # Up from 30.0
season_carryover = 0.5  # New (was 0.0 / full reset)

# Features: 19 features (removed goalie_rest_days_diff)
```

### Final Results

| Metric | V7.9 | V8.0 | Improvement |
|--------|------|------|-------------|
| **Accuracy** | 60.37% | **61.40%** | **+1.03pp** |
| **Log Loss** | 0.6582 | **0.6543** | **-0.0039** |
| **Edge vs Baseline** | +6.6pp | **+7.7pp** | **+1.1pp** |

### By Season

| Season | V7.9 | V8.0 | Change |
|--------|------|------|--------|
| 2021-22 | 62.76% | 64.15% | +1.39pp |
| 2022-23 | 58.78% | 60.57% | +1.79pp |
| 2023-24 | 60.16% | 60.98% | +0.82pp |
| 2024-25 | 59.76% | 59.91% | +0.15pp |

## Next Steps

1. ~~Update production model to use 4-season window~~ ✓
2. ~~Implement Elo season carryover~~ ✓ (V8.0)
3. ~~Optimize Elo home advantage to 35~~ ✓ (V8.0)
4. ~~Remove degraded goalie_rest_days_diff feature~~ ✓ (V8.0)
5. Set up automated feature store rebuilds
6. Track prediction accuracy over time
7. Monitor Corsi/Fenwick features (improving - may warrant more weight)
