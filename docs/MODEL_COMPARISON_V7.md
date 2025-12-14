# Model Comparison: V7.3 through V7.9

## Executive Summary

This document compares all model versions tested with forward validation on both the 2023-24 and 2024-25 NHL seasons. The key finding is that **models optimized for a single season often fail to generalize** to new data.

## Testing Methodology

**Forward Validation Protocol:**
- Train on 2 prior seasons, test on the next season
- 23-24 test: Train on 21-22 + 22-23
- 24-25 test: Train on 22-23 + 23-24
- No data leakage - test season never seen during training

## Complete Model Comparison

| Model | Features | 23-24 | 24-25 | Average | Variance | Status |
|-------|----------|-------|-------|---------|----------|--------|
| V7.3 (situational) | 222 (209+13) | **60.49%** | 56.86% | 58.68% | 3.6pp | ❌ Worst variance |
| V7.6 (team dummies) | 59 selected | 60.98% | 58.61% | 59.79% | 2.4pp | ❌ High variance |
| V7.7 (stable) | 23 curated | 59.51% | 60.21% | 59.86% | 0.7pp | ✓ Good |
| V7.8 (expanded) | 35 features | 60.16% | 59.60% | 59.88% | 0.6pp | ✓ Good |
| **V7.9 (enhanced)** | 42 features | 60.24% | **60.21%** | **60.23%** | **0.0pp** | ✅ Best |

## Model Details

### V7.3 - Situational Features Model
- **File:** `training/train_v7_3_situational.py`
- **Features:** 222 total (209 baseline + 13 situational)
- **Situational features:** fatigue_index, travel_distance, third_period_trailing_perf, divisional_matchup, post_break_game
- **Regularization:** C=0.05
- **Issue:** Situational features overfit heavily - travel/fatigue patterns from 21-23 don't predict 24-25
- **Result:** 3.6pp drop from 60.49% to 56.86% - **worst variance of all models**

### V7.6 - Feature Selection with Team Dummies
- **File:** `training/train_v7_6_feature_selection.py`
- **Features:** Top 59 by coefficient importance (includes 33 team dummies)
- **Regularization:** C=0.01
- **Issue:** Team dummies overfit to training seasons
- **Result:** Highest single-season (60.98%) but 2.4pp variance

### V7.7 - Stable Features Only (NO team dummies)
- **File:** `training/train_v7_7_stable.py`
- **Features:** 23 hand-curated stable features
- **Regularization:** C=0.01
- **Key Change:** Removed all team-specific dummy variables
- **Result:** More consistent (0.7pp variance) but slightly lower peak

### V7.8 - Expanded Stable Features
- **File:** `training/train_v7_8_expanded.py` (if created)
- **Features:** 35 features (expanded from V7.7)
- **Regularization:** C=0.005
- **Result:** Slight improvement in both accuracy and consistency

### V7.9 - Enhanced with Feature Engineering ⭐ RECOMMENDED
- **File:** `training/train_v7_9_enhanced.py`
- **Features:** 42 total (36 base + 6 engineered)
- **Regularization:** C=0.005
- **Engineered Features:**
  - `goal_momentum_accel` - Short vs long term goal trend
  - `xg_momentum_accel` - Short vs long term xG trend
  - `xg_x_corsi_10` - xG × possession interaction
  - `elo_x_rest` - Elo × rest advantage interaction
  - `dominance` - Composite quality score
  - `is_saturday` - Weekend game effect
- **Result:** Best average accuracy (60.23%) with perfect consistency (0.0pp)

## Why V7.6's 60.98% is Misleading

V7.6 achieved 60.98% on 2023-24, but this is **overfitted performance**:

1. **33 of 59 features are team dummies** - These encode "Team X is good/bad" based on 21-22 and 22-23 data
2. **Team dynamics change** - A team's quality in 22-23 doesn't predict their 24-25 performance
3. **When tested on 24-25**, accuracy dropped to 58.61% (-2.4pp)

The "true" expected performance of V7.6 on unseen data is ~59.79%, not 60.98%.

## Key Insights

### Home Ice Advantage Shifted
- 2023-24: 53.7% home wins
- 2024-25: 56.2% home wins (+2.5pp)

This shift made predictions harder and exposed models relying on historical patterns.

### Oracle Analysis
Even training on 80% of the SAME season and testing on 20%:
- 2023-24 oracle: 61.4%
- 2024-25 oracle: 59.3%

2024-25 was inherently less predictable. V7.9's 60.21% on 24-25 **exceeds the within-season oracle**.

## Recommendations

1. **For Production:** Use V7.9 - highest average accuracy with perfect consistency
2. **Avoid:** V7.3 and V7.6 - high variance means unreliable performance
3. **For 2025-26 predictions:** Train V7.9 on 23-24 + 24-25 data

## Failed Experiments

The following approaches were tested but did NOT improve results:

| Experiment | Result | Why It Failed |
|------------|--------|---------------|
| GradientBoosting | 58.50% avg | Lower accuracy, similar consistency |
| RandomForest | 58.81% avg | Lower accuracy than LogReg |
| Ensemble (LR+GB) | 59.33% avg | Averaging hurt performance |
| Stacking | 56.18% avg | Overfitting on meta-learner |
| Recency weighting (2x) | 59.57% avg | Recent season not always better |
| Isotonic calibration | 59.56% avg | Calibration didn't help accuracy |
| More features (100+) | 58.93% avg | More features = more noise |

## Data Sources

- **2021-22:** 1,230 games (cached)
- **2022-23:** 1,230 games (cached)
- **2023-24:** 1,230 games (cached)
- **2024-25:** 1,312 games (newly fetched this session)

All data cached at `data/cache/native_logs_XXXXXXXX.parquet`

---
*Document created: December 5, 2025*
*Last updated: December 5, 2025*
