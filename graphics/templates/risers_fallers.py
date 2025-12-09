#!/usr/bin/env python3
"""
Weekly Risers/Fallers Template Generator

Creates a square (1080x1080) Instagram graphic showing trending teams.
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


def draw_trend_row(
    img: Image.Image,
    team_data: Dict[str, Any],
    y_position: int,
    margin: int,
    row_height: int,
    is_riser: bool,
) -> None:
    """Draw a single team row in the trend section."""
    draw = ImageDraw.Draw(img)

    abbrev = team_data.get("abbrev", "???")
    current_rank = team_data.get("currentRank", 0)
    previous_rank = team_data.get("previousRank", 0)
    rank_delta = team_data.get("rankDelta", 0)
    goal_diff_delta = team_data.get("goalDiffDelta", 0)
    points_delta = team_data.get("pointsDelta", 0)

    # Row background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if is_riser:
        bg_color = (110, 240, 194, 15)
        accent_color = hex_to_rgb(PuckcastColors.RISING)
    else:
        bg_color = (255, 148, 168, 15)
        accent_color = hex_to_rgb(PuckcastColors.FALLING)

    coords = (margin, y_position, img.width - margin, y_position + row_height)
    draw_rounded_rect(overlay_draw, coords, radius=12, fill=bg_color)

    # Composite
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Team logo
    logo_size = 70
    logo = get_logo(abbrev, logo_size)
    logo_x = margin + 20
    logo_y = y_position + (row_height - logo_size) // 2
    result.paste(logo, (logo_x, logo_y), logo)

    # Team abbreviation
    abbrev_font = get_font(36, bold=True)
    draw.text((margin + 110, y_position + 20), abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=abbrev_font)

    # Rank change (e.g., "#25 → #4")
    rank_font = get_font(FontSizes.BODY, bold=False)
    rank_text = f"#{previous_rank} → #{current_rank}"
    draw.text((margin + 110, y_position + 60), rank_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=rank_font)

    # Big rank delta on the right
    delta_font = get_font(48, bold=True)
    if rank_delta > 0:
        delta_text = f"↑{abs(rank_delta)}"
    else:
        delta_text = f"↓{abs(rank_delta)}"

    delta_bbox = draw.textbbox((0, 0), delta_text, font=delta_font)
    delta_width = delta_bbox[2] - delta_bbox[0]
    draw.text((img.width - margin - delta_width - 30, y_position + 20), delta_text, fill=accent_color, font=delta_font)

    # Goal differential change below
    gd_font = get_font(FontSizes.CAPTION, bold=True)
    if goal_diff_delta > 0:
        gd_text = f"+{goal_diff_delta} GD"
    else:
        gd_text = f"{goal_diff_delta} GD"
    gd_bbox = draw.textbbox((0, 0), gd_text, font=gd_font)
    gd_width = gd_bbox[2] - gd_bbox[0]
    draw.text((img.width - margin - gd_width - 30, y_position + 70), gd_text, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=gd_font)

    # Copy back
    img.paste(result.convert("RGB"))


def generate_risers_fallers_image(risers: List[Dict], fallers: List[Dict]) -> Image.Image:
    """Generate the risers/fallers image."""
    width, height = ImageDimensions.SQUARE

    # Create background
    img = create_puckcast_background(width, height)

    # Draw header
    title = "TRENDING TEAMS"
    subtitle = "Weekly Rank Changes"
    y = draw_header(img, title, subtitle, margin=60)

    draw = ImageDraw.Draw(img)
    margin = 60
    row_height = 105

    # Section header - Risers
    section_font = get_font(FontSizes.HEADING, bold=True)
    draw.text((margin, y), "RISING", fill=hex_to_rgb(PuckcastColors.RISING), font=section_font)
    y += 45

    # Draw risers
    for i, team in enumerate(risers[:3]):
        draw_trend_row(img, team, y, margin, row_height, is_riser=True)
        y += row_height + 10

    y += 20

    # Section header - Fallers
    draw.text((margin, y), "FALLING", fill=hex_to_rgb(PuckcastColors.FALLING), font=section_font)
    y += 45

    # Draw fallers
    for i, team in enumerate(fallers[:3]):
        draw_trend_row(img, team, y, margin, row_height, is_riser=False)
        y += row_height + 10

    # Draw footer
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
    img.save(output_path, "PNG", quality=95)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_risers_fallers()
        if paths:
            print(f"\n Generated {len(paths)} risers/fallers image(s)")
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
