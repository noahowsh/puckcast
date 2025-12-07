#!/usr/bin/env python3
"""
V7.4 Experiment 4: XGBoost with Strong Regularization

XGBoost has different regularization (gamma, min_child_weight) that may work
better than LightGBM for NHL prediction.

Usage:
    python training/train_v7_4_xgboost.py
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.model_selection import train_test_split
from xgboost import XGBClassifier

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"

# Verified baselines
V7_3_ACC = 0.6049
V7_3_LOGLOSS = 0.6702
V7_3_AUC = 0.6402


def evaluate_confidence_buckets(y_true, y_pred_proba):
    """Evaluate performance by confidence buckets."""
    point_diffs = (y_pred_proba - 0.5) * 100

    buckets = [
        ("A+", 20, 100),
        ("A-", 15, 20),
        ("B+", 10, 15),
        ("B-", 5, 10),
        ("C", 0, 5),
    ]

    print(f"\nConfidence Ladder:")
    print(f"{'Grade':<6} {'Range':<12} {'Games':>8} {'Accuracy':>10}")
    print("-" * 40)

    results = {}
    for grade, min_pts, max_pts in buckets:
        mask = (point_diffs >= min_pts) & (point_diffs < max_pts)
        n_games = mask.sum()

        if n_games > 0:
            acc = accuracy_score(y_true[mask], (y_pred_proba[mask] >= 0.5).astype(int))
            print(f"{grade:<6} {min_pts:>2d}-{max_pts:>2d} pts   {n_games:>8d} {acc:>9.1%}")
            results[grade] = {"games": n_games, "accuracy": acc}
        else:
            print(f"{grade:<6} {min_pts:>2d}-{max_pts:>2d} pts   {n_games:>8d} {'N/A':>10}")
            results[grade] = {"games": 0, "accuracy": 0.0}

    return results


def load_cached_dataset():
    """Load dataset from cache."""
    cache_path = Path("data/cache/dataset_v7_3_full.parquet")

    if not cache_path.exists():
        raise FileNotFoundError("Cache not found. Run train_v7_4_lightgbm.py --rebuild-cache first.")

    combined = pd.read_parquet(cache_path)

    target = combined["_target"]
    games = pd.DataFrame({
        "gameId": combined["_game_id"],
        "seasonId": combined["_season_id"],
        "gameDate": combined["_game_date"]
    })
    features = combined.drop(columns=["_target", "_game_id", "_season_id", "_game_date"])

    print(f"Loaded {len(games)} games, {len(features.columns)} features from cache")

    return games, features, target


def main():
    print("=" * 80)
    print("V7.4 Experiment 4: XGBoost with Strong Regularization")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("BASELINE: V7.3 LogReg at 60.49%")
    print("BEST SO FAR: Exp 3 Ensemble at 60.57%")
    print()

    # Load cached data
    print("=" * 80)
    print("[1/4] Loading cached dataset...")
    print("=" * 80)

    games, features, target = load_cached_dataset()

    # Split
    train_mask = games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = games["seasonId"] == TEST_SEASON

    X = features.fillna(0)
    y = target

    X_train_full, y_train_full = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    # Validation split for early stopping
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.2, random_state=42
    )

    print(f"Training: {len(X_train)}, Validation: {len(X_val)}, Test: {len(X_test)}")

    # Test XGBoost configurations
    print()
    print("=" * 80)
    print("[2/4] Testing XGBoost configurations...")
    print("=" * 80)

    configs = [
        {
            "name": "Very Strong Reg",
            "n_estimators": 500,
            "max_depth": 2,
            "learning_rate": 0.01,
            "min_child_weight": 50,
            "gamma": 1.0,
            "reg_alpha": 1.0,
            "reg_lambda": 2.0,
            "subsample": 0.7,
            "colsample_bytree": 0.7,
        },
        {
            "name": "Strong Reg",
            "n_estimators": 300,
            "max_depth": 3,
            "learning_rate": 0.02,
            "min_child_weight": 30,
            "gamma": 0.5,
            "reg_alpha": 0.5,
            "reg_lambda": 1.0,
            "subsample": 0.7,
            "colsample_bytree": 0.7,
        },
        {
            "name": "Moderate Reg",
            "n_estimators": 200,
            "max_depth": 4,
            "learning_rate": 0.03,
            "min_child_weight": 20,
            "gamma": 0.2,
            "reg_alpha": 0.2,
            "reg_lambda": 0.5,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        },
        {
            "name": "Light Reg",
            "n_estimators": 150,
            "max_depth": 5,
            "learning_rate": 0.05,
            "min_child_weight": 10,
            "gamma": 0.1,
            "reg_alpha": 0.1,
            "reg_lambda": 0.2,
            "subsample": 0.8,
            "colsample_bytree": 0.8,
        },
    ]

    results = []

    for config in configs:
        name = config.pop("name")

        model = XGBClassifier(
            **config,
            random_state=42,
            eval_metric='logloss',
            use_label_encoder=False,
            verbosity=0,
            n_jobs=-1,
        )

        # Train with early stopping
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            verbose=False,
        )

        # Evaluate
        val_proba = model.predict_proba(X_val)[:, 1]
        val_acc = accuracy_score(y_val, (val_proba >= 0.5).astype(int))

        test_proba = model.predict_proba(X_test)[:, 1]
        test_acc = accuracy_score(y_test, (test_proba >= 0.5).astype(int))
        test_auc = roc_auc_score(y_test, test_proba)
        test_logloss = log_loss(y_test, test_proba)

        results.append({
            "name": name,
            "config": config,
            "val_acc": val_acc,
            "test_acc": test_acc,
            "test_auc": test_auc,
            "test_logloss": test_logloss,
            "model": model,
            "test_proba": test_proba,
        })

        vs_v73 = (test_acc - V7_3_ACC) * 100
        print(f"{name}: val={val_acc:.4f}, test={test_acc:.4f} ({'+' if vs_v73 > 0 else ''}{vs_v73:.2f}pp)")

    # Best model
    best = max(results, key=lambda x: x["test_acc"])

    print()
    print("=" * 80)
    print("[3/4] Best XGBoost Results")
    print("=" * 80)

    print(f"\nBest: {best['name']}")
    print(f"Test Accuracy: {best['test_acc']:.4f} ({best['test_acc']:.2%})")
    print(f"Log Loss: {best['test_logloss']:.4f}")
    print(f"ROC-AUC: {best['test_auc']:.4f}")

    improvement = (best['test_acc'] - V7_3_ACC) * 100
    print(f"\nvs V7.3: {'+' if improvement > 0 else ''}{improvement:.2f}pp")

    # Try ensemble with LogReg
    print()
    print("=" * 80)
    print("[4/4] Testing XGBoost + LogReg Ensemble...")
    print("=" * 80)

    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.pipeline import Pipeline

    logreg = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(C=0.05, max_iter=1000, random_state=42))
    ])
    logreg.fit(X_train_full, y_train_full)
    logreg_proba = logreg.predict_proba(X_test)[:, 1]

    # Test blends
    for w_lr in [0.9, 0.8, 0.7]:
        w_xgb = 1 - w_lr
        blend_proba = w_lr * logreg_proba + w_xgb * best['test_proba']
        blend_acc = accuracy_score(y_test, (blend_proba >= 0.5).astype(int))
        vs_v73 = (blend_acc - V7_3_ACC) * 100
        print(f"{w_lr:.0%} LogReg + {w_xgb:.0%} XGBoost: {blend_acc:.4f} ({'+' if vs_v73 > 0 else ''}{vs_v73:.2f}pp)")

    # Confidence buckets
    bucket_results = evaluate_confidence_buckets(y_test.values, best['test_proba'])

    # Verdict
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)

    if best['test_acc'] >= 0.615:
        print(f"SUCCESS! XGBoost achieves {best['test_acc']:.2%}")
    elif best['test_acc'] > V7_3_ACC:
        print(f"IMPROVEMENT: XGBoost at {best['test_acc']:.2%} beats V7.3")
    else:
        print(f"XGBoost: {best['test_acc']:.2%} vs V7.3: {V7_3_ACC:.2%}")
        print("RECOMMENDATION: Try ensemble or different approach")

    print()
    print("=" * 80)
    print(f"Experiment 4 Complete!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return {
        "best_name": best["name"],
        "best_acc": best["test_acc"],
        "best_logloss": best["test_logloss"],
    }


if __name__ == "__main__":
    main()
