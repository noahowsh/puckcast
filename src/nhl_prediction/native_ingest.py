"""Native NHL data ingestion from NHL API - replaces MoneyPuck dependency."""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.model_selection import train_test_split

from .data_sources.gamecenter import GamecenterClient

LOGGER = logging.getLogger(__name__)
_PROJECT_ROOT = Path(__file__).resolve().parents[2]
XG_MODEL_PATH = _PROJECT_ROOT / "data" / "xg_model.pkl"
CACHE_DIR = _PROJECT_ROOT / "data" / "cache"
CACHE_DIR.mkdir(exist_ok=True)


# ============================================================================
# EXPECTED GOALS (xG) MODEL
# ============================================================================

def _calculate_shot_distance(x: float, y: float, goal_x: float = 89.0) -> float:
    """Calculate distance from shot location to center of goal (in feet)."""
    return math.sqrt((goal_x - abs(x))**2 + y**2)


def _calculate_shot_angle(x: float, y: float, goal_x: float = 89.0) -> float:
    """Calculate shooting angle in degrees (0 = straight on, 90 = from boards)."""
    x_dist = goal_x - abs(x)
    if x_dist == 0:
        return 90.0
    angle_rad = math.atan(abs(y) / x_dist)
    return math.degrees(angle_rad)


def _is_high_danger_location(distance: float, angle: float) -> bool:
    """
    Classify shot as high-danger based on location.

    High-danger zone definition:
    - Distance <= 25 feet from goal
    - Angle <= 45 degrees (in front of net, not from boards)

    This roughly corresponds to the "home plate" area in front of the net.
    """
    return distance <= 25.0 and angle <= 45.0


def _parse_situation_code(code: str) -> Dict[str, Any]:
    """
    Parse NHL situation code into game state components.

    Format: ABCD where
    - A = Away skaters
    - B = Home skaters
    - C = Strength state (5=even, 4=PP, etc.)
    - D = ? (usually 1 or 5)

    Example: "1551" = 5v5 even strength
    """
    if not code or len(code) < 3:
        return {"is_even_strength": True, "is_power_play": False, "is_short_handed": False}

    away_skaters = int(code[0])
    home_skaters = int(code[1])

    is_even = away_skaters == home_skaters
    is_pp = not is_even

    return {
        "is_even_strength": is_even,
        "is_power_play": is_pp,
        "is_short_handed": is_pp,  # One team is on PP, other is SH
        "away_skaters": away_skaters,
        "home_skaters": home_skaters,
    }


@dataclass
class ShotFeatures:
    """Features for expected goals model."""
    distance: float
    angle: float
    shot_type: str
    is_even_strength: bool
    is_power_play: bool
    zone: str  # O, D, N

    def to_dict(self) -> Dict[str, Any]:
        return {
            "distance": self.distance,
            "angle": self.angle,
            "shot_type": self.shot_type,
            "is_even_strength": 1 if self.is_even_strength else 0,
            "is_power_play": 1 if self.is_power_play else 0,
            "is_offensive_zone": 1 if self.zone == "O" else 0,
        }


def _extract_shot_features(play: Dict[str, Any], home_defending: str) -> ShotFeatures:
    """Extract features from a shot event for xG model."""
    details = play.get("details", {})

    # Get coordinates (need to adjust based on which team is shooting)
    x_raw = details.get("xCoord", 0)
    y_raw = details.get("yCoord", 0)

    # NHL rink coordinates: x ranges from -100 to 100, y from -42.5 to 42.5
    # Goal is at x=89 (or -89 depending on defending side)
    # If shooting team is defending left, flip x coordinate
    event_owner = details.get("eventOwnerTeamId")
    home_team = None  # We'll infer from defending side

    # Flip coordinates if needed to make goal always at x=89
    if home_defending == "left":
        # Home team defends left goal (x=-89), so away team shoots at x=89
        # If home team is shooting, flip coordinates
        x = x_raw if event_owner else -x_raw
    else:
        # Home team defends right goal (x=89), so away team shoots at x=-89
        x = -x_raw if event_owner else x_raw

    y = y_raw

    # Calculate features
    distance = _calculate_shot_distance(x, y)
    angle = _calculate_shot_angle(x, y)

    # Get shot type
    shot_type = details.get("shotType", "wrist").lower()

    # Get situation
    situation = _parse_situation_code(play.get("situationCode", "1551"))

    # Get zone
    zone = details.get("zoneCode", "O")

    return ShotFeatures(
        distance=distance,
        angle=angle,
        shot_type=shot_type,
        is_even_strength=situation["is_even_strength"],
        is_power_play=situation["is_power_play"],
        zone=zone,
    )


