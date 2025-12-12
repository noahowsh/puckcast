#!/usr/bin/env python3
"""
Build goalie performance database with PROPER xG and team attribution.

FIXES:
1. Team abbreviations from parquet data (not boxscore)
2. xG from team-level data, attributed by TOI
3. Proper GSA calculation
4. Only training data (2021-22, 2022-23) to avoid leakage
"""

import pickle
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import logging

from src.nhl_prediction.goalie_tracker import GoalieTracker
from src.nhl_prediction.data_sources.gamecenter import GamecenterClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
OUTPUT_PATH = PROJECT_ROOT / "data" / "goalie_tracker_train_only_fixed.pkl"

TRAIN_SEASONS = ["20212022", "20222023"]  # TRAINING ONLY - no test set


def load_team_game_data(seasons: List[str]) -> pd.DataFrame:
    """Load team-level game data with xG stats."""
    all_data = []

    for season in seasons:
        parquet_path = CACHE_DIR / f"native_logs_{season}.parquet"
        if not parquet_path.exists():
            LOGGER.warning(f"Parquet file not found: {parquet_path}")
            continue

        df = pd.read_parquet(parquet_path)
        all_data.append(df)
        LOGGER.info(f"Loaded {len(df)} team-games from {season}")

    combined = pd.concat(all_data, ignore_index=True)
    LOGGER.info(f"Total: {len(combined)} team-games")

    return combined


def extract_goalie_stats_from_boxscore(
    boxscore: Dict[str, Any],
    game_id: str,
    game_date: str,
    team_data_lookup: Dict[str, Dict]
) -> List[Dict[str, Any]]:
    """
    Extract goalie statistics from boxscore with proper team and xG attribution.

    Args:
        boxscore: NHL API boxscore
        game_id: Game ID
        game_date: Game date
        team_data_lookup: Dict mapping (gameId, teamId) -> {team stats}

    Returns:
        List of goalie stat dictionaries
    """
    goalies = []
    player_stats = boxscore.get("playerByGameStats", {})

    for side in ["awayTeam", "homeTeam"]:
        # Get team info from root level
        team_info = boxscore.get(side, {})
        team_id = team_info.get("id")
        team_abbrev = team_info.get("abbrev", "UNK")

        # Get goalie data from playerByGameStats
        team_player_data = player_stats.get(side, {})

        # Get team stats from parquet data using (gameId, teamId) key
        team_stats = team_data_lookup.get((game_id, team_id), {})
        if team_stats:
            team_abbrev = team_stats.get('teamAbbrev', team_abbrev)

        # Get opponent info
        opponent_side = "homeTeam" if side == "awayTeam" else "awayTeam"
        opponent_info = boxscore.get(opponent_side, {})
        opponent_id = opponent_info.get("id")
        opponent_abbrev = opponent_info.get("abbrev", "UNK")

        opponent_stats = team_data_lookup.get((game_id, opponent_id), {})
        if opponent_stats:
            opponent_abbrev = opponent_stats.get('teamAbbrev', opponent_abbrev)

        # Get team's expected goals against (what opponent generated)
        # For home team: use away team's xGoalsFor
        # For away team: use home team's xGoalsFor
        team_xga = opponent_stats.get('xGoalsFor', 0.0)

        # Process goalies for this team
        goalie_list = team_player_data.get("goalies", [])

        # Calculate total TOI for all goalies on this team
        total_toi = 0
        goalie_toi_list = []
        for goalie in goalie_list:
            toi = goalie.get("toi", "00:00")
            try:
                mins, secs = toi.split(":")
                toi_seconds = int(mins) * 60 + int(secs)
            except:
                toi_seconds = 0

            goalie_toi_list.append((goalie, toi_seconds))
            total_toi += toi_seconds

        # Attribute xG to each goalie proportional to their TOI
        for goalie, toi_seconds in goalie_toi_list:
            if toi_seconds == 0:
                continue  # Skip backup goalies who didn't play

            player_id = goalie.get("playerId")
            name = goalie.get("name", {})
            full_name = f"{name.get('default', 'Unknown')}"

            # Get stats
            saves = goalie.get("saveShotsAgainst", "0/0")
            if "/" in saves:
                parts = saves.split("/")
                saves_made = int(parts[0])
                shots_against = int(parts[1])
                goals_against = shots_against - saves_made
            else:
                saves_made = 0
                shots_against = 0
                goals_against = 0

            # Attribute xG based on TOI proportion
            if total_toi > 0:
                toi_proportion = toi_seconds / total_toi
                goalie_xga = team_xga * toi_proportion
            else:
                goalie_xga = 0.0

            # Calculate GSA (Goals Saved Above Expected)
            gsa = goalie_xga - goals_against

            goalies.append({
                "goalie_id": player_id,
                "name": full_name,
                "game_id": game_id,
                "game_date": game_date,
                "team": team_abbrev,
                "opponent": opponent_abbrev,
                "saves": saves_made,
                "shots_against": shots_against,
                "goals_against": goals_against,
                "expected_goals_against": goalie_xga,
                "gsa": gsa,
                "toi_seconds": toi_seconds,
                "high_danger_saves": 0,  # Not available in basic boxscore
                "high_danger_shots": 0,
                "rush_saves": 0,
                "rush_shots": 0,
            })

    return goalies


