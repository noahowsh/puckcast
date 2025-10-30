"""Data ingestion utilities for NHL predictive modelling."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List

import pandas as pd
import requests

LOGGER = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEAM_CSV_PATH = _PROJECT_ROOT / "data" / "nhl_teams.csv"
TEAM_SUMMARY_ENDPOINT = "https://api.nhle.com/stats/rest/en/team/summary"

REGULAR_SEASON_GAME_TYPE = 2


@dataclass(frozen=True)
class SeasonConfig:
    """Configuration for querying NHL Stats API."""

    season_id: str  # example: "20232024"
    game_type: int = REGULAR_SEASON_GAME_TYPE


def read_team_metadata(path: Path = TEAM_CSV_PATH) -> pd.DataFrame:
    """Load static NHL team metadata."""
    return pd.read_csv(path)


def _fetch_paginated(endpoint: str, params: dict, page_size: int = 200) -> List[dict]:
    """Fetch all pages for an NHL API endpoint."""
    headers = {"User-Agent": "Mozilla/5.0 (nhl-prediction-model)"}
    offset = 0
    rows: List[dict] = []
    total = None

    while True:
        query = params | {"start": offset, "limit": page_size}
        response = requests.get(endpoint, params=query, headers=headers, timeout=30)
        response.raise_for_status()
        payload = response.json()
        batch = payload.get("data", [])

        if total is None:
            total = payload.get("total", len(batch))
        rows.extend(batch)

        LOGGER.debug("Fetched rows %s-%s (%s rows, total so far %s)", offset, offset + len(batch), len(batch), len(rows))

        if len(rows) >= total or not batch:
            break
        offset += page_size

    return rows


def fetch_team_game_logs(season: SeasonConfig) -> pd.DataFrame:
    """Pull game-level team stats for a single NHL season."""
    params = {
        "isAggregate": "false",
        "isGame": "true",
        "gameType": season.game_type,
        "cayenneExp": f"seasonId={season.season_id}",
        "sort": "[{\"property\":\"gameDate\",\"direction\":\"ASC\"}]",
    }
    records = _fetch_paginated(TEAM_SUMMARY_ENDPOINT, params=params)
    frame = pd.DataFrame(records)
    frame["seasonId"] = season.season_id
    return frame


def fetch_multi_season_logs(seasons: Iterable[str]) -> pd.DataFrame:
    """Fetch and concatenate game logs for multiple seasons."""
    frames = [fetch_team_game_logs(SeasonConfig(season_id=str(season))) for season in seasons]
    combined = pd.concat(frames, ignore_index=True)
    combined["gameDate"] = pd.to_datetime(combined["gameDate"])
    return combined


@lru_cache(maxsize=1)
def get_team_reference() -> pd.DataFrame:
    """Return team metadata with derived conference labels."""
    teams = read_team_metadata()
    division_to_conference = {
        15: "Western",
        16: "Western",
        17: "Eastern",
        18: "Eastern",
    }
    teams["conference"] = teams["divisionId"].map(division_to_conference)
    teams.rename(columns={"triCode": "teamAbbrev"}, inplace=True)
    return teams


def add_team_ids(logs: pd.DataFrame) -> pd.DataFrame:
    """Attach opponent team IDs using abbreviation lookup."""
    teams = get_team_reference()[["teamId", "teamAbbrev"]]
    abbrev_to_id = teams.set_index("teamAbbrev")["teamId"].to_dict()

    logs = logs.copy()
    logs["opponentTeamId"] = logs["opponentTeamAbbrev"].map(abbrev_to_id)
    # Drop games where opponent is not an NHL franchise in the current mapping.
    logs = logs.dropna(subset=["opponentTeamId"])
    logs["opponentTeamId"] = logs["opponentTeamId"].astype(int)
    return logs


def build_game_dataframe(logs: pd.DataFrame) -> pd.DataFrame:
    """Aggregate team logs into single rows per game with home/away splits."""
    logs = add_team_ids(logs)
    logs["is_home"] = logs["homeRoad"] == "H"

    home = (
        logs.loc[logs["is_home"]]
        .rename(columns=lambda c: f"{c}_home" if c not in {"gameId", "gameDate", "seasonId"} else c)
        .reset_index(drop=True)
    )
    away = (
        logs.loc[~logs["is_home"]]
        .rename(columns=lambda c: f"{c}_away" if c not in {"gameId", "gameDate", "seasonId"} else c)
        .reset_index(drop=True)
    )

    games = pd.merge(home, away, on=["gameId", "gameDate", "seasonId"], how="inner", validate="one_to_one")
    games["home_score"] = games["goalsFor_home"]
    games["away_score"] = games["goalsFor_away"]
    games["home_win"] = (games["home_score"] > games["away_score"]).astype(int)
    games.sort_values("gameDate", inplace=True)
    return games
