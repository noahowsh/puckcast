#!/usr/bin/env python3
"""
Player Profile Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing a goalie's
stats, performance metrics, and predictions.
Uses 2x supersampling for crisp output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any, Optional

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
GOALIE_PULSE_PATH = REPO_ROOT / "web" / "src" / "data" / "goaliePulse.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_goalie_data() -> Dict[str, Any]:
    """Load goalie pulse data."""
    if not GOALIE_PULSE_PATH.exists():
        raise FileNotFoundError(f"Goalie pulse file not found: {GOALIE_PULSE_PATH}")
    return json.loads(GOALIE_PULSE_PATH.read_text())


def get_trend_color(trend: str) -> tuple:
    """Get color for trend indicator."""
    trend_colors = {
        "surging": hex_to_rgb(PuckcastColors.RISING),
        "hot": hex_to_rgb(PuckcastColors.RISING),
        "stable": hex_to_rgb(PuckcastColors.TEXT_SECONDARY),
        "cooling": hex_to_rgb(PuckcastColors.AMBER),
        "cold": hex_to_rgb(PuckcastColors.FALLING),
        "struggling": hex_to_rgb(PuckcastColors.FALLING),
    }
    return trend_colors.get(trend.lower(), hex_to_rgb(PuckcastColors.TEXT_SECONDARY))


def draw_stat_box(
    img: Image.Image,
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    width: int,
    height: int,
    label: str,
    value: str,
    highlight: bool = False,
) -> None:
    """Draw a stat box with label and value."""
    # Create overlay for glass effect
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    if highlight:
        fill = (100, 210, 255, 25)
        border = (100, 210, 255, 60)
    else:
        fill = (255, 255, 255, 10)
        border = (255, 255, 255, 25)

    coords = (x, y, x + width, y + height)
    draw_rounded_rect(overlay_draw, coords, radius=S(10), fill=fill, outline=border, width=1)

    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)
    img.paste(result.convert("RGB"))

    # Value (large)
    value_font = get_font(S(28), bold=True)
    value_bbox = draw.textbbox((0, 0), value, font=value_font)
    value_w = value_bbox[2] - value_bbox[0]
    value_x = x + (width - value_w) // 2
    value_y = y + S(14)
    draw.text((value_x, value_y), value, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=value_font)

    # Label (small)
    label_font = get_font(S(11), bold=False)
    label_bbox = draw.textbbox((0, 0), label, font=label_font)
    label_w = label_bbox[2] - label_bbox[0]
    label_x = x + (width - label_w) // 2
    label_y = y + height - S(24)
    draw.text((label_x, label_y), label, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=label_font)


def generate_player_profile(goalie: Dict[str, Any]) -> Image.Image:
    """Generate a player profile graphic for a goalie."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(48)
    name = goalie.get("name", "Unknown")
    team = goalie.get("team", "???")
    trend = goalie.get("trend", "stable")
    note = goalie.get("note", "")

    # Header section
    title_font = get_font(S(20), bold=True)
    draw.text((margin, S(32)), "PLAYER SPOTLIGHT", fill=hex_to_rgb(PuckcastColors.AQUA), font=title_font)

    # Player name
    name_font = get_font(S(44), bold=True)
    draw.text((margin, S(60)), name.upper(), fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=name_font)

    # Team logo and info
    logo_size = S(80)
    logo = get_logo(team, logo_size)
    logo_x = RENDER_SIZE - margin - logo_size
    logo_y = S(40)
    img.paste(logo, (logo_x, logo_y), logo)

    # Team name and position
    team_font = get_font(S(16), bold=True)
    draw.text((margin, S(112)), f"{team}  •  GOALTENDER", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=team_font)

    # Trend badge
    trend_color = get_trend_color(trend)
    trend_font = get_font(S(14), bold=True)
    trend_text = trend.upper()
    trend_bbox = draw.textbbox((0, 0), trend_text, font=trend_font)
    trend_w = trend_bbox[2] - trend_bbox[0]
    trend_x = margin
    trend_y = S(145)
    # Draw trend pill
    pill_padding = S(12)
    pill_coords = (trend_x, trend_y, trend_x + trend_w + pill_padding * 2, trend_y + S(26))
    draw_rounded_rect(draw, pill_coords, radius=S(13), fill=(*trend_color, 40), outline=(*trend_color, 100), width=1)
    draw.text((trend_x + pill_padding, trend_y + S(4)), trend_text, fill=trend_color, font=trend_font)

    # Accent line
    line_y = S(188)
    draw.line([(margin, line_y), (RENDER_SIZE - margin, line_y)], fill=(255, 255, 255, 30), width=1)

    # Main stats grid (2 rows x 4 columns)
    stats_y = line_y + S(24)
    box_width = S(120)
    box_height = S(80)
    gap = S(12)
    stats_start_x = margin

    # Row 1: Core stats
    stats_row1 = [
        ("RECORD", goalie.get("record", "0-0-0")),
        ("SV%", f"{goalie.get('savePct', 0):.3f}"),
        ("GAA", f"{goalie.get('gaa', 0):.2f}"),
        ("SO", str(goalie.get("shutouts", 0))),
    ]

    for i, (label, value) in enumerate(stats_row1):
        x = stats_start_x + i * (box_width + gap)
        highlight = label in ["SV%", "GAA"]
        draw_stat_box(img, draw, x, stats_y, box_width, box_height, label, value, highlight)

    # Row 2: Advanced stats
    stats_y2 = stats_y + box_height + gap
    stats_row2 = [
        ("GSAX", f"{goalie.get('gsax', 0):+.1f}"),
        ("GP", str(goalie.get("gamesPlayed", 0))),
        ("SA/G", f"{goalie.get('shotsAgainstPerGame', 0):.1f}"),
        ("SV/G", f"{goalie.get('savesPerGame', 0):.1f}"),
    ]

    for i, (label, value) in enumerate(stats_row2):
        x = stats_start_x + i * (box_width + gap)
        highlight = label == "GSAX"
        draw_stat_box(img, draw, x, stats_y2, box_width, box_height, label, value, highlight)

    # Analysis section
    analysis_y = stats_y2 + box_height + S(32)
    section_font = get_font(S(14), bold=True)
    draw.text((margin, analysis_y), "ANALYSIS", fill=hex_to_rgb(PuckcastColors.AQUA), font=section_font)

    # Note text (wrapped)
    note_y = analysis_y + S(28)
    note_font = get_font(S(16), bold=False)

    # Simple text wrapping
    max_width = RENDER_SIZE - margin * 2
    words = note.split()
    lines = []
    current_line = ""
    for word in words:
        test_line = f"{current_line} {word}".strip()
        bbox = draw.textbbox((0, 0), test_line, font=note_font)
        if bbox[2] - bbox[0] <= max_width:
            current_line = test_line
        else:
            if current_line:
                lines.append(current_line)
            current_line = word
    if current_line:
        lines.append(current_line)

    for i, line in enumerate(lines[:3]):  # Max 3 lines
        draw.text((margin, note_y + i * S(24)), line, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=note_font)

    # Strengths & Watchouts
    sw_y = note_y + S(90)

    # Strengths
    strengths = goalie.get("strengths", [])
    if strengths:
        draw.text((margin, sw_y), "STRENGTHS", fill=hex_to_rgb(PuckcastColors.RISING), font=section_font)
        for i, strength in enumerate(strengths[:2]):
            draw.text((margin + S(16), sw_y + S(22) + i * S(22)), f"• {strength}", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=get_font(S(14), bold=False))

    # Watchouts
    watchouts = goalie.get("watchouts", [])
    if watchouts:
        wo_x = margin + S(280)
        draw.text((wo_x, sw_y), "WATCHOUTS", fill=hex_to_rgb(PuckcastColors.FALLING), font=section_font)
        for i, watchout in enumerate(watchouts[:2]):
            draw.text((wo_x + S(16), sw_y + S(22) + i * S(22)), f"• {watchout}", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=get_font(S(14), bold=False))

    # Next opponent
    next_opp = goalie.get("nextOpponent")
    if next_opp:
        opp_y = RENDER_SIZE - S(160)
        draw.line([(margin, opp_y - S(16)), (RENDER_SIZE - margin, opp_y - S(16))], fill=(255, 255, 255, 30), width=1)
        draw.text((margin, opp_y), "NEXT START", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=section_font)

        opp_logo = get_logo(next_opp, S(48))
        opp_logo_x = margin
        opp_logo_y = opp_y + S(24)
        img.paste(opp_logo, (opp_logo_x, opp_logo_y), opp_logo)

        vs_font = get_font(S(20), bold=True)
        draw.text((opp_logo_x + S(60), opp_y + S(36)), f"vs {next_opp}", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=vs_font)

        likelihood = goalie.get("startLikelihood", 0)
        like_text = f"{likelihood * 100:.0f}% start likelihood"
        draw.text((opp_logo_x + S(60), opp_y + S(62)), like_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=get_font(S(13), bold=False))

    draw_footer(img)
    return img


def generate_player_profiles(player_name: Optional[str] = None) -> list[Path]:
    """Generate player profile graphics."""
    print("Generating Player Profile graphics...")

    data = load_goalie_data()
    goalies = data.get("goalies", [])

    if not goalies:
        print("  No goalie data found")
        return []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = []

    # If specific player requested, find them
    if player_name:
        goalies = [g for g in goalies if player_name.lower() in g.get("name", "").lower()]
        if not goalies:
            print(f"  Player '{player_name}' not found")
            return []

    # Generate for top goalies or specific player
    for goalie in goalies[:3]:  # Top 3 by default
        name_slug = goalie.get("name", "unknown").lower().replace(" ", "_")
        img = generate_player_profile(goalie)
        output_path = OUTPUT_DIR / f"player_profile_{name_slug}.png"
        save_high_quality(img, output_path)
        print(f"  Saved: {output_path}")
        paths.append(output_path)

    return paths


def main():
    try:
        # Check for command line argument for specific player
        player_name = sys.argv[1] if len(sys.argv) > 1 else None
        paths = generate_player_profiles(player_name)
        if paths:
            print(f"\nGenerated {len(paths)} player profile image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
