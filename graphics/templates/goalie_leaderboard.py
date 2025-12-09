#!/usr/bin/env python3
"""
Goalie Leaderboard Template Generator

Creates a square (1080x1080) Instagram graphic showing top goalies by GSAX.
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
GOALIE_PULSE_PATH = REPO_ROOT / "web" / "src" / "data" / "goaliePulse.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_goalie_data() -> Dict[str, Any]:
    """Load goalie pulse data from JSON."""
    if not GOALIE_PULSE_PATH.exists():
        raise FileNotFoundError(f"Goalie pulse file not found: {GOALIE_PULSE_PATH}")
    return json.loads(GOALIE_PULSE_PATH.read_text())


def draw_goalie_row(
    img: Image.Image,
    goalie: Dict[str, Any],
    rank: int,
    y_position: int,
    margin: int = 60,
    row_height: int = 85,
) -> int:
    """Draw a single goalie row in the leaderboard."""
    draw = ImageDraw.Draw(img)

    # Get goalie info
    name = goalie.get("name", "Unknown")
    team = goalie.get("team", "???")
    gsax = goalie.get("gsax", 0)
    save_pct = goalie.get("savePct", 0)
    games = goalie.get("gamesPlayed", 0)

    # Row background (alternating subtle colors)
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if rank <= 3:
        # Top 3 get special highlight
        bg_color = (126, 227, 255, 15)  # Aqua tint
    elif rank % 2 == 0:
        bg_color = (255, 255, 255, 8)
    else:
        bg_color = (255, 255, 255, 4)

    coords = (margin, y_position, img.width - margin, y_position + row_height)
    draw_rounded_rect(overlay_draw, coords, radius=12, fill=bg_color)

    # Composite
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Rank number
    rank_font = get_font(36, bold=True)
    rank_color = hex_to_rgb(PuckcastColors.AQUA) if rank <= 3 else hex_to_rgb(PuckcastColors.TEXT_SECONDARY)
    draw.text((margin + 15, y_position + 22), str(rank), fill=rank_color, font=rank_font)

    # Team logo
    logo_size = 55
    logo = get_logo(team, logo_size)
    logo_x = margin + 65
    logo_y = y_position + (row_height - logo_size) // 2
    result.paste(logo, (logo_x, logo_y), logo)

    # Goalie name
    name_font = get_font(FontSizes.BODY, bold=True)
    name_color = hex_to_rgb(PuckcastColors.TEXT_PRIMARY)
    draw.text((margin + 135, y_position + 18), name, fill=name_color, font=name_font)

    # Team abbreviation under name
    team_font = get_font(FontSizes.CAPTION, bold=False)
    team_color = hex_to_rgb(PuckcastColors.TEXT_TERTIARY)
    draw.text((margin + 135, y_position + 48), team, fill=team_color, font=team_font)

    # Stats on the right side
    # GSAX (primary stat)
    gsax_font = get_font(32, bold=True)
    gsax_text = f"+{gsax:.1f}" if gsax > 0 else f"{gsax:.1f}"
    gsax_color = hex_to_rgb(PuckcastColors.RISING) if gsax > 0 else hex_to_rgb(PuckcastColors.FALLING)
    draw.text((img.width - margin - 280, y_position + 15), gsax_text, fill=gsax_color, font=gsax_font)

    # GSAX label
    gsax_label_font = get_font(FontSizes.TINY, bold=False)
    draw.text((img.width - margin - 280, y_position + 52), "GSAX", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=gsax_label_font)

    # Save percentage
    sv_font = get_font(24, bold=True)
    sv_text = f".{int(save_pct * 1000)}"
    draw.text((img.width - margin - 170, y_position + 20), sv_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=sv_font)

    sv_label_font = get_font(FontSizes.TINY, bold=False)
    draw.text((img.width - margin - 170, y_position + 52), "SV%", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=sv_label_font)

    # Games played
    gp_font = get_font(24, bold=True)
    draw.text((img.width - margin - 80, y_position + 20), str(games), fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=gp_font)

    gp_label_font = get_font(FontSizes.TINY, bold=False)
    draw.text((img.width - margin - 80, y_position + 52), "GP", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=gp_label_font)

    # Copy back
    img.paste(result.convert("RGB"))

    return y_position + row_height + 5


def generate_goalie_leaderboard_image(goalies: List[Dict], updated_at: str) -> Image.Image:
    """Generate the goalie leaderboard image."""
    width, height = ImageDimensions.SQUARE

    # Create background
    img = create_puckcast_background(width, height)

    # Draw header
    title = "TOP GOALIES BY GSAX"
    subtitle = "Goals Saved Above Expected"
    y = draw_header(img, title, subtitle, margin=60)

    y += 10

    # Draw goalie rows (top 10)
    for i, goalie in enumerate(goalies[:10], 1):
        y = draw_goalie_row(img, goalie, i, y)

    # Draw footer
    draw_footer(img, "puckcast.ai")

    return img


def generate_goalie_leaderboard() -> List[Path]:
    """Generate goalie leaderboard graphics."""
    print("Generating Goalie Leaderboard graphics...")

    data = load_goalie_data()
    goalies = data.get("goalies", [])
    updated_at = data.get("updatedAt", "")

    if not goalies:
        print("  No goalie data found")
        return []

    # Sort by GSAX (highest first)
    goalies_sorted = sorted(goalies, key=lambda g: g.get("gsax", 0), reverse=True)

    img = generate_goalie_leaderboard_image(goalies_sorted, updated_at)

    output_path = OUTPUT_DIR / "goalie_leaderboard.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_goalie_leaderboard()
        if paths:
            print(f"\n Generated {len(paths)} goalie leaderboard image(s)")
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
