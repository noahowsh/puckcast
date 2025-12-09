#!/usr/bin/env python3
"""
Edge Posts Template Generator

Creates a square (1080x1080) Instagram graphic showing top model edges for today.
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
PREDICTIONS_PATH = REPO_ROOT / "web" / "src" / "data" / "todaysPredictions.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_predictions() -> Dict[str, Any]:
    """Load today's predictions from JSON."""
    if not PREDICTIONS_PATH.exists():
        raise FileNotFoundError(f"Predictions file not found: {PREDICTIONS_PATH}")
    return json.loads(PREDICTIONS_PATH.read_text())


def draw_edge_tile(
    img: Image.Image,
    game: Dict[str, Any],
    y_position: int,
    margin: int,
    tile_height: int,
    rank: int,
) -> None:
    """Draw a single edge tile."""
    draw = ImageDraw.Draw(img)

    away_abbrev = game.get("awayTeam", {}).get("abbrev", "???")
    home_abbrev = game.get("homeTeam", {}).get("abbrev", "???")
    home_prob = game.get("homeWinProb", 0.5)
    away_prob = game.get("awayWinProb", 0.5)
    edge = game.get("edge", 0)
    confidence = game.get("confidenceGrade", "C")
    start_time = game.get("startTimeEt", "TBD")
    model_favorite = game.get("modelFavorite", "home")

    # Determine favorite
    if model_favorite == "home":
        fav_abbrev = home_abbrev
        fav_prob = home_prob
    else:
        fav_abbrev = away_abbrev
        fav_prob = away_prob

    # Tile background with confidence-based highlight
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Highlight color based on edge strength
    if abs(edge) >= 0.10:
        bg_color = (126, 227, 255, 25)  # Strong edge - aqua
    elif abs(edge) >= 0.05:
        bg_color = (110, 240, 194, 20)  # Medium edge - mint
    else:
        bg_color = (255, 255, 255, 12)  # Low edge

    coords = (margin, y_position, img.width - margin, y_position + tile_height)
    draw_rounded_rect(overlay_draw, coords, radius=14, fill=bg_color)

    # Composite
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Rank badge on the left
    rank_font = get_font(22, bold=True)
    rank_color = hex_to_rgb(PuckcastColors.AQUA)
    draw.text((margin + 18, y_position + (tile_height - 22) // 2), f"#{rank}", fill=rank_color, font=rank_font)

    # Team logos
    logo_size = 50
    logo_y = y_position + (tile_height - logo_size) // 2
    away_logo = get_logo(away_abbrev, logo_size)
    result.paste(away_logo, (margin + 60, logo_y), away_logo)

    # VS text
    vs_font = get_font(FontSizes.SMALL, bold=False)
    draw.text((margin + 118, y_position + (tile_height - 18) // 2), "vs", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=vs_font)

    home_logo = get_logo(home_abbrev, logo_size)
    result.paste(home_logo, (margin + 150, logo_y), home_logo)

    # Game time below logos
    time_font = get_font(FontSizes.SMALL, bold=False)
    draw.text((margin + 60, y_position + tile_height - 22), start_time, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=time_font)

    # Right side - Edge info
    # Big edge percentage
    edge_font = get_font(36, bold=True)
    edge_pct = abs(edge) * 100
    edge_text = f"{edge_pct:.1f}%"
    edge_color = get_confidence_color_rgb(confidence)

    edge_x = img.width - margin - 185
    draw.text((edge_x, y_position + 15), edge_text, fill=edge_color, font=edge_font)

    # "edge" label
    edge_label_font = get_font(FontSizes.SMALL, bold=False)
    draw.text((edge_x, y_position + 52), "edge", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=edge_label_font)

    # Model pick with logo
    pick_logo = get_logo(fav_abbrev, 36)
    result.paste(pick_logo, (img.width - margin - 75, y_position + 18), pick_logo)

    # Pick probability below
    prob_font = get_font(FontSizes.SMALL, bold=True)
    prob_text = f"{fav_prob * 100:.0f}%"
    draw.text((img.width - margin - 70, y_position + 58), prob_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=prob_font)

    # Copy back
    img.paste(result.convert("RGB"))


def generate_edge_posts_image(games: List[Dict], date_str: str) -> Image.Image:
    """Generate the edge posts image."""
    width, height = ImageDimensions.SQUARE

    # Create background
    img = create_puckcast_background(width, height)

    # Draw header
    title = "TOP MODEL EDGES"
    subtitle = f"Best Bets for {date_str}"
    y = draw_header(img, title, subtitle, margin=60)

    draw = ImageDraw.Draw(img)
    margin = 60
    tile_height = 100

    # Explanation
    explain_font = get_font(FontSizes.BODY, bold=False)
    explain_text = "Where the model sees the biggest advantage"
    bbox = draw.textbbox((0, 0), explain_text, font=explain_font)
    text_width = bbox[2] - bbox[0]
    draw.text(((width - text_width) // 2, y), explain_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=explain_font)
    y += 45

    # Draw edge tiles (top 6 by edge)
    for i, game in enumerate(games[:6], 1):
        draw_edge_tile(img, game, y, margin, tile_height, rank=i)
        y += tile_height + 8

    # Draw footer
    draw_footer(img)

    return img


def generate_edge_posts() -> List[Path]:
    """Generate edge posts graphics."""
    print("Generating Edge Posts graphics...")

    data = load_predictions()
    games = data.get("games", [])

    if not games:
        print("  No games found for today")
        return []

    # Sort by edge (highest first)
    games_sorted = sorted(games, key=lambda g: abs(g.get("edge", 0)), reverse=True)

    # Filter to only high-edge games (> 2%)
    high_edge_games = [g for g in games_sorted if abs(g.get("edge", 0)) > 0.02]

    if not high_edge_games:
        print("  No high-edge games found")
        high_edge_games = games_sorted[:6]  # Fall back to top 6

    # Get date
    generated_at = data.get("generatedAt", "")
    if generated_at:
        try:
            dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%B %d, %Y")
        except:
            date_str = datetime.now().strftime("%B %d, %Y")
    else:
        date_str = datetime.now().strftime("%B %d, %Y")

    img = generate_edge_posts_image(high_edge_games, date_str)

    output_path = OUTPUT_DIR / "edge_posts.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_edge_posts()
        if paths:
            print(f"\n Generated {len(paths)} edge posts image(s)")
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
