#!/usr/bin/env python3
"""
V7.9: Enhanced Stable Model with Feature Engineering

This model builds on V7.7/V7.8 with engineered features that improve
accuracy while maintaining excellent cross-season consistency.

Key improvements:
- 42 total features (36 base + 6 engineered)
- Momentum acceleration features (short vs long term trends)
- Interaction features (Elo x Rest, xG x Possession)
- Temporal features (Saturday effect)

VALIDATED RESULTS:
  23-24: 60.24% (trained on 21-22 + 22-23)
  24-25: 60.21% (trained on 22-23 + 23-24)
  Average: 60.23%, Variance: 0.0pp

Comparison:
  V7.6: 59.79% avg, 2.4pp variance (team dummies overfit)
  V7.7: 59.86% avg, 0.7pp variance (stable features only)
  V7.8: 59.88% avg, 0.6pp variance (expanded features)
  V7.9: 60.23% avg, 0.0pp variance (+ engineered features)

Usage:
    python training/train_v7_9_enhanced.py
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


# V7.9 Base Features (36 features)
V79_BASE_FEATURES = [
    # Elo ratings
    'elo_diff_pre', 'elo_expectation_home',

    # Rolling win percentage
    'rolling_win_pct_10_diff', 'rolling_win_pct_5_diff', 'rolling_win_pct_3_diff',

    # Rolling goal differential
    'rolling_goal_diff_10_diff', 'rolling_goal_diff_5_diff', 'rolling_goal_diff_3_diff',

    # Rolling xG differential
    'rolling_xg_diff_10_diff', 'rolling_xg_diff_5_diff', 'rolling_xg_diff_3_diff',

    # Possession metrics
    'rolling_corsi_10_diff', 'rolling_corsi_5_diff', 'rolling_corsi_3_diff',
    'rolling_fenwick_10_diff', 'rolling_fenwick_5_diff',

    # Season-level stats
    'season_win_pct_diff', 'season_goal_diff_avg_diff',
    'season_xg_diff_avg_diff', 'season_shot_margin_diff',

    # Rest and schedule
    'rest_diff', 'is_b2b_home', 'is_b2b_away',
    'games_last_6d_home',

    # Goaltending
    'rolling_save_pct_10_diff', 'rolling_save_pct_5_diff', 'rolling_save_pct_3_diff',
    'rolling_gsax_5_diff', 'rolling_gsax_10_diff',
    'goalie_rest_days_diff', 'goalie_trend_score_diff',

    # Momentum
    'momentum_win_pct_diff', 'momentum_goal_diff_diff', 'momentum_xg_diff',

    # High danger shots
    'rolling_high_danger_shots_5_diff', 'rolling_high_danger_shots_10_diff',
]


def create_engineered_features(features_df, games_df):
    """Create engineered features for V7.9."""
    eng = pd.DataFrame(index=features_df.index)

    # 1. Momentum acceleration (short vs long term)
    eng['goal_momentum_accel'] = (
        features_df['rolling_goal_diff_3_diff'] -
        features_df['rolling_goal_diff_10_diff']
    )
    eng['xg_momentum_accel'] = (
        features_df['rolling_xg_diff_3_diff'] -
        features_df['rolling_xg_diff_10_diff']
    )

    # 2. Interaction features
    eng['xg_x_corsi_10'] = (
        features_df['rolling_xg_diff_10_diff'] *
        features_df['rolling_corsi_10_diff']
    )
    eng['elo_x_rest'] = (
        features_df['elo_diff_pre'] *
        features_df['rest_diff']
    )

    # 3. Composite dominance score
    eng['dominance'] = (
        features_df['elo_expectation_home'] * 0.4 +
        features_df['rolling_win_pct_10_diff'].clip(-0.5, 0.5) + 0.5 * 0.3 +
        (features_df['rolling_xg_diff_10_diff'].clip(-1, 1) + 1) / 2 * 0.3
    )

    # 4. Temporal feature
    games_df = games_df.copy()
    games_df['gameDate'] = pd.to_datetime(games_df['gameDate'])
    eng['is_saturday'] = (games_df['gameDate'].dt.dayofweek == 5).astype(int).values

    return eng


def train_v79_model(train_seasons, test_season=None, verbose=True):
    """Train V7.9 model on specified seasons."""

    if verbose:
        print(f"Loading data for seasons: {train_seasons}")

    all_seasons = train_seasons.copy()
    if test_season and test_season not in all_seasons:
        all_seasons.append(test_season)

    dataset = build_dataset(all_seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    # Get base features
    base_features = features[[n for n in V79_BASE_FEATURES if n in features.columns]].copy()

    # Create engineered features
    eng_features = create_engineered_features(features, games)

    # Combine
    all_features = pd.concat([base_features, eng_features], axis=1)

    if verbose:
        print(f"Using {len(all_features.columns)} features ({len(base_features.columns)} base + {len(eng_features.columns)} engineered)")

    # Split data
    train_mask = games['seasonId'].isin(train_seasons)

    X_train = all_features[train_mask].values
    y_train = target[train_mask].values

    # Scale and train
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = LogisticRegression(C=0.005, max_iter=1000, random_state=42)
    model.fit(X_train_scaled, y_train)

    results = {
        'model': model,
        'scaler': scaler,
        'feature_names': list(all_features.columns),
        'train_games': len(y_train)
    }

    # Evaluate on test season if provided
    if test_season:
        test_mask = games['seasonId'] == test_season
        X_test = all_features[test_mask].values
        y_test = target[test_mask].values

        X_test_scaled = scaler.transform(X_test)
        proba = model.predict_proba(X_test_scaled)[:, 1]
        pred = (proba >= 0.5).astype(int)

        results['accuracy'] = accuracy_score(y_test, pred)
        results['auc'] = roc_auc_score(y_test, proba)
        results['log_loss'] = log_loss(y_test, proba)
        results['home_baseline'] = y_test.mean()
        results['test_games'] = len(y_test)
        results['predictions'] = proba

    return results


def main():
    print("=" * 70)
    print("V7.9: ENHANCED STABLE MODEL WITH FEATURE ENGINEERING")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("BASE FEATURES (36):")
    for i, f in enumerate(V79_BASE_FEATURES, 1):
        print(f"  {i:2d}. {f}")
    print()

    print("ENGINEERED FEATURES (6):")
    print("  - goal_momentum_accel (3-game vs 10-game goal diff trend)")
    print("  - xg_momentum_accel (3-game vs 10-game xG diff trend)")
    print("  - xg_x_corsi_10 (xG x possession interaction)")
    print("  - elo_x_rest (Elo x rest advantage interaction)")
    print("  - dominance (composite quality score)")
    print("  - is_saturday (weekend effect)")
    print()

    print("=" * 70)
    print("FORWARD VALIDATION")
    print("=" * 70)
    print()

    # Test on 2023-24
    print("Test 1: Train 21-22 + 22-23 -> Test 23-24")
    r1 = train_v79_model(['20212022', '20222023'], '20232024')
    print(f"  Accuracy: {r1['accuracy']*100:.2f}%")
    print(f"  Lift over baseline: +{(r1['accuracy'] - r1['home_baseline'])*100:.1f}pp")
    print(f"  AUC: {r1['auc']:.4f}")
    print()

    # Test on 2024-25
    print("Test 2: Train 22-23 + 23-24 -> Test 24-25")
    r2 = train_v79_model(['20222023', '20232024'], '20242025')
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
    print(f"Season Variance: {diff*100:.2f}pp")
    print()

    print("Model Progression:")
    print("  V7.6: 59.79% avg, 2.4pp variance (team dummies overfit)")
    print("  V7.7: 59.86% avg, 0.7pp variance (stable features)")
    print("  V7.8: 59.88% avg, 0.6pp variance (expanded features)")
    print(f"  V7.9: {avg*100:.2f}% avg, {diff*100:.1f}pp variance (+ engineered)")
    print()

    # Confidence breakdown
    print("Confidence Breakdown (24-25):")
    proba = r2['predictions']
    y_test = np.array([1 if p >= 0.5 else 0 for p in proba])  # predictions
    conf = np.abs(proba - 0.5) * 100

    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    return r1, r2


if __name__ == "__main__":
    main()
