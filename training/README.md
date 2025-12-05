# Training Scripts

This directory contains all model training, validation, and experimentation scripts.

## Production Models

| Script | Model | Accuracy | Status |
|--------|-------|----------|--------|
| `train_v7_9_enhanced.py` | V7.9 Enhanced | 60.23% avg | **RECOMMENDED** |
| `train_v7_7_stable.py` | V7.7 Stable | 59.86% avg | Good alternative |
| `train_v7_3_situational.py` | V7.3 Baseline | 58.97% avg | Baseline only |

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
V7.3 (baseline)   -> 58.97% avg, 2.7pp variance (211 features - too many)
     |
V7.4 (tree models) -> FAILED (worse than LogReg)
     |
V7.5 (features)    -> Mixed results
     |
V7.6 (selection)   -> 59.79% avg, 2.4pp variance (team dummies caused overfitting)
     |
V7.7 (stable)      -> 59.86% avg, 0.7pp variance (removed team dummies)
     |
V7.9 (enhanced)    -> 60.23% avg, 0.0pp variance (added engineered features) **BEST**
```

## Key Learnings

1. **Team dummies overfit**: 33 of 59 V7.6 features were team-specific - they don't generalize
2. **Simpler is better**: LogisticRegression outperforms tree-based models
3. **Consistency matters**: A stable 60% is better than volatile 61%/58%
4. **Feature engineering works**: Momentum acceleration and interaction terms helped

## Recommended Usage

For production predictions:
```python
from training.train_v7_9_enhanced import train_v79_model

# Train on most recent 2 seasons for next season predictions
model = train_v79_model(['20232024', '20242025'])
```

---
*Last updated: December 5, 2025*
