#!/usr/bin/env python3
"""
Audit: Compare predict_full.py feature reconstruction vs pipeline features.

This script does a detailed side-by-side comparison to identify exactly where
the two methods diverge.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

import pandas as pd
import numpy as np
from datetime import datetime

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.features import engineer_team_features, ROLL_WINDOWS
from nhl_prediction.data_ingest import build_game_dataframe, fetch_multi_season_logs

# Import predict_full functions
sys.path.insert(0, str(Path(__file__).parent.parent / 'prediction'))
from predict_full import compute_team_rolling_stats, V70_FEATURES


def compare_methods():
    """Compare pipeline vs predict_full feature computation."""

    print("=" * 80)
    print("FEATURE METHOD AUDIT: Pipeline vs predict_full.py")
    print("=" * 80)

    # Load dataset via pipeline
    seasons = ['20242025', '20232024', '20222023', '20212022']
    print(f"\nLoading {len(seasons)} seasons via pipeline...")
    dataset = build_dataset(seasons)

    games = dataset.games.copy()
    features = dataset.features.copy()

    print(f"Loaded {len(games)} games")
    print(f"Pipeline features shape: {features.shape}")

    # Pick a sample of games to compare - use games from 2024-25 with enough history
    # Just take 10 games from middle of season
    sorted_games = games.sort_values('gameDate')
    mid_point = len(sorted_games) // 2
    sample_games = sorted_games.iloc[mid_point:mid_point+10]
    print(f"Sample game dates: {sample_games['gameDate'].min()} to {sample_games['gameDate'].max()}")

    print(f"\nComparing features for {len(sample_games)} sample games...")

    # For each game, compare pipeline features vs reconstructed features
    discrepancies = []

    for idx, game in sample_games.iterrows():
        home_id = game['teamId_home']
        away_id = game['teamId_away']
        game_date = game['gameDate']
        season_id = str(game.get('seasonId', game.get('season_home', '20242025')))

        # Get pipeline features for this game
        pipeline_feats = features.loc[idx]

        # Get historical games for predict_full reconstruction
        all_games = dataset.games.copy()
        all_games['seasonId_str'] = all_games['seasonId'].astype(str)
        game_dt = pd.to_datetime(game_date)
        eligible = all_games[pd.to_datetime(all_games['gameDate']) < game_dt].copy()

        # Find home team's games
        home_games = eligible[
            ((eligible['teamId_home'] == home_id) | (eligible['teamId_away'] == home_id)) &
            (eligible['seasonId_str'] == season_id)
        ].sort_values('gameDate')

        # Find away team's games
        away_games = eligible[
            ((eligible['teamId_home'] == away_id) | (eligible['teamId_away'] == away_id)) &
            (eligible['seasonId_str'] == season_id)
        ].sort_values('gameDate')

        # Compute fresh rolling stats using predict_full method
        home_rolling = compute_team_rolling_stats(home_id, home_games, windows=[3, 5, 10])
        away_rolling = compute_team_rolling_stats(away_id, away_games, windows=[3, 5, 10])

        # Compare key features
        feature_comparisons = []

        # Rolling features
        rolling_map = {
            'rolling_win_pct_5_diff': ('win_pct_5', 'win_pct_5'),
            'rolling_goal_diff_5_diff': ('goal_diff_5', 'goal_diff_5'),
            'rolling_xg_diff_5_diff': ('xg_diff_5', 'xg_diff_5'),
            'season_win_pct_diff': ('season_win_pct', 'season_win_pct'),
            'season_goal_diff_avg_diff': ('season_goal_diff_avg', 'season_goal_diff_avg'),
            'momentum_win_pct_diff': ('momentum_win_pct', 'momentum_win_pct'),
            'momentum_goal_diff_diff': ('momentum_goal_diff', 'momentum_goal_diff'),
            'season_shot_margin_diff': ('season_shot_margin', 'season_shot_margin'),
        }

        for feat_name, (home_key, away_key) in rolling_map.items():
            if feat_name in pipeline_feats.index:
                pipeline_val = pipeline_feats[feat_name]

                home_val = home_rolling.get(home_key, 0.0)
                away_val = away_rolling.get(away_key, 0.0)
                reconstructed_val = home_val - away_val

                diff = abs(pipeline_val - reconstructed_val)

                feature_comparisons.append({
                    'feature': feat_name,
                    'pipeline': pipeline_val,
                    'reconstructed': reconstructed_val,
                    'diff': diff,
                    'pct_diff': diff / (abs(pipeline_val) + 0.0001) * 100
                })

        # Store for analysis
        for comp in feature_comparisons:
            comp['game_idx'] = idx
            comp['game_date'] = game_date
            discrepancies.append(comp)

    # Analyze discrepancies
    df = pd.DataFrame(discrepancies)

    print("\n" + "=" * 80)
    print("FEATURE COMPARISON SUMMARY")
    print("=" * 80)

    # Group by feature
    summary = df.groupby('feature').agg({
        'diff': ['mean', 'std', 'max'],
        'pct_diff': ['mean', 'max']
    }).round(4)

    print("\nMean absolute difference by feature:")
    print(summary.to_string())

    # Find worst discrepancies
    print("\n" + "-" * 60)
    print("TOP 10 LARGEST DISCREPANCIES:")
    print("-" * 60)
    worst = df.nlargest(10, 'diff')
    for _, row in worst.iterrows():
        print(f"  {row['feature']:35} | Pipeline: {row['pipeline']:8.4f} | Reconstructed: {row['reconstructed']:8.4f} | Diff: {row['diff']:.4f}")

    # Calculate overall alignment
    avg_diff = df['diff'].mean()
    max_diff = df['diff'].max()

    print("\n" + "=" * 80)
    print("OVERALL ALIGNMENT")
    print("=" * 80)
    print(f"  Average difference: {avg_diff:.6f}")
    print(f"  Maximum difference: {max_diff:.6f}")

    if avg_diff < 0.01:
        print("\n  ✅ EXCELLENT: Methods are well-aligned (avg diff < 0.01)")
    elif avg_diff < 0.05:
        print("\n  ⚠️  GOOD: Methods are reasonably aligned (avg diff < 0.05)")
    else:
        print("\n  ❌ POOR: Methods have significant divergence")

    # Now test prediction accuracy
    print("\n" + "=" * 80)
    print("PREDICTION ACCURACY COMPARISON")
    print("=" * 80)

    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler

    # Filter to V70 features
    available_v70 = [f for f in V70_FEATURES if f in features.columns]
    X = features[available_v70].fillna(0)
    y = dataset.target

    # Use 2024-25 as test set
    test_mask = games['seasonId'] == 20242025
    train_mask = ~test_mask

    X_train = X.loc[train_mask]
    y_train = y.loc[train_mask]
    X_test = X.loc[test_mask]
    y_test = y.loc[test_mask]

    print(f"\n  Training on {len(X_train)} games (prior seasons)")
    print(f"  Testing on {len(X_test)} games (2024-25)")

    # Train model
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)

    model = LogisticRegression(C=0.005, max_iter=1000, random_state=42)
    model.fit(X_train_scaled, y_train)

    # Predict
    y_pred = model.predict(X_test_scaled)
    accuracy = (y_pred == y_test).mean()

    print(f"\n  Pipeline features accuracy: {accuracy:.4f} ({accuracy*100:.2f}%)")

    return df


if __name__ == '__main__':
    compare_methods()
