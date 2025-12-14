#!/usr/bin/env python3
"""
Model Receipts Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing model prediction results.
Uses 2x supersampling for crisp output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from PIL import Image, ImageDraw

GRAPHICS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GRAPHICS_DIR))

from puckcast_brand import (
    PuckcastColors,
    hex_to_rgb,
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
PREDICTION_RESULTS_PATH = REPO_ROOT / "web" / "src" / "data" / "predictionResults.json"
PREDICTIONS_PATH = REPO_ROOT / "web" / "src" / "data" / "todaysPredictions.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_prediction_results() -> Dict[str, Any]:
    """Load prediction results from JSON."""
    if PREDICTION_RESULTS_PATH.exists():
        return json.loads(PREDICTION_RESULTS_PATH.read_text())
    return {}


def load_todays_predictions() -> Dict[str, Any]:
    """Load today's predictions for demo mode."""
    if not PREDICTIONS_PATH.exists():
        return {}
    return json.loads(PREDICTIONS_PATH.read_text())


def draw_result_row(
    img: Image.Image,
    game: Dict[str, Any],
    y_position: int,
    margin: int,
    row_height: int,
    is_demo: bool = False,
) -> None:
    """Draw a game result row."""
    away_abbrev = game.get("awayTeam", {}).get("abbrev", "???")
    home_abbrev = game.get("homeTeam", {}).get("abbrev", "???")
    home_prob = game.get("homeWinProb", 0.5)
    away_prob = game.get("awayWinProb", 0.5)
    model_favorite = game.get("modelFavorite", "home")
    actual_winner = game.get("actualWinner", None)
    is_correct = game.get("isCorrect", None)

    # Demo mode simulation
    if is_demo:
        model_conf = home_prob if model_favorite == "home" else away_prob
        is_correct = model_conf > 0.55
        actual_winner = model_favorite if is_correct else ("away" if model_favorite == "home" else "home")

    row_center_y = y_position + row_height // 2

    # Row background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if is_correct is True:
        bg_color = (110, 240, 194, 20)
        border_color = (110, 240, 194, 50)
        result_icon = "✓"
        result_color = hex_to_rgb(PuckcastColors.RISING)
    elif is_correct is False:
        bg_color = (255, 148, 168, 20)
        border_color = (255, 148, 168, 50)
        result_icon = "✗"
        result_color = hex_to_rgb(PuckcastColors.FALLING)
    else:
        bg_color = (255, 255, 255, 15)
        border_color = (255, 255, 255, 35)
        result_icon = "?"
        result_color = hex_to_rgb(PuckcastColors.TEXT_TERTIARY)

    coords = (margin, y_position, img.width - margin, y_position + row_height)
    draw_rounded_rect(overlay_draw, coords, radius=S(10), fill=bg_color, outline=border_color, width=1)

    img_rgba = img.convert("RGBA")
    result_img = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result_img)

    # Result icon
    icon_font = get_font(S(26), bold=True)
    icon_bbox = draw.textbbox((0, 0), result_icon, font=icon_font)
    icon_h = icon_bbox[3] - icon_bbox[1]
    draw.text((margin + S(15), row_center_y - icon_h // 2 - S(2)), result_icon, fill=result_color, font=icon_font)

    # Away logo
    logo_size = S(48)
    away_logo = get_logo(away_abbrev, logo_size)
    away_logo_x = margin + S(55)
    logo_y = row_center_y - logo_size // 2
    result_img.paste(away_logo, (away_logo_x, logo_y), away_logo)

    # @ symbol
    at_font = get_font(S(16), bold=False)
    at_x = away_logo_x + logo_size + S(8)
    at_bbox = draw.textbbox((0, 0), "@", font=at_font)
    at_h = at_bbox[3] - at_bbox[1]
    draw.text((at_x, row_center_y - at_h // 2 - S(2)), "@", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=at_font)

    # Home logo
    home_logo = get_logo(home_abbrev, logo_size)
    home_logo_x = at_x + S(22)
    result_img.paste(home_logo, (home_logo_x, logo_y), home_logo)

    # Model pick info
    pick_x = home_logo_x + logo_size + S(15)
    pick_font = get_font(S(18), bold=True)
    pick_abbrev = home_abbrev if model_favorite == "home" else away_abbrev
    pick_prob = home_prob if model_favorite == "home" else away_prob
    pick_text = f"Picked {pick_abbrev} ({pick_prob * 100:.0f}%)"
    pick_bbox = draw.textbbox((0, 0), pick_text, font=pick_font)
    pick_h = pick_bbox[3] - pick_bbox[1]
    draw.text((pick_x, row_center_y - pick_h // 2 - S(2)), pick_text, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=pick_font)

    # Actual result
    if actual_winner:
        winner_abbrev = home_abbrev if actual_winner == "home" else away_abbrev
        winner_font = get_font(S(18), bold=True)
        winner_text = f"{winner_abbrev} won"
        winner_bbox = draw.textbbox((0, 0), winner_text, font=winner_font)
        winner_w = winner_bbox[2] - winner_bbox[0]
        winner_h = winner_bbox[3] - winner_bbox[1]
        draw.text((img.width - margin - winner_w - S(18), row_center_y - winner_h // 2 - S(2)), winner_text, fill=result_color, font=winner_font)

    img.paste(result_img.convert("RGB"))


def generate_model_receipts_image(games: List[Dict], date_str: str, accuracy: float, is_demo: bool = False) -> Image.Image:
    """Generate the model receipts at 2x resolution."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(55)

    # Header
    title_font = get_font(S(64), bold=True)
    title = "MODEL RECEIPTS" if not is_demo else "MODEL RECEIPTS"
    draw.text((margin, S(45)), title, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    subtitle_font = get_font(S(24), bold=False)
    subtitle = f"Results from {date_str}"
    if is_demo:
        subtitle += " (Demo)"
    draw.text((margin, S(115)), subtitle, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = S(155)
    draw.line([(margin, line_y), (margin + S(200), line_y)], fill=hex_to_rgb(PuckcastColors.AQUA), width=S(4))

    # Accuracy display
    acc_y = line_y + S(30)
    acc_font = get_font(S(52), bold=True)
    acc_text = f"{accuracy * 100:.0f}%"
    acc_color = hex_to_rgb(PuckcastColors.AQUA) if accuracy >= 0.5 else hex_to_rgb(PuckcastColors.FALLING)
    acc_bbox = draw.textbbox((0, 0), acc_text, font=acc_font)
    acc_w = acc_bbox[2] - acc_bbox[0]
    draw.text(((RENDER_SIZE - acc_w) // 2, acc_y), acc_text, fill=acc_color, font=acc_font)

    label_font = get_font(S(20), bold=False)
    label_text = "Accuracy"
    label_bbox = draw.textbbox((0, 0), label_text, font=label_font)
    label_w = label_bbox[2] - label_bbox[0]
    draw.text(((RENDER_SIZE - label_w) // 2, acc_y + S(58)), label_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=label_font)

    # Game results
    content_y = acc_y + S(100)
    row_height = S(72)
    row_gap = S(8)

    for i, game in enumerate(games[:9]):
        y_pos = content_y + i * (row_height + row_gap)
        draw_result_row(img, game, y_pos, margin, row_height, is_demo=is_demo)

    draw_footer(img)
    return img


def generate_model_receipts() -> List[Path]:
    """Generate model receipts graphics (only if actual results exist)."""
    print("Generating Model Receipts graphics...")

    results = load_prediction_results()

    # Only generate if we have actual prediction results
    if not results or not results.get("results"):
        print("  No prediction results data found - skipping (this requires yesterday's game results)")
        return []

    latest = results["results"][0] if results["results"] else None
    if not latest or not latest.get("games"):
        print("  No game results in data - skipping")
        return []

    games = latest.get("games", [])
    date_str = latest.get("date", "Recent")
    correct = sum(1 for g in games if g.get("isCorrect"))
    accuracy = correct / len(games) if games else 0

    img = generate_model_receipts_image(games, date_str, accuracy, is_demo=False)

    output_path = OUTPUT_DIR / "model_receipts.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_high_quality(img, output_path)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_model_receipts()
        if paths:
            print(f"\nGenerated {len(paths)} model receipts image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
