#!/usr/bin/env python3
"""
Compare old (buggy) vs new (fixed) feature construction methods.

This script simulates predictions on historical games to measure the
accuracy impact of the feature construction fixes.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'prediction'))

import pandas as pd
import numpy as np
from datetime import datetime

from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import create_baseline_model, fit_model, tune_logreg_c
from nhl_prediction.situational_features import add_situational_features


def add_league_hw_feature(games: pd.DataFrame) -> pd.DataFrame:
    """Add rolling league-wide home win rate features."""
    games = games.sort_values('gameDate').copy()
    games['league_hw_100'] = games['home_win'].rolling(
        window=100, min_periods=50
    ).mean().shift(1)
    games['league_hw_100'] = games['league_hw_100'].fillna(0.535)
    return games


def build_features_old_method(
    home_team_id: int,
    away_team_id: int,
    season_id: str,
    eligible_games: pd.DataFrame,
    features_full: pd.DataFrame,
    feature_columns: list,
) -> pd.Series | None:
    """OLD BUGGY METHOD: Find home team's HOME games and away team's AWAY games, then average."""
    # Find home team's most recent HOME game
    home_recent = eligible_games[
        (eligible_games['teamId_home'] == home_team_id) &
        (eligible_games['seasonId_str'] == season_id)
    ].tail(1)

    # Find away team's most recent AWAY game
    away_recent = eligible_games[
        (eligible_games['teamId_away'] == away_team_id) &
        (eligible_games['seasonId_str'] == season_id)
    ].tail(1)

    if len(home_recent) == 0 or len(away_recent) == 0:
        return None

    home_idx = home_recent.index[0]
    away_idx = away_recent.index[0]

    home_features = features_full.loc[home_idx]
    away_features = features_full.loc[away_idx]

    # BUGGY: Average the differential features
    matchup_features = (home_features + away_features) / 2
    return matchup_features.reindex(feature_columns, fill_value=0.0)


def build_features_new_method(
    home_team_id: int,
    away_team_id: int,
    season_id: str,
    eligible_games: pd.DataFrame,
    feature_columns: list,
    game_date: str | None = None,
) -> pd.Series | None:
    """NEW FIXED METHOD: Find each team's most recent game, extract individual stats, compute proper diff."""
    # Find home team's most recent game (home OR away)
    home_as_home = eligible_games[
        (eligible_games['teamId_home'] == home_team_id) &
        (eligible_games['seasonId_str'] == season_id)
    ]
    home_as_away = eligible_games[
        (eligible_games['teamId_away'] == home_team_id) &
        (eligible_games['seasonId_str'] == season_id)
    ]
    home_games = pd.concat([home_as_home, home_as_away]).sort_values('gameDate')

    # Find away team's most recent game (home OR away)
    away_as_home = eligible_games[
        (eligible_games['teamId_home'] == away_team_id) &
        (eligible_games['seasonId_str'] == season_id)
    ]
    away_as_away = eligible_games[
        (eligible_games['teamId_away'] == away_team_id) &
        (eligible_games['seasonId_str'] == season_id)
    ]
    away_games = pd.concat([away_as_home, away_as_away]).sort_values('gameDate')

    if len(home_games) == 0 or len(away_games) == 0:
        return None

    home_recent = home_games.iloc[-1]
    away_recent = away_games.iloc[-1]

    home_team_was_home = home_recent['teamId_home'] == home_team_id
    away_team_was_home = away_recent['teamId_home'] == away_team_id

    # Compute actual rest days if game_date provided
    home_rest_days = None
    away_rest_days = None
    home_games_last_3d = 0
    home_games_last_6d = 0

    if game_date:
        try:
            new_game_dt = pd.to_datetime(game_date)
            home_last_game_dt = pd.to_datetime(home_recent['gameDate'])
            away_last_game_dt = pd.to_datetime(away_recent['gameDate'])
            home_rest_days = (new_game_dt - home_last_game_dt).days
            away_rest_days = (new_game_dt - away_last_game_dt).days

            cutoff_3d = new_game_dt - pd.Timedelta(days=3)
            cutoff_6d = new_game_dt - pd.Timedelta(days=6)
            home_dates = pd.to_datetime(home_games['gameDate'])
            home_games_last_3d = int((home_dates >= cutoff_3d).sum())
            home_games_last_6d = int((home_dates >= cutoff_6d).sum())
        except:
            pass

    matchup = {}
    for col in feature_columns:
        # Handle schedule features with computed values
        if col == 'rest_diff' and home_rest_days is not None and away_rest_days is not None:
            matchup[col] = home_rest_days - away_rest_days
        elif col == 'is_b2b_home' and home_rest_days is not None:
            matchup[col] = 1 if home_rest_days <= 1 else 0
        elif col == 'is_b2b_away' and away_rest_days is not None:
            matchup[col] = 1 if away_rest_days <= 1 else 0
        elif col == 'games_last_3d_home' and game_date:
            matchup[col] = home_games_last_3d
        elif col == 'games_last_6d_home' and game_date:
            matchup[col] = home_games_last_6d
        elif col.endswith('_diff'):
            base = col[:-5]
            home_col = f"{base}_home"
            away_col = f"{base}_away"

            if home_col in home_recent.index and away_col in home_recent.index:
                if home_team_was_home:
                    home_team_stat = home_recent[home_col]
                else:
                    home_team_stat = home_recent[away_col]

                if away_team_was_home:
                    away_team_stat = away_recent[home_col]
                else:
                    away_team_stat = away_recent[away_col]

                matchup[col] = home_team_stat - away_team_stat
            else:
                matchup[col] = 0.0

        elif col in ['elo_diff_pre', 'elo_expectation_home']:
            if col in home_recent.index:
                matchup[col] = home_recent[col]
            else:
                matchup[col] = 0.0

        elif col == 'league_hw_100':
            if col in home_recent.index:
                matchup[col] = home_recent[col]
            else:
                matchup[col] = 0.535

        elif col.endswith('_home'):
            if col in home_recent.index:
                if home_team_was_home:
                    matchup[col] = home_recent[col]
                else:
                    away_version = col.replace('_home', '_away')
                    if away_version in home_recent.index:
                        matchup[col] = home_recent[away_version]
                    else:
                        matchup[col] = 0.0
            else:
                matchup[col] = 0.0

        elif col.endswith('_away'):
            if col in away_recent.index:
                if away_team_was_home:
                    home_version = col.replace('_away', '_home')
                    if home_version in away_recent.index:
                        matchup[col] = away_recent[home_version]
                    else:
                        matchup[col] = 0.0
                else:
                    matchup[col] = away_recent[col]
            else:
                matchup[col] = 0.0
        else:
            if col in home_recent.index:
                matchup[col] = home_recent[col]
            else:
                matchup[col] = 0.0

    return pd.Series(matchup).reindex(feature_columns, fill_value=0.0)


