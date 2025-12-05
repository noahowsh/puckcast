"""Data ingestion utilities for NHL predictive modelling using native NHL API."""

from __future__ import annotations

import logging
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import pandas as pd

from .native_ingest import load_native_game_logs
from .goalie_features import enhance_with_goalie_features

LOGGER = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEAM_CSV_PATH = _PROJECT_ROOT / "data" / "nhl_teams.csv"

REGULAR_SEASON_GAME_TYPE = 2


def read_team_metadata(path: Path = TEAM_CSV_PATH) -> pd.DataFrame:
    """Load static NHL team metadata."""
    return pd.read_csv(path)


def fetch_multi_season_logs(seasons: Iterable[str]) -> pd.DataFrame:
    """
    Fetch and concatenate game logs for multiple seasons from native NHL API.

    Uses play-by-play data from NHL API to compute:
    - Expected goals (xG) using custom ML model
    - Shot quality metrics (Corsi, Fenwick, high-danger shots)
    - Faceoff, penalty, and possession statistics
    - Team-game level aggregations

    Includes caching to avoid re-fetching data on subsequent runs.

    Args:
        seasons: List of season IDs (e.g., ["20212022", "20222023", "20232024"])

    Returns:
        Combined DataFrame with all requested seasons
    """
    LOGGER.info(f"Fetching game logs for seasons: {seasons}")

    # Load from native NHL API with caching
    native = load_native_game_logs(list(seasons))

    if native.empty:
        LOGGER.error("Failed to load any game logs from NHL API")
        return pd.DataFrame()

    native["gameDate"] = pd.to_datetime(native["gameDate"])

    LOGGER.info(
        "Loaded %d native team-games across %d seasons (%s)",
        len(native),
        len(seasons),
        ", ".join(str(s) for s in seasons)
    )

    # Enhance with goalie-specific features
    native = enhance_with_goalie_features(native)

    return native


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
    """
    Aggregate team logs into single rows per game with home/away splits.

    Takes team-level data (one row per team per game) and creates matchups
    (one row per game with home and away team data).
    """
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

    LOGGER.info(f"Built {len(games)} complete game matchups")
    return games