def build_goalie_database(seasons: List[str]) -> GoalieTracker:
    """
    Build comprehensive goalie database with proper xG attribution.

    Args:
        seasons: List of season IDs to process

    Returns:
        GoalieTracker with all historical goalie performance
    """
    LOGGER.info("=" * 80)
    LOGGER.info("Building FIXED Goalie Database with Proper xG")
    LOGGER.info("=" * 80)

    # Load team-level data
    team_data = load_team_game_data(seasons)

    # Create lookup: (gameId, teamId) -> team stats
    team_data_lookup = {}
    for _, row in team_data.iterrows():
        key = (str(row['gameId']), row['teamId'])  # Convert gameId to string for matching
        team_data_lookup[key] = row.to_dict()

    # Initialize tracker and client
    tracker = GoalieTracker()
    client = GamecenterClient()

    # Get unique games
    unique_games = team_data[['gameId', 'gameDate']].drop_duplicates()
    total_games = len(unique_games)

    LOGGER.info(f"\nTotal unique games to process: {total_games}")
    LOGGER.info(f"Fetching boxscore data (using cache where available)...\n")

    # Process each game
    goalies_processed = 0
    games_processed = 0

    for idx, row in unique_games.iterrows():
        game_id = str(row['gameId'])
        game_date = str(row['gameDate'])

        if games_processed % 100 == 0 and games_processed > 0:
            LOGGER.info(f"Progress: {games_processed}/{total_games} games, {goalies_processed} goalie performances")

        try:
            # Fetch boxscore (uses cache if available)
            boxscore = client.get_boxscore(game_id)

            # Extract goalie stats with proper team and xG
            goalie_stats = extract_goalie_stats_from_boxscore(
                boxscore, game_id, game_date, team_data_lookup
            )

            # Add to tracker
            for stats in goalie_stats:
                tracker.add_game(
                    goalie_id=stats['goalie_id'],
                    game_id=stats['game_id'],
                    game_date=stats['game_date'],
                    team=stats['team'],
                    opponent=stats['opponent'],
                    saves=stats['saves'],
                    shots_against=stats['shots_against'],
                    goals_against=stats['goals_against'],
                    high_danger_saves=stats['high_danger_saves'],
                    high_danger_shots=stats['high_danger_shots'],
                    rush_saves=stats['rush_saves'],
                    rush_shots=stats['rush_shots'],
                    expected_goals_against=stats['expected_goals_against'],
                    toi_seconds=stats['toi_seconds']
                )
                goalies_processed += 1

            games_processed += 1

        except Exception as e:
            LOGGER.error(f"Error processing game {game_id}: {e}")
            continue

    LOGGER.info(f"\n" + "=" * 80)
    LOGGER.info(f"Database build complete!")
    LOGGER.info(f"=" * 80)
    LOGGER.info(f"Games processed: {games_processed}/{total_games}")
    LOGGER.info(f"Goalie performances: {goalies_processed}")
    LOGGER.info(f"Unique goalies: {len(tracker.goalie_games)}")

    # Display top goalies by GSA
    LOGGER.info(f"\nTop 10 Goalies by Total GSA:")
    LOGGER.info(f"{'Name':30s} {'Games':>6s} {'GSA':>8s} {'Save%':>8s} {'GAA':>8s}")
    LOGGER.info("-" * 80)

    goalie_summaries = []
    for goalie_id, games in tracker.goalie_games.items():
        total_saves = sum(g['saves'] for g in games)
        total_shots = sum(g['shots_against'] for g in games)
        total_goals = sum(g['goals_against'] for g in games)
        total_gsa = sum(g['gsa'] for g in games)
        total_toi = sum(g['toi_seconds'] for g in games)

        save_pct = total_saves / total_shots if total_shots > 0 else 0
        gaa = (total_goals / total_toi * 3600) if total_toi > 0 else 0

        goalie_summaries.append({
            'id': goalie_id,
            'games': len(games),
            'gsa': total_gsa,
            'save_pct': save_pct,
            'gaa': gaa,
        })

    # Sort by GSA
    goalie_summaries.sort(key=lambda x: x['gsa'], reverse=True)

    for i, summary in enumerate(goalie_summaries[:10]):
        LOGGER.info(f"#{i+1:2d} Goalie {summary['id']:20d} {summary['games']:6d} {summary['gsa']:8.2f} {summary['save_pct']:8.3f} {summary['gaa']:8.2f}")

    return tracker


def main():
    # Build database from TRAINING DATA ONLY
    tracker = build_goalie_database(TRAIN_SEASONS)

    # Save to disk
    LOGGER.info(f"\nSaving database to: {OUTPUT_PATH}")
    OUTPUT_PATH.parent.mkdir(exist_ok=True)

    with open(OUTPUT_PATH, 'wb') as f:
        pickle.dump(tracker, f)

    LOGGER.info(f"✓ FIXED goalie database saved ({OUTPUT_PATH.stat().st_size / 1024:.1f} KB)")
    LOGGER.info("\nDatabase ready for V7.1 training with proper GSA!")


if __name__ == "__main__":
    main()
