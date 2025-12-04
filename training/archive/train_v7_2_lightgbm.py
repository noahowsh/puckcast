#!/usr/bin/env python3
"""
V7.2: LightGBM Model Architecture Upgrade

EXPERIMENT: Testing LightGBM vs Logistic Regression
- Uses same 209 V7.0 features
- V7.0 LogReg baseline: 60.89% accuracy
- Target: 62%+ accuracy
- Expected gain: +0.5 to +0.8pp

IMPORTANT: This does NOT replace V7.0 LogReg - it's a comparison test.
"""

import sys
import pickle
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from lightgbm import LGBMClassifier

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.train import compute_season_weights

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"

# LightGBM Hyperparameters (conservative to prevent overfitting)
LGBM_PARAMS = {
    'n_estimators': 100,          # Number of trees
    'learning_rate': 0.05,        # Slow learning for stability
    'max_depth': 5,               # Shallow trees to prevent overfitting
    'num_leaves': 31,             # Max leaves per tree
    'min_child_samples': 20,      # Min samples in leaf (prevents overfitting)
    'subsample': 0.8,             # Use 80% of data per tree (adds randomness)
    'colsample_bytree': 0.8,      # Use 80% of features per tree
    'objective': 'binary',        # Binary classification
    'metric': 'binary_logloss',   # Optimize log-loss
    'random_state': 42,           # Reproducibility
    'verbose': -1,                # Suppress training output
    'n_jobs': -1                  # Use all CPU cores
}


def evaluate_confidence_buckets(y_true, y_pred_proba, bucket_name="Overall"):
    """Evaluate performance by confidence buckets."""
    # Calculate point differential (home win probability - 0.5) * 100
    point_diffs = (y_pred_proba - 0.5) * 100

    # Define buckets
    buckets = [
        ("A+", 20, 100),
        ("A-", 15, 20),
        ("B+", 10, 15),
        ("B-", 5, 10),
        ("C", 0, 5),
    ]

    print(f"\n{bucket_name} Confidence Ladder:")
    print(f"{'Grade':<6} {'Range':<12} {'Games':>8} {'Accuracy':>10} {'Exp Win%':>10}")
    print("-" * 60)

    bucket_results = []
    for grade, min_pts, max_pts in buckets:
        mask = (point_diffs >= min_pts) & (point_diffs < max_pts)
        n_games = mask.sum()

        if n_games > 0:
            acc = accuracy_score(y_true[mask], (y_pred_proba[mask] >= 0.5).astype(int))
            exp_win_pct = y_pred_proba[mask].mean()
            print(f"{grade:<6} {min_pts:>2d}-{max_pts:>2d} pts   {n_games:>8d} {acc:>9.1%}   {exp_win_pct:>9.1%}")
            bucket_results.append((grade, n_games, acc))
        else:
            print(f"{grade:<6} {min_pts:>2d}-{max_pts:>2d} pts   {n_games:>8d} {'N/A':>10} {'N/A':>10}")
            bucket_results.append((grade, 0, 0.0))

    return bucket_results


