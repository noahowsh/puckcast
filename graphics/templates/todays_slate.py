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
    draw_glass_tile,
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
    margin: int = 50,
    tile_height: int = 105,
    is_top_edge: bool = False,
) -> int:
    """
    Draw a clean, professional game tile.

    Returns the y position after the tile.
    """
    # Get team info
    away_abbrev = game.get("awayTeam", {}).get("abbrev", "???")
    home_abbrev = game.get("homeTeam", {}).get("abbrev", "???")

    home_prob = game.get("homeWinProb", 0.5)
    away_prob = game.get("awayWinProb", 0.5)
    edge = game.get("edge", 0)
    confidence = game.get("confidenceGrade", "C")
    start_time = game.get("startTimeEt", "TBD")
    model_favorite = game.get("modelFavorite", "home")

    # Determine winner
    if model_favorite == "home":
        winner_prob = home_prob
        winner_abbrev = home_abbrev
    else:
        winner_prob = away_prob
        winner_abbrev = away_abbrev

    # Draw glass tile background
    highlight_color = hex_to_rgb(PuckcastColors.AQUA) if is_top_edge else None
    result = draw_glass_tile(img, y_position, tile_height, margin, is_top_edge, highlight_color)
    draw = ImageDraw.Draw(result)

    # Layout constants
    logo_size = 56
    content_start_x = margin + 18
    logo_y = y_position + (tile_height - logo_size) // 2

    # Away team logo
    away_logo = get_logo(away_abbrev, logo_size)
    result.paste(away_logo, (content_start_x, logo_y), away_logo)

    # @ symbol between logos
    at_font = get_font(24, bold=False)
    at_x = content_start_x + logo_size + 12
    at_y = y_position + (tile_height - 24) // 2
    draw.text((at_x, at_y), "@", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=at_font)

    # Home team logo
    home_logo = get_logo(home_abbrev, logo_size)
    home_logo_x = at_x + 32
    result.paste(home_logo, (home_logo_x, logo_y), home_logo)

    # Team names in column
    names_x = home_logo_x + logo_size + 18
    name_font = get_font(20, bold=True)
    time_font = get_font(16, bold=False)

    # Away @ Home text
    matchup_text = f"{away_abbrev} @ {home_abbrev}"
    draw.text((names_x, y_position + 25), matchup_text, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=name_font)

    # Game time
    draw.text((names_x, y_position + 52), start_time, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=time_font)

    # Right side - Win probability (main stat)
    prob_font = get_font(40, bold=True)
    prob_text = f"{winner_prob * 100:.0f}%"
    prob_color = get_confidence_color_rgb(confidence)

    # Position win prob on the right
    prob_x = img.width - margin - 160
    prob_y = y_position + 18
    draw.text((prob_x, prob_y), prob_text, fill=prob_color, font=prob_font)

    # Model pick indicator (small logo of favorite)
    pick_logo = get_logo(winner_abbrev, 32)
    result.paste(pick_logo, (img.width - margin - 50, y_position + 20), pick_logo)

    # Edge value below probability
    edge_font = get_font(16, bold=True)
    edge_text = f"+{abs(edge) * 100:.1f}% edge"
    draw.text((prob_x, y_position + 62), edge_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=edge_font)

    # Confidence grade badge
    badge_font = get_font(14, bold=True)
    badge_color = get_confidence_color_rgb(confidence)
    badge_x = img.width - margin - 48
    badge_y = y_position + 60

    # Badge background
    draw_rounded_rect(
        draw,
        (badge_x - 4, badge_y - 2, badge_x + 28, badge_y + 18),
        radius=8,
        fill=(*badge_color, 50),
    )
    draw.text((badge_x + 4, badge_y), confidence, fill=badge_color, font=badge_font)

    # Copy result back
    img.paste(result.convert("RGB"))

    return y_position + tile_height + 8


def generate_slate_image(
    games: List[Dict[str, Any]],
    date_str: str,
    page: int = 1,
    games_per_page: int = 7,
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

    # Draw header with compact mode for more content
    title = "TODAY'S NHL SLATE"
    subtitle = f"Model Predictions • {date_str}"
    y = draw_header(img, title, subtitle, margin=50, compact=True)

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
        y = draw_game_tile(img, game, y, margin=50, is_top_edge=is_top_edge)

    # Draw footer
    draw_footer(img)

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

    # Generate images (one per 7 games)
    output_paths = []
    games_per_page = 7

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
