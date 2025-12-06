# Training Window Analysis

**Date:** December 6, 2025
**Model:** V8.0 Enhanced
**Data:** 8 seasons (2017-18 to 2024-25), 9,739 games

## Summary

After extensive testing, we determined that **4 seasons** with **Elo season carryover** is the optimal configuration for the V8.0 model.

**Production Choice:** 4 seasons + 50% Elo carryover = **61.2% accuracy**
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
| K=10, HA=30, carry=0.5 (new) | 60.38% | -- |
| **Full model with carry=0.5** | **61.18%** | **0.6546** |

**Improvement: +0.81pp accuracy, -0.0036 log loss**

### Implementation

Updated `src/nhl_prediction/pipeline.py` `_add_elo_features()` function:
- Added `season_carryover` parameter (default 0.5)
- Previous season ratings regress 50% toward 1500 at season start
- Maintains team strength information across seasons

## Next Steps

1. ~~Update production model to use 4-season window~~ ✓
2. ~~Implement Elo season carryover~~ ✓ (V8.0)
3. Set up automated feature store rebuilds
4. Track prediction accuracy over time
5. Investigate other degrading features for potential improvements
