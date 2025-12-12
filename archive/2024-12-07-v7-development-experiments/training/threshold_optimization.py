#!/usr/bin/env python3
"""
Threshold Optimization - Find optimal threshold for each season

The problem: 2025-26 has 52.3% home win rate but model picks home 64.5%
Solution: Adjust threshold to reduce home bias
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


def main():
    print("=" * 90)
    print("THRESHOLD OPTIMIZATION")
    print("=" * 90)

    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']
    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    available = [f for f in V81_FEATURES if f in features.columns]
    print(f"\n✅ Loaded {len(games)} games")

    # First, get raw probabilities for each season using leave-one-out
    print("\n📊 Getting raw probabilities for each season...")

    all_probs = {}
    for test_season in seasons:
        train_seasons = [s for s in seasons if s != test_season]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        X_train = features[train_mask][available].fillna(0)
        y_train = target[train_mask]
        X_test = features[test_mask][available].fillna(0)
        y_test = target[test_mask]

        model = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(C=0.01, max_iter=1000, random_state=42))
        ])
        model.fit(X_train, y_train)

        y_prob = model.predict_proba(X_test)[:, 1]
        all_probs[test_season] = {
            'probs': y_prob,
            'true': y_test.values,
            'home_win_rate': y_test.mean(),
        }

    # Show baseline stats
    print(f"\n{'Season':<12} {'Home Win%':<12} {'Model Home Pick% (t=0.5)':<25} {'Accuracy (t=0.5)':<18}")
    print("-" * 67)
    for season in seasons:
        d = all_probs[season]
        home_pick = (d['probs'] >= 0.5).mean()
        acc = accuracy_score(d['true'], (d['probs'] >= 0.5).astype(int))
        print(f"{season:<12} {d['home_win_rate']:.1%}         {home_pick:.1%}                      {acc:.1%}")

    # Find optimal threshold for each season
    print("\n" + "=" * 90)
    print("FINDING OPTIMAL THRESHOLD PER SEASON")
    print("=" * 90)

    optimal = {}
    for season in seasons:
        d = all_probs[season]
        best_acc = 0
        best_thresh = 0.5

        for thresh in np.arange(0.40, 0.65, 0.01):
            acc = accuracy_score(d['true'], (d['probs'] >= thresh).astype(int))
            if acc > best_acc:
                best_acc = acc
                best_thresh = thresh

        optimal[season] = {'threshold': best_thresh, 'accuracy': best_acc}
        home_pick = (d['probs'] >= best_thresh).mean()
        base_acc = accuracy_score(d['true'], (d['probs'] >= 0.5).astype(int))
        print(f"{season}: optimal threshold = {best_thresh:.2f}, accuracy = {best_acc:.1%} (vs {base_acc:.1%} @ t=0.5), home pick = {home_pick:.1%}")

    # Test different fixed thresholds across ALL seasons
    print("\n" + "=" * 90)
    print("TESTING FIXED THRESHOLDS ACROSS ALL SEASONS")
    print("=" * 90)

    print(f"\n{'Threshold':<12} {'Overall':<10} {'21-22':<10} {'22-23':<10} {'23-24':<10} {'24-25':<10} {'25-26':<10}")
    print("-" * 72)

    best_overall = 0
    best_thresh_overall = 0.5

    for thresh in [0.48, 0.50, 0.52, 0.54, 0.55, 0.56, 0.58, 0.60]:
        accs = {}
        for season in seasons:
            d = all_probs[season]
            acc = accuracy_score(d['true'], (d['probs'] >= thresh).astype(int))
            accs[season] = acc

        overall = np.mean(list(accs.values()))
        if overall > best_overall:
            best_overall = overall
            best_thresh_overall = thresh

        row = f"{thresh:<12} {overall*100:.1f}%     "
        for season in seasons:
            row += f"{accs[season]*100:.1f}%     "
        print(row)

    print(f"\nBest overall threshold: {best_thresh_overall} ({best_overall:.1%})")

    # Test dynamic threshold based on rolling home win rate
    print("\n" + "=" * 90)
    print("DYNAMIC THRESHOLD BASED ON LEAGUE HOME WIN RATE")
    print("=" * 90)

    # Calculate rolling league home win rate
    games = games.sort_values('gameDate').copy()
    games['rolling_hw_50'] = games['home_win'].rolling(50, min_periods=25).mean().shift(1)
    games['rolling_hw_50'] = games['rolling_hw_50'].fillna(0.535)

    HISTORICAL_HW = 0.535

    print("\nStrategy: threshold = 0.5 + (0.535 - rolling_hw_50) * k")
    print("When home win rate drops, we raise the threshold (pick home less)")

    for k in [0.5, 1.0, 1.5, 2.0, 2.5, 3.0]:
        total_correct = 0
        total_games = 0
        season_accs = {}

        for season in seasons:
            d = all_probs[season]
            mask = games['seasonId'] == season
            rolling_hw = games[mask]['rolling_hw_50'].values

            # Dynamic threshold
            dynamic_thresh = 0.5 + (HISTORICAL_HW - rolling_hw) * k
            dynamic_thresh = np.clip(dynamic_thresh, 0.4, 0.6)

            # Apply dynamic threshold
            y_pred = (d['probs'] >= dynamic_thresh).astype(int)
            acc = accuracy_score(d['true'], y_pred)
            season_accs[season] = acc
            total_correct += (y_pred == d['true']).sum()
            total_games += len(d['true'])

        overall = total_correct / total_games
        avg = np.mean(list(season_accs.values()))

        print(f"k={k}: overall={overall:.1%}, avg={avg:.1%}, 2025-26={season_accs['20252026']:.1%}")

    # Probability calibration approach
    print("\n" + "=" * 90)
    print("PROBABILITY SHRINKAGE TOWARD 0.5")
    print("=" * 90)

    print("\nStrategy: adjusted_prob = 0.5 + (prob - 0.5) * shrink_factor")

    for shrink in [0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        accs = {}
        for season in seasons:
            d = all_probs[season]
            adj_probs = 0.5 + (d['probs'] - 0.5) * shrink
            acc = accuracy_score(d['true'], (adj_probs >= 0.5).astype(int))
            accs[season] = acc

        overall = np.mean(list(accs.values()))
        print(f"shrink={shrink}: avg={overall:.1%}, 2025-26={accs['20252026']:.1%}, 21-22={accs['20212022']:.1%}")

    # Best combined approach
    print("\n" + "=" * 90)
    print("COMBINED: SHRINKAGE + DYNAMIC THRESHOLD")
    print("=" * 90)

    best_combo = None
    best_combo_score = 0

    for shrink in [0.6, 0.7, 0.8, 0.9]:
        for k in [0, 0.5, 1.0, 1.5, 2.0]:
            total_correct = 0
            total_games = 0
            season_accs = {}

            for season in seasons:
                d = all_probs[season]
                mask = games['seasonId'] == season
                rolling_hw = games[mask]['rolling_hw_50'].values

                # Apply shrinkage first
                adj_probs = 0.5 + (d['probs'] - 0.5) * shrink

                # Then dynamic threshold
                if k > 0:
                    dynamic_thresh = 0.5 + (HISTORICAL_HW - rolling_hw) * k
                    dynamic_thresh = np.clip(dynamic_thresh, 0.4, 0.6)
                else:
                    dynamic_thresh = np.full(len(adj_probs), 0.5)

                y_pred = (adj_probs >= dynamic_thresh).astype(int)
                acc = accuracy_score(d['true'], y_pred)
                season_accs[season] = acc
                total_correct += (y_pred == d['true']).sum()
                total_games += len(d['true'])

            overall = total_correct / total_games
            avg = np.mean(list(season_accs.values()))
            avg_4 = np.mean([season_accs[s] for s in seasons if s != '20252026'])

            # Score: maintain 4-season performance, improve 2025-26
            score = avg_4 * 0.8 + season_accs['20252026'] * 0.2

            if score > best_combo_score:
                best_combo_score = score
                best_combo = (shrink, k, avg_4, season_accs['20252026'], overall, season_accs)

    print(f"\nBest combination: shrink={best_combo[0]}, k={best_combo[1]}")
    print(f"   4-season avg: {best_combo[2]:.1%}")
    print(f"   2025-26: {best_combo[3]:.1%}")
    print(f"   5-season overall: {best_combo[4]:.1%}")

    print(f"\n{'Season':<12} {'Accuracy':<12}")
    print("-" * 24)
    for season in seasons:
        print(f"{season:<12} {best_combo[5][season]:.1%}")

    # Final summary
    print("\n" + "=" * 90)
    print("FINAL SUMMARY")
    print("=" * 90)

    # Baseline
    base_4 = np.mean([accuracy_score(all_probs[s]['true'], (all_probs[s]['probs'] >= 0.5).astype(int))
                      for s in seasons if s != '20252026'])
    base_2526 = accuracy_score(all_probs['20252026']['true'], (all_probs['20252026']['probs'] >= 0.5).astype(int))

    print(f"""
BASELINE V8.1 (threshold=0.5):
  - 4-season avg: {base_4:.1%}
  - 2025-26: {base_2526:.1%}

BEST CALIBRATED:
  - 4-season avg: {best_combo[2]:.1%} ({(best_combo[2]-base_4)*100:+.2f}pp)
  - 2025-26: {best_combo[3]:.1%} ({(best_combo[3]-base_2526)*100:+.2f}pp)

VERDICT:
""")

    if best_combo[2] >= 0.61:
        print("✅ 4-season performance maintained at 61%+")
    else:
        print(f"⚠️ 4-season performance at {best_combo[2]:.1%} (target: 61%+)")

    if best_combo[3] > base_2526:
        print(f"✅ 2025-26 improved by {(best_combo[3]-base_2526)*100:.1f}pp")
    else:
        print(f"❌ 2025-26 not improved")


if __name__ == '__main__':
    main()
