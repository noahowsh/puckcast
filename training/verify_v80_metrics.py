#!/usr/bin/env python3
"""
V8.0 Comprehensive Metric Verification

This script performs rigorous backtesting to verify ALL V8.0 model metrics.
Uses exact production configuration: 35 curated features, improved Elo.

Output:
- Overall accuracy, log loss, brier score
- Season-by-season breakdown
- Confidence bucket performance (A+, A, B+, B, C+, C)
- Strategy receipts

Usage:
    python training/verify_v80_metrics.py
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

# V8.0 Curated Features (35 features - removed goalie_rest_days_diff)
V80_FEATURES = [
    # Elo ratings (improved with season carryover)
    'elo_diff_pre', 'elo_expectation_home',

    # Rolling win percentage
    'rolling_win_pct_10_diff', 'rolling_win_pct_5_diff', 'rolling_win_pct_3_diff',

    # Rolling goal differential
    'rolling_goal_diff_10_diff', 'rolling_goal_diff_5_diff', 'rolling_goal_diff_3_diff',

    # Rolling xG differential
    'rolling_xg_diff_10_diff', 'rolling_xg_diff_5_diff', 'rolling_xg_diff_3_diff',

    # Possession metrics (improving over time)
    'rolling_corsi_10_diff', 'rolling_corsi_5_diff', 'rolling_corsi_3_diff',
    'rolling_fenwick_10_diff', 'rolling_fenwick_5_diff',

    # Season-level stats
    'season_win_pct_diff', 'season_goal_diff_avg_diff',
    'season_xg_diff_avg_diff', 'season_shot_margin_diff',

    # Rest and schedule
    'rest_diff', 'is_b2b_home', 'is_b2b_away',
    'games_last_6d_home',

    # Goaltending (removed goalie_rest_days_diff)
    'rolling_save_pct_10_diff', 'rolling_save_pct_5_diff', 'rolling_save_pct_3_diff',
    'rolling_gsax_5_diff', 'rolling_gsax_10_diff',
    'goalie_trend_score_diff',

    # Momentum
    'momentum_win_pct_diff', 'momentum_goal_diff_diff', 'momentum_xg_diff',

    # High danger shots
    'rolling_high_danger_shots_5_diff', 'rolling_high_danger_shots_10_diff',
]


def grade_from_edge(edge_value: float) -> str:
    """Map edge to confidence grade."""
    edge_pts = abs(edge_value) * 100
    if edge_pts >= 25:
        return "A+"
    if edge_pts >= 20:
        return "A"
    if edge_pts >= 15:
        return "B+"
    if edge_pts >= 10:
        return "B"
    if edge_pts >= 5:
        return "C+"
    return "C"


def run_verification():
    print("=" * 80)
    print("V8.0 COMPREHENSIVE METRIC VERIFICATION")
    print("=" * 80)

    # Load all seasons for testing
    seasons = ['20212022', '20222023', '20232024', '20242025']
    print(f"\n📊 Loading data for seasons: {', '.join(seasons)}")

    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    # Filter to V8.0 features
    available_v80 = [f for f in V80_FEATURES if f in features.columns]
    missing = set(V80_FEATURES) - set(available_v80)
    if missing:
        print(f"⚠️  Missing features: {missing}")

    features = features[available_v80]
    print(f"✅ Using {len(available_v80)} V8.0 features")
    print(f"✅ Total games: {len(games)}")

    # Leave-one-season-out validation to test ALL games
    all_predictions = []
    season_results = []

    unique_seasons = sorted(games['seasonId'].unique())
    print(f"\n🔄 Running leave-one-season-out validation...")
    print(f"   Seasons: {unique_seasons}")

    for i, test_season in enumerate(unique_seasons):
        # Train on ALL other seasons
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

        # Train model with C tuning (same as production)
        best_c = 0.01  # Default
        best_score = 0
        for c in [0.005, 0.01, 0.02, 0.05, 0.1, 0.5, 1.0]:
            temp_model = Pipeline([
                ('scaler', StandardScaler()),
                ('clf', LogisticRegression(C=c, max_iter=1000, random_state=42))
            ])
            # Simple cross-val on training data
            from sklearn.model_selection import cross_val_score
            scores = cross_val_score(temp_model, X_train, y_train, cv=3, scoring='accuracy')
            if scores.mean() > best_score:
                best_score = scores.mean()
                best_c = c

        model = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(C=best_c, max_iter=1000, random_state=42))
        ])
        model.fit(X_train, y_train)

        # Predict
        y_pred = model.predict(X_test)
        y_prob = model.predict_proba(X_test)[:, 1]

        # Calculate metrics for this season
        acc = accuracy_score(y_test, y_pred)
        ll = log_loss(y_test, y_prob)
        brier = brier_score_loss(y_test, y_prob)

        season_results.append({
            'season': test_season,
            'games': len(y_test),
            'accuracy': acc,
            'log_loss': ll,
            'brier': brier,
            'train_seasons': len(train_seasons)
        })

        # Store predictions for bucket analysis
        test_games['y_true'] = y_test.values
        test_games['y_prob'] = y_prob
        test_games['y_pred'] = y_pred
        test_games['edge'] = y_prob - 0.5
        test_games['grade'] = test_games['edge'].apply(grade_from_edge)
        test_games['correct'] = (test_games['y_pred'] == test_games['y_true']).astype(int)
        all_predictions.append(test_games)

        print(f"   {test_season}: {acc:.2%} ({len(y_test)} games, trained on {len(train_seasons)} seasons)")

    # Combine all predictions
    all_preds = pd.concat(all_predictions, ignore_index=True)

    print("\n" + "=" * 80)
    print("OVERALL METRICS")
    print("=" * 80)

    overall_acc = all_preds['correct'].mean()
    overall_ll = log_loss(all_preds['y_true'], all_preds['y_prob'])
    overall_brier = brier_score_loss(all_preds['y_true'], all_preds['y_prob'])
    home_win_rate = all_preds['y_true'].mean()

    print(f"\n📈 Overall Results ({len(all_preds)} games):")
    print(f"   Accuracy:     {overall_acc:.4f} ({overall_acc*100:.2f}%)")
    print(f"   Log Loss:     {overall_ll:.4f}")
    print(f"   Brier Score:  {overall_brier:.4f}")
    print(f"   Baseline:     {home_win_rate:.4f} ({home_win_rate*100:.2f}% home win rate)")
    print(f"   Edge:         +{(overall_acc - home_win_rate)*100:.2f} pp vs baseline")

    print("\n" + "=" * 80)
    print("SEASON-BY-SEASON BREAKDOWN")
    print("=" * 80)

    print(f"\n{'Season':<12} {'Games':<8} {'Accuracy':<12} {'Log Loss':<12} {'Brier':<10}")
    print("-" * 54)
    for r in season_results:
        print(f"{r['season']:<12} {r['games']:<8} {r['accuracy']:.2%}        {r['log_loss']:.4f}       {r['brier']:.4f}")

    print("\n" + "=" * 80)
    print("CONFIDENCE BUCKET PERFORMANCE")
    print("=" * 80)

    bucket_results = []
    for grade in ['A+', 'A', 'B+', 'B', 'C+', 'C']:
        grade_mask = all_preds['grade'] == grade
        if grade_mask.sum() == 0:
            continue
        grade_preds = all_preds[grade_mask]
        grade_acc = grade_preds['correct'].mean()
        bucket_results.append({
            'grade': grade,
            'games': len(grade_preds),
            'accuracy': grade_acc,
            'wins': grade_preds['correct'].sum()
        })

    print(f"\n{'Grade':<8} {'Games':<10} {'Wins':<10} {'Accuracy':<12}")
    print("-" * 40)
    for b in bucket_results:
        print(f"{b['grade']:<8} {b['games']:<10} {b['wins']:<10} {b['accuracy']:.2%}")

    # A-tier combined
    a_tier = all_preds[all_preds['grade'].isin(['A+', 'A'])]
    if len(a_tier) > 0:
        print(f"\n{'A-tier':<8} {len(a_tier):<10} {a_tier['correct'].sum():<10} {a_tier['correct'].mean():.2%}")

    print("\n" + "=" * 80)
    print("STRATEGY RECEIPTS (Simulated Flat Betting)")
    print("=" * 80)

    # Simulate flat betting strategies
    strategies = [
        ('A+ only (≥25 pts)', ['A+']),
        ('A-tier (≥20 pts)', ['A+', 'A']),
        ('A + B+ (≥15 pts)', ['A+', 'A', 'B+']),
        ('All predictions', ['A+', 'A', 'B+', 'B', 'C+', 'C']),
    ]

    print(f"\n{'Strategy':<25} {'Bets':<8} {'Wins':<8} {'Win Rate':<12} {'Units':<10}")
    print("-" * 63)

    for name, grades in strategies:
        strat_preds = all_preds[all_preds['grade'].isin(grades)]
        if len(strat_preds) == 0:
            continue
        wins = strat_preds['correct'].sum()
        bets = len(strat_preds)
        win_rate = wins / bets
        # Flat betting: win = +1, lose = -1
        units = wins - (bets - wins)
        print(f"{name:<25} {bets:<8} {wins:<8} {win_rate:.2%}        {units:+.0f}")

    print("\n" + "=" * 80)
    print("VERIFICATION SUMMARY")
    print("=" * 80)

    print(f"""
