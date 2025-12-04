#!/usr/bin/env python3
"""
╔═══════════════════════════════════════════════════════════╗
║                    PUCKCAST.AI                            ║
║          Data-Driven NHL Prediction Intelligence          ║
╚═══════════════════════════════════════════════════════════╝

FULL MODEL NHL PREDICTIONS
Predict today's games using 206 advanced features

Usage:
    python predict_full.py

    # Or predict specific date:
    python predict_full.py 2024-11-15

Requirements:
    - Internet connection (NHL API)
    - Cached game data will be used if available
"""

import sys
import json
import warnings
from pathlib import Path
from datetime import datetime, timezone, date
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from nhl_prediction.nhl_api import fetch_future_games, fetch_todays_games, fetch_schedule
from nhl_prediction.pipeline import build_dataset
from nhl_prediction.model import calibrate_threshold, create_baseline_model, fit_model, tune_logreg_c
from nhl_prediction.situational_features import add_situational_features
# from nhl_prediction.player_hub.context import refresh_player_hub_context  # Module not implemented yet

# Suppress sklearn warnings
warnings.filterwarnings('ignore', category=UserWarning)

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


def apply_calibration(prob: float, calibrator) -> float:
    """Return calibrated probability using the isotonic model if available."""
    if calibrator is None:
        return float(np.clip(prob, 0.0, 1.0))
    calibrated = calibrator.predict(np.asarray([prob]))[0]
    return float(np.clip(calibrated, 0.0, 1.0))


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


# Special teams enrichment helpers -----------------------------------------

def _build_special_team_lookup(player_hub_payload):
    if not isinstance(player_hub_payload, dict):
        return {}
    special = player_hub_payload.get("specialTeams")
    if not isinstance(special, dict):
        return {}
    teams = special.get("teams")
    if not isinstance(teams, dict):
        return {}
    lookup = {}
    for key, value in teams.items():
        if isinstance(key, str):
            lookup[key.upper()] = value or {}
    return lookup


def _safe_percent(value):
    try:
        if value is None:
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number


def _build_special_split(team_stats, opponent_stats):
    if not isinstance(team_stats, dict) or not isinstance(opponent_stats, dict):
        return None
    pp = _safe_percent(team_stats.get("powerPlayPct"))
    pk = _safe_percent(opponent_stats.get("penaltyKillPct"))
    if pp is None and pk is None:
        return None
    diff = pp - pk if pp is not None and pk is not None else None
    return {
        "powerPlayPct": pp,
        "opponentPenaltyKillPct": pk,
        "diff": diff,
    }


def _attach_special_teams(game, lookup):
    if not lookup:
        return None
    home = lookup.get(str(game.get("home_team", "")).upper())
    away = lookup.get(str(game.get("away_team", "")).upper())
    if not home or not away:
        return None
    home_split = _build_special_split(home, away)
    away_split = _build_special_split(away, home)
    if not home_split and not away_split:
        return None
    return {
        "home": home_split,
        "away": away_split,
    }


def _append_special_summary(summary: str, special: dict | None, home: dict, away: dict) -> str:
    if not special:
        return summary
    best_team = None
    best_diff = None
    for team_entry, split in ((home, special.get("home")), (away, special.get("away"))):
        diff = (split or {}).get("diff")
        if diff is None:
            continue
        if best_diff is None or abs(diff) > abs(best_diff):
            best_diff = diff
            best_team = team_entry
    if best_team is None or best_diff is None or abs(best_diff) < 3:
        return summary
    tendency = "PP edge" if best_diff > 0 else "PK drag"
    abbrev = best_team.get("abbrev") or best_team.get("name") or "Team"
    return f"{summary} {abbrev} {tendency} {best_diff:+.1f} pts vs opponent special teams."


def _player_hub_meta(player_hub_payload):
    if not isinstance(player_hub_payload, dict):
        return None
    combos = player_hub_payload.get("lineCombos") or {}
    meta = {
        "season": player_hub_payload.get("season"),
        "slateDate": player_hub_payload.get("slateDate"),
        "lineCombosGeneratedAt": combos.get("generatedAt"),
        "lineCombosSlateDate": combos.get("slateDate"),
    }
    if any(meta.values()):
        return meta
    return None


