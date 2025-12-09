#!/usr/bin/env python3
"""
Power Index Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing team power index.
Uses 2x supersampling for crisp output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Tuple

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

# Tier definitions with colors - more vibrant and clear
TIER_CONFIG = {
    "elite": {
        "color": (100, 210, 255),      # Bright cyan
        "alpha": 45,
        "label": "Elite",
    },
    "contender": {
        "color": (80, 220, 160),       # Bright green
        "alpha": 40,
        "label": "Contender",
    },
    "playoff": {
        "color": (255, 200, 100),      # Warm amber
        "alpha": 35,
        "label": "Playoff",
    },
    "bubble": {
        "color": (180, 180, 190),      # Neutral gray
        "alpha": 25,
        "label": "Bubble",
    },
    "lottery": {
        "color": (255, 120, 140),      # Soft red/pink
        "alpha": 40,
        "label": "Lottery",
    },
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
    """Draw a premium team tile with large logo."""
    draw = ImageDraw.Draw(img)
    abbrev = team.get("abbrev", "???")
    rank = team.get("rank", 0)
    delta = team.get("rankDelta", 0)
    tier = team.get("tier", "bubble")

    # Get tier color
    tier_info = TIER_CONFIG.get(tier, TIER_CONFIG["bubble"])
    bg_color = (*tier_info["color"], tier_info["alpha"])
    border_color = (*tier_info["color"], 70)

    # Draw tile background with tier color
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)
    coords = (x, y, x + tile_width, y + tile_height)
    draw_rounded_rect(overlay_draw, coords, radius=S(12), fill=bg_color, outline=border_color, width=2)

    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Rank badge in top-left corner
    rank_font = get_font(S(18), bold=True)
    rank_text = str(rank)
    rank_x = x + S(8)
    rank_y = y + S(6)
    draw.text((rank_x, rank_y), rank_text, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=rank_font)

    # LARGE team logo - centered hero element
    logo_size = S(80)
    logo = get_logo(abbrev, logo_size)
    logo_x = x + (tile_width - logo_size) // 2
    logo_y = y + S(22)
    result.paste(logo, (logo_x, logo_y), logo)

    # Team abbreviation - centered below logo
    abbrev_font = get_font(S(18), bold=True)
    abbrev_bbox = draw.textbbox((0, 0), abbrev, font=abbrev_font)
    abbrev_w = abbrev_bbox[2] - abbrev_bbox[0]
    abbrev_y = logo_y + logo_size + S(4)
    draw.text((x + (tile_width - abbrev_w) // 2, abbrev_y), abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)

    # Movement indicator next to abbreviation
    if delta != 0:
        delta_font = get_font(S(14), bold=True)
        if delta > 0:
            delta_text = f"+{delta}"
            delta_color = hex_to_rgb(PuckcastColors.RISING)
        else:
            delta_text = str(delta)
            delta_color = hex_to_rgb(PuckcastColors.FALLING)

        delta_bbox = draw.textbbox((0, 0), delta_text, font=delta_font)
        delta_w = delta_bbox[2] - delta_bbox[0]
        delta_y = abbrev_y + S(20)
        draw.text((x + (tile_width - delta_w) // 2, delta_y), delta_text, fill=delta_color, font=delta_font)

    img.paste(result.convert("RGB"))


def draw_tier_legend(img: Image.Image, y_position: int, margin: int) -> None:
    """Draw a horizontal tier color legend."""
    draw = ImageDraw.Draw(img)

    # Legend items
    legend_items = [
        ("elite", "Elite"),
        ("contender", "Contender"),
        ("playoff", "Playoff"),
        ("bubble", "Bubble"),
        ("lottery", "Lottery"),
    ]

    # Calculate spacing
    num_items = len(legend_items)
    available_width = RENDER_SIZE - 2 * margin
    item_width = available_width // num_items

    label_font = get_font(S(14), bold=True)

    for i, (tier_key, label) in enumerate(legend_items):
        tier_info = TIER_CONFIG[tier_key]
        color = tier_info["color"]

        item_x = margin + i * item_width + item_width // 2

        # Draw color dot
        dot_radius = S(8)
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.ellipse(
            [item_x - dot_radius - S(40), y_position - dot_radius,
             item_x + dot_radius - S(40), y_position + dot_radius],
            fill=(*color, 200)
        )
        img_rgba = img.convert("RGBA")
        result = Image.alpha_composite(img_rgba, overlay)
        img.paste(result.convert("RGB"))

        # Draw label
        label_bbox = draw.textbbox((0, 0), label, font=label_font)
        label_w = label_bbox[2] - label_bbox[0]
        draw.text(
            (item_x - label_w // 2, y_position - S(6)),
            label,
            fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY),
            font=label_font
        )


def generate_power_rankings_image(rankings: List[Dict], week_of: str) -> Image.Image:
    """Generate the power index grid at 2x resolution."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(36)

    # Title - branded as Power Index
    title_font = get_font(S(56), bold=True)
    draw.text((margin, S(36)), "POWER INDEX", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    # Descriptive subtitle
    subtitle_font = get_font(S(18), bold=False)
    draw.text((margin, S(98)), f"Comprehensive Team Strength Ratings  |  {week_of}", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = S(128)
    draw.line([(margin, line_y), (margin + S(180), line_y)], fill=hex_to_rgb(PuckcastColors.AQUA), width=S(4))

    # Grid layout: 6 cols for larger tiles
    cols = 6
    tile_width = S(168)
    tile_height = S(148)  # Sized to fit 6 rows with legend
    h_gap = S(8)
    v_gap = S(6)

    grid_width = cols * tile_width + (cols - 1) * h_gap
    start_x = (RENDER_SIZE - grid_width) // 2
    start_y = line_y + S(18)

    # Draw all 32 teams (6 rows, last row has 2 teams)
    for i, team in enumerate(rankings[:32]):
        col = i % cols
        row = i // cols
        x = start_x + col * (tile_width + h_gap)
        y = start_y + row * (tile_height + v_gap)
        draw_team_tile(img, team, x, y, tile_width, tile_height)

    # Draw tier legend at bottom
    legend_y = RENDER_SIZE - S(70)
    draw_tier_legend(img, legend_y, margin)

    draw_footer(img)
    return img


def generate_power_rankings() -> List[Path]:
    """Generate power index graphics."""
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
            print(f"\nGenerated {len(paths)} power index image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