┌─────────────────────────────────────────────────────────────┐
│ V8.0 MODEL VERIFIED METRICS                                  │
├─────────────────────────────────────────────────────────────┤
│ Overall Accuracy:  {overall_acc:.4f} ({overall_acc*100:.2f}%)                          │
│ Log Loss:          {overall_ll:.4f}                                     │
│ Brier Score:       {overall_brier:.4f}                                     │
│ Baseline:          {home_win_rate:.4f} ({home_win_rate*100:.2f}%)                          │
│ Edge vs Baseline:  +{(overall_acc - home_win_rate)*100:.2f} pp                                  │
│ Total Games:       {len(all_preds)}                                       │
│ Features:          {len(available_v80)}                                         │
├─────────────────────────────────────────────────────────────┤
│ CONFIDENCE BUCKETS                                           │
""")

    for b in bucket_results:
        print(f"│ {b['grade']:<4} {b['accuracy']*100:>6.1f}% ({b['games']:>4} games)                                │")

    print("""└─────────────────────────────────────────────────────────────┘
""")

    # Return data for JSON update
    return {
        'overall': {
            'games': len(all_preds),
            'accuracy': overall_acc,
            'log_loss': overall_ll,
            'brier': overall_brier,
            'baseline': home_win_rate,
        },
        'seasons': season_results,
        'buckets': bucket_results,
    }


if __name__ == '__main__':
    results = run_verification()