def export_predictions_json(predictions, generated_at=None, player_hub_payload=None):
    """Write predictions for the web landing page in JSON format."""
    WEB_PREDICTIONS_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "generatedAt": (generated_at or datetime.now(timezone.utc).isoformat()),
        "games": [],
    }
    special_team_lookup = _build_special_team_lookup(player_hub_payload)
    hub_meta = _player_hub_meta(player_hub_payload)
    if hub_meta:
        payload["playerHubMeta"] = hub_meta

    for pred in predictions:
        home_prob_display = pred.get("home_win_prob_raw", pred.get("home_win_prob", 0.0))
        away_prob_display = pred.get("away_win_prob_raw", pred.get("away_win_prob", 0.0))
        # Fallback to complement if only one side is present
        if away_prob_display == 0.0 and "home_win_prob_raw" in pred and "away_win_prob_raw" not in pred:
            away_prob_display = 1 - home_prob_display
        if home_prob_display == 0.0 and "away_win_prob_raw" in pred and "home_win_prob_raw" not in pred:
            home_prob_display = 1 - away_prob_display

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
            "homeWinProb": round(home_prob_display, 4),
            "awayWinProb": round(away_prob_display, 4),
            "confidenceScore": round(pred.get("confidence", 0.0), 3),
            "confidenceGrade": pred.get("confidence_grade", "C"),
            "edge": round(pred.get("edge", 0.0), 3),
            "summary": pred.get("summary", ""),
            "modelFavorite": pred.get("model_favorite", "home"),
            "venue": pred.get("venue"),
            "season": str(pred.get("season")) if pred.get("season") else None,
        }
        special = _attach_special_teams(pred, special_team_lookup)
        if special:
            game_entry["specialTeams"] = special
            game_entry["summary"] = _append_special_summary(game_entry["summary"], special, game_entry["homeTeam"], game_entry["awayTeam"])
        payload["games"].append(game_entry)

    WEB_PREDICTIONS_PATH.write_text(json.dumps(payload, indent=2))
    print(f"\n🛰  Exported web payload → {WEB_PREDICTIONS_PATH}")


def derive_season_id_from_date(target: datetime) -> str:
    """Return NHL season identifier (e.g., 20242025) for the provided datetime."""
    start_year = target.year if target.month >= 7 else target.year - 1
    end_year = start_year + 1
    return f"{start_year}{end_year}"


def _filter_games_by_date(games, target_date: str) -> list[dict]:
    """Return only the games scheduled for the target date."""
    filtered = [game for game in games if game.get("gameDate") == target_date]
    return filtered


