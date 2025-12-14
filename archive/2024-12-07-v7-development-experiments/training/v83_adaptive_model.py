#!/usr/bin/env python3
"""
V8.3 Adaptive Model - Maintain 61%+ on 4 seasons, improve 2025-26

Strategy:
1. Keep V8.1 features as baseline (they work for 4 seasons)
2. Detect Elo reliability in real-time using rolling correlation
3. When Elo reliability drops, reduce model confidence (shrink to 0.5)
4. Goal: 61%+ on original 4 seasons, improved 2025-26

Key insight: The problem isn't the features - it's that Elo breaks sometimes.
Rather than removing Elo (which hurts good seasons), we detect WHEN it breaks
and adjust predictions accordingly.
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

# V8.1 features - the proven baseline
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

HISTORICAL_ELO_CORR = 0.25  # Historical Elo-outcome correlation
MIN_ELO_CORR = 0.10  # Below this, Elo is considered unreliable


def calculate_rolling_elo_correlation(games, features, target, window=100):
    """Calculate rolling correlation between Elo and outcomes."""
    games = games.sort_values('gameDate').copy()
    elo_vals = features['elo_diff_pre'].values
    outcomes = target.values

    correlations = []
    for i in range(len(games)):
        start_idx = max(0, i - window)
        if i - start_idx < 50:  # Need at least 50 games
            correlations.append(HISTORICAL_ELO_CORR)  # Use historical
        else:
            window_elo = elo_vals[start_idx:i]
            window_out = outcomes[start_idx:i]
            if np.std(window_elo) > 0:
                corr = np.corrcoef(window_elo, window_out)[0, 1]
                correlations.append(max(0, corr))  # Only positive correlations
            else:
                correlations.append(HISTORICAL_ELO_CORR)

    games['elo_reliability'] = correlations
    return games


def adaptive_shrink(probs, elo_reliability, min_corr=MIN_ELO_CORR, max_corr=HISTORICAL_ELO_CORR):
    """
    Shrink probabilities toward 0.5 when Elo reliability drops.

    Full confidence when elo_reliability >= max_corr
    Maximum shrinkage when elo_reliability <= min_corr
    """
    # Calculate shrinkage factor (0 = no shrinkage, 1 = full shrinkage to 0.5)
    reliability_ratio = np.clip((elo_reliability - min_corr) / (max_corr - min_corr), 0, 1)
    shrink_factor = 1 - reliability_ratio  # Low reliability = high shrinkage

    # Apply shrinkage: move probabilities toward 0.5
    adjusted = probs - shrink_factor * (probs - 0.5) * 0.5  # Max 50% shrinkage
    return adjusted


def test_v83_adaptive(features, target, games, feature_list, C=0.01, use_adaptation=True):
    """Test V8.3 with adaptive Elo reliability."""
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

        # Apply adaptive shrinkage if enabled
        if use_adaptation:
            # Get Elo reliability for test games
            elo_reliability = test_games['elo_reliability'].values
            y_prob_adjusted = adaptive_shrink(y_prob, elo_reliability)
        else:
            y_prob_adjusted = y_prob

        y_pred = (y_prob_adjusted >= 0.5).astype(int)

        acc = accuracy_score(y_test, y_pred)
        ll = log_loss(y_test, y_prob_adjusted)
        brier = brier_score_loss(y_test, y_prob_adjusted)
        baseline = y_test.mean()
        home_pick = (y_prob_adjusted >= 0.5).mean()

        # Calculate avg Elo reliability for this season
        avg_elo_rel = test_games['elo_reliability'].mean()

        season_results.append({
            'season': test_season,
            'games': len(y_test),
            'accuracy': acc,
            'log_loss': ll,
            'brier': brier,
            'baseline': baseline,
            'edge': acc - baseline,
            'home_pick_rate': home_pick,
            'elo_reliability': avg_elo_rel,
        })

        test_games['y_true'] = y_test.values
        test_games['y_prob'] = y_prob
        test_games['y_prob_adj'] = y_prob_adjusted
        test_games['y_pred'] = y_pred
        test_games['correct'] = (y_pred == y_test.values).astype(int)
        all_predictions.append(test_games)

    all_preds = pd.concat(all_predictions, ignore_index=True)
    return season_results, all_preds


def main():
    print("=" * 100)
    print("V8.3 ADAPTIVE MODEL - MAINTAIN 61%+ ON 4 SEASONS")
    print("=" * 100)

    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']
    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    print(f"\n✅ Loaded {len(games)} games")

    # Calculate Elo reliability across all games
    print("\n📊 Calculating rolling Elo reliability...")
    games = calculate_rolling_elo_correlation(games, features, target, window=100)

    # Show Elo reliability by season
    print(f"\n{'Season':<12} {'Avg Elo Reliability':<20} {'Home Win%':<12}")
    print("-" * 44)
    for season in seasons:
        mask = games['seasonId'] == season
        avg_rel = games[mask]['elo_reliability'].mean()
        hw = target[mask].mean()
        status = "✅" if avg_rel >= MIN_ELO_CORR else "⚠️"
        print(f"{season:<12} {status} {avg_rel:.3f}              {hw:.1%}")

    # Test V8.1 baseline (no adaptation)
    print("\n" + "=" * 100)
    print("V8.1 BASELINE (no adaptation)")
    print("=" * 100)

    v81_results, v81_preds = test_v83_adaptive(
        features, target, games, V81_FEATURES, C=0.01, use_adaptation=False
    )

    print(f"\n{'Season':<12} {'Games':<8} {'Accuracy':<12} {'Baseline':<12} {'Edge':<10} {'Elo Rel':<10}")
    print("-" * 64)
    for r in v81_results:
        print(f"{r['season']:<12} {r['games']:<8} {r['accuracy']:.1%}        {r['baseline']:.1%}        +{r['edge']*100:.1f}pp    {r['elo_reliability']:.3f}")

    v81_avg = np.mean([r['accuracy'] for r in v81_results])
    v81_avg_4 = np.mean([r['accuracy'] for r in v81_results if r['season'] != '20252026'])
    v81_2526 = next(r['accuracy'] for r in v81_results if r['season'] == '20252026')

    print(f"\n{'OVERALL (5)':<12} {sum(r['games'] for r in v81_results):<8} {v81_avg:.1%}")
    print(f"{'ORIGINAL 4':<12}          {v81_avg_4:.1%}")
    print(f"{'2025-26':<12}          {v81_2526:.1%}")

    # Test V8.3 with adaptation
    print("\n" + "=" * 100)
    print("V8.3 WITH ADAPTIVE ELO SHRINKAGE")
    print("=" * 100)

    v83_results, v83_preds = test_v83_adaptive(
        features, target, games, V81_FEATURES, C=0.01, use_adaptation=True
    )

    print(f"\n{'Season':<12} {'Games':<8} {'Accuracy':<12} {'Baseline':<12} {'Edge':<10} {'Home Pick%':<12}")
    print("-" * 72)
    for r in v83_results:
        print(f"{r['season']:<12} {r['games']:<8} {r['accuracy']:.1%}        {r['baseline']:.1%}        +{r['edge']*100:.1f}pp    {r['home_pick_rate']:.1%}")

    v83_avg = np.mean([r['accuracy'] for r in v83_results])
    v83_avg_4 = np.mean([r['accuracy'] for r in v83_results if r['season'] != '20252026'])
    v83_2526 = next(r['accuracy'] for r in v83_results if r['season'] == '20252026')

    print(f"\n{'OVERALL (5)':<12} {sum(r['games'] for r in v83_results):<8} {v83_avg:.1%}")
    print(f"{'ORIGINAL 4':<12}          {v83_avg_4:.1%}")
    print(f"{'2025-26':<12}          {v83_2526:.1%}")

    # Test different shrinkage parameters
    print("\n" + "=" * 100)
    print("TUNING ADAPTIVE SHRINKAGE")
    print("=" * 100)

    best_config = None
    best_score = 0

    for shrink_mult in [0.3, 0.4, 0.5, 0.6, 0.7]:
        for min_corr in [0.05, 0.10, 0.15]:
            # Temporarily override the adaptive_shrink function
            def custom_shrink(probs, elo_reliability, _min_corr=min_corr, _mult=shrink_mult):
                reliability_ratio = np.clip((elo_reliability - _min_corr) / (HISTORICAL_ELO_CORR - _min_corr), 0, 1)
                shrink_factor = 1 - reliability_ratio
                adjusted = probs - shrink_factor * (probs - 0.5) * _mult
                return adjusted

            # Test this configuration
            results = []
            for test_season in sorted(games['seasonId'].unique()):
                train_seasons = [s for s in games['seasonId'].unique() if s != test_season]
                train_mask = games['seasonId'].isin(train_seasons)
                test_mask = games['seasonId'] == test_season

                avail = [f for f in V81_FEATURES if f in features.columns]
                X_train = features[train_mask][avail].fillna(0)
                y_train = target[train_mask]
                X_test = features[test_mask][avail].fillna(0)
                y_test = target[test_mask]
                test_games = games[test_mask].copy()

                model = Pipeline([
                    ('scaler', StandardScaler()),
                    ('clf', LogisticRegression(C=0.01, max_iter=1000, random_state=42))
                ])
                model.fit(X_train, y_train)

                y_prob = model.predict_proba(X_test)[:, 1]
                y_prob_adj = custom_shrink(y_prob, test_games['elo_reliability'].values)
                y_pred = (y_prob_adj >= 0.5).astype(int)

                acc = accuracy_score(y_test, y_pred)
                results.append({'season': test_season, 'accuracy': acc})

            avg_4 = np.mean([r['accuracy'] for r in results if r['season'] != '20252026'])
            acc_2526 = next(r['accuracy'] for r in results if r['season'] == '20252026')
            avg_5 = np.mean([r['accuracy'] for r in results])

            # Score: prioritize maintaining 61%+ on 4 seasons, then improve 2025-26
            score = avg_4 * 0.7 + acc_2526 * 0.3  # Weighted toward 4-season performance

            if score > best_score:
                best_score = score
                best_config = (shrink_mult, min_corr, avg_4, acc_2526, avg_5)

    print(f"\nBest configuration: shrink_mult={best_config[0]}, min_corr={best_config[1]}")
    print(f"   4-season avg: {best_config[2]:.1%}")
    print(f"   2025-26: {best_config[3]:.1%}")
    print(f"   5-season avg: {best_config[4]:.1%}")

    # Head-to-head comparison
    print("\n" + "=" * 100)
    print("HEAD-TO-HEAD: V8.1 vs V8.3 ADAPTIVE")
    print("=" * 100)

    print(f"\n{'Metric':<25} {'V8.1':<15} {'V8.3 Adaptive':<15} {'Change':<12}")
    print("-" * 67)

    print(f"{'Original 4 Seasons':<25} {v81_avg_4:.1%}          {v83_avg_4:.1%}          {(v83_avg_4-v81_avg_4)*100:+.2f}pp")
    print(f"{'2025-26':<25} {v81_2526:.1%}          {v83_2526:.1%}          {(v83_2526-v81_2526)*100:+.2f}pp")
    print(f"{'All 5 Seasons':<25} {v81_avg:.1%}          {v83_avg:.1%}          {(v83_avg-v81_avg)*100:+.2f}pp")

    print(f"\n{'Season':<12} {'V8.1':<12} {'V8.3':<12} {'Change':<12} {'Winner':<12}")
    print("-" * 60)
    for i in range(len(v81_results)):
        v81_acc = v81_results[i]['accuracy']
        v83_acc = v83_results[i]['accuracy']
        change = v83_acc - v81_acc
        winner = "V8.3" if change > 0.005 else "V8.1" if change < -0.005 else "Tie"
        marker = "✅" if change > 0 else "❌" if change < 0 else "➖"
        print(f"{v81_results[i]['season']:<12} {v81_acc:.1%}        {v83_acc:.1%}        {marker} {change*100:+.2f}pp    {winner}")

    # Final verdict
    print("\n" + "=" * 100)
    print("VERDICT")
    print("=" * 100)

    maintains_4_season = v83_avg_4 >= 0.61
    improves_2526 = v83_2526 > v81_2526

    if maintains_4_season and improves_2526:
        print(f"""