def _build_xg_training_data(game_ids: List[str], client: GamecenterClient) -> pd.DataFrame:
    """
    Build training dataset for xG model from historical games.

    Processes play-by-play data to extract shot features and outcomes.
    """
    LOGGER.info(f"Building xG training data from {len(game_ids)} games...")

    all_shots = []

    for i, game_id in enumerate(game_ids):
        if i % 100 == 0:
            LOGGER.info(f"Processing game {i+1}/{len(game_ids)}")

        try:
            pbp = client.get_play_by_play(game_id)
            plays = pbp.get("plays", [])
            home_defending = None

            for play in plays:
                type_key = play.get("typeDescKey", "")

                # Track which side home team is defending
                if home_defending is None:
                    home_defending = play.get("homeTeamDefendingSide", "left")

                # Only process shot events
                if type_key not in ["shot-on-goal", "missed-shot", "blocked-shot", "goal"]:
                    continue

                # Extract features
                features = _extract_shot_features(play, home_defending)

                # Label: 1 if goal, 0 if not
                is_goal = 1 if type_key == "goal" else 0

                shot_data = features.to_dict()
                shot_data["is_goal"] = is_goal
                shot_data["game_id"] = game_id

                all_shots.append(shot_data)

        except Exception as e:
            LOGGER.warning(f"Failed to process game {game_id}: {e}")
            continue

    df = pd.DataFrame(all_shots)
    LOGGER.info(f"Built xG training data: {len(df)} shots, {df['is_goal'].sum()} goals ({df['is_goal'].mean()*100:.1f}% shooting %)")

    return df


def _train_xg_model(training_data: pd.DataFrame) -> HistGradientBoostingClassifier:
    """Train expected goals model on shot data."""
    LOGGER.info("Training xG model...")

    # Encode shot types
    shot_type_dummies = pd.get_dummies(training_data["shot_type"], prefix="shot")

    # Prepare features
    feature_cols = ["distance", "angle", "is_even_strength", "is_power_play", "is_offensive_zone"]
    X = pd.concat([training_data[feature_cols], shot_type_dummies], axis=1)
    y = training_data["is_goal"]

    # Train/val split
    X_train, X_val, y_train, y_val = train_test_split(X, y, test_size=0.2, random_state=42)

    # Train model (use fewer iterations for speed)
    model = HistGradientBoostingClassifier(
        max_iter=100,
        learning_rate=0.1,
        max_depth=4,
        max_leaf_nodes=31,
        min_samples_leaf=20,
        random_state=42,
        verbose=0,
    )

    model.fit(X_train, y_train)

    # Evaluate
    train_acc = model.score(X_train, y_train)
    val_acc = model.score(X_val, y_val)

    LOGGER.info(f"xG model trained - Train acc: {train_acc:.3f}, Val acc: {val_acc:.3f}")

    # Store feature columns for prediction
    model.feature_columns_ = X.columns.tolist()

    return model


