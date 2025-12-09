#!/usr/bin/env python3
"""
Power Index Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing all 32 teams
in a clean two-column list layout with stats.
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
    get_logo,
    get_font,
    save_high_quality,
    S,
    RENDER_SIZE,
)

REPO_ROOT = GRAPHICS_DIR.parents[0]
POWER_INDEX_PATH = REPO_ROOT / "web" / "src" / "data" / "powerIndexSnapshot.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"

# Tier colors for rank badges
TIER_COLORS = {
    "elite": (100, 210, 255),       # Cyan
    "contender": (80, 220, 160),    # Green
    "playoff": (255, 200, 100),     # Amber
    "bubble": (120, 120, 130),      # Gray
    "lottery": (255, 100, 120),     # Red
}


def load_power_index() -> Dict[str, Any]:
    """Load power index from JSON."""
    if not POWER_INDEX_PATH.exists():
        raise FileNotFoundError(f"Power index file not found: {POWER_INDEX_PATH}")
    return json.loads(POWER_INDEX_PATH.read_text())


def draw_team_row(
    img: Image.Image,
    draw: ImageDraw.Draw,
    team: Dict[str, Any],
    x: int,
    y: int,
    row_width: int,
    row_height: int,
) -> None:
    """Draw a single team row with rank, logo, stats."""
    abbrev = team.get("abbrev", "???")
    rank = team.get("rank", 0)
    delta = team.get("rankDelta", 0)
    tier = team.get("tier", "bubble")
    record = team.get("record", "0-0-0")
    points = team.get("points", 0)

    tier_color = TIER_COLORS.get(tier, TIER_COLORS["bubble"])

    # Row layout: [Rank] [Logo] [Abbrev] [Record] [Pts] [Movement]
    # Proportions across row_width

    # Rank badge
    rank_size = S(28)
    rank_x = x + S(4)
    rank_y = y + (row_height - rank_size) // 2

    # Draw rank circle with tier color
    draw.ellipse(
        [rank_x, rank_y, rank_x + rank_size, rank_y + rank_size],
        fill=(*tier_color, 200)
    )
    rank_font = get_font(S(14), bold=True)
    rank_text = str(rank)
    rank_bbox = draw.textbbox((0, 0), rank_text, font=rank_font)
    rank_tw = rank_bbox[2] - rank_bbox[0]
    rank_th = rank_bbox[3] - rank_bbox[1]
    draw.text(
        (rank_x + (rank_size - rank_tw) // 2 - rank_bbox[0],
         rank_y + (rank_size - rank_th) // 2 - rank_bbox[1]),
        rank_text,
        fill=(10, 15, 25),
        font=rank_font
    )

    # Team logo
    logo_size = S(36)
    logo_x = rank_x + rank_size + S(10)
    logo_y = y + (row_height - logo_size) // 2
    logo = get_logo(abbrev, logo_size)
    img.paste(logo, (logo_x, logo_y), logo)

    # Team abbreviation
    abbrev_font = get_font(S(16), bold=True)
    abbrev_x = logo_x + logo_size + S(10)
    abbrev_bbox = draw.textbbox((0, 0), abbrev, font=abbrev_font)
    abbrev_y = y + (row_height - (abbrev_bbox[3] - abbrev_bbox[1])) // 2 - abbrev_bbox[1]
    draw.text((abbrev_x, abbrev_y), abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)

    # Record (right-aligned in middle section)
    record_font = get_font(S(13), bold=False)
    record_bbox = draw.textbbox((0, 0), record, font=record_font)
    record_w = record_bbox[2] - record_bbox[0]
    record_x = x + row_width - S(80) - record_w
    record_y = y + (row_height - (record_bbox[3] - record_bbox[1])) // 2 - record_bbox[1]
    draw.text((record_x, record_y), record, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=record_font)

    # Points
    pts_font = get_font(S(14), bold=True)
    pts_text = f"{points}"
    pts_bbox = draw.textbbox((0, 0), pts_text, font=pts_font)
    pts_w = pts_bbox[2] - pts_bbox[0]
    pts_x = x + row_width - S(36) - pts_w
    pts_y = y + (row_height - (pts_bbox[3] - pts_bbox[1])) // 2 - pts_bbox[1]
    draw.text((pts_x, pts_y), pts_text, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=pts_font)

    # Movement indicator (far right)
    if delta != 0:
        if delta > 0:
            delta_text = f"+{delta}"
            delta_color = hex_to_rgb(PuckcastColors.RISING)
        else:
            delta_text = str(delta)
            delta_color = hex_to_rgb(PuckcastColors.FALLING)
        delta_font = get_font(S(11), bold=True)
        delta_bbox = draw.textbbox((0, 0), delta_text, font=delta_font)
        delta_w = delta_bbox[2] - delta_bbox[0]
        delta_x = x + row_width - S(6) - delta_w
        delta_y = y + (row_height - (delta_bbox[3] - delta_bbox[1])) // 2 - delta_bbox[1]
        draw.text((delta_x, delta_y), delta_text, fill=delta_color, font=delta_font)


def generate_power_index_image(rankings: List[Dict], week_of: str) -> Image.Image:
    """Generate the power index with all 32 teams in two columns."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(40)

    # Header
    title_font = get_font(S(48), bold=True)
    draw.text((margin, S(28)), "POWER INDEX", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    # Subtitle
    subtitle_font = get_font(S(16), bold=False)
    draw.text((margin, S(82)), f"Team Strength Ratings  |  {week_of}", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = S(106)
    draw.line([(margin, line_y), (margin + S(140), line_y)], fill=hex_to_rgb(PuckcastColors.AQUA), width=S(3))

    # Column headers
    header_y = line_y + S(16)
    header_font = get_font(S(11), bold=True)
    header_color = hex_to_rgb(PuckcastColors.TEXT_TERTIARY)

    col_width = (RENDER_SIZE - margin * 2 - S(20)) // 2  # Gap between columns
    col1_x = margin
    col2_x = margin + col_width + S(20)

    # Draw headers for both columns
    for col_x in [col1_x, col2_x]:
        draw.text((col_x + S(4), header_y), "RK", fill=header_color, font=header_font)
        draw.text((col_x + S(50), header_y), "TEAM", fill=header_color, font=header_font)
        draw.text((col_x + col_width - S(120), header_y), "REC", fill=header_color, font=header_font)
        draw.text((col_x + col_width - S(55), header_y), "PTS", fill=header_color, font=header_font)
        draw.text((col_x + col_width - S(20), header_y), "+/-", fill=header_color, font=header_font)

    # Draw separator line under headers
    sep_y = header_y + S(18)
    draw.line([(col1_x, sep_y), (col1_x + col_width, sep_y)], fill=(255, 255, 255, 30), width=1)
    draw.line([(col2_x, sep_y), (col2_x + col_width, sep_y)], fill=(255, 255, 255, 30), width=1)

    # Team rows
    content_y = sep_y + S(8)
    row_height = S(54)
    available_height = RENDER_SIZE - content_y - S(90)  # Footer space
    row_height = min(row_height, available_height // 16)

    # Column 1: Teams 1-16
    for i, team in enumerate(rankings[:16]):
        y = content_y + i * row_height
        draw_team_row(img, draw, team, col1_x, y, col_width, row_height)
        # Subtle separator
        if i < 15:
            draw.line(
                [(col1_x + S(40), y + row_height - 1), (col1_x + col_width - S(8), y + row_height - 1)],
                fill=(255, 255, 255, 15),
                width=1
            )

    # Column 2: Teams 17-32
    for i, team in enumerate(rankings[16:32]):
        y = content_y + i * row_height
        draw_team_row(img, draw, team, col2_x, y, col_width, row_height)
        # Subtle separator
        if i < 15:
            draw.line(
                [(col2_x + S(40), y + row_height - 1), (col2_x + col_width - S(8), y + row_height - 1)],
                fill=(255, 255, 255, 15),
                width=1
            )

    draw_footer(img)
    return img


def generate_power_rankings() -> List[Path]:
    """Generate power index graphic."""
    print("Generating Power Index graphics...")

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
