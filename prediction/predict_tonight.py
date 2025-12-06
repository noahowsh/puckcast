#!/usr/bin/env python3
"""
Predict ONLY tonight's NHL games (games starting today in ET timezone).

Usage:
    python predict_tonight.py
    
Or specify a date:
    python predict_tonight.py 2025-11-10
"""

import sys
from pathlib import Path
from datetime import datetime, timezone
import pytz
import pandas as pd

# Add src to path
_PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT_ROOT))

from src.nhl_prediction.nhl_api import fetch_future_games


def get_tonights_games(date_str: str = None):
    """Get only games starting TODAY (before midnight local time)."""
    
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
    
    # Fetch all future games for this date
    all_future = fetch_future_games(date_str)
    
    # Filter to games starting TODAY in ET timezone
    et_tz = pytz.timezone('US/Eastern')
    target_date = datetime.strptime(date_str, '%Y-%m-%d').replace(tzinfo=et_tz).date()
    
    tonight_games = []
    for game in all_future:
        # Parse UTC time and convert to ET
        start_utc = datetime.strptime(game['startTimeUTC'], '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=timezone.utc)
        start_et = start_utc.astimezone(et_tz)
        
        # Only include if starts on the target date
        if start_et.date() == target_date:
            game['start_time_et'] = start_et.strftime('%I:%M %p ET')
            tonight_games.append(game)
    
    return tonight_games


def main(date_str: str = None):
    if date_str is None:
        date_str = datetime.now().strftime('%Y-%m-%d')
        date_display = datetime.now().strftime('%A, %B %d, %Y')
    else:
        date_display = datetime.strptime(date_str, '%Y-%m-%d').strftime('%A, %B %d, %Y')
    
    print('='*80)
    print('🏒 TONIGHT\'S NHL GAME PREDICTIONS')
    print('='*80)
    print(f'\n📅 {date_display}\n')
    
    # Step 1: Get tonight's games
    print('1️⃣  Fetching tonight\'s games from NHL API...')
    tonight_games = get_tonights_games(date_str)
    
    if not tonight_games:
        print(f'   ℹ️  No games scheduled for tonight ({date_str})')
        return
    
    print(f'   ✅ Found {len(tonight_games)} games tonight:\n')
    for i, game in enumerate(tonight_games, 1):
        print(f'      {i}. {game["awayTeamAbbrev"]} @ {game["homeTeamAbbrev"]} ({game["start_time_et"]})')
    
    # Step 2: Load pre-generated predictions
    print('\n2️⃣  Loading predictions...')
    
    predictions_file = f'predictions_{date_str}.csv'
    
    try:
        preds = pd.read_csv(predictions_file)
        print(f'   ✅ Loaded predictions from {predictions_file}')
    except FileNotFoundError:
        print(f'\n   ⚠️  Predictions file not found: {predictions_file}')
        print(f'\n   Please run this first to generate predictions:')
        print(f'   python predict_full.py {date_str}')
        return
    
    # Step 3: Display predictions for tonight's games only
    print('\n' + '='*80)
    print('PREDICTIONS')
    print('='*80)
    
    for i, game_info in enumerate(tonight_games, 1):
        away = game_info['awayTeamAbbrev']
        home = game_info['homeTeamAbbrev']
        time = game_info['start_time_et']
        
        # Find prediction
        game_pred = preds[
            (preds['away_team'] == away) & 
            (preds['home_team'] == home)
        ]
        
        if game_pred.empty:
            print(f'\n{i}. {away} @ {home} ({time})')
            print(f'   ⚠️  Prediction not found')
            continue
        
        row = game_pred.iloc[0]
        home_prob = row['home_win_prob']
        away_prob = row['away_win_prob']
        winner = row['predicted_winner']
        conf = row['confidence']
        
        print(f'\n{i}. {away} @ {home} ({time})')
        print(f'   Home Win: {home_prob:.1%}  |  Away Win: {away_prob:.1%}')
        
        # Cleaner prediction display
        if conf < 0.05:
            print(f'   ⚖️  Prediction: TOSS-UP (too close to call)')
        elif conf > 0.20:
            print(f'   ✅ Prediction: {winner} STRONG ({conf:.0%} edge)')
        else:
            print(f'   📊 Prediction: {winner} (slight {conf:.0%} edge)')
    
    print('\n' + '='*80)
    print('✅ Model: V8.0 (improved Elo + 35 curated features)')
    print('✅ Trained on rolling 4-season window with season carryover')
    print('='*80)


if __name__ == '__main__':
    date_arg = sys.argv[1] if len(sys.argv) > 1 else None
    main(date_arg)
