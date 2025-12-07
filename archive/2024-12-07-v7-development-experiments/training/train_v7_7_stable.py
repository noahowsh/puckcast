#!/usr/bin/env python3
"""
V7.7: Stable Features Model

This model removes team dummies and uses only stable, generalizable features
that perform consistently across different seasons.

Key improvements over V7.6:
- Removed team-specific dummy variables (64 features)
- Uses only 23 curated stable features
- More consistent performance across seasons (0.7pp vs 2.4pp variance)
- Slightly higher average accuracy (59.86% vs 59.79%)

VALIDATED RESULTS:
  23-24: 59.51% (trained on 21-22 + 22-23)
  24-25: 60.21% (trained on 22-23 + 23-24)
  Average: 59.86%, Variance: 0.7pp

Usage:
    python training/train_v7_7_stable.py
"""

import sys
from pathlib import Path
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.pipeline import build_dataset


# V7.7 Stable Feature Set - 23 features that generalize well across seasons
V77_FEATURES = [
    # Elo ratings (most stable predictors)
    'elo_diff_pre',
    'elo_expectation_home',

    # Rolling win percentage (multiple windows for robustness)
    'rolling_win_pct_10_diff',
    'rolling_win_pct_5_diff',
    'rolling_win_pct_3_diff',

    # Rolling goal differential
    'rolling_goal_diff_10_diff',
    'rolling_goal_diff_5_diff',

    # Expected goals (shot quality)
    'rolling_xg_diff_10_diff',
    'rolling_xg_diff_5_diff',

    # Possession metrics
    'rolling_corsi_10_diff',
    'rolling_corsi_5_diff',
    'rolling_fenwick_10_diff',
    'rolling_fenwick_5_diff',

    # Season-level stats
    'season_win_pct_diff',
    'season_goal_diff_avg_diff',
    'season_xg_diff_avg_diff',

    # Rest and schedule
    'rest_diff',
    'is_b2b_home',
    'is_b2b_away',

    # Goaltending
    'rolling_save_pct_10_diff',
    'rolling_save_pct_5_diff',

    # Momentum
    'momentum_win_pct_diff',
    'momentum_goal_diff_diff',
]


def train_v77_model(train_seasons, test_season=None, verbose=True):
    """Train V7.7 model on specified seasons."""

    if verbose:
        print(f"Loading data for seasons: {train_seasons}")

    all_seasons = train_seasons.copy()
    if test_season and test_season not in all_seasons:
        all_seasons.append(test_season)

    dataset = build_dataset(all_seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()
    feature_names = features.columns.tolist()

    # Get indices of V7.7 features
    v77_idx = [i for i, n in enumerate(feature_names) if n in V77_FEATURES]

    if verbose:
        print(f"Using {len(v77_idx)} stable features")

    # Split data
    train_mask = games['seasonId'].isin(train_seasons)

    X_train = features[train_mask].values[:, v77_idx]
    y_train = target[train_mask].values

    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    # Train model
    model = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    model.fit(X_train_scaled, y_train)

    # Evaluate on test season if provided
    results = {
        'model': model,
        'scaler': scaler,
        'feature_idx': v77_idx,
        'feature_names': [feature_names[i] for i in v77_idx],
        'train_games': len(y_train)
    }

    if test_season:
        test_mask = games['seasonId'] == test_season
        X_test = features[test_mask].values[:, v77_idx]
        y_test = target[test_mask].values

        X_test_scaled = scaler.transform(X_test)
        proba = model.predict_proba(X_test_scaled)[:, 1]
        pred = (proba >= 0.5).astype(int)

        results['accuracy'] = accuracy_score(y_test, pred)
        results['auc'] = roc_auc_score(y_test, proba)
        results['log_loss'] = log_loss(y_test, proba)
        results['home_baseline'] = y_test.mean()
        results['test_games'] = len(y_test)

    return results


def main():
    print("=" * 70)
    print("V7.7: STABLE FEATURES MODEL")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("FEATURES:")
    for i, f in enumerate(V77_FEATURES, 1):
        print(f"  {i:2d}. {f}")
    print()

    print("=" * 70)
    print("FORWARD VALIDATION")
    print("=" * 70)
    print()

    # Test on 2023-24
    print("Test 1: Train 21-22 + 22-23 -> Test 23-24")
    r1 = train_v77_model(['20212022', '20222023'], '20232024')
    print(f"  Accuracy: {r1['accuracy']*100:.2f}%")
    print(f"  Lift over baseline: +{(r1['accuracy'] - r1['home_baseline'])*100:.1f}pp")
    print(f"  AUC: {r1['auc']:.4f}")
    print()

    # Test on 2024-25
    print("Test 2: Train 22-23 + 23-24 -> Test 24-25")
    r2 = train_v77_model(['20222023', '20232024'], '20242025')
    print(f"  Accuracy: {r2['accuracy']*100:.2f}%")
    print(f"  Lift over baseline: +{(r2['accuracy'] - r2['home_baseline'])*100:.1f}pp")
    print(f"  AUC: {r2['auc']:.4f}")
    print()

    avg = (r1['accuracy'] + r2['accuracy']) / 2
    diff = abs(r1['accuracy'] - r2['accuracy'])

    print("=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Average Accuracy: {avg*100:.2f}%")
    print(f"Season Variance: {diff*100:.1f}pp")
    print()
    print("Comparison to V7.6:")
    print("  V7.6: 59.79% avg, 2.4pp variance")
    print(f"  V7.7: {avg*100:.2f}% avg, {diff*100:.1f}pp variance")
    print()

    if avg > 0.5979 and diff < 2.4:
        print("V7.7 WINS: Higher accuracy AND more consistent!")
    elif diff < 2.4:
        print("V7.7 is more consistent across seasons")

    print()
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return r1, r2


if __name__ == "__main__":
    main()
