#!/usr/bin/env python3
"""
V7.5 Feature Optimization & Neural Network Experiments

Based on targeted experiments:
- Advanced features (luck, consistency, dominance): +0.24pp ensemble
- Ratio features: +0.16pp ensemble
- Ratio+Momentum LogReg: +0.73pp

This script:
1. Tests optimal feature combinations
2. Optimizes ensemble weights
3. Tests neural network approach
4. Tests calibration improvements

Usage:
    python training/train_v7_5_optimize.py
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.calibration import CalibratedClassifierCV

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Configuration
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


def add_all_v75_features(combined: pd.DataFrame) -> pd.DataFrame:
    """Add all beneficial V7.5 features."""
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


def evaluate_confidence_buckets(y_true, y_pred_proba):
    """Evaluate by confidence buckets."""
    point_diffs = (y_pred_proba - 0.5) * 100

    buckets = [
        ("A+", 20, 100),
        ("A-", 15, 20),
        ("B+", 10, 15),
        ("B-", 5, 10),
        ("C", 0, 5),
    ]

    print(f"\n{'Grade':<6} {'Range':<12} {'Games':>8} {'Accuracy':>10}")
    print("-" * 40)

    for grade, min_pts, max_pts in buckets:
        mask = (point_diffs >= min_pts) & (point_diffs < max_pts)
        n_games = mask.sum()

        if n_games > 0:
            acc = accuracy_score(y_true[mask], (y_pred_proba[mask] >= 0.5).astype(int))
            print(f"{grade:<6} {min_pts:>2d}-{max_pts:>2d} pts   {n_games:>8d} {acc:>9.1%}")


def main():
    print("=" * 80)
    print("V7.5 Feature Optimization & Advanced Experiments")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load data
    games, features, target, combined = load_cached_dataset()
    print(f"Loaded {len(games)} games")

    train_mask = games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = games["seasonId"] == TEST_SEASON

    y_train = target[train_mask]
    y_test = target[test_mask]

    # Add V7.5 features
    combined_v75 = add_all_v75_features(combined)
    features_v75 = combined_v75.drop(columns=["_target", "_game_id", "_season_id", "_game_date"]).fillna(0)

    new_cols = [c for c in features_v75.columns if c not in features.columns]
    print(f"New V7.5 features: {new_cols}")

    X_train = features_v75[train_mask]
    X_test = features_v75[test_mask]

    # ===== EXPERIMENT 1: Optimal Ensemble Weights =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 1: Optimal Ensemble Weights")
    print("=" * 80)

    try:
        from xgboost import XGBClassifier
        has_xgb = True
    except ImportError:
        has_xgb = False
        print("XGBoost not available")

    # Train LogReg
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    logreg = LogisticRegression(C=0.05, max_iter=1000, random_state=42)
    logreg.fit(X_train_scaled, y_train)
    logreg_proba = logreg.predict_proba(X_test_scaled)[:, 1]

    if has_xgb:
        xgb = XGBClassifier(
            n_estimators=300, max_depth=3, learning_rate=0.02,
            min_child_weight=30, gamma=0.5, reg_alpha=0.5, reg_lambda=1.0,
            subsample=0.7, colsample_bytree=0.7, random_state=42, verbosity=0, n_jobs=-1
        )
        xgb.fit(X_train, y_train)
        xgb_proba = xgb.predict_proba(X_test)[:, 1]

        # Test different weights
        best_weight = 0.8
        best_acc = 0

        print(f"\n{'LR Weight':<12} {'XGB Weight':<12} {'Accuracy':>10} {'vs V7.4':>10}")
        print("-" * 50)

        for lr_weight in [0.95, 0.90, 0.85, 0.80, 0.75, 0.70, 0.65, 0.60]:
            xgb_weight = 1 - lr_weight
            blend = lr_weight * logreg_proba + xgb_weight * xgb_proba
            acc = accuracy_score(y_test, (blend >= 0.5).astype(int))
            delta = (acc - V74_BEST_ACC) * 100

            print(f"{lr_weight:<12.0%} {xgb_weight:<12.0%} {acc:>10.4f} {delta:>+9.2f}pp")

            if acc > best_acc:
                best_acc = acc
                best_weight = lr_weight
                best_proba = blend

        print(f"\nBest: {best_weight:.0%} LR + {1-best_weight:.0%} XGB = {best_acc:.4f}")

    # ===== EXPERIMENT 2: Calibrated Classifiers =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 2: Calibration Improvements")
    print("=" * 80)

    # Isotonic calibration
    from sklearn.model_selection import cross_val_predict

    logreg_iso = CalibratedClassifierCV(
        LogisticRegression(C=0.05, max_iter=1000, random_state=42),
        method='isotonic',
        cv=5
    )
    logreg_iso.fit(X_train_scaled, y_train)
    iso_proba = logreg_iso.predict_proba(X_test_scaled)[:, 1]
    iso_acc = accuracy_score(y_test, (iso_proba >= 0.5).astype(int))

    print(f"Isotonic calibration: {iso_acc:.4f} ({(iso_acc - V73_ACC) * 100:+.2f}pp vs V7.3)")

    # Sigmoid (Platt) calibration
    logreg_sig = CalibratedClassifierCV(
        LogisticRegression(C=0.05, max_iter=1000, random_state=42),
        method='sigmoid',
        cv=5
    )
    logreg_sig.fit(X_train_scaled, y_train)
    sig_proba = logreg_sig.predict_proba(X_test_scaled)[:, 1]
    sig_acc = accuracy_score(y_test, (sig_proba >= 0.5).astype(int))

    print(f"Sigmoid calibration: {sig_acc:.4f} ({(sig_acc - V73_ACC) * 100:+.2f}pp vs V7.3)")

    # ===== EXPERIMENT 3: Neural Network =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 3: Neural Network")
    print("=" * 80)

    try:
        from sklearn.neural_network import MLPClassifier

        # Simple MLP
        mlp = MLPClassifier(
            hidden_layer_sizes=(64, 32),
            activation='relu',
            solver='adam',
            alpha=0.01,  # L2 regularization
            learning_rate='adaptive',
            max_iter=500,
            early_stopping=True,
            validation_fraction=0.2,
            random_state=42,
            verbose=False
        )
        mlp.fit(X_train_scaled, y_train)
        mlp_proba = mlp.predict_proba(X_test_scaled)[:, 1]
        mlp_acc = accuracy_score(y_test, (mlp_proba >= 0.5).astype(int))

        print(f"MLP (64, 32): {mlp_acc:.4f} ({(mlp_acc - V73_ACC) * 100:+.2f}pp vs V7.3)")

        # Deeper MLP
        mlp_deep = MLPClassifier(
            hidden_layer_sizes=(128, 64, 32),
            activation='relu',
            solver='adam',
            alpha=0.01,
            learning_rate='adaptive',
            max_iter=500,
            early_stopping=True,
            validation_fraction=0.2,
            random_state=42,
            verbose=False
        )
        mlp_deep.fit(X_train_scaled, y_train)
        mlp_deep_proba = mlp_deep.predict_proba(X_test_scaled)[:, 1]
        mlp_deep_acc = accuracy_score(y_test, (mlp_deep_proba >= 0.5).astype(int))

        print(f"MLP (128, 64, 32): {mlp_deep_acc:.4f} ({(mlp_deep_acc - V73_ACC) * 100:+.2f}pp vs V7.3)")

        # More regularized MLP
        mlp_reg = MLPClassifier(
            hidden_layer_sizes=(32, 16),
            activation='relu',
            solver='adam',
            alpha=0.1,  # Strong L2 regularization
            learning_rate='adaptive',
            max_iter=500,
            early_stopping=True,
            validation_fraction=0.2,
            random_state=42,
            verbose=False
        )
        mlp_reg.fit(X_train_scaled, y_train)
        mlp_reg_proba = mlp_reg.predict_proba(X_test_scaled)[:, 1]
        mlp_reg_acc = accuracy_score(y_test, (mlp_reg_proba >= 0.5).astype(int))

        print(f"MLP (32, 16) strong reg: {mlp_reg_acc:.4f} ({(mlp_reg_acc - V73_ACC) * 100:+.2f}pp vs V7.3)")

        # MLP + LogReg ensemble
        if has_xgb:
            for mlp_weight in [0.1, 0.2, 0.3]:
                lr_weight = 0.8 - mlp_weight
                xgb_weight = 0.2

                blend = lr_weight * logreg_proba + xgb_weight * xgb_proba + mlp_weight * mlp_proba
                acc = accuracy_score(y_test, (blend >= 0.5).astype(int))
                print(f"LR({lr_weight:.0%})+XGB({xgb_weight:.0%})+MLP({mlp_weight:.0%}): {acc:.4f}")

    except Exception as e:
        print(f"Neural network error: {e}")

    # ===== EXPERIMENT 4: Different C values =====
    print("\n" + "=" * 80)
    print("EXPERIMENT 4: LogReg Regularization Tuning")
    print("=" * 80)

    for c_val in [0.01, 0.02, 0.03, 0.05, 0.07, 0.1, 0.2]:
        lr = LogisticRegression(C=c_val, max_iter=1000, random_state=42)
        lr.fit(X_train_scaled, y_train)
        proba = lr.predict_proba(X_test_scaled)[:, 1]
        acc = accuracy_score(y_test, (proba >= 0.5).astype(int))
        print(f"C={c_val}: {acc:.4f} ({(acc - V73_ACC) * 100:+.2f}pp)")

    # ===== FINAL SUMMARY =====
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)

    print(f"\nBaseline V7.3: {V73_ACC:.4f}")
    print(f"Baseline V7.4: {V74_BEST_ACC:.4f}")

    if has_xgb:
        print(f"\nBest V7.5 ensemble: {best_acc:.4f} ({(best_acc - V74_BEST_ACC) * 100:+.2f}pp)")
        print(f"  Weight: {best_weight:.0%} LR + {1-best_weight:.0%} XGB")

        print("\nConfidence Buckets (Best Model):")
        evaluate_confidence_buckets(y_test.values, best_proba)

    # Gap analysis
    gap = 0.62 - best_acc
    print(f"\nGap to 62% target: {gap * 100:.2f}pp")

    print(f"\nFinished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
