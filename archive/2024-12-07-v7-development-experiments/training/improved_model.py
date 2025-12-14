#!/usr/bin/env python3
"""
Improved Model - Focus on Consistent Features

Based on analysis:
1. Elo is broken in 2025-26 (correlation dropped from 0.25 to 0.05)
2. Possession features are most consistent (1.9pp std)
3. Rolling Win % has high variance (3.3pp std) - unreliable

Strategy:
- Weight features by their consistency across seasons
- De-emphasize Elo when recent correlation is weak
- Focus on possession-based features
"""

import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, log_loss
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.pipeline import build_dataset

# Features grouped by consistency (low variance = good)
CONSISTENT_FEATURES = [
    # Possession (1.9pp std) - BEST consistency, works in 2025-26
    'rolling_corsi_10_diff', 'rolling_corsi_5_diff', 'rolling_corsi_3_diff',
    'rolling_fenwick_10_diff', 'rolling_fenwick_5_diff',

    # Rest/Schedule (1.4pp std) - Most consistent
    'rest_diff', 'is_b2b_home', 'is_b2b_away',
    'games_last_6d_home', 'games_last_3d_home',

    # Goaltending (1.5pp std)
    'rolling_save_pct_10_diff', 'rolling_save_pct_5_diff', 'rolling_save_pct_3_diff',
    'rolling_gsax_5_diff', 'rolling_gsax_10_diff',
    'goalie_trend_score_diff',
]

# High variance features - use cautiously
HIGH_VARIANCE_FEATURES = [
    # Elo (3.6pp std) - broken in 2025-26
    'elo_diff_pre', 'elo_expectation_home',

    # Season Stats (3.3pp std)
    'season_win_pct_diff', 'season_goal_diff_avg_diff',
    'season_xg_diff_avg_diff', 'season_shot_margin_diff',

    # Rolling Win % (3.3pp std)
    'rolling_win_pct_10_diff', 'rolling_win_pct_5_diff', 'rolling_win_pct_3_diff',
]

# Medium variance - useful but not great
MEDIUM_VARIANCE_FEATURES = [
    # Rolling xG (2.7pp std)
    'rolling_xg_diff_10_diff', 'rolling_xg_diff_5_diff', 'rolling_xg_diff_3_diff',

    # Rolling Goals (2.8pp std)
    'rolling_goal_diff_10_diff', 'rolling_goal_diff_5_diff', 'rolling_goal_diff_3_diff',

    # Shots (2.7pp std)
    'rolling_high_danger_shots_5_diff', 'rolling_high_danger_shots_10_diff',
    'shotsFor_roll_10_diff', 'rolling_faceoff_5_diff',

    # Momentum (1.7pp std)
    'momentum_win_pct_diff', 'momentum_goal_diff_diff', 'momentum_xg_diff',
]

ALL_V81 = CONSISTENT_FEATURES + MEDIUM_VARIANCE_FEATURES + HIGH_VARIANCE_FEATURES


def calculate_elo_reliability(features, target, games, lookback=100):
    """Calculate recent Elo reliability based on correlation."""
    games = games.sort_values('gameDate').copy()

    # Rolling correlation of Elo with outcomes
    elo_vals = features['elo_diff_pre'].values
    outcomes = target.values

    correlations = []
    for i in range(len(games)):
        start_idx = max(0, i - lookback)
        if i - start_idx < 50:  # Need at least 50 games
            correlations.append(0.2)  # Default moderate reliability
        else:
            window_elo = elo_vals[start_idx:i]
            window_out = outcomes[start_idx:i]
            if np.std(window_elo) > 0:
                corr = np.corrcoef(window_elo, window_out)[0, 1]
                correlations.append(max(0, corr))  # Only positive correlations count
            else:
                correlations.append(0.2)

    games['elo_reliability'] = correlations
    return games


def test_model(features, target, games, feature_list, name, C=0.01, use_elo_weighting=False):
    """Test a model configuration."""
    results = []
    unique_seasons = sorted(games['seasonId'].unique())

    for test_season in unique_seasons:
        train_seasons = [s for s in unique_seasons if s != test_season]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        avail_features = [f for f in feature_list if f in features.columns]
        X_train = features[train_mask][avail_features].fillna(0)
        y_train = target[train_mask]
        X_test = features[test_mask][avail_features].fillna(0)
        y_test = target[test_mask]

        if len(X_train) == 0 or len(X_test) == 0:
            continue

        model = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(C=C, max_iter=1000, random_state=42))
        ])
        model.fit(X_train, y_train)

        y_prob = model.predict_proba(X_test)[:, 1]
        y_pred = (y_prob >= 0.5).astype(int)

        acc = accuracy_score(y_test, y_pred)
        baseline = y_test.mean()
        home_pick = (y_prob >= 0.5).mean()

        results.append({
            'season': test_season,
            'accuracy': acc,
            'baseline': baseline,
            'edge': acc - baseline,
            'home_pick_rate': home_pick,
            'games': len(y_test),
        })

    return results