class ExpectedGoalsModel:
    """Expected goals model for shot quality prediction."""

    def __init__(self, model: HistGradientBoostingClassifier):
        self.model = model
        self.feature_columns = model.feature_columns_

    def predict_xg(self, shot_features: ShotFeatures) -> float:
        """Predict expected goal value for a single shot."""
        # Convert to feature dict
        features = shot_features.to_dict()

        # Add shot type one-hot encoding
        shot_type = shot_features.shot_type.lower()
        for col in self.feature_columns:
            if col.startswith("shot_"):
                features[col] = 1 if col == f"shot_{shot_type}" else 0

        # Ensure all features present
        for col in self.feature_columns:
            if col not in features:
                features[col] = 0

        # Create DataFrame with correct column order
        X = pd.DataFrame([features])[self.feature_columns]

        # Predict probability
        return self.model.predict_proba(X)[0, 1]


# ============================================================================
# GAME LOG PROCESSING
# ============================================================================

def _process_game_plays(game_id: str, pbp: Dict[str, Any], xg_model: ExpectedGoalsModel) -> Dict[str, Any]:
    """
    Process all plays from a game to compute advanced metrics.

    Returns team-level statistics for both home and away teams.
    """
    plays = pbp.get("plays", [])
    home_team_id = pbp["homeTeam"]["id"]
    away_team_id = pbp["awayTeam"]["id"]
    home_team_abbrev = pbp["homeTeam"]["abbrev"]
    away_team_abbrev = pbp["awayTeam"]["abbrev"]
    game_date = pbp.get("gameDate", "")
    season = pbp.get("season", "")

    # Initialize stat counters
    stats = {
        home_team_id: {
            "teamId": home_team_id,
            "teamAbbrev": home_team_abbrev,
            "opponentTeamAbbrev": away_team_abbrev,
            "homeRoad": "H",
            "gameId": game_id,
            "gameDate": game_date,
            "season": season,
            "goalsFor": 0,
            "goalsAgainst": 0,
            "shotsForPerGame": 0,
            "shotsAgainstPerGame": 0,
            "shotAttemptsFor": 0,
            "shotAttemptsAgainst": 0,
            "xGoalsFor": 0.0,
            "xGoalsAgainst": 0.0,
            "corsiFor": 0,
            "corsiAgainst": 0,
            "fenwickFor": 0,
            "fenwickAgainst": 0,
            "highDangerShotsFor": 0,
            "highDangerShotsAgainst": 0,
            "highDangerxGoalsFor": 0.0,
            "highDangerxGoalsAgainst": 0.0,
            "faceoffsWon": 0,
            "faceoffsLost": 0,
        },
        away_team_id: {
            "teamId": away_team_id,
            "teamAbbrev": away_team_abbrev,
            "opponentTeamAbbrev": home_team_abbrev,
            "homeRoad": "A",
            "gameId": game_id,
            "gameDate": game_date,
            "season": season,
            "goalsFor": 0,
            "goalsAgainst": 0,
            "shotsForPerGame": 0,
            "shotsAgainstPerGame": 0,
            "shotAttemptsFor": 0,
            "shotAttemptsAgainst": 0,
            "xGoalsFor": 0.0,
            "xGoalsAgainst": 0.0,
            "corsiFor": 0,
            "corsiAgainst": 0,
            "fenwickFor": 0,
            "fenwickAgainst": 0,
            "highDangerShotsFor": 0,
            "highDangerShotsAgainst": 0,
            "highDangerxGoalsFor": 0.0,
            "highDangerxGoalsAgainst": 0.0,
            "faceoffsWon": 0,
            "faceoffsLost": 0,
        },
    }

    home_defending = None

    # Process each play
    for play in plays:
        type_key = play.get("typeDescKey", "")
        details = play.get("details", {})
        event_owner = details.get("eventOwnerTeamId")

        # Track defending side
        if home_defending is None:
            home_defending = play.get("homeTeamDefendingSide", "left")

        # Skip if no event owner
        if not event_owner:
            continue

        # Determine which team took the action and which team is opponent
        acting_team = event_owner
        opponent_team = away_team_id if acting_team == home_team_id else home_team_id

        # === GOALS ===
        if type_key == "goal":
            stats[acting_team]["goalsFor"] += 1
            stats[opponent_team]["goalsAgainst"] += 1

        # === SHOTS AND xG ===
        if type_key in ["shot-on-goal", "goal"]:
            stats[acting_team]["shotsForPerGame"] += 1
            stats[opponent_team]["shotsAgainstPerGame"] += 1

            # Compute xG
            features = _extract_shot_features(play, home_defending)
            xg = xg_model.predict_xg(features)

            stats[acting_team]["xGoalsFor"] += xg
            stats[opponent_team]["xGoalsAgainst"] += xg

            # High-danger shots
            if _is_high_danger_location(features.distance, features.angle):
                stats[acting_team]["highDangerShotsFor"] += 1
                stats[opponent_team]["highDangerShotsAgainst"] += 1
                stats[acting_team]["highDangerxGoalsFor"] += xg
                stats[opponent_team]["highDangerxGoalsAgainst"] += xg

        # === CORSI (all shot attempts) ===
        if type_key in ["shot-on-goal", "goal", "missed-shot", "blocked-shot"]:
            stats[acting_team]["shotAttemptsFor"] += 1
            stats[opponent_team]["shotAttemptsAgainst"] += 1
            stats[acting_team]["corsiFor"] += 1
            stats[opponent_team]["corsiAgainst"] += 1

        # === FENWICK (unblocked shot attempts) ===
        if type_key in ["shot-on-goal", "goal", "missed-shot"]:
            stats[acting_team]["fenwickFor"] += 1
            stats[opponent_team]["fenwickAgainst"] += 1

        # === FACEOFFS ===
        if type_key == "faceoff-won":
            winning_team = details.get("eventOwnerTeamId")
            losing_team = away_team_id if winning_team == home_team_id else home_team_id
            if winning_team:
                stats[winning_team]["faceoffsWon"] += 1
                stats[losing_team]["faceoffsLost"] += 1

    # Compute derived metrics
    for team_id in [home_team_id, away_team_id]:
        s = stats[team_id]

        # Corsi %
        total_corsi = s["corsiFor"] + s["corsiAgainst"]
        s["corsiPercentage"] = (s["corsiFor"] / total_corsi * 100) if total_corsi > 0 else 50.0

        # Fenwick %
        total_fenwick = s["fenwickFor"] + s["fenwickAgainst"]
        s["fenwickPercentage"] = (s["fenwickFor"] / total_fenwick * 100) if total_fenwick > 0 else 50.0

        # xGoals %
        total_xg = s["xGoalsFor"] + s["xGoalsAgainst"]
        s["xGoalsPercentage"] = (s["xGoalsFor"] / total_xg * 100) if total_xg > 0 else 50.0

        # Faceoff win %
        total_faceoffs = s["faceoffsWon"] + s["faceoffsLost"]
        s["faceoffWinPct"] = (s["faceoffsWon"] / total_faceoffs * 100) if total_faceoffs > 0 else 50.0

    return stats


