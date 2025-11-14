"""Storage helpers (placeholders).

Future implementations will abstract writing to filesystem, S3, or databases.
For now we simply define stubs so ingest jobs can depend on a consistent API.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any


def write_json(path: Path, payload: Any) -> None:  # pragma: no cover - placeholder
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_text("{}\n")  # TODO: serialize actual payload


def write_bytes(path: Path, payload: bytes) -> None:  # pragma: no cover - placeholder
  path.parent.mkdir(parents=True, exist_ok=True)
  path.write_bytes(payload)
