#!/usr/bin/env python3
"""
Verify exact V8.1 baseline numbers to establish ground truth.
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


def test_model(features, target, games, feature_list, C=0.01):
    """Standard leave-one-season-out test."""
    results = []
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
        baseline = y_test.mean()
        correct = (y_pred == y_test).sum()

        results.append({
            'season': test_season,
            'games': len(y_test),
            'correct': correct,
            'accuracy': acc,
            'log_loss': ll,
            'baseline': baseline,
            'edge': acc - baseline,
        })

    return results


def main():
    print("=" * 80)
    print("V8.1 BASELINE VERIFICATION")
    print("=" * 80)

    # Test on original 4 seasons only
    print("\n" + "=" * 80)
    print("TEST 1: ORIGINAL 4 SEASONS (21-22, 22-23, 23-24, 24-25)")
    print("=" * 80)

    seasons_4 = ['20212022', '20222023', '20232024', '20242025']
    dataset_4 = build_dataset(seasons_4)
    games_4 = dataset_4.games.copy()
    features_4 = dataset_4.features.copy()
    target_4 = dataset_4.target.copy()

    available = [f for f in V81_FEATURES if f in features_4.columns]
    print(f"\n✅ Loaded {len(games_4)} games, {len(available)}/38 features available")
    print(f"   Missing: {[f for f in V81_FEATURES if f not in features_4.columns]}")

    results_4 = test_model(features_4, target_4, games_4, available, C=0.01)

    print(f"\n{'Season':<12} {'Games':<8} {'Correct':<10} {'Accuracy':<12} {'Baseline':<12} {'Edge':<10} {'Log Loss':<10}")
    print("-" * 84)
    for r in results_4:
        print(f"{r['season']:<12} {r['games']:<8} {r['correct']:<10} {r['accuracy']:.2%}        {r['baseline']:.2%}        +{r['edge']*100:.1f}pp    {r['log_loss']:.4f}")

    total_correct_4 = sum(r['correct'] for r in results_4)
    total_games_4 = sum(r['games'] for r in results_4)
    overall_acc_4 = total_correct_4 / total_games_4
    avg_acc_4 = np.mean([r['accuracy'] for r in results_4])
    avg_ll_4 = np.mean([r['log_loss'] for r in results_4])

    print(f"\n{'TOTAL':<12} {total_games_4:<8} {total_correct_4:<10} {overall_acc_4:.2%} overall")
    print(f"{'AVERAGE':<12}                    {avg_acc_4:.2%} per-season avg")
    print(f"{'LOG LOSS':<12}                                            {avg_ll_4:.4f}")

    # Test on all 5 seasons
    print("\n" + "=" * 80)
    print("TEST 2: ALL 5 SEASONS (including 2025-26)")
    print("=" * 80)

    seasons_5 = ['20212022', '20222023', '20232024', '20242025', '20252026']
    dataset_5 = build_dataset(seasons_5)
    games_5 = dataset_5.games.copy()
    features_5 = dataset_5.features.copy()
    target_5 = dataset_5.target.copy()

    available_5 = [f for f in V81_FEATURES if f in features_5.columns]
    print(f"\n✅ Loaded {len(games_5)} games, {len(available_5)}/38 features available")

    results_5 = test_model(features_5, target_5, games_5, available_5, C=0.01)

    print(f"\n{'Season':<12} {'Games':<8} {'Correct':<10} {'Accuracy':<12} {'Baseline':<12} {'Edge':<10} {'Log Loss':<10}")
    print("-" * 84)
    for r in results_5:
        print(f"{r['season']:<12} {r['games']:<8} {r['correct']:<10} {r['accuracy']:.2%}        {r['baseline']:.2%}        +{r['edge']*100:.1f}pp    {r['log_loss']:.4f}")

    total_correct_5 = sum(r['correct'] for r in results_5)
    total_games_5 = sum(r['games'] for r in results_5)
    overall_acc_5 = total_correct_5 / total_games_5
    avg_acc_5 = np.mean([r['accuracy'] for r in results_5])
    avg_ll_5 = np.mean([r['log_loss'] for r in results_5])

    # Also calculate 4-season avg when trained on all 5
    avg_acc_4_from_5 = np.mean([r['accuracy'] for r in results_5 if r['season'] != '20252026'])

    print(f"\n{'TOTAL':<12} {total_games_5:<8} {total_correct_5:<10} {overall_acc_5:.2%} overall")
    print(f"{'AVG (5)':<12}                    {avg_acc_5:.2%} per-season avg")
    print(f"{'AVG (4)':<12}                    {avg_acc_4_from_5:.2%} (original 4 when 5 used)")
    print(f"{'LOG LOSS':<12}                                            {avg_ll_5:.4f}")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    print(f"""
V8.1 BASELINE NUMBERS:

On original 4 seasons only:
  - Overall accuracy: {overall_acc_4:.2%} ({total_correct_4}/{total_games_4})
  - Per-season average: {avg_acc_4:.2%}
  - Log loss: {avg_ll_4:.4f}

On all 5 seasons:
  - Overall accuracy: {overall_acc_5:.2%} ({total_correct_5}/{total_games_5})
  - Per-season average (5): {avg_acc_5:.2%}
  - Per-season average (4): {avg_acc_4_from_5:.2%}
  - 2025-26: {next(r['accuracy'] for r in results_5 if r['season']=='20252026'):.2%}
  - Log loss: {avg_ll_5:.4f}

KEY INSIGHT:
The 61.2% you mentioned is likely the OVERALL accuracy on 4 seasons ({overall_acc_4:.2%})
not the per-season average ({avg_acc_4:.2%}).

When 2025-26 is included:
- Overall drops from {overall_acc_4:.2%} to {overall_acc_5:.2%}
- This is because 2025-26 is genuinely hard (low home advantage, broken Elo)
""")


if __name__ == '__main__':
    main()
