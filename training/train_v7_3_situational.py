#!/usr/bin/env python3
"""
V7.3: Situational Context Features

V7.0 (209 features) + 5 new situational features = 214 total features

NEW FEATURES:
1. Fatigue Index - Weighted games in last 7 days
2. Third Period Trailing Performance - Win% in close games (clutch proxy)
3. Travel Distance - Miles traveled since last game
4. Divisional Matchup - Same division flag
5. Post-Break Performance - First game after 4+ days rest

Expected improvement: +0.40 to +0.70pp (conservative: +0.20 to +0.35pp)
Target: Close gap from 60.89% → 62%+
"""

import sys
import pickle
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities
from nhl_prediction.train import compute_season_weights
from nhl_prediction.situational_features import add_situational_features

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
OPTIMAL_C = 0.05  # From V7.0 optimization
OPTIMAL_DECAY = 1.0


def evaluate_confidence_buckets(y_true, y_pred_proba, bucket_name="Overall"):
    """Evaluate performance by confidence buckets."""
    point_diffs = (y_pred_proba - 0.5) * 100

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
    """Train V7.3 model with situational context features."""
    print("="*80)
    print("V7.3: Training with Situational Context Features")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("BASELINE: V7.0 Logistic Regression")
    print("  Features:  209")
    print("  Accuracy:  60.89%")
    print("  Log Loss:  0.6752")
    print("  A+ Bucket: 69.5% (436 games)")
    print()
    print("V7.3 ADDITIONS: 5 Situational Context Features")
    print("  1. Fatigue Index (games in last 7 days)")
    print("  2. Third Period Trailing Performance")
    print("  3. Travel Distance")
    print("  4. Divisional Matchup")
    print("  5. Post-Break Performance")
    print()
    print("  Expected: +0.20 to +0.70pp accuracy improvement")
    print("  Target:   62%+ accuracy")
    print()

    # Load V7.0 dataset
    print("=" * 80)
    print("[1/5] Loading V7.0 base dataset...")
    print("=" * 80)
    dataset = build_dataset(TRAIN_SEASONS + [TEST_SEASON])
    print(f"✓ Loaded {len(dataset.games)} games")
    print(f"✓ V7.0 features: {len(dataset.features.columns)}")
    print()

    # Add V7.3 situational features
    print("=" * 80)
    print("[2/5] Adding V7.3 situational features...")
    print("=" * 80)

    # Add features to games dataframe
    games_with_situational = add_situational_features(dataset.games)

    # Extract new feature columns
    situational_feature_cols = [
        'fatigue_index_home', 'fatigue_index_away', 'fatigue_index_diff',
        'third_period_trailing_perf_home', 'third_period_trailing_perf_away', 'third_period_trailing_perf_diff',
        'travel_distance_home', 'travel_distance_away', 'travel_distance_diff',
        'divisional_matchup',
        'post_break_game_home', 'post_break_game_away', 'post_break_game_diff',
    ]

    # Check which features were actually added
    available_situational = [col for col in situational_feature_cols if col in games_with_situational.columns]
    print(f"✓ Added {len(available_situational)} situational features")
    print(f"  Features: {', '.join(available_situational[:5])}...")

    # Combine V7.0 features + V7.3 situational features
    features_v7_3 = pd.concat([
        dataset.features,
        games_with_situational[available_situational]
    ], axis=1)

    print(f"✓ Total V7.3 features: {len(features_v7_3.columns)} (V7.0: 209 + V7.3: {len(available_situational)})")
    print()

    # Split train/test
    print("=" * 80)
    print("[3/5] Preparing train/test split...")
    print("=" * 80)

    train_mask = dataset.games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = dataset.games["seasonId"] == TEST_SEASON

    X = features_v7_3.fillna(0)
    y = dataset.target

    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    print(f"Training games: {train_mask.sum()}")
    print(f"Test games: {test_mask.sum()}")
    print(f"Features: {len(X_train.columns)}")
    print(f"Home team wins (train): {y_train.mean():.1%}")
    print(f"Home team wins (test): {y_test.mean():.1%}")

    # Compute sample weights
    train_weights = compute_season_weights(dataset.games[train_mask], TRAIN_SEASONS, decay_factor=OPTIMAL_DECAY)
    print(f"✓ Sample weights computed")
    print()

    # Train V7.3 model
    print("=" * 80)
    print(f"[4/5] Training V7.3 model (C={OPTIMAL_C})...")
    print("=" * 80)

    model = create_baseline_model(C=OPTIMAL_C)
    train_mask_fit = pd.Series(True, index=X_train.index)
    model = fit_model(model, X_train, y_train, train_mask_fit, sample_weight=train_weights)

    print("✓ Model trained")
    print(f"   Features used: {len(X_train.columns)}")
    print()

    # Evaluate
    print("=" * 80)
    print("[5/5] Evaluating V7.3 performance...")
    print("=" * 80)

    test_mask_pred = pd.Series(True, index=X_test.index)
    y_test_pred_proba = predict_probabilities(model, X_test, test_mask_pred)
    y_test_pred = (y_test_pred_proba >= 0.5).astype(int)

    test_acc = accuracy_score(y_test, y_test_pred)
    test_auc = roc_auc_score(y_test, y_test_pred_proba)
    test_logloss = log_loss(y_test, y_test_pred_proba)

    print()
    print("=" * 80)
    print("V7.3 RESULTS")
    print("=" * 80)
    print(f"\nTest Set Performance:")
    print(f"  Accuracy:  {test_acc:.4f} ({test_acc:.2%})")
    print(f"  ROC-AUC:   {test_auc:.4f}")
    print(f"  Log Loss:  {test_logloss:.4f}")

    # Compare to V7.0
    v7_0_acc = 0.6089
    v7_0_logloss = 0.6752
    v7_0_a_plus_acc = 0.695
    v7_0_a_plus_games = 436

    improvement_acc = (test_acc - v7_0_acc) * 100
    improvement_logloss = v7_0_logloss - test_logloss

    print(f"\n📊 vs V7.0 Baseline:")
    print(f"  Accuracy:  {'+' if improvement_acc > 0 else ''}{improvement_acc:.2f} pp ({test_acc:.2%} vs {v7_0_acc:.2%})")
    print(f"  Log Loss:  {'+' if improvement_logloss > 0 else ''}{improvement_logloss:.4f} ({test_logloss:.4f} vs {v7_0_logloss:.4f})")

    # Target achievement
    print(f"\n🎯 Target Achievement:")
    print(f"  Accuracy:  {'✓' if test_acc >= 0.62 else '✗'} {test_acc:.2%} (target: 62%+)")
    print(f"  Log Loss:  {'✓' if test_logloss <= 0.670 else '✗'} {test_logloss:.4f} (target: ≤0.670)")

    if test_acc >= 0.62:
        print(f"\n🎉 SUCCESS! V7.3 achieves 62%+ accuracy target!")
        gap_closed = (test_acc - v7_0_acc) * 100
        print(f"   Closed {gap_closed:.2f}pp of the 1.11pp gap from V7.0")
    else:
        gap_remaining = (0.62 - test_acc) * 100
        print(f"\n⚠️  Gap remaining: {gap_remaining:.2f}pp to 62% target")

    # Confidence buckets
    bucket_results = evaluate_confidence_buckets(y_test.values, y_test_pred_proba, "V7.3")

    # Compare A+ bucket
    a_plus_acc = bucket_results[0][2]
    a_plus_games = bucket_results[0][1]

    print(f"\nA+ Bucket Comparison:")
    print(f"  V7.0:  {v7_0_a_plus_acc:.1%} ({v7_0_a_plus_games} games)")
    print(f"  V7.3:  {a_plus_acc:.1%} ({a_plus_games} games)")
    if a_plus_games > 0:
        print(f"  Change: {'+' if a_plus_acc > v7_0_a_plus_acc else ''}{(a_plus_acc - v7_0_a_plus_acc)*100:.1f}pp")

    # Feature importance (V7.3 situational features)
    print("\n" + "="*80)
    print("V7.3 Situational Feature Importance")
    print("="*80)

    feature_names = X_train.columns.tolist()
    coefficients = model.named_steps['clf'].coef_[0]

    # Get V7.3 features
    v7_3_features = [
        (name, coef) for name, coef in zip(feature_names, coefficients)
        if any(keyword in name for keyword in ['fatigue', 'trailing', 'travel', 'divisional', 'break'])
    ]
    v7_3_features.sort(key=lambda x: abs(x[1]), reverse=True)

    print(f"\nV7.3 Feature Coefficients:")
    print(f"{'Feature':<40} {'Coefficient':>12} {'Abs Importance':>15}")
    print("-" * 70)
    for name, coef in v7_3_features:
        print(f"{name:<40} {coef:>12.4f} {abs(coef):>15.4f}")

    # Overall top 20 features
    print(f"\nTop 20 Features Overall (V7.0 + V7.3):")
    print(f"{'Rank':<6} {'Feature':<45} {'Coefficient':>12}")
    print("-" * 70)

    all_features = [(name, coef) for name, coef in zip(feature_names, coefficients)]
    all_features.sort(key=lambda x: abs(x[1]), reverse=True)

    for i, (name, coef) in enumerate(all_features[:20], 1):
        v7_3_marker = "⭐" if any(kw in name for kw in ['fatigue', 'trailing', 'travel', 'divisional', 'break']) else ""
        print(f"{i:<6} {name:<45} {coef:>12.4f} {v7_3_marker}")

    # Final recommendation
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)

    if test_acc >= 0.62 and test_logloss <= 0.670:
        print("✅ DEPLOY V7.3: Both targets achieved!")
        print("   STATUS: Production ready")
        print("   NEXT STEP: Deploy to production, monitor performance")
    elif test_acc >= 0.62:
        print("✅ ACCURACY TARGET MET!")
        print("   STATUS: Proceed to calibration tuning for log-loss")
        print("   NEXT STEP: Temperature scaling to get log-loss under 0.670")
    elif test_acc > v7_0_acc:
        print("⚠️  IMPROVEMENT BUT NOT AT TARGET")
        print(f"   Gained {improvement_acc:.2f}pp over V7.0")
        print(f"   Need {(0.62 - test_acc)*100:.2f}pp more to reach 62%")
        print("   NEXT STEP: Consider additional features or accept V7.3 as best")
    else:
        print("❌ NO IMPROVEMENT OVER V7.0")
        print("   RECOMMENDATION: Keep V7.0 as production model")
        print("   NEXT STEP: Re-evaluate feature engineering approach")

    print()
    print("="*80)
    print(f"V7.3 Training Complete!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    main()
