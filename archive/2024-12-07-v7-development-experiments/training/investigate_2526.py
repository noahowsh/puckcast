#!/usr/bin/env python3
"""
Investigate the 2025-26 performance discrepancy.

Site shows 58.9% but our tests show 53%. What's going on?
"""

import sys
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score
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
    print("=" * 80)
    print("INVESTIGATING 2025-26 PERFORMANCE DISCREPANCY")
    print("=" * 80)

    # Load all data
    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']
    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    available_v81 = [f for f in V81_FEATURES if f in features.columns]
    features = features[available_v81]

    # Get 2025-26 data
    mask_2526 = games['seasonId'] == '20252026'
    games_2526 = games[mask_2526].copy()

    print(f"\n📊 2025-26 Season Data:")
    print(f"   Total games: {len(games_2526)}")
    print(f"   Date range: {games_2526['gameDate'].min()} to {games_2526['gameDate'].max()}")
    print(f"   Home win rate: {target[mask_2526].mean():.1%}")

    # Sort by date
    games_2526 = games_2526.sort_values('gameDate')

    # Check performance over time
    print(f"\n📅 Performance by Month:")
    games_2526['month'] = pd.to_datetime(games_2526['gameDate']).dt.to_period('M')

    # Train model on all prior seasons (like production)
    train_mask = games['seasonId'].isin(['20212022', '20222023', '20232024', '20242025'])
    X_train = features[train_mask].fillna(0)
    y_train = target[train_mask]

    model = Pipeline([
        ('scaler', StandardScaler()),
        ('clf', LogisticRegression(C=0.01, max_iter=1000, random_state=42))
    ])
    model.fit(X_train, y_train)

    # Predict 2025-26
    X_test = features[mask_2526].fillna(0)
    y_test = target[mask_2526]
    y_prob = model.predict_proba(X_test)[:, 1]
    y_pred = (y_prob >= 0.5).astype(int)

    games_2526['y_true'] = y_test.values
    games_2526['y_prob'] = y_prob
    games_2526['y_pred'] = y_pred
    games_2526['correct'] = (y_pred == y_test.values).astype(int)

    # Monthly breakdown
    monthly = games_2526.groupby('month').agg({
        'correct': ['sum', 'count', 'mean'],
        'y_true': 'mean',  # Home win rate
        'y_prob': lambda x: (x >= 0.5).mean()  # Home pick rate
    }).round(3)

    print(f"\n{'Month':<12} {'Games':<8} {'Correct':<10} {'Accuracy':<12} {'HW Rate':<10} {'Home Pick%':<10}")
    print("-" * 62)

    for month in monthly.index:
        row = monthly.loc[month]
        games_ct = int(row[('correct', 'count')])
        correct_ct = int(row[('correct', 'sum')])
        acc = row[('correct', 'mean')]
        hw_rate = row[('y_true', 'mean')]
        hp_rate = row[('y_prob', '<lambda>')]
        print(f"{str(month):<12} {games_ct:<8} {correct_ct:<10} {acc:.1%}        {hw_rate:.1%}      {hp_rate:.1%}")

    # First 347 games vs all 440
    print(f"\n📊 First 347 games vs All {len(games_2526)} games:")
    games_2526_sorted = games_2526.sort_values('gameDate')
    first_347 = games_2526_sorted.head(347)

    acc_347 = first_347['correct'].mean()
    acc_all = games_2526['correct'].mean()

    print(f"   First 347 games: {acc_347:.1%} accuracy ({first_347['correct'].sum()} correct)")
    print(f"   All {len(games_2526)} games:  {acc_all:.1%} accuracy ({games_2526['correct'].sum()} correct)")

    last_93 = games_2526_sorted.tail(len(games_2526) - 347)
    if len(last_93) > 0:
        acc_last = last_93['correct'].mean()
        print(f"   Last {len(last_93)} games:   {acc_last:.1%} accuracy ({last_93['correct'].sum()} correct)")

    # Home vs Away analysis
    print(f"\n🏠 Home vs Away Prediction Analysis:")
    home_picks = games_2526[games_2526['y_prob'] >= 0.5]
    away_picks = games_2526[games_2526['y_prob'] < 0.5]

    print(f"   Home picks: {len(home_picks)} ({len(home_picks)/len(games_2526):.1%})")
    print(f"   Away picks: {len(away_picks)} ({len(away_picks)/len(games_2526):.1%})")
    print(f"   Actual home wins: {target[mask_2526].sum()} ({target[mask_2526].mean():.1%})")

    if len(home_picks) > 0:
        print(f"   Home pick accuracy: {home_picks['correct'].mean():.1%}")
    if len(away_picks) > 0:
        print(f"   Away pick accuracy: {away_picks['correct'].mean():.1%}")

    # Confidence grade breakdown
    print(f"\n📊 Confidence Grade Breakdown for 2025-26:")

    def grade_from_edge(edge):
        pts = abs(edge) * 100
        if pts >= 25: return "A+"
        if pts >= 20: return "A"
        if pts >= 15: return "B+"
        if pts >= 10: return "B"
        if pts >= 5: return "C+"
        return "C"

    games_2526['edge'] = games_2526['y_prob'] - 0.5
    games_2526['grade'] = games_2526['edge'].apply(grade_from_edge)

    print(f"\n{'Grade':<8} {'Games':<10} {'Correct':<10} {'Accuracy':<12}")
    print("-" * 40)

    for grade in ['A+', 'A', 'B+', 'B', 'C+', 'C']:
        grade_games = games_2526[games_2526['grade'] == grade]
        if len(grade_games) > 0:
            print(f"{grade:<8} {len(grade_games):<10} {grade_games['correct'].sum():<10} {grade_games['correct'].mean():.1%}")

    # Compare to historical seasons
    print(f"\n📊 All Seasons Comparison (Same Model):")
    print(f"\n{'Season':<12} {'Games':<8} {'Accuracy':<12} {'HW Rate':<10} {'Edge':<10}")
    print("-" * 52)

    for season in ['20212022', '20222023', '20232024', '20242025', '20252026']:
        # Train on all OTHER seasons
        other_seasons = [s for s in ['20212022', '20222023', '20232024', '20242025'] if s != season]
        if season == '20252026':
            other_seasons = ['20212022', '20222023', '20232024', '20242025']

        train_m = games['seasonId'].isin(other_seasons)
        test_m = games['seasonId'] == season

        if train_m.sum() == 0 or test_m.sum() == 0:
            continue

        X_tr = features[train_m].fillna(0)
        y_tr = target[train_m]
        X_te = features[test_m].fillna(0)
        y_te = target[test_m]

        mdl = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(C=0.01, max_iter=1000, random_state=42))
        ])
        mdl.fit(X_tr, y_tr)

        y_p = mdl.predict(X_te)
        acc = accuracy_score(y_te, y_p)
        hw = y_te.mean()
        edge = acc - hw

        print(f"{season:<12} {test_m.sum():<8} {acc:.1%}        {hw:.1%}      +{edge*100:.1f}pp")


if __name__ == '__main__':
    main()
