#!/usr/bin/env python3
"""
Today's Slate Template Generator

Creates a square (1080x1080) Instagram graphic showing today's NHL predictions.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from PIL import Image, ImageDraw

# Add parent directory to path for imports
GRAPHICS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GRAPHICS_DIR))

from puckcast_brand import (
    PuckcastColors,
    hex_to_rgb,
    get_team_primary_rgb,
    get_confidence_color_rgb,
    get_team_name,
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
    format_probability,
    format_edge,
)

# Paths
REPO_ROOT = GRAPHICS_DIR.parents[0]
PREDICTIONS_PATH = REPO_ROOT / "web" / "src" / "data" / "todaysPredictions.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_predictions() -> Dict[str, Any]:
    """Load today's predictions from JSON."""
    if not PREDICTIONS_PATH.exists():
        raise FileNotFoundError(f"Predictions file not found: {PREDICTIONS_PATH}")
    return json.loads(PREDICTIONS_PATH.read_text())


def draw_game_tile(
    img: Image.Image,
    game: Dict[str, Any],
    y_position: int,
    margin: int = 60,
    tile_height: int = 130,
    is_top_edge: bool = False,
) -> int:
    """
    Draw a single game tile.

    Returns the y position after the tile.
    """
    draw = ImageDraw.Draw(img)

    # Tile background
    tile_bg = (255, 255, 255, 12) if not is_top_edge else (126, 227, 255, 20)
    border_color = (255, 255, 255, 25) if not is_top_edge else (126, 227, 255, 50)

    # Create overlay for transparency
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    coords = (margin, y_position, img.width - margin, y_position + tile_height)
    draw_rounded_rect(overlay_draw, coords, radius=16, fill=tile_bg, outline=border_color, width=1)

    # Composite overlay
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)

    # Get team info
    away_abbrev = game.get("awayTeam", {}).get("abbrev", "???")
    home_abbrev = game.get("homeTeam", {}).get("abbrev", "???")
    away_name = game.get("awayTeam", {}).get("name", away_abbrev)
    home_name = game.get("homeTeam", {}).get("name", home_abbrev)

    home_prob = game.get("homeWinProb", 0.5)
    away_prob = game.get("awayWinProb", 0.5)
    edge = game.get("edge", 0)
    confidence = game.get("confidenceGrade", "C")
    start_time = game.get("startTimeEt", "TBD")
    model_favorite = game.get("modelFavorite", "home")

    # Determine winner probability
    if model_favorite == "home":
        winner_prob = home_prob
        winner_abbrev = home_abbrev
    else:
        winner_prob = away_prob
        winner_abbrev = away_abbrev

    # Draw on the composited image
    draw = ImageDraw.Draw(result)

    # Logo positions
    logo_size = 65
    logo_y = y_position + (tile_height - logo_size) // 2

    # Away logo (left side)
    away_logo = get_logo(away_abbrev, logo_size)
    result.paste(away_logo, (margin + 20, logo_y), away_logo)

    # Home logo (after the matchup text)
    home_logo_x = margin + 20 + logo_size + 200
    home_logo = get_logo(home_abbrev, logo_size)
    result.paste(home_logo, (home_logo_x, logo_y), home_logo)

    # Matchup text
    matchup_font = get_font(FontSizes.HEADING, bold=True)
    matchup_text = f"{away_abbrev}  @  {home_abbrev}"
    text_x = margin + 20 + logo_size + 15
    text_y = y_position + 25
    draw.text((text_x, text_y), matchup_text, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=matchup_font)

    # Time
    time_font = get_font(FontSizes.CAPTION, bold=False)
    time_y = text_y + 40
    draw.text((text_x, time_y), start_time, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=time_font)

    # Right side: Probability and edge
    prob_font = get_font(48, bold=True)
    prob_text = f"{winner_prob * 100:.0f}%"
    prob_x = img.width - margin - 180
    prob_y = y_position + 20
    prob_color = get_confidence_color_rgb(confidence)
    draw.text((prob_x, prob_y), prob_text, fill=prob_color, font=prob_font)

    # Edge below probability
    edge_font = get_font(FontSizes.CAPTION, bold=True)
    edge_text = f"{abs(edge) * 100:.1f} pts edge"
    edge_y = prob_y + 55
    draw.text((prob_x, edge_y), edge_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=edge_font)

    # Confidence badge
    badge_font = get_font(FontSizes.SMALL, bold=True)
    badge_text = confidence
    badge_x = img.width - margin - 55
    badge_y = y_position + tile_height - 35
    badge_color = get_confidence_color_rgb(confidence)

    # Draw badge background
    draw_rounded_rect(
        draw,
        (badge_x - 5, badge_y - 3, badge_x + 40, badge_y + 22),
        radius=10,
        fill=(*badge_color, 40),
    )
    draw.text((badge_x, badge_y), badge_text, fill=badge_color, font=badge_font)

    # Copy result back to original image
    img.paste(result.convert("RGB"))

    return y_position + tile_height + 15


