"""GameCenter play-by-play ingestion (stub).

This module will eventually download raw event JSON for every NHL game and
produce two artifacts:

1. Raw JSON snapshots (for auditing / reprocessing)
2. Parsed per-event/per-shot tables that downstream feature builders can use

Implementation roadmap (next steps):
- Build a schedule enumerator so we can backfill every gameId for the desired seasons
- Call `https://api.nhle.com/stats/rest/en/gamecenter/{gameId}/landing`
- Persist the JSON under `data/raw/nhl/gamecenter/{season}/{gameId}.json`
- Normalize shots/goals into a dataframe/table under `data/processed/...`
"""

from __future__ import annotations

import logging
import json
from datetime import datetime
from pathlib import Path
from typing import Iterable

import requests

from data_pipeline.config import PipelineConfig, DEFAULT_CONFIG
from data_pipeline.ingest.base import BaseIngestor
from data_pipeline.ingest.utils import fetch_json

LOGGER = logging.getLogger(__name__)
GAMECENTER_URL = "https://api.nhle.com/stats/rest/en/gamecenter/{game_id}/landing"


class GameCenterIngestor(BaseIngestor):
  """Collects GameCenter play-by-play payloads."""

  def __init__(self, config: PipelineConfig = DEFAULT_CONFIG, session: requests.Session | None = None) -> None:
    super().__init__(config)
    self.session = session or requests.Session()

  def backfill(self, *, season_ids: Iterable[str]) -> None:
    """Backfill entire seasons (placeholder)."""
    for season_id in season_ids:
      LOGGER.info("[stub] would backfill season %s", season_id)
      game_ids = self._fetch_game_ids_for_season(season_id)
      for game_id in game_ids:
        payload = self._fetch_gamecenter_json(game_id)
        self._persist_raw(game_id, payload)

  def run_incremental(self) -> None:
    """Incremental ingest for today's slate (placeholder)."""
    LOGGER.info("[stub] incremental ingest not implemented yet")

  def _fetch_gamecenter_json(self, game_id: int) -> dict:
    url = GAMECENTER_URL.format(game_id=game_id)
    LOGGER.debug("Fetching %s", url)
    return fetch_json(self.session, url, timeout=self.config.http_timeout)

  def _persist_raw(self, game_id: int, payload: dict) -> None:
    season = payload.get("game", {}).get("season") or guess_season(payload)
    season_dir = self.config.raw_data_dir / "gamecenter" / str(season)
    season_dir.mkdir(parents=True, exist_ok=True)
    path = season_dir / f"{game_id}.json"
    path.write_text(json.dumps(payload, indent=2))

  def _fetch_game_ids_for_season(self, season_id: str) -> list[int]:
    LOGGER.info("[stub] enumerating gameIds for season %s", season_id)
    # TODO: call schedule endpoint to return actual IDs
    return []


def guess_season(payload: dict) -> str:
  game = payload.get("game", {})
  season = game.get("season")
  if season:
    return str(season)
  date_str = game.get("gameDate")
  if not date_str:
    return "unknown"
  dt = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
  year = dt.year
  start_year = year if dt.month >= 7 else year - 1
  return f"{start_year}{start_year + 1}"
