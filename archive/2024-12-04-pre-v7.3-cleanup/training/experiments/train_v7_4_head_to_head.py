#!/usr/bin/env python3
"""
V7.4: Train model with Head-to-Head Matchup Features

Based on V7.3 error analysis, many errors cluster in specific matchups.
This version adds 6 H2H features to capture historical matchup performance.

Expected improvement: +0.2-0.4pp accuracy
Target: Close 30-60% of the 0.62pp gap to 62%
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
from nhl_prediction.head_to_head_features import add_head_to_head_features

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
OPTIMAL_C = 0.05
OPTIMAL_DECAY = 1.0


def main():
    print("=" * 80)
    print("V7.4: Training with Head-to-Head Matchup Features")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load V7.0 dataset
    print("=" * 80)
    print("[1/5] Loading V7.0 dataset...")
    print("=" * 80)
    dataset = build_dataset(TRAIN_SEASONS + [TEST_SEASON])
    print(f"✓ Loaded {len(dataset.games)} games")
    print(f"✓ V7.0 base features: {len(dataset.features.columns)}")
    print()

    # Add V7.3 situational features
    print("=" * 80)
    print("[2/5] Adding V7.3 situational features...")
    print("=" * 80)
    games_with_situational = add_situational_features(dataset.games)

    v7_3_features = [
        'fatigue_index_diff', 'third_period_trailing_perf_diff',
        'travel_distance_diff', 'divisional_matchup',
        'post_break_game_home', 'post_break_game_away', 'post_break_game_diff'
    ]
    available_v7_3 = [f for f in v7_3_features if f in games_with_situational.columns]
    print(f"✓ V7.3 features available: {len(available_v7_3)}")
    print()

    # Add V7.4 head-to-head features
    print("=" * 80)
    print("[3/5] Adding V7.4 head-to-head features...")
    print("=" * 80)
    # Pass training seasons to prevent test set leakage
    games_with_h2h = add_head_to_head_features(games_with_situational, train_seasons=TRAIN_SEASONS)

    v7_4_features = [
        'h2h_win_pct_last_season',
        'h2h_win_pct_recent',
        'h2h_goal_diff_recent',
        'h2h_home_advantage',
        'season_series_home_wins',
        'season_series_away_wins',
    ]
    available_v7_4 = [f for f in v7_4_features if f in games_with_h2h.columns]
    print(f"✓ V7.4 H2H features available: {len(available_v7_4)}")
    print()

    # Combine all features
    all_new_features = available_v7_3 + available_v7_4
    features_v7_4 = pd.concat([
        dataset.features,
        games_with_h2h[all_new_features]
    ], axis=1)

    print(f"Feature Summary:")
    print(f"  V7.0 base: {len(dataset.features.columns)}")
    print(f"  V7.3 situational: {len(available_v7_3)}")
    print(f"  V7.4 head-to-head: {len(available_v7_4)}")
    print(f"  Total: {len(features_v7_4.columns)}")
    print()

    # Train/test split
    print("=" * 80)
    print("[4/5] Preparing train/test split...")
    print("=" * 80)
    train_mask = dataset.games['seasonId'].isin(TRAIN_SEASONS)
    test_mask = dataset.games['seasonId'] == TEST_SEASON

    X_train = features_v7_4[train_mask]
    y_train = dataset.target[train_mask]
    X_test = features_v7_4[test_mask]
    y_test = dataset.target[test_mask]

    train_weights = compute_season_weights(
        dataset.games[train_mask],
        TRAIN_SEASONS,
        decay_factor=OPTIMAL_DECAY
    )

    train_mask_fit = dataset.games[train_mask]['games_played_prior_home'] > 10

    print(f"Training games: {len(X_train)}")
    print(f"Test games: {len(X_test)}")
    print(f"Features: {len(features_v7_4.columns)}")
    print(f"Home team wins (train): {y_train.mean():.1%}")
    print(f"Home team wins (test): {y_test.mean():.1%}")
    print()

    # Train model
    print("=" * 80)
    print(f"[5/5] Training V7.4 model (C={OPTIMAL_C})...")
    print("=" * 80)
    model = create_baseline_model(C=OPTIMAL_C)
    model = fit_model(model, X_train, y_train, train_mask_fit, sample_weight=train_weights)
    print(f"✓ Model trained")
    print()

    # Evaluate
    print("=" * 80)
    print("Evaluating V7.4 performance...")
    print("=" * 80)
    test_mask_predict = pd.Series([True] * len(X_test), index=X_test.index)
    y_test_pred_proba = predict_probabilities(model, X_test, test_mask_predict)
    y_test_pred = (y_test_pred_proba >= 0.5).astype(int)

    test_acc = accuracy_score(y_test, y_test_pred)
    test_roc_auc = roc_auc_score(y_test, y_test_pred_proba)
    test_log_loss = log_loss(y_test, y_test_pred_proba)

    print()
    print("=" * 80)
    print("V7.4 RESULTS")
    print("=" * 80)
    print()
    print("Test Set Performance:")
    print(f"  Accuracy:  {test_acc:.4f} ({test_acc*100:.2f}%)")
    print(f"  ROC-AUC:   {test_roc_auc:.4f}")
    print(f"  Log Loss:  {test_log_loss:.4f}")
    print()

    # Compare to previous versions
    v7_0_acc = 0.6089
    v7_3_acc = 0.6138
    target_acc = 0.62

    improvement_v7_0 = (test_acc - v7_0_acc) * 100
    improvement_v7_3 = (test_acc - v7_3_acc) * 100
    gap_closed = improvement_v7_3 / (target_acc - v7_3_acc) * 100 if v7_3_acc < target_acc else 0

    print("📊 Model Comparison:")
    print(f"  V7.0 (baseline):      60.89%")
    print(f"  V7.3 (situational):   61.38%")
    print(f"  V7.4 (+ H2H):         {test_acc*100:.2f}%")
    print(f"  Target:               62.00%")
    print()

    print("📈 Improvements:")
    print(f"  vs V7.0:  {improvement_v7_0:+.2f} pp")
    print(f"  vs V7.3:  {improvement_v7_3:+.2f} pp")
    if gap_closed > 0:
        print(f"  Gap closed: {gap_closed:.1f}% of 0.62pp gap to 62%")
    print()

    # Feature importance
    print("=" * 80)
    print("Top 20 Most Important Features:")
    print("=" * 80)
    lr = model.named_steps['clf']
    feature_names = features_v7_4.columns
    coefficients = lr.coef_[0]

    feature_importance = [(f, coefficients[i]) for i, f in enumerate(feature_names)]
    feature_importance.sort(key=lambda x: abs(x[1]), reverse=True)

    print(f"{'Feature':<50s} {'Coefficient':>12s}  {'Abs Importance':>15s}")
    print("-" * 80)
    for feat, coef in feature_importance[:20]:
        print(f"{feat:<50s} {coef:12.4f}  {abs(coef):15.4f}")

    # H2H feature importance specifically
    print()
    print("=" * 80)
    print("V7.4 Head-to-Head Feature Importance:")
    print("=" * 80)
    h2h_features = [f for f in feature_names if 'h2h_' in f or 'season_series_' in f]
    h2h_coefs = [(f, coefficients[list(feature_names).index(f)]) for f in h2h_features]
    h2h_coefs.sort(key=lambda x: abs(x[1]), reverse=True)

    print(f"{'Feature':<40s} {'Coefficient':>12s}  {'Abs Importance':>15s}")
    print("-" * 70)
    for feat, coef in h2h_coefs:
        print(f"{feat:<40s} {coef:12.4f}  {abs(coef):15.4f}")

    print()
    print("=" * 80)
    print("V7.4 Training Complete!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
