#!/usr/bin/env python3
"""
Compare All Model Versions (V7.3 through V7.9)

This script runs forward validation on all model versions to provide
a fair comparison across both the 2023-24 and 2024-25 test seasons.

Usage:
    python training/compare_all_models.py
"""

import sys
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.situational_features import add_situational_features
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities
from nhl_prediction.train import compute_season_weights


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


def test_v73_situational(train_seasons, test_season):
    """Test V7.3 with situational features (the TRUE V7.3)."""
    all_seasons = train_seasons + [test_season]
    dataset = build_dataset(all_seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

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

    return acc, y_test.mean(), len(features_full.columns)


def test_model(games, features, target, train_seasons, test_season,
               feature_idx=None, C=0.01, n_select=None):
    """Test a model configuration."""
    train_mask = games['seasonId'].isin(train_seasons)
    test_mask = games['seasonId'] == test_season

    if feature_idx is not None:
        X_train = features[train_mask].values[:, feature_idx]
        X_test = features[test_mask].values[:, feature_idx]
    else:
        X_train = features[train_mask].values
        X_test = features[test_mask].values

    y_train = target[train_mask].values
    y_test = target[test_mask].values

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    # Feature selection if requested
    if n_select and n_select < X_train_s.shape[1]:
        lr_full = LogisticRegression(C=C, max_iter=1000, random_state=42)
        lr_full.fit(X_train_s, y_train)
        top_idx = np.argsort(np.abs(lr_full.coef_[0]))[::-1][:n_select]
        X_train_s = X_train_s[:, top_idx]
        X_test_s = X_test_s[:, top_idx]

    lr = LogisticRegression(C=C, max_iter=1000, random_state=42)
    lr.fit(X_train_s, y_train)
    proba = lr.predict_proba(X_test_s)[:, 1]
    pred = (proba >= 0.5).astype(int)

    return accuracy_score(y_test, pred), y_test.mean()


def main():
    print("=" * 70)
    print("COMPLETE MODEL COMPARISON: V7.3 through V7.9")
    print("=" * 70)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load data
    print("Loading data...")
    dataset = build_dataset(['20212022', '20222023', '20232024', '20242025'])
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()
    feature_names = features.columns.tolist()

    print(f"Total games: {len(games)}")
    print(f"Total features: {len(feature_names)}")
    print()

    # Prepare feature indices
    team_dummy_idx = [i for i, n in enumerate(feature_names)
                     if n.startswith('home_team_') or n.startswith('away_team_')]
    non_team_idx = [i for i in range(len(feature_names)) if i not in team_dummy_idx]
    v77_idx = [i for i, n in enumerate(feature_names) if n in V77_FEATURES]
    v79_base_idx = [i for i, n in enumerate(feature_names) if n in V79_BASE_FEATURES]

    # Create V7.9 features
    v79_base = features[[n for n in V79_BASE_FEATURES if n in features.columns]].copy()
    v79_eng = create_v79_engineered_features(features, games)
    v79_full = pd.concat([v79_base, v79_eng], axis=1)

    results = []

    # Test each model
    models = [
        ("V7.3 (situational)", "v73", 0.05, None, "222 features (209 + 13 situational)"),
        ("V7.6 (team dummies)", None, 0.01, 59, "Top 59 (includes team dummies)"),
        ("V7.7 (stable)", v77_idx, 0.01, None, "23 stable features (NO team dummies)"),
        ("V7.9 (enhanced)", "v79", 0.005, None, "42 features (36 base + 6 engineered)"),
    ]

    print("=" * 70)
    print("RESULTS")
    print("=" * 70)
    print()
    print(f"{'Model':<25} {'23-24':>10} {'24-25':>10} {'Average':>10} {'Variance':>10}")
    print("-" * 70)

    for name, feat_idx, C, n_select, description in models:
        if name == "V7.3 (situational)":
            # V7.3 with situational features - uses pipeline + sample weights
            acc1, base1, n_feat = test_v73_situational(['20212022', '20222023'], '20232024')
            acc2, base2, _ = test_v73_situational(['20222023', '20232024'], '20242025')
        elif name == "V7.9 (enhanced)":
            # V7.9 uses its own feature set
            X_v79 = v79_full.values

            train_mask1 = games['seasonId'].isin(['20212022', '20222023'])
            test_mask1 = games['seasonId'] == '20232024'
            train_mask2 = games['seasonId'].isin(['20222023', '20232024'])
            test_mask2 = games['seasonId'] == '20242025'

            scaler = StandardScaler()

            X_train1_s = scaler.fit_transform(X_v79[train_mask1])
            X_test1_s = scaler.transform(X_v79[test_mask1])
            lr1 = LogisticRegression(C=C, max_iter=1000, random_state=42)
            lr1.fit(X_train1_s, target[train_mask1].values)
            acc1 = accuracy_score(target[test_mask1].values,
                                 (lr1.predict_proba(X_test1_s)[:, 1] >= 0.5).astype(int))

            X_train2_s = scaler.fit_transform(X_v79[train_mask2])
            X_test2_s = scaler.transform(X_v79[test_mask2])
            lr2 = LogisticRegression(C=C, max_iter=1000, random_state=42)
            lr2.fit(X_train2_s, target[train_mask2].values)
            acc2 = accuracy_score(target[test_mask2].values,
                                 (lr2.predict_proba(X_test2_s)[:, 1] >= 0.5).astype(int))

            base1 = target[test_mask1].mean()
            base2 = target[test_mask2].mean()
        else:
            acc1, base1 = test_model(games, features, target,
                                     ['20212022', '20222023'], '20232024',
                                     feat_idx, C, n_select)
            acc2, base2 = test_model(games, features, target,
                                     ['20222023', '20232024'], '20242025',
                                     feat_idx, C, n_select)

        avg = (acc1 + acc2) / 2
        var = abs(acc1 - acc2)

        results.append({
            'name': name,
            'acc_2324': acc1,
            'acc_2425': acc2,
            'avg': avg,
            'var': var,
            'description': description
        })

        print(f"{name:<25} {acc1*100:>9.2f}% {acc2*100:>9.2f}% {avg*100:>9.2f}% {var*100:>9.1f}pp")

    # Summary
    print()
    print("=" * 70)
    print("ANALYSIS")
    print("=" * 70)
    print()

    print("Home Ice Advantage by Season:")
    for season in ['20232024', '20242025']:
        mask = games['seasonId'] == season
        home_pct = target[mask].mean()
        print(f"  {season[:4]}-{season[4:6]}: {home_pct*100:.1f}% home wins")

    print()
    print("Model Descriptions:")
    for r in results:
        print(f"  {r['name']}: {r['description']}")

    print()
    print("=" * 70)
    print("RECOMMENDATION")
    print("=" * 70)
    print()

    best = max(results, key=lambda x: x['avg'])
    most_consistent = min(results, key=lambda x: x['var'])

    print(f"Highest Average Accuracy: {best['name']} at {best['avg']*100:.2f}%")
    print(f"Most Consistent: {most_consistent['name']} at {most_consistent['var']*100:.1f}pp variance")
    print()

    if best['name'] == most_consistent['name']:
        print(f"✅ RECOMMENDED: {best['name']}")
        print(f"   - Best accuracy AND most consistent")
    else:
        print(f"⚠️  Trade-off between accuracy and consistency")
        print(f"   - For highest accuracy: {best['name']}")
        print(f"   - For consistency: {most_consistent['name']}")


if __name__ == "__main__":
    main()