def _fetch_games_for_season(season_id: str, client: GamecenterClient) -> List[str]:
    """Get all game IDs for a season."""
    # Season format: "20232024" -> use 2023
    year = int(season_id[:4])

    # Regular season game IDs: {season}02{game_num}
    # Typical season has ~1271 games (32 teams * 82 games / 2)
    game_ids = []

    for game_num in range(1, 1400):
        game_id = f"{year}02{game_num:04d}"
        game_ids.append(game_id)

    return game_ids


def _load_cached_xg_model() -> ExpectedGoalsModel | None:
    """Load cached xG model if available."""
    import pickle

    if XG_MODEL_PATH.exists():
        LOGGER.info(f"Loading cached xG model from {XG_MODEL_PATH}")
        with open(XG_MODEL_PATH, "rb") as f:
            model = pickle.load(f)
        return ExpectedGoalsModel(model)

    return None


def _save_xg_model(model: HistGradientBoostingClassifier) -> None:
    """Save xG model to cache."""
    import pickle

    XG_MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)

    with open(XG_MODEL_PATH, "wb") as f:
        pickle.dump(model, f)

    LOGGER.info(f"Saved xG model to {XG_MODEL_PATH}")


def _get_season_cache_path(season_id: str) -> Path:
    """Get path to cached season data file."""
    return CACHE_DIR / f"native_logs_{season_id}.parquet"


