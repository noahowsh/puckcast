#!/usr/bin/env python3
"""
Weekly Risers/Fallers Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing trending teams.
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
SOCIAL_METRICS_PATH = REPO_ROOT / "web" / "src" / "data" / "socialMetrics.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_social_metrics() -> Dict[str, Any]:
    """Load social metrics data from JSON."""
    if not SOCIAL_METRICS_PATH.exists():
        raise FileNotFoundError(f"Social metrics file not found: {SOCIAL_METRICS_PATH}")
    return json.loads(SOCIAL_METRICS_PATH.read_text())


def draw_trend_row(
    img: Image.Image,
    team_data: Dict[str, Any],
    y_position: int,
    margin: int,
    row_height: int,
    is_riser: bool,
) -> None:
    """Draw a team trend row."""
    abbrev = team_data.get("abbrev", "???")
    current_rank = team_data.get("currentRank", 0)
    previous_rank = team_data.get("previousRank", 0)
    rank_delta = team_data.get("rankDelta", 0)
    goal_diff_delta = team_data.get("goalDiffDelta", 0)

    row_center_y = y_position + row_height // 2

    # Row background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if is_riser:
        bg_color = (110, 240, 194, 22)
        border_color = (110, 240, 194, 50)
        accent_color = hex_to_rgb(PuckcastColors.RISING)
    else:
        bg_color = (255, 148, 168, 22)
        border_color = (255, 148, 168, 50)
        accent_color = hex_to_rgb(PuckcastColors.FALLING)

    coords = (margin, y_position, img.width - margin, y_position + row_height)
    draw_rounded_rect(overlay_draw, coords, radius=S(12), fill=bg_color, outline=border_color, width=1)

    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Team logo
    logo_size = S(65)
    logo = get_logo(abbrev, logo_size)
    logo_x = margin + S(16)
    logo_y = row_center_y - logo_size // 2
    result.paste(logo, (logo_x, logo_y), logo)

    # Team abbreviation and rank change
    info_x = logo_x + logo_size + S(16)
    abbrev_font = get_font(S(30), bold=True)
    rank_font = get_font(S(16), bold=False)

    abbrev_bbox = draw.textbbox((0, 0), abbrev, font=abbrev_font)
    abbrev_h = abbrev_bbox[3] - abbrev_bbox[1]
    rank_text = f"#{previous_rank} → #{current_rank}"
    rank_bbox = draw.textbbox((0, 0), rank_text, font=rank_font)
    rank_h = rank_bbox[3] - rank_bbox[1]

    total_h = abbrev_h + S(6) + rank_h
    text_y = row_center_y - total_h // 2

    draw.text((info_x, text_y), abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)
    draw.text((info_x, text_y + abbrev_h + S(6)), rank_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=rank_font)

    # Rank delta on the right
    delta_font = get_font(S(42), bold=True)
    delta_text = f"↑{abs(rank_delta)}" if rank_delta > 0 else f"↓{abs(rank_delta)}"
    delta_bbox = draw.textbbox((0, 0), delta_text, font=delta_font)
    delta_w = delta_bbox[2] - delta_bbox[0]
    delta_h = delta_bbox[3] - delta_bbox[1]

    gd_font = get_font(S(14), bold=True)
    gd_text = f"+{goal_diff_delta} GD" if goal_diff_delta > 0 else f"{goal_diff_delta} GD"
    gd_bbox = draw.textbbox((0, 0), gd_text, font=gd_font)
    gd_w = gd_bbox[2] - gd_bbox[0]
    gd_h = gd_bbox[3] - gd_bbox[1]

    right_x = img.width - margin - max(delta_w, gd_w) - S(20)
    total_right_h = delta_h + S(4) + gd_h
    right_y = row_center_y - total_right_h // 2

    draw.text((right_x, right_y), delta_text, fill=accent_color, font=delta_font)
    draw.text((right_x + (delta_w - gd_w) // 2, right_y + delta_h + S(4)), gd_text, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=gd_font)

    img.paste(result.convert("RGB"))


def generate_risers_fallers_image(risers: List[Dict], fallers: List[Dict]) -> Image.Image:
    """Generate the risers/fallers image at 2x resolution."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(55)

    # Header
    title_font = get_font(S(68), bold=True)
    draw.text((margin, S(45)), "TRENDING TEAMS", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    subtitle_font = get_font(S(26), bold=False)
    draw.text((margin, S(120)), "Weekly Rank Changes", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = S(165)
    draw.line([(margin, line_y), (margin + S(220), line_y)], fill=hex_to_rgb(PuckcastColors.AQUA), width=S(4))

    row_height = S(100)
    row_gap = S(10)

    # Risers section
    section_font = get_font(S(28), bold=True)
    y = line_y + S(22)
    draw.text((margin, y), "RISING", fill=hex_to_rgb(PuckcastColors.RISING), font=section_font)
    y += S(38)

    for team in risers[:3]:
        draw_trend_row(img, team, y, margin, row_height, is_riser=True)
        y += row_height + row_gap

    # Fallers section
    y += S(12)
    draw.text((margin, y), "FALLING", fill=hex_to_rgb(PuckcastColors.FALLING), font=section_font)
    y += S(38)

    for team in fallers[:3]:
        draw_trend_row(img, team, y, margin, row_height, is_riser=False)
        y += row_height + row_gap

    draw_footer(img)
    return img


def generate_risers_fallers() -> List[Path]:
    """Generate risers/fallers graphics."""
    print("Generating Risers/Fallers graphics...")

    data = load_social_metrics()
    risers = data.get("topRisers", [])
    fallers = data.get("topFallers", [])

    if not risers and not fallers:
        print("  No trend data found")
        return []

    img = generate_risers_fallers_image(risers, fallers)

    output_path = OUTPUT_DIR / "risers_fallers.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_high_quality(img, output_path)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_risers_fallers()
        if paths:
            print(f"\nGenerated {len(paths)} risers/fallers image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