def generate_slate_image(
    games: List[Dict[str, Any]],
    date_str: str,
    page: int = 1,
    games_per_page: int = 6,
) -> Image.Image:
    """
    Generate a single slate image.

    Args:
        games: List of game dictionaries
        date_str: Date string for the header
        page: Page number (for multi-page slates)
        games_per_page: Maximum games per image

    Returns:
        PIL Image
    """
    width, height = ImageDimensions.SQUARE

    # Create background
    img = create_puckcast_background(width, height)

    # Draw header
    title = "TODAY'S NHL SLATE"
    subtitle = f"Puckcast Model Predictions • {date_str}"
    y = draw_header(img, title, subtitle, margin=60)

    # Find top edge game
    top_edge_idx = 0
    top_edge_val = 0
    for i, game in enumerate(games):
        edge = abs(game.get("edge", 0))
        if edge > top_edge_val:
            top_edge_val = edge
            top_edge_idx = i

    # Draw game tiles
    for i, game in enumerate(games[:games_per_page]):
        is_top_edge = (i == top_edge_idx)
        y = draw_game_tile(img, game, y, is_top_edge=is_top_edge)

    # Draw footer
    draw_footer(img, "puckcast.ai")

    return img


def generate_todays_slate() -> List[Path]:
    """
    Generate today's slate graphics.

    Returns list of output file paths.
    """
    print("Generating Today's Slate graphics...")

    # Load predictions
    data = load_predictions()
    games = data.get("games", [])

    if not games:
        print("  No games found for today")
        return []

    # Get date from first game or generated timestamp
    generated_at = data.get("generatedAt", "")
    if generated_at:
        try:
            dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%B %d, %Y")
        except:
            date_str = datetime.now().strftime("%B %d, %Y")
    else:
        date_str = datetime.now().strftime("%B %d, %Y")

    # Sort games by edge (highest first)
    games_sorted = sorted(games, key=lambda g: abs(g.get("edge", 0)), reverse=True)

    # Generate images (one per 6 games)
    output_paths = []
    games_per_page = 6

    for page in range(0, len(games_sorted), games_per_page):
        page_games = games_sorted[page:page + games_per_page]
        page_num = page // games_per_page + 1

        img = generate_slate_image(page_games, date_str, page=page_num)

        # Save
        if len(games_sorted) > games_per_page:
            output_path = OUTPUT_DIR / f"todays_slate_{page_num}.png"
        else:
            output_path = OUTPUT_DIR / "todays_slate.png"

        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        img.save(output_path, "PNG", quality=95)
        print(f"  Saved: {output_path}")
        output_paths.append(output_path)

    return output_paths


def main():
    """CLI entry point."""
    try:
        paths = generate_todays_slate()
        if paths:
            print(f"\n Generated {len(paths)} slate image(s)")
        else:
            print("\n No images generated")
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
