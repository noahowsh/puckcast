#!/usr/bin/env python3
"""
Expanded Training Data Comparison

Tests all model versions with varying amounts of training data:
- 3 seasons (baseline)
- 4 seasons
- 5 seasons
- 6 seasons
- 7 seasons (all available historical data)

Uses historical data from 2017-18 through 2024-25.

Usage:
    python training/compare_expanded_training.py
"""

import sys
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.situational_features import add_situational_features
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities
from nhl_prediction.train import compute_season_weights


# All available seasons (chronological order)
ALL_SEASONS = [
    '20172018',  # 2017-18
    '20182019',  # 2018-19
    '20192020',  # 2019-20 (COVID-shortened)
    '20202021',  # 2020-21 (COVID 56-game)
    '20212022',  # 2021-22
    '20222023',  # 2022-23
    '20232024',  # 2023-24
    '20242025',  # 2024-25 (current)
]

# Test seasons (we'll validate on these)
TEST_SEASONS = ['20232024', '20242025']

# V7.7 Stable Features (23 features - NO team dummies)
V77_FEATURES = [
    'elo_diff_pre', 'elo_expectation_home',
    'rolling_win_pct_10_diff', 'rolling_win_pct_5_diff', 'rolling_win_pct_3_diff',
    'rolling_goal_diff_10_diff', 'rolling_goal_diff_5_diff',
    'rolling_xg_diff_10_diff', 'rolling_xg_diff_5_diff',
    'rolling_corsi_10_diff', 'rolling_corsi_5_diff',
    'rolling_fenwick_10_diff', 'rolling_fenwick_5_diff',
    'season_win_pct_diff', 'season_goal_diff_avg_diff', 'season_xg_diff_avg_diff',
    'rest_diff', 'is_b2b_home', 'is_b2b_away',
    'rolling_save_pct_10_diff', 'rolling_save_pct_5_diff',
    'momentum_win_pct_diff', 'momentum_goal_diff_diff',
]

# V7.9 Base Features (36 features)
V79_BASE_FEATURES = [
    'elo_diff_pre', 'elo_expectation_home',
    'rolling_win_pct_10_diff', 'rolling_win_pct_5_diff', 'rolling_win_pct_3_diff',
    'rolling_goal_diff_10_diff', 'rolling_goal_diff_5_diff', 'rolling_goal_diff_3_diff',
    'rolling_xg_diff_10_diff', 'rolling_xg_diff_5_diff', 'rolling_xg_diff_3_diff',
    'rolling_corsi_10_diff', 'rolling_corsi_5_diff', 'rolling_corsi_3_diff',
    'rolling_fenwick_10_diff', 'rolling_fenwick_5_diff',
    'season_win_pct_diff', 'season_goal_diff_avg_diff',
    'season_xg_diff_avg_diff', 'season_shot_margin_diff',
    'rest_diff', 'is_b2b_home', 'is_b2b_away',
    'games_last_6d_home',
    'rolling_save_pct_10_diff', 'rolling_save_pct_5_diff', 'rolling_save_pct_3_diff',
    'rolling_gsax_5_diff', 'rolling_gsax_10_diff',
    'goalie_rest_days_diff', 'goalie_trend_score_diff',
    'momentum_win_pct_diff', 'momentum_goal_diff_diff', 'momentum_xg_diff',
    'rolling_high_danger_shots_5_diff', 'rolling_high_danger_shots_10_diff',
]


def create_v79_engineered_features(features_df, games_df):
    """Create V7.9 engineered features."""
    eng = pd.DataFrame(index=features_df.index)

    eng['goal_momentum_accel'] = (
        features_df['rolling_goal_diff_3_diff'] -
        features_df['rolling_goal_diff_10_diff']
    )
    eng['xg_momentum_accel'] = (
        features_df['rolling_xg_diff_3_diff'] -
        features_df['rolling_xg_diff_10_diff']
    )
    eng['xg_x_corsi_10'] = (
        features_df['rolling_xg_diff_10_diff'] *
        features_df['rolling_corsi_10_diff']
    )
    eng['elo_x_rest'] = (
        features_df['elo_diff_pre'] *
        features_df['rest_diff']
    )
    eng['dominance'] = (
        features_df['elo_expectation_home'] * 0.4 +
        features_df['rolling_win_pct_10_diff'].clip(-0.5, 0.5) + 0.5 * 0.3 +
        (features_df['rolling_xg_diff_10_diff'].clip(-1, 1) + 1) / 2 * 0.3
    )

    games_df = games_df.copy()
    games_df['gameDate'] = pd.to_datetime(games_df['gameDate'])
    eng['is_saturday'] = (games_df['gameDate'].dt.dayofweek == 5).astype(int).values

    return eng


