#!/usr/bin/env python3
"""
V7.3 Error Analysis - Find patterns in incorrect predictions.

Analyzes the 475 games (out of 1,230) that V7.3 gets wrong to identify:
- Which teams are hardest to predict
- Situational patterns (B2B, rest, divisional, etc.)
- Confidence distribution of errors
- Specific matchup weaknesses
"""

import sys
import pickle
from pathlib import Path
from datetime import datetime
from collections import defaultdict

import pandas as pd
import numpy as np
from sklearn.metrics import accuracy_score

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, predict_probabilities
from nhl_prediction.train import compute_season_weights
from nhl_prediction.situational_features import add_situational_features

# Configuration
TRAIN_SEASONS = ["20212022", "20222023"]
TEST_SEASON = "20232024"
OPTIMAL_C = 0.05
OPTIMAL_DECAY = 1.0


def analyze_errors_by_team(games_df: pd.DataFrame, errors_df: pd.DataFrame):
    """Analyze which teams are hardest to predict."""
    print("\n" + "="*80)
    print("ERROR ANALYSIS BY TEAM")
    print("="*80)

    # Count errors for each team (both home and away)
    team_stats = defaultdict(lambda: {'total': 0, 'errors': 0, 'home_errors': 0, 'away_errors': 0})

    for _, game in errors_df.iterrows():
        home_team = game['teamAbbrev_home']
        away_team = game['teamAbbrev_away']

        team_stats[home_team]['total'] += 1
        team_stats[home_team]['errors'] += 1
        team_stats[home_team]['home_errors'] += 1

        team_stats[away_team]['total'] += 1
        team_stats[away_team]['errors'] += 1
        team_stats[away_team]['away_errors'] += 1

    # Count total appearances for each team
    for _, game in games_df.iterrows():
        home_team = game['teamAbbrev_home']
        away_team = game['teamAbbrev_away']

        if home_team not in team_stats or team_stats[home_team]['total'] == 0:
            team_stats[home_team]['total'] = 0
            team_stats[home_team]['errors'] = 0
            team_stats[home_team]['home_errors'] = 0
            team_stats[away_team]['away_errors'] = 0

        team_stats[home_team]['total'] += 1
        team_stats[away_team]['total'] += 1

    # Calculate error rates
    team_error_rates = []
    for team, stats in team_stats.items():
        if stats['total'] > 0:
            error_rate = stats['errors'] / stats['total']
            team_error_rates.append({
                'team': team,
                'total_games': stats['total'],
                'errors': stats['errors'],
                'error_rate': error_rate,
                'home_errors': stats['home_errors'],
                'away_errors': stats['away_errors']
            })

    # Sort by error rate
    team_error_rates.sort(key=lambda x: x['error_rate'], reverse=True)

    print(f"\nTop 15 Hardest Teams to Predict:")
    print(f"{'Team':6s}  {'Games':>5s}  {'Errors':>6s}  {'Error%':>7s}  {'Home':>5s}  {'Away':>5s}")
    print("-" * 60)
    for team_stats in team_error_rates[:15]:
        print(f"{team_stats['team']:6s}  {team_stats['total_games']:5d}  "
              f"{team_stats['errors']:6d}  {team_stats['error_rate']*100:6.1f}%  "
              f"{team_stats['home_errors']:5d}  {team_stats['away_errors']:5d}")

    print(f"\nEasiest 10 Teams to Predict:")
    print(f"{'Team':6s}  {'Games':>5s}  {'Errors':>6s}  {'Error%':>7s}  {'Home':>5s}  {'Away':>5s}")
    print("-" * 60)
    for team_stats in team_error_rates[-10:]:
        print(f"{team_stats['team']:6s}  {team_stats['total_games']:5d}  "
              f"{team_stats['errors']:6d}  {team_stats['error_rate']*100:6.1f}%  "
              f"{team_stats['home_errors']:5d}  {team_stats['away_errors']:5d}")


