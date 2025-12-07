#!/usr/bin/env python3
"""
V7.0 Baseline Verification Script

Runs the V7.0 model WITHOUT situational features to verify the 60.89% baseline.
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities
from nhl_prediction.train import compute_season_weights

# Configuration - same as V7.3
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
OPTIMAL_C = 0.05
OPTIMAL_DECAY = 1.0


def main():
    print("=" * 80)
    print("V7.0 BASELINE VERIFICATION")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    print("Expected V7.0 Baseline:")
    print("  Accuracy: 60.89%")
    print("  Log Loss: 0.6752")
    print("  Features: 209")
    print()

    # Load dataset (V7.0 baseline only - no situational features)
    print("=" * 80)
    print("[1/4] Loading V7.0 dataset...")
    print("=" * 80)
    dataset = build_dataset(TRAIN_SEASONS + [TEST_SEASON])
    print(f"Loaded {len(dataset.games)} games")
    print(f"Features: {len(dataset.features.columns)}")
    print()

    # Split train/test
    print("=" * 80)
    print("[2/4] Preparing train/test split...")
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
    print()

    # Compute sample weights
    train_weights = compute_season_weights(dataset.games[train_mask], TRAIN_SEASONS, decay_factor=OPTIMAL_DECAY)

    # Train model
    print("=" * 80)
    print(f"[3/4] Training V7.0 model (C={OPTIMAL_C})...")
    print("=" * 80)

    model = create_baseline_model(C=OPTIMAL_C)
    train_mask_fit = pd.Series(True, index=X_train.index)
    model = fit_model(model, X_train, y_train, train_mask_fit, sample_weight=train_weights)
    print("Model trained")
    print()

    # Evaluate
    print("=" * 80)
    print("[4/4] Evaluating V7.0 baseline...")
    print("=" * 80)

    test_mask_pred = pd.Series(True, index=X_test.index)
    y_pred_proba = predict_probabilities(model, X_test, test_mask_pred)
    y_pred = (y_pred_proba >= 0.5).astype(int)

    accuracy = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, y_pred_proba)
    logloss = log_loss(y_test, y_pred_proba)
    brier = np.mean((y_pred_proba - y_test) ** 2)

    print()
    print("=" * 80)
    print("V7.0 BASELINE RESULTS")
    print("=" * 80)
    print(f"  Accuracy:    {accuracy:.4f} ({accuracy:.2%})")
    print(f"  ROC-AUC:     {auc:.4f}")
    print(f"  Log Loss:    {logloss:.4f}")
    print(f"  Brier Score: {brier:.4f}")
    print(f"  Features:    {len(X_train.columns)}")
    print()

    # Compare to claimed baseline
    claimed_acc = 0.6089
    claimed_logloss = 0.6752

    print("COMPARISON TO CLAIMED V7.0:")
    print(f"  Accuracy:  {'+' if accuracy > claimed_acc else ''}{(accuracy - claimed_acc) * 100:.2f} pp ({accuracy:.2%} vs {claimed_acc:.2%})")
    print(f"  Log Loss:  {'+' if logloss < claimed_logloss else ''}{claimed_logloss - logloss:.4f} ({logloss:.4f} vs {claimed_logloss:.4f})")
    print()

    # Confidence buckets
    point_diffs = (y_pred_proba - 0.5) * 100
    buckets = [
        ("A+", 20, 100),
        ("A-", 15, 20),
        ("B+", 10, 15),
        ("B-", 5, 10),
        ("C", 0, 5),
    ]

    print("Confidence Ladder:")
    print(f"{'Grade':<6} {'Range':<12} {'Games':>8} {'Accuracy':>10}")
    print("-" * 40)

    for grade, min_pts, max_pts in buckets:
        mask = (point_diffs >= min_pts) & (point_diffs < max_pts)
        n_games = mask.sum()
        if n_games > 0:
            acc = accuracy_score(y_test[mask], y_pred[mask])
            print(f"{grade:<6} {min_pts:>2d}-{max_pts:>2d} pts   {n_games:>8d} {acc:>9.1%}")
        else:
            print(f"{grade:<6} {min_pts:>2d}-{max_pts:>2d} pts   {n_games:>8d} {'N/A':>10}")

    print()
    print("=" * 80)
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
