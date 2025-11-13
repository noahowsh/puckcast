"""Unified accessors for official NHL data sources."""

from __future__ import annotations

from importlib import import_module
from typing import Any

__all__ = ["GamecenterClient", "StatsRestClient", "LegacyStatsClient"]


def __getattr__(name: str) -> Any:
    if name == "GamecenterClient":
        module = import_module("nhl_prediction.data_sources.gamecenter")
        return module.GamecenterClient
    if name == "StatsRestClient":
        module = import_module("nhl_prediction.data_sources.stats_rest")
        return module.StatsRestClient
    if name == "LegacyStatsClient":
        module = import_module("nhl_prediction.data_sources.legacy_api")
        return module.LegacyStatsClient
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(list(globals().keys()) + __all__)
