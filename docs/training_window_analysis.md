# Training Window Analysis

**Date:** December 6, 2025
**Model:** V7.9 Enhanced
**Data:** 8 seasons (2017-18 to 2024-25), 9,739 games

## Summary

After extensive testing, we determined that **3-4 seasons** is the optimal training window for the V7.9 model.

**Production Choice:** 4 seasons
**Backup Option:** 3 seasons (slightly higher accuracy)

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

## Next Steps

1. Update production model to use 4-season window
2. Set up automated feature store rebuilds
3. Track prediction accuracy over time
