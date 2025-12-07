#!/usr/bin/env python3
"""
Comprehensive Feature Analysis Across All Seasons

Goal: Find features that CONSISTENTLY help across all seasons, and identify
features that may be hurting certain seasons.
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

# Group features by category
FEATURE_GROUPS = {
    'Elo': ['elo_diff_pre', 'elo_expectation_home'],
    'Rolling Win %': ['rolling_win_pct_10_diff', 'rolling_win_pct_5_diff', 'rolling_win_pct_3_diff'],
    'Rolling Goals': ['rolling_goal_diff_10_diff', 'rolling_goal_diff_5_diff', 'rolling_goal_diff_3_diff'],
    'Rolling xG': ['rolling_xg_diff_10_diff', 'rolling_xg_diff_5_diff', 'rolling_xg_diff_3_diff'],
    'Possession': ['rolling_corsi_10_diff', 'rolling_corsi_5_diff', 'rolling_corsi_3_diff',
                   'rolling_fenwick_10_diff', 'rolling_fenwick_5_diff'],
    'Season Stats': ['season_win_pct_diff', 'season_goal_diff_avg_diff',
                     'season_xg_diff_avg_diff', 'season_shot_margin_diff'],
    'Rest/Schedule': ['rest_diff', 'is_b2b_home', 'is_b2b_away', 'games_last_6d_home', 'games_last_3d_home'],
    'Goaltending': ['rolling_save_pct_10_diff', 'rolling_save_pct_5_diff', 'rolling_save_pct_3_diff',
                    'rolling_gsax_5_diff', 'rolling_gsax_10_diff', 'goalie_trend_score_diff'],
    'Momentum': ['momentum_win_pct_diff', 'momentum_goal_diff_diff', 'momentum_xg_diff'],
    'Shots': ['rolling_high_danger_shots_5_diff', 'rolling_high_danger_shots_10_diff',
              'shotsFor_roll_10_diff', 'rolling_faceoff_5_diff'],
}


def test_feature_group(features, target, games, feature_list, C=0.01):
    """Test a group of features across all seasons."""
    results = {}
    unique_seasons = sorted(games['seasonId'].unique())

    for test_season in unique_seasons:
        train_seasons = [s for s in unique_seasons if s != test_season]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        X_train = features[train_mask][feature_list].fillna(0)
        y_train = target[train_mask]
        X_test = features[test_mask][feature_list].fillna(0)
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

        results[test_season] = {
            'accuracy': acc,
            'baseline': baseline,
            'edge': acc - baseline,
            'home_pick_rate': home_pick,
        }

    return results


def analyze_single_feature(features, target, games, feature_name):
    """Analyze correlation between a single feature and outcomes."""
    results = {}

    for season in sorted(games['seasonId'].unique()):
        mask = games['seasonId'] == season
        feat_vals = features[mask][feature_name].fillna(0).values
        outcomes = target[mask].values

        # Correlation
        if len(feat_vals) > 0 and np.std(feat_vals) > 0:
            corr = np.corrcoef(feat_vals, outcomes)[0, 1]
        else:
            corr = 0

        # When feature > 0 (favors home), how often does home win?
        home_favored = outcomes[feat_vals > 0]
        away_favored = outcomes[feat_vals <= 0]

        results[season] = {
            'correlation': corr,
            'home_favored_wins': home_favored.mean() if len(home_favored) > 0 else 0,
            'away_favored_wins': 1 - (away_favored.mean() if len(away_favored) > 0 else 0),
            'predictive_power': (home_favored.mean() if len(home_favored) > 0 else 0.5) - 0.5,
        }

    return results


def main():
    print("=" * 100)
    print("COMPREHENSIVE FEATURE ANALYSIS ACROSS ALL SEASONS")
    print("=" * 100)

    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']
    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    available = [f for f in V81_FEATURES if f in features.columns]
    print(f"\n✅ Loaded {len(games)} games, {len(available)} features")

    # Season overview
    print("\n" + "=" * 100)
    print("SEASON OVERVIEW")
    print("=" * 100)

    print(f"\n{'Season':<12} {'Games':<8} {'Home Win%':<12} {'Deviation from 53.5%':<20}")
    print("-" * 52)
    for season in sorted(games['seasonId'].unique()):
        mask = games['seasonId'] == season
        hw = target[mask].mean()
        dev = hw - 0.535
        print(f"{season:<12} {mask.sum():<8} {hw:.1%}        {dev*100:+.1f} pp")

    # Test full model as baseline
    print("\n" + "=" * 100)
    print("BASELINE: FULL V8.1 MODEL")
    print("=" * 100)

    baseline_results = test_feature_group(features, target, games, available)
    print(f"\n{'Season':<12} {'Accuracy':<12} {'Baseline':<12} {'Edge':<10} {'Home Pick%':<12}")
    print("-" * 58)
    for season, r in sorted(baseline_results.items()):
        print(f"{season:<12} {r['accuracy']:.1%}        {r['baseline']:.1%}        +{r['edge']*100:.1f}pp    {r['home_pick_rate']:.1%}")

    avg_acc = np.mean([r['accuracy'] for r in baseline_results.values()])
    avg_edge = np.mean([r['edge'] for r in baseline_results.values()])
    print(f"\n{'AVERAGE':<12} {avg_acc:.1%}                      +{avg_edge*100:.1f}pp")

    # Test each feature group
    print("\n" + "=" * 100)
    print("FEATURE GROUP ANALYSIS")
    print("=" * 100)

    group_performance = {}

    for group_name, group_features in FEATURE_GROUPS.items():
        avail_group = [f for f in group_features if f in features.columns]
        if not avail_group:
            continue

        results = test_feature_group(features, target, games, avail_group)

        avg_acc = np.mean([r['accuracy'] for r in results.values()])
        avg_edge = np.mean([r['edge'] for r in results.values()])
        min_acc = min([r['accuracy'] for r in results.values()])
        max_acc = max([r['accuracy'] for r in results.values()])
        std_acc = np.std([r['accuracy'] for r in results.values()])

        # 2025-26 specific
        acc_2526 = results.get('20252026', {}).get('accuracy', 0)

        group_performance[group_name] = {
            'avg_acc': avg_acc,
            'avg_edge': avg_edge,
            'min_acc': min_acc,
            'max_acc': max_acc,
            'std_acc': std_acc,
            'acc_2526': acc_2526,
            'features': len(avail_group),
            'results': results,
        }

    print(f"\n{'Group':<20} {'Avg Acc':<10} {'Avg Edge':<10} {'Min':<8} {'Max':<8} {'Std':<8} {'25-26':<8} {'#Feat':<6}")
    print("-" * 88)

    for group_name, perf in sorted(group_performance.items(), key=lambda x: x[1]['avg_acc'], reverse=True):
        print(f"{group_name:<20} {perf['avg_acc']:.1%}      +{perf['avg_edge']*100:.1f}pp    {perf['min_acc']:.1%}    {perf['max_acc']:.1%}    {perf['std_acc']*100:.1f}pp   {perf['acc_2526']:.1%}    {perf['features']}")

    # Analyze Elo specifically
    print("\n" + "=" * 100)
    print("ELO ANALYSIS - Is Elo Actually Helping?")
    print("=" * 100)

    elo_analysis = analyze_single_feature(features, target, games, 'elo_diff_pre')
    print(f"\n{'Season':<12} {'Correlation':<14} {'When Elo favors home':<22} {'Predictive Power':<18}")
    print("-" * 66)
    for season, r in sorted(elo_analysis.items()):
        print(f"{season:<12} {r['correlation']:+.3f}         Home wins {r['home_favored_wins']:.1%}        {r['predictive_power']*100:+.1f} pp")

    # Test without Elo
    print("\n" + "=" * 100)
    print("TEST: MODEL WITHOUT ELO")
    print("=" * 100)

    no_elo_features = [f for f in available if 'elo' not in f.lower()]
    no_elo_results = test_feature_group(features, target, games, no_elo_features)

    print(f"\n{'Season':<12} {'With Elo':<12} {'Without Elo':<14} {'Change':<10}")
    print("-" * 48)
    for season in sorted(baseline_results.keys()):
        with_elo = baseline_results[season]['accuracy']
        without_elo = no_elo_results[season]['accuracy']
        change = without_elo - with_elo
        marker = "✅" if change > 0 else "❌" if change < 0 else "➖"
        print(f"{season:<12} {with_elo:.1%}        {without_elo:.1%}          {marker} {change*100:+.2f}pp")

    avg_with = np.mean([r['accuracy'] for r in baseline_results.values()])
    avg_without = np.mean([r['accuracy'] for r in no_elo_results.values()])
    print(f"\n{'AVERAGE':<12} {avg_with:.1%}        {avg_without:.1%}          {(avg_without-avg_with)*100:+.2f}pp")

    # Find best minimal feature set
    print("\n" + "=" * 100)
    print("FINDING BEST MINIMAL FEATURE COMBINATIONS")
    print("=" * 100)

    # Test top performing groups combined
    top_groups = ['Rolling Win %', 'Rolling Goals', 'Season Stats']
    top_features = []
    for g in top_groups:
        top_features.extend([f for f in FEATURE_GROUPS.get(g, []) if f in features.columns])

    top_results = test_feature_group(features, target, games, top_features)
    print(f"\nTop 3 Groups ({len(top_features)} features): Rolling Win% + Rolling Goals + Season Stats")
    avg_top = np.mean([r['accuracy'] for r in top_results.values()])
    print(f"Average accuracy: {avg_top:.1%}")
    for season, r in sorted(top_results.items()):
        print(f"   {season}: {r['accuracy']:.1%} (edge: +{r['edge']*100:.1f}pp)")

    # Test without home-specific features
    print("\n" + "=" * 100)
    print("TEST: WITHOUT HOME-SPECIFIC FEATURES")
    print("=" * 100)

    no_home_features = [f for f in available if 'home' not in f.lower() and 'away' not in f.lower() and 'b2b' not in f.lower()]
    no_home_results = test_feature_group(features, target, games, no_home_features)

    print(f"\n{'Season':<12} {'Full Model':<12} {'No Home Feat':<14} {'Change':<10}")
    print("-" * 48)
    for season in sorted(baseline_results.keys()):
        full = baseline_results[season]['accuracy']
        no_home = no_home_results[season]['accuracy']
        change = no_home - full
        marker = "✅" if change > 0 else "❌" if change < 0 else "➖"
        print(f"{season:<12} {full:.1%}        {no_home:.1%}          {marker} {change*100:+.2f}pp")

    # Summary recommendations
    print("\n" + "=" * 100)
    print("RECOMMENDATIONS")
    print("=" * 100)

    print("""
Based on the analysis:

1. BEST PERFORMING FEATURE GROUPS (by average accuracy):
""")
    for i, (group_name, perf) in enumerate(sorted(group_performance.items(), key=lambda x: x[1]['avg_acc'], reverse=True)[:5], 1):
        print(f"   {i}. {group_name}: {perf['avg_acc']:.1%} avg, {perf['acc_2526']:.1%} on 2025-26")

    print("""
2. ELO OBSERVATIONS:
   - Check if Elo correlation is consistent across seasons
   - If negative in recent seasons, consider recalibrating or down-weighting

3. HOME ADVANTAGE:
   - Home-specific features may be causing bias
   - Consider removing or reducing weight of home/away specific features

4. CONSISTENCY:
   - Look for features with LOW std deviation (consistent performance)
   - Avoid features that vary wildly between seasons
""")


if __name__ == '__main__':
    main()
