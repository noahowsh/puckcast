#!/usr/bin/env python3
"""
V7.1 SIMPLE: Train model with basic goalie features (save%, games played).

Fixes the GSA bug from original V7.1 by using simple, reliable metrics:
- Save percentage (last 5 games)
- Games played (sample size indicator)
- Starter confirmation flag

No GSA or xG-dependent features.

Expected improvement: +0.3-0.5pp accuracy
Target: 62%+ accuracy, ≤0.670 log-loss
"""

import sys
import pickle
import sqlite3
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities
from nhl_prediction.train import compute_season_weights
from nhl_prediction.goalie_tracker import GoalieTracker

# Paths
GOALIE_TRACKER_PATH = Path("data/goalie_tracker_train_only.pkl")
STARTING_GOALIES_DB = Path("data/starting_goalies.db")

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
OPTIMAL_C = 0.05
OPTIMAL_DECAY = 1.0


def load_goalie_tracker() -> GoalieTracker:
    """Load goalie performance tracker."""
    print(f"Loading goalie tracker from {GOALIE_TRACKER_PATH}")
    with open(GOALIE_TRACKER_PATH, 'rb') as f:
        tracker = pickle.load(f)
    print(f"✓ Loaded {len(tracker.goalie_games)} goalies with performance history")
    return tracker


def load_starting_goalies() -> pd.DataFrame:
    """Load starting goalie assignments from database."""
    print(f"Loading starting goalies from {STARTING_GOALIES_DB}")
    conn = sqlite3.connect(STARTING_GOALIES_DB)
    df = pd.read_sql_query("SELECT * FROM starting_goalies", conn)
    conn.close()
    print(f"✓ Loaded starting assignments for {len(df)} games")
    return df


