"""Fetch 2024-25 season data from NHL API."""

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

from nhl_prediction.native_ingest import load_native_game_logs

def main():
    print("="*60)
    print("FETCHING 2024-25 NHL SEASON DATA")
    print("="*60)
    print()
    print("This will fetch all completed games from the 2024-25 season.")
    print("The data will be cached for future use.")
    print()
    print("Expected: ~1,312 games (complete season)")
    print("Estimated time: 20-40 minutes (with rate limiting)")
    print()
    print("-"*60)

    # Fetch just 2024-25 season
    df = load_native_game_logs(["20242025"])

    print()
    print("="*60)
    print("FETCH COMPLETE!")
    print("="*60)
    print(f"Total team-games fetched: {len(df)}")
    print(f"Unique games: {df['gameId'].nunique() if 'gameId' in df.columns else 'N/A'}")

    if not df.empty:
        print(f"\nDate range: {df['gameDate'].min()} to {df['gameDate'].max()}")
        print(f"\nData saved to: data/cache/native_logs_20242025.parquet")
    else:
        print("\nWARNING: No data was fetched!")

if __name__ == "__main__":
    main()
