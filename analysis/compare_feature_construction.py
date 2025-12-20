"""
Compare feature construction approaches for NHL predictions.

This script tests whether properly computing home_stat - away_stat
for new matchups improves accuracy over the current averaging approach.

Current approach (predict_full.py):
  - Find home team's recent HOME game, get differential features
  - Find away team's recent AWAY game, get differential features
  - Average them: (home_features + away_features) / 2

Proposed approach:
  - Find each team's most recent game (any home/away)
  - Extract that team's raw stats from that game
  - Compute proper differential: home_team_stat - away_team_stat
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score, log_loss

from nhl_prediction.pipeline import build_dataset

# V7.0 features we care about (the differential ones)
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

# Base features (without _diff suffix) that have _home and _away variants
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
    # Find team's most recent game (either home or away) before this date
    mask_home = (games_df['teamId_home'] == team_id) & (games_df['gameDate'] < before_date) & (games_df['seasonId'] == season)
    mask_away = (games_df['teamId_away'] == team_id) & (games_df['gameDate'] < before_date) & (games_df['seasonId'] == season)

    recent_home = games_df[mask_home].tail(1)
    recent_away = games_df[mask_away].tail(1)

    # Get the more recent of the two
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

    # Extract raw stats for this team
    stats = {}
    for base in BASE_FEATURES:
        col = f"{base}_{side}"
        if col in recent.columns:
            stats[base] = recent[col].values[0]

    # Also get Elo (stored differently)
    if side == 'home':
        stats['elo'] = recent['elo_home_pre'].values[0] if 'elo_home_pre' in recent.columns else 1500
    else:
        stats['elo'] = recent['elo_away_pre'].values[0] if 'elo_away_pre' in recent.columns else 1500

    return stats


def construct_proper_features(games_df: pd.DataFrame, home_id: int, away_id: int,
                              game_date: str, season: str) -> np.ndarray:
    """Construct features by properly computing home_stat - away_stat."""
    home_stats = get_team_recent_stats(games_df, home_id, game_date, season)
    away_stats = get_team_recent_stats(games_df, away_id, game_date, season)

    if home_stats is None or away_stats is None:
        return None

    features = []

    # Elo diff
    features.append(home_stats.get('elo', 1500) - away_stats.get('elo', 1500))
    # Elo expectation (compute from Elo diff)
    elo_diff = features[0]
    features.append(1.0 / (1.0 + 10 ** (-elo_diff / 400)))

    # All other differential features
    for base in BASE_FEATURES:
        home_val = home_stats.get(base, 0)
        away_val = away_stats.get(base, 0)
        features.append(home_val - away_val)

    return np.array(features)


def construct_current_features(games_df: pd.DataFrame, features_df: pd.DataFrame,
                               home_id: int, away_id: int, game_date: str, season: str,
                               feature_cols: list) -> np.ndarray:
    """Construct features using current averaging approach."""
    # Find home team's recent HOME game
    mask_home = (games_df['teamId_home'] == home_id) & (games_df['gameDate'] < game_date) & (games_df['seasonId'] == season)
    recent_home = games_df[mask_home].tail(1)

    # Find away team's recent AWAY game
    mask_away = (games_df['teamId_away'] == away_id) & (games_df['gameDate'] < game_date) & (games_df['seasonId'] == season)
    recent_away = games_df[mask_away].tail(1)

    if len(recent_home) == 0 or len(recent_away) == 0:
        return None

    home_idx = recent_home.index[0]
    away_idx = recent_away.index[0]

    home_features = features_df.loc[home_idx, feature_cols].values
    away_features = features_df.loc[away_idx, feature_cols].values

    # Average them (current approach)
    return (home_features + away_features) / 2


def main():
    print("=" * 80)
    print("FEATURE CONSTRUCTION COMPARISON TEST")
    print("=" * 80)

    # Load data
    print("\n1. Loading dataset...")
    seasons = ["20212022", "20222023", "20232024", "20242025"]
    dataset = build_dataset(seasons)
    games = dataset.games.copy()

    print(f"   Total games: {len(games)}")

    # Filter to available features
    available_diff = [f for f in DIFF_FEATURES if f in dataset.features.columns]
    print(f"   Available differential features: {len(available_diff)}")

    features_df = dataset.features[available_diff].copy()

    # Split: train on first 3 seasons, test on last season
    train_seasons = ["20212022", "20222023", "20232024"]
    test_season = "20242025"

    train_mask = games['seasonId'].isin(train_seasons)
    test_mask = games['seasonId'] == test_season

    print(f"\n2. Training set: {train_mask.sum()} games")
    print(f"   Test set: {test_mask.sum()} games")

    # Train model on training data (using actual features, not simulated)
    print("\n3. Training baseline model on actual differential features...")
    X_train = features_df.loc[train_mask].fillna(0)
    y_train = dataset.target.loc[train_mask]

    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)

    model = LogisticRegression(max_iter=2000, C=1.0, random_state=42)
    model.fit(X_train_scaled, y_train)

    # Evaluate on training data
    train_probs = model.predict_proba(X_train_scaled)[:, 1]
    train_acc = accuracy_score(y_train, (train_probs >= 0.5).astype(int))
    print(f"   Training accuracy: {train_acc:.1%}")

    # Now simulate predictions on test set using both approaches
    print("\n4. Simulating predictions on test set...")

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

        # Current approach
        current_feat = construct_current_features(games, features_df, home_id, away_id,
                                                   game_date, season, available_diff)

        # Proper approach
        proper_feat = construct_proper_features(games, home_id, away_id, game_date, season)

        if current_feat is not None and proper_feat is not None:
            # Scale and predict
            current_scaled = scaler.transform(current_feat.reshape(1, -1))

            # For proper features, we need to match the feature order
            # Build a compatible feature vector
            proper_dict = {}
            proper_dict['elo_diff_pre'] = proper_feat[0]
            proper_dict['elo_expectation_home'] = proper_feat[1]
            for i, base in enumerate(BASE_FEATURES):
                proper_dict[f'{base}_diff'] = proper_feat[i + 2]

            proper_vec = np.array([proper_dict.get(f, 0) for f in available_diff])
            proper_scaled = scaler.transform(proper_vec.reshape(1, -1))

            current_prob = model.predict_proba(current_scaled)[0, 1]
            proper_prob = model.predict_proba(proper_scaled)[0, 1]

            results_current.append(current_prob)
            results_proper.append(proper_prob)
            actuals.append(actual)

    print(f"   Valid predictions: {len(actuals)}")

    # Compare results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    actuals = np.array(actuals)
    results_current = np.array(results_current)
    results_proper = np.array(results_proper)

    # Accuracy
    current_acc = accuracy_score(actuals, (results_current >= 0.5).astype(int))
    proper_acc = accuracy_score(actuals, (results_proper >= 0.5).astype(int))

    # Log loss
    current_ll = log_loss(actuals, results_current)
    proper_ll = log_loss(actuals, results_proper)

    print(f"\nCurrent Approach (averaging):")
    print(f"   Accuracy: {current_acc:.1%}")
    print(f"   Log Loss: {current_ll:.4f}")

    print(f"\nProper Approach (home_stat - away_stat):")
    print(f"   Accuracy: {proper_acc:.1%}")
    print(f"   Log Loss: {proper_ll:.4f}")

    print(f"\nDifference:")
    print(f"   Accuracy: {(proper_acc - current_acc) * 100:+.2f} percentage points")
    print(f"   Log Loss: {proper_ll - current_ll:+.4f} (lower is better)")

    # Analyze disagreements
    current_preds = (results_current >= 0.5).astype(int)
    proper_preds = (results_proper >= 0.5).astype(int)
    disagreements = np.sum(current_preds != proper_preds)

    print(f"\n   Prediction disagreements: {disagreements} ({disagreements/len(actuals)*100:.1f}%)")

    # When they disagree, who's right?
    disagree_mask = current_preds != proper_preds
    if disagreements > 0:
        current_right = np.sum((current_preds == actuals) & disagree_mask)
        proper_right = np.sum((proper_preds == actuals) & disagree_mask)
        print(f"   When they disagree:")
        print(f"      Current approach correct: {current_right} ({current_right/disagreements*100:.1f}%)")
        print(f"      Proper approach correct:  {proper_right} ({proper_right/disagreements*100:.1f}%)")

    print("\n" + "=" * 80)

    return current_acc, proper_acc


if __name__ == "__main__":
    main()
