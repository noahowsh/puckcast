#!/usr/bin/env python3
"""
Verify that reconstructed features match pipeline features.

This script checks if build_matchup_features() produces features that match
what the pipeline computed for historical games.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'prediction'))

import pandas as pd
import numpy as np

from nhl_prediction.pipeline import build_dataset
from predict_full import build_matchup_features, add_league_hw_feature, V70_FEATURES
from nhl_prediction.situational_features import add_situational_features


def main():
    print("=" * 80)
    print("FEATURE RECONSTRUCTION VERIFICATION")
    print("Comparing reconstructed features vs actual pipeline features")
    print("=" * 80)

    # Load dataset
    print("\n1️⃣  Loading dataset...")
    seasons = ['20242025', '20232024', '20222023', '20212022']
    dataset = build_dataset(seasons)

    games = add_league_hw_feature(dataset.games)
    games = add_situational_features(games)

    situational_features = ['fatigue_index_diff', 'third_period_trailing_perf_diff',
                    'travel_distance_diff', 'divisional_matchup',
                    'post_break_game_home', 'post_break_game_away', 'post_break_game_diff']
    available_situational = [f for f in situational_features if f in games.columns]

    features_full = pd.concat([
        dataset.features,
        games[available_situational],
        games[['league_hw_100']],
    ], axis=1)

    available_v70 = [f for f in V70_FEATURES if f in features_full.columns]
    features_v70 = features_full[available_v70]

    games['seasonId_str'] = games['seasonId'].astype(str)
    games_sorted = games.sort_values('gameDate').copy()

    print(f"   ✅ Loaded {len(games)} games with {len(available_v70)} features")

    # Sample 20 games from mid-season (where we have good data)
    print("\n2️⃣  Sampling games for verification...")

    # Get games from 2023-24 season (well-established data)
    season_2324 = games_sorted[games_sorted['seasonId_str'] == '20232024']
    # Take games from the middle of the season
    mid_start = len(season_2324) // 3
    mid_end = 2 * len(season_2324) // 3
    sample_games = season_2324.iloc[mid_start:mid_end].sample(n=20, random_state=42)

    print(f"   Selected 20 games from 2023-24 season")

    # Compare features
    print("\n3️⃣  Comparing features for each game...")

    feature_columns = list(available_v70)

    total_features = 0
    matching_features = 0
    close_features = 0  # Within 5%
    mismatches = []

    for idx, game in sample_games.iterrows():
        game_date = game['gameDate']
        home_id = game['teamId_home']
        away_id = game['teamId_away']
        season_id = str(game['seasonId'])

        # Get games before this one
        games_before = games_sorted[pd.to_datetime(games_sorted['gameDate']) < pd.to_datetime(game_date)].copy()
        games_before['seasonId_str'] = games_before['seasonId'].astype(str)

        # Reconstruct features
        reconstructed = build_matchup_features(
            home_id, away_id, season_id,
            games_before, feature_columns, game_date
        )

        if reconstructed is None:
            print(f"   ⚠️  Could not reconstruct features for game {idx}")
            continue

        # Get pipeline features
        pipeline = features_v70.loc[idx]

        # Compare each feature
        for col in feature_columns:
            total_features += 1
            recon_val = reconstructed[col]
            pipe_val = pipeline[col]

            if pd.isna(recon_val) or pd.isna(pipe_val):
                continue

            if abs(recon_val - pipe_val) < 0.001:
                matching_features += 1
            elif abs(recon_val - pipe_val) / (abs(pipe_val) + 0.001) < 0.05:
                close_features += 1
            else:
                mismatches.append({
                    'game': idx,
                    'feature': col,
                    'reconstructed': recon_val,
                    'pipeline': pipe_val,
                    'diff': recon_val - pipe_val
                })

    # Results
    print("\n" + "=" * 80)
    print("VERIFICATION RESULTS")
    print("=" * 80)

    print(f"\nTotal features compared: {total_features}")
    print(f"Exact matches (±0.001): {matching_features} ({100*matching_features/total_features:.1f}%)")
    print(f"Close matches (±5%): {close_features} ({100*close_features/total_features:.1f}%)")
    print(f"Mismatches: {len(mismatches)} ({100*len(mismatches)/total_features:.1f}%)")

    if mismatches:
        print(f"\n📊 TOP MISMATCHES (showing first 20):")
        mismatch_df = pd.DataFrame(mismatches)
        mismatch_df['abs_diff'] = mismatch_df['diff'].abs()
        top_mismatches = mismatch_df.nlargest(20, 'abs_diff')

        for _, row in top_mismatches.iterrows():
            print(f"   {row['feature']}: recon={row['reconstructed']:.4f}, pipe={row['pipeline']:.4f}, diff={row['diff']:.4f}")

        # Group by feature to see which features have the most issues
        print(f"\n📊 MISMATCHES BY FEATURE:")
        feature_counts = mismatch_df['feature'].value_counts().head(10)
        for feat, count in feature_counts.items():
            avg_diff = mismatch_df[mismatch_df['feature'] == feat]['abs_diff'].mean()
            print(f"   {feat}: {count} mismatches, avg diff: {avg_diff:.4f}")
    else:
        print("\n✅ All features match perfectly!")


if __name__ == "__main__":
    main()
