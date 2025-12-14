#!/usr/bin/env python3
"""
Build Feature Store - Pre-compute all features for fast model testing

This script pre-computes ALL features (base + situational + V7.9 engineered)
for all available seasons and saves them to a single parquet file.

This eliminates the need to recompute features during model testing,
reducing test time from hours to seconds.

Usage:
    python training/build_feature_store.py

Output:
    data/feature_store.parquet - All games with all features pre-computed
"""

import sys
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path
from datetime import datetime

import pandas as pd
import numpy as np

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.situational_features import add_situational_features


# All available seasons
ALL_SEASONS = [
    '20172018', '20182019', '20192020', '20202021',
    '20212022', '20222023', '20232024', '20242025',
]

# V7.9 engineered feature definitions
def create_v79_engineered_features(features_df, games_df):
    """Create V7.9 engineered features."""
    eng = pd.DataFrame(index=features_df.index)

    # Momentum acceleration
    if 'rolling_goal_diff_3_diff' in features_df.columns and 'rolling_goal_diff_10_diff' in features_df.columns:
        eng['goal_momentum_accel'] = (
            features_df['rolling_goal_diff_3_diff'] -
            features_df['rolling_goal_diff_10_diff']
        )

    if 'rolling_xg_diff_3_diff' in features_df.columns and 'rolling_xg_diff_10_diff' in features_df.columns:
        eng['xg_momentum_accel'] = (
            features_df['rolling_xg_diff_3_diff'] -
            features_df['rolling_xg_diff_10_diff']
        )

    # Interaction features
    if 'rolling_xg_diff_10_diff' in features_df.columns and 'rolling_corsi_10_diff' in features_df.columns:
        eng['xg_x_corsi_10'] = (
            features_df['rolling_xg_diff_10_diff'] *
            features_df['rolling_corsi_10_diff']
        )

    if 'elo_diff_pre' in features_df.columns and 'rest_diff' in features_df.columns:
        eng['elo_x_rest'] = (
            features_df['elo_diff_pre'] *
            features_df['rest_diff']
        )

    # Dominance score
    if all(c in features_df.columns for c in ['elo_expectation_home', 'rolling_win_pct_10_diff', 'rolling_xg_diff_10_diff']):
        eng['dominance'] = (
            features_df['elo_expectation_home'] * 0.4 +
            features_df['rolling_win_pct_10_diff'].clip(-0.5, 0.5) + 0.5 * 0.3 +
            (features_df['rolling_xg_diff_10_diff'].clip(-1, 1) + 1) / 2 * 0.3
        )

    # Day of week
    games_df = games_df.copy()
    games_df['gameDate'] = pd.to_datetime(games_df['gameDate'])
    eng['is_saturday'] = (games_df['gameDate'].dt.dayofweek == 5).astype(int).values
    eng['is_sunday'] = (games_df['gameDate'].dt.dayofweek == 6).astype(int).values
    eng['is_weekday'] = (games_df['gameDate'].dt.dayofweek < 5).astype(int).values

    return eng


def main():
    start_time = datetime.now()
    print("=" * 70)
    print("BUILDING FEATURE STORE")
    print("=" * 70)
    print(f"Start time: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Step 1: Load base dataset with all seasons
    print("Step 1/4: Loading base dataset...")
    print(f"  Seasons: {', '.join(ALL_SEASONS)}")
    dataset = build_dataset(ALL_SEASONS)
    games = dataset.games.copy()
    features = dataset.features.copy()
    target = dataset.target.copy()
    print(f"  Loaded {len(games):,} games with {len(features.columns)} base features")

    # Step 2: Add situational features (this is the slow part!)
    print()
    print("Step 2/4: Computing situational features (this takes a few minutes)...")
    games_with_sit = add_situational_features(games)
    sit_cols = [c for c in games_with_sit.columns if any(k in c for k in
        ['fatigue', 'trailing', 'travel', 'divisional', 'break'])]
    print(f"  Added {len(sit_cols)} situational features")

    # Step 3: Create V7.9 engineered features
    print()
    print("Step 3/4: Creating V7.9 engineered features...")
    v79_eng = create_v79_engineered_features(features, games)
    print(f"  Created {len(v79_eng.columns)} V7.9 engineered features")

    # Step 4: Combine everything into feature store
    print()
    print("Step 4/4: Building feature store...")

    # Game metadata columns to keep
    game_cols = ['gameId', 'seasonId', 'gameDate', 'homeTeam', 'awayTeam',
                 'homeScore', 'awayScore']
    game_cols = [c for c in game_cols if c in games.columns]

    # Get situational columns that aren't already in base features
    existing_cols = set(features.columns)
    new_sit_cols = [c for c in sit_cols if c not in existing_cols]

    # Combine all features (avoiding duplicates)
    feature_store = pd.concat([
        games[game_cols].reset_index(drop=True),
        features.reset_index(drop=True),
        games_with_sit[new_sit_cols].reset_index(drop=True),
        v79_eng.reset_index(drop=True),
        target.reset_index(drop=True).to_frame('target'),
    ], axis=1)

    # Remove any remaining duplicate columns (keep first)
    feature_store = feature_store.loc[:, ~feature_store.columns.duplicated()]

    # Fill any NaN values
    feature_store = feature_store.fillna(0)

    # Save to parquet
    output_path = Path(__file__).parent.parent / 'data' / 'feature_store.parquet'
    feature_store.to_parquet(output_path, index=False)

    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()

    print()
    print("=" * 70)
    print("FEATURE STORE COMPLETE")
    print("=" * 70)
    print(f"  Output: {output_path}")
    print(f"  Size: {output_path.stat().st_size / 1024 / 1024:.2f} MB")
    print(f"  Games: {len(feature_store):,}")
    print(f"  Total columns: {len(feature_store.columns)}")
    print(f"    - Game metadata: {len(game_cols)}")
    print(f"    - Base features: {len(features.columns)}")
    print(f"    - Situational features: {len(sit_cols)}")
    print(f"    - V7.9 engineered: {len(v79_eng.columns)}")
    print(f"    - Target: 1")
    print(f"  Build time: {duration:.1f} seconds ({duration/60:.1f} minutes)")
    print()
    print("Feature columns:")
    for i, col in enumerate(feature_store.columns):
        if i < 10 or i >= len(feature_store.columns) - 5:
            print(f"  {i+1:3d}. {col}")
        elif i == 10:
            print(f"  ... ({len(feature_store.columns) - 15} more) ...")


if __name__ == "__main__":
    main()