def add_simple_goalie_features(
    features: pd.DataFrame,
    games: pd.DataFrame,
    tracker: GoalieTracker,
    starting_goalies_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Add SIMPLE individual goalie features (no GSA).

    Features per game:
    - goalie_save_pct_last5_home/away: Save % over last 5 starts
    - goalie_games_last5_home/away: Games played in last 5 starts
    - goalie_starter_known_home/away: 1 if we have data, 0 otherwise
    """
    print("Adding simple goalie features (save%, games played)...")

    features = features.copy()

    # Create goalie feature columns
    goalie_cols = [
        'goalie_save_pct_last5_home',
        'goalie_save_pct_last5_away',
        'goalie_games_last5_home',
        'goalie_games_last5_away',
        'goalie_starter_known_home',
        'goalie_starter_known_away',
    ]

    for col in goalie_cols:
        features[col] = 0.0 if 'save_pct' in col or 'known' in col else 0

    # Create lookup: game_id -> (away_starter_id, home_starter_id)
    goalie_lookup = {}
    for _, row in starting_goalies_df.iterrows():
        goalie_lookup[row['game_id']] = (row['away_starter_id'], row['home_starter_id'])

    games_with_goalies = 0
    games_with_sufficient_data = 0

    # Add goalie features for each game
    for idx in features.index:
        game_row = games.loc[idx]
        game_id = int(game_row['gameId'])

        if game_id not in goalie_lookup:
            continue

        away_goalie_id, home_goalie_id = goalie_lookup[game_id]
        game_date = str(game_row['gameDate'])

        # Home goalie features
        if home_goalie_id and home_goalie_id in tracker.goalie_games:
            home_form = tracker.get_recent_form(home_goalie_id, game_date, last_n_games=5)
            games_played = home_form.get('games_played', 0)

            if games_played >= 3:  # Require at least 3 games of history
                features.at[idx, 'goalie_save_pct_last5_home'] = home_form.get('save_pct', 0.910)
                features.at[idx, 'goalie_games_last5_home'] = games_played
                features.at[idx, 'goalie_starter_known_home'] = 1.0

        # Away goalie features
        if away_goalie_id and away_goalie_id in tracker.goalie_games:
            away_form = tracker.get_recent_form(away_goalie_id, game_date, last_n_games=5)
            games_played = away_form.get('games_played', 0)

            if games_played >= 3:  # Require at least 3 games of history
                features.at[idx, 'goalie_save_pct_last5_away'] = away_form.get('save_pct', 0.910)
                features.at[idx, 'goalie_games_last5_away'] = games_played
                features.at[idx, 'goalie_starter_known_away'] = 1.0

            games_with_goalies += 1

        # Count games where we have sufficient data for BOTH goalies
        if features.at[idx, 'goalie_starter_known_home'] == 1.0 and features.at[idx, 'goalie_starter_known_away'] == 1.0:
            games_with_sufficient_data += 1

    # Add differential features
    features['goalie_save_pct_diff'] = (
        features['goalie_save_pct_last5_home'] - features['goalie_save_pct_last5_away']
    )
    features['goalie_both_starters_known'] = (
        (features['goalie_starter_known_home'] == 1.0) &
        (features['goalie_starter_known_away'] == 1.0)
    ).astype(int)

    print(f"✓ Added goalie features for {games_with_goalies}/{len(features)} games")
    print(f"✓ Games with both starters known (≥3 games history): {games_with_sufficient_data}")
    print(f"✓ Total features (including goalies): {len(features.columns)}")

    return features


def main():
    print("=" * 80)
    print("V7.1 SIMPLE: Training with Basic Goalie Features")
    print("=" * 80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load goalie data
    print("=" * 80)
    print("[1/6] Loading goalie data...")
    print("=" * 80)
    tracker = load_goalie_tracker()
    starting_goalies_df = load_starting_goalies()
    print()

    # Load V7.0 dataset
    print("=" * 80)
    print("[2/6] Loading V7.0 dataset...")
    print("=" * 80)
    dataset = build_dataset(TRAIN_SEASONS + [TEST_SEASON])
    print(f"✓ Loaded {len(dataset.games)} games")
    print(f"✓ V7.0 features: {len(dataset.features.columns)}")
    print()

    # Add goalie features
    print("=" * 80)
    print("[3/6] Adding simple goalie features...")
    print("=" * 80)
    features_with_goalies = add_simple_goalie_features(
        dataset.features,
        dataset.games,
        tracker,
        starting_goalies_df
    )
    print()

    # Prepare train/test split
    print("=" * 80)
    print("[4/6] Preparing train/test split...")
    print("=" * 80)
    train_mask = dataset.games['seasonId'].isin(TRAIN_SEASONS)
    test_mask = dataset.games['seasonId'] == TEST_SEASON

    X_train = features_with_goalies[train_mask]
    y_train = dataset.target[train_mask]
    X_test = features_with_goalies[test_mask]
    y_test = dataset.target[test_mask]

    # Compute sample weights
    train_weights = compute_season_weights(
        dataset.games[train_mask],
        TRAIN_SEASONS,
        decay_factor=OPTIMAL_DECAY
    )

    # Create fit mask (exclude first 10 games per team)
    train_mask_fit = dataset.games[train_mask]['games_played_prior_home'] > 10

    print(f"Training games: {len(X_train)}")
    print(f"Test games: {len(X_test)}")
    print(f"Features: {len(features_with_goalies.columns)}")
    print(f"Home team wins (train): {y_train.mean():.1%}")
    print(f"Home team wins (test): {y_test.mean():.1%}")
    print("✓ Sample weights computed")
    print()

    # Train model
    print("=" * 80)
    print(f"[5/6] Training V7.1 SIMPLE model (C={OPTIMAL_C})...")
    print("=" * 80)
    model = create_baseline_model(C=OPTIMAL_C)
    model = fit_model(model, X_train, y_train, train_mask_fit, sample_weight=train_weights)
    print(f"✓ Model trained")
    print(f"   Features used: {len(features_with_goalies.columns)}")
    print()

    # Evaluate
    print("=" * 80)
    print("[6/6] Evaluating V7.1 SIMPLE performance...")
    print("=" * 80)
    # Create test mask (all True for test set)
    test_mask_predict = pd.Series([True] * len(X_test), index=X_test.index)
    y_test_pred_proba = predict_probabilities(model, X_test, test_mask_predict)
    y_test_pred = (y_test_pred_proba >= 0.5).astype(int)

    test_acc = accuracy_score(y_test, y_test_pred)
    test_roc_auc = roc_auc_score(y_test, y_test_pred_proba)
    test_log_loss = log_loss(y_test, y_test_pred_proba)

    print()
    print("=" * 80)
    print("V7.1 SIMPLE RESULTS")
    print("=" * 80)
    print()
    print("Test Set Performance:")
    print(f"  Accuracy:  {test_acc:.4f} ({test_acc*100:.2f}%)")
    print(f"  ROC-AUC:   {test_roc_auc:.4f}")
    print(f"  Log Loss:  {test_log_loss:.4f}")
    print()

    # Compare to V7.0
    v7_0_acc = 0.6089
    v7_0_log_loss = 0.6758
    improvement_acc = (test_acc - v7_0_acc) * 100
    improvement_log_loss = test_log_loss - v7_0_log_loss

    print("🎯 Target Achievement:")
    target_acc = 0.62
    target_log_loss = 0.670
    acc_check = "✓" if test_acc >= target_acc else "✗"
    log_loss_check = "✓" if test_log_loss <= target_log_loss else "✗"
    print(f"  Accuracy:  {acc_check} {test_acc*100:.2f}% (target: 62%+)")
    print(f"  Log Loss:  {log_loss_check} {test_log_loss:.4f} (target: ≤0.670)")
    print()

    print("📊 vs V7.0:")
    print(f"  Accuracy:  {improvement_acc:+.2f} pp")
    print(f"  Log Loss:  {improvement_log_loss:+.4f}")
    print()

    # Feature importance
    print("=" * 80)
    print("Goalie Feature Importance:")
    print("=" * 80)
    lr = model.named_steps['logistic']
    feature_names = features_with_goalies.columns
    coefficients = lr.coef_[0]

    # Get goalie features
    goalie_features = [f for f in feature_names if 'goalie_' in f]
    goalie_coefs = [(f, coefficients[list(feature_names).index(f)]) for f in goalie_features]
    goalie_coefs.sort(key=lambda x: abs(x[1]), reverse=True)

    print(f"{'Feature':<40s} {'Coefficient':>12s}  {'Abs Importance':>15s}")
    print("-" * 70)
    for feat, coef in goalie_coefs:
        print(f"{feat:<40s} {coef:12.4f}  {abs(coef):15.4f}")

    print()
    print("=" * 80)
    print("V7.1 SIMPLE Training Complete!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)


if __name__ == "__main__":
    main()
