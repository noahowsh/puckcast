#!/usr/bin/env python3
"""
Matchup Overview Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing a detailed
breakdown of a specific game matchup with stats and predictions.
Uses 2x supersampling for crisp output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional

from PIL import Image, ImageDraw

GRAPHICS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GRAPHICS_DIR))

from puckcast_brand import (
    PuckcastColors,
    hex_to_rgb,
    get_confidence_color_rgb,
)
from image_utils import (
    create_puckcast_background,
    draw_footer,
    draw_rounded_rect,
    get_logo,
    get_font,
    save_high_quality,
    S,
    RENDER_SIZE,
)

REPO_ROOT = GRAPHICS_DIR.parents[0]
PREDICTIONS_PATH = REPO_ROOT / "web" / "src" / "data" / "todaysPredictions.json"
STANDINGS_PATH = REPO_ROOT / "web" / "src" / "data" / "currentStandings.json"
GOALIE_PATH = REPO_ROOT / "web" / "src" / "data" / "goaliePulse.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_data() -> tuple[Dict, Dict, Dict]:
    """Load all required data."""
    predictions = {}
    standings = {}
    goalies = {}

    if PREDICTIONS_PATH.exists():
        predictions = json.loads(PREDICTIONS_PATH.read_text())
    if STANDINGS_PATH.exists():
        standings_data = json.loads(STANDINGS_PATH.read_text())
        # Index by team abbrev
        for team in standings_data.get("teams", []):
            standings[team["abbrev"]] = team
    if GOALIE_PATH.exists():
        goalie_data = json.loads(GOALIE_PATH.read_text())
        for g in goalie_data.get("goalies", []):
            if g["team"] not in goalies:
                goalies[g["team"]] = g

    return predictions, standings, goalies


def draw_team_side(
    img: Image.Image,
    draw: ImageDraw.Draw,
    team_abbrev: str,
    team_name: str,
    win_prob: float,
    standings: Dict,
    goalie: Optional[Dict],
    x_center: int,
    y_start: int,
    is_favorite: bool,
) -> None:
    """Draw one team's side of the matchup."""
    team_stats = standings.get(team_abbrev, {})

    # Team logo (large)
    logo_size = S(120)
    logo = get_logo(team_abbrev, logo_size)
    logo_x = x_center - logo_size // 2
    logo_y = y_start
    img.paste(logo, (logo_x, logo_y), logo)

    # Team abbreviation
    abbrev_font = get_font(S(32), bold=True)
    abbrev_bbox = draw.textbbox((0, 0), team_abbrev, font=abbrev_font)
    abbrev_w = abbrev_bbox[2] - abbrev_bbox[0]
    draw.text((x_center - abbrev_w // 2, logo_y + logo_size + S(8)), team_abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)

    # Win probability (large, colored)
    prob_y = logo_y + logo_size + S(48)
    prob_text = f"{win_prob * 100:.0f}%"
    prob_font = get_font(S(48), bold=True)
    prob_bbox = draw.textbbox((0, 0), prob_text, font=prob_font)
    prob_w = prob_bbox[2] - prob_bbox[0]
    prob_color = hex_to_rgb(PuckcastColors.AQUA) if is_favorite else hex_to_rgb(PuckcastColors.TEXT_SECONDARY)
    draw.text((x_center - prob_w // 2, prob_y), prob_text, fill=prob_color, font=prob_font)

    # "WIN PROB" label
    label_font = get_font(S(12), bold=True)
    label_text = "WIN PROB"
    label_bbox = draw.textbbox((0, 0), label_text, font=label_font)
    label_w = label_bbox[2] - label_bbox[0]
    draw.text((x_center - label_w // 2, prob_y + S(52)), label_text, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=label_font)

    # Team stats section
    stats_y = prob_y + S(90)
    stat_font = get_font(S(14), bold=False)
    stat_value_font = get_font(S(16), bold=True)
    line_height = S(28)

    record = f"{team_stats.get('wins', 0)}-{team_stats.get('losses', 0)}-{team_stats.get('ot', 0)}"
    points = team_stats.get('points', 0)
    gf = team_stats.get('goalsForPerGame', 0)
    ga = team_stats.get('goalsAgainstPerGame', 0)
    pp = team_stats.get('powerPlayPct', 0) * 100
    pk = team_stats.get('penaltyKillPct', 0) * 100

    stats = [
        ("Record", record),
        ("Points", str(points)),
        ("GF/G", f"{gf:.2f}"),
        ("GA/G", f"{ga:.2f}"),
        ("PP%", f"{pp:.1f}%"),
        ("PK%", f"{pk:.1f}%"),
    ]

    for i, (label, value) in enumerate(stats):
        y = stats_y + i * line_height
        # Label
        draw.text((x_center - S(70), y), label, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=stat_font)
        # Value (right aligned)
        val_bbox = draw.textbbox((0, 0), value, font=stat_value_font)
        val_w = val_bbox[2] - val_bbox[0]
        draw.text((x_center + S(70) - val_w, y), value, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=stat_value_font)

    # Goalie info
    if goalie:
        goalie_y = stats_y + len(stats) * line_height + S(20)
        draw.line([(x_center - S(60), goalie_y), (x_center + S(60), goalie_y)], fill=(255, 255, 255, 30), width=1)

        goalie_y += S(12)
        goalie_name = goalie.get("name", "TBD").split()[-1]  # Last name only
        goalie_sv = goalie.get("savePct", 0)

        name_font = get_font(S(14), bold=True)
        draw.text((x_center - S(60), goalie_y), "IN NET", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=get_font(S(10), bold=True))
        draw.text((x_center - S(60), goalie_y + S(16)), goalie_name, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=name_font)
        draw.text((x_center - S(60), goalie_y + S(36)), f".{int(goalie_sv * 1000)} SV%", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=get_font(S(12), bold=False))


def generate_matchup_overview(game: Dict, standings: Dict, goalies: Dict) -> Image.Image:
    """Generate a matchup overview graphic."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(48)

    home = game.get("homeTeam", {})
    away = game.get("awayTeam", {})
    home_abbrev = home.get("abbrev", "???")
    away_abbrev = away.get("abbrev", "???")
    home_prob = game.get("homeWinProb", 0.5)
    away_prob = game.get("awayWinProb", 0.5)
    confidence = game.get("confidenceGrade", "C")
    start_time = game.get("startTimeEt", "TBD")
    venue = game.get("venue", "")

    # Header
    title_font = get_font(S(18), bold=True)
    draw.text((margin, S(28)), "MATCHUP BREAKDOWN", fill=hex_to_rgb(PuckcastColors.AQUA), font=title_font)

    # Game info
    time_font = get_font(S(14), bold=False)
    draw.text((margin, S(52)), f"{start_time}  •  {venue}", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=time_font)

    # Main matchup display
    matchup_y = S(90)
    quarter_width = RENDER_SIZE // 4

    # Away team (left side)
    draw_team_side(
        img, draw,
        away_abbrev, away.get("name", ""),
        away_prob, standings, goalies.get(away_abbrev),
        quarter_width, matchup_y,
        is_favorite=(away_prob > home_prob)
    )

    # VS in center
    vs_font = get_font(S(24), bold=True)
    vs_y = matchup_y + S(60)
    draw.text((RENDER_SIZE // 2 - S(12), vs_y), "@", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=vs_font)

    # Home team (right side)
    draw_team_side(
        img, draw,
        home_abbrev, home.get("name", ""),
        home_prob, standings, goalies.get(home_abbrev),
        quarter_width * 3, matchup_y,
        is_favorite=(home_prob > away_prob)
    )

    # Center divider line
    draw.line([(RENDER_SIZE // 2, matchup_y + S(20)), (RENDER_SIZE // 2, RENDER_SIZE - S(180))], fill=(255, 255, 255, 20), width=1)

    # Bottom section - Model prediction
    pred_y = RENDER_SIZE - S(160)
    draw.line([(margin, pred_y - S(16)), (RENDER_SIZE - margin, pred_y - S(16))], fill=(255, 255, 255, 30), width=1)

    # Confidence grade badge
    grade_color = get_confidence_color_rgb(confidence)
    badge_size = S(50)
    badge_x = margin
    badge_y = pred_y

    draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], fill=grade_color)
    grade_font = get_font(S(28), bold=True)
    grade_bbox = draw.textbbox((0, 0), confidence, font=grade_font)
    grade_w = grade_bbox[2] - grade_bbox[0]
    grade_h = grade_bbox[3] - grade_bbox[1]
    draw.text(
        (badge_x + (badge_size - grade_w) // 2 - grade_bbox[0],
         badge_y + (badge_size - grade_h) // 2 - grade_bbox[1]),
        confidence, fill=(20, 20, 30), font=grade_font
    )

    # Prediction text
    pred_text_x = badge_x + badge_size + S(16)
    favorite = away_abbrev if away_prob > home_prob else home_abbrev
    fav_prob = max(away_prob, home_prob)

    draw.text((pred_text_x, pred_y + S(4)), "MODEL PICK", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=get_font(S(12), bold=True))
    pick_font = get_font(S(22), bold=True)
    draw.text((pred_text_x, pred_y + S(22)), f"{favorite} ({fav_prob * 100:.0f}%)", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=pick_font)

    # Edge
    edge = game.get("edge", 0)
    if edge:
        edge_text = f"Edge: {edge * 100:+.1f}%"
        draw.text((pred_text_x + S(180), pred_y + S(26)), edge_text, fill=hex_to_rgb(PuckcastColors.AQUA), font=get_font(S(14), bold=True))

    draw_footer(img)
    return img


def generate_matchup_overviews(game_index: Optional[int] = None) -> list[Path]:
    """Generate matchup overview graphics."""
    print("Generating Matchup Overview graphics...")

    predictions, standings, goalies = load_data()
    games = predictions.get("games", [])

    if not games:
        print("  No games found")
        return []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = []

    # Generate for specific game or first game
    if game_index is not None:
        games = [games[game_index]] if game_index < len(games) else []

    for i, game in enumerate(games[:1]):  # Just first game by default
        home = game.get("homeTeam", {}).get("abbrev", "UNK")
        away = game.get("awayTeam", {}).get("abbrev", "UNK")

        img = generate_matchup_overview(game, standings, goalies)
        output_path = OUTPUT_DIR / f"matchup_{away}_at_{home}.png"
        save_high_quality(img, output_path)
        print(f"  Saved: {output_path}")
        paths.append(output_path)

    return paths


def main():
    try:
        game_index = int(sys.argv[1]) if len(sys.argv) > 1 else None
        paths = generate_matchup_overviews(game_index)
        if paths:
            print(f"\nGenerated {len(paths)} matchup overview image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