def analyze_errors_by_situation(errors_df: pd.DataFrame):
    """Analyze situational patterns in errors."""
    print("\n" + "="*80)
    print("ERROR ANALYSIS BY SITUATION")
    print("="*80)

    # B2B analysis
    b2b_both = len(errors_df[(errors_df['is_b2b_home'] == 1) & (errors_df['is_b2b_away'] == 1)])
    b2b_home_only = len(errors_df[(errors_df['is_b2b_home'] == 1) & (errors_df['is_b2b_away'] == 0)])
    b2b_away_only = len(errors_df[(errors_df['is_b2b_home'] == 0) & (errors_df['is_b2b_away'] == 1)])
    b2b_neither = len(errors_df[(errors_df['is_b2b_home'] == 0) & (errors_df['is_b2b_away'] == 0)])

    print(f"\nBack-to-Back Analysis:")
    print(f"  Both teams B2B: {b2b_both}")
    print(f"  Home B2B only: {b2b_home_only}")
    print(f"  Away B2B only: {b2b_away_only}")
    print(f"  Neither B2B: {b2b_neither}")

    # Rest differential
    print(f"\nRest Differential in Errors:")
    print(f"  Mean: {errors_df['rest_days_diff'].mean():.2f} days")
    print(f"  Median: {errors_df['rest_days_diff'].median():.2f} days")
    print(f"  Std: {errors_df['rest_days_diff'].std():.2f} days")

    # Check if divisional is available
    if 'is_divisional_matchup' in errors_df.columns:
        divisional_errors = len(errors_df[errors_df['is_divisional_matchup'] == 1])
        non_divisional_errors = len(errors_df[errors_df['is_divisional_matchup'] == 0])
        print(f"\nDivisional vs Non-Divisional:")
        print(f"  Divisional matchup errors: {divisional_errors}")
        print(f"  Non-divisional errors: {non_divisional_errors}")


def analyze_errors_by_confidence(predictions: np.ndarray, actuals: np.ndarray,
                                 errors_mask: np.ndarray):
    """Analyze error distribution by confidence level."""
    print("\n" + "="*80)
    print("ERROR ANALYSIS BY CONFIDENCE LEVEL")
    print("="*80)

    # Calculate confidence (distance from 0.5)
    confidence = np.abs(predictions - 0.5) * 100  # Convert to points

    # Define confidence buckets
    buckets = [
        ("Very High (20+ pts)", 20, 100),
        ("High (15-20 pts)", 15, 20),
        ("Medium (10-15 pts)", 10, 15),
        ("Low (5-10 pts)", 5, 10),
        ("Very Low (0-5 pts)", 0, 5),
    ]

    print(f"\n{'Confidence':20s}  {'Total':>6s}  {'Errors':>7s}  {'Error%':>8s}")
    print("-" * 60)

    for name, min_conf, max_conf in buckets:
        mask = (confidence >= min_conf) & (confidence < max_conf)
        total = mask.sum()
        errors = (mask & errors_mask).sum()
        error_rate = errors / total * 100 if total > 0 else 0

        print(f"{name:20s}  {total:6d}  {errors:7d}  {error_rate:7.1f}%")


def analyze_head_to_head_errors(errors_df: pd.DataFrame):
    """Analyze specific head-to-head matchups with multiple errors."""
    print("\n" + "="*80)
    print("PROBLEMATIC HEAD-TO-HEAD MATCHUPS")
    print("="*80)

    # Count errors by matchup (order-independent)
    matchup_errors = defaultdict(int)

    for _, game in errors_df.iterrows():
        home = game['teamAbbrev_home']
        away = game['teamAbbrev_away']
        # Create order-independent key
        matchup = tuple(sorted([home, away]))
        matchup_errors[matchup] += 1

    # Find matchups with multiple errors
    problematic = [(matchup, count) for matchup, count in matchup_errors.items() if count >= 3]
    problematic.sort(key=lambda x: x[1], reverse=True)

    print(f"\nMatchups with 3+ Errors (out of ~6-8 games):")
    print(f"{'Matchup':20s}  {'Errors':>7s}")
    print("-" * 40)

    for (team1, team2), error_count in problematic[:20]:
        print(f"{team1} vs {team2:6s}  {error_count:7d}")

    return problematic


