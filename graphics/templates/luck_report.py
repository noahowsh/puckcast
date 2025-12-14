#!/usr/bin/env python3
"""
Luck Report Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing luckiest and unluckiest teams.
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


def draw_luck_row(
    img: Image.Image,
    team_data: Dict[str, Any],
    rank: int,
    y_position: int,
    x_offset: int,
    width: int,
    row_height: int,
    is_lucky: bool,
) -> None:
    """Draw a team row in the luck section."""
    abbrev = team_data.get("abbrev", "???")
    luck_score = team_data.get("luckScore", 0)
    pdo = team_data.get("pdo", 100)

    row_center_y = y_position + row_height // 2

    # Row background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if is_lucky:
        bg_color = (110, 240, 194, 20)
        border_color = (110, 240, 194, 45)
        accent_color = hex_to_rgb(PuckcastColors.RISING)
    else:
        bg_color = (255, 148, 168, 20)
        border_color = (255, 148, 168, 45)
        accent_color = hex_to_rgb(PuckcastColors.FALLING)

    coords = (x_offset, y_position, x_offset + width, y_position + row_height)
    draw_rounded_rect(overlay_draw, coords, radius=S(8), fill=bg_color, outline=border_color, width=1)

    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Rank - with proper internal padding
    rank_font = get_font(S(30), bold=True)
    rank_bbox = draw.textbbox((0, 0), str(rank), font=rank_font)
    rank_h = rank_bbox[3] - rank_bbox[1]
    draw.text((x_offset + S(12), row_center_y - rank_h // 2), str(rank), fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=rank_font)

    # Team logo
    logo_size = S(80)
    logo = get_logo(abbrev, logo_size)
    logo_x = x_offset + S(48)
    logo_y = row_center_y - logo_size // 2
    result.paste(logo, (logo_x, logo_y), logo)

    # Team abbreviation and PDO - aligned vertically
    info_x = logo_x + logo_size + S(12)
    abbrev_font = get_font(S(26), bold=True)
    pdo_font = get_font(S(16), bold=False)

    abbrev_bbox = draw.textbbox((0, 0), abbrev, font=abbrev_font)
    abbrev_h = abbrev_bbox[3] - abbrev_bbox[1]
    pdo_text = f"PDO: {pdo:.1f}"
    pdo_bbox = draw.textbbox((0, 0), pdo_text, font=pdo_font)
    pdo_h = pdo_bbox[3] - pdo_bbox[1]

    total_h = abbrev_h + S(6) + pdo_h
    text_y = row_center_y - total_h // 2

    draw.text((info_x, text_y), abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)
    draw.text((info_x, text_y + abbrev_h + S(6)), pdo_text, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=pdo_font)

    # Luck score on the right - aligned on grid
    luck_font = get_font(S(34), bold=True)
    luck_text = f"+{luck_score:.2f}" if luck_score > 0 else f"{luck_score:.2f}"
    luck_bbox = draw.textbbox((0, 0), luck_text, font=luck_font)
    luck_w = luck_bbox[2] - luck_bbox[0]
    luck_h = luck_bbox[3] - luck_bbox[1]
    draw.text((x_offset + width - luck_w - S(14), row_center_y - luck_h // 2), luck_text, fill=accent_color, font=luck_font)

    img.paste(result.convert("RGB"))


def generate_luck_report_image(luck_report: Dict[str, Any]) -> Image.Image:
    """Generate the luck report at 2x resolution."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(36)

    # Header with proper spacing (26-32px title-subtitle)
    title_font = get_font(S(56), bold=True)
    draw.text((margin, S(48)), "LUCK REPORT", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    subtitle_font = get_font(S(22), bold=False)
    draw.text((margin, S(112)), "PDO & Luck Score Analysis", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = S(146)
    draw.line([(margin, line_y), (margin + S(160), line_y)], fill=hex_to_rgb(PuckcastColors.AQUA), width=S(4))

    # Two columns - tighter gap
    col_gap = S(18)  # Reduced from 24
    col_width = (RENDER_SIZE - 2 * margin - col_gap) // 2
    left_x = margin
    right_x = margin + col_width + col_gap

    # Column headers - more space below accent line
    header_y = line_y + S(24)  # 14-18px below subtitle
    section_font = get_font(S(26), bold=True)
    draw.text((left_x, header_y), "LUCKIEST", fill=hex_to_rgb(PuckcastColors.RISING), font=section_font)
    draw.text((right_x, header_y), "UNLUCKIEST", fill=hex_to_rgb(PuckcastColors.FALLING), font=section_font)

    # Team rows - with proper internal padding
    content_y = header_y + S(36)
    row_height = S(140)  # 10-14px more internal padding
    row_gap = S(8)

    luckiest = luck_report.get("luckiest", [])
    unluckiest = luck_report.get("unluckiest", [])

    for i, team in enumerate(luckiest[:5], 1):
        y_pos = content_y + (i - 1) * (row_height + row_gap)
        draw_luck_row(img, team, i, y_pos, left_x, col_width, row_height, is_lucky=True)

    for i, team in enumerate(unluckiest[:5], 1):
        y_pos = content_y + (i - 1) * (row_height + row_gap)
        draw_luck_row(img, team, i, y_pos, right_x, col_width, row_height, is_lucky=False)

    draw_footer(img)
    return img


def generate_luck_report() -> List[Path]:
    """Generate luck report graphics."""
    print("Generating Luck Report graphics...")

    data = load_social_metrics()
    luck_report = data.get("luckReport", {})

    if not luck_report:
        print("  No luck report data found")
        return []

    img = generate_luck_report_image(luck_report)

    output_path = OUTPUT_DIR / "luck_report.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_high_quality(img, output_path)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_luck_report()
        if paths:
            print(f"\nGenerated {len(paths)} luck report image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
