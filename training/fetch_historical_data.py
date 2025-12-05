"""Fetch historical NHL season data from 2017-18 through 2020-21.

This script fetches play-by-play data for older NHL seasons to expand
the training dataset. The NHL Web API (api-web.nhle.com/v1) supports
historical data back to the 2017-18 season.

Season Notes:
- 2017-18: Full 82-game season, 31 teams (1271 games)
- 2018-19: Full 82-game season, 31 teams (1271 games)
- 2019-20: COVID-shortened (~68-71 games/team before March 11, 2020 pause)
           Regular season resumed in August 2020 as playoffs only
           Approximately 1082 regular season games completed
- 2020-21: COVID-shortened 56-game season, all-division schedule (868 games)

Total expected games: ~4,492 games (8,984 team-game rows)
Estimated fetch time: 2-4 hours with rate limiting
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(project_root / "src"))

import logging

# Set up logging to see progress
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

from nhl_prediction.native_ingest import load_native_game_logs, _get_season_cache_path

# Historical seasons to fetch
HISTORICAL_SEASONS = {
    "20172018": {
        "name": "2017-18",
        "description": "Full 82-game season, 31 teams",
        "expected_games": 1271,
    },
    "20182019": {
        "name": "2018-19",
        "description": "Full 82-game season, 31 teams",
        "expected_games": 1271,
    },
    "20192020": {
        "name": "2019-20",
        "description": "COVID-shortened (pause March 11, 2020)",
        "expected_games": 1082,  # Actual games completed before pause
    },
    "20202021": {
        "name": "2020-21",
        "description": "COVID-shortened 56-game season",
        "expected_games": 868,
    },
}


def check_cached_seasons():
    """Check which seasons are already cached."""
    cached = []
    missing = []

    for season_id, info in HISTORICAL_SEASONS.items():
        cache_path = _get_season_cache_path(season_id)
        if cache_path.exists():
            cached.append((season_id, info))
        else:
            missing.append((season_id, info))

    return cached, missing


def fetch_season(season_id: str, force: bool = False):
    """Fetch a single season's data."""
    info = HISTORICAL_SEASONS[season_id]
    cache_path = _get_season_cache_path(season_id)

    if cache_path.exists() and not force:
        print(f"\n{info['name']} already cached at {cache_path}")
        print("Use --force to re-fetch")
        return None

    print(f"\n{'='*60}")
    print(f"FETCHING {info['name']} NHL SEASON")
    print(f"{'='*60}")
    print(f"Description: {info['description']}")
    print(f"Expected games: ~{info['expected_games']}")
    print(f"{'='*60}")

    df = load_native_game_logs([season_id])

    print(f"\n{'='*60}")
    print(f"{info['name']} FETCH COMPLETE!")
    print(f"{'='*60}")
    print(f"Total team-games fetched: {len(df)}")

    if not df.empty and 'gameId' in df.columns:
        unique_games = df['gameId'].nunique()
        print(f"Unique games: {unique_games}")
        print(f"Date range: {df['gameDate'].min()} to {df['gameDate'].max()}")
        print(f"Data saved to: {cache_path}")

    return df


def fetch_all_historical(force: bool = False):
    """Fetch all historical seasons."""
    cached, missing = check_cached_seasons()

    print("="*60)
    print("HISTORICAL NHL DATA FETCH")
    print("="*60)
    print()
    print("Seasons to fetch: 2017-18 through 2020-21")
    print()

    if cached:
        print("Already cached:")
        for season_id, info in cached:
            cache_path = _get_season_cache_path(season_id)
            print(f"  - {info['name']}: {cache_path}")

    if missing:
        print("\nMissing (will fetch):")
        for season_id, info in missing:
            print(f"  - {info['name']}: {info['description']}")
        print()

        total_expected = sum(info['expected_games'] for _, info in missing)
        print(f"Total expected games: ~{total_expected}")
        print(f"Estimated time: {total_expected // 60}-{total_expected // 30} minutes")

    if not missing and not force:
        print("\nAll historical seasons already cached!")
        print("Use --force to re-fetch all seasons")
        return

    print()
    print("-"*60)

    # Fetch each season
    seasons_to_fetch = [s[0] for s in missing] if not force else list(HISTORICAL_SEASONS.keys())

    results = {}
    for season_id in seasons_to_fetch:
        df = fetch_season(season_id, force=force)
        if df is not None:
            results[season_id] = len(df)

    # Summary
    print()
    print("="*60)
    print("ALL HISTORICAL SEASONS COMPLETE!")
    print("="*60)

    for season_id, count in results.items():
        info = HISTORICAL_SEASONS[season_id]
        print(f"  {info['name']}: {count} team-games")

    total = sum(results.values())
    print(f"\nTotal: {total} team-games across {len(results)} seasons")


def main():
    parser = argparse.ArgumentParser(
        description="Fetch historical NHL season data (2017-18 through 2020-21)"
    )
    parser.add_argument(
        "--season",
        choices=list(HISTORICAL_SEASONS.keys()),
        help="Fetch a specific season only"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Re-fetch even if data is already cached"
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Only check which seasons are cached (don't fetch)"
    )

    args = parser.parse_args()

    if args.check:
        cached, missing = check_cached_seasons()
        print("Cached seasons:")
        for season_id, info in cached:
            cache_path = _get_season_cache_path(season_id)
            print(f"  {info['name']}: {cache_path}")

        if missing:
            print("\nMissing seasons:")
            for season_id, info in missing:
                print(f"  {info['name']}: Not cached")
        return

    if args.season:
        fetch_season(args.season, force=args.force)
    else:
        fetch_all_historical(force=args.force)


if __name__ == "__main__":
    main()