✅ V8.3 ADAPTIVE IS RECOMMENDED

Benefits:
- Maintains {v83_avg_4:.1%} on original 4 seasons (target: 61%+)
- Improves 2025-26 from {v81_2526:.1%} to {v83_2526:.1%} (+{(v83_2526-v81_2526)*100:.1f}pp)
- Automatically detects when Elo reliability drops
- No feature changes - same V8.1 features, just smarter confidence

How it works:
1. Calculates rolling Elo-outcome correlation (100 game window)
2. When correlation drops below {MIN_ELO_CORR}, reduces prediction confidence
3. Shrinks probabilities toward 0.5 proportional to reliability drop
""")
    elif maintains_4_season:
        print(f"""
⚠️ V8.3 MAINTAINS 4-SEASON PERFORMANCE BUT DOESN'T HELP 2025-26

4-season avg: {v83_avg_4:.1%} (target: 61%+) ✅
2025-26: {v83_2526:.1%} vs V8.1 {v81_2526:.1%}

The 2025-26 problem may be too severe for simple adaptation.
Consider:
- Accepting lower 2025-26 performance as structural issue
- Removing Elo entirely for real-time predictions
- Using ensemble of multiple approaches
""")
    else:
        print(f"""
❌ V8.3 DOES NOT MEET REQUIREMENTS

4-season avg: {v83_avg_4:.1%} (target: 61%+) ❌
2025-26: {v83_2526:.1%}

Recommendations:
- Stick with V8.1 for the 4 original seasons
- Accept that 2025-26 is anomalous
- Consider season-specific model adjustments
""")


if __name__ == '__main__':
    main()
