#!/usr/bin/env python3
"""
Fast Model Comparison - Uses Pre-computed Feature Store

This script runs model comparisons using the pre-computed feature store,
eliminating the need to recompute features each time.

Requires: data/feature_store.parquet (run build_feature_store.py first)

Usage:
    python training/compare_fast.py
"""

import sys
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path
from datetime import datetime
import time

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# Feature sets for different model versions
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

V79_ENGINEERED = [
    'goal_momentum_accel', 'xg_momentum_accel', 'xg_x_corsi_10',
    'elo_x_rest', 'dominance', 'is_saturday',
]

V73_SITUATIONAL = [
    'fatigue_index_diff', 'third_period_trailing_perf_diff',
    'travel_distance_diff', 'divisional_matchup', 'post_break_game_diff',
]

ALL_SEASONS = [
    '20172018', '20182019', '20192020', '20202021',
    '20212022', '20222023', '20232024', '20242025',
]


def load_feature_store():
    """Load pre-computed feature store."""
    path = Path(__file__).parent.parent / 'data' / 'feature_store.parquet'
    if not path.exists():
        raise FileNotFoundError(
            f"Feature store not found at {path}\n"
            "Run: python training/build_feature_store.py"
        )
    return pd.read_parquet(path)


def get_feature_cols(df, feature_list):
    """Get available feature columns from a list."""
    return [c for c in feature_list if c in df.columns]


def train_and_test(df, train_seasons, test_season, feature_cols, C=0.01):
    """Train model and return test metrics."""
    train_mask = df['seasonId'].isin(train_seasons)
    test_mask = df['seasonId'] == test_season

    X_train = df.loc[train_mask, feature_cols].values
    X_test = df.loc[test_mask, feature_cols].values
    y_train = df.loc[train_mask, 'target'].values
    y_test = df.loc[test_mask, 'target'].values

    scaler = StandardScaler()
    X_train_s = scaler.fit_transform(X_train)
    X_test_s = scaler.transform(X_test)

    lr = LogisticRegression(C=C, max_iter=1000, random_state=42)
    lr.fit(X_train_s, y_train)

    proba = lr.predict_proba(X_test_s)[:, 1]
    pred = (proba >= 0.5).astype(int)

    return {
        'accuracy': accuracy_score(y_test, pred),
        'auc': roc_auc_score(y_test, proba),
        'log_loss': log_loss(y_test, proba),
        'n_test': len(y_test),
        'home_win_rate': y_test.mean(),
    }


def main():
    start_time = time.time()

    print("=" * 80)
    print("FAST MODEL COMPARISON (using pre-computed feature store)")
    print("=" * 80)
    print(f"Run time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load feature store
    print("Loading feature store...")
    load_start = time.time()
    df = load_feature_store()
    load_time = time.time() - load_start
    print(f"  Loaded {len(df):,} games with {len(df.columns)} columns in {load_time:.2f}s")
    print()

    # Define models
    models = {
        'V7.3 (situational)': {
            'features': V77_FEATURES + V73_SITUATIONAL,
            'C': 0.05,
        },
        'V7.7 (stable)': {
            'features': V77_FEATURES,
            'C': 0.01,
        },
        'V7.9 (enhanced)': {
            'features': V79_BASE_FEATURES + V79_ENGINEERED,
            'C': 0.005,
        },
    }

    # Training configurations
    configs = {
        '3 seasons': {
            '20232024': ['20202021', '20212022', '20222023'],
            '20242025': ['20212022', '20222023', '20232024'],
        },
        '5 seasons': {
            '20232024': ['20182019', '20192020', '20202021', '20212022', '20222023'],
            '20242025': ['20192020', '20202021', '20212022', '20222023', '20232024'],
        },
        '7 seasons': {
            '20232024': ['20172018', '20182019', '20192020', '20202021', '20212022', '20222023'],
            '20242025': ['20172018', '20182019', '20192020', '20202021', '20212022', '20222023', '20232024'],
        },
    }

    # Run all tests
    results = []
    test_start = time.time()

    for config_name, train_config in configs.items():
        for model_name, model_cfg in models.items():
            feature_cols = get_feature_cols(df, model_cfg['features'])

            for test_season in ['20232024', '20242025']:
                train_seasons = train_config[test_season]
                metrics = train_and_test(df, train_seasons, test_season, feature_cols, model_cfg['C'])

                results.append({
                    'config': config_name,
                    'model': model_name,
                    'test_season': test_season,
                    **metrics
                })

    test_time = time.time() - test_start

    # Summary
    print("=" * 80)
    print("RESULTS")
    print("=" * 80)
    print()
    print(f"{'Model':<22} {'Config':<12} {'23-24':>8} {'24-25':>8} {'Avg':>8} {'AUC':>7}")
    print("-" * 75)

    for model_name in models.keys():
        for config_name in configs.keys():
            model_results = [r for r in results if r['model'] == model_name and r['config'] == config_name]
            if len(model_results) == 2:
                r2324 = [r for r in model_results if r['test_season'] == '20232024'][0]
                r2425 = [r for r in model_results if r['test_season'] == '20242025'][0]
                avg_acc = (r2324['accuracy'] + r2425['accuracy']) / 2
                avg_auc = (r2324['auc'] + r2425['auc']) / 2
                print(f"{model_name:<22} {config_name:<12} {r2324['accuracy']*100:>7.2f}% {r2425['accuracy']*100:>7.2f}% {avg_acc*100:>7.2f}% {avg_auc:>6.4f}")

    # Best models
    print()
    print("-" * 75)

    # Group by model and find best config
    for model_name in models.keys():
        model_results = [r for r in results if r['model'] == model_name]
        by_config = {}
        for r in model_results:
            if r['config'] not in by_config:
                by_config[r['config']] = []
            by_config[r['config']].append(r['accuracy'])

        best_config = max(by_config.keys(), key=lambda k: np.mean(by_config[k]))
        best_avg = np.mean(by_config[best_config])
        print(f"{model_name}: Best with {best_config} → {best_avg*100:.2f}% avg")

    # Timing summary
    total_time = time.time() - start_time
    print()
    print("=" * 80)
    print("TIMING")
    print("=" * 80)
    print(f"  Feature store load: {load_time:.2f}s")
    print(f"  All tests ({len(results)} runs): {test_time:.2f}s")
    print(f"  Per test average: {test_time/len(results)*1000:.1f}ms")
    print(f"  TOTAL: {total_time:.2f}s")
    print()
    print("Compare to old method: ~8 minutes per model = ~24+ minutes total")
    print(f"Speedup: ~{24*60/total_time:.0f}x faster!")


if __name__ == "__main__":
    main()
