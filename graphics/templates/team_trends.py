#!/usr/bin/env python3
"""
Team Trends Template Generator

Creates a square (1080x1080) Instagram graphic showing team trend deep dives.
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
    TEAM_NAMES,
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


def draw_stat_block(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    label: str,
    value: str,
    delta: str = None,
    delta_positive: bool = True,
) -> None:
    """Draw a stat block with label and value."""
    # Value
    value_font = get_font(32, bold=True)
    draw.text((x, y), value, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=value_font)

    # Label below
    label_font = get_font(FontSizes.CAPTION, bold=False)
    draw.text((x, y + 35), label, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=label_font)

    # Delta if provided
    if delta:
        delta_font = get_font(FontSizes.SMALL, bold=True)
        delta_color = hex_to_rgb(PuckcastColors.RISING if delta_positive else PuckcastColors.FALLING)
        draw.text((x + 80, y + 5), delta, fill=delta_color, font=delta_font)


def draw_team_trend_card(
    img: Image.Image,
    team_data: Dict[str, Any],
    full_team_data: Dict[str, Any],
    y_position: int,
    margin: int,
    card_height: int,
    is_rising: bool,
) -> None:
    """Draw a detailed team trend card."""
    draw = ImageDraw.Draw(img)

    abbrev = team_data.get("abbrev", "???")
    team_name = team_data.get("team", TEAM_NAMES.get(abbrev, abbrev))
    current_rank = team_data.get("currentRank", 0)
    previous_rank = team_data.get("previousRank", 0)
    rank_delta = team_data.get("rankDelta", 0)
    points_delta = team_data.get("pointsDelta", 0)
    goal_diff_delta = team_data.get("goalDiffDelta", 0)
    trend_direction = team_data.get("trendDirection", "steady")

    # Get additional stats from full team data
    pdo = full_team_data.get("pdo", 100) if full_team_data else 100
    luck_score = full_team_data.get("totalLuckScore", 0) if full_team_data else 0
    goals_for_pg = full_team_data.get("goalsForPerGame", 0) if full_team_data else 0
    goals_against_pg = full_team_data.get("goalsAgainstPerGame", 0) if full_team_data else 0
    shot_share = full_team_data.get("shotShare", 50) if full_team_data else 50

    # Card background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if is_rising:
        bg_color = (110, 240, 194, 12)
        accent_color = hex_to_rgb(PuckcastColors.RISING)
    else:
        bg_color = (255, 148, 168, 12)
        accent_color = hex_to_rgb(PuckcastColors.FALLING)

    coords = (margin, y_position, img.width - margin, y_position + card_height)
    draw_rounded_rect(overlay_draw, coords, radius=16, fill=bg_color)

    # Composite
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Team logo (large)
    logo_size = 100
    logo = get_logo(abbrev, logo_size)
    logo_x = margin + 25
    logo_y = y_position + 25
    result.paste(logo, (logo_x, logo_y), logo)

    # Team name and rank
    name_font = get_font(32, bold=True)
    draw.text((logo_x + logo_size + 20, y_position + 25), team_name, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=name_font)

    # Rank change
    rank_font = get_font(FontSizes.BODY, bold=False)
    rank_text = f"#{previous_rank} → #{current_rank}"
    draw.text((logo_x + logo_size + 20, y_position + 60), rank_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=rank_font)

    # Big trend indicator on the right
    trend_font = get_font(60, bold=True)
    if rank_delta > 0:
        trend_text = f"↑{abs(rank_delta)}"
    else:
        trend_text = f"↓{abs(rank_delta)}"
    trend_bbox = draw.textbbox((0, 0), trend_text, font=trend_font)
    trend_width = trend_bbox[2] - trend_bbox[0]
    draw.text((img.width - margin - trend_width - 30, y_position + 30), trend_text, fill=accent_color, font=trend_font)

    # Trend label
    trend_label_font = get_font(FontSizes.CAPTION, bold=True)
    trend_label = trend_direction.upper()
    label_bbox = draw.textbbox((0, 0), trend_label, font=trend_label_font)
    label_width = label_bbox[2] - label_bbox[0]
    draw.text((img.width - margin - label_width - 30, y_position + 95), trend_label, fill=accent_color, font=trend_label_font)

    # Stats row
    stats_y = y_position + 140
    stat_width = 130

    # Points delta
    pts_delta = f"+{points_delta}" if points_delta > 0 else str(points_delta)
    draw_stat_block(draw, margin + 30, stats_y, "Points", pts_delta, None)

    # Goal diff delta
    gd_delta = f"+{goal_diff_delta}" if goal_diff_delta > 0 else str(goal_diff_delta)
    draw_stat_block(draw, margin + 30 + stat_width, stats_y, "Goal Diff", gd_delta, None)

    # GF/Game
    draw_stat_block(draw, margin + 30 + stat_width * 2, stats_y, "GF/G", f"{goals_for_pg:.2f}", None)

    # GA/Game
    draw_stat_block(draw, margin + 30 + stat_width * 3, stats_y, "GA/G", f"{goals_against_pg:.2f}", None)

    # Shot share
    draw_stat_block(draw, margin + 30 + stat_width * 4, stats_y, "Shot%", f"{shot_share:.1f}", None)

    # PDO
    pdo_delta = "Lucky" if pdo > 101 else ("Unlucky" if pdo < 99 else "Neutral")
    draw_stat_block(draw, margin + 30 + stat_width * 5, stats_y, "PDO", f"{pdo:.1f}", None)

    # Copy back
    img.paste(result.convert("RGB"))


def generate_team_trends_image(risers: List[Dict], fallers: List[Dict], teams_dict: Dict[str, Dict]) -> Image.Image:
    """Generate the team trends image."""
    width, height = ImageDimensions.SQUARE

    # Create background
    img = create_puckcast_background(width, height)

    # Draw header
    title = "TEAM TRENDS"
    subtitle = "Trending Up & Trending Down"
    y = draw_header(img, title, subtitle, margin=60)

    draw = ImageDraw.Draw(img)
    margin = 60
    card_height = 200

    # Section header - Trending Up
    section_font = get_font(FontSizes.HEADING, bold=True)
    draw.text((margin, y), "TRENDING UP", fill=hex_to_rgb(PuckcastColors.RISING), font=section_font)
    y += 45

    # Draw top riser
    if risers:
        top_riser = risers[0]
        abbrev = top_riser.get("abbrev", "")
        full_data = teams_dict.get(abbrev, {})
        draw_team_trend_card(img, top_riser, full_data, y, margin, card_height, is_rising=True)
    y += card_height + 30

    # Section header - Trending Down
    draw.text((margin, y), "TRENDING DOWN", fill=hex_to_rgb(PuckcastColors.FALLING), font=section_font)
    y += 45

    # Draw top faller
    if fallers:
        top_faller = fallers[0]
        abbrev = top_faller.get("abbrev", "")
        full_data = teams_dict.get(abbrev, {})
        draw_team_trend_card(img, top_faller, full_data, y, margin, card_height, is_rising=False)

    # Draw footer
    draw_footer(img)

    return img


def generate_team_trends() -> List[Path]:
    """Generate team trends graphics."""
    print("Generating Team Trends graphics...")

    data = load_social_metrics()
    risers = data.get("topRisers", [])
    fallers = data.get("topFallers", [])
    teams = data.get("teams", [])

    # Create lookup dict
    teams_dict = {t.get("abbrev"): t for t in teams}

    if not risers and not fallers:
        print("  No trend data found")
        return []

    img = generate_team_trends_image(risers, fallers, teams_dict)

    output_path = OUTPUT_DIR / "team_trends.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    img.save(output_path, "PNG", quality=95)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_team_trends()
        if paths:
            print(f"\n Generated {len(paths)} team trends image(s)")
    except Exception as e:
        print(f" Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
