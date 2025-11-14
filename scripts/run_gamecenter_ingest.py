#!/usr/bin/env python3
"""CLI entry point for the GameCenter ingestor (currently stubbed)."""

from __future__ import annotations

import argparse
import logging

from data_pipeline.ingest.gamecenter import GameCenterIngestor

logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")


def parse_args() -> argparse.Namespace:
  parser = argparse.ArgumentParser(description="Backfill or update GameCenter play-by-play data.")
  parser.add_argument("--season", action="append", help="Season ID to backfill (e.g., 20242025). Can be repeated.")
  return parser.parse_args()


def main() -> None:
  args = parse_args()
  ingestor = GameCenterIngestor()
  if args.season:
    ingestor.backfill(season_ids=args.season)
  else:
    ingestor.run_incremental()


if __name__ == "__main__":
  main()