V70_FEATURES = [
    'league_hw_100',
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


def main():
    print("=" * 80)
    print("FEATURE CONSTRUCTION METHOD COMPARISON")
    print("Comparing OLD (buggy) vs NEW (fixed) approaches on historical games")
    print("=" * 80)

    # Load dataset
    print("\n1️⃣  Loading dataset...")
    seasons = ['20242025', '20232024', '20222023', '20212022']
    dataset = build_dataset(seasons)

    games = add_league_hw_feature(dataset.games)
    games = add_situational_features(games)

    # Build features DataFrame
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

    print(f"   ✅ Loaded {len(games)} games with {len(available_v70)} features")

    # Train model on first 3 seasons, test on last season
    print("\n2️⃣  Setting up train/test split...")
    games['seasonId_str'] = games['seasonId'].astype(str)

    # Debug: check what seasonIds we have
    print(f"   Available seasons: {games['seasonId'].unique()}")

    train_seasons = ['20212022', '20222023', '20232024']
    test_seasons = ['20242025']

    train_mask = games['seasonId_str'].isin(train_seasons)
    test_mask = games['seasonId_str'].isin(test_seasons)

    train_games = games.loc[train_mask].copy()
    train_features = features_v70.loc[train_mask].copy()
    train_target = dataset.target.loc[train_mask].copy()

    test_games = games.loc[test_mask].copy()
    test_target = dataset.target.loc[test_mask].copy()

    print(f"   Training: {len(train_games)} games (2021-24)")
    print(f"   Testing: {len(test_games)} games (2024-25)")

    # Train model
    print("\n3️⃣  Training model...")
    candidate_cs = [0.005, 0.01, 0.02, 0.05, 0.1]
    best_c = tune_logreg_c(candidate_cs, train_features, train_target, train_games,
                           sorted(train_games['seasonId'].unique().tolist()))

    model = create_baseline_model(C=best_c)
    training_mask = pd.Series(True, index=train_features.index)
    model = fit_model(model, train_features, train_target, training_mask)

    print(f"   ✅ Model trained with C={best_c}")

    # Simulate predictions on test set
    print("\n4️⃣  Simulating predictions on test set...")

    # We need to build eligible_games for each test game (games before that date)
    test_games_sorted = test_games.sort_values('gameDate')

    old_correct = 0
    new_correct = 0
    old_total = 0
    new_total = 0
    both_same = 0
    old_only_correct = 0
    new_only_correct = 0

    feature_columns = list(available_v70)

    for idx, game in test_games_sorted.iterrows():
        game_date = game['gameDate']
        home_id = game['teamId_home']
        away_id = game['teamId_away']
        season_id = str(game['seasonId'])
        actual_home_win = test_target.loc[idx]

        # Get games before this date for feature lookup
        all_games_before = games[pd.to_datetime(games['gameDate']) < pd.to_datetime(game_date)].copy()
        all_games_before['seasonId_str'] = all_games_before['seasonId'].astype(str)
        features_before = features_v70.loc[all_games_before.index]

        # Build features using OLD method
        old_features = build_features_old_method(
            home_id, away_id, season_id,
            all_games_before, features_before, feature_columns
        )

        # Build features using NEW method
        new_features = build_features_new_method(
            home_id, away_id, season_id,
            all_games_before, feature_columns, game_date
        )

        if old_features is not None:
            old_prob = model.predict_proba(old_features.values.reshape(1, -1))[0][1]
            old_pred_home_win = old_prob >= 0.5
            old_correct_pred = (old_pred_home_win == actual_home_win)
            old_correct += int(old_correct_pred)
            old_total += 1
        else:
            old_correct_pred = None

        if new_features is not None:
            new_prob = model.predict_proba(new_features.values.reshape(1, -1))[0][1]
            new_pred_home_win = new_prob >= 0.5
            new_correct_pred = (new_pred_home_win == actual_home_win)
            new_correct += int(new_correct_pred)
            new_total += 1
        else:
            new_correct_pred = None

        # Track disagreements
        if old_correct_pred is not None and new_correct_pred is not None:
            if old_correct_pred and new_correct_pred:
                both_same += 1
            elif old_correct_pred and not new_correct_pred:
                old_only_correct += 1
            elif new_correct_pred and not old_correct_pred:
                new_only_correct += 1

    # Results
    print("\n" + "=" * 80)
    print("RESULTS")
    print("=" * 80)

    old_acc = old_correct / old_total * 100 if old_total > 0 else 0
    new_acc = new_correct / new_total * 100 if new_total > 0 else 0

    print(f"\n📊 OLD METHOD (buggy averaging):")
    print(f"   Accuracy: {old_acc:.2f}% ({old_correct}/{old_total} games)")

    print(f"\n📊 NEW METHOD (proper differentials + schedule):")
    print(f"   Accuracy: {new_acc:.2f}% ({new_correct}/{new_total} games)")

    print(f"\n📈 COMPARISON:")
    print(f"   Difference: {new_acc - old_acc:+.2f} percentage points")
    print(f"   Both correct: {both_same}")
    print(f"   Only OLD correct: {old_only_correct}")
    print(f"   Only NEW correct: {new_only_correct}")

    if new_acc > old_acc:
        print(f"\n✅ NEW METHOD IS BETTER by {new_acc - old_acc:.2f}pp")
    elif old_acc > new_acc:
        print(f"\n⚠️  OLD METHOD performed better by {old_acc - new_acc:.2f}pp")
    else:
        print(f"\n🔄 METHODS PERFORMED THE SAME")


if __name__ == "__main__":
    main()
