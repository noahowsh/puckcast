#!/usr/bin/env python3
"""
Model Receipts Template Generator

Creates a square (1080x1080) Instagram graphic showing how the model did on recent predictions.
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
    ImageDimensions,
)
from image_utils import (
    create_puckcast_background,
    draw_header,
    draw_footer,
    draw_rounded_rect,
    get_logo,
    get_font,
    FontSizes,
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
    """Draw a single game result row."""
    draw = ImageDraw.Draw(img)

    away_abbrev = game.get("awayTeam", {}).get("abbrev", "???")
    home_abbrev = game.get("homeTeam", {}).get("abbrev", "???")
    home_prob = game.get("homeWinProb", 0.5)
    away_prob = game.get("awayWinProb", 0.5)
    model_favorite = game.get("modelFavorite", "home")

    # For results - check if prediction was correct
    actual_winner = game.get("actualWinner", None)  # "home", "away", or None
    is_correct = game.get("isCorrect", None)

    # Demo mode - simulate results
    if is_demo:
        # Simulate: model picks correctly when confidence > 55%
        model_conf = home_prob if model_favorite == "home" else away_prob
        is_correct = model_conf > 0.55
        actual_winner = model_favorite if is_correct else ("away" if model_favorite == "home" else "home")

    # Row background based on result
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if is_correct is True:
        bg_color = (110, 240, 194, 15)  # Green for correct
        result_icon = "✓"
        result_color = hex_to_rgb(PuckcastColors.RISING)
    elif is_correct is False:
        bg_color = (255, 148, 168, 15)  # Red for incorrect
        result_icon = "✗"
        result_color = hex_to_rgb(PuckcastColors.FALLING)
    else:
        bg_color = (255, 255, 255, 10)  # Neutral
        result_icon = "?"
        result_color = hex_to_rgb(PuckcastColors.TEXT_TERTIARY)

    coords = (margin, y_position, img.width - margin, y_position + row_height)
    draw_rounded_rect(overlay_draw, coords, radius=12, fill=bg_color)

    # Composite
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Result icon on the left
    icon_font = get_font(36, bold=True)
    draw.text((margin + 20, y_position + 18), result_icon, fill=result_color, font=icon_font)

    # Away team logo
    logo_size = 50
    away_logo = get_logo(away_abbrev, logo_size)
    result.paste(away_logo, (margin + 70, y_position + (row_height - logo_size) // 2), away_logo)

    # @ symbol
    at_font = get_font(FontSizes.BODY, bold=False)
    draw.text((margin + 130, y_position + 25), "@", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=at_font)

    # Home team logo
    home_logo = get_logo(home_abbrev, logo_size)
    result.paste(home_logo, (margin + 165, y_position + (row_height - logo_size) // 2), home_logo)

    # Model pick
    pick_font = get_font(FontSizes.BODY, bold=True)
    pick_abbrev = home_abbrev if model_favorite == "home" else away_abbrev
    pick_prob = home_prob if model_favorite == "home" else away_prob
    pick_text = f"Picked {pick_abbrev} ({pick_prob * 100:.0f}%)"
    draw.text((margin + 240, y_position + 25), pick_text, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=pick_font)

    # Actual result on the right
    if actual_winner:
        winner_abbrev = home_abbrev if actual_winner == "home" else away_abbrev
        winner_font = get_font(FontSizes.BODY, bold=True)
        winner_text = f"{winner_abbrev} won"
        bbox = draw.textbbox((0, 0), winner_text, font=winner_font)
        text_width = bbox[2] - bbox[0]
        draw.text((img.width - margin - text_width - 20, y_position + 25), winner_text, fill=result_color, font=winner_font)

    # Copy back
    img.paste(result.convert("RGB"))


def generate_model_receipts_image(games: List[Dict], date_str: str, accuracy: float, is_demo: bool = False) -> Image.Image:
    """Generate the model receipts image."""
    width, height = ImageDimensions.SQUARE

    # Create background
    img = create_puckcast_background(width, height)

    # Draw header
    title = "MODEL RECEIPTS" if not is_demo else "MODEL RECEIPTS (DEMO)"
    subtitle = f"Results from {date_str}"
    y = draw_header(img, title, subtitle, margin=60)

    draw = ImageDraw.Draw(img)
    margin = 60
    row_height = 75

    # Accuracy summary
    acc_font = get_font(48, bold=True)
    acc_text = f"{accuracy * 100:.0f}%"
    acc_color = hex_to_rgb(PuckcastColors.AQUA) if accuracy >= 0.5 else hex_to_rgb(PuckcastColors.FALLING)

    # Center accuracy
    acc_bbox = draw.textbbox((0, 0), acc_text, font=acc_font)
    acc_width = acc_bbox[2] - acc_bbox[0]
    draw.text(((width - acc_width) // 2, y), acc_text, fill=acc_color, font=acc_font)

    # "Accuracy" label
    label_font = get_font(FontSizes.BODY, bold=False)
    label_text = "Accuracy"
    label_bbox = draw.textbbox((0, 0), label_text, font=label_font)
    label_width = label_bbox[2] - label_bbox[0]
    draw.text(((width - label_width) // 2, y + 55), label_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=label_font)

    y += 100

    # Draw game results
    for game in games[:8]:  # Max 8 games
        draw_result_row(img, game, y, margin, row_height, is_demo=is_demo)
        y += row_height + 8

    # Draw footer
    draw_footer(img)

    return img


def generate_model_receipts() -> List[Path]:
    """Generate model receipts graphics."""
    print("Generating Model Receipts graphics...")

    # Try to load actual results
    results = load_prediction_results()

    if results and results.get("results"):
        # Use actual results
        latest = results["results"][0] if results["results"] else None
        if latest:
            games = latest.get("games", [])
            date_str = latest.get("date", "Recent")
            correct = sum(1 for g in games if g.get("isCorrect"))
            accuracy = correct / len(games) if games else 0
            is_demo = False
        else:
            games = []
            date_str = "No Data"
            accuracy = 0
            is_demo = True
    else:
        # Demo mode - use today's predictions
        print("  No results data found, using demo mode with today's predictions")
        predictions = load_todays_predictions()
        games = predictions.get("games", [])
        date_str = datetime.now().strftime("%B %d, %Y") + " (Demo)"

        # Simulate accuracy based on confidence
        correct = sum(1 for g in games if (g.get("homeWinProb", 0.5) if g.get("modelFavorite") == "home" else g.get("awayWinProb", 0.5)) > 0.55)
        accuracy = correct / len(games) if games else 0
        is_demo = True

    if not games:
        print("  No game data found")
        return []

    img = generate_model_receipts_image(games, date_str, accuracy, is_demo=is_demo)

    output_path = OUTPUT_DIR / "model_receipts.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_model_receipts()
        if paths:
            print(f"\n Generated {len(paths)} model receipts image(s)")
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
