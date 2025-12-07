#!/usr/bin/env python3
"""
Away Back-to-Back Weakness Analysis

V7.0 error analysis showed:
- Away B2B errors: 56
- Home B2B errors: 14
- 4x worse prediction for away B2B games

This script investigates why and builds enhanced B2B features.
"""

import sys
import pickle
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

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


def analyze_b2b_performance(games: pd.DataFrame, predictions: np.ndarray, actuals: np.ndarray, pred_proba: np.ndarray):
    """Analyze prediction accuracy in different B2B scenarios."""

    games = games.copy()
    games['predicted'] = predictions
    games['actual'] = actuals
    games['pred_proba'] = pred_proba
    games['correct'] = (predictions == actuals)

    print("=" * 80)
    print("BACK-TO-BACK PREDICTION ANALYSIS")
    print("=" * 80)

    # Create B2B categories
    scenarios = {
        'Neither B2B': (games['home_b2b'] == 0) & (games['away_b2b'] == 0),
        'Home B2B only': (games['home_b2b'] == 1) & (games['away_b2b'] == 0),
        'Away B2B only': (games['home_b2b'] == 0) & (games['away_b2b'] == 1),
        'Both B2B': (games['home_b2b'] == 1) & (games['away_b2b'] == 1),
    }

    print(f"\n{'Scenario':<20s} {'Games':>6s} {'Accuracy':>9s} {'Errors':>7s} {'Home Win%':>10s}")
    print("-" * 70)

    for scenario_name, mask in scenarios.items():
        scenario_games = games[mask]
        if len(scenario_games) > 0:
            accuracy = scenario_games['correct'].mean()
            errors = (~scenario_games['correct']).sum()
            home_win_pct = scenario_games['actual'].mean()

            print(f"{scenario_name:<20s} {len(scenario_games):6d} {accuracy*100:8.2f}% {errors:7d} {home_win_pct*100:9.2f}%")

    # Deep dive on away B2B
    print("\n" + "=" * 80)
    print("AWAY BACK-TO-BACK DEEP DIVE")
    print("=" * 80)

    away_b2b = games[(games['home_b2b'] == 0) & (games['away_b2b'] == 1)].copy()

    print(f"\nAway B2B Games: {len(away_b2b)}")
    print(f"Actual home win rate: {away_b2b['actual'].mean():.1%}")
    print(f"Predicted home win rate: {away_b2b['predicted'].mean():.1%}")
    print(f"Accuracy: {away_b2b['correct'].mean():.1%}")

    # Check if we're systematically over/under predicting
    print(f"\nPrediction calibration:")
    print(f"  Mean predicted probability: {away_b2b['pred_proba'].mean():.3f}")
    print(f"  Actual home win rate: {away_b2b['actual'].mean():.3f}")
    print(f"  Bias: {away_b2b['pred_proba'].mean() - away_b2b['actual'].mean():.3f}")

    # Analyze by rest differential
    print("\n" + "=" * 80)
    print("AWAY B2B BY REST DIFFERENTIAL")
    print("=" * 80)

    away_b2b['rest_diff_bucket'] = pd.cut(
        away_b2b['rest_diff'],
        bins=[-10, -2, -1, 0, 1, 2, 10],
        labels=['< -2', '-2', '-1', '0', '1', '2+']
    )

    print(f"\n{'Rest Diff':<10s} {'Games':>6s} {'Accuracy':>9s} {'Home Win%':>10s} {'Pred Win%':>10s}")
    print("-" * 60)

    for bucket in away_b2b['rest_diff_bucket'].cat.categories:
        bucket_games = away_b2b[away_b2b['rest_diff_bucket'] == bucket]
        if len(bucket_games) > 0:
            acc = bucket_games['correct'].mean()
            actual_win = bucket_games['actual'].mean()
            pred_win = bucket_games['pred_proba'].mean()

            print(f"{bucket:<10s} {len(bucket_games):6d} {acc*100:8.2f}% {actual_win*100:9.2f}% {pred_win*100:9.2f}%")

    # Analyze by travel distance
    if 'travel_distance_away' in away_b2b.columns:
        print("\n" + "=" * 80)
        print("AWAY B2B BY TRAVEL DISTANCE")
        print("=" * 80)

        away_b2b['travel_bucket'] = pd.cut(
            away_b2b['travel_distance_away'],
            bins=[0, 500, 1000, 1500, 3000],
            labels=['<500mi', '500-1k', '1-1.5k', '1.5k+']
        )

        print(f"\n{'Travel':<10s} {'Games':>6s} {'Accuracy':>9s} {'Home Win%':>10s} {'Pred Win%':>10s}")
        print("-" * 60)

        for bucket in away_b2b['travel_bucket'].cat.categories:
            bucket_games = away_b2b[away_b2b['travel_bucket'] == bucket]
            if len(bucket_games) > 0:
                acc = bucket_games['correct'].mean()
                actual_win = bucket_games['actual'].mean()
                pred_win = bucket_games['pred_proba'].mean()

                print(f"{bucket:<10s} {len(bucket_games):6d} {acc*100:8.2f}% {actual_win*100:9.2f}% {pred_win*100:9.2f}%")


def main():
    print("=" * 80)
    print("Away Back-to-Back Weakness Analysis")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load dataset
    print("Loading dataset...")
    dataset = build_dataset(TRAIN_SEASONS + [TEST_SEASON])
    print(f"✓ Loaded {len(dataset.games)} games")
    print()

    # Add situational features
    print("Adding situational features...")
    games_with_situational = add_situational_features(dataset.games)

    # Use V7.0 features only (to isolate B2B effect)
    features_v7_0 = dataset.features

    print(f"✓ Features: {len(features_v7_0.columns)}")
    print()

    # Train/test split
    train_mask = dataset.games['seasonId'].isin(TRAIN_SEASONS)
    test_mask = dataset.games['seasonId'] == TEST_SEASON

    X_train = features_v7_0[train_mask]
    y_train = dataset.target[train_mask]
    X_test = features_v7_0[test_mask]
    y_test = dataset.target[test_mask]

    train_weights = compute_season_weights(
        dataset.games[train_mask],
        TRAIN_SEASONS,
        decay_factor=OPTIMAL_DECAY
    )

    train_mask_fit = dataset.games[train_mask]['games_played_prior_home'] > 10

    print(f"Training V7.0 baseline model...")
    model = create_baseline_model(C=OPTIMAL_C)
    model = fit_model(model, X_train, y_train, train_mask_fit, sample_weight=train_weights)
    print("✓ Model trained")
    print()

    # Get predictions
    test_mask_predict = pd.Series([True] * len(X_test), index=X_test.index)
    y_pred_proba = predict_probabilities(model, X_test, test_mask_predict)
    y_pred = (y_pred_proba >= 0.5).astype(int)

    accuracy = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {accuracy*100:.2f}%")
    print()

    # Analyze B2B performance
    test_games = games_with_situational[test_mask].copy()
    analyze_b2b_performance(test_games, y_pred, y_test.values, y_pred_proba)

    print("\n" + "=" * 80)
    print("Analysis Complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
