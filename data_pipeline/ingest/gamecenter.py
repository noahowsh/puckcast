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
from typing import Iterable

import requests

from data_pipeline.config import PipelineConfig, DEFAULT_CONFIG
from data_pipeline.ingest.base import BaseIngestor

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
      # TODO: enumerate gameIds for the season, call `_fetch_gamecenter_json`, and persist

  def run_incremental(self) -> None:
    """Incremental ingest for today's slate (placeholder)."""
    LOGGER.info("[stub] incremental ingest not implemented yet")

  def _fetch_gamecenter_json(self, game_id: int) -> dict:
    """Fetch a single GameCenter payload (placeholder)."""
    url = GAMECENTER_URL.format(game_id=game_id)
    LOGGER.debug("Fetching %s", url)
    resp = self.session.get(url, timeout=self.config.http_timeout)
    resp.raise_for_status()
    return resp.json()
