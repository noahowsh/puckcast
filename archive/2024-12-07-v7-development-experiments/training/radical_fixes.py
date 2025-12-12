#!/usr/bin/env python3
"""
Radical fixes - completely rethink the approach for 2025-26.

The fundamental issue: model learned home bias from 2024-25 (56.2% HW)
but 2025-26 has dropped to 52.3% HW.
"""

import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.pipeline import build_dataset

V81_FEATURES = [
    'elo_diff_pre', 'elo_expectation_home',
    'rolling_win_pct_10_diff', 'rolling_win_pct_5_diff', 'rolling_win_pct_3_diff',
    'rolling_goal_diff_10_diff', 'rolling_goal_diff_5_diff', 'rolling_goal_diff_3_diff',
    'rolling_xg_diff_10_diff', 'rolling_xg_diff_5_diff', 'rolling_xg_diff_3_diff',
    'rolling_corsi_10_diff', 'rolling_corsi_5_diff', 'rolling_corsi_3_diff',
    'rolling_fenwick_10_diff', 'rolling_fenwick_5_diff',
    'season_win_pct_diff', 'season_goal_diff_avg_diff',
    'season_xg_diff_avg_diff', 'season_shot_margin_diff',
    'rest_diff', 'is_b2b_home', 'is_b2b_away',
    'games_last_6d_home', 'games_last_3d_home',
    'rolling_save_pct_10_diff', 'rolling_save_pct_5_diff', 'rolling_save_pct_3_diff',
    'rolling_gsax_5_diff', 'rolling_gsax_10_diff',
    'goalie_trend_score_diff',
    'momentum_win_pct_diff', 'momentum_goal_diff_diff', 'momentum_xg_diff',
    'rolling_high_danger_shots_5_diff', 'rolling_high_danger_shots_10_diff',
    'shotsFor_roll_10_diff', 'rolling_faceoff_5_diff',
]


