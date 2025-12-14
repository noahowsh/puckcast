#!/usr/bin/env python3
"""
Team Trends Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing team trend deep dives.
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
    TEAM_NAMES,
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


def draw_stat_block(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    label: str,
    value: str,
) -> None:
    """Draw a stat block with value and label."""
    value_font = get_font(S(28), bold=True)
    label_font = get_font(S(14), bold=False)

    draw.text((x, y), value, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=value_font)
    draw.text((x, y + S(32)), label, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=label_font)


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
    abbrev = team_data.get("abbrev", "???")
    team_name = team_data.get("team", TEAM_NAMES.get(abbrev, abbrev))
    current_rank = team_data.get("currentRank", 0)
    previous_rank = team_data.get("previousRank", 0)
    rank_delta = team_data.get("rankDelta", 0)
    points_delta = team_data.get("pointsDelta", 0)
    goal_diff_delta = team_data.get("goalDiffDelta", 0)
    trend_direction = team_data.get("trendDirection", "steady")

    # Additional stats
    pdo = full_team_data.get("pdo", 100) if full_team_data else 100
    goals_for_pg = full_team_data.get("goalsForPerGame", 0) if full_team_data else 0
    goals_against_pg = full_team_data.get("goalsAgainstPerGame", 0) if full_team_data else 0
    shot_share = full_team_data.get("shotShare", 50) if full_team_data else 50

    # Card background
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if is_rising:
        bg_color = (110, 240, 194, 15)
        accent_color = hex_to_rgb(PuckcastColors.RISING)
    else:
        bg_color = (255, 148, 168, 15)
        accent_color = hex_to_rgb(PuckcastColors.FALLING)

    coords = (margin, y_position, img.width - margin, y_position + card_height)
    draw_rounded_rect(overlay_draw, coords, radius=S(14), fill=bg_color)

    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    draw = ImageDraw.Draw(result)

    # Team logo
    logo_size = S(100)
    logo = get_logo(abbrev, logo_size)
    logo_x = margin + S(25)
    logo_y = y_position + S(25)
    result.paste(logo, (logo_x, logo_y), logo)

    # Team name and rank
    info_x = logo_x + logo_size + S(20)
    name_font = get_font(S(30), bold=True)
    draw.text((info_x, y_position + S(25)), team_name, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=name_font)

    rank_font = get_font(S(20), bold=False)
    rank_text = f"#{previous_rank} → #{current_rank}"
    draw.text((info_x, y_position + S(60)), rank_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=rank_font)

    # Big trend indicator on the right
    trend_font = get_font(S(56), bold=True)
    trend_text = f"↑{abs(rank_delta)}" if rank_delta > 0 else f"↓{abs(rank_delta)}"
    trend_bbox = draw.textbbox((0, 0), trend_text, font=trend_font)
    trend_w = trend_bbox[2] - trend_bbox[0]
    draw.text((img.width - margin - trend_w - S(30), y_position + S(30)), trend_text, fill=accent_color, font=trend_font)

    # Trend label
    trend_label_font = get_font(S(16), bold=True)
    trend_label = trend_direction.upper()
    label_bbox = draw.textbbox((0, 0), trend_label, font=trend_label_font)
    label_w = label_bbox[2] - label_bbox[0]
    draw.text((img.width - margin - label_w - S(30), y_position + S(90)), trend_label, fill=accent_color, font=trend_label_font)

    # Stats row
    stats_y = y_position + S(135)
    stat_spacing = S(125)

    pts_delta = f"+{points_delta}" if points_delta > 0 else str(points_delta)
    draw_stat_block(draw, margin + S(30), stats_y, "Points", pts_delta)

    gd_delta = f"+{goal_diff_delta}" if goal_diff_delta > 0 else str(goal_diff_delta)
    draw_stat_block(draw, margin + S(30) + stat_spacing, stats_y, "Goal Diff", gd_delta)

    draw_stat_block(draw, margin + S(30) + stat_spacing * 2, stats_y, "GF/G", f"{goals_for_pg:.2f}")
    draw_stat_block(draw, margin + S(30) + stat_spacing * 3, stats_y, "GA/G", f"{goals_against_pg:.2f}")
    draw_stat_block(draw, margin + S(30) + stat_spacing * 4, stats_y, "Shot%", f"{shot_share:.1f}")
    draw_stat_block(draw, margin + S(30) + stat_spacing * 5, stats_y, "PDO", f"{pdo:.1f}")

    img.paste(result.convert("RGB"))


def generate_team_trends_image(risers: List[Dict], fallers: List[Dict], teams_dict: Dict[str, Dict]) -> Image.Image:
    """Generate the team trends image at 2x resolution."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(55)

    # Header
    title_font = get_font(S(68), bold=True)
    draw.text((margin, S(45)), "TEAM TRENDS", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    subtitle_font = get_font(S(26), bold=False)
    draw.text((margin, S(120)), "Weekly Performance Analysis", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = S(165)
    draw.line([(margin, line_y), (margin + S(200), line_y)], fill=hex_to_rgb(PuckcastColors.AQUA), width=S(4))

    card_height = S(195)

    # Trending Up section
    section_font = get_font(S(28), bold=True)
    y = line_y + S(25)
    draw.text((margin, y), "TRENDING UP", fill=hex_to_rgb(PuckcastColors.RISING), font=section_font)
    y += S(38)

    if risers:
        top_riser = risers[0]
        abbrev = top_riser.get("abbrev", "")
        full_data = teams_dict.get(abbrev, {})
        draw_team_trend_card(img, top_riser, full_data, y, margin, card_height, is_rising=True)
    y += card_height + S(25)

    # Trending Down section
    draw.text((margin, y), "TRENDING DOWN", fill=hex_to_rgb(PuckcastColors.FALLING), font=section_font)
    y += S(38)

    if fallers:
        top_faller = fallers[0]
        abbrev = top_faller.get("abbrev", "")
        full_data = teams_dict.get(abbrev, {})
        draw_team_trend_card(img, top_faller, full_data, y, margin, card_height, is_rising=False)

    draw_footer(img)
    return img


def generate_team_trends() -> List[Path]:
    """Generate team trends graphics."""
    print("Generating Team Trends graphics...")

    data = load_social_metrics()
    risers = data.get("topRisers", [])
    fallers = data.get("topFallers", [])
    teams = data.get("teams", [])

    teams_dict = {t.get("abbrev"): t for t in teams}

    if not risers and not fallers:
        print("  No trend data found")
        return []

    img = generate_team_trends_image(risers, fallers, teams_dict)

    output_path = OUTPUT_DIR / "team_trends.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_high_quality(img, output_path)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_team_trends()
        if paths:
            print(f"\nGenerated {len(paths)} team trends image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
