#!/usr/bin/env python3
"""
Compare V7.6 model performance on 2023-24 and 2024-25 seasons.

This script validates whether V7.6 performance generalizes to the new season.
"""

import sys
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.situational_features import add_situational_features


def add_v75_features(df):
    """Add V7.5 ratio/interaction features."""
    g = df.copy()
    if 'rolling_goal_diff_5_diff' in g.columns:
        if 'shotsFor_roll_5_diff' in g.columns:
            shots = g['shotsFor_roll_5_diff'].replace(0, np.nan)
            g['ratio_goals_per_shot_5'] = (g['rolling_goal_diff_5_diff'] / shots).fillna(0).clip(-1, 1)
        if 'shotsFor_roll_10_diff' in g.columns:
            shots = g['shotsFor_roll_10_diff'].replace(0, np.nan)
            g['ratio_goals_per_shot_10'] = (g['rolling_goal_diff_10_diff'] / shots).fillna(0).clip(-1, 1)
    if 'rolling_goal_diff_5_diff' in g.columns and 'rolling_xg_diff_5_diff' in g.columns:
        xg = g['rolling_xg_diff_5_diff'].replace(0, np.nan)
        g['ratio_goals_vs_xg_5'] = (g['rolling_goal_diff_5_diff'] / xg).clip(-3, 3).fillna(0)
    if 'rolling_goal_diff_10_diff' in g.columns and 'rolling_xg_diff_10_diff' in g.columns:
        xg = g['rolling_xg_diff_10_diff'].replace(0, np.nan)
        g['ratio_goals_vs_xg_10'] = (g['rolling_goal_diff_10_diff'] / xg).clip(-3, 3).fillna(0)
    if 'rolling_high_danger_shots_5_diff' in g.columns and 'shotsFor_roll_5_diff' in g.columns:
        shots = g['shotsFor_roll_5_diff'].replace(0, np.nan)
        g['ratio_hd_shots_5'] = (g['rolling_high_danger_shots_5_diff'] / shots).fillna(0).clip(-1, 1)
    if 'rolling_xg_for_5_diff' in g.columns:
        g['luck_indicator_5'] = g['rolling_goal_diff_5_diff'] - g['rolling_xg_diff_5_diff']
    if 'rolling_goal_diff_3_diff' in g.columns and 'rolling_goal_diff_10_diff' in g.columns:
        g['consistency_gd'] = abs(g['rolling_goal_diff_3_diff'] - g['rolling_goal_diff_10_diff'])
    if 'rolling_goal_diff_5_diff' in g.columns and 'rolling_win_pct_5_diff' in g.columns:
        g['dominance_score'] = g['rolling_win_pct_5_diff'].clip(-1, 1) * g['rolling_goal_diff_5_diff'].clip(-3, 3)
    return g


def train_v76_model(X_train, y_train, X_test, n_features=59):
    """Train V7.6 model using coefficient-based feature selection."""
    # Scale
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    # Get coefficients from training data ONLY
    lr_full = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr_full.fit(X_train_scaled, y_train)

    # Select top features by |coefficient|
    coef_importance = np.abs(lr_full.coef_[0])
    top_idx = np.argsort(coef_importance)[::-1][:n_features]

    # Train final model on selected features
    X_train_sub = X_train_scaled[:, top_idx]
    X_test_sub = X_test_scaled[:, top_idx]

    lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr.fit(X_train_sub, y_train)

    proba = lr.predict_proba(X_test_sub)[:, 1]
    return proba, top_idx


def run_validation(all_features, all_games, all_target, train_seasons, test_season):
    """Run forward validation: train on train_seasons, test on test_season."""
    train_mask = all_games['seasonId'].isin(train_seasons)
    test_mask = all_games['seasonId'] == test_season

    X_train = all_features[train_mask].values
    X_test = all_features[test_mask].values
    y_train = all_target[train_mask].values
    y_test = all_target[test_mask].values

    proba, top_idx = train_v76_model(X_train, y_train, X_test, n_features=59)
    y_pred = (proba >= 0.5).astype(int)

    acc = accuracy_score(y_test, y_pred)
    auc = roc_auc_score(y_test, proba)
    ll = log_loss(y_test, proba)
    home_baseline = y_test.mean()

    return {
        'test_season': test_season,
        'train_seasons': train_seasons,
        'train_games': len(y_train),
        'test_games': len(y_test),
        'accuracy': acc,
        'auc': auc,
        'log_loss': ll,
        'home_baseline': home_baseline
    }


