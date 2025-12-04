#!/usr/bin/env python3
"""
V7.6: Train model with Team-Specific Calibration

Adds bias adjustment features for teams with highest error rates:
- VGK (34.7% error rate)
- PHI (33.9%)
- NYI (32.2%)
- WSH, PIT

Expected improvement: +0.1-0.3pp accuracy
Target: Close gap to 62%
"""

import sys
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities
from nhl_prediction.train import compute_season_weights
from nhl_prediction.team_calibration_features import add_team_calibration_features

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
OPTIMAL_C = 0.05
OPTIMAL_DECAY = 1.0


def main():
    print("=" * 80)
    print("V7.6: Training with Team-Specific Calibration")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load V7.0 dataset
    print("=" * 80)
    print("[1/3] Loading V7.0 dataset...")
    print("=" * 80)
    dataset = build_dataset(TRAIN_SEASONS + [TEST_SEASON])
    print(f"✓ Loaded {len(dataset.games)} games")
    print(f"✓ V7.0 base features: {len(dataset.features.columns)}")
    print()

    # Add V7.6 team calibration features
    print("=" * 80)
    print("[2/3] Adding V7.6 team calibration features...")
    print("=" * 80)
    features_with_calibration = add_team_calibration_features(dataset.features, dataset.games)

    calibration_features = [c for c in features_with_calibration.columns if c.startswith('team_')]
    print(f"✓ Calibration features added: {len(calibration_features)}")
    print()

    print(f"Feature Summary:")
    print(f"  V7.0 base: {len(dataset.features.columns)}")
    print(f"  V7.6 team calibration: {len(calibration_features)}")
    print(f"  Total: {len(features_with_calibration.columns)}")
    print()

    # Train/test split
    print("=" * 80)
    print("[3/3] Training V7.6 model...")
    print("=" * 80)
    train_mask = dataset.games['seasonId'].isin(TRAIN_SEASONS)
    test_mask = dataset.games['seasonId'] == TEST_SEASON

    X_train = features_with_calibration[train_mask]
    y_train = dataset.target[train_mask]
    X_test = features_with_calibration[test_mask]
    y_test = dataset.target[test_mask]

    train_weights = compute_season_weights(
        dataset.games[train_mask],
        TRAIN_SEASONS,
        decay_factor=OPTIMAL_DECAY
    )

    train_mask_fit = dataset.games[train_mask]['games_played_prior_home'] > 10

    print(f"Training games: {len(X_train)}")
    print(f"Test games: {len(X_test)}")
    print(f"Features: {len(features_with_calibration.columns)}")
    print()

    # Train model
    print(f"Training V7.6 model (C={OPTIMAL_C})...")
    model = create_baseline_model(C=OPTIMAL_C)
    model = fit_model(model, X_train, y_train, train_mask_fit, sample_weight=train_weights)
    print(f"✓ Model trained")
    print()

    # Evaluate
    print("=" * 80)
    print("Evaluating V7.6 performance...")
    print("=" * 80)
    test_mask_predict = pd.Series([True] * len(X_test), index=X_test.index)
    y_test_pred_proba = predict_probabilities(model, X_test, test_mask_predict)
    y_test_pred = (y_test_pred_proba >= 0.5).astype(int)

    test_acc = accuracy_score(y_test, y_test_pred)
    test_roc_auc = roc_auc_score(y_test, y_test_pred_proba)
    test_log_loss = log_loss(y_test, y_test_pred_proba)

    print()
    print("=" * 80)
    print("V7.6 RESULTS")
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
    print(f"  V7.0 (baseline):          60.89%")
    print(f"  V7.3 (situational):       61.38%")
    print(f"  V7.6 (+ calibration):     {test_acc*100:.2f}%")
    print(f"  Target:                   62.00%")
    print()

    print("📈 Improvements:")
    print(f"  vs V7.0:  {improvement_v7_0:+.2f} pp")
    print(f"  vs V7.3:  {improvement_v7_3:+.2f} pp")
    if gap_closed > 0:
        print(f"  Gap closed: {gap_closed:.1f}% of 0.62pp gap to 62%")
    print()

    # Feature importance
    print("=" * 80)
    print("Team Calibration Feature Importance:")
    print("=" * 80)
    lr = model.named_steps['clf']
    feature_names = features_with_calibration.columns
    coefficients = lr.coef_[0]

    # Get calibration features
    calibration_coefs = [(f, coefficients[list(feature_names).index(f)]) for f in calibration_features]
    calibration_coefs.sort(key=lambda x: abs(x[1]), reverse=True)

    print(f"{'Feature':<30s} {'Coefficient':>12s}  {'Abs Importance':>15s}")
    print("-" * 60)
    for feat, coef in calibration_coefs:
        print(f"{feat:<30s} {coef:12.4f}  {abs(coef):15.4f}")

    print()
    print("=" * 80)
    print("V7.6 Training Complete!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
