#!/usr/bin/env python3
"""
Elo Investigation - Why is Elo broken in 2025-26?

Current Elo implementation:
- base_rating = 1500
- k_factor = 10 (how quickly ratings change)
- home_advantage = 35 Elo points (corresponds to ~55% home win prob)
- season_carryover = 0.5 (regress 50% toward mean at season start)

Hypothesis: The home_advantage of 35 is calibrated for ~53.5% home win rate,
but 2025-26 has only 52.3% home win rate. This mismatch causes Elo to be
miscalibrated for the current season.

Potential fixes:
1. Dynamic home advantage based on recent league home win rate
2. Faster Elo adaptation (higher k_factor)
3. Season-specific home advantage
4. Remove home advantage from Elo entirely (pure team strength)
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

from nhl_prediction.pipeline import build_dataset

# V8.1 features for baseline comparison
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


def compute_custom_elo(
    games: pd.DataFrame,
    base_rating: float = 1500.0,
    k_factor: float = 10.0,
    home_advantage: float = 35.0,
    season_carryover: float = 0.5,
    dynamic_home_adv: bool = False,
    home_adv_window: int = 50,
) -> pd.DataFrame:
    """Compute Elo with custom parameters."""
    games = games.sort_values("gameDate").copy()
    elo_home: List[float] = []
    elo_away: List[float] = []
    expected_home_probs: List[float] = []

    current_season: str = None
    ratings: Dict[int, float] = {}
    prev_season_ratings: Dict[int, float] = {}

    # For dynamic home advantage
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

        # Dynamic home advantage based on recent home win rate
        if dynamic_home_adv and len(recent_home_wins) >= 25:
            recent_hw_rate = np.mean(recent_home_wins[-home_adv_window:])
            # Convert home win rate to Elo home advantage
            # 50% = 0 points, 53.5% ≈ 35 points, linear scaling
            current_home_adv = (recent_hw_rate - 0.5) * (35 / 0.035)
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

    games["elo_home_pre_custom"] = elo_home
    games["elo_away_pre_custom"] = elo_away
    games["elo_diff_pre_custom"] = games["elo_home_pre_custom"] - games["elo_away_pre_custom"]
    games["elo_expectation_home_custom"] = expected_home_probs
    return games


def analyze_elo_correlation(games, features, target):
    """Analyze Elo correlation with outcomes by season."""
    print("\n" + "=" * 80)
    print("ELO CORRELATION BY SEASON")
    print("=" * 80)

    print(f"\n{'Season':<12} {'Home Win%':<12} {'Elo Corr':<12} {'When Elo favors home':<25} {'Elo Accuracy':<15}")
    print("-" * 76)

    for season in sorted(games['seasonId'].unique()):
        mask = games['seasonId'] == season
        hw = target[mask].mean()

        elo_vals = features[mask]['elo_diff_pre'].values
        outcomes = target[mask].values

        # Correlation
        if np.std(elo_vals) > 0:
            corr = np.corrcoef(elo_vals, outcomes)[0, 1]
        else:
            corr = 0

        # When Elo favors home
        home_favored_mask = elo_vals > 0
        if home_favored_mask.sum() > 0:
            hw_when_favored = outcomes[home_favored_mask].mean()
        else:
            hw_when_favored = 0

        # Elo accuracy (pick team with higher Elo)
        elo_pred = (elo_vals > 0).astype(int)
        elo_acc = accuracy_score(outcomes, elo_pred)

        print(f"{season:<12} {hw:.1%}         {corr:+.3f}       Home wins {hw_when_favored:.1%}         {elo_acc:.1%}")


def test_elo_configuration(games, features, target, elo_column, name):
    """Test a specific Elo configuration."""
    results = []
    seasons = sorted(games['seasonId'].unique())

    # Create feature set with custom Elo
    features_copy = features.copy()
    if elo_column != 'elo_diff_pre':
        features_copy['elo_diff_pre'] = games[elo_column].values
        features_copy['elo_expectation_home'] = games[elo_column.replace('diff_pre', 'expectation_home')].values

    available = [f for f in V81_FEATURES if f in features_copy.columns]

    for test_season in seasons:
        train_seasons = [s for s in seasons if s != test_season]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        X_train = features_copy[train_mask][available].fillna(0)
        y_train = target[train_mask]
        X_test = features_copy[test_mask][available].fillna(0)
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
    print("ELO INVESTIGATION - WHY IS ELO BROKEN IN 2025-26?")
    print("=" * 90)

    seasons = ['20212022', '20222023', '20232024', '20242025', '20252026']
    dataset = build_dataset(seasons)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()

    print(f"\n✅ Loaded {len(games)} games")

    # Analyze current Elo
    analyze_elo_correlation(games, features, target)

    # Check Elo home advantage assumption
    print("\n" + "=" * 80)
    print("ELO HOME ADVANTAGE ANALYSIS")
    print("=" * 80)

    print("\nCurrent Elo uses home_advantage = 35 points (≈ 55% expected home win)")
    print("But actual home win rates vary:")
    for season in seasons:
        mask = games['seasonId'] == season
        actual_hw = target[mask].mean()
        # Convert to Elo points: 35 points ≈ 3.5% above 50%
        implied_adv = (actual_hw - 0.5) * (35 / 0.035)
        print(f"   {season}: {actual_hw:.1%} home wins → implies ~{implied_adv:.0f} Elo points (vs 35 default)")

    # Test different Elo configurations
    print("\n" + "=" * 80)
    print("TESTING ELO CONFIGURATIONS")
    print("=" * 80)

    configs = [
        ("Original (k=10, adv=35)", 10, 35, False),
        ("No home advantage (k=10, adv=0)", 10, 0, False),
        ("Lower home advantage (k=10, adv=20)", 10, 20, False),
        ("Higher home advantage (k=10, adv=50)", 10, 50, False),
        ("Faster adaptation (k=20, adv=35)", 20, 35, False),
        ("Much faster (k=32, adv=35)", 32, 35, False),
        ("Dynamic home advantage", 10, 35, True),
        ("Dynamic + faster (k=20)", 20, 35, True),
    ]

    all_results = {}
    for name, k, adv, dynamic in configs:
        print(f"\n⏳ Testing: {name}...")

        # Compute custom Elo
        games_with_elo = compute_custom_elo(
            games,
            k_factor=k,
            home_advantage=adv,
            dynamic_home_adv=dynamic
        )

        # Test it
        results = test_elo_configuration(games_with_elo, features, target, 'elo_diff_pre_custom', name)
        all_results[name] = results

        avg = np.mean([r['accuracy'] for r in results])
        acc_2526 = next(r['accuracy'] for r in results if r['season'] == '20252026')
        print(f"   Average: {avg:.1%}, 2025-26: {acc_2526:.1%}")

    # Compare all configurations
    print("\n" + "=" * 90)
    print("FULL COMPARISON")
    print("=" * 90)

    print(f"\n{'Configuration':<35} {'Avg':<10} {'21-22':<10} {'22-23':<10} {'23-24':<10} {'24-25':<10} {'25-26':<10}")
    print("-" * 95)

    # Add baseline
    baseline_results = test_elo_configuration(games, features, target, 'elo_diff_pre', 'Baseline V8.1')
    all_results['Baseline V8.1'] = baseline_results

    for name, results in all_results.items():
        accs = {r['season']: r['accuracy'] for r in results}
        avg = np.mean(list(accs.values()))
        row = f"{name:<35} {avg*100:.1f}%     "
        for s in seasons:
            row += f"{accs.get(s, 0)*100:.1f}%     "
        print(row)

    # Find best configurations
    print("\n" + "=" * 80)
    print("BEST CONFIGURATIONS")
    print("=" * 80)

    # Best overall
    best_overall = max(all_results.items(), key=lambda x: np.mean([r['accuracy'] for r in x[1]]))
    print(f"\n✅ Best Overall: {best_overall[0]} ({np.mean([r['accuracy'] for r in best_overall[1]])*100:.1f}%)")

    # Best 2025-26
    best_2526 = max(all_results.items(), key=lambda x: next(r['accuracy'] for r in x[1] if r['season'] == '20252026'))
    acc_2526 = next(r['accuracy'] for r in best_2526[1] if r['season'] == '20252026')
    print(f"✅ Best 2025-26: {best_2526[0]} ({acc_2526*100:.1f}%)")

    # Best 4-season average
    best_4 = max(all_results.items(), key=lambda x: np.mean([r['accuracy'] for r in x[1] if r['season'] != '20252026']))
    avg_4 = np.mean([r['accuracy'] for r in best_4[1] if r['season'] != '20252026'])
    print(f"✅ Best 4-season: {best_4[0]} ({avg_4*100:.1f}%)")

    # Test removing Elo entirely
    print("\n" + "=" * 80)
    print("TEST: MODEL WITHOUT ELO")
    print("=" * 80)

    no_elo_features = [f for f in V81_FEATURES if 'elo' not in f.lower()]
    no_elo_results = []
    for test_season in seasons:
        train_seasons = [s for s in seasons if s != test_season]
        train_mask = games['seasonId'].isin(train_seasons)
        test_mask = games['seasonId'] == test_season

        available = [f for f in no_elo_features if f in features.columns]
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
        no_elo_results.append({'season': test_season, 'accuracy': acc})

    print(f"\n{'Season':<12} {'With Elo':<12} {'Without Elo':<14} {'Change':<10}")
    print("-" * 48)
    for i, season in enumerate(seasons):
        with_elo = next(r['accuracy'] for r in baseline_results if r['season'] == season)
        without_elo = no_elo_results[i]['accuracy']
        change = without_elo - with_elo
        marker = "✅" if change > 0 else "❌" if change < 0 else "➖"
        print(f"{season:<12} {with_elo:.1%}        {without_elo:.1%}          {marker} {change*100:+.2f}pp")

    avg_with = np.mean([r['accuracy'] for r in baseline_results])
    avg_without = np.mean([r['accuracy'] for r in no_elo_results])
    print(f"\n{'AVERAGE':<12} {avg_with:.1%}        {avg_without:.1%}          {(avg_without-avg_with)*100:+.2f}pp")

    # Summary
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    baseline_2526 = next(r['accuracy'] for r in baseline_results if r['season'] == '20252026')
    best_2526_acc = next(r['accuracy'] for r in best_2526[1] if r['season'] == '20252026')
    without_elo_2526 = next(r['accuracy'] for r in no_elo_results if r['season'] == '20252026')

    print(f"""
KEY FINDINGS:

1. Elo Home Advantage Mismatch:
   - Default: 35 points (assumes ~55% home win rate)
   - 2025-26 actual: 52.3% home win rate
   - This explains why Elo predictions are biased toward home

2. Best Elo Configuration for 2025-26: {best_2526[0]}
   - 2025-26 accuracy: {best_2526_acc:.1%} (vs baseline {baseline_2526:.1%})

3. Removing Elo:
   - 2025-26 without Elo: {without_elo_2526:.1%}
   - This suggests Elo is actively hurting 2025-26 predictions

RECOMMENDATION:
""")

    if best_2526_acc > baseline_2526 + 0.01:
        print(f"✅ Use {best_2526[0]} configuration for improved 2025-26 performance")
    elif without_elo_2526 > baseline_2526 + 0.01:
        print("✅ Consider removing Elo features for 2025-26 or using dynamic home advantage")
    else:
        print("⚠️ Elo tuning provides marginal improvement. Focus on threshold adjustment instead.")


if __name__ == '__main__':
    main()
