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
from predict_full import compute_team_rolling_stats


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

    # Compute FRESH rolling stats for both teams
    home_rolling = compute_team_rolling_stats(home_team_id, home_games, windows=[3, 5, 10])
    away_rolling = compute_team_rolling_stats(away_team_id, away_games, windows=[3, 5, 10])

    # Mapping from feature names to fresh rolling stat keys
    rolling_feature_map = {
        'rolling_win_pct_3_diff': ('win_pct_3', 'win_pct_3'),
        'rolling_win_pct_5_diff': ('win_pct_5', 'win_pct_5'),
        'rolling_win_pct_10_diff': ('win_pct_10', 'win_pct_10'),
        'rolling_goal_diff_3_diff': ('goal_diff_3', 'goal_diff_3'),
        'rolling_goal_diff_5_diff': ('goal_diff_5', 'goal_diff_5'),
        'rolling_goal_diff_10_diff': ('goal_diff_10', 'goal_diff_10'),
        'rolling_xg_diff_3_diff': ('xg_diff_3', 'xg_diff_3'),
        'rolling_xg_diff_5_diff': ('xg_diff_5', 'xg_diff_5'),
        'rolling_xg_diff_10_diff': ('xg_diff_10', 'xg_diff_10'),
        'rolling_corsi_3_diff': ('corsi_3', 'corsi_3'),
        'rolling_corsi_5_diff': ('corsi_5', 'corsi_5'),
        'rolling_corsi_10_diff': ('corsi_10', 'corsi_10'),
        'rolling_fenwick_5_diff': ('fenwick_5', 'fenwick_5'),
        'rolling_fenwick_10_diff': ('fenwick_10', 'fenwick_10'),
        'rolling_high_danger_shots_5_diff': ('high_danger_shots_5', 'high_danger_shots_5'),
        'rolling_high_danger_shots_10_diff': ('high_danger_shots_10', 'high_danger_shots_10'),
        'rolling_save_pct_3_diff': ('save_pct_3', 'save_pct_3'),
        'rolling_save_pct_5_diff': ('save_pct_5', 'save_pct_5'),
        'rolling_save_pct_10_diff': ('save_pct_10', 'save_pct_10'),
        'rolling_faceoff_5_diff': ('faceoff_5', 'faceoff_5'),
        'shotsFor_roll_10_diff': ('shots_for_10', 'shots_for_10'),
        'momentum_win_pct_diff': ('momentum_win_pct', 'momentum_win_pct'),
        'momentum_goal_diff_diff': ('momentum_goal_diff', 'momentum_goal_diff'),
        'momentum_xg_diff': ('momentum_xg', 'momentum_xg'),
        'season_win_pct_diff': ('season_win_pct', 'season_win_pct'),
        'season_goal_diff_avg_diff': ('season_goal_diff_avg', 'season_goal_diff_avg'),
        'season_xg_diff_avg_diff': ('season_xg_diff_avg', 'season_xg_diff_avg'),
        'season_shot_margin_diff': ('season_shot_margin', 'season_shot_margin'),
    }

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
        elif col in rolling_feature_map:
            # Use FRESH rolling stats
            home_key, away_key = rolling_feature_map[col]
            home_val = home_rolling.get(home_key, 0.0)
            away_val = away_rolling.get(away_key, 0.0)
            matchup[col] = home_val - away_val
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
            # Elo features - compute current Elo by applying post-game updates
            if col == 'elo_diff_pre':
                # Get each team's pre-game Elo from their most recent game
                if home_team_was_home:
                    home_pre_elo = home_recent.get('elo_home_pre', 1500.0)
                    home_opp_pre_elo = home_recent.get('elo_away_pre', 1500.0)
                else:
                    home_pre_elo = home_recent.get('elo_away_pre', 1500.0)
                    home_opp_pre_elo = home_recent.get('elo_home_pre', 1500.0)

                if away_team_was_home:
                    away_pre_elo = away_recent.get('elo_home_pre', 1500.0)
                    away_opp_pre_elo = away_recent.get('elo_away_pre', 1500.0)
                else:
                    away_pre_elo = away_recent.get('elo_away_pre', 1500.0)
                    away_opp_pre_elo = away_recent.get('elo_home_pre', 1500.0)

                # Compute post-game Elo for home team
                home_game_home_win = home_recent.get('home_win', 0)
                home_game_home_score = home_recent.get('home_score', 0)
                home_game_away_score = home_recent.get('away_score', 0)

                if home_team_was_home:
                    home_outcome = 1.0 if home_game_home_win == 1 else 0.0
                    home_expected = home_recent.get('elo_expectation_home', 0.5)
                    goal_diff = home_game_home_score - home_game_away_score
                else:
                    home_outcome = 0.0 if home_game_home_win == 1 else 1.0
                    home_expected = 1.0 - home_recent.get('elo_expectation_home', 0.5)
                    goal_diff = home_game_away_score - home_game_home_score

                margin = max(abs(goal_diff), 1)
                rating_diff = abs(home_pre_elo - home_opp_pre_elo)
                multiplier = np.log(margin + 1) * (2.2 / (rating_diff * 0.001 + 2.2))
                home_delta = 10.0 * multiplier * (home_outcome - home_expected)
                home_current_elo = home_pre_elo + home_delta

                # Compute post-game Elo for away team
                away_game_home_win = away_recent.get('home_win', 0)
                away_game_home_score = away_recent.get('home_score', 0)
                away_game_away_score = away_recent.get('away_score', 0)

                if away_team_was_home:
                    away_outcome = 1.0 if away_game_home_win == 1 else 0.0
                    away_expected = away_recent.get('elo_expectation_home', 0.5)
                    goal_diff = away_game_home_score - away_game_away_score
                else:
                    away_outcome = 0.0 if away_game_home_win == 1 else 1.0
                    away_expected = 1.0 - away_recent.get('elo_expectation_home', 0.5)
                    goal_diff = away_game_away_score - away_game_home_score

                margin = max(abs(goal_diff), 1)
                rating_diff = abs(away_pre_elo - away_opp_pre_elo)
                multiplier = np.log(margin + 1) * (2.2 / (rating_diff * 0.001 + 2.2))
                away_delta = 10.0 * multiplier * (away_outcome - away_expected)
                away_current_elo = away_pre_elo + away_delta

                matchup[col] = home_current_elo - away_current_elo

            elif col == 'elo_expectation_home':
                if 'elo_diff_pre' in matchup:
                    elo_diff = matchup['elo_diff_pre']
                    home_adv = 35.0
                    matchup[col] = 1.0 / (1.0 + 10 ** ((-elo_diff - home_adv) / 400))
                elif col in home_recent.index:
                    matchup[col] = home_recent[col]
                else:
                    matchup[col] = 0.5

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
    print("FEATURE CONSTRUCTION METHOD COMPARISON (FULL 5000+ GAME TEST)")
    print("Comparing OLD (buggy) vs NEW (fixed) approaches on ALL historical games")
    print("Using walk-forward methodology with rolling model retraining")
    print("=" * 80)

    # Load dataset
    print("\n1️⃣  Loading dataset...")
    # Include 3 prior seasons before 21-22 so it has proper training data like the others
    seasons = ['20242025', '20232024', '20222023', '20212022', '20202021', '20192020', '20182019']
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

    games['seasonId_str'] = games['seasonId'].astype(str)
    games_sorted = games.sort_values('gameDate').copy()

    print(f"   ✅ Loaded {len(games)} games with {len(available_v70)} features")
    print(f"   Available seasons: {sorted(games['seasonId'].unique())}")

    # Walk-forward testing: for each game, use only prior games for training and prediction
    print("\n2️⃣  Running walk-forward simulation on ALL games...")
    print("   (Retraining model at start of each season)")

    # Minimum games needed before we can start predicting
    MIN_TRAINING_GAMES = 200

    old_correct = 0
    new_correct = 0
    pipeline_correct = 0
    old_total = 0
    new_total = 0
    pipeline_total = 0
    both_correct = 0
    old_only_correct = 0
    new_only_correct = 0
    both_wrong = 0

    # Track per-season results
    season_results = {}

    feature_columns = list(available_v70)
    current_model = None
    current_model_season = None

    total_games = len(games_sorted)

    for i, (idx, game) in enumerate(games_sorted.iterrows()):
        game_date = game['gameDate']
        home_id = game['teamId_home']
        away_id = game['teamId_away']
        season_id = str(game['seasonId'])
        actual_home_win = dataset.target.loc[idx]

        # Get all games before this one
        games_before = games_sorted[pd.to_datetime(games_sorted['gameDate']) < pd.to_datetime(game_date)]

        # Skip if not enough training data
        if len(games_before) < MIN_TRAINING_GAMES:
            continue

        # Retrain model at start of each new season (or if no model yet)
        if current_model is None or season_id != current_model_season:
            # Train on all games before this season starts
            train_features = features_v70.loc[games_before.index]
            train_target = dataset.target.loc[games_before.index]

            # Find best C using cross-validation on training data
            train_games_df = games_before.copy()
            train_seasons = sorted(train_games_df['seasonId'].unique().tolist())

            if len(train_seasons) >= 2:
                candidate_cs = [0.005, 0.01, 0.02, 0.05, 0.1]
                best_c = tune_logreg_c(candidate_cs, train_features, train_target,
                                       train_games_df, train_seasons)
            else:
                best_c = 0.01  # Default if not enough seasons for CV

            current_model = create_baseline_model(C=best_c)
            training_mask = pd.Series(True, index=train_features.index)
            current_model = fit_model(current_model, train_features, train_target, training_mask)
            current_model_season = season_id

            print(f"\n   📅 Season {season_id}: Trained model on {len(games_before)} games (C={best_c:.3f})")

            # Initialize season tracking
            if season_id not in season_results:
                season_results[season_id] = {'old_correct': 0, 'new_correct': 0, 'pipeline_correct': 0,
                                              'old_total': 0, 'new_total': 0, 'pipeline_total': 0}

        # Build features using OLD method
        games_before_copy = games_before.copy()
        games_before_copy['seasonId_str'] = games_before_copy['seasonId'].astype(str)
        features_before = features_v70.loc[games_before.index]

        old_features = build_features_old_method(
            home_id, away_id, season_id,
            games_before_copy, features_before, feature_columns
        )

        # Build features using NEW method
        new_features = build_features_new_method(
            home_id, away_id, season_id,
            games_before_copy, feature_columns, game_date
        )

        old_correct_pred = None
        new_correct_pred = None
        pipeline_correct_pred = None

        # PIPELINE BASELINE: Use actual pipeline features for this game
        pipeline_features = features_v70.loc[idx]
        pipeline_prob = current_model.predict_proba(pipeline_features.values.reshape(1, -1))[0][1]
        pipeline_pred_home_win = pipeline_prob >= 0.5
        pipeline_correct_pred = (pipeline_pred_home_win == actual_home_win)
        pipeline_correct += int(pipeline_correct_pred)
        pipeline_total += 1
        season_results[season_id]['pipeline_correct'] += int(pipeline_correct_pred)
        season_results[season_id]['pipeline_total'] += 1

        if old_features is not None:
            old_prob = current_model.predict_proba(old_features.values.reshape(1, -1))[0][1]
            old_pred_home_win = old_prob >= 0.5
            old_correct_pred = (old_pred_home_win == actual_home_win)
            old_correct += int(old_correct_pred)
            old_total += 1
            season_results[season_id]['old_correct'] += int(old_correct_pred)
            season_results[season_id]['old_total'] += 1

        if new_features is not None:
            new_prob = current_model.predict_proba(new_features.values.reshape(1, -1))[0][1]
            new_pred_home_win = new_prob >= 0.5
            new_correct_pred = (new_pred_home_win == actual_home_win)
            new_correct += int(new_correct_pred)
            new_total += 1
            season_results[season_id]['new_correct'] += int(new_correct_pred)
            season_results[season_id]['new_total'] += 1

        # Track agreement/disagreement
        if old_correct_pred is not None and new_correct_pred is not None:
            if old_correct_pred and new_correct_pred:
                both_correct += 1
            elif old_correct_pred and not new_correct_pred:
                old_only_correct += 1
            elif new_correct_pred and not old_correct_pred:
                new_only_correct += 1
            else:
                both_wrong += 1

        # Progress update every 500 games
        if (i + 1) % 500 == 0:
            print(f"   Processed {i + 1}/{total_games} games...")

    # Results
    print("\n" + "=" * 80)
    print("RESULTS (FULL WALK-FORWARD TEST)")
    print("=" * 80)

    old_acc = old_correct / old_total * 100 if old_total > 0 else 0
    new_acc = new_correct / new_total * 100 if new_total > 0 else 0
    pipeline_acc = pipeline_correct / pipeline_total * 100 if pipeline_total > 0 else 0

    print(f"\n📊 PIPELINE BASELINE (actual features - expected ~60%):")
    print(f"   Accuracy: {pipeline_acc:.2f}% ({pipeline_correct}/{pipeline_total} games)")

    print(f"\n📊 OLD METHOD (buggy averaging):")
    print(f"   Accuracy: {old_acc:.2f}% ({old_correct}/{old_total} games)")

    print(f"\n📊 NEW METHOD (proper differentials + schedule):")
    print(f"   Accuracy: {new_acc:.2f}% ({new_correct}/{new_total} games)")

    print(f"\n📈 OVERALL COMPARISON:")
    print(f"   Difference: {new_acc - old_acc:+.2f} percentage points")
    print(f"   Both correct: {both_correct}")
    print(f"   Only OLD correct: {old_only_correct}")
    print(f"   Only NEW correct: {new_only_correct}")
    print(f"   Both wrong: {both_wrong}")

    print(f"\n📅 PER-SEASON BREAKDOWN:")
    for season in sorted(season_results.keys()):
        sr = season_results[season]
        pipeline_s_acc = sr['pipeline_correct'] / sr['pipeline_total'] * 100 if sr['pipeline_total'] > 0 else 0
        old_s_acc = sr['old_correct'] / sr['old_total'] * 100 if sr['old_total'] > 0 else 0
        new_s_acc = sr['new_correct'] / sr['new_total'] * 100 if sr['new_total'] > 0 else 0
        diff = new_s_acc - old_s_acc
        print(f"   {season}: PIPELINE {pipeline_s_acc:.1f}% | OLD {old_s_acc:.1f}% | NEW {new_s_acc:.1f}% ({diff:+.1f}pp) [{sr['pipeline_total']} games]")

    if new_acc > old_acc:
        print(f"\n✅ NEW METHOD IS BETTER by {new_acc - old_acc:.2f}pp")
    elif old_acc > new_acc:
        print(f"\n⚠️  OLD METHOD performed better by {old_acc - new_acc:.2f}pp")
    else:
        print(f"\n🔄 METHODS PERFORMED THE SAME")


if __name__ == "__main__":
    main()
