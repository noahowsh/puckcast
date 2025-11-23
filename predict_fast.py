#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════╗
║                    PUCKCAST.AI                            ║
║          Fast NHL Prediction Intelligence                 ║
╚═══════════════════════════════════════════════════════════╝

FAST NHL PREDICTIONS using pre-trained model
Predict today's games in under 2 minutes using the saved model.

Usage:
    python predict_fast.py

    # Or predict specific date:
    python predict_fast.py 2024-11-15

Requirements:
    - Internet connection (NHL API)
    - Pre-trained model: model_v6_6seasons.pkl
"""

import sys
import json
import pickle
import warnings
from pathlib import Path
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from nhl_prediction.nhl_api import fetch_future_games, fetch_todays_games, fetch_schedule
from nhl_prediction.pipeline import build_dataset

# Suppress sklearn warnings
warnings.filterwarnings('ignore', category=UserWarning)

MODEL_PATH = Path(__file__).parent / "model_v6_6seasons.pkl"
WEB_PREDICTIONS_PATH = Path(__file__).parent / "web" / "src" / "data" / "todaysPredictions.json"
ET_ZONE = ZoneInfo("America/New_York")

def recent_seasons(anchor: datetime | date | None = None, count: int = 3) -> list[str]:
    """Return the most recent NHL season IDs ending at the anchor date."""
    if anchor is None:
        anchor_date = datetime.utcnow().date()
    elif isinstance(anchor, datetime):
        anchor_date = anchor.date()
    else:
        anchor_date = anchor

    start_year = anchor_date.year if anchor_date.month >= 7 else anchor_date.year - 1
    seasons = []
    for offset in range(count):
        year = start_year - offset
        seasons.append(f"{year}{year + 1}")
    return seasons

def format_start_times(start_time_utc: str):
    """Return ISO + human-readable ET string for a UTC start time."""
    if not start_time_utc:
        return None, None

    try:
        dt_utc = datetime.fromisoformat(start_time_utc.replace("Z", "+00:00"))
    except ValueError:
        return None, None

    dt_et = dt_utc.astimezone(ET_ZONE)
    display = dt_et.strftime("%I:%M %p").lstrip("0")
    return dt_utc.isoformat(), f"{display} ET"


def grade_from_edge(edge_value: float) -> str:
    """Map edge (probability delta) to letter grades used on the site."""
    edge_pts = abs(edge_value) * 100
    if edge_pts >= 20:
        return "A+"
    if edge_pts >= 17:
        return "A"
    if edge_pts >= 14:
        return "A-"
    if edge_pts >= 10:
        return "B+"
    if edge_pts >= 7:
        return "B"
    if edge_pts >= 4:
        return "B-"
    if edge_pts >= 2:
        return "C+"
    return "C"


def build_summary(home_team: str, away_team: str, prob_home: float, confidence_grade: str) -> str:
    favorite = home_team if prob_home >= 0.5 else away_team
    favorite_prob = prob_home if favorite == home_team else 1 - prob_home
    edge_pct = abs(prob_home - 0.5) * 100
    direction = "home" if favorite == home_team else "road"
    article = "an" if confidence_grade.startswith("A") else "a"
    return (
        f"{favorite} project at {favorite_prob:.0%} as the {direction} lean — "
        f"{article} {confidence_grade}-tier edge worth {edge_pct:.1f} pts over a coin flip."
    )


def export_predictions_json(predictions, generated_at=None):
    """Write predictions for the web landing page in JSON format."""
    WEB_PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAt": (generated_at or datetime.now(timezone.utc).isoformat()),
        "games": [],
    }

    for pred in predictions:
        game_entry = {
            "id": str(pred.get("game_id", pred.get("game_num"))),
            "gameDate": pred.get("date"),
            "startTimeEt": pred.get("start_time_et"),
            "startTimeUtc": pred.get("start_time_utc"),
            "homeTeam": {
                "name": pred.get("home_team_name", pred.get("home_team")),
                "abbrev": pred.get("home_team"),
            },
            "awayTeam": {
                "name": pred.get("away_team_name", pred.get("away_team")),
                "abbrev": pred.get("away_team"),
            },
            "homeWinProb": round(pred.get("home_win_prob", 0.0), 4),
            "awayWinProb": round(pred.get("away_win_prob", 0.0), 4),
            "confidenceScore": round(pred.get("confidence", 0.0), 3),
            "confidenceGrade": pred.get("confidence_grade", "C"),
            "edge": round(pred.get("edge", 0.0), 3),
            "summary": pred.get("summary", ""),
            "modelFavorite": pred.get("model_favorite", "home"),
            "venue": pred.get("venue"),
            "season": str(pred.get("season")) if pred.get("season") else None,
        }
        payload["games"].append(game_entry)

    WEB_PREDICTIONS_PATH.write_text(json.dumps(payload, indent=2))
    print(f"\n🛰  Exported web payload → {WEB_PREDICTIONS_PATH}")


def _filter_games_by_date(games, target_date: str) -> list[dict]:
    """Return only the games scheduled for the target date."""
    filtered = [game for game in games if game.get("gameDate") == target_date]
    return filtered


def predict_games_fast(date=None, num_games=20):
    """
    Predict NHL games using pre-trained model (FAST VERSION).

    Args:
        date: Date string 'YYYY-MM-DD' or None for today
        num_games: Number of games to predict (default 20)
    """

    print("━"*80)
    print("🏒 PUCKCAST.AI - FAST NHL PREDICTIONS")
    print("   Using Pre-Trained Model for Speed")
    print("━"*80)

    # Step 0: Load pre-trained model
    print(f"\n0️⃣  Loading pre-trained model from {MODEL_PATH}...")
    if not MODEL_PATH.exists():
        print(f"   ❌ Model file not found: {MODEL_PATH}")
        print("   Run 'python train_optimal.py' to create the model first.")
        return []

    with open(MODEL_PATH, "rb") as f:
        model = pickle.load(f)
    print(f"   ✅ Model loaded: {type(model).__name__}")

    # Get date
    if date is None:
        target_dt = datetime.now()
    else:
        target_dt = datetime.strptime(date, '%Y-%m-%d')
    date_str = target_dt.strftime('%Y-%m-%d')
    date_display = target_dt.strftime('%A, %B %d, %Y')

    print(f"\n📅 Date: {date_display}")

    # Step 1: Fetch games
    print(f"\n1️⃣  Fetching games for {date_str}...")

    if date is None:
        games = fetch_todays_games()
    else:
        games = fetch_future_games(date_str)
    if not games and target_dt.date() < datetime.now().date():
        print("   ⚠️  No future games detected — falling back to historical schedule for backfill.")
        games = fetch_schedule(date_str)
    if not games:
        print(f"   ℹ️  No games scheduled for {date_str}")
        export_predictions_json([], generated_at=datetime.now(timezone.utc).isoformat())
        return []

    filtered_games = _filter_games_by_date(games, date_str)
    filtered_count = len(filtered_games)
    print(f"   ✅ Found {filtered_count} game(s) for {date_str}")
    if filtered_count == 0:
        print("   ℹ️  Using the full schedule because no games matched the target date.")
        games_for_model = games
    else:
        if filtered_count != len(games):
            print(f"   ℹ️  Filtered down from {len(games)} scheduled game(s).")
        games_for_model = filtered_games

    # Step 2: Build dataset (only for feature extraction)
    # HARDCODED: Use real seasons with LOCAL raw data (not future seasons)
    # These seasons have data in data/raw/web_v1/ that will be cached on first run
    seasons = ["20232024", "20212022"]  # Real seasons with local raw data
    print("\n2️⃣  Loading recent game data for feature extraction...")
    print(f"   (Loading {len(seasons)} season(s): {', '.join(seasons)})")

    try:
        dataset = build_dataset(seasons)
        print(f"   ✅ {len(dataset.games)} games loaded")
        print(f"   ✅ {dataset.features.shape[1]} features available")
    except Exception as e:
        print(f"   ❌ Failed to load dataset: {e}")
        print(f"   ℹ️  Exporting empty predictions due to data loading failure")
        export_predictions_json([], generated_at=datetime.now(timezone.utc).isoformat())
        return []

    # Step 3: Use only recent games for feature extraction
    print("\n3️⃣  Extracting features from recent games...")
    predict_date = target_dt
    cutoff = pd.Timestamp(predict_date.date())
    game_dates = pd.to_datetime(dataset.games["gameDate"])
    eligible_mask = game_dates < cutoff

    if not eligible_mask.any():
        print("   ❌ No historical games available before this date.")
        return []

    eligible_games = dataset.games.loc[eligible_mask].copy()
    eligible_features = dataset.features.loc[eligible_mask].copy()
    train_seasons = sorted(eligible_games["seasonId"].unique().tolist())

    print(f"   ✅ Using {eligible_mask.sum():,} recent games | seasons: {', '.join(map(str, train_seasons))}")

    # Step 4: Predict (FAST - no training!)
    print(f"\n4️⃣  Generating predictions for {min(num_games, len(games_for_model))} games...")

    print("\n" + "="*80)
    print("PREDICTIONS")
    print("="*80)

    predictions = []
    eligible_games["seasonId_str"] = eligible_games["seasonId"].astype(str)
    feature_columns = eligible_features.columns

    for i, game in enumerate(games_for_model[:num_games], 1):
        home_id = game['homeTeamId']
        away_id = game['awayTeamId']
        home_abbrev = game['homeTeamAbbrev']
        away_abbrev = game['awayTeamAbbrev']
        season_id = str(game.get("season") or train_seasons[-1])

        # Find most recent games for each team
        home_recent = eligible_games[
            (eligible_games['teamId_home'] == home_id) &
            (eligible_games['seasonId_str'] == season_id)
        ].tail(1)

        away_recent = eligible_games[
            (eligible_games['teamId_away'] == away_id) &
            (eligible_games['seasonId_str'] == season_id)
        ].tail(1)

        if len(home_recent) == 0 or len(away_recent) == 0:
            print(f"\n{i}. {away_abbrev} @ {home_abbrev}")
            print(f"   ⚠️  Insufficient data (team hasn't played this season)")
            continue

        # Get feature vectors
        home_idx = home_recent.index[0]
        away_idx = away_recent.index[0]

        home_features = dataset.features.loc[home_idx]
        away_features = dataset.features.loc[away_idx]

        # Create matchup features (average of recent performance)
        matchup_features = (home_features + away_features) / 2
        matchup_features = matchup_features.reindex(feature_columns, fill_value=0.0)

        # Predict with pre-trained model (FAST!)
        prob_home = model.predict_proba(matchup_features.values.reshape(1, -1))[0][1]
        prob_home = float(np.clip(prob_home, 0.0, 1.0))
        prob_away = 1 - prob_home

        start_time_utc_iso, start_time_et = format_start_times(game.get('startTimeUTC', ''))
        edge = prob_home - 0.5
        confidence_score = abs(edge) * 2  # 0-1 scale
        confidence_grade = grade_from_edge(edge)
        model_favorite = 'home' if prob_home >= prob_away else 'away'
        summary = build_summary(game.get('homeTeamName', home_abbrev), game.get('awayTeamName', away_abbrev), prob_home, confidence_grade)

        # Store prediction
        predictions.append({
            'game_num': i,
            'game_id': game.get('gameId'),
            'date': game.get('gameDate', date_str),
            'season': game.get('season'),
            'venue': game.get('venue'),
            'game_state': game.get('gameState'),
            'start_time_utc': start_time_utc_iso,
            'start_time_et': start_time_et,
            'away_team': away_abbrev,
            'away_team_name': game.get('awayTeamName', away_abbrev),
            'home_team': home_abbrev,
            'home_team_name': game.get('homeTeamName', home_abbrev),
            'home_win_prob': prob_home,
            'away_win_prob': prob_away,
            'edge': edge,
            'predicted_winner': home_abbrev if prob_home > 0.5 else away_abbrev,
            'model_favorite': model_favorite,
            'confidence': confidence_score,
            'confidence_grade': confidence_grade,
            'summary': summary
        })

        # Display prediction
        print(f"\n{i}. {away_abbrev} @ {home_abbrev}")
        print(f"   Home Win: {prob_home:.1%}  |  Away Win: {prob_away:.1%}")

        # Classify prediction strength
        confidence_pct = confidence_score * 100

        if prob_home > 0.70:
            print(f"   ✅ Prediction: {home_abbrev} STRONG FAVORITE")
        elif prob_home < 0.30:
            print(f"   ✅ Prediction: {away_abbrev} STRONG FAVORITE")
        elif 0.45 <= prob_home <= 0.55:
            print(f"   ⚖️  Prediction: TOSS-UP (too close to call)")
        else:
            favorite = home_abbrev if prob_home > 0.5 else away_abbrev
            print(f"   📊 Prediction: {favorite} ({confidence_pct:.0f}% confidence)")

    # Summary
    print("\n" + "="*80)
    print(f"✅ FAST PREDICTIONS COMPLETE")
    print(f"   Total Games: {len(predictions)}")
    print(f"   Model: Pre-trained {type(model).__name__} (no retraining needed)")
    print(f"   Features: {len(feature_columns)} features from recent games")
    print("="*80)

    return predictions


def main():
    """Main entry point."""

    # Parse command line args - simple: just date (optional)
    # Usage: python predict_fast.py [YYYY-MM-DD]
    if len(sys.argv) > 1:
        date_arg = sys.argv[1]
        # Skip if it's a flag like --date
        if date_arg.startswith('--'):
            date = None
            print("\nPredicting today's games...")
        else:
            date = date_arg
            print(f"\nPredicting games for: {date}")
    else:
        date = None
        print("\nPredicting today's games...")

    try:
        predictions = predict_games_fast(date=date, num_games=20)

        # Save to CSV
        if predictions:
            df = pd.DataFrame(predictions)
            filename = f"predictions_{date or datetime.now().strftime('%Y-%m-%d')}.csv"
            df.to_csv(filename, index=False)
            print(f"\n💾 Saved predictions to: {filename}")

        export_predictions_json(
            predictions,
            generated_at=datetime.now(timezone.utc).isoformat(),
        )

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
