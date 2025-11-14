"""Shared configuration for the puckcast-native data pipeline."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class PipelineConfig:
  """Filesystem + runtime knobs for ingest jobs."""

  repo_root: Path = Path(__file__).resolve().parents[1]
  raw_data_dir: Path = repo_root / "data" / "raw" / "nhl"
  parsed_data_dir: Path = repo_root / "data" / "processed" / "nhl"
  http_timeout: int = 20


DEFAULT_CONFIG = PipelineConfig()
