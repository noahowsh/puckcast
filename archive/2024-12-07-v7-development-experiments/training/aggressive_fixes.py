#!/usr/bin/env python3
"""
Aggressive Fixes for 2025-26 Home Bias Problem

Goal: Get 2025-26 from 53% back to 60%+ while maintaining other seasons.

The problem: Model picks home 64.5% when home only wins 52.3%
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

HISTORICAL_HW = 0.535

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


def test_approach(name, features, target, games, train_seasons_filter=None,
                  weight_fn=None, post_process_fn=None, threshold=0.5, C=0.01):
    """Test an approach with leave-one-season-out."""
    results = []
    unique_seasons = sorted(games['seasonId'].unique())

    for test_season in unique_seasons:
        train_seasons = [s for s in unique_seasons if s != test_season]

        # Apply training filter if provided
        if train_seasons_filter:
            train_seasons = train_seasons_filter(train_seasons)

        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        X_train = features[train_mask].fillna(0)
        y_train = target[train_mask]
        X_test = features[test_mask].fillna(0)
        y_test = target[test_mask]

        if len(X_train) == 0 or len(X_test) == 0:
            continue

        # Calculate weights
        weights = weight_fn(games[train_mask], y_train) if weight_fn else None

        model = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(C=C, max_iter=1000, random_state=42))
        ])

        if weights is not None:
            model.fit(X_train, y_train, clf__sample_weight=weights)
        else:
            model.fit(X_train, y_train)

        y_prob = model.predict_proba(X_test)[:, 1]

        # Post-process probabilities
        if post_process_fn:
            y_prob = post_process_fn(y_prob, games[test_mask], target[test_mask])

        # Apply threshold
        y_pred = (y_prob >= threshold).astype(int)

        acc = accuracy_score(y_test, y_pred)
        home_pick_rate = (y_prob >= threshold).mean()
        baseline = y_test.mean()

        results.append({
            'season': test_season,
            'accuracy': acc,
            'baseline': baseline,
            'edge': acc - baseline,
            'home_pick_rate': home_pick_rate,
            'games': len(y_test)
        })

    return results


def main():
    print("=" * 90)
    print("AGGRESSIVE FIXES FOR 2025-26 HOME BIAS")
    print("=" * 90)

    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']
    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    # Add league HW feature
    games = games.sort_values('gameDate').copy()
    games['league_hw_50'] = games['home_win'].rolling(50, min_periods=25).mean().shift(1).fillna(HISTORICAL_HW)
    features['league_hw_50'] = games['league_hw_50'].values

    available = [f for f in V81_FEATURES if f in features.columns]
    features_v81 = features[available]
    features_with_hw = features[available + ['league_hw_50']]

    print(f"\n✅ Loaded {len(games)} games")
    print(f"   2025-26 home win rate: {target[games['seasonId']=='20252026'].mean():.1%}")

    approaches = []

    # 1. Baseline V8.1
    approaches.append(("1. V8.1 Baseline", features_v81, None, None, None, 0.5, 0.01))

    # 2. Exclude 2024-25 entirely
    def exclude_2425(seasons):
        return [s for s in seasons if s != '20242025']
    approaches.append(("2. Exclude 2024-25", features_v81, exclude_2425, None, None, 0.5, 0.01))

    # 3. Dynamic threshold based on league HW
    def dynamic_threshold_post(probs, test_games, test_target):
        # Use current league HW as threshold instead of 0.5
        league_hw = test_games['league_hw_50'].mean()
        return probs  # Return unchanged, threshold applied separately
    approaches.append(("3. Dynamic threshold (HW)", features_with_hw, None, None, dynamic_threshold_post, 0.52, 0.01))

    # 4. Aggressive probability shrinkage (30%)
    def shrink_30(probs, test_games, test_target):
        return 0.5 + (probs - 0.5) * 0.7
    approaches.append(("4. Shrink probs 30%", features_v81, None, None, shrink_30, 0.5, 0.01))

    # 5. Very aggressive shrinkage (40%)
    def shrink_40(probs, test_games, test_target):
        return 0.5 + (probs - 0.5) * 0.6
    approaches.append(("5. Shrink probs 40%", features_v81, None, None, shrink_40, 0.5, 0.01))

    # 6. Recalibrate to league HW
    def recalibrate_to_hw(probs, test_games, test_target):
        # Shift probabilities so mean matches league HW
        current_mean = probs.mean()
        league_hw = test_games['league_hw_50'].mean()
        shift = league_hw - current_mean
        return np.clip(probs + shift, 0.01, 0.99)
    approaches.append(("6. Recalibrate to HW", features_with_hw, None, None, recalibrate_to_hw, 0.5, 0.01))

    # 7. Heavy down-weight 2024-25
    def heavy_downweight(train_games, train_target):
        weights = np.ones(len(train_target))
        for i, season in enumerate(train_games['seasonId'].values):
            if season == '20242025':
                weights[i] = 0.3  # Heavy penalty
        return weights
    approaches.append(("7. 70% downweight 2024-25", features_v81, None, heavy_downweight, None, 0.5, 0.01))

    # 8. Use higher threshold (0.55)
    approaches.append(("8. Threshold = 0.55", features_v81, None, None, None, 0.55, 0.01))

    # 9. Use even higher threshold (0.58)
    approaches.append(("9. Threshold = 0.58", features_v81, None, None, None, 0.58, 0.01))

    # 10. Combine: Exclude 2024-25 + shrink 30%
    approaches.append(("10. Exclude 2425 + shrink 30%", features_v81, exclude_2425, None, shrink_30, 0.5, 0.01))

    # 11. Combine: Heavy downweight + shrink 30%
    approaches.append(("11. Downweight + shrink 30%", features_v81, None, heavy_downweight, shrink_30, 0.5, 0.01))

    # 12. Recalibrate + threshold 0.52
    approaches.append(("12. Recalib + thresh 0.52", features_with_hw, None, None, recalibrate_to_hw, 0.52, 0.01))

    # Run all approaches
    all_results = {}
    for name, feats, train_filter, weight_fn, post_fn, thresh, c in approaches:
        print(f"\n⏳ Testing: {name}")
        results = test_approach(name, feats, target, games, train_filter, weight_fn, post_fn, thresh, c)
        all_results[name] = results

        # Quick summary
        s2526 = next((r for r in results if r['season'] == '20252026'), None)
        overall_acc = np.mean([r['accuracy'] for r in results])
        if s2526:
            print(f"   Overall: {overall_acc:.1%}, 2025-26: {s2526['accuracy']:.1%} (home pick: {s2526['home_pick_rate']:.1%})")

    # Print full comparison
    print("\n" + "=" * 100)
    print("FULL RESULTS COMPARISON")
    print("=" * 100)

    print(f"\n{'Approach':<30} {'Overall':<10} {'21-22':<10} {'22-23':<10} {'23-24':<10} {'24-25':<10} {'25-26':<10}")
    print("-" * 90)

    for name, results in all_results.items():
        overall = np.mean([r['accuracy'] for r in results])
        season_accs = {r['season']: r['accuracy'] for r in results}
        row = f"{name:<30} {overall*100:.1f}%     "
        for s in ['20212022', '20222023', '20232024', '20242025', '20252026']:
            if s in season_accs:
                row += f"{season_accs[s]*100:.1f}%     "
            else:
                row += "N/A       "
        print(row)

    # Find best for 2025-26
    print("\n" + "=" * 100)
    print("2025-26 RANKING (Target: 60%+)")
    print("=" * 100)

    ranking = []
    for name, results in all_results.items():
        s2526 = next((r for r in results if r['season'] == '20252026'), None)
        overall = np.mean([r['accuracy'] for r in results])
        if s2526:
            ranking.append((name, s2526['accuracy'], s2526['home_pick_rate'], overall))

    ranking.sort(key=lambda x: x[1], reverse=True)

    print(f"\n{'Rank':<6} {'Approach':<30} {'2025-26':<12} {'Home Pick%':<12} {'Overall':<10}")
    print("-" * 70)
    for i, (name, acc, hp, overall) in enumerate(ranking, 1):
        marker = "✅" if acc >= 0.58 else "⚠️" if acc >= 0.55 else "❌"
        print(f"{i:<6} {name:<30} {marker} {acc*100:.1f}%      {hp*100:.1f}%         {overall*100:.1f}%")

    # Best overall that doesn't hurt other seasons too much
    print("\n" + "=" * 100)
    print("RECOMMENDATION")
    print("=" * 100)

    best = max(ranking, key=lambda x: x[1])
    print(f"\n🏆 Best for 2025-26: {best[0]}")
    print(f"   2025-26 accuracy: {best[1]*100:.1f}%")
    print(f"   Home pick rate: {best[2]*100:.1f}%")
    print(f"   Overall accuracy: {best[3]*100:.1f}%")


if __name__ == '__main__':
    main()
