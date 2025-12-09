#!/usr/bin/env python3
"""
Today's Slate Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing today's NHL predictions.
Uses 2x supersampling for crisp output.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

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
    get_logo,
    get_font,
    save_high_quality,
    S,
    RENDER_SIZE,
)

REPO_ROOT = GRAPHICS_DIR.parents[0]
PREDICTIONS_PATH = REPO_ROOT / "web" / "src" / "data" / "todaysPredictions.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_predictions() -> Dict[str, Any]:
    """Load today's predictions from JSON."""
    if not PREDICTIONS_PATH.exists():
        raise FileNotFoundError(f"Predictions file not found: {PREDICTIONS_PATH}")
    return json.loads(PREDICTIONS_PATH.read_text())


def draw_game_row(
    img: Image.Image,
    draw: ImageDraw.Draw,
    game: Dict[str, Any],
    y_position: int,
    margin: int,
    row_height: int,
) -> None:
    """Draw a single game row with large logos and clean layout."""
    away_abbrev = game.get("awayTeam", {}).get("abbrev", "???")
    home_abbrev = game.get("homeTeam", {}).get("abbrev", "???")
    home_prob = game.get("homeWinProb", 0.5)
    away_prob = game.get("awayWinProb", 0.5)
    confidence = game.get("confidenceGrade", "C")
    start_time = game.get("startTimeEt", "TBD")
    model_favorite = game.get("modelFavorite", "home")

    # Determine favorite
    if model_favorite == "home":
        pick_abbrev = home_abbrev
        pick_prob = home_prob
    else:
        pick_abbrev = away_abbrev
        pick_prob = away_prob

    row_center_y = y_position + row_height // 2

    # Team logos - sized for row height
    logo_size = S(82)
    logo_y = row_center_y - logo_size // 2

    # Away logo
    away_logo = get_logo(away_abbrev, logo_size)
    img.paste(away_logo, (margin, logo_y), away_logo)

    # @ symbol
    at_font = get_font(S(18), bold=False)
    at_x = margin + logo_size + S(6)
    at_bbox = draw.textbbox((0, 0), "@", font=at_font)
    at_h = at_bbox[3] - at_bbox[1]
    draw.text((at_x, row_center_y - at_h // 2), "@", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=at_font)

    # Home logo
    home_logo = get_logo(home_abbrev, logo_size)
    home_logo_x = at_x + S(20)
    img.paste(home_logo, (home_logo_x, logo_y), home_logo)

    # Game info - matchup and time
    info_x = home_logo_x + logo_size + S(14)
    matchup_font = get_font(S(24), bold=True)
    time_font = get_font(S(18), bold=False)  # Larger time text

    matchup_text = f"{away_abbrev} @ {home_abbrev}"
    matchup_bbox = draw.textbbox((0, 0), matchup_text, font=matchup_font)
    matchup_h = matchup_bbox[3] - matchup_bbox[1]

    time_bbox = draw.textbbox((0, 0), start_time, font=time_font)
    time_h = time_bbox[3] - time_bbox[1]

    total_h = matchup_h + S(6) + time_h
    text_y = row_center_y - total_h // 2

    draw.text((info_x, text_y), matchup_text, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=matchup_font)
    draw.text((info_x, text_y + matchup_h + S(6)), start_time, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=time_font)

    # Right side: Grade badge + probability - pulled closer (50px inward)
    grade_color = get_confidence_color_rgb(confidence)

    # Grade badge
    badge_size = S(52)
    badge_x = img.width - margin - S(25) - badge_size  # Pulled inward 50px
    badge_y = row_center_y - badge_size // 2

    draw.ellipse([badge_x, badge_y, badge_x + badge_size, badge_y + badge_size], fill=grade_color)

    # Grade letter
    grade_font = get_font(S(30), bold=True)
    grade_bbox = draw.textbbox((0, 0), confidence, font=grade_font)
    grade_w = grade_bbox[2] - grade_bbox[0]
    grade_h = grade_bbox[3] - grade_bbox[1]
    grade_x = badge_x + (badge_size - grade_w) // 2 - grade_bbox[0]
    grade_y = badge_y + (badge_size - grade_h) // 2 - grade_bbox[1]
    draw.text(
        (grade_x, grade_y),
        confidence,
        fill=(20, 20, 30),
        font=grade_font,
    )

    # Win probability - larger and more prominent
    prob_font = get_font(S(42), bold=True)
    prob_text = f"{pick_prob * 100:.0f}%"
    prob_bbox = draw.textbbox((0, 0), prob_text, font=prob_font)
    prob_w = prob_bbox[2] - prob_bbox[0]
    prob_h = prob_bbox[3] - prob_bbox[1]
    prob_x = badge_x - prob_w - S(14)

    draw.text((prob_x, row_center_y - prob_h // 2 - S(10)), prob_text, fill=grade_color, font=prob_font)

    # Pick label - larger
    pick_font = get_font(S(16), bold=True)
    pick_label = f"Pick: {pick_abbrev}"
    pick_bbox = draw.textbbox((0, 0), pick_label, font=pick_font)
    pick_w = pick_bbox[2] - pick_bbox[0]
    draw.text((prob_x + (prob_w - pick_w) // 2, row_center_y + S(14)), pick_label, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=pick_font)


def generate_slate_image(games: List[Dict], date_str: str, page: int = 1) -> Image.Image:
    """Generate the slate image at 2x resolution."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(48)

    # Header - with proper spacing
    title_font = get_font(S(58), bold=True)
    draw.text((margin, S(48)), "TODAY'S SLATE", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    # Subtitle - 30px below title for clear hierarchy
    subtitle_font = get_font(S(22), bold=False)
    subtitle = f"Model Predictions • {date_str}"
    if page > 1:
        subtitle += f" (Page {page})"
    draw.text((margin, S(118)), subtitle, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = S(154)
    draw.line([(margin, line_y), (margin + S(140), line_y)], fill=hex_to_rgb(PuckcastColors.AQUA), width=S(4))

    # Game rows - consistent height and spacing
    content_y = line_y + S(18)
    row_height = S(120)  # Consistent row height
    row_gap = S(10)  # Consistent gap

    for i, game in enumerate(games[:6]):
        y_pos = content_y + i * (row_height + row_gap)
        draw_game_row(img, draw, game, y_pos, margin, row_height)

    draw_footer(img)
    return img


def generate_todays_slate() -> List[Path]:
    """Generate today's slate graphics."""
    print("Generating Today's Slate graphics...")

    data = load_predictions()
    games = data.get("games", [])

    if not games:
        print("  No games found")
        return []

    generated_at = data.get("generatedAt", "")
    if generated_at:
        try:
            dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%B %d, %Y")
        except:
            date_str = datetime.now().strftime("%B %d, %Y")
    else:
        date_str = datetime.now().strftime("%B %d, %Y")

    # Sort by confidence grade then probability
    grade_order = {"A+": 0, "A": 1, "A-": 2, "B+": 3, "B": 4, "B-": 5, "C+": 6, "C": 7, "C-": 8, "D": 9, "F": 10}
    games_sorted = sorted(
        games,
        key=lambda g: (grade_order.get(g.get("confidenceGrade", "C"), 7), -max(g.get("homeWinProb", 0.5), g.get("awayWinProb", 0.5)))
    )

    output_paths = []
    games_per_page = 6

    for page_idx in range(0, len(games_sorted), games_per_page):
        page_games = games_sorted[page_idx:page_idx + games_per_page]
        page_num = page_idx // games_per_page + 1

        img = generate_slate_image(page_games, date_str, page=page_num)

        if len(games_sorted) > games_per_page:
            output_path = OUTPUT_DIR / f"todays_slate_{page_num}.png"
        else:
            output_path = OUTPUT_DIR / "todays_slate.png"

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        save_high_quality(img, output_path)
        print(f"  Saved: {output_path}")
        output_paths.append(output_path)

    return output_paths


def main():
    try:
        paths = generate_todays_slate()
        if paths:
            print(f"\nGenerated {len(paths)} slate image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
