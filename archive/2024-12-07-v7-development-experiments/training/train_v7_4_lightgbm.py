#!/usr/bin/env python3
"""
V7.4: LightGBM Gradient Boosting Experiment

Tests whether gradient boosting can exceed the LogReg ceiling of 60.49%.

Key hypothesis: Non-linear model can capture feature interactions that
LogReg cannot, potentially improving accuracy.

Usage:
    python training/train_v7_4_lightgbm.py

    # With cached dataset (fast, <1 min after first run)
    python training/train_v7_4_lightgbm.py --use-cache

    # Force rebuild dataset
    python training/train_v7_4_lightgbm.py --rebuild-cache
"""

import sys
import argparse
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.model_selection import cross_val_score
from lightgbm import LGBMClassifier

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.train import compute_season_weights
from nhl_prediction.situational_features import add_situational_features

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"

# Verified V7.3 baseline (for comparison)
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


def load_dataset_with_situational(seasons, use_cache=False, rebuild_cache=False):
    """Load dataset with V7.3 situational features."""
    cache_path = Path("data/cache/dataset_v7_3_full.parquet")
    meta_path = Path("data/cache/dataset_v7_3_full_meta.json")

    # Try to load from cache
    if use_cache and cache_path.exists() and not rebuild_cache:
        print("Loading cached dataset...")
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
        print(f"Cache created: {meta.get('created_at', 'unknown')}")

        return games, features, target

    # Build fresh
    print("Building dataset (this takes ~48 minutes for fresh data)...")
    dataset = build_dataset(seasons)
    print(f"Loaded {len(dataset.games)} games")

    # Add situational features
    print("Adding V7.3 situational features...")
    games_with_situational = add_situational_features(dataset.games)

    situational_cols = [
        'fatigue_index_home', 'fatigue_index_away', 'fatigue_index_diff',
        'third_period_trailing_perf_home', 'third_period_trailing_perf_away', 'third_period_trailing_perf_diff',
        'travel_distance_home', 'travel_distance_away', 'travel_distance_diff',
        'travel_burden_home', 'travel_burden_away',
        'divisional_matchup',
        'post_break_game_home', 'post_break_game_away', 'post_break_game_diff',
    ]

    # Only add columns that don't already exist in base features
    available_situational = [
        col for col in situational_cols
        if col in games_with_situational.columns and col not in dataset.features.columns
    ]

    features = pd.concat([
        dataset.features,
        games_with_situational[available_situational]
    ], axis=1)

    print(f"Total features: {len(features.columns)}")

    # Cache for future use
    if use_cache or rebuild_cache:
        import json
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        combined = features.copy()
        combined["_target"] = dataset.target
        combined["_game_id"] = dataset.games["gameId"].values
        combined["_season_id"] = dataset.games["seasonId"].values
        combined["_game_date"] = dataset.games["gameDate"].values

        combined.to_parquet(cache_path, index=False)
        meta = {
            "seasons": seasons,
            "n_games": len(dataset.games),
            "n_features": len(features.columns),
            "created_at": datetime.now().isoformat()
        }
        meta_path.write_text(json.dumps(meta, indent=2))
        print(f"Cached dataset to {cache_path}")

    return dataset.games, features, dataset.target


