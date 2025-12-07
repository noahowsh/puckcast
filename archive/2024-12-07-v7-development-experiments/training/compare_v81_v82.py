#!/usr/bin/env python3
"""
Comprehensive V8.1 vs V8.2 Comparison

Compare both models across all seasons including 2025-26 current season.
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
from sklearn.model_selection import cross_val_score

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.pipeline import build_dataset

HISTORICAL_HOME_WIN_RATE = 0.535

# V8.1 Features (38)
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

# V8.2 Features (39) - adds league_hw_100
V82_FEATURES = ['league_hw_100'] + V81_FEATURES


def add_league_hw_feature(games: pd.DataFrame) -> pd.DataFrame:
    """Add rolling 100-game league-wide home win rate."""
    games = games.sort_values('gameDate').copy()
    games['league_hw_100'] = games['home_win'].rolling(
        window=100, min_periods=50
    ).mean().shift(1)
    games['league_hw_100'] = games['league_hw_100'].fillna(HISTORICAL_HOME_WIN_RATE)
    return games


def calculate_adaptive_weights(games: pd.DataFrame, target: pd.Series) -> np.ndarray:
    """Calculate sample weights for V8.2."""
    weights = np.ones(len(target))
    seasons = games['seasonId'].values

    season_hw_rates = {}
    for season in games['seasonId'].unique():
        season_mask = games['seasonId'] == season
        season_hw = target[season_mask].mean()
        season_hw_rates[season] = season_hw

    for i, season in enumerate(seasons):
        season_hw = season_hw_rates[season]
        deviation = abs(season_hw - HISTORICAL_HOME_WIN_RATE)
        weights[i] = 1.0 / (1.0 + deviation * 5)

    return weights


def grade_from_edge(edge_value: float) -> str:
    edge_pts = abs(edge_value) * 100
    if edge_pts >= 25: return "A+"
    if edge_pts >= 20: return "A"
    if edge_pts >= 15: return "B+"
    if edge_pts >= 10: return "B"
    if edge_pts >= 5: return "C+"
    return "C"


def run_model_test(features, target, games, model_name, use_adaptive_weights=False):
    """Run leave-one-season-out testing."""
    all_predictions = []
    season_results = []

    unique_seasons = sorted(games['seasonId'].unique())

    for test_season in unique_seasons:
        train_seasons = [s for s in unique_seasons if s != test_season]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        X_train = features.loc[train_mask].fillna(0)
        y_train = target.loc[train_mask]
        X_test = features.loc[test_mask].fillna(0)
        y_test = target.loc[test_mask]
        test_games = games.loc[test_mask].copy()

        if len(X_train) == 0 or len(X_test) == 0:
            continue

        # Calculate weights if using V8.2
        train_games = games.loc[train_mask].copy()
        if use_adaptive_weights:
            weights = calculate_adaptive_weights(train_games, y_train)
        else:
            weights = None

        # Tune C
        best_c = 0.01
        best_score = 0
        for c in [0.005, 0.01, 0.02, 0.05, 0.1, 0.5, 1.0]:
            temp_model = Pipeline([
                ('scaler', StandardScaler()),
                ('clf', LogisticRegression(C=c, max_iter=1000, random_state=42))
            ])
            scores = cross_val_score(temp_model, X_train, y_train, cv=3, scoring='accuracy')
            if scores.mean() > best_score:
                best_score = scores.mean()
                best_c = c

        model = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(C=best_c, max_iter=1000, random_state=42))
        ])

        if weights is not None:
            model.fit(X_train, y_train, clf__sample_weight=weights)
        else:
            model.fit(X_train, y_train)

        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        acc = accuracy_score(y_test, y_pred)
        ll = log_loss(y_test, y_prob)
        brier = brier_score_loss(y_test, y_prob)
        baseline = y_test.mean()

        # Home pick rate
        home_picks = (y_prob >= 0.5).sum()
        home_pick_rate = home_picks / len(y_prob)

        season_results.append({
            'season': test_season,
            'games': len(y_test),
            'accuracy': acc,
            'log_loss': ll,
            'brier': brier,
            'baseline': baseline,
            'edge': acc - baseline,
            'home_pick_rate': home_pick_rate,
        })

        test_games['y_true'] = y_test.values
        test_games['y_prob'] = y_prob
        test_games['y_pred'] = y_pred
        test_games['edge'] = y_prob - 0.5
        test_games['grade'] = test_games['edge'].apply(grade_from_edge)
        test_games['correct'] = (test_games['y_pred'] == test_games['y_true']).astype(int)
        all_predictions.append(test_games)

    all_preds = pd.concat(all_predictions, ignore_index=True)

    # Overall metrics
    overall_acc = all_preds['correct'].mean()
    overall_ll = log_loss(all_preds['y_true'], all_preds['y_prob'])
    overall_brier = brier_score_loss(all_preds['y_true'], all_preds['y_prob'])
    home_win_rate = all_preds['y_true'].mean()

    # Bucket analysis
    bucket_results = {}
    for grade in ['A+', 'A', 'B+', 'B', 'C+', 'C']:
        grade_mask = all_preds['grade'] == grade
        if grade_mask.sum() > 0:
            grade_preds = all_preds[grade_mask]
            bucket_results[grade] = {
                'games': len(grade_preds),
                'accuracy': grade_preds['correct'].mean(),
            }

    # A-tier combined
    a_tier = all_preds[all_preds['grade'].isin(['A+', 'A'])]
    if len(a_tier) > 0:
        bucket_results['A-tier'] = {
            'games': len(a_tier),
            'accuracy': a_tier['correct'].mean(),
        }

    return {
        'model': model_name,
        'overall': {
            'games': len(all_preds),
            'accuracy': overall_acc,
            'log_loss': overall_ll,
            'brier': overall_brier,
            'baseline': home_win_rate,
            'edge': overall_acc - home_win_rate,
        },
        'seasons': season_results,
        'buckets': bucket_results,
    }


def main():
    print("=" * 90)
    print("COMPREHENSIVE V8.1 vs V8.2 COMPARISON")
    print("=" * 90)

    # Load ALL seasons including 2025-26
    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']
    print(f"\n📊 Loading data for seasons: {', '.join(seasons)}")

    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    # Add league_hw_100 feature
    games = add_league_hw_feature(games)
    features['league_hw_100'] = games['league_hw_100'].values

    print(f"✅ Total games: {len(games)}")

    # Show season breakdown
    print("\n📅 Season breakdown:")
    for season in sorted(games['seasonId'].unique()):
        season_mask = games['seasonId'] == season
        count = season_mask.sum()
        hw = target[season_mask].mean()
        print(f"   {season}: {count:>4} games, home win rate: {hw:.1%}")

    # Filter features for each model
    available_v81 = [f for f in V81_FEATURES if f in features.columns]
    available_v82 = [f for f in V82_FEATURES if f in features.columns]

    features_v81 = features[available_v81]
    features_v82 = features[available_v82]

    print(f"\n✅ V8.1: {len(available_v81)} features")
    print(f"✅ V8.2: {len(available_v82)} features")

    # Run V8.1 test
    print("\n" + "=" * 90)
    print("TESTING V8.1 MODEL...")
    print("=" * 90)
    v81_results = run_model_test(features_v81, target, games, "V8.1", use_adaptive_weights=False)

    # Run V8.2 test
    print("\n" + "=" * 90)
    print("TESTING V8.2 MODEL...")
    print("=" * 90)
    v82_results = run_model_test(features_v82, target, games, "V8.2", use_adaptive_weights=True)

    # Print comparison
    print("\n" + "=" * 90)
    print("OVERALL COMPARISON")
    print("=" * 90)

    print(f"\n{'Metric':<20} {'V8.1':<15} {'V8.2':<15} {'Change':<15}")
    print("-" * 65)

    v81_o = v81_results['overall']
    v82_o = v82_results['overall']

    acc_diff = (v82_o['accuracy'] - v81_o['accuracy']) * 100
    ll_diff = v82_o['log_loss'] - v81_o['log_loss']
    brier_diff = v82_o['brier'] - v81_o['brier']
    edge_diff = (v82_o['edge'] - v81_o['edge']) * 100

    print(f"{'Accuracy':<20} {v81_o['accuracy']*100:.2f}%         {v82_o['accuracy']*100:.2f}%         {acc_diff:+.2f} pp")
    print(f"{'Log Loss':<20} {v81_o['log_loss']:.4f}        {v82_o['log_loss']:.4f}        {ll_diff:+.4f}")
    print(f"{'Brier Score':<20} {v81_o['brier']:.4f}        {v82_o['brier']:.4f}        {brier_diff:+.4f}")
    print(f"{'Edge vs Baseline':<20} +{v81_o['edge']*100:.2f} pp       +{v82_o['edge']*100:.2f} pp       {edge_diff:+.2f} pp")
    print(f"{'Games Tested':<20} {v81_o['games']:<15} {v82_o['games']:<15}")

    print("\n" + "=" * 90)
    print("SEASON-BY-SEASON COMPARISON")
    print("=" * 90)

    print(f"\n{'Season':<12} {'V8.1 Acc':<12} {'V8.2 Acc':<12} {'Change':<10} {'V8.1 Edge':<12} {'V8.2 Edge':<12} {'Baseline':<10}")
    print("-" * 90)

    for v81_s in v81_results['seasons']:
        season = v81_s['season']
        v82_s = next((s for s in v82_results['seasons'] if s['season'] == season), None)
        if v82_s:
            acc_diff = (v82_s['accuracy'] - v81_s['accuracy']) * 100
            print(f"{season:<12} {v81_s['accuracy']*100:.2f}%       {v82_s['accuracy']*100:.2f}%       {acc_diff:+.2f} pp    +{v81_s['edge']*100:.1f} pp      +{v82_s['edge']*100:.1f} pp      {v81_s['baseline']*100:.1f}%")

    print("\n" + "=" * 90)
    print("CONFIDENCE BUCKET COMPARISON")
    print("=" * 90)

    print(f"\n{'Grade':<10} {'V8.1 Acc':<15} {'V8.2 Acc':<15} {'Change':<12} {'V8.1 Games':<12} {'V8.2 Games':<12}")
    print("-" * 76)

    for grade in ['A+', 'A', 'A-tier', 'B+', 'B', 'C+', 'C']:
        v81_b = v81_results['buckets'].get(grade, {})
        v82_b = v82_results['buckets'].get(grade, {})
        if v81_b and v82_b:
            acc_diff = (v82_b['accuracy'] - v81_b['accuracy']) * 100
            symbol = "✅" if acc_diff > 0 else "❌" if acc_diff < 0 else "➖"
            print(f"{grade:<10} {v81_b['accuracy']*100:.2f}%          {v82_b['accuracy']*100:.2f}%          {symbol} {acc_diff:+.2f} pp    {v81_b['games']:<12} {v82_b['games']:<12}")

    print("\n" + "=" * 90)
    print("HOME PICK RATE COMPARISON (Key diagnostic for bias)")
    print("=" * 90)

    print(f"\n{'Season':<12} {'Baseline HW':<14} {'V8.1 Home %':<14} {'V8.2 Home %':<14} {'Change':<12}")
    print("-" * 66)

    for v81_s in v81_results['seasons']:
        season = v81_s['season']
        v82_s = next((s for s in v82_results['seasons'] if s['season'] == season), None)
        if v82_s:
            hp_diff = (v82_s['home_pick_rate'] - v81_s['home_pick_rate']) * 100
            # Check if V8.2 moved closer to baseline
            v81_bias = abs(v81_s['home_pick_rate'] - v81_s['baseline'])
            v82_bias = abs(v82_s['home_pick_rate'] - v82_s['baseline'])
            better = "✅" if v82_bias < v81_bias else "❌" if v82_bias > v81_bias else "➖"
            print(f"{season:<12} {v81_s['baseline']*100:.1f}%          {v81_s['home_pick_rate']*100:.1f}%          {v82_s['home_pick_rate']*100:.1f}%          {better} {hp_diff:+.1f} pp")

    print("\n" + "=" * 90)
    print("SUMMARY")
    print("=" * 90)

    # Count wins/losses
    better_count = 0
    worse_count = 0
    for v81_s in v81_results['seasons']:
        v82_s = next((s for s in v82_results['seasons'] if s['season'] == v81_s['season']), None)
        if v82_s:
            if v82_s['accuracy'] > v81_s['accuracy']:
                better_count += 1
            elif v82_s['accuracy'] < v81_s['accuracy']:
                worse_count += 1

    print(f"\nSeasons where V8.2 is better: {better_count}")
    print(f"Seasons where V8.2 is worse:  {worse_count}")

    # Key takeaways
    a_plus_v81 = v81_results['buckets'].get('A+', {}).get('accuracy', 0)
    a_plus_v82 = v82_results['buckets'].get('A+', {}).get('accuracy', 0)

    print(f"\nA+ tier change: {(a_plus_v82 - a_plus_v81)*100:+.2f} pp")
    print(f"Overall accuracy change: {acc_diff:+.2f} pp")
    print(f"Log loss change: {ll_diff:+.4f} (negative = better)")

    return v81_results, v82_results


if __name__ == '__main__':
    v81, v82 = main()
