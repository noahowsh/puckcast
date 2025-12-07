# V7.0 Development Experiments Archive

**Archived**: 2024-12-07
**Purpose**: Clean up training directory by moving experimental scripts

## What's Here

These are the experimental training and verification scripts created during V7.0 development. They document various approaches tested before arriving at the final V7.0 production model.

### Training Experiments (`training/`)

| File | Description | Result |
|------|-------------|--------|
| `train_v7_3_situational.py` | Situational features (fatigue, rest, travel) | ✅ Features included in V7.0 |
| `train_v7_4_*.py` | LightGBM, XGBoost, ensemble experiments | ❌ Rejected - overfitting |
| `train_v7_5_*.py` | Feature interaction experiments | ❌ Rejected - no improvement |
| `train_v7_6_*.py` | Team calibration, ensemble optimization | ❌ Rejected - weak signal |
| `train_v7_7_stable.py` | Stability improvements | Merged into V7.0 |
| `train_v7_9_enhanced.py` | Enhanced features experiment | ❌ Rejected |

### Comparison Scripts

| File | Description |
|------|-------------|
| `compare_all_models.py` | Compare multiple model architectures |
| `compare_expanded_training.py` | Test expanded training windows |
| `compare_fast.py` | Quick comparison utilities |
| `compare_seasons_v76.py` | V7.6 season-by-season analysis |
| `compare_v81_v82.py` | V8.1 vs V8.2 comparison |

### Verification Scripts

| File | Description |
|------|-------------|
| `verify_v7_0_baseline.py` | Baseline verification |
| `verify_v80_metrics.py` | V8.0 metrics validation |
| `verify_v81_baseline.py` | V8.1 baseline check |
| `v83_adaptive_model.py` | Adaptive model experiment |
| `v84_final_test.py` | V8.4 final testing |
| `v85_dynamic_elo_test.py` | Dynamic Elo experiments |
| `v9_model_test.py` | V9 architecture testing |

### Investigation Scripts

| File | Description |
|------|-------------|
| `aggressive_fixes.py` | Aggressive model fixes |
| `radical_fixes.py` | Radical approach testing |
| `explore_improvements.py` | General improvement exploration |
| `feature_analysis.py` | Feature importance analysis |
| `improved_model.py` | Model improvement experiments |
| `investigate_2526.py` | 2025-26 season investigation |
| `threshold_optimization.py` | Decision threshold tuning |
| `elo_*.py` | Elo rating experiments |
| `test_v7_6_*.py` | V7.6 comprehensive tests |

## V7.0 Production Model

The final V7.0 production model uses:
- **39 curated features** with adaptive weights
- **60.9% accuracy** on 4-season holdout (5,002 games)
- **Logistic regression** with isotonic calibration
- **Key innovations**: Adaptive Elo home advantage, league home win rate feature

## Why Archived

These scripts are kept for:
1. Historical documentation of development process
2. Reference for future experiments
3. Reproducibility of test results

They were removed from active `training/` directory to:
1. Reduce clutter
2. Make clear what's production vs experimental
3. Simplify repository structure
