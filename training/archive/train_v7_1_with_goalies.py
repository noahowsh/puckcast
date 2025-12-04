#!/usr/bin/env python3
"""
V7.1: Train model with individual goalie tracking features.

Expected improvement: +0.8-1.2% accuracy, -0.005 to -0.010 log-loss
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
GOALIE_TRACKER_PATH = Path("data/goalie_tracker_train_only.pkl")  # TRAINING DATA ONLY - no test set leakage
STARTING_GOALIES_DB = Path("data/starting_goalies.db")

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
OPTIMAL_C = 0.05  # From V7.0 optimization
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


def add_goalie_features_to_dataset(
    features: pd.DataFrame,
    games: pd.DataFrame,
    tracker: GoalieTracker,
    starting_goalies_df: pd.DataFrame
) -> pd.DataFrame:
    """
    Add individual goalie features to the feature matrix.

    New features per game:
    - goalie_gsa_last5_home/away: GSA avg over last 5 starts
    - goalie_save_pct_last5_home/away: Overall save %
    - goalie_gsa_diff: Home GSA - Away GSA
    - goalie_quality_diff: Home save% - Away save%
    - goalie_games_played_last5_home/away: Sample size indicator
    """
    print("Adding individual goalie features...")

    features = features.copy()

    # Create goalie feature columns
    goalie_cols = [
        'goalie_gsa_last5_home',
        'goalie_gsa_last5_away',
        'goalie_save_pct_last5_home',
        'goalie_save_pct_last5_away',
        'goalie_games_played_last5_home',
        'goalie_games_played_last5_away',
    ]

    for col in goalie_cols:
        features[col] = 0.0

    # Create lookup: game_id -> (away_starter_id, home_starter_id)
    goalie_lookup = {}
    for _, row in starting_goalies_df.iterrows():
        goalie_lookup[row['game_id']] = (row['away_starter_id'], row['home_starter_id'])

    games_with_goalies = 0

    # Add goalie features for each game
    for idx in features.index:
        game_row = games.loc[idx]
        game_id = int(game_row['gameId'])

        if game_id not in goalie_lookup:
            continue

        away_goalie_id, home_goalie_id = goalie_lookup[game_id]

        # Get game date
        game_date = str(game_row['gameDate'])

        # Home goalie features
        if home_goalie_id and home_goalie_id in tracker.goalie_games:
            home_form = tracker.get_recent_form(home_goalie_id, game_date, last_n_games=5)
            features.at[idx, 'goalie_gsa_last5_home'] = home_form.get('gsa_avg', 0.0)
            features.at[idx, 'goalie_save_pct_last5_home'] = home_form.get('save_pct', 0.910)
            features.at[idx, 'goalie_games_played_last5_home'] = home_form.get('games_played', 0)

        # Away goalie features
        if away_goalie_id and away_goalie_id in tracker.goalie_games:
            away_form = tracker.get_recent_form(away_goalie_id, game_date, last_n_games=5)
            features.at[idx, 'goalie_gsa_last5_away'] = away_form.get('gsa_avg', 0.0)
            features.at[idx, 'goalie_save_pct_last5_away'] = away_form.get('save_pct', 0.910)
            features.at[idx, 'goalie_games_played_last5_away'] = away_form.get('games_played', 0)

            games_with_goalies += 1

    # Add differential features
    features['goalie_gsa_diff'] = (
        features['goalie_gsa_last5_home'] - features['goalie_gsa_last5_away']
    )
    features['goalie_quality_diff'] = (
        features['goalie_save_pct_last5_home'] - features['goalie_save_pct_last5_away']
    )

    print(f"✓ Added goalie features for {games_with_goalies}/{len(features)} games")
    print(f"✓ Total features (including goalies): {len(features.columns)}")

    return features


def evaluate_confidence_buckets(y_true, y_pred_proba, bucket_name="Overall"):
    """Evaluate performance by confidence buckets."""
    # Calculate point differential (home win probability - 0.5) * 100
    point_diffs = (y_pred_proba - 0.5) * 100

    # Define buckets
    buckets = [
        ("A+", 20, 100),
        ("A-", 15, 20),
        ("B+", 10, 15),
        ("B-", 5, 10),
        ("C", 0, 5),
    ]

    print(f"\n{bucket_name} Confidence Ladder:")
    print(f"{'Grade':<6} {'Range':<12} {'Games':>8} {'Accuracy':>10} {'Exp Win%':>10}")
    print("-" * 60)

    for grade, min_pts, max_pts in buckets:
        mask = (point_diffs >= min_pts) & (point_diffs < max_pts)
        n_games = mask.sum()

        if n_games > 0:
            acc = accuracy_score(y_true[mask], (y_pred_proba[mask] >= 0.5).astype(int))
            exp_win_pct = y_pred_proba[mask].mean()
            print(f"{grade:<6} {min_pts:>2d}-{max_pts:>2d} pts   {n_games:>8d} {acc:>9.1%}   {exp_win_pct:>9.1%}")
        else:
            print(f"{grade:<6} {min_pts:>2d}-{max_pts:>2d} pts   {n_games:>8d} {'N/A':>10} {'N/A':>10}")


def main():
    """Train V7.1 model with individual goalie features."""
    print("="*80)
    print("V7.1: Training with Individual Goalie Features")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load goalie data
    print("=" * 80)
    print("[1/6] Loading goalie data...")
    print("=" * 80)
    tracker = load_goalie_tracker()
    starting_goalies_df = load_starting_goalies()
    print()

    # Load dataset
    print("=" * 80)
    print("[2/6] Loading V7.0 dataset...")
    print("=" * 80)
    dataset = build_dataset(TRAIN_SEASONS + [TEST_SEASON])
    print(f"✓ Loaded {len(dataset.games)} games")
    print(f"✓ V7.0 features: {len(dataset.features.columns)}")
    print()

    # Add goalie features
    print("=" * 80)
    print("[3/6] Adding individual goalie features...")
    print("=" * 80)
    features_with_goalies = add_goalie_features_to_dataset(
        dataset.features,
        dataset.games,
        tracker,
        starting_goalies_df
    )
    print()

    # Split train/test
    print("=" * 80)
    print("[4/6] Preparing train/test split...")
    print("=" * 80)

    train_mask = dataset.games["seasonId"].isin(TRAIN_SEASONS)
    test_mask = dataset.games["seasonId"] == TEST_SEASON

    X = features_with_goalies.fillna(0)
    y = dataset.target

    X_train, y_train = X[train_mask], y[train_mask]
    X_test, y_test = X[test_mask], y[test_mask]

    print(f"Training games: {train_mask.sum()}")
    print(f"Test games: {test_mask.sum()}")
    print(f"Home team wins (train): {y_train.mean():.1%}")
    print(f"Home team wins (test): {y_test.mean():.1%}")

    # Compute sample weights
    train_weights = compute_season_weights(dataset.games[train_mask], TRAIN_SEASONS, decay_factor=OPTIMAL_DECAY)
    print(f"✓ Sample weights computed")
    print()

    # Train model
    print("=" * 80)
    print(f"[5/6] Training V7.1 model (C={OPTIMAL_C})...")
    print("=" * 80)

    model = create_baseline_model(C=OPTIMAL_C)
    train_mask_fit = pd.Series(True, index=X_train.index)
    model = fit_model(model, X_train, y_train, train_mask_fit, sample_weight=train_weights)
    print("✓ Model trained")
    print(f"   Features used: {len(X_train.columns)}")
    print()

    # Evaluate
    print("=" * 80)
    print("[6/6] Evaluating V7.1 performance...")
    print("=" * 80)

    test_mask_pred = pd.Series(True, index=X_test.index)
    y_test_pred_proba = predict_probabilities(model, X_test, test_mask_pred)
    y_test_pred = (y_test_pred_proba >= 0.5).astype(int)

    test_acc = accuracy_score(y_test, y_test_pred)
    test_auc = roc_auc_score(y_test, y_test_pred_proba)
    test_logloss = log_loss(y_test, y_test_pred_proba)

    print()
    print("=" * 80)
    print("V7.1 RESULTS")
    print("=" * 80)
    print(f"\nTest Set Performance:")
    print(f"  Accuracy:  {test_acc:.4f} ({test_acc:.2%})")
    print(f"  ROC-AUC:   {test_auc:.4f}")
    print(f"  Log Loss:  {test_logloss:.4f}")

    # Targets
    print(f"\n🎯 Target Achievement:")
    print(f"  Accuracy:  {'✓' if test_acc >= 0.62 else '✗'} {test_acc:.2%} (target: 62%+)")
    print(f"  Log Loss:  {'✓' if test_logloss <= 0.670 else '✗'} {test_logloss:.4f} (target: ≤0.670)")

    # V7.0 comparison
    v7_0_acc = 0.6089
    v7_0_logloss = 0.6752
    improvement_acc = (test_acc - v7_0_acc) * 100
    improvement_logloss = v7_0_logloss - test_logloss

    print(f"\n📊 vs V7.0:")
    print(f"  Accuracy:  {'+' if improvement_acc > 0 else ''}{improvement_acc:.2f} pp")
    print(f"  Log Loss:  {'+' if improvement_logloss > 0 else ''}{improvement_logloss:.4f}")

    # Confidence buckets
    evaluate_confidence_buckets(y_test.values, y_test_pred_proba, "V7.1")

    # Feature importance for goalie features
    print("\n" + "="*80)
    print("Goalie Feature Importance:")
    print("="*80)

    feature_names = X_train.columns.tolist()
    coefficients = model.named_steps['clf'].coef_[0]

    goalie_features = [
        (name, coef) for name, coef in zip(feature_names, coefficients)
        if 'goalie' in name.lower()
    ]
    goalie_features.sort(key=lambda x: abs(x[1]), reverse=True)

    print(f"{'Feature':<40} {'Coefficient':>12} {'Abs Importance':>15}")
    print("-" * 70)
    for name, coef in goalie_features[:15]:
        print(f"{name:<40} {coef:>12.4f} {abs(coef):>15.4f}")

    print("\n" + "="*80)
    print(f"V7.1 Training Complete!")
    print(f"Finished: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*80)


if __name__ == "__main__":
    main()
