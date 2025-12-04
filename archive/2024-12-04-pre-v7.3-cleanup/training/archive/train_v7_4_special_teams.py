#!/usr/bin/env python3
"""
V7.4: Enhanced Special Teams Features

V7.3 (222 features) + 6 new special teams features = 228 total features

V7.3 BASELINE: 61.38% accuracy (0.62pp short of 62% target)

NEW FEATURES (6):
1. special_teams_goal_diff_rolling - (PP goals - SH goals allowed) last 10 games
2. pp_opportunities_rolling - Penalties drawn last 10 games
3. pk_opportunities_rolling - Penalties taken last 10 games
4. special_teams_efficiency_diff - (PP goals/opps) - (SH allowed/opps)
5. pp_home_away_variance - PP% difference home vs away
6. pk_home_away_variance - PK% difference home vs away

WHY THESE FEATURES:
- ALL 16 existing special teams features have ZERO coefficients in V7.0-V7.3
- Raw PP%/PK% are collinear with goal differential
- These enhanced features capture IMPACT and OPPORTUNITIES, not just percentages
- Special teams account for 20-25% of goals but model completely ignores them

Expected improvement: +0.30 to +0.50pp (conservative: +0.15 to +0.25pp)
Target: Close final 0.62pp gap from 61.38% → 62%+
"""

