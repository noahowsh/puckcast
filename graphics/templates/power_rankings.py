#!/usr/bin/env python3
"""
Power Rankings Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing power index rankings.
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
    tile_height: int = None,
) -> None:
    """Draw a team tile with large logo as the hero element."""
    if tile_height is None:
        tile_height = tile_width

    draw = ImageDraw.Draw(img)
    abbrev = team.get("abbrev", "???")
    rank = team.get("rank", 0)
    delta = team.get("rankDelta", 0)
    tier = team.get("tier", "")

    # Tier colors - subtle backgrounds
    tier_colors = {
        "elite": (126, 227, 255, 30),
        "contender": (110, 240, 194, 25),
        "playoff": (246, 193, 119, 20),
        "bubble": (255, 255, 255, 12),
        "lottery": (255, 148, 168, 20),
    }
    bg_color = tier_colors.get(tier, (255, 255, 255, 12))

    # Draw tile background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    coords = (x, y, x + tile_width, y + tile_height)
    draw_rounded_rect(overlay_draw, coords, radius=S(10), fill=bg_color, outline=(255, 255, 255, 25), width=1)

    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # LARGE team logo - hero element (centered)
    logo_size = S(90)  # Much larger logo
    logo = get_logo(abbrev, logo_size)
    logo_x = x + (tile_width - logo_size) // 2
    logo_y = y + S(12)
    result.paste(logo, (logo_x, logo_y), logo)

    # Team abbreviation - centered below logo
    abbrev_font = get_font(S(18), bold=True)
    abbrev_bbox = draw.textbbox((0, 0), abbrev, font=abbrev_font)
    abbrev_w = abbrev_bbox[2] - abbrev_bbox[0]
    abbrev_y = logo_y + logo_size + S(6)
    draw.text((x + (tile_width - abbrev_w) // 2, abbrev_y), abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)

    # Rank + Delta together at bottom center
    rank_font = get_font(S(16), bold=True)
    rank_text = str(rank)
    rank_bbox = draw.textbbox((0, 0), rank_text, font=rank_font)
    rank_w = rank_bbox[2] - rank_bbox[0]

    # Calculate total width for rank + delta
    delta_text = ""
    delta_w = 0
    if delta != 0:
        delta_font = get_font(S(14), bold=True)
        delta_text = f"+{delta}" if delta > 0 else str(delta)
        delta_bbox = draw.textbbox((0, 0), delta_text, font=delta_font)
        delta_w = delta_bbox[2] - delta_bbox[0] + S(6)  # gap

    total_w = rank_w + delta_w
    start_x = x + (tile_width - total_w) // 2
    bottom_y = y + tile_height - S(24)

    # Draw rank number
    draw.text((start_x, bottom_y), rank_text, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=rank_font)

    # Draw delta next to rank
    if delta != 0:
        delta_color = hex_to_rgb(PuckcastColors.RISING) if delta > 0 else hex_to_rgb(PuckcastColors.FALLING)
        draw.text((start_x + rank_w + S(6), bottom_y + S(1)), delta_text, fill=delta_color, font=get_font(S(14), bold=True))

    img.paste(result.convert("RGB"))


def generate_power_rankings_image(rankings: List[Dict], week_of: str) -> Image.Image:
    """Generate the power rankings grid at 2x resolution."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(40)

    # Compact header
    title_font = get_font(S(52), bold=True)
    draw.text((margin, S(40)), "POWER RANKINGS", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    # Subtitle
    subtitle_font = get_font(S(18), bold=False)
    draw.text((margin, S(98)), f"Week of {week_of}", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = S(126)
    draw.line([(margin, line_y), (margin + S(160), line_y)], fill=hex_to_rgb(PuckcastColors.AQUA), width=S(4))

    # Grid layout: 8 cols x 4 rows - larger tiles with big logos
    cols, rows = 8, 4
    tile_width = S(128)   # Wider tiles
    tile_height = S(170)  # Taller tiles for big logos
    gap = S(6)

    grid_width = cols * tile_width + (cols - 1) * gap
    start_x = (RENDER_SIZE - grid_width) // 2
    start_y = line_y + S(16)

    for i, team in enumerate(rankings[:32]):
        col = i % cols
        row = i // cols
        x = start_x + col * (tile_width + gap)
        y = start_y + row * (tile_height + gap)
        draw_team_tile(img, team, x, y, tile_width, tile_height)

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
    save_high_quality(img, output_path)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_power_rankings()
        if paths:
            print(f"\nGenerated {len(paths)} power rankings image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
