"""
Dataset Caching for Fast Training Iterations

Caches the complete built dataset (features + targets) after the slow
feature engineering pipeline. Reduces training time from ~48 min to <1 min.

Usage:
    from nhl_prediction.dataset_cache import get_cached_dataset

    # First run: builds and caches (~48 min)
    # Subsequent runs: loads from cache (<1 min)
    dataset = get_cached_dataset(["20212022", "20222023", "20232024"])

    # Force rebuild
    dataset = get_cached_dataset(seasons, force_rebuild=True)
"""

from __future__ import annotations

import hashlib
import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import pandas as pd

LOGGER = logging.getLogger(__name__)
CACHE_DIR = Path(__file__).parent.parent.parent / "data" / "cache"


@dataclass
class CachedDataset:
    """Container for cached dataset with metadata."""
    games: pd.DataFrame
    features: pd.DataFrame
    target: pd.Series
    metadata: dict


def _get_cache_key(seasons: List[str]) -> str:
    """Generate cache key from seasons list."""
    seasons_str = "_".join(sorted(seasons))
    return f"dataset_{seasons_str}"


def _get_cache_path(seasons: List[str]) -> Path:
    """Get path for cached dataset."""
    return CACHE_DIR / f"{_get_cache_key(seasons)}.parquet"


def _get_metadata_path(seasons: List[str]) -> Path:
    """Get path for cache metadata."""
    return CACHE_DIR / f"{_get_cache_key(seasons)}_meta.json"


def save_dataset(dataset, seasons: List[str]) -> None:
    """Save dataset to cache with metadata."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    cache_path = _get_cache_path(seasons)
    meta_path = _get_metadata_path(seasons)

    # Combine all data into single DataFrame for storage
    combined = dataset.features.copy()
    combined["_target"] = dataset.target
    combined["_game_id"] = dataset.games["gameId"].values
    combined["_season_id"] = dataset.games["seasonId"].values
    combined["_game_date"] = dataset.games["gameDate"].values

    # Save as parquet
    combined.to_parquet(cache_path, index=False)

    # Save metadata
    metadata = {
        "seasons": seasons,
        "n_games": len(dataset.games),
        "n_features": len(dataset.features.columns),
        "feature_names": list(dataset.features.columns),
        "created_at": datetime.now().isoformat(),
        "cache_version": "1.0"
    }
    meta_path.write_text(json.dumps(metadata, indent=2))

    LOGGER.info(f"Cached dataset: {len(dataset.games)} games, {len(dataset.features.columns)} features")
    LOGGER.info(f"Cache path: {cache_path}")


def load_cached_dataset(seasons: List[str]) -> Optional[CachedDataset]:
    """Load dataset from cache if exists."""
    cache_path = _get_cache_path(seasons)
    meta_path = _get_metadata_path(seasons)

    if not cache_path.exists() or not meta_path.exists():
        return None

    try:
        # Load metadata
        metadata = json.loads(meta_path.read_text())

        # Load data
        combined = pd.read_parquet(cache_path)

        # Extract components
        target = combined["_target"]
        game_ids = combined["_game_id"]
        season_ids = combined["_season_id"]
        game_dates = combined["_game_date"]

        # Reconstruct games DataFrame (minimal)
        games = pd.DataFrame({
            "gameId": game_ids,
            "seasonId": season_ids,
            "gameDate": game_dates
        })

        # Features are everything except meta columns
        meta_cols = ["_target", "_game_id", "_season_id", "_game_date"]
        features = combined.drop(columns=meta_cols)

        LOGGER.info(f"Loaded cached dataset: {len(games)} games, {len(features.columns)} features")
        LOGGER.info(f"Cache created: {metadata.get('created_at', 'unknown')}")

        return CachedDataset(
            games=games,
            features=features,
            target=target,
            metadata=metadata
        )

    except Exception as e:
        LOGGER.warning(f"Failed to load cache: {e}")
        return None


def get_cached_dataset(seasons: List[str], force_rebuild: bool = False):
    """
    Get dataset from cache or build fresh.

    Args:
        seasons: List of season IDs (e.g., ["20212022", "20222023"])
        force_rebuild: If True, rebuild even if cache exists

    Returns:
        Dataset with games, features, and target
    """
    from nhl_prediction.pipeline import build_dataset

    if not force_rebuild:
        cached = load_cached_dataset(seasons)
        if cached is not None:
            # Return in same format as build_dataset
            return type('Dataset', (), {
                'games': cached.games,
                'features': cached.features,
                'target': cached.target
            })()

    LOGGER.info("Building dataset from scratch (will cache for next time)...")
    dataset = build_dataset(seasons)

    # Cache for future use
    save_dataset(dataset, seasons)

    return dataset


def clear_cache(seasons: Optional[List[str]] = None) -> None:
    """Clear cached datasets."""
    if seasons:
        cache_path = _get_cache_path(seasons)
        meta_path = _get_metadata_path(seasons)
        if cache_path.exists():
            cache_path.unlink()
        if meta_path.exists():
            meta_path.unlink()
        LOGGER.info(f"Cleared cache for seasons: {seasons}")
    else:
        # Clear all dataset caches
        for f in CACHE_DIR.glob("dataset_*.parquet"):
            f.unlink()
        for f in CACHE_DIR.glob("dataset_*_meta.json"):
            f.unlink()
        LOGGER.info("Cleared all dataset caches")


def list_cached_datasets() -> List[dict]:
    """List all cached datasets with metadata."""
    caches = []
    for meta_path in CACHE_DIR.glob("dataset_*_meta.json"):
        try:
            metadata = json.loads(meta_path.read_text())
            cache_path = meta_path.with_suffix("").with_suffix(".parquet")
            metadata["size_mb"] = cache_path.stat().st_size / (1024 * 1024) if cache_path.exists() else 0
            caches.append(metadata)
        except Exception:
            pass
    return caches