def main():
    parser = argparse.ArgumentParser(description="Train V7.4 LightGBM model")
    parser.add_argument("--use-cache", action="store_true", help="Use cached dataset")
    parser.add_argument("--rebuild-cache", action="store_true", help="Rebuild and cache dataset")
    args = parser.parse_args()

    print("=" * 80)
    print("V7.4: LightGBM Gradient Boosting Experiment")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("BASELINE: V7.3 Logistic Regression (Verified)")
    print(f"  Accuracy:  {V7_3_ACC:.2%}")
    print(f"  Log Loss:  {V7_3_LOGLOSS:.4f}")
    print(f"  ROC-AUC:   {V7_3_AUC:.4f}")
    print()
    print("HYPOTHESIS: LightGBM can capture non-linear patterns")
    print("  Expected improvement: +0.5-1.5pp accuracy")
    print()

    # Load data
    print("=" * 80)
    print("[1/5] Loading dataset...")
    print("=" * 80)

    all_seasons = TRAIN_SEASONS + [TEST_SEASON]
    games, features, target = load_dataset_with_situational(
        all_seasons,
        use_cache=args.use_cache,
        rebuild_cache=args.rebuild_cache
    )

    # Split train/test
    print()
    print("=" * 80)
    print("[2/5] Preparing train/test split...")
    print("=" * 80)

    train_mask = games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = games["seasonId"] == TEST_SEASON

    X = features.fillna(0)
    y = target

    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    print(f"Training games: {train_mask.sum()}")
    print(f"Test games: {test_mask.sum()}")
    print(f"Features: {len(X_train.columns)}")

    # Cross-validation to find good hyperparameters
    print()
    print("=" * 80)
    print("[3/5] Cross-validation for hyperparameter selection...")
    print("=" * 80)

    # Test a few configurations
    configs = [
        {"n_estimators": 100, "max_depth": 4, "learning_rate": 0.1, "num_leaves": 15},
        {"n_estimators": 200, "max_depth": 5, "learning_rate": 0.05, "num_leaves": 31},
        {"n_estimators": 300, "max_depth": 6, "learning_rate": 0.03, "num_leaves": 31},
        {"n_estimators": 500, "max_depth": 4, "learning_rate": 0.02, "num_leaves": 15},
    ]

    best_config = None
    best_cv_score = 0

    for i, config in enumerate(configs):
        model = LGBMClassifier(
            **config,
            min_child_samples=20,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=42,
            verbose=-1
        )

        # 3-fold CV on training data
        cv_scores = cross_val_score(model, X_train, y_train, cv=3, scoring='accuracy')
        mean_cv = cv_scores.mean()

        print(f"Config {i+1}: n_est={config['n_estimators']}, depth={config['max_depth']}, "
              f"lr={config['learning_rate']} -> CV: {mean_cv:.4f} (+/- {cv_scores.std():.4f})")

        if mean_cv > best_cv_score:
            best_cv_score = mean_cv
            best_config = config

    print(f"\nBest config: {best_config} (CV: {best_cv_score:.4f})")

    # Train final model
    print()
    print("=" * 80)
    print("[4/5] Training final LightGBM model...")
    print("=" * 80)

    model = LGBMClassifier(
        **best_config,
        min_child_samples=20,
        subsample=0.8,
        colsample_bytree=0.8,
        random_state=42,
        verbose=-1
    )

    model.fit(X_train, y_train)
    print("Model trained")

    # Evaluate
    print()
    print("=" * 80)
    print("[5/5] Evaluating on test set...")
    print("=" * 80)

    y_pred_proba = model.predict_proba(X_test)[:, 1]
    y_pred = (y_pred_proba >= 0.5).astype(int)

    test_acc = accuracy_score(y_test, y_pred)
    test_auc = roc_auc_score(y_test, y_pred_proba)
    test_logloss = log_loss(y_test, y_pred_proba)
    test_brier = np.mean((y_pred_proba - y_test) ** 2)

    print()
    print("=" * 80)
    print("V7.4 LIGHTGBM RESULTS")
    print("=" * 80)
    print(f"\nTest Set Performance:")
    print(f"  Accuracy:    {test_acc:.4f} ({test_acc:.2%})")
    print(f"  ROC-AUC:     {test_auc:.4f}")
    print(f"  Log Loss:    {test_logloss:.4f}")
    print(f"  Brier Score: {test_brier:.4f}")

    # Compare to V7.3
    improvement_acc = (test_acc - V7_3_ACC) * 100
    improvement_logloss = V7_3_LOGLOSS - test_logloss
    improvement_auc = test_auc - V7_3_AUC

    print(f"\n📊 vs V7.3 LogReg Baseline:")
    print(f"  Accuracy:  {'+' if improvement_acc > 0 else ''}{improvement_acc:.2f} pp ({test_acc:.2%} vs {V7_3_ACC:.2%})")
    print(f"  Log Loss:  {'+' if improvement_logloss > 0 else ''}{improvement_logloss:.4f} ({test_logloss:.4f} vs {V7_3_LOGLOSS:.4f})")
    print(f"  ROC-AUC:   {'+' if improvement_auc > 0 else ''}{improvement_auc:.4f} ({test_auc:.4f} vs {V7_3_AUC:.4f})")

    # Confidence buckets
    bucket_results = evaluate_confidence_buckets(y_test.values, y_pred_proba)

    # Feature importance
    print("\n" + "=" * 80)
    print("Top 20 Feature Importance (LightGBM)")
    print("=" * 80)

    importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"\n{'Rank':<6} {'Feature':<45} {'Importance':>12}")
    print("-" * 65)
    for i, (_, row) in enumerate(importance.head(20).iterrows(), 1):
        is_situational = any(kw in row['feature'] for kw in ['fatigue', 'trailing', 'travel', 'divisional', 'break'])
        marker = "⭐" if is_situational else ""
        print(f"{i:<6} {row['feature']:<45} {row['importance']:>12.0f} {marker}")

    # Final verdict
    print("\n" + "=" * 80)
    print("VERDICT")
    print("=" * 80)

    if test_acc >= 0.615:
        print("✅ SUCCESS! LightGBM exceeds target (61.5%+)")
        print(f"   Improvement: +{improvement_acc:.2f}pp over V7.3")
        print("   RECOMMENDATION: Proceed with V7.4 deployment")
    elif test_acc > V7_3_ACC:
        print("⚠️  MARGINAL IMPROVEMENT")
        print(f"   Gained {improvement_acc:.2f}pp over V7.3")
        print("   RECOMMENDATION: Consider if complexity is worth the gain")
    else:
        print("❌ NO IMPROVEMENT OVER V7.3")
        print(f"   LightGBM: {test_acc:.2%} vs LogReg: {V7_3_ACC:.2%}")
        print("   RECOMMENDATION: Keep V7.3 LogReg as production model")

    print()
    print("=" * 80)
    print(f"V7.4 LightGBM Experiment Complete!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)

    return {
        "accuracy": test_acc,
        "roc_auc": test_auc,
        "log_loss": test_logloss,
        "brier": test_brier,
        "buckets": bucket_results,
        "vs_v7_3": improvement_acc
    }


if __name__ == "__main__":
    main()
