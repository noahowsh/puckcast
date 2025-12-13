# Archived Experimental Features (2025-12-13)

These files were V7.0 experimental feature modules that were tested and **rejected** because they did not improve model accuracy over the V7.0 baseline (60.9%).

## Archived Files

| File | Purpose | Test Result |
|------|---------|-------------|
| `enhanced_shot_features.py` | Enhanced shot quality metrics | Did not improve accuracy |
| `momentum_features.py` | Momentum-weighted team features | Did not improve accuracy |
| `pdo_features.py` | PDO regression features | Did not improve accuracy |
| `feature_pruning.py` | Automated feature selection | Did not improve accuracy |
| `v75_features.py` | V7.5 experimental feature bundle | 60.08% (worse than baseline) |
| `confirmed_starter_features.py` | Goalie confirmation features | Did not improve accuracy |

## Context

Per the V7.0 development documentation, these features were tested in controlled experiments:
- **H2H features**: 60.00% (worse than 60.9% baseline)
- **Feature interactions**: 60.08% (worse)
- **Team calibration**: 60.73% (worse)

The production model uses the simpler, more robust feature set documented in `MODEL_SAUCE.md`.

## Why Archived (Not Deleted)

These files are preserved for:
1. Historical reference on what was tried
2. Potential future re-evaluation with more data
3. Documentation of the development process