def main():
    print("=" * 100)
    print("IMPROVED MODEL - TESTING CONSISTENT FEATURE SETS")
    print("=" * 100)

    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']
    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    print(f"\n✅ Loaded {len(games)} games")

    # Test different configurations
    configs = [
        ("1. Full V8.1 (38 features)", ALL_V81),
        ("2. Consistent only (16 features)", CONSISTENT_FEATURES),
        ("3. Consistent + Medium (32 features)", CONSISTENT_FEATURES + MEDIUM_VARIANCE_FEATURES),
        ("4. No Elo (36 features)", [f for f in ALL_V81 if 'elo' not in f.lower()]),
        ("5. No Season Stats (34 features)", [f for f in ALL_V81 if 'season_' not in f]),
        ("6. Possession + Rest only (10 features)", CONSISTENT_FEATURES[:10]),
        ("7. xG focused", [
            'rolling_xg_diff_10_diff', 'rolling_xg_diff_5_diff', 'rolling_xg_diff_3_diff',
            'season_xg_diff_avg_diff',
            'rolling_corsi_10_diff', 'rolling_fenwick_10_diff',
            'rolling_high_danger_shots_10_diff',
        ]),
        ("8. Form-based (no Elo, no season)", [f for f in ALL_V81 if 'elo' not in f.lower() and 'season_' not in f]),
    ]

    all_results = {}
    for name, feature_list in configs:
        avail = [f for f in feature_list if f in features.columns]
        print(f"\n⏳ Testing: {name} ({len(avail)} features)")
        results = test_model(features, target, games, avail, name)
        all_results[name] = results

        avg_acc = np.mean([r['accuracy'] for r in results])
        acc_2526 = next((r['accuracy'] for r in results if r['season'] == '20252026'), 0)
        print(f"   Avg: {avg_acc:.1%}, 2025-26: {acc_2526:.1%}")

    # Print comparison
    print("\n" + "=" * 120)
    print("FULL COMPARISON")
    print("=" * 120)

    print(f"\n{'Configuration':<40} {'Avg':<8} {'21-22':<8} {'22-23':<8} {'23-24':<8} {'24-25':<8} {'25-26':<8} {'Consistency':<12}")
    print("-" * 120)

    for name, results in all_results.items():
        accs = {r['season']: r['accuracy'] for r in results}
        avg = np.mean(list(accs.values()))
        std = np.std(list(accs.values()))

        row = f"{name:<40} {avg*100:.1f}%   "
        for s in ['20212022', '20222023', '20232024', '20242025', '20252026']:
            row += f"{accs.get(s, 0)*100:.1f}%   "
        row += f"±{std*100:.1f}pp"
        print(row)

    # Find best config
    print("\n" + "=" * 100)
    print("ANALYSIS BY METRIC")
    print("=" * 100)

    # Best average
    best_avg = max(all_results.items(), key=lambda x: np.mean([r['accuracy'] for r in x[1]]))
    print(f"\n✅ Best Average: {best_avg[0]} ({np.mean([r['accuracy'] for r in best_avg[1]])*100:.1f}%)")

    # Best 2025-26
    best_2526 = max(all_results.items(), key=lambda x: next((r['accuracy'] for r in x[1] if r['season'] == '20252026'), 0))
    acc_2526 = next((r['accuracy'] for r in best_2526[1] if r['season'] == '20252026'), 0)
    print(f"✅ Best 2025-26: {best_2526[0]} ({acc_2526*100:.1f}%)")

    # Most consistent (lowest std)
    best_consistency = min(all_results.items(), key=lambda x: np.std([r['accuracy'] for r in x[1]]))
    std_val = np.std([r['accuracy'] for r in best_consistency[1]])
    print(f"✅ Most Consistent: {best_consistency[0]} (±{std_val*100:.1f}pp)")

    # Best worst-case (highest minimum)
    best_worst = max(all_results.items(), key=lambda x: min([r['accuracy'] for r in x[1]]))
    worst_acc = min([r['accuracy'] for r in best_worst[1]])
    print(f"✅ Best Worst-Case: {best_worst[0]} (min: {worst_acc*100:.1f}%)")

    # Detailed breakdown of best models
    print("\n" + "=" * 100)
    print("DETAILED BREAKDOWN OF TOP MODELS")
    print("=" * 100)

    top_configs = [
        best_avg[0],
        best_2526[0],
        best_consistency[0],
    ]

    for config_name in set(top_configs):
        results = all_results[config_name]
        print(f"\n{config_name}:")
        print(f"{'Season':<12} {'Accuracy':<12} {'Edge':<10} {'Home Pick%':<12}")
        print("-" * 46)
        for r in results:
            print(f"{r['season']:<12} {r['accuracy']:.1%}        +{r['edge']*100:.1f}pp    {r['home_pick_rate']:.1%}")

    # Test regularization variations
    print("\n" + "=" * 100)
    print("REGULARIZATION TUNING ON BEST CONFIG")
    print("=" * 100)

    best_config_features = [f for f in configs[0][1] if f in features.columns]  # Use full model

    for C in [0.001, 0.005, 0.01, 0.02, 0.05, 0.1, 0.5, 1.0]:
        results = test_model(features, target, games, best_config_features, f"C={C}", C=C)
        avg = np.mean([r['accuracy'] for r in results])
        acc_2526 = next((r['accuracy'] for r in results if r['season'] == '20252026'), 0)
        std = np.std([r['accuracy'] for r in results])
        print(f"C={C:<6} Avg: {avg:.1%}, 2025-26: {acc_2526:.1%}, Std: ±{std*100:.1f}pp")


if __name__ == '__main__':
    main()
