#!/usr/bin/env python3
"""
Confidence Calibration Analysis

Analyze how well-calibrated V7.3's predicted probabilities are.
From error analysis: 15-20pt confidence has 47% error rate.

Test if we can improve by:
1. Adjusting decision threshold from 0.5
2. Refusing low-confidence predictions
3. Recalibrating probabilities
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, brier_score_loss
from sklearn.calibration import calibration_curve

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities
from nhl_prediction.train import compute_season_weights
from nhl_prediction.situational_features import add_situational_features

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
OPTIMAL_C = 0.05
OPTIMAL_DECAY = 1.0


def analyze_calibration(y_true, y_prob):
    """Analyze prediction calibration."""
    print("=" * 80)
    print("CALIBRATION ANALYSIS")
    print("=" * 80)

    # Overall metrics
    brier = brier_score_loss(y_true, y_prob)
    print(f"\nBrier Score: {brier:.4f} (lower is better)")
    print(f"Baseline accuracy (0.5 threshold): {((y_prob >= 0.5).astype(int) == y_true).mean():.4f}")

    # Calibration curve
    prob_true, prob_pred = calibration_curve(y_true, y_prob, n_bins=10, strategy='uniform')

    print("\nCalibration Curve (10 bins):")
    print(f"{'Predicted':>12s} {'Actual':>12s} {'Diff':>12s} {'Count':>8s}")
    print("-" * 50)

    # Count samples in each bin
    bin_edges = np.linspace(0, 1, 11)
    for i in range(len(prob_pred)):
        # Count samples in this bin
        mask = (y_prob >= bin_edges[i]) & (y_prob < bin_edges[i+1])
        count = mask.sum()

        diff = prob_true[i] - prob_pred[i]
        print(f"{prob_pred[i]:12.3f} {prob_true[i]:12.3f} {diff:+12.3f} {count:8d}")

    # Analyze by confidence level
    print("\n" + "=" * 80)
    print("ACCURACY BY CONFIDENCE LEVEL")
    print("=" * 80)

    confidence = np.abs(y_prob - 0.5)  # Distance from 0.5

    bins = [
        ("Very High (25+ pts)", 0.25, 1.0),
        ("High (20-25 pts)", 0.20, 0.25),
        ("Medium (15-20 pts)", 0.15, 0.20),
        ("Low (10-15 pts)", 0.10, 0.15),
        ("Very Low (5-10 pts)", 0.05, 0.10),
        ("Extremely Low (0-5 pts)", 0.00, 0.05),
    ]

    print(f"\n{'Confidence':>22s} {'Games':>8s} {'Accuracy':>10s} {'Avg Prob':>10s} {'Actual Rate':>12s}")
    print("-" * 70)

    for name, min_conf, max_conf in bins:
        mask = (confidence >= min_conf) & (confidence < max_conf)
        if mask.sum() > 0:
            acc = ((y_prob[mask] >= 0.5).astype(int) == y_true[mask]).mean()
            avg_prob = y_prob[mask].mean()
            actual_rate = y_true[mask].mean()

            print(f"{name:>22s} {mask.sum():8d} {acc*100:9.2f}% {avg_prob:10.3f} {actual_rate:12.3f}")

    # Test different thresholds
    print("\n" + "=" * 80)
    print("OPTIMAL THRESHOLD SEARCH")
    print("=" * 80)

    thresholds = np.arange(0.45, 0.56, 0.01)
    best_acc = 0
    best_threshold = 0.5

    print(f"\n{'Threshold':>12s} {'Accuracy':>10s} {'Predictions':>12s}")
    print("-" * 40)

    for thresh in thresholds:
        y_pred = (y_prob >= thresh).astype(int)
        acc = accuracy_score(y_true, y_pred)

        print(f"{thresh:12.2f} {acc*100:9.2f}% {y_pred.sum():12d}")

        if acc > best_acc:
            best_acc = acc
            best_threshold = thresh

    print(f"\nBest threshold: {best_threshold:.2f} (accuracy: {best_acc*100:.2f}%)")

    # Analyze coverage vs accuracy tradeoff
    print("\n" + "=" * 80)
    print("COVERAGE VS ACCURACY TRADEOFF")
    print("=" * 80)

    min_confidences = [0.00, 0.05, 0.10, 0.15, 0.20, 0.25]

    print(f"\n{'Min Confidence':>15s} {'Coverage':>10s} {'Accuracy':>10s} {'Improvement':>12s}")
    print("-" * 55)

    baseline_acc = ((y_prob >= 0.5).astype(int) == y_true).mean()

    for min_conf in min_confidences:
        mask = confidence >= min_conf
        if mask.sum() > 0:
            coverage = mask.sum() / len(y_true)
            acc = ((y_prob[mask] >= 0.5).astype(int) == y_true[mask]).mean()
            improvement = (acc - baseline_acc) * 100

            print(f"{min_conf*100:15.0f}% {coverage*100:9.1f}% {acc*100:9.2f}% {improvement:+11.2f}pp")


def main():
    print("=" * 80)
    print("Confidence Calibration Analysis")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load dataset
    print("Loading dataset...")
    dataset = build_dataset(TRAIN_SEASONS + [TEST_SEASON])
    print(f"✓ Loaded {len(dataset.games)} games")

    # Add V7.3 features
    print("Adding V7.3 situational features...")
    games_with_situational = add_situational_features(dataset.games)

    v7_3_features = [
        'fatigue_index_diff', 'third_period_trailing_perf_diff',
        'travel_distance_diff', 'divisional_matchup',
        'post_break_game_home', 'post_break_game_away', 'post_break_game_diff'
    ]
    available_v7_3 = [f for f in v7_3_features if f in games_with_situational.columns]

    features_v7_3 = pd.concat([
        dataset.features,
        games_with_situational[available_v7_3]
    ], axis=1)

    print(f"✓ Total features: {len(features_v7_3.columns)}")
    print()

    # Train/test split
    train_mask = dataset.games['seasonId'].isin(TRAIN_SEASONS)
    test_mask = dataset.games['seasonId'] == TEST_SEASON

    X_train = features_v7_3[train_mask]
    y_train = dataset.target[train_mask]
    X_test = features_v7_3[test_mask]
    y_test = dataset.target[test_mask]

    train_weights = compute_season_weights(
        dataset.games[train_mask],
        TRAIN_SEASONS,
        decay_factor=OPTIMAL_DECAY
    )

    train_mask_fit = dataset.games[train_mask]['games_played_prior_home'] > 10

    print("Training V7.3 model...")
    model = create_baseline_model(C=OPTIMAL_C)
    model = fit_model(model, X_train, y_train, train_mask_fit, sample_weight=train_weights)
    print("✓ Model trained")
    print()

    # Get predictions
    test_mask_predict = pd.Series([True] * len(X_test), index=X_test.index)
    y_pred_proba = predict_probabilities(model, X_test, test_mask_predict)

    # Analyze calibration
    analyze_calibration(y_test.values, y_pred_proba)

    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