def test_v73_situational(train_seasons, test_season, all_data):
    """Test V7.3 with situational features."""
    games, features, target = all_data

    # Add situational features
    games_sit = add_situational_features(games)
    sit_cols = [c for c in games_sit.columns if any(k in c for k in
        ['fatigue', 'trailing', 'travel', 'divisional', 'break'])]

    features_full = pd.concat([features, games_sit[sit_cols]], axis=1).fillna(0)

    train_mask = games['seasonId'].isin(train_seasons)
    test_mask = games['seasonId'] == test_season

    X_train, y_train = features_full[train_mask], target[train_mask]
    X_test, y_test = features_full[test_mask], target[test_mask]

    weights = compute_season_weights(games[train_mask], train_seasons, decay_factor=1.0)

    model = create_baseline_model(C=0.05)
    model = fit_model(model, X_train, y_train, pd.Series(True, index=X_train.index), sample_weight=weights)

    proba = predict_probabilities(model, X_test, pd.Series(True, index=X_test.index))
    acc = accuracy_score(y_test, (proba >= 0.5).astype(int))

    return acc


def test_v77_stable(train_seasons, test_season, all_data):
    """Test V7.7 stable features."""
    games, features, target = all_data

    v77_cols = [c for c in V77_FEATURES if c in features.columns]
    X = features[v77_cols].values

    train_mask = games['seasonId'].isin(train_seasons)
    test_mask = games['seasonId'] == test_season

    X_train = X[train_mask]
    X_test = X[test_mask]
    y_train = target[train_mask].values
    y_test = target[test_mask].values

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr.fit(X_train_s, y_train)
    pred = (lr.predict_proba(X_test_s)[:, 1] >= 0.5).astype(int)

    return accuracy_score(y_test, pred)


def test_v79_enhanced(train_seasons, test_season, all_data, v79_full):
    """Test V7.9 enhanced features."""
    games, _, target = all_data

    train_mask = games['seasonId'].isin(train_seasons)
    test_mask = games['seasonId'] == test_season

    X_train = v79_full[train_mask].values
    X_test = v79_full[test_mask].values
    y_train = target[train_mask].values
    y_test = target[test_mask].values

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    lr = LogisticRegression(C=0.005, max_iter=1000, random_state=42)
    lr.fit(X_train_s, y_train)
    pred = (lr.predict_proba(X_test_s)[:, 1] >= 0.5).astype(int)

    return accuracy_score(y_test, pred)


def test_v76_team_dummies(train_seasons, test_season, all_data):
    """Test V7.6 with team dummies and feature selection."""
    games, features, target = all_data

    train_mask = games['seasonId'].isin(train_seasons)
    test_mask = games['seasonId'] == test_season

    X_train = features[train_mask].values
    X_test = features[test_mask].values
    y_train = target[train_mask].values
    y_test = target[test_mask].values

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # Feature selection to top 59
    lr_full = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr_full.fit(X_train_s, y_train)
    top_idx = np.argsort(np.abs(lr_full.coef_[0]))[::-1][:59]
    X_train_s = X_train_s[:, top_idx]
    X_test_s = X_test_s[:, top_idx]

    lr = LogisticRegression(C=0.01, max_iter=1000, random_state=42)
    lr.fit(X_train_s, y_train)
    pred = (lr.predict_proba(X_test_s)[:, 1] >= 0.5).astype(int)

    return accuracy_score(y_test, pred)


