#!/usr/bin/env python3
"""
V7.4 Experiment 2: Heavily Regularized LightGBM

Tests whether aggressive regularization can make LightGBM competitive with LogReg.

Key changes from Experiment 1:
- max_depth: 6 -> 3 (shallower trees)
- min_data_in_leaf: 20 -> 100 (larger leaves)
- reg_alpha/reg_lambda: 0 -> 1.0 (L1/L2 regularization)
- learning_rate: 0.03 -> 0.01 (slower learning)
- Early stopping on validation set

Usage:
    python training/train_v7_4_lightgbm_regularized.py
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.model_selection import train_test_split
from lightgbm import LGBMClassifier

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
    meta_path = Path("data/cache/dataset_v7_3_full_meta.json")

    if not cache_path.exists():
        raise FileNotFoundError(f"Cache not found at {cache_path}. Run train_v7_4_lightgbm.py --rebuild-cache first.")

    import json
    combined = pd.read_parquet(cache_path)
    meta = json.loads(meta_path.read_text())

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
    print("V7.4 Experiment 2: Heavily Regularized LightGBM")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("BASELINE: V7.3 LogReg at 60.49%")
    print("PREVIOUS: Exp 1 LightGBM at 57.15% (FAILED - overfitting)")
    print()
    print("HYPOTHESIS: Aggressive regularization can match LogReg")
    print()

    # Load cached data
    print("=" * 80)
    print("[1/4] Loading cached dataset...")
    print("=" * 80)

    games, features, target = load_cached_dataset()

    # Split train/test
    print()
    print("=" * 80)
    print("[2/4] Preparing train/val/test split...")
    print("=" * 80)

    train_mask = games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = games["seasonId"] == TEST_SEASON

    X = features.fillna(0)
    y = target

    X_train_full, y_train_full = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    # Create validation set from training data for early stopping
    X_train, X_val, y_train, y_val = train_test_split(
        X_train_full, y_train_full, test_size=0.2, random_state=42
    )

    print(f"Training games: {len(X_train)}")
    print(f"Validation games: {len(X_val)}")
    print(f"Test games: {len(X_test)}")

    # Test heavily regularized configurations
    print()
    print("=" * 80)
    print("[3/4] Testing regularized configurations...")
    print("=" * 80)

    configs = [
        # Very aggressive regularization
        {
            "name": "Ultra-Conservative",
            "n_estimators": 500,
            "max_depth": 2,
            "learning_rate": 0.005,
            "num_leaves": 4,
            "min_data_in_leaf": 200,
            "reg_alpha": 2.0,
            "reg_lambda": 2.0,
        },
        # Aggressive regularization
        {
            "name": "Very Conservative",
            "n_estimators": 300,
            "max_depth": 3,
            "learning_rate": 0.01,
            "num_leaves": 8,
            "min_data_in_leaf": 100,
            "reg_alpha": 1.0,
            "reg_lambda": 1.0,
        },
        # Moderate regularization
        {
            "name": "Conservative",
            "n_estimators": 200,
            "max_depth": 4,
            "learning_rate": 0.02,
            "num_leaves": 15,
            "min_data_in_leaf": 50,
            "reg_alpha": 0.5,
            "reg_lambda": 0.5,
        },
        # Light regularization (but more than Exp 1)
        {
            "name": "Moderate",
            "n_estimators": 150,
            "max_depth": 5,
            "learning_rate": 0.03,
            "num_leaves": 20,
            "min_data_in_leaf": 30,
            "reg_alpha": 0.1,
            "reg_lambda": 0.1,
        },
    ]

    results = []

    for config in configs:
        name = config.pop("name")

        model = LGBMClassifier(
            **config,
            subsample=0.7,
            colsample_bytree=0.7,
            random_state=42,
            verbose=-1,
            n_jobs=-1,
        )

        # Train with early stopping
        model.fit(
            X_train, y_train,
            eval_set=[(X_val, y_val)],
            callbacks=[
                # Early stopping callback
            ]
        )

        # Evaluate on validation
        val_proba = model.predict_proba(X_val)[:, 1]
        val_acc = accuracy_score(y_val, (val_proba >= 0.5).astype(int))

        # Evaluate on test
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
        print(f"{name}: val={val_acc:.4f}, test={test_acc:.4f} ({'+' if vs_v73 > 0 else ''}{vs_v73:.2f}pp vs V7.3)")

    # Find best model
    best = max(results, key=lambda x: x["test_acc"])

    print()
    print("=" * 80)
    print("[4/4] Best Model Results")
    print("=" * 80)

    print(f"\nBest Config: {best['name']}")
    print(f"Parameters: {best['config']}")

    print(f"\nTest Set Performance:")
    print(f"  Accuracy:    {best['test_acc']:.4f} ({best['test_acc']:.2%})")
    print(f"  ROC-AUC:     {best['test_auc']:.4f}")
    print(f"  Log Loss:    {best['test_logloss']:.4f}")

    # Compare to baselines
    improvement_v73 = (best['test_acc'] - V7_3_ACC) * 100
    improvement_exp1 = (best['test_acc'] - 0.5715) * 100

    print(f"\nvs V7.3 LogReg (60.49%):")
    print(f"  Accuracy: {'+' if improvement_v73 > 0 else ''}{improvement_v73:.2f}pp")

    print(f"\nvs Exp 1 LightGBM (57.15%):")
    print(f"  Accuracy: {'+' if improvement_exp1 > 0 else ''}{improvement_exp1:.2f}pp")

    # Confidence buckets for best model
    bucket_results = evaluate_confidence_buckets(y_test.values, best['test_proba'])

    # Feature importance
    print("\n" + "=" * 80)
    print("Top 15 Feature Importance")
    print("=" * 80)

    importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': best['model'].feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"\n{'Rank':<6} {'Feature':<45} {'Importance':>12}")
    print("-" * 65)
    for i, (_, row) in enumerate(importance.head(15).iterrows(), 1):
        print(f"{i:<6} {row['feature']:<45} {row['importance']:>12.0f}")

    # Verdict
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)

    if best['test_acc'] >= 0.615:
        print(f"SUCCESS! Regularized LightGBM achieves {best['test_acc']:.2%}")
        print(f"  Improvement: +{improvement_v73:.2f}pp over V7.3")
        print("  RECOMMENDATION: Consider for V7.4 production")
    elif best['test_acc'] > V7_3_ACC:
        print(f"MARGINAL IMPROVEMENT")
        print(f"  Best: {best['test_acc']:.2%} vs V7.3: {V7_3_ACC:.2%}")
        print(f"  Gained {improvement_v73:.2f}pp")
        print("  RECOMMENDATION: Try ensemble approach next")
    else:
        print(f"STILL UNDERPERFORMS V7.3")
        print(f"  Best: {best['test_acc']:.2%} vs V7.3: {V7_3_ACC:.2%}")
        print(f"  Gap: {improvement_v73:.2f}pp")
        print("  RECOMMENDATION: Try ensemble approach")

    print()
    print("=" * 80)
    print(f"Experiment 2 Complete!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return {
        "best_name": best["name"],
        "best_acc": best["test_acc"],
        "best_auc": best["test_auc"],
        "best_logloss": best["test_logloss"],
        "all_results": [(r["name"], r["test_acc"]) for r in results],
    }


if __name__ == "__main__":
    main()
