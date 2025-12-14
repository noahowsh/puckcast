# Model Improvement Analysis

**Date:** December 6, 2025
**Model:** V7.9 Enhanced

## 1. Hyperparameter Tuning

### C (Regularization Strength)

Tested C values from 0.0001 to 10.0 with 4-season training window:

| C Value | Accuracy | AUC | LogLoss |
|---------|----------|-----|---------|
| 0.0001 | 58.75% | 0.6208 | 0.6715 |
| 0.001 | 59.54% | 0.6280 | 0.6629 |
| **0.005** | **59.50%** | **0.6292** | **0.6619** |
| 0.01 | 59.60% | 0.6288 | 0.6622 |
| 0.1 | 59.41% | 0.6269 | 0.6634 |
| 1.0 | 59.21% | 0.6251 | 0.6642 |

**Result:** C=0.005 is already optimal for AUC and LogLoss. C=0.01 gives +0.1pp accuracy but worse calibration.

### Regularization Type

| Config | Accuracy | AUC | LogLoss |
|--------|----------|-----|---------|
| **L2 (Ridge) C=0.005** | **59.50%** | **0.6292** | **0.6619** |
| L2 (Ridge) C=0.01 | 59.60% | 0.6288 | 0.6622 |
| L1 (Lasso) C=0.05 | 59.36% | 0.6261 | 0.6631 |
| ElasticNet (0.3) C=0.01 | 59.41% | 0.6251 | 0.6634 |

**Result:** L2 Ridge regularization is optimal. L1 and ElasticNet perform worse.

## 2. Feature Importance Analysis

### Top 15 Most Important Features

| Rank | Feature | |Coefficient| |
|------|---------|-------------|
| 1 | elo_expectation_home | 0.1392 |
| 2 | elo_diff_pre | 0.1388 |
| 3 | is_b2b_away | 0.1077 |
| 4 | is_b2b_home | 0.0994 |
| 5 | rolling_high_danger_shots_5_diff | 0.0770 |
| 6 | season_xg_diff_avg_diff | 0.0678 |
| 7 | season_shot_margin_diff | 0.0650 |
| 8 | goalie_trend_score_diff | 0.0618 |
| 9 | rolling_corsi_3_diff | 0.0585 |
| 10 | rolling_save_pct_10_diff | 0.0575 |
| 11 | rolling_save_pct_5_diff | 0.0550 |
| 12 | xg_momentum_accel | 0.0535 |
| 13 | rolling_corsi_10_diff | 0.0444 |
| 14 | momentum_xg_diff | 0.0444 |
| 15 | rolling_save_pct_3_diff | 0.0391 |

### Least Important Features

- rolling_goal_diff_10_diff (0.0007)
- momentum_goal_diff_diff (0.0019)
- rolling_corsi_5_diff (0.0032)
- momentum_win_pct_diff (0.0038)
- rolling_xg_diff_10_diff (0.0057)

### Importance by Category

| Category | # Features | Total Importance |
|----------|------------|------------------|
| Rest/Fatigue | 6 | 0.3137 |
| Elo | 3 | 0.2930 |
| Goalie | 7 | 0.2761 |
| xG | 7 | 0.2479 |
| Corsi/Fenwick | 6 | 0.1555 |
| Momentum | 5 | 0.1383 |
| Win % | 5 | 0.1113 |
| Goal Diff | 5 | 0.0837 |

## 3. Feature Selection

Testing top N features by importance:

| # Features | Accuracy | AUC | LogLoss |
|------------|----------|-----|---------|
| 10 | 59.11% | 0.6269 | 0.6626 |
| 15 | 58.83% | 0.6275 | 0.6626 |
| **20** | **59.73%** | 0.6283 | 0.6624 |
| 25 | 59.60% | 0.6283 | 0.6622 |
| **30** | 59.57% | **0.6293** | **0.6618** |
| 42 (all) | 59.50% | 0.6292 | 0.6619 |

**Key Finding:** Using only 20 features gives BETTER accuracy (59.73%) than all 42 features (59.50%)!

### Optimal 20-Feature Set

1. elo_expectation_home
2. elo_diff_pre
3. is_b2b_away
4. is_b2b_home
5. rolling_high_danger_shots_5_diff
6. season_xg_diff_avg_diff
7. season_shot_margin_diff
8. goalie_trend_score_diff
9. rolling_corsi_3_diff
10. rolling_save_pct_10_diff
11. rolling_save_pct_5_diff
12. xg_momentum_accel
13. rolling_corsi_10_diff
14. momentum_xg_diff
15. rolling_save_pct_3_diff
16. rest_diff
17. season_goal_diff_avg_diff
18. goal_momentum_accel
19. goalie_rest_days_diff
20. season_win_pct_diff

## 4. xG Model Retraining

The original xG model was trained on ~200 games from 2021-22 only.

A new script (`training/retrain_xg_model.py`) trains on data from:
- 2018-19 (250 games)
- 2021-22 (250 games)
- 2022-23 (250 games)
- 2023-24 (250 games)

Total: ~1000 games, ~250K shots (vs original ~50K shots)

## Recommendations

### Production Config
```python
# Current optimal settings
C = 0.005
penalty = 'l2'
training_window = 4  # seasons (backup: 3 seasons)
```

### Potential Improvements
1. **Use 20-feature subset** instead of all 42 (+0.23pp accuracy)
2. Consider **C=0.01** if prioritizing accuracy over calibration (+0.1pp)
3. Test expanded xG model once retraining completes
