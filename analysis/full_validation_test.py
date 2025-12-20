"""
Full-scale validation: Current vs Proper Feature Construction

Tests on ALL games using leave-one-season-out cross-validation:
- For each season, train on ALL other seasons, test on that season
- This tests every single game in the dataset
- Reports comprehensive metrics
"""

import sys
from pathlib import Path
import warnings

warnings.filterwarnings('ignore')

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, log_loss, brier_score_loss

from nhl_prediction.pipeline import build_dataset

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


def evaluate_season_loso(games: pd.DataFrame, features_df: pd.DataFrame,
                         test_season: str, all_seasons: list, feature_cols: list) -> dict:
    """Leave-one-season-out: train on all OTHER seasons, test on this one."""

    train_seasons = [s for s in all_seasons if s != test_season]
    train_mask = games['seasonId'].isin(train_seasons)
    test_mask = games['seasonId'] == test_season

    if train_mask.sum() == 0 or test_mask.sum() == 0:
        return None

    # Train model
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
    skipped = 0

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
        else:
            skipped += 1

    if len(actuals) == 0:
        return None

    actuals = np.array(actuals)
    results_current = np.array(results_current)
    results_proper = np.array(results_proper)

    return {
        'season': test_season,
        'n_games': len(actuals),
        'n_skipped': skipped,
        'current_acc': accuracy_score(actuals, (results_current >= 0.5).astype(int)),
        'proper_acc': accuracy_score(actuals, (results_proper >= 0.5).astype(int)),
        'current_ll': log_loss(actuals, results_current),
        'proper_ll': log_loss(actuals, results_proper),
        'current_brier': brier_score_loss(actuals, results_current),
        'proper_brier': brier_score_loss(actuals, results_proper),
        'actuals': actuals,
        'current_probs': results_current,
        'proper_probs': results_proper,
    }


