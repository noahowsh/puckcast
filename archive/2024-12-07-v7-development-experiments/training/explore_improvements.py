#!/usr/bin/env python3
"""
Explore Additional Model Improvements

Test various approaches to further reduce home bias and improve accuracy.
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

HISTORICAL_HOME_WIN_RATE = 0.535

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


def add_league_hw_feature(games: pd.DataFrame, window: int = 100) -> pd.DataFrame:
    """Add rolling league-wide home win rate."""
    games = games.sort_values('gameDate').copy()
    games[f'league_hw_{window}'] = games['home_win'].rolling(
        window=window, min_periods=50
    ).mean().shift(1)
    games[f'league_hw_{window}'] = games[f'league_hw_{window}'].fillna(HISTORICAL_HOME_WIN_RATE)
    return games


def grade_from_edge(edge_value: float) -> str:
    edge_pts = abs(edge_value) * 100
    if edge_pts >= 25: return "A+"
    if edge_pts >= 20: return "A"
    if edge_pts >= 15: return "B+"
    if edge_pts >= 10: return "B"
    if edge_pts >= 5: return "C+"
    return "C"


def test_approach(features, target, games, approach_name,
                  weight_func=None, post_process_func=None, C=0.01):
    """Test a specific approach."""
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

        train_games = games.loc[train_mask].copy()
        weights = weight_func(train_games, y_train) if weight_func else None

        model = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(C=C, max_iter=1000, random_state=42))
        ])

        if weights is not None:
            model.fit(X_train, y_train, clf__sample_weight=weights)
        else:
            model.fit(X_train, y_train)

        y_prob = model.predict_proba(X_test)[:, 1]

        # Post-processing (e.g., probability shrinkage)
        if post_process_func:
            y_prob = post_process_func(y_prob, test_games)

        y_pred = (y_prob >= 0.5).astype(int)

        acc = accuracy_score(y_test, y_pred)
        ll = log_loss(y_test, np.clip(y_prob, 0.001, 0.999))
        baseline = y_test.mean()
        home_pick_rate = (y_prob >= 0.5).mean()

        season_results.append({
            'season': test_season,
            'games': len(y_test),
            'accuracy': acc,
            'log_loss': ll,
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

    overall_acc = all_preds['correct'].mean()
    overall_ll = log_loss(all_preds['y_true'], np.clip(all_preds['y_prob'], 0.001, 0.999))
    home_win_rate = all_preds['y_true'].mean()

    # A+ tier
    a_plus = all_preds[all_preds['grade'] == 'A+']
    a_plus_acc = a_plus['correct'].mean() if len(a_plus) > 0 else 0

    return {
        'approach': approach_name,
        'overall_acc': overall_acc,
        'overall_ll': overall_ll,
        'edge': overall_acc - home_win_rate,
        'a_plus_acc': a_plus_acc,
        'a_plus_games': len(a_plus),
        'seasons': season_results,
    }


def main():
    print("=" * 90)
    print("EXPLORING ADDITIONAL IMPROVEMENTS")
    print("=" * 90)

    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']
    print(f"\n📊 Loading data for seasons: {', '.join(seasons)}")

    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    # Add various league hw features
    games = add_league_hw_feature(games, 100)
    games = add_league_hw_feature(games, 50)
    games = add_league_hw_feature(games, 200)

    features['league_hw_100'] = games['league_hw_100'].values
    features['league_hw_50'] = games['league_hw_50'].values
    features['league_hw_200'] = games['league_hw_200'].values

    print(f"✅ Total games: {len(games)}")

    available_v81 = [f for f in V81_FEATURES if f in features.columns]

    # Define different approaches to test
    approaches = []

    # 1. Baseline V8.1
    def no_weights(g, t): return None
    approaches.append(("1. V8.1 Baseline", available_v81, no_weights, None, 0.01))

    # 2. V8.2 (current - adaptive weights + league_hw_100)
    def adaptive_weights_v82(g, t):
        weights = np.ones(len(t))
        seasons = g['seasonId'].values
        season_hw_rates = {}
        for season in g['seasonId'].unique():
            season_mask = g['seasonId'] == season
            season_hw = t[season_mask].mean()
            season_hw_rates[season] = season_hw
        for i, season in enumerate(seasons):
            deviation = abs(season_hw_rates[season] - HISTORICAL_HOME_WIN_RATE)
            weights[i] = 1.0 / (1.0 + deviation * 5)
        return weights

    v82_features = ['league_hw_100'] + available_v81
    approaches.append(("2. V8.2 (current)", v82_features, adaptive_weights_v82, None, 0.01))

    # 3. Stronger adaptive weights (deviation * 10)
    def adaptive_weights_strong(g, t):
        weights = np.ones(len(t))
        seasons = g['seasonId'].values
        season_hw_rates = {}
        for season in g['seasonId'].unique():
            season_mask = g['seasonId'] == season
            season_hw = t[season_mask].mean()
            season_hw_rates[season] = season_hw
        for i, season in enumerate(seasons):
            deviation = abs(season_hw_rates[season] - HISTORICAL_HOME_WIN_RATE)
            weights[i] = 1.0 / (1.0 + deviation * 10)  # Stronger penalty
        return weights

    approaches.append(("3. Stronger weights (*10)", v82_features, adaptive_weights_strong, None, 0.01))

    # 4. Probability shrinkage toward 0.5
    def shrink_toward_half(probs, games):
        shrink_factor = 0.9  # Move 10% toward 0.5
        return 0.5 + (probs - 0.5) * shrink_factor

    approaches.append(("4. Probability shrinkage (0.9)", v82_features, adaptive_weights_v82, shrink_toward_half, 0.01))

    # 5. Aggressive probability shrinkage
    def shrink_aggressive(probs, games):
        shrink_factor = 0.8  # Move 20% toward 0.5
        return 0.5 + (probs - 0.5) * shrink_factor

    approaches.append(("5. Aggressive shrinkage (0.8)", v82_features, adaptive_weights_v82, shrink_aggressive, 0.01))

    # 6. Dynamic shrinkage based on league HW deviation
    def shrink_dynamic(probs, games):
        league_hw = games['league_hw_100'].values
        # When league HW deviates from historical, shrink more
        deviation = np.abs(league_hw - HISTORICAL_HOME_WIN_RATE)
        shrink_factor = 1.0 - deviation * 3  # Max 10% shrinkage when deviation is 3%
        shrink_factor = np.clip(shrink_factor, 0.7, 1.0)
        return 0.5 + (probs - 0.5) * shrink_factor

    approaches.append(("6. Dynamic shrinkage", v82_features, adaptive_weights_v82, shrink_dynamic, 0.01))

    # 7. Exclude 2024-25 from training completely
    def exclude_2024_weights(g, t):
        weights = np.ones(len(t))
        seasons = g['seasonId'].values
        for i, season in enumerate(seasons):
            if season == '20242025':
                weights[i] = 0.0  # Completely exclude
        return weights

    approaches.append(("7. Exclude 2024-25", v82_features, exclude_2024_weights, None, 0.01))

    # 8. Heavier regularization (C=0.005)
    approaches.append(("8. Heavy regularization (C=0.005)", v82_features, adaptive_weights_v82, None, 0.005))

    # 9. Lighter regularization (C=0.02)
    approaches.append(("9. Light regularization (C=0.02)", v82_features, adaptive_weights_v82, None, 0.02))

    # 10. League HW 50 window (more responsive)
    v82_features_50 = ['league_hw_50'] + available_v81
    approaches.append(("10. League HW window=50", v82_features_50, adaptive_weights_v82, None, 0.01))

    # Run all approaches
    results = []
    for name, feats, weight_fn, post_fn, c in approaches:
        print(f"\n⏳ Testing: {name}")
        feature_subset = features[[f for f in feats if f in features.columns]]
        result = test_approach(feature_subset, target, games, name, weight_fn, post_fn, c)
        results.append(result)
        print(f"   Overall: {result['overall_acc']*100:.2f}%, A+: {result['a_plus_acc']*100:.1f}%, LL: {result['overall_ll']:.4f}")

    # Print comparison table
    print("\n" + "=" * 100)
    print("RESULTS COMPARISON")
    print("=" * 100)

    print(f"\n{'Approach':<35} {'Overall':<10} {'Edge':<10} {'A+ Acc':<10} {'A+ Games':<10} {'Log Loss':<10}")
    print("-" * 85)

    for r in results:
        print(f"{r['approach']:<35} {r['overall_acc']*100:.2f}%     +{r['edge']*100:.1f}pp    {r['a_plus_acc']*100:.1f}%      {r['a_plus_games']:<10} {r['overall_ll']:.4f}")

    # Season breakdown for top approaches
    print("\n" + "=" * 100)
    print("2025-26 SEASON COMPARISON (Current Season)")
    print("=" * 100)

    print(f"\n{'Approach':<35} {'Accuracy':<12} {'Edge':<10} {'Home Pick %':<12} {'Baseline':<10}")
    print("-" * 79)

    for r in results:
        s2526 = next((s for s in r['seasons'] if s['season'] == '20252026'), None)
        if s2526:
            print(f"{r['approach']:<35} {s2526['accuracy']*100:.2f}%       +{s2526['edge']*100:.1f}pp    {s2526['home_pick_rate']*100:.1f}%         {s2526['baseline']*100:.1f}%")

    print("\n" + "=" * 100)
    print("2024-25 SEASON COMPARISON (Anomalous Season)")
    print("=" * 100)

    print(f"\n{'Approach':<35} {'Accuracy':<12} {'Edge':<10} {'Home Pick %':<12} {'Baseline':<10}")
    print("-" * 79)

    for r in results:
        s2425 = next((s for s in r['seasons'] if s['season'] == '20242025'), None)
        if s2425:
            print(f"{r['approach']:<35} {s2425['accuracy']*100:.2f}%       +{s2425['edge']*100:.1f}pp    {s2425['home_pick_rate']*100:.1f}%         {s2425['baseline']*100:.1f}%")

    # Find best approach
    print("\n" + "=" * 100)
    print("RECOMMENDATIONS")
    print("=" * 100)

    best_overall = max(results, key=lambda x: x['overall_acc'])
    best_a_plus = max(results, key=lambda x: x['a_plus_acc'])
    best_2526 = max(results, key=lambda x: next((s['accuracy'] for s in x['seasons'] if s['season'] == '20252026'), 0))

    print(f"\n✅ Best Overall Accuracy: {best_overall['approach']} ({best_overall['overall_acc']*100:.2f}%)")
    print(f"✅ Best A+ Accuracy: {best_a_plus['approach']} ({best_a_plus['a_plus_acc']*100:.1f}%)")
    print(f"✅ Best 2025-26 Performance: {best_2526['approach']}")


if __name__ == '__main__':
    main()