def _load_cached_season(season_id: str) -> pd.DataFrame | None:
    """Load cached season data if it exists."""
    cache_path = _get_season_cache_path(season_id)
    if cache_path.exists():
        LOGGER.info(f"Loading cached data for season {season_id}")
        return pd.read_parquet(cache_path)
    return None


def _save_season_cache(season_id: str, df: pd.DataFrame) -> None:
    """Save season data to cache."""
    cache_path = _get_season_cache_path(season_id)
    df.to_parquet(cache_path, index=False)
    LOGGER.info(f"Cached {len(df)} team-games for season {season_id}")


def load_native_game_logs(seasons: List[str]) -> pd.DataFrame:
    """
    Load game logs from native NHL API data for multiple seasons.

    This replaces MoneyPuck data by:
    1. Fetching play-by-play data from NHL API
    2. Computing xG using our own model
    3. Computing Corsi/Fenwick/high-danger metrics
    4. Aggregating to team-game level

    Uses caching to avoid re-fetching data from NHL API on subsequent runs.

    Args:
        seasons: List of season IDs (e.g., ["20212022", "20222023"])

    Returns:
        DataFrame with team-game logs matching MoneyPuck schema
    """
    LOGGER.info(f"Loading native game logs for seasons: {seasons}")

    # Try to load cached data for each season
    season_dataframes = []
    seasons_to_fetch = []

    for season_id in seasons:
        cached_df = _load_cached_season(season_id)
        if cached_df is not None:
            season_dataframes.append(cached_df)
        else:
            seasons_to_fetch.append(season_id)

    # If all seasons are cached, combine and return
    if not seasons_to_fetch:
        LOGGER.info("All seasons loaded from cache!")
        return pd.concat(season_dataframes, ignore_index=True) if season_dataframes else pd.DataFrame()

    # Otherwise, fetch missing seasons from NHL API
    LOGGER.info(f"Fetching {len(seasons_to_fetch)} seasons from NHL API: {seasons_to_fetch}")

    # Use slower rate limiting to avoid 503 errors
    client = GamecenterClient(rate_limit_seconds=1.0)

    # Load or train xG model
    xg_model = _load_cached_xg_model()

    if xg_model is None:
        LOGGER.info("No cached xG model found - training new model...")

        # Get training games from earlier seasons (use fewer games for speed)
        # Sample ~200 games from 2021-2022 season should give us ~50K shots
        training_game_ids = []
        for train_season in ["20212022"]:
            season_games = _fetch_games_for_season(train_season, client)[:200]  # 200 games = ~50K shots
            training_game_ids.extend(season_games)

        LOGGER.info(f"Training xG model on {len(training_game_ids)} games...")

        # Build training data
        training_data = _build_xg_training_data(training_game_ids, client)

        # Train model
        sklearn_model = _train_xg_model(training_data)

        # Cache model
        _save_xg_model(sklearn_model)

        xg_model = ExpectedGoalsModel(sklearn_model)

    # Process requested seasons that need to be fetched
    for season_id in seasons_to_fetch:
        LOGGER.info(f"Processing season {season_id}...")

        season_team_games = []

        game_ids = _fetch_games_for_season(season_id, client)
        consecutive_errors = 0
        max_consecutive_errors = 10  # Stop after 10 consecutive failures

        for i, game_id in enumerate(game_ids):
            if i % 100 == 0:
                LOGGER.info(f"Processing game {i+1}/{len(game_ids)} in season {season_id}")

            try:
                pbp = client.get_play_by_play(game_id)

                # Skip if game not played yet
                if pbp.get("gameState") not in ["OFF", "FINAL"]:
                    consecutive_errors += 1
                    if consecutive_errors >= max_consecutive_errors:
                        LOGGER.info(f"Reached unplayed games, processed {len(all_team_games)} team-games so far")
                        break
                    continue

                # Successfully processed game - reset error counter
                consecutive_errors = 0

                # Process game
                game_stats = _process_game_plays(game_id, pbp, xg_model)

                # Add both team stats to list
                for team_id, team_stats in game_stats.items():
                    team_stats["seasonId"] = season_id
                    season_team_games.append(team_stats)

            except Exception as e:
                consecutive_errors += 1
                error_msg = str(e)

                # Log first few errors for debugging
                if i < 20:
                    LOGGER.warning(f"Error processing game {game_id}: {error_msg[:100]}")

                # Stop if we hit too many consecutive errors (likely end of season or API issues)
                if consecutive_errors >= max_consecutive_errors:
                    LOGGER.info(f"Stopped after {consecutive_errors} consecutive errors. Processed {len(season_team_games)} team-games.")
                    break

        # Convert season data to DataFrame
        season_df = pd.DataFrame(season_team_games)

        if not season_df.empty:
            # Compute goaltending metrics for this season
            season_df = _compute_goaltending_metrics(season_df)

            # Cache this season for future runs
            _save_season_cache(season_id, season_df)

            # Add to list of all seasons
            season_dataframes.append(season_df)

    # Combine all seasons (cached + newly fetched)
    if not season_dataframes:
        LOGGER.warning("No games found - returning empty DataFrame")
        return pd.DataFrame()

    combined_df = pd.concat(season_dataframes, ignore_index=True)
    LOGGER.info(f"Loaded {len(combined_df)} team-games total from native NHL API")

    return combined_df


