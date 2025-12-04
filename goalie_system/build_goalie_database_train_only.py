#!/usr/bin/env python3
"""
Build goalie performance database from TRAINING DATA ONLY.

CRITICAL: Only uses 2021-22 and 2022-23 seasons to avoid data leakage.
The 2023-24 season is the test set and must not be included.
"""

import pickle
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent / 'src'))

from build_goalie_database import build_goalie_database
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

OUTPUT_PATH = Path("data/goalie_tracker_train_only.pkl")

def main():
    """Build goalie tracker from TRAINING DATA ONLY."""
    LOGGER.info("="*80)
    LOGGER.info("Building Goalie Database - TRAINING DATA ONLY")
    LOGGER.info("="*80)
    LOGGER.info("Seasons: 2021-22, 2022-23 (excluding 2023-24 test set)")
    LOGGER.info("")

    # Build tracker from TRAINING seasons only
    tracker = build_goalie_database(seasons=["20212022", "20222023"])

    # Save to disk
    LOGGER.info(f"\nSaving database to: {OUTPUT_PATH}")
    OUTPUT_PATH.parent.mkdir(exist_ok=True)

    with open(OUTPUT_PATH, 'wb') as f:
        pickle.dump(tracker, f)

    LOGGER.info(f"✓ Goalie database saved ({OUTPUT_PATH.stat().st_size / 1024:.1f} KB)")
    LOGGER.info("\n" + "="*80)
    LOGGER.info("TRAINING-ONLY goalie database ready for V7.1")
    LOGGER.info("="*80)

if __name__ == "__main__":
    main()
