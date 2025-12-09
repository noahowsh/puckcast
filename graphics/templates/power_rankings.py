#!/usr/bin/env python3
"""
Power Index Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing all 32 teams.
Uses 2x supersampling for crisp output.
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
POWER_INDEX_PATH = REPO_ROOT / "web" / "src" / "data" / "powerIndexSnapshot.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"

# Tier colors - used as accent stripe
TIER_COLORS = {
    "elite": (100, 210, 255),       # Cyan
    "contender": (80, 220, 160),    # Green
    "playoff": (255, 200, 100),     # Amber
    "bubble": (150, 150, 160),      # Gray
    "lottery": (255, 100, 120),     # Red
}


def load_power_index() -> Dict[str, Any]:
    """Load power index from JSON."""
    if not POWER_INDEX_PATH.exists():
        raise FileNotFoundError(f"Power index file not found: {POWER_INDEX_PATH}")
    return json.loads(POWER_INDEX_PATH.read_text())


def draw_team_tile(
    img: Image.Image,
    team: Dict[str, Any],
    x: int,
    y: int,
    tile_width: int,
    tile_height: int,
) -> None:
    """Draw a compact team tile with rank, logo, and abbreviation."""
    abbrev = team.get("abbrev", "???")
    rank = team.get("rank", 0)
    delta = team.get("rankDelta", 0)
    tier = team.get("tier", "bubble")

    tier_color = TIER_COLORS.get(tier, TIER_COLORS["bubble"])

    # Create overlay for tile background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Simple dark tile with subtle tier-colored left border accent
    coords = (x, y, x + tile_width, y + tile_height)
    draw_rounded_rect(overlay_draw, coords, radius=S(8), fill=(20, 25, 40, 200))

    # Tier color accent - left edge stripe
    accent_coords = (x, y + S(4), x + S(3), y + tile_height - S(4))
    overlay_draw.rectangle(accent_coords, fill=(*tier_color, 180))

    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Rank number - top left
    rank_font = get_font(S(14), bold=True)
    rank_text = str(rank)
    draw.text((x + S(10), y + S(6)), rank_text, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=rank_font)

    # Team logo - centered
    logo_size = S(52)
    logo = get_logo(abbrev, logo_size)
    logo_x = x + (tile_width - logo_size) // 2
    logo_y = y + S(14)
    result.paste(logo, (logo_x, logo_y), logo)

    # Team abbreviation + optional movement - centered below logo
    abbrev_font = get_font(S(13), bold=True)

    if delta != 0:
        # Show abbrev with movement
        if delta > 0:
            delta_str = f" +{delta}"
            delta_color = hex_to_rgb(PuckcastColors.RISING)
        else:
            delta_str = f" {delta}"
            delta_color = hex_to_rgb(PuckcastColors.FALLING)

        # Draw abbreviation
        abbrev_bbox = draw.textbbox((0, 0), abbrev, font=abbrev_font)
        abbrev_w = abbrev_bbox[2] - abbrev_bbox[0]

        delta_font = get_font(S(10), bold=True)
        delta_bbox = draw.textbbox((0, 0), delta_str, font=delta_font)
        delta_w = delta_bbox[2] - delta_bbox[0]

        total_w = abbrev_w + delta_w
        start_x = x + (tile_width - total_w) // 2
        text_y = logo_y + logo_size + S(4)

        draw.text((start_x, text_y), abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)
        draw.text((start_x + abbrev_w, text_y + S(2)), delta_str, fill=delta_color, font=delta_font)
    else:
        # Just abbreviation centered
        abbrev_bbox = draw.textbbox((0, 0), abbrev, font=abbrev_font)
        abbrev_w = abbrev_bbox[2] - abbrev_bbox[0]
        abbrev_x = x + (tile_width - abbrev_w) // 2
        text_y = logo_y + logo_size + S(4)
        draw.text((abbrev_x, text_y), abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)

    img.paste(result.convert("RGB"))


def generate_power_index_image(rankings: List[Dict], week_of: str) -> Image.Image:
    """Generate the power index with all 32 teams on one page."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(40)

    # Compact header
    title_font = get_font(S(44), bold=True)
    draw.text((margin, S(24)), "POWER INDEX", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    # Subtitle
    subtitle_font = get_font(S(14), bold=False)
    draw.text((margin, S(72)), f"Team Strength Ratings  |  {week_of}", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = S(92)
    draw.line([(margin, line_y), (margin + S(120), line_y)], fill=hex_to_rgb(PuckcastColors.AQUA), width=S(2))

    # Grid layout: 4 cols x 8 rows = 32 teams
    cols, rows = 4, 8

    # Calculate tile sizes to fit properly
    grid_margin = S(32)
    available_width = RENDER_SIZE - grid_margin * 2
    available_height = RENDER_SIZE - line_y - S(16) - S(80)  # Header + footer space

    h_gap = S(8)
    v_gap = S(6)

    tile_width = (available_width - (cols - 1) * h_gap) // cols
    tile_height = (available_height - (rows - 1) * v_gap) // rows

    start_x = grid_margin
    start_y = line_y + S(16)

    for i, team in enumerate(rankings[:32]):
        col = i % cols
        row = i // cols
        x = start_x + col * (tile_width + h_gap)
        y = start_y + row * (tile_height + v_gap)
        draw_team_tile(img, team, x, y, tile_width, tile_height)

    draw_footer(img)
    return img


def generate_power_rankings() -> List[Path]:
    """Generate power index graphic."""
    print("Generating Power Rankings graphics...")

    data = load_power_index()
    rankings = data.get("rankings", [])
    week_of = data.get("weekOf", "")

    if not rankings:
        print("  No rankings found")
        return []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    img = generate_power_index_image(rankings, week_of)
    output_path = OUTPUT_DIR / "power_rankings.png"
    save_high_quality(img, output_path)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_power_rankings()
        if paths:
            print(f"\nGenerated {len(paths)} power index image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
