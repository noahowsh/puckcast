#!/usr/bin/env python3
"""
Retrain xG Model with Expanded Historical Data

The current xG model was trained on ~200 games from 2021-22.
This script retrains it on data from all available seasons
for potentially better shot quality predictions.

Usage:
    python training/retrain_xg_model.py
"""

import sys
import warnings
warnings.filterwarnings('ignore')
from pathlib import Path
from datetime import datetime
import pickle

import pandas as pd
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, roc_auc_score, log_loss

sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.data_sources.gamecenter import GamecenterClient

PROJECT_ROOT = Path(__file__).parent.parent
XG_MODEL_PATH = PROJECT_ROOT / "data" / "xg_model.pkl"
XG_MODEL_BACKUP_PATH = PROJECT_ROOT / "data" / "xg_model_backup.pkl"
XG_MODEL_EXPANDED_PATH = PROJECT_ROOT / "data" / "xg_model_expanded.pkl"


def extract_shot_features(play: dict, game_context: dict) -> dict | None:
    """Extract features from a shot play."""
    details = play.get("details", {})

    # Must have coordinates
    x = details.get("xCoord")
    y = details.get("yCoord")
    if x is None or y is None:
        return None

    # Calculate distance and angle
    # NHL rink: goal at x=89, y=0
    goal_x = 89
    goal_y = 0

    # Normalize x (some plays might have negative x)
    x = abs(x)

    distance = np.sqrt((x - goal_x)**2 + (y - goal_y)**2)
    angle = np.degrees(np.arctan2(abs(y), goal_x - x)) if x < goal_x else 90

    # Get shot type
    shot_type = details.get("shotType", "wrist").lower()

    # Get situation
    situation = play.get("situationCode", "1551")
    home_skaters = int(situation[0]) if situation else 5
    away_skaters = int(situation[1]) if situation else 5

    # Determine if shooter is home or away
    event_team = details.get("eventOwnerTeamId")
    is_home = event_team == game_context.get("homeTeamId")

    # Power play detection
    if is_home:
        is_pp = home_skaters > away_skaters
        is_es = home_skaters == away_skaters == 5
    else:
        is_pp = away_skaters > home_skaters
        is_es = home_skaters == away_skaters == 5

    # Zone detection (offensive zone if x > 25)
    is_oz = x > 25

    # Period
    period = play.get("periodDescriptor", {}).get("number", 1)

    # Additional features
    type_code = play.get("typeCode", 0)
    is_goal = type_code == 505  # Goal type code

    return {
        "distance": distance,
        "angle": angle,
        "shot_type": shot_type,
        "is_goal": int(is_goal),
        "is_even_strength": int(is_es),
        "is_power_play": int(is_pp),
        "is_offensive_zone": int(is_oz),
        "is_third_period": int(period >= 3),
        "is_rebound": 0,  # Would need sequence analysis
        "is_rush_shot": 0,  # Would need sequence analysis
        "is_deflection": int(shot_type == "deflection"),
        "is_screened": 0,  # Not available in basic data
        "is_one_timer": 0,  # Not available in basic data
    }


def collect_training_data(seasons: list, games_per_season: int = 300) -> pd.DataFrame:
    """Collect shot data from multiple seasons."""
    client = GamecenterClient(rate_limit_seconds=0.5)

    all_shots = []

    for season in seasons:
        print(f"  Collecting from {season[:4]}-{season[4:6]}...")

        # Get game list for season
        schedule_url = f"https://api-web.nhle.com/v1/schedule/{season[:4]}-{season[4:6]}-10"

        # Get games from schedule
        try:
            game_ids = []
            # Fetch schedule weeks to get game IDs
            for month in range(10, 13):  # Oct-Dec
                for day in [1, 15]:
                    try:
                        url = f"https://api-web.nhle.com/v1/schedule/{season[:4]}-{month:02d}-{day:02d}"
                        resp = client.session.get(url)
                        if resp.ok:
                            data = resp.json()
                            for week in data.get("gameWeek", []):
                                for game in week.get("games", []):
                                    if game.get("gameType") == 2:  # Regular season
                                        game_ids.append(str(game["id"]))
                    except:
                        continue

            for month in range(1, 5):  # Jan-Apr
                for day in [1, 15]:
                    try:
                        year = int(season[:4]) + 1
                        url = f"https://api-web.nhle.com/v1/schedule/{year}-{month:02d}-{day:02d}"
                        resp = client.session.get(url)
                        if resp.ok:
                            data = resp.json()
                            for week in data.get("gameWeek", []):
                                for game in week.get("games", []):
                                    if game.get("gameType") == 2:
                                        game_ids.append(str(game["id"]))
                    except:
                        continue

            game_ids = list(set(game_ids))[:games_per_season]
            print(f"    Found {len(game_ids)} games")

            # Process games
            for i, game_id in enumerate(game_ids):
                if i % 50 == 0:
                    print(f"    Processing game {i+1}/{len(game_ids)}")

                try:
                    pbp = client.get_play_by_play(game_id)
                    if not pbp or pbp.get("gameState") not in ["OFF", "FINAL"]:
                        continue

                    game_context = {
                        "homeTeamId": pbp["homeTeam"]["id"],
                        "awayTeamId": pbp["awayTeam"]["id"],
                    }

                    for play in pbp.get("plays", []):
                        type_code = play.get("typeCode", 0)
                        if type_code in [505, 506, 507, 508]:  # Goal, shot, missed, blocked
                            features = extract_shot_features(play, game_context)
                            if features:
                                all_shots.append(features)
                except Exception as e:
                    continue

        except Exception as e:
            print(f"    Error: {e}")
            continue

    return pd.DataFrame(all_shots)