import sys
import pickle
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities
from nhl_prediction.train import compute_season_weights
from nhl_prediction.situational_features import add_situational_features
from nhl_prediction.special_teams_features import add_special_teams_features

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
    """Train V7.4 model with enhanced special teams features."""
    print("="*80)
    print("V7.4: Training with Enhanced Special Teams Features")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("BASELINE: V7.3 Situational Features")
    print("  Features:  222 (V7.0: 209 + V7.3: 13)")
    print("  Accuracy:  61.38%")
    print("  Log Loss:  0.6698 (TARGET HIT! ≤0.670)")
    print("  A+ Bucket: 71.1% (246 games)")
    print()
    print("V7.4 ADDITIONS: 6 Enhanced Special Teams Features")
    print("  1. Special Teams Goal Differential (rolling 10)")
    print("  2. PP Opportunities (penalties drawn)")
    print("  3. PK Opportunities (penalties taken)")
    print("  4. Special Teams Efficiency")
    print("  5. PP Home/Away Variance")
    print("  6. PK Home/Away Variance")
    print()
    print("  WHY: ALL 16 existing special teams features = ZERO coefficients")
    print("       Raw PP%/PK% collinear with goal differential")
    print("       These features capture IMPACT, not just percentages")
    print()
    print("  Expected: +0.15 to +0.50pp accuracy improvement")
    print("  Target:   62%+ accuracy (need +0.62pp from V7.3)")
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

    games_with_situational = add_situational_features(dataset.games)

    situational_feature_cols = [
        'fatigue_index_home', 'fatigue_index_away', 'fatigue_index_diff',
        'third_period_trailing_perf_home', 'third_period_trailing_perf_away', 'third_period_trailing_perf_diff',
        'travel_distance_home', 'travel_distance_away', 'travel_distance_diff',
        'divisional_matchup',
        'post_break_game_home', 'post_break_game_away', 'post_break_game_diff',
    ]

    available_situational = [col for col in situational_feature_cols if col in games_with_situational.columns]
    print(f"✓ Added {len(available_situational)} V7.3 situational features")
    print()

    # Add V7.4 special teams features
    print("=" * 80)
    print("[3/5] Adding V7.4 enhanced special teams features...")
    print("=" * 80)

    games_with_all_features = add_special_teams_features(games_with_situational)

    special_teams_feature_cols = [
        'special_teams_goal_diff_rolling_home', 'special_teams_goal_diff_rolling_away', 'special_teams_goal_diff_rolling_diff',
        'pp_opportunities_rolling_home', 'pp_opportunities_rolling_away', 'pp_opportunities_rolling_diff',
        'pk_opportunities_rolling_home', 'pk_opportunities_rolling_away', 'pk_opportunities_rolling_diff',
        'special_teams_efficiency_home', 'special_teams_efficiency_away', 'special_teams_efficiency_diff',
        'pp_home_away_variance_home', 'pp_home_away_variance_away', 'pp_home_away_variance_diff',
        'pk_home_away_variance_home', 'pk_home_away_variance_away', 'pk_home_away_variance_diff',
    ]

    available_special_teams = [col for col in special_teams_feature_cols if col in games_with_all_features.columns]
    print(f"✓ Added {len(available_special_teams)} V7.4 special teams features")
    print(f"  Features: {', '.join(available_special_teams[:3])}...")

    # Combine V7.0 + V7.3 + V7.4 features
    features_v7_4 = pd.concat([
        dataset.features,
        games_with_all_features[available_situational],
        games_with_all_features[available_special_teams]
    ], axis=1)

    print(f"✓ Total V7.4 features: {len(features_v7_4.columns)} (V7.0: 209 + V7.3: {len(available_situational)} + V7.4: {len(available_special_teams)})")
    print()

    # Split train/test
    print("=" * 80)
    print("[4/5] Preparing train/test split...")
    print("=" * 80)

    train_mask = dataset.games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = dataset.games["seasonId"] == TEST_SEASON

    X = features_v7_4.fillna(0)
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

    # Train V7.4 model
    print("=" * 80)
    print(f"[5/5] Training V7.4 model (C={OPTIMAL_C})...")
    print("=" * 80)

    model = create_baseline_model(C=OPTIMAL_C)
    train_mask_fit = pd.Series(True, index=X_train.index)
    model = fit_model(model, X_train, y_train, train_mask_fit, sample_weight=train_weights)

    print("✓ Model trained")
    print(f"   Features used: {len(X_train.columns)}")
    print()

    # Evaluate
    print("=" * 80)
    print("[6/6] Evaluating V7.4 performance...")
    print("=" * 80)

    test_mask_pred = pd.Series(True, index=X_test.index)
    y_test_pred_proba = predict_probabilities(model, X_test, test_mask_pred)
    y_test_pred = (y_test_pred_proba >= 0.5).astype(int)

    test_acc = accuracy_score(y_test, y_test_pred)
    test_auc = roc_auc_score(y_test, y_test_pred_proba)
    test_logloss = log_loss(y_test, y_test_pred_proba)

    print()
    print("=" * 80)
    print("V7.4 RESULTS")
    print("=" * 80)
    print(f"\nTest Set Performance:")
    print(f"  Accuracy:  {test_acc:.4f} ({test_acc:.2%})")
    print(f"  ROC-AUC:   {test_auc:.4f}")
    print(f"  Log Loss:  {test_logloss:.4f}")

    # Compare to V7.3
    v7_3_acc = 0.6138
    v7_3_logloss = 0.6698
    v7_3_a_plus_acc = 0.711
    v7_3_a_plus_games = 246

    improvement_acc = (test_acc - v7_3_acc) * 100
    improvement_logloss = v7_3_logloss - test_logloss

    print(f"\n📊 vs V7.3 Baseline:")
    print(f"  Accuracy:  {'+' if improvement_acc > 0 else ''}{improvement_acc:.2f} pp ({test_acc:.2%} vs {v7_3_acc:.2%})")
    print(f"  Log Loss:  {'+' if improvement_logloss > 0 else ''}{improvement_logloss:.4f} ({test_logloss:.4f} vs {v7_3_logloss:.4f})")

    # Target achievement
    print(f"\n🎯 Target Achievement:")
    print(f"  Accuracy:  {'✓' if test_acc >= 0.62 else '✗'} {test_acc:.2%} (target: 62%+)")
    print(f"  Log Loss:  {'✓' if test_logloss <= 0.670 else '✗'} {test_logloss:.4f} (target: ≤0.670)")

    if test_acc >= 0.62:
        print(f"\n🎉 SUCCESS! V7.4 achieves 62%+ accuracy target!")
        gap_closed = (test_acc - v7_3_acc) * 100
        print(f"   Closed {gap_closed:.2f}pp gap from V7.3")
    else:
        gap_remaining = (0.62 - test_acc) * 100
        print(f"\n⚠️  Gap remaining: {gap_remaining:.2f}pp to 62% target")

    # Confidence buckets
    bucket_results = evaluate_confidence_buckets(y_test.values, y_test_pred_proba, "V7.4")

    # Compare A+ bucket
    a_plus_acc = bucket_results[0][2]
    a_plus_games = bucket_results[0][1]

    print(f"\nA+ Bucket Comparison:")
    print(f"  V7.3:  {v7_3_a_plus_acc:.1%} ({v7_3_a_plus_games} games)")
    print(f"  V7.4:  {a_plus_acc:.1%} ({a_plus_games} games)")
    if a_plus_games > 0:
        print(f"  Change: {'+' if a_plus_acc > v7_3_a_plus_acc else ''}{(a_plus_acc - v7_3_a_plus_acc)*100:.1f}pp")

    # Feature importance (V7.4 special teams features)
    print("\n" + "="*80)
    print("V7.4 Special Teams Feature Importance")
    print("="*80)

    feature_names = X_train.columns.tolist()
    coefficients = model.named_steps['clf'].coef_[0]

    # Get V7.4 features
    v7_4_features = [
        (name, coef) for name, coef in zip(feature_names, coefficients)
        if any(keyword in name for keyword in ['special_teams', 'pp_', 'pk_'])
    ]
    v7_4_features.sort(key=lambda x: abs(x[1]), reverse=True)

    print(f"\nV7.4 Feature Coefficients:")
    print(f"{'Feature':<50} {'Coefficient':>12} {'Abs Importance':>15}")
    print("-" * 80)
    for name, coef in v7_4_features:
        print(f"{name:<50} {coef:>12.4f} {abs(coef):>15.4f}")

    # Overall top 20 features
    print(f"\nTop 20 Features Overall (V7.0 + V7.3 + V7.4):")
    print(f"{'Rank':<6} {'Feature':<50} {'Coefficient':>12}")
    print("-" * 80)

    all_features = [(name, coef) for name, coef in zip(feature_names, coefficients)]
    all_features.sort(key=lambda x: abs(x[1]), reverse=True)

    for i, (name, coef) in enumerate(all_features[:20], 1):
        v7_4_marker = "⭐" if any(kw in name for kw in ['special_teams', 'pp_', 'pk_']) else ""
        print(f"{i:<6} {name:<50} {coef:>12.4f} {v7_4_marker}")

    # Final recommendation
    print("\n" + "="*80)
    print("RECOMMENDATION")
    print("="*80)

    if test_acc >= 0.62 and test_logloss <= 0.670:
        print("✅ DEPLOY V7.4: Both targets achieved!")
        print("   STATUS: Production ready")
        print("   NEXT STEP: Deploy to production, monitor performance")
    elif test_acc >= 0.62:
        print("✅ ACCURACY TARGET MET!")
        print("   STATUS: Proceed to calibration tuning for log-loss")
        print("   NEXT STEP: Temperature scaling to get log-loss under 0.670")
    elif test_acc > v7_3_acc:
        print("⚠️  IMPROVEMENT BUT NOT AT TARGET")
        print(f"   Gained {improvement_acc:.2f}pp over V7.3")
        print(f"   Need {(0.62 - test_acc)*100:.2f}pp more to reach 62%")
        print("   NEXT STEP: Consider V7.4 Phase 2 (PDO Regression) or accept current best")
    else:
        print("❌ NO IMPROVEMENT OVER V7.3")
        print("   RECOMMENDATION: Keep V7.3 as production model")
        print("   NEXT STEP: Re-evaluate feature engineering approach (try PDO features)")

    print()
    print("="*80)
    print(f"V7.4 Training Complete!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    main()
