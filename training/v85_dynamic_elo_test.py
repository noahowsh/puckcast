#!/usr/bin/env python3
"""
V8.5 Test - Dynamic Elo + Dynamic Threshold Combined

V8.4: Dynamic threshold based on rolling home win rate
V8.5: Dynamic Elo home advantage based on rolling home win rate

This test verifies the combined improvement.
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

# Import after path setup to get updated pipeline
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

HISTORICAL_HW = 0.535
THRESHOLD_K = 0.5


def calculate_dynamic_threshold(league_hw, k=THRESHOLD_K):
    """Calculate dynamic threshold based on rolling home win rate."""
    threshold = 0.5 + (HISTORICAL_HW - league_hw) * k
    return np.clip(threshold, 0.45, 0.55)


def test_model(features, target, games, feature_list, use_dynamic_threshold=False):
    """Test model with leave-one-season-out."""
    results = []
    seasons = sorted(games['seasonId'].unique())

    # Calculate rolling HW for dynamic threshold
    games = games.sort_values('gameDate').copy()
    games['rolling_hw_50'] = games['home_win'].rolling(50, min_periods=25).mean().shift(1)
    games['rolling_hw_50'] = games['rolling_hw_50'].fillna(HISTORICAL_HW)

    for test_season in seasons:
        train_seasons = [s for s in seasons if s != test_season]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        available = [f for f in feature_list if f in features.columns]
        X_train = features[train_mask][available].fillna(0)
        y_train = target[train_mask]
        X_test = features[test_mask][available].fillna(0)
        y_test = target[test_mask]
        test_games = games[test_mask]

        model = Pipeline([
            ('scaler', StandardScaler()),
            ('clf', LogisticRegression(C=0.01, max_iter=1000, random_state=42))
        ])
        model.fit(X_train, y_train)

        y_prob = model.predict_proba(X_test)[:, 1]

        if use_dynamic_threshold:
            rolling_hw = test_games['rolling_hw_50'].values
            dynamic_thresh = calculate_dynamic_threshold(rolling_hw)
            y_pred = (y_prob >= dynamic_thresh).astype(int)
        else:
            y_pred = (y_prob >= 0.5).astype(int)

        acc = accuracy_score(y_test, y_pred)
        results.append({'season': test_season, 'accuracy': acc, 'baseline': y_test.mean()})

    return results


def main():
    print("=" * 90)
    print("V8.5 TEST - DYNAMIC ELO + DYNAMIC THRESHOLD COMBINED")
    print("=" * 90)

    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']

    # Build dataset (now using dynamic Elo)
    print("\n📊 Building dataset with V8.5 dynamic Elo...")
    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    print(f"✅ Loaded {len(games)} games with dynamic Elo")

    # Check Elo correlation
    print("\n" + "=" * 80)
    print("ELO CORRELATION CHECK (V8.5 Dynamic Elo)")
    print("=" * 80)

    print(f"\n{'Season':<12} {'Home Win%':<12} {'Elo Corr':<12} {'When Elo favors home':<22}")
    print("-" * 58)

    for season in seasons:
        mask = games['seasonId'] == season
        hw = target[mask].mean()

        elo_vals = features[mask]['elo_diff_pre'].values
        outcomes = target[mask].values

        if np.std(elo_vals) > 0:
            corr = np.corrcoef(elo_vals, outcomes)[0, 1]
        else:
            corr = 0

        home_favored_mask = elo_vals > 0
        if home_favored_mask.sum() > 0:
            hw_when_favored = outcomes[home_favored_mask].mean()
        else:
            hw_when_favored = 0

        print(f"{season:<12} {hw:.1%}         {corr:+.3f}       Home wins {hw_when_favored:.1%}")

    # Test configurations
    print("\n" + "=" * 80)
    print("MODEL COMPARISON")
    print("=" * 80)

    # V8.1 baseline (fixed threshold)
    print("\n⏳ Testing V8.5 Dynamic Elo + Fixed threshold...")
    results_fixed = test_model(features, target, games, V81_FEATURES, use_dynamic_threshold=False)

    # V8.5 (dynamic Elo + dynamic threshold)
    print("⏳ Testing V8.5 Dynamic Elo + Dynamic threshold...")
    results_dynamic = test_model(features, target, games, V81_FEATURES, use_dynamic_threshold=True)

    # Print results
    print(f"\n{'Season':<12} {'Fixed Thresh':<15} {'Dynamic Thresh':<15} {'Change':<12}")
    print("-" * 54)

    for i, season in enumerate(seasons):
        fixed = results_fixed[i]['accuracy']
        dynamic = results_dynamic[i]['accuracy']
        change = dynamic - fixed
        marker = "✅" if change > 0 else "❌" if change < 0 else "➖"
        print(f"{season:<12} {fixed:.1%}           {dynamic:.1%}           {marker} {change*100:+.2f}pp")

    # Summary
    avg_fixed = np.mean([r['accuracy'] for r in results_fixed])
    avg_dynamic = np.mean([r['accuracy'] for r in results_dynamic])
    avg_4_fixed = np.mean([r['accuracy'] for r in results_fixed if r['season'] != '20252026'])
    avg_4_dynamic = np.mean([r['accuracy'] for r in results_dynamic if r['season'] != '20252026'])
    acc_2526_fixed = next(r['accuracy'] for r in results_fixed if r['season'] == '20252026')
    acc_2526_dynamic = next(r['accuracy'] for r in results_dynamic if r['season'] == '20252026')

    print(f"\n{'Metric':<20} {'Fixed':<15} {'Dynamic':<15} {'Change':<12}")
    print("-" * 62)
    print(f"{'5-season avg':<20} {avg_fixed:.1%}           {avg_dynamic:.1%}           {(avg_dynamic-avg_fixed)*100:+.2f}pp")
    print(f"{'4-season avg':<20} {avg_4_fixed:.1%}           {avg_4_dynamic:.1%}           {(avg_4_dynamic-avg_4_fixed)*100:+.2f}pp")
    print(f"{'2025-26':<20} {acc_2526_fixed:.1%}           {acc_2526_dynamic:.1%}           {(acc_2526_dynamic-acc_2526_fixed)*100:+.2f}pp")

    # Final verdict
    print("\n" + "=" * 80)
    print("V8.5 RESULTS")
    print("=" * 80)

    print(f"""
V8.5 Dynamic Elo Results:

Combined improvements (Dynamic Elo + Dynamic Threshold):
- 4-season average: {avg_4_dynamic:.1%}
- 2025-26: {acc_2526_dynamic:.1%}
- 5-season average: {avg_dynamic:.1%}

Comparison to V8.1 baseline (61.16% on 4 seasons, 53.2% on 2025-26):
- 4-season: {avg_4_fixed:.1%} with dynamic Elo alone
- 4-season: {avg_4_dynamic:.1%} with dynamic Elo + threshold ({(avg_4_dynamic-0.6116)*100:+.1f}pp vs V8.1)
- 2025-26: {acc_2526_dynamic:.1%} ({(acc_2526_dynamic-0.532)*100:+.1f}pp vs V8.1 53.2%)
""")

    if avg_4_dynamic >= 0.61 and acc_2526_dynamic > 0.532:
        print("✅ V8.5 RECOMMENDED: Maintains 61%+ on 4 seasons, improves 2025-26")
    elif acc_2526_dynamic > 0.532:
        print(f"✅ V8.5 improves 2025-26 by {(acc_2526_dynamic-0.532)*100:.1f}pp")
    else:
        print("⚠️ V8.5 shows marginal improvement")


if __name__ == '__main__':
    main()