def train_xg_model(training_data: pd.DataFrame) -> HistGradientBoostingClassifier:
    """Train the xG model."""
    print(f"Training on {len(training_data):,} shots...")

    # Encode shot types
    shot_type_dummies = pd.get_dummies(training_data["shot_type"], prefix="shot")

    # Feature columns
    feature_cols = [
        "distance", "angle",
        "is_even_strength", "is_power_play", "is_offensive_zone",
        "is_rebound", "is_rush_shot", "is_third_period",
        "is_deflection", "is_screened", "is_one_timer"
    ]

    X = pd.concat([training_data[feature_cols], shot_type_dummies], axis=1)
    y = training_data["is_goal"]

    # Train/val split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    print(f"  Train: {len(X_train):,} shots, Val: {len(X_val):,} shots")
    print(f"  Goal rate: {y.mean()*100:.2f}%")

    # Train model
    model = HistGradientBoostingClassifier(
        max_iter=200,  # More iterations for more data
        learning_rate=0.08,
        max_depth=6,
        max_leaf_nodes=50,
        min_samples_leaf=20,
        random_state=42,
        verbose=0,
    )

    model.fit(X_train, y_train)

    # Evaluate
    train_proba = model.predict_proba(X_train)[:, 1]
    val_proba = model.predict_proba(X_val)[:, 1]

    train_acc = accuracy_score(y_train, (train_proba >= 0.5).astype(int))
    val_acc = accuracy_score(y_val, (val_proba >= 0.5).astype(int))
    train_auc = roc_auc_score(y_train, train_proba)
    val_auc = roc_auc_score(y_val, val_proba)
    val_ll = log_loss(y_val, val_proba)

    print(f"  Train - Acc: {train_acc:.4f}, AUC: {train_auc:.4f}")
    print(f"  Val   - Acc: {val_acc:.4f}, AUC: {val_auc:.4f}, LogLoss: {val_ll:.4f}")

    # Store feature columns
    model.feature_columns_ = X.columns.tolist()

    return model, {'val_acc': val_acc, 'val_auc': val_auc, 'val_logloss': val_ll}


def main():
    print("=" * 70)
    print("RETRAIN xG MODEL WITH EXPANDED DATA")
    print("=" * 70)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Backup existing model
    if XG_MODEL_PATH.exists():
        print("Backing up existing model...")
        import shutil
        shutil.copy(XG_MODEL_PATH, XG_MODEL_BACKUP_PATH)
        print(f"  Saved to {XG_MODEL_BACKUP_PATH}")

    # Collect training data from multiple seasons
    print()
    print("Collecting shot data from historical seasons...")

    # Use seasons that have good data quality
    training_seasons = [
        '20182019',  # Full season
        '20212022',  # Post-COVID full season
        '20222023',  # Recent
        '20232024',  # Recent
    ]

    training_data = collect_training_data(training_seasons, games_per_season=250)

    print(f"\nTotal shots collected: {len(training_data):,}")
    print(f"Goal rate: {training_data['is_goal'].mean()*100:.2f}%")

    # Train new model
    print()
    print("Training expanded xG model...")
    model, metrics = train_xg_model(training_data)

    # Save expanded model
    print()
    print("Saving model...")
    with open(XG_MODEL_EXPANDED_PATH, "wb") as f:
        pickle.dump(model, f)
    print(f"  Saved to {XG_MODEL_EXPANDED_PATH}")

    # Compare with old model if exists
    if XG_MODEL_BACKUP_PATH.exists():
        print()
        print("=" * 70)
        print("COMPARISON WITH OLD MODEL")
        print("=" * 70)

        with open(XG_MODEL_BACKUP_PATH, "rb") as f:
            old_model = pickle.load(f)

        # Compare on validation set
        # (Would need to hold out some data for fair comparison)
        print("New model metrics:")
        print(f"  Val Accuracy: {metrics['val_acc']:.4f}")
        print(f"  Val AUC: {metrics['val_auc']:.4f}")
        print(f"  Val LogLoss: {metrics['val_logloss']:.4f}")

    print()
    print("=" * 70)
    print("DONE")
    print("=" * 70)
    print()
    print("To use the new model, copy it to replace the old one:")
    print(f"  cp {XG_MODEL_EXPANDED_PATH} {XG_MODEL_PATH}")


if __name__ == "__main__":
    main()