def main():
    print("="*80)
    print("V7.3 Error Analysis")
    print("="*80)
    print(f"Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Load V7.0 dataset
    print("Loading dataset...")
    dataset = build_dataset(TRAIN_SEASONS + [TEST_SEASON])
    print(f"✓ Loaded {len(dataset.games)} games")

    # Add V7.3 situational features
    print("Adding V7.3 situational features...")
    games_with_situational = add_situational_features(dataset.games)

    # Identify available V7.3 features
    v7_3_features = [
        'fatigue_index_diff', 'third_period_trailing_diff',
        'travel_distance_diff', 'is_divisional_matchup',
        'is_post_break_home', 'is_post_break_away'
    ]
    available_features = [f for f in v7_3_features if f in games_with_situational.columns]

    # Combine features
    features_v7_3 = pd.concat([
        dataset.features,
        games_with_situational[available_features]
    ], axis=1)

    print(f"✓ Total features: {len(features_v7_3.columns)}")

    # Train/test split
    train_mask = dataset.games['seasonId'].isin(TRAIN_SEASONS)
    test_mask = dataset.games['seasonId'] == TEST_SEASON

    X_train = features_v7_3[train_mask]
    y_train = dataset.target[train_mask]
    X_test = features_v7_3[test_mask]
    y_test = dataset.target[test_mask]

    train_weights = compute_season_weights(
        dataset.games[train_mask],
        TRAIN_SEASONS,
        decay_factor=OPTIMAL_DECAY
    )

    train_mask_fit = dataset.games[train_mask]['games_played_prior_home'] > 10

    print(f"Training games: {len(X_train)}")
    print(f"Test games: {len(X_test)}")
    print()

    # Train model
    print("Training V7.3 model...")
    model = create_baseline_model(C=OPTIMAL_C)
    model = fit_model(model, X_train, y_train, train_mask_fit, sample_weight=train_weights)
    print("✓ Model trained")
    print()

    # Get predictions
    print("Generating predictions...")
    test_mask_predict = pd.Series([True] * len(X_test), index=X_test.index)
    y_pred_proba = predict_probabilities(model, X_test, test_mask_predict)
    y_pred = (y_pred_proba >= 0.5).astype(int)

    # Calculate accuracy
    accuracy = accuracy_score(y_test, y_pred)
    print(f"Test Accuracy: {accuracy*100:.2f}%")
    print(f"Correct: {(y_pred == y_test).sum()}")
    print(f"Incorrect: {(y_pred != y_test).sum()}")
    print()

    # Identify errors
    errors_mask = (y_pred != y_test).values
    test_games = dataset.games[test_mask].copy()
    test_games['predicted'] = y_pred
    test_games['actual'] = y_test.values
    test_games['pred_proba'] = y_pred_proba
    test_games['correct'] = ~errors_mask

    errors_df = test_games[errors_mask].copy()

    # Run analyses
    analyze_errors_by_team(test_games, errors_df)
    analyze_errors_by_situation(errors_df)
    analyze_errors_by_confidence(y_pred_proba, y_test.values, errors_mask)
    problematic_matchups = analyze_head_to_head_errors(errors_df)

    # Save error details for further analysis
    output_file = Path("v7_3_error_analysis.csv")
    errors_df.to_csv(output_file, index=False)
    print(f"\n✓ Error details saved to: {output_file}")

    # Summary
    print("\n" + "="*80)
    print("KEY FINDINGS")
    print("="*80)
    print(f"\nTotal test games: {len(test_games)}")
    print(f"Correct predictions: {(~errors_mask).sum()} ({(~errors_mask).sum()/len(test_games)*100:.1f}%)")
    print(f"Incorrect predictions: {errors_mask.sum()} ({errors_mask.sum()/len(test_games)*100:.1f}%)")
    print(f"\nTop 5 problematic matchups:")
    for i, ((team1, team2), count) in enumerate(problematic_matchups[:5], 1):
        print(f"  {i}. {team1} vs {team2}: {count} errors")

    print("\n" + "="*80)
    print("Error Analysis Complete!")
    print("="*80)


if __name__ == "__main__":
    main()