def main():
    print("=" * 90)
    print("RADICAL FIXES - UNDERSTANDING THE 2025-26 PROBLEM")
    print("=" * 90)

    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']
    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    games = games.sort_values('gameDate').copy()

    available = [f for f in V81_FEATURES if f in features.columns]

    # Focus on 2025-26
    mask_2526 = games['seasonId'] == '20252026'
    train_mask = games['seasonId'].isin(['20212022', '20222023', '20232024', '20242025'])

    X_train = features[train_mask][available].fillna(0)
    y_train = target[train_mask]
    X_test = features[mask_2526][available].fillna(0)
    y_test = target[mask_2526]
    games_test = games[mask_2526].copy()

    # Train baseline model
    model = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(C=0.01, max_iter=1000, random_state=42))
    ])
    model.fit(X_train, y_train)

    y_prob = model.predict_proba(X_test)[:, 1]
    games_test['y_prob'] = y_prob
    games_test['y_true'] = y_test.values

    print(f"\n📊 2025-26 Analysis:")
    print(f"   Games: {len(games_test)}")
    print(f"   Home win rate: {y_test.mean():.1%}")
    print(f"   Model home pick rate: {(y_prob >= 0.5).mean():.1%}")

    # What if we just used Elo alone?
    print("\n" + "=" * 90)
    print("TEST 1: ELO ONLY (no home advantage)")
    print("=" * 90)

    elo_only = ['elo_diff_pre']
    X_train_elo = features[train_mask][elo_only].fillna(0)
    X_test_elo = features[mask_2526][elo_only].fillna(0)

    model_elo = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(C=0.01, max_iter=1000, random_state=42))
    ])
    model_elo.fit(X_train_elo, y_train)
    y_prob_elo = model_elo.predict_proba(X_test_elo)[:, 1]

    acc_elo = accuracy_score(y_test, (y_prob_elo >= 0.5).astype(int))
    print(f"   Accuracy: {acc_elo:.1%}")
    print(f"   Home pick rate: {(y_prob_elo >= 0.5).mean():.1%}")

    # What if we removed home-correlated features?
    print("\n" + "=" * 90)
    print("TEST 2: ONLY DIFFERENTIAL FEATURES (no home-specific)")
    print("=" * 90)

    diff_features = [f for f in available if 'diff' in f.lower() and 'home' not in f.lower() and 'away' not in f.lower()]
    X_train_diff = features[train_mask][diff_features].fillna(0)
    X_test_diff = features[mask_2526][diff_features].fillna(0)

    model_diff = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(C=0.01, max_iter=1000, random_state=42))
    ])
    model_diff.fit(X_train_diff, y_train)
    y_prob_diff = model_diff.predict_proba(X_test_diff)[:, 1]

    acc_diff = accuracy_score(y_test, (y_prob_diff >= 0.5).astype(int))
    print(f"   Using {len(diff_features)} features")
    print(f"   Accuracy: {acc_diff:.1%}")
    print(f"   Home pick rate: {(y_prob_diff >= 0.5).mean():.1%}")

    # What's the theoretical maximum if we perfectly knew home advantage?
    print("\n" + "=" * 90)
    print("TEST 3: ORACLE - What's the best possible?")
    print("=" * 90)

    # If we knew home wins 52.3%, best strategy is pick home for strongest home teams
    # But with random model, we'd expect ~52.3% if always pick home, ~47.7% if always pick away

    # Let's see: if home wins 52.3% and we pick home 52.3% of the time (matching baseline)
    # We'd get: 0.523 * 0.523 + 0.477 * 0.477 = 0.274 + 0.228 = 0.50 (coin flip!)

    # The issue is that there's very little signal in who wins
    print(f"   If always pick home: {y_test.mean():.1%}")
    print(f"   If always pick away: {1-y_test.mean():.1%}")
    print(f"   Coin flip: 50.0%")

    # Check if Elo has predictive power on its own
    elo_values = features[mask_2526]['elo_diff_pre'].values
    games_test['elo_diff'] = elo_values

    # When Elo favors home (elo_diff > 0)
    home_favored = games_test[games_test['elo_diff'] > 0]
    away_favored = games_test[games_test['elo_diff'] <= 0]

    print(f"\n   When Elo favors home ({len(home_favored)} games):")
    print(f"      Home actually wins: {home_favored['y_true'].mean():.1%}")

    print(f"   When Elo favors away ({len(away_favored)} games):")
    print(f"      Home actually wins: {away_favored['y_true'].mean():.1%}")

    # What if we use Elo to pick and ignore home advantage?
    print("\n" + "=" * 90)
    print("TEST 4: PICK BETTER TEAM (ignore home/away)")
    print("=" * 90)

    # Pick home if elo_diff > 0 (home is better team)
    y_pred_elo_only = (elo_values > 0).astype(int)
    acc_elo_pick = accuracy_score(y_test, y_pred_elo_only)
    print(f"   Pick home if Elo favors home: {acc_elo_pick:.1%}")
    print(f"   Home pick rate: {(elo_values > 0).mean():.1%}")

    # What if we're more conservative - only pick home if strong Elo advantage?
    print("\n" + "=" * 90)
    print("TEST 5: CONSERVATIVE ELO PICKS")
    print("=" * 90)

    for threshold in [0, 25, 50, 75, 100]:
        y_pred_cons = (elo_values > threshold).astype(int)
        acc_cons = accuracy_score(y_test, y_pred_cons)
        hp_rate = (elo_values > threshold).mean()
        print(f"   Elo diff > {threshold:>3}: {acc_cons:.1%} accuracy, {hp_rate:.1%} home picks")

    # What about rolling features only (most recent form)?
    print("\n" + "=" * 90)
    print("TEST 6: RECENT FORM ONLY (rolling features)")
    print("=" * 90)

    rolling_features = [f for f in available if 'rolling' in f.lower() and 'diff' in f.lower()]
    X_train_roll = features[train_mask][rolling_features].fillna(0)
    X_test_roll = features[mask_2526][rolling_features].fillna(0)

    model_roll = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(C=0.01, max_iter=1000, random_state=42))
    ])
    model_roll.fit(X_train_roll, y_train)
    y_prob_roll = model_roll.predict_proba(X_test_roll)[:, 1]

    acc_roll = accuracy_score(y_test, (y_prob_roll >= 0.5).astype(int))
    print(f"   Using {len(rolling_features)} rolling features")
    print(f"   Accuracy: {acc_roll:.1%}")
    print(f"   Home pick rate: {(y_prob_roll >= 0.5).mean():.1%}")

    # What if we train ONLY on 2022-23 and 2023-24 (normal HW seasons)?
    print("\n" + "=" * 90)
    print("TEST 7: TRAIN ON NORMAL HW SEASONS ONLY (22-23, 23-24)")
    print("=" * 90)

    normal_mask = games['seasonId'].isin(['20222023', '20232024'])
    X_train_norm = features[normal_mask][available].fillna(0)
    y_train_norm = target[normal_mask]

    model_norm = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(C=0.01, max_iter=1000, random_state=42))
    ])
    model_norm.fit(X_train_norm, y_train_norm)
    y_prob_norm = model_norm.predict_proba(X_test)[:, 1]

    acc_norm = accuracy_score(y_test, (y_prob_norm >= 0.5).astype(int))
    print(f"   Training on {normal_mask.sum()} games (22-23 + 23-24)")
    print(f"   2025-26 Accuracy: {acc_norm:.1%}")
    print(f"   Home pick rate: {(y_prob_norm >= 0.5).mean():.1%}")

    # Summary
    print("\n" + "=" * 90)
    print("SUMMARY OF ALL APPROACHES")
    print("=" * 90)

    results = [
        ("Full V8.1 model", accuracy_score(y_test, (y_prob >= 0.5).astype(int)), (y_prob >= 0.5).mean()),
        ("Elo only", acc_elo, (y_prob_elo >= 0.5).mean()),
        ("Diff features only", acc_diff, (y_prob_diff >= 0.5).mean()),
        ("Pick if Elo > 0", acc_elo_pick, (elo_values > 0).mean()),
        ("Pick if Elo > 50", accuracy_score(y_test, (elo_values > 50).astype(int)), (elo_values > 50).mean()),
        ("Rolling features only", acc_roll, (y_prob_roll >= 0.5).mean()),
        ("Normal HW seasons", acc_norm, (y_prob_norm >= 0.5).mean()),
        ("Always pick home", y_test.mean(), 1.0),
        ("Always pick away", 1 - y_test.mean(), 0.0),
    ]

    print(f"\n{'Approach':<25} {'Accuracy':<12} {'Home Pick%':<12}")
    print("-" * 49)
    for name, acc, hp in sorted(results, key=lambda x: x[1], reverse=True):
        marker = "✅" if acc >= 0.55 else "⚠️" if acc >= 0.52 else "❌"
        print(f"{name:<25} {marker} {acc*100:.1f}%       {hp*100:.1f}%")

    print("\n" + "=" * 90)
    print("CONCLUSION")
    print("=" * 90)
    print("""
The fundamental issue is that 2025-26 has very weak home advantage (52.3%), making
it very hard to predict. Even simple approaches like "pick better Elo team" only
get ~55%.

Key insight: The model's skill comes from identifying WHICH home teams will win,
not from knowing that home teams have an advantage. When home advantage drops,
the model's home-favoring bias becomes a liability.

BEST APPROACHES:
1. Train on normal HW seasons only (22-23, 23-24)
2. Use Elo-based conservative picks (only pick home if Elo strongly favors)
3. Reduce home pick rate to match actual home win rate (~52%)
""")


if __name__ == '__main__':
    main()