def _compute_goaltending_metrics(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute team-level goaltending metrics from game logs.

    Metrics:
    - team_save_pct: Season-to-date save percentage
    - team_gsax_per_60: Goals Saved Above Expected per 60 minutes (season-to-date)
    """
    df = df.copy()

    # Compute per-game save percentage
    df["saves"] = df["shotsAgainstPerGame"] - df["goalsAgainst"]
    df["save_pct"] = df["saves"] / df["shotsAgainstPerGame"].replace(0, 1)  # Avoid div by zero

    # Compute per-game GSAx (Goals Saved Above Expected)
    # GSAx = xGoalsAgainst - goalsAgainst
    # Positive GSAx means goalie saved more than expected (good)
    df["gsax"] = df["xGoalsAgainst"] - df["goalsAgainst"]

    # Compute season-to-date aggregates by team and season
    df = df.sort_values(["teamId", "gameDate"])

    # Running totals
    df["cumulative_saves"] = df.groupby(["teamId", "seasonId"])["saves"].cumsum()
    df["cumulative_shots_against"] = df.groupby(["teamId", "seasonId"])["shotsAgainstPerGame"].cumsum()
    df["cumulative_gsax"] = df.groupby(["teamId", "seasonId"])["gsax"].cumsum()
    df["cumulative_minutes"] = df.groupby(["teamId", "seasonId"]).cumcount() + 1  # Games played
    df["cumulative_minutes"] = df["cumulative_minutes"] * 60  # Approx minutes (60 min/game)

    # Season-to-date metrics
    df["team_save_pct"] = df["cumulative_saves"] / df["cumulative_shots_against"].replace(0, 1)
    df["team_gsax_per_60"] = df["cumulative_gsax"] / (df["cumulative_minutes"] / 60)

    # Fill NaN with league average
    df["team_save_pct"] = df["team_save_pct"].fillna(0.86)
    df["team_gsax_per_60"] = df["team_gsax_per_60"].fillna(0.0)

    # Drop intermediate columns
    df = df.drop(columns=["saves", "save_pct", "gsax", "cumulative_saves",
                          "cumulative_shots_against", "cumulative_gsax", "cumulative_minutes"])

    return df
