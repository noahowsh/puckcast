#!/usr/bin/env python3
"""
Power Index Template Generator - Premium Instagram Design

Creates square (1080x1080) Instagram graphics showing team power index.
Uses 2x supersampling for crisp output. Generates 2 pages for all 32 teams.
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

    # Dark tile background
    coords = (x, y, x + tile_width, y + tile_height)
    draw_rounded_rect(overlay_draw, coords, radius=S(14), fill=(30, 35, 50, 200), outline=(255, 255, 255, 40), width=1)

    # Tier color accent stripe on left
    stripe_width = S(5)
    stripe_coords = (x, y + S(12), x + stripe_width, y + tile_height - S(12))
    overlay_draw.rectangle(stripe_coords, fill=(*tier_color, 255))

    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Large rank number - top left
    rank_font = get_font(S(32), bold=True)
    rank_text = str(rank)
    rank_x = x + S(18)
    rank_y = y + S(12)
    draw.text((rank_x, rank_y), rank_text, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=rank_font)

    # Movement indicator next to rank
    if delta != 0:
        delta_font = get_font(S(18), bold=True)
        if delta > 0:
            delta_text = f"+{delta}"
            delta_color = hex_to_rgb(PuckcastColors.RISING)
        else:
            delta_text = str(delta)
            delta_color = hex_to_rgb(PuckcastColors.FALLING)
        draw.text((rank_x + S(40), rank_y + S(8)), delta_text, fill=delta_color, font=delta_font)

    # HUGE team logo - centered
    logo_size = S(120)
    logo = get_logo(abbrev, logo_size)
    logo_x = x + (tile_width - logo_size) // 2
    logo_y = y + S(48)
    result.paste(logo, (logo_x, logo_y), logo)

    # Team abbreviation - centered below logo
    abbrev_font = get_font(S(26), bold=True)
    abbrev_bbox = draw.textbbox((0, 0), abbrev, font=abbrev_font)
    abbrev_w = abbrev_bbox[2] - abbrev_bbox[0]
    abbrev_y = logo_y + logo_size + S(8)
    draw.text((x + (tile_width - abbrev_w) // 2, abbrev_y), abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)

    # Record and points - bottom of tile
    stats_font = get_font(S(16), bold=False)
    stats_text = f"{record}  |  {points} PTS"
    stats_bbox = draw.textbbox((0, 0), stats_text, font=stats_font)
    stats_w = stats_bbox[2] - stats_bbox[0]
    stats_y = y + tile_height - S(28)
    draw.text((x + (tile_width - stats_w) // 2, stats_y), stats_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=stats_font)

    img.paste(result.convert("RGB"))


def generate_power_index_page(rankings: List[Dict], week_of: str, page: int) -> Image.Image:
    """Generate a single page of the power index (16 teams per page)."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(40)

    # Title
    title_font = get_font(S(52), bold=True)
    draw.text((margin, S(32)), "POWER INDEX", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    # Subtitle with page indicator
    subtitle_font = get_font(S(18), bold=False)
    if page == 1:
        page_text = f"Top 16 Teams  |  {week_of}"
    else:
        page_text = f"Teams 17-32  |  {week_of}"
    draw.text((margin, S(90)), page_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = S(118)
    draw.line([(margin, line_y), (margin + S(160), line_y)], fill=hex_to_rgb(PuckcastColors.AQUA), width=S(4))

    # Grid layout: 4 cols x 4 rows = 16 teams per page
    cols, rows = 4, 4
    tile_width = S(250)
    tile_height = S(200)
    h_gap = S(10)
    v_gap = S(10)

    grid_width = cols * tile_width + (cols - 1) * h_gap
    start_x = (RENDER_SIZE - grid_width) // 2
    start_y = line_y + S(16)

    # Get teams for this page
    start_idx = (page - 1) * 16
    end_idx = start_idx + 16
    page_teams = rankings[start_idx:end_idx]

    for i, team in enumerate(page_teams):
        col = i % cols
        row = i // cols
        x = start_x + col * (tile_width + h_gap)
        y = start_y + row * (tile_height + v_gap)
        draw_team_tile(img, team, x, y, tile_width, tile_height)

    draw_footer(img)
    return img


def generate_power_rankings() -> List[Path]:
    """Generate power index graphics (2 pages)."""
    print("Generating Power Rankings graphics...")

    data = load_power_index()
    rankings = data.get("rankings", [])
    week_of = data.get("weekOf", "")

    if not rankings:
        print("  No rankings found")
        return []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_paths = []

    # Generate page 1 (Top 16)
    img1 = generate_power_index_page(rankings, week_of, 1)
    output_path1 = OUTPUT_DIR / "power_rankings.png"
    save_high_quality(img1, output_path1)
    print(f"  Saved: {output_path1}")
    output_paths.append(output_path1)

    # Generate page 2 (Teams 17-32)
    img2 = generate_power_index_page(rankings, week_of, 2)
    output_path2 = OUTPUT_DIR / "power_rankings_2.png"
    save_high_quality(img2, output_path2)
    print(f"  Saved: {output_path2}")
    output_paths.append(output_path2)

    return output_paths


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
