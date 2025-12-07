#!/usr/bin/env python3
"""
Elo Algorithm Tuning - Find optimal parameters for ALL seasons

Problem: Dynamic Elo helps 2025-26 but slightly hurts other seasons.
Goal: Find Elo configuration that works well for ALL seasons.

Hypothesis: The issue might be:
1. The dynamic home advantage window is too short (50 games)
2. The scaling factor is wrong
3. We need season-specific optimization
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


def compute_elo_with_params(
    games: pd.DataFrame,
    base_rating: float = 1500.0,
    k_factor: float = 10.0,
    home_advantage: float = 35.0,
    season_carryover: float = 0.5,
    dynamic_home_adv: bool = False,
    home_adv_window: int = 50,
    home_adv_scale: float = 1000.0,  # Scale factor for converting HW rate to points
    home_adv_min: float = 0.0,
    home_adv_max: float = 70.0,
) -> pd.DataFrame:
    """Compute Elo with configurable parameters."""
    games = games.sort_values("gameDate").copy()
    elo_home: List[float] = []
    elo_away: List[float] = []
    expected_home_probs: List[float] = []

    current_season: str = None
    ratings: Dict[int, float] = {}
    prev_season_ratings: Dict[int, float] = {}
    recent_home_wins: List[int] = []

    for idx, row in games.iterrows():
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


def build_features_from_games(games: pd.DataFrame) -> pd.DataFrame:
    """Build feature matrix from games dataframe."""
    # This is a simplified version - just extract the features we need
    feature_cols = [c for c in games.columns if c in V81_FEATURES or
                    any(base in c for base in ['rolling_', 'season_', 'momentum_', 'rest_', 'is_b2b', 'games_last', 'goalie_'])]

    # For missing features, we'll need to compute them
    # For now, just return what we have
    return games[feature_cols] if feature_cols else pd.DataFrame()


def test_elo_config(games_base, target, config_name, **elo_params):
    """Test a specific Elo configuration."""
    games = compute_elo_with_params(games_base.copy(), **elo_params)

    # Build simple feature set with Elo
    features = games[['elo_diff_pre', 'elo_expectation_home']].copy()

    # Add other available features
    other_features = [c for c in games.columns if c in V81_FEATURES and c not in features.columns]
    for f in other_features:
        features[f] = games[f]

    results = []
    seasons = sorted(games['seasonId'].unique())

    for test_season in seasons:
        train_seasons = [s for s in seasons if s != test_season]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        available = [f for f in features.columns if f in V81_FEATURES]
        X_train = features[train_mask][available].fillna(0)
        y_train = target[train_mask]
        X_test = features[test_mask][available].fillna(0)
        y_test = target[test_mask]

        if len(X_train) == 0 or len(X_test) == 0:
            continue

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
    print("ELO ALGORITHM TUNING - OPTIMIZE FOR ALL SEASONS")
    print("=" * 90)

    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']

    # Load raw data and build games
    print("\n📊 Loading data...")
    raw_logs = fetch_multi_season_logs(seasons)
    enriched_logs = engineer_team_features(raw_logs)
    games_base = build_game_dataframe(enriched_logs)
    target = games_base['home_win'].copy()

    print(f"✅ Loaded {len(games_base)} games")

    # Show season home win rates
    print("\n" + "=" * 60)
    print("SEASON HOME WIN RATES")
    print("=" * 60)

    for season in seasons:
        mask = games_base['seasonId'] == season
        hw = target[mask].mean()
        # Calculate what the "optimal" fixed home advantage would be
        optimal_adv = (hw - 0.5) * 1000  # Using same scale
        print(f"   {season}: {hw:.1%} home wins → optimal ~{optimal_adv:.0f} Elo points")

    # Test different configurations
    print("\n" + "=" * 90)
    print("TESTING ELO CONFIGURATIONS")
    print("=" * 90)

    configs = [
        # Baseline - fixed home advantage
        ("Fixed adv=35 (V8.1)", {"home_advantage": 35, "dynamic_home_adv": False}),
        ("Fixed adv=30", {"home_advantage": 30, "dynamic_home_adv": False}),
        ("Fixed adv=25", {"home_advantage": 25, "dynamic_home_adv": False}),

        # Dynamic with different windows
        ("Dynamic window=50", {"dynamic_home_adv": True, "home_adv_window": 50}),
        ("Dynamic window=100", {"dynamic_home_adv": True, "home_adv_window": 100}),
        ("Dynamic window=200", {"dynamic_home_adv": True, "home_adv_window": 200}),

        # Dynamic with different scales
        ("Dynamic scale=500", {"dynamic_home_adv": True, "home_adv_window": 100, "home_adv_scale": 500}),
        ("Dynamic scale=750", {"dynamic_home_adv": True, "home_adv_window": 100, "home_adv_scale": 750}),
        ("Dynamic scale=1000", {"dynamic_home_adv": True, "home_adv_window": 100, "home_adv_scale": 1000}),

        # Blend: start with fixed, then go dynamic
        ("Blend fixed+dynamic", {"home_advantage": 30, "dynamic_home_adv": True, "home_adv_window": 100, "home_adv_scale": 500}),

        # Different k-factors
        ("k=15, adv=30", {"k_factor": 15, "home_advantage": 30, "dynamic_home_adv": False}),
        ("k=20, adv=30", {"k_factor": 20, "home_advantage": 30, "dynamic_home_adv": False}),

        # Conservative dynamic (smaller adjustments)
        ("Conservative dynamic", {"dynamic_home_adv": True, "home_adv_window": 100, "home_adv_scale": 400, "home_adv_min": 20, "home_adv_max": 50}),
    ]

    all_results = {}

    for name, params in configs:
        print(f"\n⏳ Testing: {name}...")
        results = test_elo_config(games_base, target, name, **params)
        all_results[name] = results

        avg = np.mean([r['accuracy'] for r in results])
        avg_4 = np.mean([r['accuracy'] for r in results if r['season'] != '20252026'])
        acc_2526 = next((r['accuracy'] for r in results if r['season'] == '20252026'), 0)
        print(f"   4-season: {avg_4:.1%}, 2025-26: {acc_2526:.1%}, Overall: {avg:.1%}")

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

    # Find best configurations
    print("\n" + "=" * 80)
    print("BEST CONFIGURATIONS")
    print("=" * 80)

    # Best 4-season
    best_4 = max(all_results.items(), key=lambda x: np.mean([r['accuracy'] for r in x[1] if r['season'] != '20252026']))
    avg_4 = np.mean([r['accuracy'] for r in best_4[1] if r['season'] != '20252026'])
    print(f"\n✅ Best 4-season: {best_4[0]} ({avg_4*100:.1f}%)")

    # Best 2025-26
    best_2526 = max(all_results.items(), key=lambda x: next((r['accuracy'] for r in x[1] if r['season'] == '20252026'), 0))
    acc_2526 = next(r['accuracy'] for r in best_2526[1] if r['season'] == '20252026')
    print(f"✅ Best 2025-26: {best_2526[0]} ({acc_2526*100:.1%})")

    # Best overall
    best_overall = max(all_results.items(), key=lambda x: np.mean([r['accuracy'] for r in x[1]]))
    avg_all = np.mean([r['accuracy'] for r in best_overall[1]])
    print(f"✅ Best overall: {best_overall[0]} ({avg_all*100:.1f}%)")

    # Best balanced (maximize 4-season while keeping 2025-26 above baseline)
    baseline_2526 = next(r['accuracy'] for r in all_results["Fixed adv=35 (V8.1)"] if r['season'] == '20252026')

    best_balanced = None
    best_balanced_score = 0
    for name, results in all_results.items():
        acc_2526 = next((r['accuracy'] for r in results if r['season'] == '20252026'), 0)
        avg_4 = np.mean([r['accuracy'] for r in results if r['season'] != '20252026'])

        # Only consider if 2025-26 is at least as good as baseline
        if acc_2526 >= baseline_2526:
            score = avg_4
            if score > best_balanced_score:
                best_balanced_score = score
                best_balanced = (name, avg_4, acc_2526)

    if best_balanced:
        print(f"✅ Best balanced: {best_balanced[0]} (4-season: {best_balanced[1]*100:.1f}%, 2025-26: {best_balanced[2]*100:.1f}%)")

    # Summary
    print("\n" + "=" * 80)
    print("RECOMMENDATIONS")
    print("=" * 80)

    baseline_4 = np.mean([r['accuracy'] for r in all_results["Fixed adv=35 (V8.1)"] if r['season'] != '20252026'])

    print(f"""
BASELINE (Fixed adv=35):
- 4-season: {baseline_4*100:.1f}%
- 2025-26: {baseline_2526*100:.1f}%

ANALYSIS:
The dynamic Elo helps 2025-26 because it adapts to the lower home win rate.
However, it slightly hurts other seasons because:
1. The window (50-100 games) causes lag in adaptation
2. Historical seasons had different home win rates that don't match "optimal"
3. The scale factor may be too aggressive

BEST APPROACH:
""")

    if best_balanced:
        print(f"Use {best_balanced[0]}:")
        print(f"- Maintains 4-season at {best_balanced[1]*100:.1f}%")
        print(f"- Improves 2025-26 to {best_balanced[2]*100:.1f}%")
    else:
        print("Consider using Fixed adv=30 as a compromise:")
        fixed_30_4 = np.mean([r['accuracy'] for r in all_results.get("Fixed adv=30", []) if r['season'] != '20252026'])
        fixed_30_2526 = next((r['accuracy'] for r in all_results.get("Fixed adv=30", []) if r['season'] == '20252026'), 0)
        print(f"- 4-season: {fixed_30_4*100:.1f}%")
        print(f"- 2025-26: {fixed_30_2526*100:.1f}%")


if __name__ == '__main__':
    main()
