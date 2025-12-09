#!/usr/bin/env python3
"""
Power Rankings Template Generator

Creates a square (1080x1080) Instagram graphic showing power index rankings.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Dict, Any

from PIL import Image, ImageDraw

GRAPHICS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GRAPHICS_DIR))

from puckcast_brand import (
    PuckcastColors,
    hex_to_rgb,
    get_team_primary_rgb,
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
POWER_INDEX_PATH = REPO_ROOT / "web" / "src" / "data" / "powerIndexSnapshot.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_power_index() -> Dict[str, Any]:
    """Load power index from JSON."""
    if not POWER_INDEX_PATH.exists():
        raise FileNotFoundError(f"Power index file not found: {POWER_INDEX_PATH}")
    return json.loads(POWER_INDEX_PATH.read_text())


def draw_team_tile(
    img: Image.Image,
    team: Dict[str, Any],
    position: tuple,
    tile_size: int = 110,
) -> None:
    """Draw a single team tile in the grid."""
    x, y = position
    draw = ImageDraw.Draw(img)

    # Get team info
    abbrev = team.get("abbrev", "???")
    rank = team.get("rank", 0)
    delta = team.get("rankDelta", 0)
    tier = team.get("tier", "")

    # Tile background color based on tier
    tier_colors = {
        "elite": (126, 227, 255, 25),
        "contender": (110, 240, 194, 20),
        "playoff": (246, 193, 119, 15),
        "bubble": (255, 255, 255, 10),
        "lottery": (255, 148, 168, 15),
    }
    bg_color = tier_colors.get(tier, (255, 255, 255, 10))

    # Create overlay for tile
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    coords = (x, y, x + tile_size, y + tile_size)
    draw_rounded_rect(overlay_draw, coords, radius=12, fill=bg_color)

    # Composite
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)

    # Draw rank number (top left)
    rank_font = get_font(FontSizes.SMALL, bold=True)
    rank_color = hex_to_rgb(PuckcastColors.TEXT_TERTIARY)
    ImageDraw.Draw(result).text((x + 8, y + 6), str(rank), fill=rank_color, font=rank_font)

    # Draw logo (centered)
    logo_size = 50
    logo = get_logo(abbrev, logo_size)
    logo_x = x + (tile_size - logo_size) // 2
    logo_y = y + 25
    result.paste(logo, (logo_x, logo_y), logo)

    # Draw abbreviation
    abbrev_font = get_font(FontSizes.SMALL, bold=True)
    abbrev_color = hex_to_rgb(PuckcastColors.TEXT_PRIMARY)
    bbox = ImageDraw.Draw(result).textbbox((0, 0), abbrev, font=abbrev_font)
    text_width = bbox[2] - bbox[0]
    text_x = x + (tile_size - text_width) // 2
    ImageDraw.Draw(result).text((text_x, y + 78), abbrev, fill=abbrev_color, font=abbrev_font)

    # Draw delta indicator (bottom right)
    if delta != 0:
        delta_font = get_font(FontSizes.TINY, bold=True)
        if delta > 0:
            delta_text = f"+{delta}"
            delta_color = hex_to_rgb(PuckcastColors.RISING)
        else:
            delta_text = str(delta)
            delta_color = hex_to_rgb(PuckcastColors.FALLING)
        ImageDraw.Draw(result).text((x + tile_size - 28, y + tile_size - 18), delta_text, fill=delta_color, font=delta_font)

    # Copy back
    img.paste(result.convert("RGB"))


def generate_power_rankings_image(rankings: List[Dict], week_of: str) -> Image.Image:
    """Generate the power rankings grid image."""
    width, height = ImageDimensions.SQUARE

    # Create background
    img = create_puckcast_background(width, height)

    # Draw header
    title = "POWER INDEX RANKINGS"
    subtitle = f"Week of {week_of}"
    y_start = draw_header(img, title, subtitle, margin=60)

    # Calculate grid layout
    # We want to show all 32 teams in a grid
    cols = 8
    rows = 4
    margin = 60
    tile_size = 110
    gap = 10

    grid_width = cols * tile_size + (cols - 1) * gap
    grid_height = rows * tile_size + (rows - 1) * gap

    start_x = (width - grid_width) // 2
    start_y = y_start + 20

    # Draw team tiles
    for i, team in enumerate(rankings[:32]):
        col = i % cols
        row = i // cols
        x = start_x + col * (tile_size + gap)
        y = start_y + row * (tile_size + gap)
        draw_team_tile(img, team, (x, y), tile_size)

    # Draw footer
    draw_footer(img)

    return img


def generate_power_rankings() -> List[Path]:
    """Generate power rankings graphics."""
    print("Generating Power Rankings graphics...")

    data = load_power_index()
    rankings = data.get("rankings", [])
    week_of = data.get("weekOf", "")

    if not rankings:
        print("  No rankings found")
        return []

    img = generate_power_rankings_image(rankings, week_of)

    output_path = OUTPUT_DIR / "power_rankings.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_power_rankings()
        if paths:
            print(f"\n Generated {len(paths)} power rankings image(s)")
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
