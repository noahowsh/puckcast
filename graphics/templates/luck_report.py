#!/usr/bin/env python3
"""
Luck Report Template Generator

Creates a square (1080x1080) Instagram graphic showing luckiest and unluckiest teams.
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
    ImageDimensions,
)
from image_utils import (
    create_puckcast_background,
    draw_header,
    draw_footer,
    draw_rounded_rect,
    draw_glass_tile,
    get_logo,
    get_font,
    FontSizes,
)

REPO_ROOT = GRAPHICS_DIR.parents[0]
SOCIAL_METRICS_PATH = REPO_ROOT / "web" / "src" / "data" / "socialMetrics.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_social_metrics() -> Dict[str, Any]:
    """Load social metrics data from JSON."""
    if not SOCIAL_METRICS_PATH.exists():
        raise FileNotFoundError(f"Social metrics file not found: {SOCIAL_METRICS_PATH}")
    return json.loads(SOCIAL_METRICS_PATH.read_text())


def draw_luck_team_row(
    img: Image.Image,
    team_data: Dict[str, Any],
    rank: int,
    y_position: int,
    x_offset: int,
    width: int,
    is_lucky: bool,
) -> None:
    """Draw a team row in the luck section with bigger logos."""
    abbrev = team_data.get("abbrev", "???")
    luck_score = team_data.get("luckScore", 0)
    pdo = team_data.get("pdo", 100)

    row_height = 90  # Bigger row for bigger logos

    # Row background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if is_lucky:
        bg_color = (110, 240, 194, 18)
        border_color = (110, 240, 194, 40)
    else:
        bg_color = (255, 148, 168, 18)
        border_color = (255, 148, 168, 40)

    coords = (x_offset, y_position, x_offset + width, y_position + row_height)
    draw_rounded_rect(overlay_draw, coords, radius=12, fill=bg_color, outline=border_color, width=1)

    # Composite
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Rank
    rank_font = get_font(26, bold=True)
    rank_color = hex_to_rgb(PuckcastColors.TEXT_SECONDARY)
    draw.text((x_offset + 12, y_position + (row_height - 26) // 2), str(rank), fill=rank_color, font=rank_font)

    # Team logo - BIGGER
    logo_size = 60
    logo = get_logo(abbrev, logo_size)
    logo_x = x_offset + 45
    logo_y = y_position + (row_height - logo_size) // 2
    result.paste(logo, (logo_x, logo_y), logo)

    # Team abbreviation
    abbrev_font = get_font(22, bold=True)
    draw.text((x_offset + 115, y_position + 20), abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)

    # PDO below
    pdo_font = get_font(16, bold=False)
    pdo_text = f"PDO: {pdo:.1f}"
    draw.text((x_offset + 115, y_position + 50), pdo_text, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=pdo_font)

    # Luck score on the right
    luck_font = get_font(28, bold=True)
    if luck_score > 0:
        luck_text = f"+{luck_score:.2f}"
        luck_color = hex_to_rgb(PuckcastColors.RISING)
    else:
        luck_text = f"{luck_score:.2f}"
        luck_color = hex_to_rgb(PuckcastColors.FALLING)

    luck_bbox = draw.textbbox((0, 0), luck_text, font=luck_font)
    luck_width = luck_bbox[2] - luck_bbox[0]
    draw.text((x_offset + width - luck_width - 15, y_position + (row_height - 28) // 2), luck_text, fill=luck_color, font=luck_font)

    # Copy back
    img.paste(result.convert("RGB"))


def generate_luck_report_image(luck_report: Dict[str, Any]) -> Image.Image:
    """Generate the luck report image."""
    width, height = ImageDimensions.SQUARE

    # Create background
    img = create_puckcast_background(width, height)

    # Draw header with compact mode
    title = "LUCK REPORT"
    subtitle = "PDO & Luck Score Analysis"
    y = draw_header(img, title, subtitle, margin=50, compact=True)

    draw = ImageDraw.Draw(img)

    # Split layout - two columns with more width
    margin = 40
    col_width = (width - 2 * margin - 20) // 2
    left_x = margin
    right_x = margin + col_width + 20

    # Column headers
    section_font = get_font(32, bold=True)

    # Lucky column header
    lucky_header_color = hex_to_rgb(PuckcastColors.RISING)
    draw.text((left_x, y), "LUCKIEST", fill=lucky_header_color, font=section_font)

    # Unlucky column header
    unlucky_header_color = hex_to_rgb(PuckcastColors.FALLING)
    draw.text((right_x, y), "UNLUCKIEST", fill=unlucky_header_color, font=section_font)

    y += 50

    # Row spacing (90px row height + 8px gap = 98px)
    row_spacing = 98

    # Draw lucky teams (8 teams to fill space)
    luckiest = luck_report.get("luckiest", [])
    for i, team in enumerate(luckiest[:8], 1):
        draw_luck_team_row(img, team, i, y + (i - 1) * row_spacing, left_x, col_width, is_lucky=True)

    # Draw unlucky teams (8 teams to fill space)
    unluckiest = luck_report.get("unluckiest", [])
    for i, team in enumerate(unluckiest[:8], 1):
        draw_luck_team_row(img, team, i, y + (i - 1) * row_spacing, right_x, col_width, is_lucky=False)

    # Draw footer
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
    img.save(output_path, "PNG", quality=95)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_luck_report()
        if paths:
            print(f"\n Generated {len(paths)} luck report image(s)")
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
