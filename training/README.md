# Training Scripts

This directory contains all model training, validation, and experimentation scripts.

## Production Models

| Script | Model | Accuracy | Variance | Status |
|--------|-------|----------|----------|--------|
| `train_v7_9_enhanced.py` | V7.9 Enhanced | 60.23% avg | 0.0pp | **RECOMMENDED** |
| `train_v7_7_stable.py` | V7.7 Stable | 59.86% avg | 0.7pp | Good alternative |

## Legacy Models (High Variance - Not Recommended)

| Script | Model | 23-24 | 24-25 | Variance | Issue |
|--------|-------|-------|-------|----------|-------|
| `train_v7_3_situational.py` | V7.3 | 60.49% | 56.86% | 3.6pp | Situational features overfit |
| `train_v7_6_feature_selection.py` | V7.6 | 60.98% | 58.61% | 2.4pp | Team dummies overfit |

## Comparison & Validation Scripts

| Script | Purpose |
|--------|---------|
| `compare_all_models.py` | Comprehensive comparison of V7.3-V7.9 on both test seasons |
| `compare_seasons_v76.py` | V7.6 performance analysis across 23-24 and 24-25 |
| `test_v7_6_true_performance.py` | TRUE forward validation of V7.6 |
| `test_v7_6_comprehensive.py` | Detailed V7.6 analysis |
| `verify_v7_0_baseline.py` | Baseline model verification |

## Data Scripts

| Script | Purpose |
|--------|---------|
| `fetch_2024_25_data.py` | Fetch and cache 2024-25 season data from NHL API |

---

## Failed Experiments (Do Not Use)

The following scripts contain experiments that did NOT improve results:

### V7.4 Series - Alternative Algorithms (FAILED)

| Script | Approach | Result | Why It Failed |
|--------|----------|--------|---------------|
| `train_v7_4_lightgbm.py` | LightGBM | ~58% | Lower accuracy than LogReg |
| `train_v7_4_lightgbm_regularized.py` | Regularized LightGBM | ~58% | Still worse than LogReg |
| `train_v7_4_xgboost.py` | XGBoost | ~58% | Tree models underperform |
| `train_v7_4_ensemble.py` | LR+GB Ensemble | 59.33% | Averaging hurt performance |

### V7.5 Series - Feature Engineering Attempts (MIXED)

| Script | Approach | Result | Notes |
|--------|----------|--------|-------|
| `train_v7_5_features.py` | Additional features | Mixed | Some features helped |
| `train_v7_5_targeted.py` | Targeted features | Mixed | Limited improvement |
| `train_v7_5_optimize.py` | Optimization | Mixed | Explored hyperparameters |
| `train_v7_5_final.py` | Final V7.5 | ~59% | Superseded by V7.6+ |

### V7.6 Series - Feature Selection (HIGH VARIANCE)

| Script | Approach | Result | Why Problematic |
|--------|----------|--------|-----------------|
| `train_v7_6_feature_selection.py` | Top 59 by coefficient | 60.98% on 23-24 | **2.4pp variance** - team dummies overfit |
| `train_v7_6_experiments.py` | Various experiments | Mixed | Exploratory only |
| `train_v7_6_ensemble_optimization.py` | Ensemble tuning | ~59% | Didn't help |

---

## Model Evolution Summary

```
V7.3 (situational) -> 58.68% avg, 3.6pp variance (situational features overfit)
     |
V7.4 (tree models) -> FAILED (worse than LogReg)
     |
V7.5 (features)    -> Mixed results
     |
V7.6 (selection)   -> 59.79% avg, 2.4pp variance (team dummies overfit)
     |
V7.7 (stable)      -> 59.86% avg, 0.7pp variance (removed ALL overfit features)
     |
V7.9 (enhanced)    -> 60.23% avg, 0.0pp variance (+ engineered features) **BEST**
```

## Key Learnings

1. **Team dummies overfit**: 33 of 59 V7.6 features were team-specific - they don't generalize
2. **Situational features overfit**: V7.3's fatigue/travel features had worst variance (3.6pp)
3. **Simpler is better**: LogisticRegression outperforms tree-based models
4. **Consistency matters**: A stable 60% is better than volatile 61%/58%
5. **Feature engineering works**: Momentum acceleration and interaction terms helped (when done right)

## Recommended Usage

For production predictions:
```python
from training.train_v7_9_enhanced import train_v79_model

# Train on most recent 2 seasons for next season predictions
model = train_v79_model(['20232024', '20242025'])
```

---
*Last updated: December 20, 2024*
