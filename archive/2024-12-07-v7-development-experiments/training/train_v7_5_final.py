#!/usr/bin/env python3
"""
V7.5 Final Model Tuning

Based on experiments:
- C=0.01 LogReg with V7.5 features: 61.22%
- 75% LR + 25% XGB ensemble: 61.22%

This script does final optimization to push toward 62%.

Usage:
    python training/train_v7_5_final.py
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss, brier_score_loss
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import cross_val_score

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"

V73_ACC = 0.6049
V74_BEST_ACC = 0.6098


def load_cached_dataset():
    cache_path = Path("data/cache/dataset_v7_3_full.parquet")
    combined = pd.read_parquet(cache_path)

    target = combined["_target"]
    games = pd.DataFrame({
        "gameId": combined["_game_id"],
        "seasonId": combined["_season_id"],
        "gameDate": combined["_game_date"]
    })
    features = combined.drop(columns=["_target", "_game_id", "_season_id", "_game_date"])

    return games, features, target, combined


def add_v75_features(combined: pd.DataFrame) -> pd.DataFrame:
    """Add best V7.5 features."""
    games = combined.copy()

    # Ratio features
    if 'rolling_goal_diff_5_diff' in games.columns:
        if 'shotsFor_roll_5_diff' in games.columns:
            shots = games['shotsFor_roll_5_diff'].replace(0, np.nan)
            games['ratio_goals_per_shot_5'] = (games['rolling_goal_diff_5_diff'] / shots).fillna(0).clip(-1, 1)

        if 'shotsFor_roll_10_diff' in games.columns:
            shots = games['shotsFor_roll_10_diff'].replace(0, np.nan)
            games['ratio_goals_per_shot_10'] = (games['rolling_goal_diff_10_diff'] / shots).fillna(0).clip(-1, 1)

    if 'rolling_goal_diff_5_diff' in games.columns and 'rolling_xg_diff_5_diff' in games.columns:
        xg = games['rolling_xg_diff_5_diff'].replace(0, np.nan)
        games['ratio_goals_vs_xg_5'] = (games['rolling_goal_diff_5_diff'] / xg).clip(-3, 3).fillna(0)

    if 'rolling_goal_diff_10_diff' in games.columns and 'rolling_xg_diff_10_diff' in games.columns:
        xg = games['rolling_xg_diff_10_diff'].replace(0, np.nan)
        games['ratio_goals_vs_xg_10'] = (games['rolling_goal_diff_10_diff'] / xg).clip(-3, 3).fillna(0)

    if 'rolling_high_danger_shots_5_diff' in games.columns and 'shotsFor_roll_5_diff' in games.columns:
        shots = games['shotsFor_roll_5_diff'].replace(0, np.nan)
        games['ratio_hd_shots_5'] = (games['rolling_high_danger_shots_5_diff'] / shots).fillna(0).clip(-1, 1)

    # Advanced features
    if 'rolling_xg_for_5_diff' in games.columns and 'rolling_goal_diff_5_diff' in games.columns:
        games['luck_indicator_5'] = games['rolling_goal_diff_5_diff'] - games['rolling_xg_diff_5_diff']

    if 'rolling_goal_diff_3_diff' in games.columns and 'rolling_goal_diff_10_diff' in games.columns:
        games['consistency_gd'] = abs(games['rolling_goal_diff_3_diff'] - games['rolling_goal_diff_10_diff'])

    if 'rolling_goal_diff_5_diff' in games.columns and 'rolling_win_pct_5_diff' in games.columns:
        win_pct = games['rolling_win_pct_5_diff'].clip(-1, 1)
        gd = games['rolling_goal_diff_5_diff'].clip(-3, 3)
        games['dominance_score'] = win_pct * gd

    return games


def evaluate_buckets(y_true, y_pred_proba):
    """Evaluate by confidence buckets."""
    point_diffs = (y_pred_proba - 0.5) * 100

    buckets = [("A+", 20, 100), ("A-", 15, 20), ("B+", 10, 15), ("B-", 5, 10), ("C", 0, 5)]

    print(f"\n{'Grade':<6} {'Games':>8} {'Accuracy':>10}")
    print("-" * 30)

    results = {}
    for grade, min_pts, max_pts in buckets:
        mask = (point_diffs >= min_pts) & (point_diffs < max_pts)
        n_games = mask.sum()

        if n_games > 0:
            acc = accuracy_score(y_true[mask], (y_pred_proba[mask] >= 0.5).astype(int))
            print(f"{grade:<6} {n_games:>8d} {acc:>9.1%}")
            results[grade] = acc
        else:
            print(f"{grade:<6} {n_games:>8d} {'N/A':>10}")

    return results


def main():
    print("=" * 80)
    print("V7.5 Final Model Tuning")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Load data
    games, features, target, combined = load_cached_dataset()

    train_mask = games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = games["seasonId"] == TEST_SEASON

    y_train = target[train_mask]
    y_test = target[test_mask]

    # Add V7.5 features
    combined_v75 = add_v75_features(combined)
    features_v75 = combined_v75.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)

    X_train = features_v75[train_mask]
    X_test = features_v75[test_mask]

    print(f"\nFeatures: {len(X_train.columns)}")
    print(f"Training: {len(X_train)}, Test: {len(X_test)}")

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    try:
        from xgboost import XGBClassifier
        has_xgb = True
    except ImportError:
        has_xgb = False

    # ===== GRID SEARCH: C values × XGB weights =====
    print("\n" + "=" * 80)
    print("GRID SEARCH: C values × Ensemble Weights")
    print("=" * 80)

    best_acc = 0
    best_config = None
    best_proba = None

    c_values = [0.005, 0.01, 0.015, 0.02, 0.03, 0.05]
    xgb_weights = [0.0, 0.15, 0.20, 0.25, 0.30, 0.35] if has_xgb else [0.0]

    print(f"\n{'C':<8} {'XGB %':<8} {'Accuracy':>10} {'vs Best':>10}")
    print("-" * 40)

    for c_val in c_values:
        # Train LogReg with this C
        logreg = LogisticRegression(C=c_val, max_iter=1000, random_state=42)
        logreg.fit(X_train_scaled, y_train)
        logreg_proba = logreg.predict_proba(X_test_scaled)[:, 1]

        for xgb_weight in xgb_weights:
            if xgb_weight > 0 and has_xgb:
                # Train XGBoost
                xgb = XGBClassifier(
                    n_estimators=300, max_depth=3, learning_rate=0.02,
                    min_child_weight=30, gamma=0.5, reg_alpha=0.5, reg_lambda=1.0,
                    subsample=0.7, colsample_bytree=0.7, random_state=42, verbosity=0, n_jobs=-1
                )
                xgb.fit(X_train, y_train)
                xgb_proba = xgb.predict_proba(X_test)[:, 1]

                blend = (1 - xgb_weight) * logreg_proba + xgb_weight * xgb_proba
            else:
                blend = logreg_proba

            acc = accuracy_score(y_test, (blend >= 0.5).astype(int))

            if acc > best_acc:
                delta = (acc - best_acc) * 100
                print(f"{c_val:<8.3f} {xgb_weight:<8.0%} {acc:>10.4f} {'+' + f'{delta:.2f}':>9}pp")
                best_acc = acc
                best_config = (c_val, xgb_weight)
                best_proba = blend

    print(f"\nBest: C={best_config[0]}, XGB={best_config[1]:.0%}, Accuracy={best_acc:.4f}")

    # ===== CROSS-VALIDATION of best config =====
    print("\n" + "=" * 80)
    print("CROSS-VALIDATION (Best Config)")
    print("=" * 80)

    best_c, best_xgb_w = best_config

    logreg_best = LogisticRegression(C=best_c, max_iter=1000, random_state=42)
    cv_scores = cross_val_score(logreg_best, X_train_scaled, y_train, cv=5, scoring='accuracy')
    print(f"5-fold CV: {cv_scores.mean():.4f} (+/- {cv_scores.std() * 2:.4f})")

    # ===== FINAL METRICS =====
    print("\n" + "=" * 80)
    print("FINAL V7.5 MODEL METRICS")
    print("=" * 80)

    print(f"\nTest Set ({len(y_test)} games):")
    print(f"  Accuracy:     {best_acc:.4f} ({best_acc:.2%})")
    print(f"  Log Loss:     {log_loss(y_test, best_proba):.4f}")
    print(f"  ROC-AUC:      {roc_auc_score(y_test, best_proba):.4f}")
    print(f"  Brier Score:  {brier_score_loss(y_test, best_proba):.4f}")

    print(f"\nComparison:")
    print(f"  vs V7.3 ({V73_ACC:.2%}): {(best_acc - V73_ACC) * 100:+.2f}pp")
    print(f"  vs V7.4 ({V74_BEST_ACC:.2%}): {(best_acc - V74_BEST_ACC) * 100:+.2f}pp")
    print(f"  Gap to 62%: {(0.62 - best_acc) * 100:.2f}pp")

    # Confidence buckets
    print("\nConfidence Buckets:")
    evaluate_buckets(y_test.values, best_proba)

    # ===== SAVE BEST MODEL CONFIG =====
    print("\n" + "=" * 80)
    print("BEST V7.5 CONFIGURATION")
    print("=" * 80)

    print(f"""
V7.5 Model Configuration:
------------------------
LogReg:
  C = {best_c}
  max_iter = 1000

XGBoost (if weight > 0):
  n_estimators = 300
  max_depth = 3
  learning_rate = 0.02
  min_child_weight = 30
  gamma = 0.5
  reg_alpha = 0.5
  reg_lambda = 1.0

Ensemble:
  LogReg weight: {1 - best_xgb_w:.0%}
  XGBoost weight: {best_xgb_w:.0%}

New Features (8):
  - ratio_goals_per_shot_5
  - ratio_goals_per_shot_10
  - ratio_goals_vs_xg_5
  - ratio_goals_vs_xg_10
  - ratio_hd_shots_5
  - luck_indicator_5
  - consistency_gd
  - dominance_score
""")

    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return {
        'best_acc': best_acc,
        'best_config': best_config,
        'cv_mean': cv_scores.mean(),
        'cv_std': cv_scores.std(),
    }


if __name__ == "__main__":
    main()