def predict_games(date=None, num_games=20):
    """
    Predict NHL games using full model with all features.
    
    Args:
        date: Date string 'YYYY-MM-DD' or None for today
        num_games: Number of games to predict (default 20)
    """
    
    print("━"*80)
    print("🏒 PUCKCAST.AI - NHL PREDICTIONS")
    print("   Data-Driven Intelligence for Today's Games")
    print("━"*80)
    
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
    
    # Step 2: Build dataset
    seasons = recent_seasons(target_dt, count=3)
    print("\n2️⃣  Building dataset with native artifacts...")
    print(f"   (Loading {len(seasons)} season(s): {', '.join(seasons)})")

    dataset = build_dataset(seasons)

    print(f"   ✅ {len(dataset.games)} games loaded")
    print(f"   ✅ {dataset.features.shape[1]} baseline features engineered")

    # Add V7.3 situational features
    games_with_situational = add_situational_features(dataset.games)
    v7_3_features = ['fatigue_index_diff', 'third_period_trailing_perf_diff',
                     'travel_distance_diff', 'divisional_matchup',
                     'post_break_game_home', 'post_break_game_away', 'post_break_game_diff']
    available_v7_3 = [f for f in v7_3_features if f in games_with_situational.columns]

    # Combine baseline + situational features
    features_v7_3 = pd.concat([dataset.features, games_with_situational[available_v7_3]], axis=1)
    print(f"   ✅ {len(available_v7_3)} V7.3 situational features added")
    print(f"   ✅ Total: {features_v7_3.shape[1]} features (V7.3 Production Model)")

    # Step 3: Train calibrated model using only past games
    print("\n3️⃣  Training calibrated logistic regression model...")
    predict_date = target_dt
    cutoff = pd.Timestamp(predict_date.date())
    game_dates = pd.to_datetime(dataset.games["gameDate"])
    eligible_mask = game_dates < cutoff
    
    if not eligible_mask.any():
        print("   ❌ No historical games available before this date.")
        return []
    
    eligible_games = dataset.games.loc[eligible_mask].copy()
    eligible_features = features_v7_3.loc[eligible_mask].copy()
    eligible_target = dataset.target.loc[eligible_mask].copy()
    train_seasons = sorted(eligible_games["seasonId"].unique().tolist())
    
    candidate_cs = [0.005, 0.01, 0.02, 0.03, 0.05, 0.1, 0.3, 0.5, 1.0]
    best_c = tune_logreg_c(candidate_cs, eligible_features, eligible_target, eligible_games, train_seasons)
    threshold, val_acc, calibrator = calibrate_threshold(best_c, eligible_features, eligible_target, eligible_games, train_seasons)
    
    training_mask = pd.Series(True, index=eligible_features.index)
    model = create_baseline_model(C=best_c)
    model = fit_model(model, eligible_features, eligible_target, training_mask)
    
    print(f"   ✅ Trained on {training_mask.sum():,} historical games | seasons: {', '.join(map(str, train_seasons))}")
    print(f"   ✅ Selected logistic regression C={best_c:.3f}")
    if val_acc is not None:
        print(f"   ✅ Validation threshold {threshold:.3f} (accuracy {val_acc:.3f})")
    else:
        print("   ℹ️  Not enough seasons for validation; using default 0.500 threshold")
    if calibrator is not None:
        print("   ✅ Applied isotonic probability calibration")
    
    # Step 4: Predict
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

        home_features = features_v7_3.loc[home_idx]
        away_features = features_v7_3.loc[away_idx]
        
        # Create matchup features (average of recent performance)
        matchup_features = (home_features + away_features) / 2
        matchup_features = matchup_features.reindex(feature_columns, fill_value=0.0)
        
        # Predict with calibrated model
        prob_home_raw = model.predict_proba(matchup_features.values.reshape(1, -1))[0][1]
        prob_home_calibrated = apply_calibration(prob_home_raw, calibrator)
        prob_home_display = prob_home_raw  # Show raw probabilities to avoid calibration plateaus
        prob_away_raw = 1 - prob_home_raw
        prob_away_calibrated = 1 - prob_home_calibrated

        start_time_utc_iso, start_time_et = format_start_times(game.get('startTimeUTC', ''))
        # Use raw probabilities for display and edge/grade to avoid calibration plateaus
        edge = prob_home_display - 0.5
        confidence_score = abs(edge) * 2  # 0-1 scale
        confidence_grade = grade_from_edge(edge)
        model_favorite = 'home' if prob_home_display >= prob_away_raw else 'away'
        summary = build_summary(
            game.get('homeTeamName', home_abbrev),
            game.get('awayTeamName', away_abbrev),
            prob_home_display,
            confidence_grade,
        )
        
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
            # Display raw probabilities for UI while keeping calibrated for decisioning
            'home_win_prob': prob_home_display,
            'away_win_prob': prob_away_raw,
            'home_win_prob_raw': prob_home_raw,
            'away_win_prob_raw': prob_away_raw,
            'home_win_prob_calibrated': prob_home_calibrated,
            'away_win_prob_calibrated': prob_away_calibrated,
            'edge': edge,
            'predicted_winner': home_abbrev if prob_home_display > 0.5 else away_abbrev,
            'model_favorite': model_favorite,
            'confidence': confidence_score,
            'confidence_grade': confidence_grade,
            'summary': summary
        })
        
        # Display prediction
        print(f"\n{i}. {away_abbrev} @ {home_abbrev}")
        print(f"   Home Win (raw): {prob_home_display:.1%}  |  Away Win (raw): {prob_away_raw:.1%}")
        
        # Classify prediction strength
        confidence_pct = confidence_score * 100

        if prob_home_display > 0.70:
            print(f"   ✅ Prediction: {home_abbrev} STRONG FAVORITE")
        elif prob_home_display < 0.30:
            print(f"   ✅ Prediction: {away_abbrev} STRONG FAVORITE")
        elif 0.45 <= prob_home_display <= 0.55:
            print(f"   ⚖️  Prediction: TOSS-UP (too close to call)")
        else:
            favorite = home_abbrev if prob_home_display > 0.5 else away_abbrev
            print(f"   📊 Prediction: {favorite} ({confidence_pct:.0f}% confidence)")
    
    # Summary
    print("\n" + "="*80)
    print(f"✅ PREDICTIONS COMPLETE")
    print(f"   Total Games: {len(predictions)}")
    print(f"   Model: Logistic Regression (C={best_c:.3f}) with {eligible_features.shape[1]} features")
    print(f"   Training: {training_mask.sum():,} games from seasons {', '.join(map(str, train_seasons))}")
    if calibrator is not None:
        print("   Calibration: Isotonic regression on validation season")
    else:
        print("   Calibration: Not available (insufficient validation split)")
    print("="*80)
    
    return predictions


def main():
    """Main entry point."""
    
    # Parse command line args - simple: just date (optional)
    # Usage: python predict_full.py [YYYY-MM-DD]
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
        predictions = predict_games(date=date, num_games=20)

        # Save to CSV
        if predictions:
            df = pd.DataFrame(predictions)
            filename = f"predictions_{date or datetime.now().strftime('%Y-%m-%d')}.csv"
            df.to_csv(filename, index=False)
            print(f"\n💾 Saved predictions to: {filename}")

        target_dt = datetime.strptime(date, "%Y-%m-%d") if date else datetime.now()
        player_hub_payload = None
        # Player Hub module not implemented yet - skip context refresh
        # try:
        #     season_id = derive_season_id_from_date(target_dt)
        #     player_hub_payload = refresh_player_hub_context(target_dt.date(), season_id)
        #     print("🗂  Updated Player Hub context payload.")
        # except Exception as refresh_error:
        #     print(f"⚠️  Failed to refresh Player Hub context: {refresh_error}")
        export_predictions_json(
            predictions,
            generated_at=datetime.now(timezone.utc).isoformat(),
            player_hub_payload=player_hub_payload,
        )

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