def main():
    print("=" * 70)
    print("V7.6 MODEL COMPARISON: 2023-24 vs 2024-25")
    print("=" * 70)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Build dataset with all 4 seasons
    print("Building dataset with all seasons...")
    all_seasons = ['20212022', '20222023', '20232024', '20242025']
    dataset = build_dataset(all_seasons)

    print(f"Total games: {len(dataset.games)}")
    print(f"Total features: {dataset.features.shape[1]}")
    print()

    # Add V7.5 features
    games_df = dataset.games.copy()
    features_df = dataset.features.copy()
    target = dataset.target.copy()

    # Add seasonId and gameDate for filtering
    combined = pd.concat([
        games_df[['seasonId', 'gameDate']].reset_index(drop=True),
        features_df.reset_index(drop=True),
        target.reset_index(drop=True).to_frame('_target')
    ], axis=1)

    # Add V7.5 features
    combined = add_v75_features(combined)

    # Prepare data
    all_games = combined[['seasonId', 'gameDate']]
    all_target = combined['_target']
    all_features = combined.drop(columns=['seasonId', 'gameDate', '_target']).fillna(0)

    print(f"Features after V7.5: {all_features.shape[1]}")
    print()

    # Games per season
    for season in all_seasons:
        n = (all_games['seasonId'] == season).sum()
        print(f"  {season}: {n} games")
    print()

    results = []

    # Test 1: Train on 21-22 + 22-23, test on 23-24 (original V7.6)
    print("-" * 70)
    print("TEST 1: Train 21-22 + 22-23 -> Test 23-24")
    r1 = run_validation(all_features, all_games, all_target,
                        ['20212022', '20222023'], '20232024')
    print(f"  Train games: {r1['train_games']}")
    print(f"  Test games: {r1['test_games']}")
    print(f"  Accuracy: {r1['accuracy']:.4f} ({r1['accuracy']*100:.2f}%)")
    print(f"  AUC: {r1['auc']:.4f}")
    print(f"  Home baseline: {r1['home_baseline']:.4f} ({r1['home_baseline']*100:.2f}%)")
    results.append(r1)

    # Test 2: Train on 22-23 + 23-24, test on 24-25 (NEW)
    print("-" * 70)
    print("TEST 2: Train 22-23 + 23-24 -> Test 24-25")
    r2 = run_validation(all_features, all_games, all_target,
                        ['20222023', '20232024'], '20242025')
    print(f"  Train games: {r2['train_games']}")
    print(f"  Test games: {r2['test_games']}")
    print(f"  Accuracy: {r2['accuracy']:.4f} ({r2['accuracy']*100:.2f}%)")
    print(f"  AUC: {r2['auc']:.4f}")
    print(f"  Home baseline: {r2['home_baseline']:.4f} ({r2['home_baseline']*100:.2f}%)")
    results.append(r2)

    # Test 3: Train on ALL prior seasons, test on 24-25
    print("-" * 70)
    print("TEST 3: Train 21-22 + 22-23 + 23-24 -> Test 24-25")
    r3 = run_validation(all_features, all_games, all_target,
                        ['20212022', '20222023', '20232024'], '20242025')
    print(f"  Train games: {r3['train_games']}")
    print(f"  Test games: {r3['test_games']}")
    print(f"  Accuracy: {r3['accuracy']:.4f} ({r3['accuracy']*100:.2f}%)")
    print(f"  AUC: {r3['auc']:.4f}")
    print(f"  Home baseline: {r3['home_baseline']:.4f} ({r3['home_baseline']*100:.2f}%)")
    results.append(r3)

    # Summary
    print()
    print("=" * 70)
    print("SUMMARY: V7.6 Performance Comparison")
    print("=" * 70)
    print()
    print(f"{'Test Season':<12} {'Training Data':<28} {'Accuracy':<12} {'AUC':<10} {'Baseline'}")
    print("-" * 70)
    for r in results:
        train_str = ' + '.join([s[:4] + '-' + s[4:6] for s in r['train_seasons']])
        test_str = r['test_season'][:4] + '-' + r['test_season'][4:6]
        print(f"{test_str:<12} {train_str:<28} {r['accuracy']*100:>6.2f}%      {r['auc']:.4f}    {r['home_baseline']*100:.2f}%")

    print()
    print("=" * 70)
    print("KEY FINDINGS")
    print("=" * 70)

    diff = r2['accuracy'] - r1['accuracy']
    print(f"\n2023-24 test accuracy: {r1['accuracy']*100:.2f}%")
    print(f"2024-25 test accuracy: {r2['accuracy']*100:.2f}%")
    print(f"Difference: {diff*100:+.2f}pp")
    print()

    # Compare with 3 seasons of training
    diff3 = r3['accuracy'] - r2['accuracy']
    print(f"With 3 seasons training (21-24): {r3['accuracy']*100:.2f}% ({diff3*100:+.2f}pp)")
    print()

    if abs(diff) < 0.015:
        print("CONCLUSION: Model performance is CONSISTENT across seasons")
        print("            V7.6 generalizes well to new data")
    elif diff > 0:
        print(f"CONCLUSION: Model performs BETTER on 2024-25 (+{diff*100:.2f}pp)")
        print("            This could indicate the model is improving with more recent patterns")
    else:
        print(f"CONCLUSION: Model performs WORSE on 2024-25 ({diff*100:.2f}pp)")
        print("            This could indicate season-specific variance")

    print()
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
