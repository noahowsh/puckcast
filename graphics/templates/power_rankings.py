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
    """Draw a premium team tile with large logo and stats."""
    abbrev = team.get("abbrev", "???")
    rank = team.get("rank", 0)
    delta = team.get("rankDelta", 0)
    tier = team.get("tier", "bubble")
    record = team.get("record", "0-0-0")
    points = team.get("points", 0)

    tier_color = TIER_COLORS.get(tier, TIER_COLORS["bubble"])

    # Create overlay for tile background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    # Dark tile background with tier-colored border
    coords = (x, y, x + tile_width, y + tile_height)
    draw_rounded_rect(overlay_draw, coords, radius=S(10), fill=(25, 30, 45, 220), outline=(*tier_color, 120), width=2)

    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Rank number - top left corner
    rank_font = get_font(S(18), bold=True)
    rank_text = str(rank)
    draw.text((x + S(8), y + S(6)), rank_text, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=rank_font)

    # Large team logo - centered
    logo_size = S(72)
    logo = get_logo(abbrev, logo_size)
    logo_x = x + (tile_width - logo_size) // 2
    logo_y = y + S(24)
    result.paste(logo, (logo_x, logo_y), logo)

    # Team abbreviation + movement - centered below logo
    abbrev_font = get_font(S(16), bold=True)
    if delta != 0:
        if delta > 0:
            delta_text = f"+{delta}"
            delta_color = hex_to_rgb(PuckcastColors.RISING)
        else:
            delta_text = str(delta)
            delta_color = hex_to_rgb(PuckcastColors.FALLING)
        # Draw abbrev and delta side by side
        abbrev_bbox = draw.textbbox((0, 0), abbrev, font=abbrev_font)
        abbrev_w = abbrev_bbox[2] - abbrev_bbox[0]
        delta_font = get_font(S(13), bold=True)
        delta_bbox = draw.textbbox((0, 0), delta_text, font=delta_font)
        delta_w = delta_bbox[2] - delta_bbox[0]
        total_w = abbrev_w + S(6) + delta_w
        start_x = x + (tile_width - total_w) // 2
        abbrev_y = logo_y + logo_size + S(4)
        draw.text((start_x, abbrev_y), abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)
        draw.text((start_x + abbrev_w + S(6), abbrev_y + S(2)), delta_text, fill=delta_color, font=delta_font)
    else:
        abbrev_bbox = draw.textbbox((0, 0), abbrev, font=abbrev_font)
        abbrev_w = abbrev_bbox[2] - abbrev_bbox[0]
        abbrev_y = logo_y + logo_size + S(4)
        draw.text((x + (tile_width - abbrev_w) // 2, abbrev_y), abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)

    # Points - bottom of tile
    stats_font = get_font(S(12), bold=False)
    stats_text = f"{points} PTS"
    stats_bbox = draw.textbbox((0, 0), stats_text, font=stats_font)
    stats_w = stats_bbox[2] - stats_bbox[0]
    stats_y = y + tile_height - S(18)
    draw.text((x + (tile_width - stats_w) // 2, stats_y), stats_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=stats_font)

    img.paste(result.convert("RGB"))


def generate_power_index_image(rankings: List[Dict], week_of: str) -> Image.Image:
    """Generate the power index with all 32 teams on one page."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(36)

    # Compact header
    title_font = get_font(S(48), bold=True)
    draw.text((margin, S(28)), "POWER INDEX", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    # Subtitle
    subtitle_font = get_font(S(16), bold=False)
    draw.text((margin, S(80)), f"Team Strength Ratings  |  {week_of}", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = S(104)
    draw.line([(margin, line_y), (margin + S(140), line_y)], fill=hex_to_rgb(PuckcastColors.AQUA), width=S(3))

    # Grid layout: 4 cols x 8 rows = 32 teams
    cols, rows = 4, 8
    tile_width = S(254)
    tile_height = S(118)
    h_gap = S(6)
    v_gap = S(5)

    grid_width = cols * tile_width + (cols - 1) * h_gap
    start_x = (RENDER_SIZE - grid_width) // 2
    start_y = line_y + S(12)

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
