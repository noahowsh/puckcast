#!/usr/bin/env python3
"""
Player Profile Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic with radar chart,
percentile bars, and skill breakdown matching the website design.
Uses 2x supersampling for crisp output.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

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

# Tier colors matching website
TIER_COLORS = {
    "elite": (100, 210, 255),       # sky-400
    "above_avg": (52, 211, 153),    # emerald-400
    "average": (160, 160, 170),     # gray
    "below_avg": (251, 191, 36),    # amber-400
    "poor": (251, 113, 133),        # rose-400
}


def get_tier_color(percentile: float) -> Tuple[int, int, int]:
    """Get tier color based on percentile."""
    if percentile >= 80:
        return TIER_COLORS["elite"]
    elif percentile >= 60:
        return TIER_COLORS["above_avg"]
    elif percentile >= 40:
        return TIER_COLORS["average"]
    elif percentile >= 20:
        return TIER_COLORS["below_avg"]
    else:
        return TIER_COLORS["poor"]


def get_tier_label(percentile: float) -> str:
    """Get tier label based on percentile."""
    if percentile >= 80:
        return "ELITE"
    elif percentile >= 60:
        return "ABOVE AVG"
    elif percentile >= 40:
        return "AVERAGE"
    elif percentile >= 20:
        return "BELOW AVG"
    else:
        return "POOR"


def load_goalie_data() -> Dict[str, Any]:
    """Load goalie pulse data."""
    if not GOALIE_PULSE_PATH.exists():
        raise FileNotFoundError(f"Goalie pulse file not found: {GOALIE_PULSE_PATH}")
    return json.loads(GOALIE_PULSE_PATH.read_text())


def calculate_percentiles(goalie: Dict, all_goalies: List[Dict]) -> Dict[str, float]:
    """Calculate percentile rankings for goalie stats."""
    # Filter goalies with minimum games
    qualified = [g for g in all_goalies if g.get("gamesPlayed", 0) >= 3]
    if not qualified:
        qualified = all_goalies

    def percentile_rank(value: float, all_values: List[float], higher_is_better: bool = True) -> float:
        sorted_vals = sorted(all_values)
        if not sorted_vals:
            return 50.0
        rank = sum(1 for v in sorted_vals if v < value) if higher_is_better else sum(1 for v in sorted_vals if v > value)
        return (rank / len(sorted_vals)) * 100

    sv_pct = goalie.get("savePct", 0)
    gaa = goalie.get("gaa", 3.0)
    gsax = goalie.get("gsax", 0)
    wins = goalie.get("wins", 0)
    shutouts = goalie.get("shutouts", 0)

    all_sv = [g.get("savePct", 0) for g in qualified]
    all_gaa = [g.get("gaa", 3.0) for g in qualified]
    all_gsax = [g.get("gsax", 0) for g in qualified]
    all_wins = [g.get("wins", 0) for g in qualified]
    all_so = [g.get("shutouts", 0) for g in qualified]

    return {
        "savePct": percentile_rank(sv_pct, all_sv, True),
        "gaa": percentile_rank(gaa, all_gaa, False),  # Lower is better
        "gsax": percentile_rank(gsax, all_gsax, True),
        "wins": percentile_rank(wins, all_wins, True),
        "shutouts": percentile_rank(shutouts, all_so, True),
    }


def draw_radar_chart(
    img: Image.Image,
    center_x: int,
    center_y: int,
    radius: int,
    values: List[float],  # 5 values from 0-100
    labels: List[str],
) -> None:
    """Draw a 5-point radar/spider chart."""
    draw = ImageDraw.Draw(img)

    # Calculate points for pentagon
    num_points = 5
    angle_offset = -90  # Start from top

    def get_point(angle_deg: float, r: float) -> Tuple[int, int]:
        angle_rad = math.radians(angle_deg)
        x = center_x + r * math.cos(angle_rad)
        y = center_y + r * math.sin(angle_rad)
        return (int(x), int(y))

    # Draw background circles at 25%, 50%, 75%, 100%
    for pct in [0.25, 0.5, 0.75, 1.0]:
        r = radius * pct
        points = []
        for i in range(num_points):
            angle = angle_offset + (360 / num_points) * i
            points.append(get_point(angle, r))
        points.append(points[0])  # Close the shape

        # Draw pentagon outline
        for j in range(len(points) - 1):
            draw.line([points[j], points[j + 1]], fill=(255, 255, 255, 25), width=1)

    # Draw axis lines
    for i in range(num_points):
        angle = angle_offset + (360 / num_points) * i
        end_point = get_point(angle, radius)
        draw.line([(center_x, center_y), end_point], fill=(255, 255, 255, 20), width=1)

    # Draw data polygon
    data_points = []
    for i, val in enumerate(values):
        angle = angle_offset + (360 / num_points) * i
        r = radius * (val / 100)
        data_points.append(get_point(angle, r))

    # Fill polygon with semi-transparent color
    if len(data_points) >= 3:
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.polygon(data_points, fill=(100, 210, 255, 60))
        img_rgba = img.convert("RGBA")
        result = Image.alpha_composite(img_rgba, overlay)
        img.paste(result.convert("RGB"))

    # Draw polygon outline
    draw = ImageDraw.Draw(img)
    for i in range(len(data_points)):
        next_i = (i + 1) % len(data_points)
        draw.line([data_points[i], data_points[next_i]], fill=(100, 210, 255, 200), width=2)

    # Draw data points
    for point in data_points:
        r = S(4)
        draw.ellipse([point[0] - r, point[1] - r, point[0] + r, point[1] + r], fill=(100, 210, 255))

    # Draw labels
    label_font = get_font(S(11), bold=True)
    label_offset = radius + S(20)
    for i, label in enumerate(labels):
        angle = angle_offset + (360 / num_points) * i
        lx, ly = get_point(angle, label_offset)
        bbox = draw.textbbox((0, 0), label, font=label_font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        draw.text((lx - lw // 2, ly - lh // 2), label, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=label_font)


def draw_percentile_bar(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    width: int,
    height: int,
    percentile: float,
    label: str,
    value: str,
) -> None:
    """Draw a horizontal percentile bar with label and value."""
    tier_color = get_tier_color(percentile)

    # Background bar
    draw.rounded_rectangle([x, y, x + width, y + height], radius=height // 2, fill=(255, 255, 255, 15))

    # Filled portion
    fill_width = int(width * (percentile / 100))
    if fill_width > 0:
        draw.rounded_rectangle([x, y, x + fill_width, y + height], radius=height // 2, fill=(*tier_color, 180))

    # Label (left)
    label_font = get_font(S(12), bold=False)
    draw.text((x, y - S(18)), label, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=label_font)

    # Value and percentile (right)
    value_font = get_font(S(14), bold=True)
    pct_font = get_font(S(11), bold=True)

    pct_text = f"{percentile:.0f}%"
    pct_bbox = draw.textbbox((0, 0), pct_text, font=pct_font)
    pct_w = pct_bbox[2] - pct_bbox[0]

    value_bbox = draw.textbbox((0, 0), value, font=value_font)
    value_w = value_bbox[2] - value_bbox[0]

    draw.text((x + width - value_w - pct_w - S(8), y - S(18)), value, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=value_font)
    draw.text((x + width - pct_w, y - S(16)), pct_text, fill=tier_color, font=pct_font)


def draw_overall_rating(
    img: Image.Image,
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    size: int,
    percentile: float,
) -> None:
    """Draw circular overall rating with colored ring."""
    tier_color = get_tier_color(percentile)
    tier_label = get_tier_label(percentile)

    # Outer ring
    ring_width = S(6)
    draw.ellipse([x, y, x + size, y + size], outline=tier_color, width=ring_width)

    # Inner fill
    inner_margin = ring_width + S(4)
    draw.ellipse(
        [x + inner_margin, y + inner_margin, x + size - inner_margin, y + size - inner_margin],
        fill=(30, 35, 50)
    )

    # Percentile number
    pct_font = get_font(S(36), bold=True)
    pct_text = f"{percentile:.0f}"
    pct_bbox = draw.textbbox((0, 0), pct_text, font=pct_font)
    pct_w = pct_bbox[2] - pct_bbox[0]
    pct_h = pct_bbox[3] - pct_bbox[1]
    draw.text(
        (x + (size - pct_w) // 2 - pct_bbox[0], y + (size - pct_h) // 2 - S(8) - pct_bbox[1]),
        pct_text, fill=tier_color, font=pct_font
    )

    # Tier label
    tier_font = get_font(S(10), bold=True)
    tier_bbox = draw.textbbox((0, 0), tier_label, font=tier_font)
    tier_w = tier_bbox[2] - tier_bbox[0]
    draw.text(
        (x + (size - tier_w) // 2, y + size // 2 + S(14)),
        tier_label, fill=tier_color, font=tier_font
    )


def generate_player_profile(goalie: Dict[str, Any], all_goalies: List[Dict]) -> Image.Image:
    """Generate a player profile graphic for a goalie."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(40)
    name = goalie.get("name", "Unknown")
    team = goalie.get("team", "???")
    trend = goalie.get("trend", "stable")

    # Calculate percentiles
    percentiles = calculate_percentiles(goalie, all_goalies)
    overall = sum(percentiles.values()) / len(percentiles)

    # Header
    header_font = get_font(S(14), bold=True)
    draw.text((margin, S(24)), "GOALIE SKILL PROFILE", fill=hex_to_rgb(PuckcastColors.AQUA), font=header_font)

    # Team logo (top right)
    logo_size = S(72)
    logo = get_logo(team, logo_size)
    logo_x = RENDER_SIZE - margin - logo_size
    logo_y = S(20)
    img.paste(logo, (logo_x, logo_y), logo)

    # Player name
    name_font = get_font(S(40), bold=True)
    draw.text((margin, S(48)), name.upper(), fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=name_font)

    # Team and position
    team_font = get_font(S(16), bold=False)
    draw.text((margin, S(96)), f"{team}  •  GOALTENDER", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=team_font)

    # Trend badge
    trend_colors = {
        "surging": hex_to_rgb(PuckcastColors.RISING),
        "hot": hex_to_rgb(PuckcastColors.RISING),
        "stable": hex_to_rgb(PuckcastColors.TEXT_SECONDARY),
        "cooling": (251, 191, 36),
        "cold": hex_to_rgb(PuckcastColors.FALLING),
    }
    trend_color = trend_colors.get(trend.lower(), hex_to_rgb(PuckcastColors.TEXT_SECONDARY))
    trend_text = trend.upper()
    trend_font = get_font(S(11), bold=True)
    trend_bbox = draw.textbbox((0, 0), trend_text, font=trend_font)
    trend_w = trend_bbox[2] - trend_bbox[0]
    pill_x = margin
    pill_y = S(126)
    draw_rounded_rect(draw, (pill_x, pill_y, pill_x + trend_w + S(20), pill_y + S(24)), radius=S(12), fill=(*trend_color[:3], 40), outline=(*trend_color[:3], 100), width=1)
    draw.text((pill_x + S(10), pill_y + S(5)), trend_text, fill=trend_color, font=trend_font)

    # Divider
    line_y = S(168)
    draw.line([(margin, line_y), (RENDER_SIZE - margin, line_y)], fill=(255, 255, 255, 30), width=1)

    # Two-column layout: Overall rating + Radar chart
    content_y = line_y + S(24)

    # Left: Overall rating circle
    rating_size = S(120)
    rating_x = margin + S(20)
    rating_y = content_y + S(20)
    draw_overall_rating(img, draw, rating_x, rating_y, rating_size, overall)

    # Tier legend below rating
    legend_y = rating_y + rating_size + S(20)
    legend_font = get_font(S(9), bold=True)
    tiers = [("ELITE", TIER_COLORS["elite"]), ("ABOVE", TIER_COLORS["above_avg"]), ("AVG", TIER_COLORS["average"]), ("BELOW", TIER_COLORS["below_avg"]), ("POOR", TIER_COLORS["poor"])]
    legend_x = margin
    for tier_name, tier_col in tiers:
        draw.ellipse([legend_x, legend_y, legend_x + S(8), legend_y + S(8)], fill=tier_col)
        draw.text((legend_x + S(12), legend_y - S(1)), tier_name, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=legend_font)
        legend_x += S(52)

    # Right: Radar chart
    radar_x = RENDER_SIZE - margin - S(200)
    radar_y = content_y + S(100)
    radar_radius = S(90)

    radar_values = [
        percentiles["savePct"],
        percentiles["gaa"],
        percentiles["gsax"],
        percentiles["wins"],
        percentiles["shutouts"],
    ]
    radar_labels = ["SV%", "GAA", "GSAX", "WINS", "SO"]
    draw_radar_chart(img, radar_x, radar_y, radar_radius, radar_values, radar_labels)

    # Key Metrics section
    metrics_y = content_y + S(230)
    section_font = get_font(S(12), bold=True)
    draw.text((margin, metrics_y), "KEY METRICS", fill=hex_to_rgb(PuckcastColors.AQUA), font=section_font)

    # Percentile bars
    bar_y = metrics_y + S(36)
    bar_width = S(220)
    bar_height = S(10)
    bar_gap = S(50)

    metrics = [
        ("Save %", f".{int(goalie.get('savePct', 0) * 1000)}", percentiles["savePct"]),
        ("GAA", f"{goalie.get('gaa', 0):.2f}", percentiles["gaa"]),
        ("GSAX", f"{goalie.get('gsax', 0):+.1f}", percentiles["gsax"]),
        ("Wins", str(goalie.get("wins", 0)), percentiles["wins"]),
    ]

    # Two columns of bars
    for i, (label, value, pct) in enumerate(metrics):
        col = i % 2
        row = i // 2
        x = margin + col * (bar_width + S(40))
        y = bar_y + row * bar_gap
        draw_percentile_bar(draw, x, y, bar_width, bar_height, pct, label, value)

    # Stats boxes
    stats_y = bar_y + 2 * bar_gap + S(30)
    draw.line([(margin, stats_y - S(16)), (RENDER_SIZE - margin, stats_y - S(16))], fill=(255, 255, 255, 20), width=1)

    box_width = S(110)
    box_height = S(70)
    box_gap = S(12)
    boxes_start = margin

    stats = [
        ("GP", str(goalie.get("gamesPlayed", 0))),
        ("RECORD", goalie.get("record", "0-0-0")),
        ("SV/G", f"{goalie.get('savesPerGame', 0):.1f}"),
        ("SA/G", f"{goalie.get('shotsAgainstPerGame', 0):.1f}"),
    ]

    for i, (label, value) in enumerate(stats):
        x = boxes_start + i * (box_width + box_gap)
        draw_rounded_rect(draw, (x, stats_y, x + box_width, stats_y + box_height), radius=S(8), fill=(255, 255, 255, 10), outline=(255, 255, 255, 25), width=1)

        # Value
        val_font = get_font(S(22), bold=True)
        val_bbox = draw.textbbox((0, 0), value, font=val_font)
        val_w = val_bbox[2] - val_bbox[0]
        draw.text((x + (box_width - val_w) // 2, stats_y + S(12)), value, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=val_font)

        # Label
        lbl_font = get_font(S(10), bold=True)
        lbl_bbox = draw.textbbox((0, 0), label, font=lbl_font)
        lbl_w = lbl_bbox[2] - lbl_bbox[0]
        draw.text((x + (box_width - lbl_w) // 2, stats_y + box_height - S(20)), label, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=lbl_font)

    # Next opponent section
    next_opp = goalie.get("nextOpponent")
    if next_opp:
        next_y = RENDER_SIZE - S(140)
        draw.line([(margin, next_y - S(12)), (RENDER_SIZE - margin, next_y - S(12))], fill=(255, 255, 255, 20), width=1)

        draw.text((margin, next_y), "NEXT START", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=section_font)

        opp_logo = get_logo(next_opp, S(44))
        img.paste(opp_logo, (margin, next_y + S(20)), opp_logo)

        vs_font = get_font(S(18), bold=True)
        draw.text((margin + S(56), next_y + S(26)), f"vs {next_opp}", fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=vs_font)

        likelihood = goalie.get("startLikelihood", 0)
        like_text = f"{likelihood * 100:.0f}% start likelihood"
        draw.text((margin + S(56), next_y + S(50)), like_text, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=get_font(S(12), bold=False))

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

    # If specific player requested
    if player_name:
        goalies_to_gen = [g for g in goalies if player_name.lower() in g.get("name", "").lower()]
        if not goalies_to_gen:
            print(f"  Player '{player_name}' not found")
            return []
    else:
        goalies_to_gen = goalies[:3]

    for goalie in goalies_to_gen:
        name_slug = goalie.get("name", "unknown").lower().replace(" ", "_")
        img = generate_player_profile(goalie, goalies)
        output_path = OUTPUT_DIR / f"player_profile_{name_slug}.png"
        save_high_quality(img, output_path)
        print(f"  Saved: {output_path}")
        paths.append(output_path)

    return paths


def main():
    try:
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
