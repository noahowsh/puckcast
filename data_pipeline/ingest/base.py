"""Abstract ingest interfaces.

These classes outline the expected behavior for concrete collectors (GameCenter,
shift charts, rosters, etc.). They deliberately keep I/O responsibilities
separate from transformation steps so we can plug in different storage layers
later (filesystem, S3, Postgres...).
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, Protocol

from data_pipeline.config import PipelineConfig, DEFAULT_CONFIG


class Writer(Protocol):
  """Interface for writing blobs/records to a backing store."""

  def write_json(self, path: Path, payload: dict) -> None: ...
  def write_bytes(self, path: Path, payload: bytes) -> None: ...


class BaseIngestor(ABC):
  """Shared hooks for ingest jobs."""

  def __init__(self, config: PipelineConfig = DEFAULT_CONFIG) -> None:
    self.config = config

  @abstractmethod
  def backfill(self, *, season_ids: Iterable[str]) -> None:
    """Fetch and store historical data."""

  @abstractmethod
  def run_incremental(self) -> None:
    """Fetch the latest data (e.g., today's schedule)."""
