#!/usr/bin/env python3
"""
Fetch Gamecenter play-by-play, extract shot events, and train a basic xG model.

This provides an end-to-end proof of concept that NHL Web API data alone can
recreate the shot-quality features we currently import from MoneyPuck.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path
from typing import Iterable, List, Sequence

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import brier_score_loss, log_loss, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC_PATH = REPO_ROOT / "src"
sys.path.insert(0, str(SRC_PATH))

from nhl_prediction.data_sources.gamecenter import GamecenterClient  # noqa: E402
from nhl_prediction.data_sources.gamecenter_events import extract_shot_events  # noqa: E402

MONEYPUCK_PATH = REPO_ROOT / "data" / "moneypuck_all_games.csv"
OUTPUT_DIR = REPO_ROOT / "data" / "processed"
METRICS_PATH = REPO_ROOT / "reports" / "gamecenter_xg_metrics.json"


def sample_game_ids(csv_path: Path, min_season: int, max_games: int) -> List[int]:
    seen: set[int] = set()
    game_ids: List[int] = []
    with csv_path.open(newline="") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            try:
                season = int(row["season"])
                game_id = int(row["gameId"])
            except (ValueError, KeyError):
                continue
            if season < min_season:
                continue
            if game_id in seen:
                continue
            seen.add(game_id)
            game_ids.append(game_id)
            if len(game_ids) >= max_games:
                break
    return game_ids


def build_shot_dataset(game_ids: Sequence[int], client: GamecenterClient) -> pd.DataFrame:
    frames: List[pd.DataFrame] = []
    for idx, game_id in enumerate(game_ids, start=1):
        try:
            pbp = client.get_play_by_play(game_id)
            df = extract_shot_events(pbp)
            if not df.empty:
                frames.append(df)
        except Exception as exc:  # pragma: no cover - debug logging in CLI
            print(f"[warn] failed to process game {game_id}: {exc}")
        if idx % 25 == 0:
            print(f"Processed {idx}/{len(game_ids)} games...")
    if not frames:
        return pd.DataFrame()
    shots = pd.concat(frames, ignore_index=True)
    shots["shot_type"] = shots["shot_type"].fillna("unknown")
    shots["strength_state"] = (
        shots["shooting_skaters"].fillna(0).astype(int).astype(str)
        + "v"
        + shots["defending_skaters"].fillna(0).astype(int).astype(str)
    )
    shots["score_state"] = (
        shots["home_score_before"].astype(int).astype(str)
        + "-"
        + shots["away_score_before"].astype(int).astype(str)
    )
    return shots


def train_xg_model(shots: pd.DataFrame) -> dict:
    numeric_cols = [
        "distance_ft",
        "angle_deg",
        "seconds_elapsed",
        "score_diff_before",
        "is_home_team",
        "is_empty_net",
    ]
    feature_df = shots[numeric_cols].copy()
    feature_df.replace([np.inf, -np.inf], np.nan, inplace=True)
    feature_df.dropna(inplace=True)

    aligned = shots.loc[feature_df.index]
    dummies = pd.get_dummies(
        aligned[["shot_type", "strength_state"]], prefix=["shot", "strength"], dtype=int
    )
    X = pd.concat([feature_df, dummies], axis=1)
    y = aligned["is_goal"].astype(int)

    scaler = StandardScaler()
    X[numeric_cols] = scaler.fit_transform(X[numeric_cols])

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model = LogisticRegression(max_iter=1000, solver="lbfgs")
    model.fit(X_train, y_train)

    test_probs = model.predict_proba(X_test)[:, 1]
    baseline_prob = y_train.mean()
    baseline = np.full_like(test_probs, baseline_prob)

    metrics = {
        "shots": int(len(shots)),
        "train_events": int(len(X_train)),
        "test_events": int(len(X_test)),
        "goal_rate": float(y_train.mean()),
        "log_loss": float(log_loss(y_test, test_probs)),
        "brier": float(brier_score_loss(y_test, test_probs)),
        "roc_auc": float(roc_auc_score(y_test, test_probs)),
        "baseline_log_loss": float(log_loss(y_test, baseline)),
        "baseline_brier": float(brier_score_loss(y_test, baseline)),
    }
    return {"model": model, "scaler": scaler, "metrics": metrics, "feature_matrix": X, "target": y}


def save_dataset(shots: pd.DataFrame, name: str) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    parquet_path = OUTPUT_DIR / f"{name}.parquet"
    try:
        shots.to_parquet(parquet_path, index=False)
        return parquet_path
    except Exception:
        # Fallback to CSV if parquet engines are unavailable.
        csv_path = OUTPUT_DIR / f"{name}.csv"
        shots.to_csv(csv_path, index=False)
        return csv_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Train a simple Gamecenter-based xG model.")
    parser.add_argument("--season", type=int, default=2022, help="Earliest MoneyPuck season to sample (e.g., 2022).")
    parser.add_argument("--games", type=int, default=150, help="Number of games to ingest.")
    args = parser.parse_args()

    if not MONEYPUCK_PATH.exists():
        raise FileNotFoundError(f"{MONEYPUCK_PATH} is required to sample game IDs.")

    print(f"Sampling up to {args.games} games from MoneyPuck season >= {args.season}...")
    game_ids = sample_game_ids(MONEYPUCK_PATH, args.season, args.games)
    print(f"Collected {len(game_ids)} unique game IDs")

    client = GamecenterClient()
    shots = build_shot_dataset(game_ids, client)
    if shots.empty:
        print("No shots extracted; aborting.")
        return

    dataset_path = save_dataset(shots, f"gamecenter_shots_{args.season}_{len(game_ids)}g")
    print(f"Saved shot dataset to {dataset_path}")

    result = train_xg_model(shots)
    metrics = result["metrics"]

    print("\nModel evaluation (test split):")
    print(f"  Log loss        : {metrics['log_loss']:.4f} (baseline {metrics['baseline_log_loss']:.4f})")
    print(f"  Brier score     : {metrics['brier']:.4f} (baseline {metrics['baseline_brier']:.4f})")
    print(f"  ROC AUC         : {metrics['roc_auc']:.3f}")
    print(f"  Goal rate (train): {metrics['goal_rate']:.3%}")
    print(f"  Train/Test shots: {metrics['train_events']}/{metrics['test_events']}")

    METRICS_PATH.parent.mkdir(parents=True, exist_ok=True)
    METRICS_PATH.write_text(json.dumps(metrics, indent=2))
    print(f"Wrote metrics to {METRICS_PATH}")


if __name__ == "__main__":
    main()