def main():
    print("=" * 80)
    print("EXPANDED TRAINING DATA COMPARISON")
    print("=" * 80)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load all data
    print("Loading data for all seasons...")
    dataset = build_dataset(ALL_SEASONS)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    all_data = (games, features, target)

    # Create V7.9 features
    v79_base = features[[n for n in V79_BASE_FEATURES if n in features.columns]].copy()
    v79_eng = create_v79_engineered_features(features, games)
    v79_full = pd.concat([v79_base, v79_eng], axis=1)

    # Season counts
    print("\nData Summary:")
    print("-" * 40)
    for season in ALL_SEASONS:
        count = (games['seasonId'] == season).sum()
        season_fmt = f"{season[:4]}-{season[4:6]}"
        print(f"  {season_fmt}: {count:,} games")
    print(f"  TOTAL: {len(games):,} games")
    print()

    # Training configurations to test
    # For test on 2023-24: train on seasons before it
    # For test on 2024-25: train on seasons before it
    configs = {
        '3 seasons': {
            '20232024': ['20202021', '20212022', '20222023'],
            '20242025': ['20212022', '20222023', '20232024'],
        },
        '4 seasons': {
            '20232024': ['20192020', '20202021', '20212022', '20222023'],
            '20242025': ['20202021', '20212022', '20222023', '20232024'],
        },
        '5 seasons': {
            '20232024': ['20182019', '20192020', '20202021', '20212022', '20222023'],
            '20242025': ['20192020', '20202021', '20212022', '20222023', '20232024'],
        },
        '6 seasons': {
            '20232024': ['20172018', '20182019', '20192020', '20202021', '20212022', '20222023'],
            '20242025': ['20182019', '20192020', '20202021', '20212022', '20222023', '20232024'],
        },
        '7 seasons': {
            '20232024': ['20172018', '20182019', '20192020', '20202021', '20212022', '20222023'],
            '20242025': ['20172018', '20182019', '20192020', '20202021', '20212022', '20222023', '20232024'],
        },
    }

    models = [
        ('V7.3 (situational)', test_v73_situational),
        ('V7.6 (team dummies)', test_v76_team_dummies),
        ('V7.7 (stable)', test_v77_stable),
        ('V7.9 (enhanced)', None),  # Special handling
    ]

    # Results storage
    results = []

    print("=" * 80)
    print("TESTING ALL CONFIGURATIONS")
    print("=" * 80)

    for config_name, train_config in configs.items():
        print(f"\n>>> Training with {config_name}")
        train_games_2324 = sum((games['seasonId'] == s).sum() for s in train_config['20232024'])
        train_games_2425 = sum((games['seasonId'] == s).sum() for s in train_config['20242025'])
        print(f"    Training games: ~{train_games_2324:,} (for 23-24 test), ~{train_games_2425:,} (for 24-25 test)")

        for model_name, test_fn in models:
            try:
                if model_name == 'V7.9 (enhanced)':
                    acc_2324 = test_v79_enhanced(train_config['20232024'], '20232024', all_data, v79_full)
                    acc_2425 = test_v79_enhanced(train_config['20242025'], '20242025', all_data, v79_full)
                else:
                    acc_2324 = test_fn(train_config['20232024'], '20232024', all_data)
                    acc_2425 = test_fn(train_config['20242025'], '20242025', all_data)

                avg = (acc_2324 + acc_2425) / 2
                var = abs(acc_2324 - acc_2425)

                results.append({
                    'config': config_name,
                    'model': model_name,
                    'acc_2324': acc_2324,
                    'acc_2425': acc_2425,
                    'avg': avg,
                    'variance': var,
                })

                print(f"    {model_name}: 23-24={acc_2324*100:.2f}%, 24-25={acc_2425*100:.2f}%, avg={avg*100:.2f}%")
            except Exception as e:
                print(f"    {model_name}: ERROR - {e}")

    # Summary tables
    print("\n" + "=" * 80)
    print("SUMMARY RESULTS")
    print("=" * 80)

    # By model
    print("\n--- Results by Model ---")
    print(f"{'Model':<25} {'Config':<12} {'23-24':>8} {'24-25':>8} {'Avg':>8} {'Var':>6}")
    print("-" * 75)

    for model_name in [m[0] for m in models]:
        model_results = [r for r in results if r['model'] == model_name]
        for r in model_results:
            print(f"{r['model']:<25} {r['config']:<12} {r['acc_2324']*100:>7.2f}% {r['acc_2425']*100:>7.2f}% {r['avg']*100:>7.2f}% {r['variance']*100:>5.1f}%")
        if model_results:
            best = max(model_results, key=lambda x: x['avg'])
            print(f"  └─ Best: {best['config']} at {best['avg']*100:.2f}% avg")
        print()

    # Best overall
    print("\n--- Best Configurations ---")
    best_overall = max(results, key=lambda x: x['avg'])
    most_consistent = min(results, key=lambda x: x['variance'])

    print(f"Highest Average Accuracy: {best_overall['model']} with {best_overall['config']}")
    print(f"  → 23-24: {best_overall['acc_2324']*100:.2f}%, 24-25: {best_overall['acc_2425']*100:.2f}%, Avg: {best_overall['avg']*100:.2f}%")
    print()
    print(f"Most Consistent: {most_consistent['model']} with {most_consistent['config']}")
    print(f"  → Variance: {most_consistent['variance']*100:.1f}pp")

    # Does more data help?
    print("\n--- Does More Training Data Help? ---")
    for model_name in [m[0] for m in models]:
        model_results = [r for r in results if r['model'] == model_name]
        if len(model_results) >= 2:
            min_data = min(model_results, key=lambda x: int(x['config'].split()[0]))
            max_data = max(model_results, key=lambda x: int(x['config'].split()[0]))
            diff = max_data['avg'] - min_data['avg']
            direction = "↑" if diff > 0.001 else ("↓" if diff < -0.001 else "→")
            print(f"  {model_name}: {min_data['avg']*100:.2f}% ({min_data['config']}) {direction} {max_data['avg']*100:.2f}% ({max_data['config']}) [{diff*100:+.2f}pp]")

    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)
    print()
    print("Based on the expanded training data tests:")
    print(f"  • Best overall: {best_overall['model']} with {best_overall['config']}")
    print(f"  • Average accuracy: {best_overall['avg']*100:.2f}%")
    print()


if __name__ == "__main__":
    main()
