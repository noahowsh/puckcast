from __future__ import annotations

import time
import logging
from typing import Iterable

import requests

LOGGER = logging.getLogger(__name__)


def batched(iterable: Iterable[int], batch_size: int):
  batch = []
  for item in iterable:
    batch.append(item)
    if len(batch) == batch_size:
      yield batch
      batch = []
  if batch:
    yield batch


def fetch_json(session: requests.Session, url: str, *, timeout: int = 20, retries: int = 3, backoff: float = 1.0) -> dict:
  for attempt in range(1, retries + 1):
    try:
      resp = session.get(url, timeout=timeout)
      resp.raise_for_status()
      return resp.json()
    except requests.RequestException as exc:
      LOGGER.warning("Request failed (%s/%s): %s", attempt, retries, exc)
      if attempt == retries:
        raise
      time.sleep(backoff * attempt)
