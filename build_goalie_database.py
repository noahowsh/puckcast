"""
Build goalie performance database from NHL API boxscore data.

Extracts individual goalie stats from each game and builds a comprehensive
GoalieTracker database for V7.0 individual goalie features.
"""

import pickle
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import logging

from src.nhl_prediction.goalie_tracker import GoalieTracker
from src.nhl_prediction.data_sources.gamecenter import GamecenterClient

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
LOGGER = logging.getLogger(__name__)

PROJECT_ROOT = Path(__file__).parent
CACHE_DIR = PROJECT_ROOT / "data" / "cache"
OUTPUT_PATH = PROJECT_ROOT / "data" / "goalie_tracker.pkl"


def extract_goalie_stats_from_boxscore(
    boxscore: Dict[str, Any],
    game_id: str,
    game_date: str
) -> List[Dict[str, Any]]:
    """
    Extract goalie statistics from boxscore JSON.

    Returns list of goalie stat dictionaries.
    """
    goalies = []

    # Boxscore structure: playerByGameStats -> awayTeam/homeTeam -> goalies
    player_stats = boxscore.get("playerByGameStats", {})

    for side in ["awayTeam", "homeTeam"]:
        team_data = player_stats.get(side, {})
        team_id = team_data.get("teamId")
        team_abbrev = team_data.get("abbrev", "UNK")

        # Get opponent info
        opponent_side = "homeTeam" if side == "awayTeam" else "awayTeam"
        opponent_data = player_stats.get(opponent_side, {})
        opponent_abbrev = opponent_data.get("abbrev", "UNK")

        # Process goalies for this team
        goalie_list = team_data.get("goalies", [])

        for goalie in goalie_list:
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

            # Time on ice
            toi = goalie.get("toi", "00:00")
            try:
                mins, secs = toi.split(":")
                toi_seconds = int(mins) * 60 + int(secs)
            except:
                toi_seconds = 0

            # Only include goalies who actually played
            if toi_seconds > 0:
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
                    "toi_seconds": toi_seconds,
                })

    return goalies


def build_goalie_database(seasons: List[str] = ["20212022", "20222023", "20232024"]) -> GoalieTracker:
    """
    Build comprehensive goalie database from NHL API data.

    Args:
        seasons: List of season IDs to process

    Returns:
        GoalieTracker with all historical goalie performance
    """
    LOGGER.info("=" * 80)
    LOGGER.info("Building Goalie Database from NHL API")
    LOGGER.info("=" * 80)

    # Initialize tracker and client
    tracker = GoalieTracker()
    client = GamecenterClient()

    # Load all games from parquet files
    all_games = []
    for season in seasons:
        parquet_path = CACHE_DIR / f"native_logs_{season}.parquet"
        if not parquet_path.exists():
            LOGGER.warning(f"Parquet file not found: {parquet_path}")
            continue

        df = pd.read_parquet(parquet_path)
        # Get unique games (each game appears twice, once per team)
        games = df[['gameId', 'gameDate']].drop_duplicates()
        all_games.append(games)
        LOGGER.info(f"Season {season}: {len(games)} games")

    # Combine all games
    all_games_df = pd.concat(all_games, ignore_index=True)
    all_games_df = all_games_df.drop_duplicates(subset=['gameId'])
    total_games = len(all_games_df)

    LOGGER.info(f"\nTotal unique games to process: {total_games}")
    LOGGER.info(f"Fetching boxscore data (using cache where available)...\n")

    # Process each game
    goalies_processed = 0
    games_processed = 0

    for idx, row in all_games_df.iterrows():
        game_id = str(row['gameId'])
        game_date = str(row['gameDate'])

        if games_processed % 100 == 0 and games_processed > 0:
            LOGGER.info(f"Progress: {games_processed}/{total_games} games, {goalies_processed} goalies")

        try:
            # Fetch boxscore (uses cache if available)
            boxscore = client.get_boxscore(game_id)

            # Extract goalie stats
            goalie_stats = extract_goalie_stats_from_boxscore(boxscore, game_id, game_date)

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
                    high_danger_saves=0,  # Not available in basic boxscore
                    high_danger_shots=0,
                    rush_saves=0,
                    rush_shots=0,
                    expected_goals_against=0.0,  # Will compute from xG model later
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

    # Display top goalies by games played
    LOGGER.info(f"\nTop 10 Goalies by Games Played:")
    LOGGER.info(f"{'Name':30s} {'Games':>6s} {'Save%':>8s} {'GAA':>8s}")
    LOGGER.info("-" * 80)

    goalie_summaries = []
    for goalie_id, games in tracker.goalie_games.items():
        total_saves = sum(g['saves'] for g in games)
        total_shots = sum(g['shots_against'] for g in games)
        total_goals = sum(g['goals_against'] for g in games)
        total_toi = sum(g['toi_seconds'] for g in games)

        save_pct = total_saves / total_shots if total_shots > 0 else 0
        gaa = (total_goals / total_toi * 3600) if total_toi > 0 else 0

        goalie_summaries.append({
            'id': goalie_id,
            'games': len(games),
            'save_pct': save_pct,
            'gaa': gaa,
        })

    # Sort by games played
    goalie_summaries.sort(key=lambda x: x['games'], reverse=True)

    for i, summary in enumerate(goalie_summaries[:10]):
        LOGGER.info(f"#{i+1:2d} Goalie {summary['id']:20d} {summary['games']:6d} {summary['save_pct']:8.3f} {summary['gaa']:8.2f}")

    return tracker


def main():
    # Build database
    tracker = build_goalie_database()

    # Save to disk
    LOGGER.info(f"\nSaving database to: {OUTPUT_PATH}")
    OUTPUT_PATH.parent.mkdir(exist_ok=True)

    with open(OUTPUT_PATH, 'wb') as f:
        pickle.dump(tracker, f)

    LOGGER.info(f"✓ Goalie database saved ({OUTPUT_PATH.stat().st_size / 1024:.1f} KB)")
    LOGGER.info("\nDatabase ready for V7.0 individual goalie features!")


if __name__ == "__main__":
    main()
