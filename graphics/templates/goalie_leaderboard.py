#!/usr/bin/env python3
"""
Goalie Leaderboard Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing top goalies by GSAX.
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
GOALIE_PULSE_PATH = REPO_ROOT / "web" / "src" / "data" / "goaliePulse.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_goalie_data() -> Dict[str, Any]:
    """Load goalie pulse data from JSON."""
    if not GOALIE_PULSE_PATH.exists():
        raise FileNotFoundError(f"Goalie pulse file not found: {GOALIE_PULSE_PATH}")
    return json.loads(GOALIE_PULSE_PATH.read_text())


def draw_goalie_row(
    img: Image.Image,
    draw: ImageDraw.Draw,
    goalie: Dict[str, Any],
    rank: int,
    y_position: int,
    margin: int,
    row_height: int,
) -> None:
    """Draw a goalie row with clean layout and strict column grid."""
    name = goalie.get("name", "Unknown")
    team = goalie.get("team", "???")
    gsax = goalie.get("gsax", 0)
    save_pct = goalie.get("savePct", 0)
    games = goalie.get("gamesPlayed", 0)

    row_center_y = y_position + row_height // 2
    is_top3 = rank <= 3

    # Rank - with 16-18px internal padding
    rank_font = get_font(S(28), bold=True)
    rank_color = hex_to_rgb(PuckcastColors.AQUA) if is_top3 else hex_to_rgb(PuckcastColors.TEXT_TERTIARY)
    rank_bbox = draw.textbbox((0, 0), str(rank), font=rank_font)
    rank_h = rank_bbox[3] - rank_bbox[1]
    draw.text((margin + S(4), row_center_y - rank_h // 2), str(rank), fill=rank_color, font=rank_font)

    # Team logo
    logo_size = S(72)  # Slightly larger for better fill
    logo = get_logo(team, logo_size)
    logo_x = margin + S(44)
    logo_y = row_center_y - logo_size // 2
    img.paste(logo, (logo_x, logo_y), logo)

    # Goalie name and team
    info_x = logo_x + logo_size + S(16)
    name_font = get_font(S(26), bold=True)
    team_font = get_font(S(15), bold=False)

    name_bbox = draw.textbbox((0, 0), name, font=name_font)
    name_h = name_bbox[3] - name_bbox[1]
    team_bbox = draw.textbbox((0, 0), team, font=team_font)
    team_h = team_bbox[3] - team_bbox[1]

    total_h = name_h + S(6) + team_h
    text_y = row_center_y - total_h // 2

    draw.text((info_x, text_y), name, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=name_font)
    draw.text((info_x, text_y + name_h + S(6)), team, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=team_font)

    # Stats on strict column grid - fixed positions from right edge
    label_font = get_font(S(12), bold=False)
    value_y_offset = S(16)  # Consistent baseline for all values
    label_y_offset = S(12)  # Consistent offset for labels below values

    # Column positions - strict grid with equal spacing
    col_gp_x = img.width - margin - S(60)      # GP column (rightmost)
    col_sv_x = img.width - margin - S(160)     # SV% column
    col_gsax_x = img.width - margin - S(280)   # GSAX column (leftmost stat)

    # GSAX
    gsax_font = get_font(S(24), bold=True)
    gsax_text = f"+{gsax:.1f}" if gsax > 0 else f"{gsax:.1f}"
    gsax_color = hex_to_rgb(PuckcastColors.RISING) if gsax > 0 else hex_to_rgb(PuckcastColors.FALLING)
    draw.text((col_gsax_x, row_center_y - value_y_offset), gsax_text, fill=gsax_color, font=gsax_font)
    draw.text((col_gsax_x, row_center_y + label_y_offset), "GSAX", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=label_font)

    # SV%
    sv_font = get_font(S(22), bold=True)
    sv_text = f".{int(save_pct * 1000)}"
    draw.text((col_sv_x, row_center_y - value_y_offset), sv_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=sv_font)
    draw.text((col_sv_x, row_center_y + label_y_offset), "SV%", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=label_font)

    # GP
    gp_font = get_font(S(22), bold=True)
    draw.text((col_gp_x, row_center_y - value_y_offset), str(games), fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=gp_font)
    draw.text((col_gp_x, row_center_y + label_y_offset), "GP", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=label_font)


def generate_goalie_leaderboard_image(goalies: List[Dict]) -> Image.Image:
    """Generate the goalie leaderboard at 2x resolution."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(48)

    # Header with proper top padding (18-24px more)
    title_font = get_font(S(54), bold=True)
    draw.text((margin, S(56)), "GOALIE LEADERS", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    # Subtitle - 22-26px below title for clear hierarchy
    subtitle_font = get_font(S(20), bold=False)
    draw.text((margin, S(118)), "Top Goalies by Goals Saved Above Expected", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = S(152)
    draw.line([(margin, line_y), (margin + S(160), line_y)], fill=hex_to_rgb(PuckcastColors.AQUA), width=S(4))

    # Goalie rows - consistent height with 16-18px internal padding
    content_y = line_y + S(20)
    row_height = S(108)  # Taller rows for proper internal padding
    row_gap = S(6)  # Consistent spacing between rows

    for i, goalie in enumerate(goalies[:8], 1):
        y_pos = content_y + (i - 1) * (row_height + row_gap)
        draw_goalie_row(img, draw, goalie, i, y_pos, margin, row_height)

    draw_footer(img)
    return img


def generate_goalie_leaderboard() -> List[Path]:
    """Generate goalie leaderboard graphics."""
    print("Generating Goalie Leaderboard graphics...")

    data = load_goalie_data()
    goalies = data.get("goalies", [])

    if not goalies:
        print("  No goalie data found")
        return []

    goalies_sorted = sorted(goalies, key=lambda g: g.get("gsax", 0), reverse=True)
    img = generate_goalie_leaderboard_image(goalies_sorted)

    output_path = OUTPUT_DIR / "goalie_leaderboard.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_high_quality(img, output_path)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_goalie_leaderboard()
        if paths:
            print(f"\nGenerated {len(paths)} goalie leaderboard image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
