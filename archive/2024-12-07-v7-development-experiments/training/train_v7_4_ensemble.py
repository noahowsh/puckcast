#!/usr/bin/env python3
"""
V7.4 Experiment 3: Ensemble (LogReg + LightGBM)

Blends LogReg predictions with regularized LightGBM to combine their strengths:
- LogReg: Well-calibrated, good at avoiding overfitting
- LightGBM: Can capture non-linear patterns

Usage:
    python training/train_v7_4_ensemble.py
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
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
        raise FileNotFoundError(f"Cache not found. Run train_v7_4_lightgbm.py --rebuild-cache first.")

    import json
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
    print("V7.4 Experiment 3: Ensemble (LogReg + LightGBM)")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("BASELINE: V7.3 LogReg at 60.49%")
    print("EXP 2: Regularized LightGBM at 59.92%")
    print()
    print("HYPOTHESIS: Ensemble can outperform both individual models")
    print()

    # Load cached data
    print("=" * 80)
    print("[1/5] Loading cached dataset...")
    print("=" * 80)

    games, features, target = load_cached_dataset()

    # Split train/test
    print()
    print("=" * 80)
    print("[2/5] Preparing data splits...")
    print("=" * 80)

    train_mask = games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = games["seasonId"] == TEST_SEASON

    X = features.fillna(0)
    y = target

    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    print(f"Training games: {len(X_train)}")
    print(f"Test games: {len(X_test)}")

    # Train LogReg (matching V7.3 config)
    print()
    print("=" * 80)
    print("[3/5] Training LogReg (C=0.05)...")
    print("=" * 80)

    logreg = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(C=0.05, max_iter=1000, random_state=42))
    ])
    logreg.fit(X_train, y_train)

    logreg_proba = logreg.predict_proba(X_test)[:, 1]
    logreg_acc = accuracy_score(y_test, (logreg_proba >= 0.5).astype(int))
    print(f"LogReg test accuracy: {logreg_acc:.4f}")

    # Train LightGBM (best regularized config from Exp 2)
    print()
    print("=" * 80)
    print("[4/5] Training Regularized LightGBM...")
    print("=" * 80)

    lgbm = LGBMClassifier(
        n_estimators=200,
        max_depth=4,
        learning_rate=0.02,
        num_leaves=15,
        min_data_in_leaf=50,
        reg_alpha=0.5,
        reg_lambda=0.5,
        subsample=0.7,
        colsample_bytree=0.7,
        random_state=42,
        verbose=-1,
        n_jobs=-1,
    )
    lgbm.fit(X_train, y_train)

    lgbm_proba = lgbm.predict_proba(X_test)[:, 1]
    lgbm_acc = accuracy_score(y_test, (lgbm_proba >= 0.5).astype(int))
    print(f"LightGBM test accuracy: {lgbm_acc:.4f}")

    # Test ensemble weights
    print()
    print("=" * 80)
    print("[5/5] Testing ensemble weights...")
    print("=" * 80)

    weights_to_test = [
        (1.0, 0.0, "LogReg only"),
        (0.9, 0.1, "90% LogReg + 10% LGBM"),
        (0.8, 0.2, "80% LogReg + 20% LGBM"),
        (0.7, 0.3, "70% LogReg + 30% LGBM"),
        (0.6, 0.4, "60% LogReg + 40% LGBM"),
        (0.5, 0.5, "50% LogReg + 50% LGBM"),
        (0.4, 0.6, "40% LogReg + 60% LGBM"),
        (0.3, 0.7, "30% LogReg + 70% LGBM"),
        (0.0, 1.0, "LGBM only"),
    ]

    results = []
    for w_lr, w_lgbm, name in weights_to_test:
        ensemble_proba = w_lr * logreg_proba + w_lgbm * lgbm_proba
        ensemble_acc = accuracy_score(y_test, (ensemble_proba >= 0.5).astype(int))
        ensemble_auc = roc_auc_score(y_test, ensemble_proba)
        ensemble_logloss = log_loss(y_test, ensemble_proba)

        results.append({
            "name": name,
            "w_lr": w_lr,
            "w_lgbm": w_lgbm,
            "acc": ensemble_acc,
            "auc": ensemble_auc,
            "logloss": ensemble_logloss,
            "proba": ensemble_proba,
        })

        vs_v73 = (ensemble_acc - V7_3_ACC) * 100
        print(f"{name}: {ensemble_acc:.4f} ({'+' if vs_v73 > 0 else ''}{vs_v73:.2f}pp vs V7.3)")

    # Find best
    best = max(results, key=lambda x: x["acc"])

    print()
    print("=" * 80)
    print("BEST ENSEMBLE RESULTS")
    print("=" * 80)

    print(f"\nBest Weights: {best['name']}")
    print(f"  LogReg: {best['w_lr']:.0%}, LightGBM: {best['w_lgbm']:.0%}")

    print(f"\nTest Set Performance:")
    print(f"  Accuracy:    {best['acc']:.4f} ({best['acc']:.2%})")
    print(f"  ROC-AUC:     {best['auc']:.4f}")
    print(f"  Log Loss:    {best['logloss']:.4f}")

    # Compare to baselines
    improvement = (best['acc'] - V7_3_ACC) * 100

    print(f"\nvs V7.3 LogReg ({V7_3_ACC:.2%}):")
    print(f"  Accuracy: {'+' if improvement > 0 else ''}{improvement:.2f}pp")

    # Confidence buckets
    bucket_results = evaluate_confidence_buckets(y_test.values, best['proba'])

    # Verdict
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)

    if best['acc'] >= 0.615:
        print(f"SUCCESS! Ensemble achieves {best['acc']:.2%}")
        print(f"  Improvement: +{improvement:.2f}pp over V7.3")
        print("  RECOMMENDATION: Deploy as V7.4")
    elif best['acc'] > V7_3_ACC:
        print(f"IMPROVEMENT FOUND!")
        print(f"  Best: {best['acc']:.2%} vs V7.3: {V7_3_ACC:.2%}")
        print(f"  Gained {improvement:.2f}pp")
        print("  RECOMMENDATION: Consider for production if stable across runs")
    else:
        print(f"NO IMPROVEMENT OVER V7.3")
        print(f"  Best: {best['acc']:.2%} vs V7.3: {V7_3_ACC:.2%}")
        print("  RECOMMENDATION: LogReg alone is optimal")

    # Also show correlation between models
    correlation = np.corrcoef(logreg_proba, lgbm_proba)[0, 1]
    print(f"\nModel Correlation: {correlation:.4f}")
    print("  (Lower = more diverse predictions = better ensemble potential)")

    # Show where they disagree
    disagree_mask = ((logreg_proba >= 0.5) != (lgbm_proba >= 0.5))
    n_disagree = disagree_mask.sum()
    disagree_acc = accuracy_score(y_test[disagree_mask], (best['proba'][disagree_mask] >= 0.5).astype(int))
    print(f"\nDisagreement Analysis:")
    print(f"  Games where models disagree: {n_disagree} ({n_disagree/len(y_test):.1%})")
    print(f"  Ensemble accuracy on disagreements: {disagree_acc:.1%}")

    print()
    print("=" * 80)
    print(f"Experiment 3 Complete!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return {
        "best_name": best["name"],
        "best_acc": best["acc"],
        "logreg_acc": logreg_acc,
        "lgbm_acc": lgbm_acc,
        "correlation": correlation,
    }


if __name__ == "__main__":
    main()
