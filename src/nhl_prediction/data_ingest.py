"""Data ingestion utilities for NHL predictive modelling using MoneyPuck data."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Iterable, List

import pandas as pd

from .native_ingest import load_native_game_logs
from .goalie_features import enhance_with_goalie_features

LOGGER = logging.getLogger(__name__)

_PROJECT_ROOT = Path(__file__).resolve().parents[2]
TEAM_CSV_PATH = _PROJECT_ROOT / "data" / "nhl_teams.csv"
MONEYPUCK_DATA_PATH = _PROJECT_ROOT / "data" / "moneypuck_all_games.csv"
TEAM_GOALTENDING_PATH = _PROJECT_ROOT / "data" / "team_goaltending.csv"

REGULAR_SEASON_GAME_TYPE = 2


@dataclass(frozen=True)
class SeasonConfig:
    """Configuration for querying MoneyPuck data."""

    season_id: str  # example: "20232024"
    game_type: int = REGULAR_SEASON_GAME_TYPE


def read_team_metadata(path: Path = TEAM_CSV_PATH) -> pd.DataFrame:
    """Load static NHL team metadata."""
    return pd.read_csv(path)


def load_moneypuck_data(data_path: Path = MONEYPUCK_DATA_PATH) -> pd.DataFrame:
    """
    Load MoneyPuck game-by-game data for all teams.
    
    Returns:
        DataFrame with game-level team statistics including expected goals,
        shot quality metrics, and advanced analytics.
    """
    LOGGER.info(f"Loading MoneyPuck data from {data_path}")
    df = pd.read_csv(data_path)
    
    # Filter to team-level data (not player-level) and "all" situation (full game stats)
    df = df[
        (df['position'] == 'Team Level') & 
        (df['situation'] == 'all') &
        (df['playoffGame'] == 0)  # Regular season only
    ].copy()
    
    LOGGER.info(f"Loaded {len(df)} team-games from MoneyPuck")
    return df


def fetch_team_game_logs(season: SeasonConfig) -> pd.DataFrame:
    """
    Pull game-level team stats for a single NHL season from MoneyPuck data.
    
    Args:
        season: Season configuration (season_id like "20232024")
    
    Returns:
        DataFrame with game logs for the specified season
    """
    # Load full MoneyPuck dataset
    df = load_moneypuck_data()
    
    # Convert season format: MoneyPuck uses 2023 for 2023-24 season
    # Our format is 20232024, so extract first 4 digits
    moneypuck_season = int(season.season_id[:4])
    
    # Filter to requested season
    season_df = df[df['season'] == moneypuck_season].copy()
    
    # Standardize column names to match expected format
    season_df = _standardize_moneypuck_columns(season_df)
    
    # Add seasonId in our format
    season_df['seasonId'] = season.season_id
    
    LOGGER.info(f"Fetched {len(season_df)} games for season {season.season_id}")
    return season_df


def _add_goaltending_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add team-level goaltending metrics to game logs.
    
    Merges season-aggregate goaltending quality (save %, GSAx/60) for each team.
    This represents the overall quality of a team's goaltending corps that season.
    """
    try:
        goalies = pd.read_csv(TEAM_GOALTENDING_PATH)
        
        # Merge goalie metrics by team abbreviation and season
        df = df.merge(
            goalies[['team', 'season', 'team_save_pct', 'team_gsax_per_60']],
            left_on=['teamAbbrev', 'season'],
            right_on=['team', 'season'],
            how='left'
        )
        
        # Drop duplicate 'team' column from merge
        df = df.drop(columns=['team'], errors='ignore')
        
        # Fill missing values with league average
        df['team_save_pct'] = df['team_save_pct'].fillna(0.86)  # ~86% is typical
        df['team_gsax_per_60'] = df['team_gsax_per_60'].fillna(0.0)
        
        LOGGER.info(f"Added goaltending metrics to {len(df)} games")
        
    except FileNotFoundError:
        LOGGER.warning(f"Goaltending data not found at {TEAM_GOALTENDING_PATH}, skipping goalie metrics")
        df['team_save_pct'] = 0.86
        df['team_gsax_per_60'] = 0.0
    
    return df


