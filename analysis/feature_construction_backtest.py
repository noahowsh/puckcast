"""
Large-scale backtest: Current vs Proper Feature Construction

Tests across multiple seasons using walk-forward validation:
- For each test season, train on all prior seasons
- Compare current averaging approach vs proper home_stat - away_stat
- Report accuracy and log loss per season and overall averages
"""

import sys
from pathlib import Path
import warnings

# Suppress sklearn warnings
warnings.filterwarnings('ignore')

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss

from nhl_prediction.pipeline import build_dataset

# Features to use (matching V7.0 model)
DIFF_FEATURES = [
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

BASE_FEATURES = [
    'rolling_win_pct_10', 'rolling_win_pct_5', 'rolling_win_pct_3',
    'rolling_goal_diff_10', 'rolling_goal_diff_5', 'rolling_goal_diff_3',
    'rolling_xg_diff_10', 'rolling_xg_diff_5', 'rolling_xg_diff_3',
    'rolling_corsi_10', 'rolling_corsi_5', 'rolling_corsi_3',
    'rolling_fenwick_10', 'rolling_fenwick_5',
    'season_win_pct', 'season_goal_diff_avg',
    'season_xg_diff_avg', 'season_shot_margin',
    'rolling_save_pct_10', 'rolling_save_pct_5', 'rolling_save_pct_3',
    'rolling_gsax_5', 'rolling_gsax_10',
    'goalie_trend_score',
    'momentum_win_pct', 'momentum_goal_diff', 'momentum_xg',
    'rolling_high_danger_shots_5', 'rolling_high_danger_shots_10',
    'shotsFor_roll_10', 'rolling_faceoff_5',
]


def get_team_recent_stats(games_df: pd.DataFrame, team_id: int, before_date: str, season: str) -> dict:
    """Get a team's most recent stats before a given date."""
    mask_home = (games_df['teamId_home'] == team_id) & (games_df['gameDate'] < before_date) & (games_df['seasonId'] == season)
    mask_away = (games_df['teamId_away'] == team_id) & (games_df['gameDate'] < before_date) & (games_df['seasonId'] == season)

    recent_home = games_df[mask_home].tail(1)
    recent_away = games_df[mask_away].tail(1)

    if len(recent_home) == 0 and len(recent_away) == 0:
        return None
    elif len(recent_home) == 0:
        recent = recent_away
        side = 'away'
    elif len(recent_away) == 0:
        recent = recent_home
        side = 'home'
    else:
        if recent_home['gameDate'].values[0] > recent_away['gameDate'].values[0]:
            recent = recent_home
            side = 'home'
        else:
            recent = recent_away
            side = 'away'

    stats = {}
    for base in BASE_FEATURES:
        col = f"{base}_{side}"
        if col in recent.columns:
            stats[base] = recent[col].values[0]

    if side == 'home':
        stats['elo'] = recent['elo_home_pre'].values[0] if 'elo_home_pre' in recent.columns else 1500
    else:
        stats['elo'] = recent['elo_away_pre'].values[0] if 'elo_away_pre' in recent.columns else 1500

    return stats


def construct_proper_features(games_df: pd.DataFrame, home_id: int, away_id: int,
                              game_date: str, season: str, feature_cols: list) -> np.ndarray:
    """Construct features by properly computing home_stat - away_stat."""
    home_stats = get_team_recent_stats(games_df, home_id, game_date, season)
    away_stats = get_team_recent_stats(games_df, away_id, game_date, season)

    if home_stats is None or away_stats is None:
        return None

    # Build feature dict matching expected order
    proper_dict = {}
    proper_dict['elo_diff_pre'] = home_stats.get('elo', 1500) - away_stats.get('elo', 1500)
    elo_diff = proper_dict['elo_diff_pre']
    proper_dict['elo_expectation_home'] = 1.0 / (1.0 + 10 ** (-elo_diff / 400))

    for base in BASE_FEATURES:
        home_val = home_stats.get(base, 0)
        away_val = away_stats.get(base, 0)
        proper_dict[f'{base}_diff'] = home_val - away_val

    return np.array([proper_dict.get(f, 0) for f in feature_cols])


def construct_current_features(games_df: pd.DataFrame, features_df: pd.DataFrame,
                               home_id: int, away_id: int, game_date: str, season: str,
                               feature_cols: list) -> np.ndarray:
    """Construct features using current averaging approach."""
    mask_home = (games_df['teamId_home'] == home_id) & (games_df['gameDate'] < game_date) & (games_df['seasonId'] == season)
    recent_home = games_df[mask_home].tail(1)

    mask_away = (games_df['teamId_away'] == away_id) & (games_df['gameDate'] < game_date) & (games_df['seasonId'] == season)
    recent_away = games_df[mask_away].tail(1)

    if len(recent_home) == 0 or len(recent_away) == 0:
        return None

    home_idx = recent_home.index[0]
    away_idx = recent_away.index[0]

    home_features = features_df.loc[home_idx, feature_cols].values
    away_features = features_df.loc[away_idx, feature_cols].values

    return (home_features + away_features) / 2


def evaluate_season(games: pd.DataFrame, features_df: pd.DataFrame,
                    train_seasons: list, test_season: str, feature_cols: list) -> dict:
    """Evaluate both approaches on a single test season."""

    train_mask = games['seasonId'].isin(train_seasons)
    test_mask = games['seasonId'] == test_season

    if train_mask.sum() == 0 or test_mask.sum() == 0:
        return None

    # Train model on training data
    X_train = features_df.loc[train_mask, feature_cols].fillna(0)
    y_train = games.loc[train_mask, 'home_win']

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = LogisticRegression(max_iter=2000, C=1.0, random_state=42)
    model.fit(X_train_scaled, y_train)

    # Simulate predictions on test set
    test_games = games[test_mask].copy()

    results_current = []
    results_proper = []
    actuals = []

    for idx, row in test_games.iterrows():
        home_id = row['teamId_home']
        away_id = row['teamId_away']
        game_date = row['gameDate']
        season = row['seasonId']
        actual = row['home_win']

        current_feat = construct_current_features(games, features_df, home_id, away_id,
                                                   game_date, season, feature_cols)
        proper_feat = construct_proper_features(games, home_id, away_id, game_date, season, feature_cols)

        if current_feat is not None and proper_feat is not None:
            current_scaled = scaler.transform(current_feat.reshape(1, -1))
            proper_scaled = scaler.transform(proper_feat.reshape(1, -1))

            current_prob = model.predict_proba(current_scaled)[0, 1]
            proper_prob = model.predict_proba(proper_scaled)[0, 1]

            results_current.append(current_prob)
            results_proper.append(proper_prob)
            actuals.append(actual)

    if len(actuals) == 0:
        return None

    actuals = np.array(actuals)
    results_current = np.array(results_current)
    results_proper = np.array(results_proper)

    return {
        'season': test_season,
        'n_games': len(actuals),
        'current_acc': accuracy_score(actuals, (results_current >= 0.5).astype(int)),
        'proper_acc': accuracy_score(actuals, (results_proper >= 0.5).astype(int)),
        'current_ll': log_loss(actuals, results_current),
        'proper_ll': log_loss(actuals, results_proper),
        'current_brier': brier_score_loss(actuals, results_current),
        'proper_brier': brier_score_loss(actuals, results_proper),
    }


def main():
    print("=" * 80)
    print("LARGE-SCALE FEATURE CONSTRUCTION BACKTEST")
    print("=" * 80)

    # Load all seasons
    print("\n1. Loading dataset (this may take a minute)...")
    all_seasons = ["20212022", "20222023", "20232024", "20242025"]
    dataset = build_dataset(all_seasons)
    games = dataset.games.copy()

    # Get available features
    available_diff = [f for f in DIFF_FEATURES if f in dataset.features.columns]
    features_df = dataset.features[available_diff].copy()

    print(f"   Total games: {len(games)}")
    print(f"   Seasons: {all_seasons}")
    print(f"   Features: {len(available_diff)}")

    # Walk-forward evaluation
    print("\n2. Running walk-forward evaluation...")
    print("   (Train on prior seasons, test on each season)\n")

    results = []

    # Test on seasons 2022-23, 2023-24, 2024-25 (using prior seasons for training)
    test_configs = [
        (["20212022"], "20222023"),
        (["20212022", "20222023"], "20232024"),
        (["20212022", "20222023", "20232024"], "20242025"),
    ]

    for train_seasons, test_season in test_configs:
        print(f"   Testing {test_season} (trained on {', '.join(train_seasons)})...")
        result = evaluate_season(games, features_df, train_seasons, test_season, available_diff)
        if result:
            results.append(result)
            print(f"      Current: {result['current_acc']:.1%} acc, {result['current_ll']:.4f} log loss")
            print(f"      Proper:  {result['proper_acc']:.1%} acc, {result['proper_ll']:.4f} log loss")
            print(f"      Δ Acc: {(result['proper_acc'] - result['current_acc']) * 100:+.2f}pp")

    # Summary
    print("\n" + "=" * 80)
    print("RESULTS SUMMARY")
    print("=" * 80)

    print("\nPer-Season Results:")
    print("-" * 70)
    print(f"{'Season':<12} {'Games':<8} {'Current Acc':<12} {'Proper Acc':<12} {'Δ Acc':<10}")
    print("-" * 70)

    for r in results:
        delta = (r['proper_acc'] - r['current_acc']) * 100
        print(f"{r['season']:<12} {r['n_games']:<8} {r['current_acc']:.1%}        {r['proper_acc']:.1%}        {delta:+.2f}pp")

    print("-" * 70)

    # Weighted averages (by number of games)
    total_games = sum(r['n_games'] for r in results)
    avg_current_acc = sum(r['current_acc'] * r['n_games'] for r in results) / total_games
    avg_proper_acc = sum(r['proper_acc'] * r['n_games'] for r in results) / total_games
    avg_current_ll = sum(r['current_ll'] * r['n_games'] for r in results) / total_games
    avg_proper_ll = sum(r['proper_ll'] * r['n_games'] for r in results) / total_games
    avg_current_brier = sum(r['current_brier'] * r['n_games'] for r in results) / total_games
    avg_proper_brier = sum(r['proper_brier'] * r['n_games'] for r in results) / total_games

    print(f"{'AVERAGE':<12} {total_games:<8} {avg_current_acc:.1%}        {avg_proper_acc:.1%}        {(avg_proper_acc - avg_current_acc) * 100:+.2f}pp")
    print("-" * 70)

    print("\nLog Loss Comparison:")
    print("-" * 70)
    print(f"{'Season':<12} {'Current LL':<12} {'Proper LL':<12} {'Δ LL':<12}")
    print("-" * 70)

    for r in results:
        delta = r['proper_ll'] - r['current_ll']
        print(f"{r['season']:<12} {r['current_ll']:.4f}       {r['proper_ll']:.4f}       {delta:+.4f}")

    print("-" * 70)
    print(f"{'AVERAGE':<12} {avg_current_ll:.4f}       {avg_proper_ll:.4f}       {avg_proper_ll - avg_current_ll:+.4f}")
    print("-" * 70)

    print("\nBrier Score Comparison:")
    print("-" * 70)
    print(f"{'Season':<12} {'Current':<12} {'Proper':<12} {'Δ Brier':<12}")
    print("-" * 70)

    for r in results:
        delta = r['proper_brier'] - r['current_brier']
        print(f"{r['season']:<12} {r['current_brier']:.4f}       {r['proper_brier']:.4f}       {delta:+.4f}")

    print("-" * 70)
    print(f"{'AVERAGE':<12} {avg_current_brier:.4f}       {avg_proper_brier:.4f}       {avg_proper_brier - avg_current_brier:+.4f}")
    print("-" * 70)

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)
    acc_improvement = (avg_proper_acc - avg_current_acc) * 100
    ll_improvement = avg_current_ll - avg_proper_ll

    print(f"\nProper feature construction improves:")
    print(f"   Accuracy:   {acc_improvement:+.2f} percentage points")
    print(f"   Log Loss:   {ll_improvement:+.4f} (lower is better)")
    print(f"   Brier:      {avg_current_brier - avg_proper_brier:+.4f} (lower is better)")

    if acc_improvement > 0 and ll_improvement > 0:
        print(f"\n✅ RECOMMENDATION: Implement the fix - consistent improvement across all metrics")
    elif acc_improvement > 0:
        print(f"\n⚠️  RECOMMENDATION: Consider implementing - accuracy improves but log loss mixed")
    else:
        print(f"\n❌ RECOMMENDATION: Do not implement - no clear improvement")

    print("=" * 80)

    return results


if __name__ == "__main__":
    main()
