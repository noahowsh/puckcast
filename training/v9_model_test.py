#!/usr/bin/env python3
"""
V9 Model - Optimized for Consistency

Based on analysis:
- Remove high-variance features (Elo, Season Stats, Rolling Win %)
- Keep consistent features (Possession, Rest, Goaltending)
- Keep medium-variance features (xG, Goals, Shots, Momentum)
- Use stronger regularization (C=0.001)

Expected results:
- 2025-26: ~56% (vs 53% in V8.1)
- Average: ~59% (maintained)
- Consistency: ±2.2pp (vs ±3.3pp in V8.1)
"""

import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.pipeline import build_dataset

# V9 Features - Optimized for consistency
# Removed: Elo (broken in 2025-26), Season Stats (high variance), Rolling Win % (high variance)
V9_FEATURES = [
    # CONSISTENT FEATURES (low variance, reliable)
    # Possession (1.9pp std) - Works in 2025-26
    'rolling_corsi_10_diff', 'rolling_corsi_5_diff', 'rolling_corsi_3_diff',
    'rolling_fenwick_10_diff', 'rolling_fenwick_5_diff',

    # Rest/Schedule (1.4pp std) - Most consistent
    'rest_diff', 'is_b2b_home', 'is_b2b_away',
    'games_last_6d_home', 'games_last_3d_home',

    # Goaltending (1.5pp std)
    'rolling_save_pct_10_diff', 'rolling_save_pct_5_diff', 'rolling_save_pct_3_diff',
    'rolling_gsax_5_diff', 'rolling_gsax_10_diff',
    'goalie_trend_score_diff',

    # MEDIUM VARIANCE FEATURES (useful)
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

# For comparison - V8.1 features
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


def grade_from_edge(edge_value: float) -> str:
    edge_pts = abs(edge_value) * 100
    if edge_pts >= 25: return "A+"
    if edge_pts >= 20: return "A"
    if edge_pts >= 15: return "B+"
    if edge_pts >= 10: return "B"
    if edge_pts >= 5: return "C+"
    return "C"


def test_model(features, target, games, feature_list, C=0.01):
    """Full leave-one-season-out test."""
    all_predictions = []
    season_results = []
    unique_seasons = sorted(games['seasonId'].unique())

    for test_season in unique_seasons:
        train_seasons = [s for s in unique_seasons if s != test_season]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        avail = [f for f in feature_list if f in features.columns]
        X_train = features[train_mask][avail].fillna(0)
        y_train = target[train_mask]
        X_test = features[test_mask][avail].fillna(0)
        y_test = target[test_mask]
        test_games = games[test_mask].copy()

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
        ll = log_loss(y_test, y_prob)
        brier = brier_score_loss(y_test, y_prob)
        baseline = y_test.mean()
        home_pick = (y_prob >= 0.5).mean()

        season_results.append({
            'season': test_season,
            'games': len(y_test),
            'accuracy': acc,
            'log_loss': ll,
            'brier': brier,
            'baseline': baseline,
            'edge': acc - baseline,
            'home_pick_rate': home_pick,
        })

        test_games['y_true'] = y_test.values
        test_games['y_prob'] = y_prob
        test_games['y_pred'] = y_pred
        test_games['edge_val'] = y_prob - 0.5
        test_games['grade'] = test_games['edge_val'].apply(grade_from_edge)
        test_games['correct'] = (y_pred == y_test.values).astype(int)
        all_predictions.append(test_games)

    all_preds = pd.concat(all_predictions, ignore_index=True)

    # Bucket analysis
    bucket_results = []
    for grade in ['A+', 'A', 'B+', 'B', 'C+', 'C']:
        grade_mask = all_preds['grade'] == grade
        if grade_mask.sum() > 0:
            grade_preds = all_preds[grade_mask]
            bucket_results.append({
                'grade': grade,
                'games': len(grade_preds),
                'accuracy': grade_preds['correct'].mean(),
                'wins': grade_preds['correct'].sum(),
            })

    return season_results, bucket_results, all_preds


def main():
    print("=" * 100)
    print("V9 MODEL - COMPREHENSIVE TEST")
    print("=" * 100)

    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']
    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    print(f"\n✅ Loaded {len(games)} games")

    # Test V8.1 baseline
    print("\n" + "=" * 100)
    print("V8.1 BASELINE (38 features, C=0.01)")
    print("=" * 100)

    v81_seasons, v81_buckets, v81_preds = test_model(features, target, games, V81_FEATURES, C=0.01)

    print(f"\n{'Season':<12} {'Games':<8} {'Accuracy':<12} {'Baseline':<12} {'Edge':<10} {'Log Loss':<10}")
    print("-" * 64)
    for r in v81_seasons:
        print(f"{r['season']:<12} {r['games']:<8} {r['accuracy']:.1%}        {r['baseline']:.1%}        +{r['edge']*100:.1f}pp    {r['log_loss']:.4f}")

    v81_avg = np.mean([r['accuracy'] for r in v81_seasons])
    v81_std = np.std([r['accuracy'] for r in v81_seasons])
    v81_ll = np.mean([r['log_loss'] for r in v81_seasons])
    print(f"\n{'OVERALL':<12} {sum(r['games'] for r in v81_seasons):<8} {v81_avg:.1%}                      ±{v81_std*100:.1f}pp   {v81_ll:.4f}")

    # Test V9
    print("\n" + "=" * 100)
    print("V9 MODEL (29 features, C=0.01)")
    print("=" * 100)

    v9_seasons, v9_buckets, v9_preds = test_model(features, target, games, V9_FEATURES, C=0.01)

    print(f"\n{'Season':<12} {'Games':<8} {'Accuracy':<12} {'Baseline':<12} {'Edge':<10} {'Log Loss':<10}")
    print("-" * 64)
    for r in v9_seasons:
        print(f"{r['season']:<12} {r['games']:<8} {r['accuracy']:.1%}        {r['baseline']:.1%}        +{r['edge']*100:.1f}pp    {r['log_loss']:.4f}")

    v9_avg = np.mean([r['accuracy'] for r in v9_seasons])
    v9_std = np.std([r['accuracy'] for r in v9_seasons])
    v9_ll = np.mean([r['log_loss'] for r in v9_seasons])
    print(f"\n{'OVERALL':<12} {sum(r['games'] for r in v9_seasons):<8} {v9_avg:.1%}                      ±{v9_std*100:.1f}pp   {v9_ll:.4f}")

    # Test V9 with stronger regularization
    print("\n" + "=" * 100)
    print("V9 MODEL WITH C=0.001 (stronger regularization)")
    print("=" * 100)

    v9_strong_seasons, v9_strong_buckets, v9_strong_preds = test_model(features, target, games, V9_FEATURES, C=0.001)

    print(f"\n{'Season':<12} {'Games':<8} {'Accuracy':<12} {'Baseline':<12} {'Edge':<10} {'Log Loss':<10}")
    print("-" * 64)
    for r in v9_strong_seasons:
        print(f"{r['season']:<12} {r['games']:<8} {r['accuracy']:.1%}        {r['baseline']:.1%}        +{r['edge']*100:.1f}pp    {r['log_loss']:.4f}")

    v9_strong_avg = np.mean([r['accuracy'] for r in v9_strong_seasons])
    v9_strong_std = np.std([r['accuracy'] for r in v9_strong_seasons])
    v9_strong_ll = np.mean([r['log_loss'] for r in v9_strong_seasons])
    print(f"\n{'OVERALL':<12} {sum(r['games'] for r in v9_strong_seasons):<8} {v9_strong_avg:.1%}                      ±{v9_strong_std*100:.1f}pp   {v9_strong_ll:.4f}")

    # Comparison
    print("\n" + "=" * 100)
    print("HEAD-TO-HEAD COMPARISON")
    print("=" * 100)

    print(f"\n{'Metric':<25} {'V8.1':<15} {'V9 (C=0.01)':<15} {'V9 (C=0.001)':<15}")
    print("-" * 70)
    print(f"{'Average Accuracy':<25} {v81_avg:.1%}          {v9_avg:.1%}          {v9_strong_avg:.1%}")
    print(f"{'Consistency (std)':<25} ±{v81_std*100:.1f}pp        ±{v9_std*100:.1f}pp        ±{v9_strong_std*100:.1f}pp")
    print(f"{'Log Loss':<25} {v81_ll:.4f}        {v9_ll:.4f}        {v9_strong_ll:.4f}")

    print(f"\n{'Season':<12} {'V8.1':<12} {'V9':<12} {'V9 C=0.001':<12} {'Best':<12}")
    print("-" * 60)
    for i, season in enumerate(['20212022', '20222023', '20232024', '20242025', '20252026']):
        v81 = v81_seasons[i]['accuracy']
        v9 = v9_seasons[i]['accuracy']
        v9s = v9_strong_seasons[i]['accuracy']
        best = max(v81, v9, v9s)
        winner = "V8.1" if best == v81 else "V9" if best == v9 else "V9 C=0.001"
        print(f"{season:<12} {v81:.1%}        {v9:.1%}        {v9s:.1%}        {winner}")

    # Confidence buckets
    print("\n" + "=" * 100)
    print("CONFIDENCE BUCKET COMPARISON")
    print("=" * 100)

    print(f"\n{'Grade':<8} {'V8.1 Acc':<12} {'V9 Acc':<12} {'V9 C=0.001':<14} {'V8.1 Games':<12} {'V9 Games':<12}")
    print("-" * 70)

    for grade in ['A+', 'A', 'B+', 'B', 'C+', 'C']:
        v81_b = next((b for b in v81_buckets if b['grade'] == grade), None)
        v9_b = next((b for b in v9_buckets if b['grade'] == grade), None)
        v9s_b = next((b for b in v9_strong_buckets if b['grade'] == grade), None)

        if v81_b and v9_b and v9s_b:
            print(f"{grade:<8} {v81_b['accuracy']:.1%}        {v9_b['accuracy']:.1%}        {v9s_b['accuracy']:.1%}          {v81_b['games']:<12} {v9_b['games']}")

    # Summary
    print("\n" + "=" * 100)
    print("SUMMARY")
    print("=" * 100)

    v81_2526 = next(r['accuracy'] for r in v81_seasons if r['season'] == '20252026')
    v9_2526 = next(r['accuracy'] for r in v9_seasons if r['season'] == '20252026')
    v9s_2526 = next(r['accuracy'] for r in v9_strong_seasons if r['season'] == '20252026')

    print(f"""
V9 Model Improvements:

1. Features: 29 (vs 38 in V8.1)
   - REMOVED: Elo (broken in 2025-26), Season Stats (high variance), Rolling Win % (high variance)
   - KEPT: Possession, Rest, Goaltending, xG, Goals, Shots, Momentum

2. 2025-26 Performance:
   - V8.1: {v81_2526:.1%}
   - V9:   {v9_2526:.1%} ({(v9_2526-v81_2526)*100:+.1f}pp)
   - V9 C=0.001: {v9s_2526:.1%} ({(v9s_2526-v81_2526)*100:+.1f}pp)

3. Consistency:
   - V8.1: ±{v81_std*100:.1f}pp
   - V9:   ±{v9_std*100:.1f}pp
   - V9 C=0.001: ±{v9_strong_std*100:.1f}pp

4. Average Accuracy:
   - V8.1: {v81_avg:.1%}
   - V9:   {v9_avg:.1%}
   - V9 C=0.001: {v9_strong_avg:.1%}
""")

    if v9_2526 > v81_2526 and v9_avg >= v81_avg - 0.005:
        print("✅ RECOMMENDATION: Adopt V9 model - better 2025-26 performance with maintained overall accuracy")
    elif v9s_2526 > v81_2526 and v9_strong_avg >= v81_avg - 0.005:
        print("✅ RECOMMENDATION: Adopt V9 with C=0.001 - best 2025-26 performance")
    else:
        print("⚠️ More testing needed")


if __name__ == '__main__':
    main()