def main():
    """Train V7.2 LightGBM model and compare to V7.0 LogReg baseline."""
    print("="*80)
    print("V7.2: LightGBM Architecture Test")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("BASELINE: V7.0 Logistic Regression")
    print("  Accuracy:  60.89%")
    print("  Log Loss:  0.6752")
    print("  A+ Bucket: 69.5% (436 games)")
    print()
    print("EXPERIMENT: V7.2 LightGBM (same 209 features)")
    print("  Expected:  +0.5 to +0.8pp accuracy improvement")
    print("  Target:    62%+ accuracy")
    print()

    # Load dataset
    print("=" * 80)
    print("[1/5] Loading V7.0 dataset...")
    print("=" * 80)
    dataset = build_dataset(TRAIN_SEASONS + [TEST_SEASON])
    print(f"✓ Loaded {len(dataset.games)} games")
    print(f"✓ Features: {len(dataset.features.columns)}")
    print()

    # Split train/test
    print("=" * 80)
    print("[2/5] Preparing train/test split...")
    print("=" * 80)

    train_mask = dataset.games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = dataset.games["seasonId"] == TEST_SEASON

    X = dataset.features.fillna(0)
    y = dataset.target

    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    print(f"Training games: {train_mask.sum()}")
    print(f"Test games: {test_mask.sum()}")
    print(f"Features: {len(X_train.columns)}")
    print(f"Home team wins (train): {y_train.mean():.1%}")
    print(f"Home team wins (test): {y_test.mean():.1%}")

    # Compute sample weights
    train_weights = compute_season_weights(dataset.games[train_mask], TRAIN_SEASONS, decay_factor=1.0)
    print(f"✓ Sample weights computed")
    print()

    # Train LightGBM model
    print("=" * 80)
    print("[3/5] Training LightGBM model...")
    print("=" * 80)
    print(f"Hyperparameters:")
    for key, value in LGBM_PARAMS.items():
        if key not in ['verbose', 'n_jobs']:
            print(f"  {key}: {value}")
    print()

    model = LGBMClassifier(**LGBM_PARAMS)

    # Train with sample weights
    model.fit(
        X_train,
        y_train,
        sample_weight=train_weights
    )

    print("✓ LightGBM model trained")
    print(f"  Trees: {model.n_estimators}")
    print(f"  Features used: {len(X_train.columns)}")
    print()

    # Evaluate on test set
    print("=" * 80)
    print("[4/5] Evaluating on test set...")
    print("=" * 80)

    # Generate predictions
    y_test_pred_proba = model.predict_proba(X_test)[:, 1]
    y_test_pred = (y_test_pred_proba >= 0.5).astype(int)

    # Calculate metrics
    test_acc = accuracy_score(y_test, y_test_pred)
    test_auc = roc_auc_score(y_test, y_test_pred_proba)
    test_logloss = log_loss(y_test, y_test_pred_proba)

    print()
    print("=" * 80)
    print("V7.2 LIGHTGBM RESULTS")
    print("=" * 80)
    print(f"\nTest Set Performance:")
    print(f"  Accuracy:  {test_acc:.4f} ({test_acc:.2%})")
    print(f"  ROC-AUC:   {test_auc:.4f}")
    print(f"  Log Loss:  {test_logloss:.4f}")

    # Compare to V7.0 baseline
    v7_0_acc = 0.6089
    v7_0_logloss = 0.6752
    v7_0_a_plus = 0.695  # 69.5%

    improvement_acc = (test_acc - v7_0_acc) * 100
    improvement_logloss = v7_0_logloss - test_logloss

    print(f"\n📊 vs V7.0 Logistic Regression:")
    print(f"  Accuracy:  {'+' if improvement_acc > 0 else ''}{improvement_acc:.2f} pp ({test_acc:.2%} vs {v7_0_acc:.2%})")
    print(f"  Log Loss:  {'+' if improvement_logloss > 0 else ''}{improvement_logloss:.4f} ({test_logloss:.4f} vs {v7_0_logloss:.4f})")

    # Target achievement
    print(f"\n🎯 Target Achievement:")
    print(f"  Accuracy:  {'✓' if test_acc >= 0.62 else '✗'} {test_acc:.2%} (target: 62%+)")
    print(f"  Log Loss:  {'✓' if test_logloss <= 0.670 else '✗'} {test_logloss:.4f} (target: ≤0.670)")

    # Confidence buckets
    bucket_results = evaluate_confidence_buckets(y_test.values, y_test_pred_proba, "V7.2 LightGBM")

    # Compare A+ bucket
    a_plus_acc = bucket_results[0][2]  # First bucket is A+
    a_plus_games = bucket_results[0][1]

    print(f"\nA+ Bucket Comparison:")
    print(f"  V7.0 LogReg:    {v7_0_a_plus:.1%} (436 games)")
    print(f"  V7.2 LightGBM:  {a_plus_acc:.1%} ({a_plus_games} games)")
    print(f"  Change:         {'+' if a_plus_acc > v7_0_a_plus else ''}{(a_plus_acc - v7_0_a_plus)*100:.1f}pp")

    # Feature importance (top 20)
    print("\n" + "="*80)
    print("[5/5] Feature Importance Analysis")
    print("="*80)

    feature_importance = pd.DataFrame({
        'feature': X_train.columns,
        'importance': model.feature_importances_
    }).sort_values('importance', ascending=False)

    print(f"\nTop 20 Features (by gain):")
    print(f"{'Rank':<6} {'Feature':<45} {'Importance':>12}")
    print("-" * 70)
    for i, row in feature_importance.head(20).iterrows():
        print(f"{feature_importance.index.get_loc(i)+1:<6} {row['feature']:<45} {row['importance']:>12.1f}")

    # Final recommendation
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)

    if test_acc >= 0.62:
        print("✅ SUCCESS: V7.2 LightGBM achieves 62%+ target!")
        print(f"   Accuracy improved by {improvement_acc:.2f}pp over V7.0")
        print("   RECOMMENDATION: Proceed with calibration tuning for log-loss")
        print("   STATUS: Ready for production after calibration")
    elif test_acc >= 0.615:
        print("⚠️  CLOSE: V7.2 LightGBM shows improvement but not quite at target")
        print(f"   Accuracy improved by {improvement_acc:.2f}pp over V7.0")
        print(f"   Gap to target: {(0.62 - test_acc)*100:.2f}pp")
        print("   RECOMMENDATION: Add situational features (Phase 2)")
        print("   Expected: +0.3-0.4pp from Phase 2 should hit 62%")
    elif test_acc > v7_0_acc:
        print("⚠️  MODEST GAIN: V7.2 LightGBM shows small improvement")
        print(f"   Accuracy improved by {improvement_acc:.2f}pp over V7.0")
        print(f"   Gap to target: {(0.62 - test_acc)*100:.2f}pp")
        print("   RECOMMENDATION: Evaluate if worth complexity, may need Phase 2")
    else:
        print("❌ NO IMPROVEMENT: V7.2 LightGBM performs worse than V7.0")
        print(f"   Accuracy changed by {improvement_acc:.2f}pp vs V7.0")
        print("   RECOMMENDATION: Keep V7.0 LogReg, explore alternative approaches")
        print("   Consider: Feature engineering or different hyperparameters")

    print()
    print("="*80)
    print(f"V7.2 Evaluation Complete!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)
    print()
    print("NOTE: V7.0 Logistic Regression remains untouched and production-ready.")
    print("      This was a comparative experiment only.")


if __name__ == "__main__":
    main()
