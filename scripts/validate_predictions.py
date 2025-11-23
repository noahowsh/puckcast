#!/usr/bin/env python3
"""
Lightweight validation to catch placeholder prediction payloads before publishing.

Checks:
- File exists and is valid JSON
- At least one game present
- Home/away win probs are finite, in [0, 1]
- Home + away prob sums to ~1
- Not all games are perfectly 50/50 (signals placeholder)
"""
from __future__ import annotations

import json
import math
import sys
from pathlib import Path


def fail(message: str) -> None:
    print(f"❌ {message}")
    sys.exit(1)


def main() -> None:
    path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("web/src/data/todaysPredictions.json")
    if not path.exists():
        fail(f"Predictions file not found: {path}")

    try:
        payload = json.loads(path.read_text())
    except Exception as exc:  # pragma: no cover - defensive
        fail(f"Unable to parse JSON from {path}: {exc}")

    games = payload.get("games") or []
    if not games:
        fail("Predictions payload has no games.")

    all_coin_flip = True
    for g in games:
        home = g.get("homeWinProb")
        away = g.get("awayWinProb")
        if home is None or away is None:
            fail(f"Missing probabilities for game id {g.get('id')}")
        if not (isinstance(home, (int, float)) and isinstance(away, (int, float))):
            fail(f"Non-numeric probabilities for game id {g.get('id')}")
        if any(math.isnan(x) or math.isinf(x) for x in (home, away)):
            fail(f"NaN/inf probabilities for game id {g.get('id')}")
        if not (0.0 <= home <= 1.0 and 0.0 <= away <= 1.0):
            fail(f"Probabilities out of range for game id {g.get('id')}: {home}, {away}")
        if abs((home + away) - 1.0) > 0.02:
            fail(f"Probabilities do not sum to 1 for game id {g.get('id')}: {home} + {away} = {home + away}")
        if abs(home - 0.5) > 1e-6:
            all_coin_flip = False

    if all_coin_flip:
        fail("All games are 50/50 — likely placeholder output.")

    print(f"✅ Predictions validated: {len(games)} games OK")


if __name__ == "__main__":
    main()
