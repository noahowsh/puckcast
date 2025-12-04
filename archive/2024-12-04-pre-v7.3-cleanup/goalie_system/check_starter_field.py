#!/usr/bin/env python3
"""Quick script to verify NHL API has starter field in boxscores."""

import json
from pathlib import Path

cache_dir = Path("data/raw/web_v1/2023")
boxscores = list(cache_dir.glob("*boxscore.json"))[:10]

print(f"Checking {len(boxscores)} boxscores for starter field...\n")

games_with_starter_field = 0
total_goalies_checked = 0

for boxscore_path in boxscores:
    with open(boxscore_path) as f:
        data = json.load(f)

    game_id = boxscore_path.stem.replace("_boxscore", "")
    print(f"Game {game_id}:")

    for team_key in ["awayTeam", "homeTeam"]:
        goalies = data.get("playerByGameStats", {}).get(team_key, {}).get("goalies", [])
        for goalie in goalies:
            name = goalie.get("name", {}).get("default", "Unknown")
            starter = goalie.get("starter", "MISSING")
            toi = goalie.get("toi", "N/A")

            total_goalies_checked += 1
            if starter != "MISSING":
                games_with_starter_field += 1

            print(f"  {name}: starter={starter}, toi={toi}")

    print()

print(f"\nSummary:")
print(f"Total goalies checked: {total_goalies_checked}")
print(f"Goalies with 'starter' field: {games_with_starter_field}")
print(f"Coverage: {games_with_starter_field/total_goalies_checked*100:.1f}%")
