#!/usr/bin/env python3
"""
Elo Full Model Test - Test Elo configurations with FULL V8.1 feature set

This uses the complete pipeline to properly evaluate Elo changes.
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
from typing import Dict, List

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.data_ingest import build_game_dataframe, fetch_multi_season_logs
from nhl_prediction.features import ROLL_WINDOWS, engineer_team_features
from nhl_prediction.pipeline import Dataset

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


def add_elo_features(
    games: pd.DataFrame,
    k_factor: float = 10.0,
    home_advantage: float = 35.0,
    season_carryover: float = 0.5,
    dynamic_home_adv: bool = False,
    home_adv_window: int = 50,
    home_adv_scale: float = 1000.0,
    home_adv_min: float = 0.0,
    home_adv_max: float = 70.0,
) -> pd.DataFrame:
    """Add Elo features with configurable parameters."""
    games = games.sort_values("gameDate").copy()
    base_rating = 1500.0

    elo_home: List[float] = []
    elo_away: List[float] = []
    expected_home_probs: List[float] = []

    current_season = None
    ratings: Dict[int, float] = {}
    prev_season_ratings: Dict[int, float] = {}
    recent_home_wins: List[int] = []

    for _, row in games.iterrows():
        season = row["seasonId"]
        if season != current_season:
            if current_season is not None:
                prev_season_ratings = ratings.copy()
            current_season = season
            if season_carryover > 0 and prev_season_ratings:
                ratings = {
                    team: base_rating + season_carryover * (rating - base_rating)
                    for team, rating in prev_season_ratings.items()
                }
            else:
                ratings = {}

        home_id = int(row["teamId_home"])
        away_id = int(row["teamId_away"])

        home_rating = ratings.get(home_id, base_rating)
        away_rating = ratings.get(away_id, base_rating)

        elo_home.append(home_rating)
        elo_away.append(away_rating)

        # Dynamic home advantage
        if dynamic_home_adv and len(recent_home_wins) >= 25:
            recent_hw_rate = np.mean(recent_home_wins[-home_adv_window:])
            current_home_adv = (recent_hw_rate - 0.5) * home_adv_scale
            current_home_adv = max(home_adv_min, min(home_adv_max, current_home_adv))
        else:
            current_home_adv = home_advantage

        expected_home = 1.0 / (1.0 + 10 ** ((away_rating - (home_rating + current_home_adv)) / 400))
        expected_home_probs.append(expected_home)

        outcome_home = 1.0 if row["home_win"] == 1 else 0.0
        recent_home_wins.append(int(row["home_win"]))

        goal_diff = row["home_score"] - row["away_score"]
        margin = max(abs(goal_diff), 1)
        multiplier = np.log(margin + 1) * (2.2 / ((abs(home_rating - away_rating) * 0.001) + 2.2))
        delta = k_factor * multiplier * (outcome_home - expected_home)

        ratings[home_id] = home_rating + delta
        ratings[away_id] = away_rating - delta

    games["elo_home_pre"] = elo_home
    games["elo_away_pre"] = elo_away
    games["elo_diff_pre"] = games["elo_home_pre"] - games["elo_away_pre"]
    games["elo_expectation_home"] = expected_home_probs
    return games


def build_full_features(games: pd.DataFrame) -> pd.DataFrame:
    """Build full feature matrix like the real pipeline."""
    rolling_windows = ROLL_WINDOWS
    feature_bases = [
        "rolling_win_pct", "rolling_goal_diff", "rolling_xg_diff",
        "rolling_corsi", "rolling_fenwick", "rolling_save_pct",
        "rolling_gsax", "rolling_high_danger_shots"
    ]

    feature_columns = [
        "elo_diff_pre", "elo_expectation_home",
        "rest_diff", "is_b2b_home", "is_b2b_away",
        "season_win_pct_diff", "season_goal_diff_avg_diff",
        "season_xg_diff_avg_diff", "season_shot_margin_diff",
        "games_last_6d_home", "games_last_3d_home",
        "goalie_trend_score_diff",
        "momentum_win_pct_diff", "momentum_goal_diff_diff", "momentum_xg_diff",
        "shotsFor_roll_10_diff", "rolling_faceoff_5_diff",
    ]

    # Add rolling features
    for base in feature_bases:
        for w in rolling_windows:
            col = f"{base}_{w}_diff"
            if col in games.columns:
                feature_columns.append(col)

    available = [c for c in feature_columns if c in games.columns]
    return games[available].copy()


def test_elo_config(games_base, features_base, target, config_name, **elo_params):
    """Test Elo config with full model."""
    # Recompute Elo with new params
    games = add_elo_features(games_base.copy(), **elo_params)

    # Update Elo columns in features
    features = features_base.copy()
    features['elo_diff_pre'] = games['elo_diff_pre'].values
    features['elo_expectation_home'] = games['elo_expectation_home'].values

    results = []
    seasons = sorted(games['seasonId'].unique())
    available = [f for f in V81_FEATURES if f in features.columns]

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

        y_pred = model.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        results.append({'season': test_season, 'accuracy': acc})

    return results


def main():
    print("=" * 90)
    print("ELO FULL MODEL TEST - WITH ALL V8.1 FEATURES")
    print("=" * 90)

    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']

    # Build full dataset with default Elo
    print("\n📊 Building full dataset...")
    raw_logs = fetch_multi_season_logs(seasons)
    enriched_logs = engineer_team_features(raw_logs)
    games_base = build_game_dataframe(enriched_logs)
    games_base = add_elo_features(games_base, dynamic_home_adv=False)  # Default Elo
    target = games_base['home_win'].copy()
    features_base = build_full_features(games_base)

    print(f"✅ Loaded {len(games_base)} games, {len(features_base.columns)} features")

    # Test configurations
    configs = [
        # Baseline
        ("Fixed adv=35 (baseline)", {"home_advantage": 35, "dynamic_home_adv": False}),
        ("Fixed adv=30", {"home_advantage": 30, "dynamic_home_adv": False}),
        ("Fixed adv=25", {"home_advantage": 25, "dynamic_home_adv": False}),
        ("Fixed adv=20", {"home_advantage": 20, "dynamic_home_adv": False}),

        # Dynamic with different parameters
        ("Dynamic w=50 s=1000", {"dynamic_home_adv": True, "home_adv_window": 50, "home_adv_scale": 1000}),
        ("Dynamic w=100 s=1000", {"dynamic_home_adv": True, "home_adv_window": 100, "home_adv_scale": 1000}),
        ("Dynamic w=100 s=700", {"dynamic_home_adv": True, "home_adv_window": 100, "home_adv_scale": 700}),
        ("Dynamic w=100 s=500", {"dynamic_home_adv": True, "home_adv_window": 100, "home_adv_scale": 500}),

        # Conservative dynamic (smaller range)
        ("Conservative dynamic", {"dynamic_home_adv": True, "home_adv_window": 100, "home_adv_scale": 500, "home_adv_min": 15, "home_adv_max": 50}),

        # Adaptive: start high, can go low
        ("Adaptive (15-60)", {"dynamic_home_adv": True, "home_adv_window": 100, "home_adv_scale": 700, "home_adv_min": 15, "home_adv_max": 60}),
    ]

    all_results = {}
    print("\n" + "=" * 90)
    print("TESTING CONFIGURATIONS")
    print("=" * 90)

    for name, params in configs:
        print(f"\n⏳ Testing: {name}...")
        results = test_elo_config(games_base, features_base, target, name, **params)
        all_results[name] = results

        avg_4 = np.mean([r['accuracy'] for r in results if r['season'] != '20252026'])
        acc_2526 = next(r['accuracy'] for r in results if r['season'] == '20252026')
        avg_all = np.mean([r['accuracy'] for r in results])
        print(f"   4-season: {avg_4:.1%}, 2025-26: {acc_2526:.1%}, Overall: {avg_all:.1%}")

    # Full comparison
    print("\n" + "=" * 100)
    print("FULL COMPARISON")
    print("=" * 100)

    print(f"\n{'Configuration':<25} {'4-season':<12} {'21-22':<10} {'22-23':<10} {'23-24':<10} {'24-25':<10} {'25-26':<10}")
    print("-" * 97)

    for name, results in all_results.items():
        accs = {r['season']: r['accuracy'] for r in results}
        avg_4 = np.mean([accs[s] for s in seasons if s != '20252026'])
        row = f"{name:<25} {avg_4*100:.1f}%       "
        for s in seasons:
            row += f"{accs.get(s, 0)*100:.1f}%     "
        print(row)

    # Analysis
    print("\n" + "=" * 80)
    print("ANALYSIS")
    print("=" * 80)

    baseline = all_results["Fixed adv=35 (baseline)"]
    baseline_4 = np.mean([r['accuracy'] for r in baseline if r['season'] != '20252026'])
    baseline_2526 = next(r['accuracy'] for r in baseline if r['season'] == '20252026')

    print(f"\nBaseline (Fixed adv=35): 4-season={baseline_4:.1%}, 2025-26={baseline_2526:.1%}")

    # Find best for each metric
    best_4 = max(all_results.items(), key=lambda x: np.mean([r['accuracy'] for r in x[1] if r['season'] != '20252026']))
    best_2526 = max(all_results.items(), key=lambda x: next(r['accuracy'] for r in x[1] if r['season'] == '20252026'))

    print(f"\nBest 4-season: {best_4[0]} ({np.mean([r['accuracy'] for r in best_4[1] if r['season'] != '20252026'])*100:.1f}%)")
    print(f"Best 2025-26: {best_2526[0]} ({next(r['accuracy'] for r in best_2526[1] if r['season'] == '20252026')*100:.1f}%)")

    # Find best balanced
    best_balanced = None
    best_score = 0

    for name, results in all_results.items():
        avg_4 = np.mean([r['accuracy'] for r in results if r['season'] != '20252026'])
        acc_2526 = next(r['accuracy'] for r in results if r['season'] == '20252026')

        # Score: balance 4-season and 2025-26 improvement
        improvement_4 = avg_4 - baseline_4
        improvement_2526 = acc_2526 - baseline_2526

        # Only consider if doesn't hurt 4-season more than 0.5pp
        if improvement_4 >= -0.005:
            score = improvement_4 + improvement_2526 * 0.5  # Weight 2025-26 improvement
            if score > best_score:
                best_score = score
                best_balanced = (name, avg_4, acc_2526, improvement_4, improvement_2526)

    print("\n" + "=" * 80)
    print("RECOMMENDATION")
    print("=" * 80)

    if best_balanced:
        print(f"""
Best balanced configuration: {best_balanced[0]}
- 4-season: {best_balanced[1]*100:.1f}% ({best_balanced[3]*100:+.2f}pp vs baseline)
- 2025-26: {best_balanced[2]*100:.1f}% ({best_balanced[4]*100:+.2f}pp vs baseline)
""")
    else:
        print("\nNo configuration improves both metrics. Consider sticking with baseline.")


if __name__ == '__main__':
    main()