def _standardize_moneypuck_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Rename and create columns to match expected schema.
    
    MoneyPuck columns → Our expected columns
    """
    df = df.copy()
    
    # Core game identifiers
    df['teamAbbrev'] = df['playerTeam']
    df['opponentTeamAbbrev'] = df['opposingTeam']
    df['homeRoad'] = df['home_or_away'].apply(lambda x: 'H' if x == 'HOME' else 'A')
    
    # Map team abbreviations to numeric IDs
    teams = read_team_metadata()
    abbrev_to_id = teams.set_index('triCode')['teamId'].to_dict()
    df['teamId'] = df['teamAbbrev'].map(abbrev_to_id)
    
    # Drop rows where team abbreviation doesn't match (e.g., old franchises)
    df = df.dropna(subset=['teamId'])
    df['teamId'] = df['teamId'].astype(int)
    
    # Date
    df['gameDate'] = pd.to_datetime(df['gameDate'], format='%Y%m%d')
    
    # Goals and outcomes
    df['goalsFor'] = df['goalsFor']
    df['goalsAgainst'] = df['goalsAgainst']
    
    # Shots
    df['shotsForPerGame'] = df['shotsOnGoalFor']
    df['shotsAgainstPerGame'] = df['shotsOnGoalAgainst']
    
    # Shot attempts (Corsi)
    df['shotAttemptsFor'] = df['shotAttemptsFor']
    df['shotAttemptsAgainst'] = df['shotAttemptsAgainst']
    
    # NOTE: MoneyPuck doesn't provide PP%/PK% per game (only opportunities/goals).
    # We could calculate cumulative season PP%/PK% but it's not worth it - xGoals
    # captures shot quality better anyway. Removed these features.
    
    # Faceoffs
    df['faceoffWinPct'] = (
        df['faceOffsWonFor'] / (df['faceOffsWonFor'] + df['faceOffsWonAgainst'])
    ).fillna(0.5) * 100
    
    # Expected goals (MoneyPuck's unique advantage!)
    df['xGoalsFor'] = df['xGoalsFor']
    df['xGoalsAgainst'] = df['xGoalsAgainst']
    df['xGoalsPercentage'] = df['xGoalsPercentage']
    
    # Possession metrics
    df['corsiPercentage'] = df['corsiPercentage'] * 100
    df['fenwickPercentage'] = df['fenwickPercentage'] * 100
    
    # Shot quality
    df['highDangerShotsFor'] = df['highDangerShotsFor']
    df['highDangerShotsAgainst'] = df['highDangerShotsAgainst']
    df['highDangerxGoalsFor'] = df['highDangerxGoalsFor']
    df['highDangerxGoalsAgainst'] = df['highDangerxGoalsAgainst']
    
    # NOTE: Cumulative season stats (wins, losses, points) are NOT provided by MoneyPuck per game.
    # These would need to be calculated from game outcomes across the season.
    # We don't use these - we use xGoals and rolling windows instead which are more predictive.
    
    # Add goaltending metrics
    df = _add_goaltending_metrics(df)
    
    return df


def fetch_multi_season_logs(seasons: Iterable[str]) -> pd.DataFrame:
    """
    Fetch and concatenate game logs for multiple seasons from MoneyPuck data.

    Args:
        seasons: List of season IDs (e.g., ["20212022", "20222023", "20232024"])

    Returns:
        Combined DataFrame with all requested seasons
    """
    native = load_native_game_logs(seasons)
    if not native.empty:
        native["gameDate"] = pd.to_datetime(native["gameDate"])
        LOGGER.info("Loaded %d native team-games across %d seasons (%s)",
                    len(native), len(seasons), ", ".join(str(s) for s in seasons))
        # Add individual starting goalie features
        native = enhance_with_goalie_features(native)
        return native

    frames = [fetch_team_game_logs(SeasonConfig(season_id=str(season))) for season in seasons]
    combined = pd.concat(frames, ignore_index=True)
    combined["gameDate"] = pd.to_datetime(combined["gameDate"])

    LOGGER.info(f"Falling back to MoneyPuck: combined {len(combined)} team-games across {len(seasons)} seasons")

    # Add individual starting goalie features
    combined = enhance_with_goalie_features(combined)

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
    """
    Aggregate team logs into single rows per game with home/away splits.
    
    Takes MoneyPuck data (one row per team per game) and creates matchups
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