def main():
    print("=" * 80)
    print("FULL-SCALE VALIDATION: ALL GAMES")
    print("Leave-One-Season-Out Cross-Validation")
    print("=" * 80)

    print("\n1. Loading dataset...")
    all_seasons = ["20212022", "20222023", "20232024", "20242025"]
    dataset = build_dataset(all_seasons)
    games = dataset.games.copy()

    available_diff = [f for f in DIFF_FEATURES if f in dataset.features.columns]
    features_df = dataset.features[available_diff].copy()

    print(f"   Total games in dataset: {len(games)}")
    print(f"   Seasons: {', '.join(all_seasons)}")
    print(f"   Features: {len(available_diff)}")

    print("\n2. Running leave-one-season-out cross-validation...")
    print("   (For each season: train on other 3, test on that one)\n")

    results = []
    all_actuals = []
    all_current_probs = []
    all_proper_probs = []

    for test_season in all_seasons:
        train_seasons = [s for s in all_seasons if s != test_season]
        print(f"   Testing {test_season} (trained on {', '.join(train_seasons)})...")

        result = evaluate_season_loso(games, features_df, test_season, all_seasons, available_diff)
        if result:
            results.append(result)
            all_actuals.extend(result['actuals'])
            all_current_probs.extend(result['current_probs'])
            all_proper_probs.extend(result['proper_probs'])

            print(f"      Games tested: {result['n_games']} (skipped {result['n_skipped']} early-season)")
            print(f"      Current: {result['current_acc']:.1%} acc, {result['current_ll']:.4f} LL")
            print(f"      Proper:  {result['proper_acc']:.1%} acc, {result['proper_ll']:.4f} LL")
            print(f"      Δ Acc: {(result['proper_acc'] - result['current_acc']) * 100:+.2f}pp")

    # Convert to arrays for overall metrics
    all_actuals = np.array(all_actuals)
    all_current_probs = np.array(all_current_probs)
    all_proper_probs = np.array(all_proper_probs)

    print("\n" + "=" * 80)
    print("FULL RESULTS - ALL GAMES")
    print("=" * 80)

    print("\nPer-Season Breakdown:")
    print("-" * 75)
    print(f"{'Season':<12} {'Games':<8} {'Skipped':<10} {'Current':<12} {'Proper':<12} {'Δ Acc':<10}")
    print("-" * 75)

    total_tested = 0
    total_skipped = 0
    for r in results:
        delta = (r['proper_acc'] - r['current_acc']) * 100
        print(f"{r['season']:<12} {r['n_games']:<8} {r['n_skipped']:<10} {r['current_acc']:.1%}        {r['proper_acc']:.1%}        {delta:+.2f}pp")
        total_tested += r['n_games']
        total_skipped += r['n_skipped']

    print("-" * 75)

    # Overall metrics
    overall_current_acc = accuracy_score(all_actuals, (all_current_probs >= 0.5).astype(int))
    overall_proper_acc = accuracy_score(all_actuals, (all_proper_probs >= 0.5).astype(int))
    overall_current_ll = log_loss(all_actuals, all_current_probs)
    overall_proper_ll = log_loss(all_actuals, all_proper_probs)
    overall_current_brier = brier_score_loss(all_actuals, all_current_probs)
    overall_proper_brier = brier_score_loss(all_actuals, all_proper_probs)

    print(f"{'TOTAL':<12} {total_tested:<8} {total_skipped:<10} {overall_current_acc:.1%}        {overall_proper_acc:.1%}        {(overall_proper_acc - overall_current_acc) * 100:+.2f}pp")
    print("-" * 75)

    print(f"\n📊 OVERALL METRICS ({total_tested:,} games tested)")
    print("-" * 75)
    print(f"{'Metric':<20} {'Current':<15} {'Proper':<15} {'Δ (Improvement)':<20}")
    print("-" * 75)
    print(f"{'Accuracy':<20} {overall_current_acc:.2%}          {overall_proper_acc:.2%}          {(overall_proper_acc - overall_current_acc) * 100:+.2f} pp")
    print(f"{'Log Loss':<20} {overall_current_ll:.4f}          {overall_proper_ll:.4f}          {overall_current_ll - overall_proper_ll:+.4f}")
    print(f"{'Brier Score':<20} {overall_current_brier:.4f}          {overall_proper_brier:.4f}          {overall_current_brier - overall_proper_brier:+.4f}")
    print("-" * 75)

    # Analyze disagreements
    current_preds = (all_current_probs >= 0.5).astype(int)
    proper_preds = (all_proper_probs >= 0.5).astype(int)
    disagreements = np.sum(current_preds != proper_preds)
    disagree_mask = current_preds != proper_preds

    print(f"\n🔍 DISAGREEMENT ANALYSIS")
    print("-" * 75)
    print(f"Games where approaches disagree: {disagreements} ({disagreements/len(all_actuals)*100:.1f}%)")

    if disagreements > 0:
        current_right = np.sum((current_preds == all_actuals) & disagree_mask)
        proper_right = np.sum((proper_preds == all_actuals) & disagree_mask)
        print(f"When they disagree:")
        print(f"   Current approach correct: {current_right}/{disagreements} ({current_right/disagreements*100:.1f}%)")
        print(f"   Proper approach correct:  {proper_right}/{disagreements} ({proper_right/disagreements*100:.1f}%)")

    # Confidence bucket analysis
    print(f"\n📈 ACCURACY BY CONFIDENCE LEVEL")
    print("-" * 75)

    buckets = [(0.5, 0.55), (0.55, 0.60), (0.60, 0.65), (0.65, 0.70), (0.70, 1.0)]
    print(f"{'Confidence':<15} {'N Games':<10} {'Current Acc':<15} {'Proper Acc':<15} {'Δ Acc':<10}")
    print("-" * 75)

    for low, high in buckets:
        # For proper approach
        mask = (all_proper_probs >= low) & (all_proper_probs < high) | \
               (all_proper_probs <= (1-low)) & (all_proper_probs > (1-high))
        if mask.sum() > 0:
            curr_acc = accuracy_score(all_actuals[mask], (all_current_probs[mask] >= 0.5).astype(int))
            prop_acc = accuracy_score(all_actuals[mask], (all_proper_probs[mask] >= 0.5).astype(int))
            label = f"{low:.0%}-{high:.0%}"
            print(f"{label:<15} {mask.sum():<10} {curr_acc:.1%}           {prop_acc:.1%}           {(prop_acc-curr_acc)*100:+.1f}pp")

    print("-" * 75)

    print("\n" + "=" * 80)
    print("CONCLUSION")
    print("=" * 80)

    acc_improvement = (overall_proper_acc - overall_current_acc) * 100
    ll_improvement = overall_current_ll - overall_proper_ll

    print(f"\n🎯 Tested on {total_tested:,} games across 4 seasons")
    print(f"\n   Proper feature construction improves:")
    print(f"   ├─ Accuracy:    {acc_improvement:+.2f} percentage points ({overall_current_acc:.1%} → {overall_proper_acc:.1%})")
    print(f"   ├─ Log Loss:    {ll_improvement:+.4f} (lower is better)")
    print(f"   └─ Brier Score: {overall_current_brier - overall_proper_brier:+.4f} (lower is better)")

    if acc_improvement > 1.0 and ll_improvement > 0:
        print(f"\n✅ VERDICT: Clear improvement - implement the fix")
    elif acc_improvement > 0 and ll_improvement > 0:
        print(f"\n✅ VERDICT: Consistent improvement - implement the fix")
    else:
        print(f"\n⚠️  VERDICT: Mixed results - review further")

    print("=" * 80)

    return {
        'total_games': total_tested,
        'current_acc': overall_current_acc,
        'proper_acc': overall_proper_acc,
        'acc_improvement': acc_improvement,
        'll_improvement': ll_improvement,
    }


if __name__ == "__main__":
    main()
