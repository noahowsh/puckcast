#!/usr/bin/env python3
"""
Team Overview Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic with circular ranking display,
league ranking bars, record breakdown, and team stats matching the website.
Uses 2x supersampling for crisp output.
"""

from __future__ import annotations

import json
import math
import sys
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List

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
POWER_INDEX_PATH = REPO_ROOT / "web" / "src" / "data" / "powerIndexSnapshot.json"
GOALIE_PATH = REPO_ROOT / "web" / "src" / "data" / "goaliePulse.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"

TEAM_NAMES = {
    "ANA": "Anaheim Ducks", "ARI": "Arizona Coyotes", "BOS": "Boston Bruins",
    "BUF": "Buffalo Sabres", "CGY": "Calgary Flames", "CAR": "Carolina Hurricanes",
    "CHI": "Chicago Blackhawks", "COL": "Colorado Avalanche", "CBJ": "Columbus Blue Jackets",
    "DAL": "Dallas Stars", "DET": "Detroit Red Wings", "EDM": "Edmonton Oilers",
    "FLA": "Florida Panthers", "LAK": "Los Angeles Kings", "MIN": "Minnesota Wild",
    "MTL": "Montréal Canadiens", "NSH": "Nashville Predators", "NJD": "New Jersey Devils",
    "NYI": "New York Islanders", "NYR": "New York Rangers", "OTT": "Ottawa Senators",
    "PHI": "Philadelphia Flyers", "PIT": "Pittsburgh Penguins", "SJS": "San Jose Sharks",
    "SEA": "Seattle Kraken", "STL": "St. Louis Blues", "TBL": "Tampa Bay Lightning",
    "TOR": "Toronto Maple Leafs", "UTA": "Utah Hockey Club", "VAN": "Vancouver Canucks",
    "VGK": "Vegas Golden Knights", "WSH": "Washington Capitals", "WPG": "Winnipeg Jets",
}

TIER_COLORS = {
    "elite": (100, 210, 255),
    "contender": (52, 211, 153),
    "playoff": (251, 191, 36),
    "bubble": (120, 120, 130),
    "lottery": (251, 113, 133),
}


def get_rank_color(rank: int) -> Tuple[int, int, int]:
    """Get color based on league rank (1-32)."""
    if rank <= 5:
        return (100, 210, 255)   # Elite - blue
    elif rank <= 10:
        return (52, 211, 153)    # Great - green
    elif rank <= 16:
        return (251, 191, 36)    # Good - amber
    elif rank <= 24:
        return (251, 146, 60)    # Average - orange
    else:
        return (251, 113, 133)   # Below avg - red


def load_data() -> tuple[Dict, Dict, List]:
    """Load all required data."""
    teams = {}
    power_index = {}
    goalies = []

    if SOCIAL_METRICS_PATH.exists():
        data = json.loads(SOCIAL_METRICS_PATH.read_text())
        for team in data.get("teams", []):
            teams[team["abbrev"]] = team

    if POWER_INDEX_PATH.exists():
        data = json.loads(POWER_INDEX_PATH.read_text())
        for team in data.get("rankings", []):
            power_index[team["abbrev"]] = team

    if GOALIE_PATH.exists():
        data = json.loads(GOALIE_PATH.read_text())
        goalies = data.get("goalies", [])

    return teams, power_index, goalies


def draw_power_ring(
    img: Image.Image,
    draw: ImageDraw.Draw,
    center_x: int,
    center_y: int,
    outer_radius: int,
    rank: int,
    tier: str,
) -> None:
    """Draw a circular power rank display with progress ring."""
    tier_color = TIER_COLORS.get(tier, TIER_COLORS["bubble"])

    # Draw background circle
    inner_radius = outer_radius - S(12)
    draw.ellipse(
        [center_x - outer_radius, center_y - outer_radius,
         center_x + outer_radius, center_y + outer_radius],
        fill=(30, 35, 50)
    )

    # Draw progress ring (32 - rank) / 32 of the circle
    progress = (33 - rank) / 32
    start_angle = -90  # Start from top
    end_angle = start_angle + (360 * progress)

    # Draw arc using polygon approximation
    points = [(center_x, center_y)]
    for angle in range(int(start_angle), int(end_angle) + 1, 2):
        rad = math.radians(angle)
        x = center_x + outer_radius * math.cos(rad)
        y = center_y + outer_radius * math.sin(rad)
        points.append((x, y))
    points.append((center_x, center_y))

    if len(points) > 2:
        overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)
        overlay_draw.polygon(points, fill=(*tier_color, 180))
        # Cut out inner circle
        overlay_draw.ellipse(
            [center_x - inner_radius, center_y - inner_radius,
             center_x + inner_radius, center_y + inner_radius],
            fill=(0, 0, 0, 0)
        )
        img_rgba = img.convert("RGBA")
        result = Image.alpha_composite(img_rgba, overlay)
        img.paste(result.convert("RGB"))

    # Draw inner circle
    draw = ImageDraw.Draw(img)
    draw.ellipse(
        [center_x - inner_radius + S(4), center_y - inner_radius + S(4),
         center_x + inner_radius - S(4), center_y + inner_radius - S(4)],
        fill=(20, 25, 40)
    )

    # Rank number
    rank_font = get_font(S(48), bold=True)
    rank_text = f"#{rank}"
    rank_bbox = draw.textbbox((0, 0), rank_text, font=rank_font)
    rank_w = rank_bbox[2] - rank_bbox[0]
    rank_h = rank_bbox[3] - rank_bbox[1]
    draw.text(
        (center_x - rank_w // 2 - rank_bbox[0], center_y - rank_h // 2 - rank_bbox[1]),
        rank_text, fill=tier_color, font=rank_font
    )


def draw_record_bar(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    width: int,
    height: int,
    wins: int,
    losses: int,
    ot: int,
) -> None:
    """Draw a W-L-OT record breakdown bar."""
    total = wins + losses + ot
    if total == 0:
        total = 1

    win_width = int(width * (wins / total))
    loss_width = int(width * (losses / total))
    ot_width = width - win_width - loss_width

    # Background
    draw.rounded_rectangle([x, y, x + width, y + height], radius=height // 2, fill=(40, 45, 60))

    # Wins (green)
    if win_width > 0:
        draw.rounded_rectangle([x, y, x + win_width, y + height], radius=height // 2, fill=(52, 211, 153))

    # Losses (red)
    if loss_width > 0:
        draw.rectangle([x + win_width, y, x + win_width + loss_width, y + height], fill=(251, 113, 133))

    # OT (amber)
    if ot_width > 0:
        draw.rounded_rectangle([x + win_width + loss_width, y, x + width, y + height], radius=height // 2, fill=(251, 191, 36))

    # Labels below
    label_font = get_font(S(10), bold=True)
    label_y = y + height + S(6)

    draw.text((x, label_y), f"{wins}W", fill=(52, 211, 153), font=label_font)

    loss_text = f"{losses}L"
    loss_bbox = draw.textbbox((0, 0), loss_text, font=label_font)
    draw.text((x + (width - (loss_bbox[2] - loss_bbox[0])) // 2, label_y), loss_text, fill=(251, 113, 133), font=label_font)

    ot_text = f"{ot}OT"
    ot_bbox = draw.textbbox((0, 0), ot_text, font=label_font)
    draw.text((x + width - (ot_bbox[2] - ot_bbox[0]), label_y), ot_text, fill=(251, 191, 36), font=label_font)


def draw_ranking_bar(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    width: int,
    height: int,
    rank: int,
    label: str,
    value: str,
) -> None:
    """Draw a league ranking bar with rank indicator."""
    rank_color = get_rank_color(rank)

    # Background bar
    draw.rounded_rectangle([x, y, x + width, y + height], radius=height // 2, fill=(40, 45, 60))

    # Filled portion based on rank (1 = full, 32 = minimal)
    fill_pct = (33 - rank) / 32
    fill_width = int(width * fill_pct)
    if fill_width > 0:
        draw.rounded_rectangle([x, y, x + fill_width, y + height], radius=height // 2, fill=(*rank_color, 180))

    # Rank number
    rank_font = get_font(S(12), bold=True)
    rank_text = f"#{rank}"
    draw.text((x + width + S(8), y - S(1)), rank_text, fill=rank_color, font=rank_font)

    # Label and value above bar
    label_font = get_font(S(11), bold=False)
    value_font = get_font(S(13), bold=True)

    draw.text((x, y - S(18)), label, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=label_font)

    value_bbox = draw.textbbox((0, 0), value, font=value_font)
    draw.text((x + width - (value_bbox[2] - value_bbox[0]), y - S(18)), value, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=value_font)


def generate_team_overview(team_abbrev: str, teams: Dict, power_index: Dict, goalies: List) -> Image.Image:
    """Generate a team overview graphic."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(40)
    team_stats = teams.get(team_abbrev, {})
    power_stats = power_index.get(team_abbrev, {})
    team_goalies = [g for g in goalies if g.get("team") == team_abbrev]

    team_name = TEAM_NAMES.get(team_abbrev, team_abbrev)
    tier = power_stats.get("tier", "bubble")
    rank = power_stats.get("rank", 16)
    rank_delta = power_stats.get("rankDelta", 0)

    # Header
    header_font = get_font(S(14), bold=True)
    draw.text((margin, S(24)), "TEAM SPOTLIGHT", fill=hex_to_rgb(PuckcastColors.AQUA), font=header_font)

    # Two-column layout: Team info (left) + Power Ring (right)
    content_y = S(56)

    # Left column: Team name and quick stats
    name_font = get_font(S(32), bold=True)
    draw.text((margin, content_y), team_name.upper(), fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=name_font)

    # Tier badge
    tier_color = TIER_COLORS.get(tier, TIER_COLORS["bubble"])
    tier_text = tier.upper()
    tier_font = get_font(S(11), bold=True)
    tier_bbox = draw.textbbox((0, 0), tier_text, font=tier_font)
    tier_w = tier_bbox[2] - tier_bbox[0]
    tier_y = content_y + S(42)
    draw_rounded_rect(draw, (margin, tier_y, margin + tier_w + S(20), tier_y + S(24)), radius=S(12), fill=(*tier_color, 40), outline=(*tier_color, 100), width=1)
    draw.text((margin + S(10), tier_y + S(5)), tier_text, fill=tier_color, font=tier_font)

    # Movement indicator
    if rank_delta != 0:
        delta_text = f"{'▲' if rank_delta > 0 else '▼'}{abs(rank_delta)}"
        delta_color = hex_to_rgb(PuckcastColors.RISING) if rank_delta > 0 else hex_to_rgb(PuckcastColors.FALLING)
        delta_x = margin + tier_w + S(36)
        draw.text((delta_x, tier_y + S(5)), delta_text, fill=delta_color, font=tier_font)

    # Right column: Power ring with logo
    ring_radius = S(80)
    ring_x = RENDER_SIZE - margin - ring_radius - S(20)
    ring_y = content_y + S(40)

    draw_power_ring(img, draw, ring_x, ring_y, ring_radius, rank, tier)

    # Team logo in center of ring
    logo_size = S(56)
    logo = get_logo(team_abbrev, logo_size)
    logo_x = ring_x - logo_size // 2
    logo_y = ring_y - logo_size // 2
    img.paste(logo, (logo_x, logo_y), logo)

    # Quick stats row
    stats_row_y = content_y + S(90)
    stat_box_w = S(100)
    stat_gap = S(12)

    quick_stats = [
        ("POINTS", str(team_stats.get("points", 0))),
        ("GOAL DIFF", f"{team_stats.get('goalDifferential', 0):+d}"),
        ("POINT %", f"{team_stats.get('pointPct', 0) * 100:.1f}%"),
    ]

    for i, (label, value) in enumerate(quick_stats):
        x = margin + i * (stat_box_w + stat_gap)
        draw_rounded_rect(draw, (x, stats_row_y, x + stat_box_w, stats_row_y + S(56)), radius=S(8), fill=(255, 255, 255, 10), outline=(255, 255, 255, 25), width=1)

        val_font = get_font(S(20), bold=True)
        val_bbox = draw.textbbox((0, 0), value, font=val_font)
        val_color = hex_to_rgb(PuckcastColors.AQUA) if "+" in value else hex_to_rgb(PuckcastColors.TEXT_PRIMARY)
        if "-" in value and "DIFF" in label:
            val_color = hex_to_rgb(PuckcastColors.FALLING)
        draw.text((x + (stat_box_w - (val_bbox[2] - val_bbox[0])) // 2, stats_row_y + S(8)), value, fill=val_color, font=val_font)

        lbl_font = get_font(S(9), bold=True)
        lbl_bbox = draw.textbbox((0, 0), label, font=lbl_font)
        draw.text((x + (stat_box_w - (lbl_bbox[2] - lbl_bbox[0])) // 2, stats_row_y + S(38)), label, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=lbl_font)

    # Record bar
    record_y = stats_row_y + S(80)
    section_font = get_font(S(12), bold=True)
    draw.text((margin, record_y), "SEASON RECORD", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=section_font)

    record_bar_y = record_y + S(24)
    wins = team_stats.get("wins", 0)
    losses = team_stats.get("losses", 0)
    ot = team_stats.get("otLosses", 0)
    draw_record_bar(draw, margin, record_bar_y, RENDER_SIZE - margin * 2, S(16), wins, losses, ot)

    # League Rankings section
    rankings_y = record_bar_y + S(60)
    draw.line([(margin, rankings_y), (RENDER_SIZE - margin, rankings_y)], fill=(255, 255, 255, 20), width=1)
    rankings_y += S(16)
    draw.text((margin, rankings_y), "LEAGUE RANKINGS", fill=hex_to_rgb(PuckcastColors.AQUA), font=section_font)

    # Calculate ranks (approximation based on value relative to league)
    bar_width = S(180)
    bar_height = S(10)
    bar_gap = S(44)
    rankings_start_y = rankings_y + S(40)

    # Two columns of rankings
    col1_x = margin
    col2_x = margin + bar_width + S(80)

    rankings = [
        # Left column
        [
            ("Offense", f"{team_stats.get('goalsForPerGame', 0):.2f} GF/G", min(32, max(1, 33 - int(team_stats.get('goalsForPerGame', 2.5) * 10)))),
            ("Defense", f"{team_stats.get('goalsAgainstPerGame', 0):.2f} GA/G", min(32, max(1, int(team_stats.get('goalsAgainstPerGame', 3) * 10)))),
            ("Shot Share", f"{team_stats.get('shotShare', 50):.1f}%", min(32, max(1, 33 - int(team_stats.get('shotShare', 50))))),
        ],
        # Right column
        [
            ("Power Play", f"{team_stats.get('powerPlayPct', 0.2) * 100:.1f}%", min(32, max(1, 33 - int(team_stats.get('powerPlayPct', 0.2) * 160)))),
            ("Penalty Kill", f"{team_stats.get('penaltyKillPct', 0.8) * 100:.1f}%", min(32, max(1, 33 - int(team_stats.get('penaltyKillPct', 0.8) * 40)))),
            ("PDO", f"{team_stats.get('pdo', 100):.1f}", min(32, max(1, 33 - int((team_stats.get('pdo', 100) - 96) * 4)))),
        ],
    ]

    for col, (col_x, col_rankings) in enumerate([(col1_x, rankings[0]), (col2_x, rankings[1])]):
        for i, (label, value, rank) in enumerate(col_rankings):
            y = rankings_start_y + i * bar_gap
            draw_ranking_bar(draw, col_x, y, bar_width, bar_height, rank, label, value)

    # Goaltending section
    goalie_y = rankings_start_y + 3 * bar_gap + S(20)
    draw.line([(margin, goalie_y), (RENDER_SIZE - margin, goalie_y)], fill=(255, 255, 255, 20), width=1)
    goalie_y += S(16)
    draw.text((margin, goalie_y), "GOALTENDING", fill=hex_to_rgb(PuckcastColors.AQUA), font=section_font)

    goalie_y += S(28)
    if team_goalies:
        for i, goalie in enumerate(team_goalies[:2]):
            g_x = margin + i * S(250)

            name = goalie.get("name", "Unknown")
            sv_pct = goalie.get("savePct", 0)
            gaa = goalie.get("gaa", 0)
            record = goalie.get("record", "0-0-0")
            trend = goalie.get("trend", "stable")

            name_font = get_font(S(16), bold=True)
            stat_font = get_font(S(12), bold=False)

            draw.text((g_x, goalie_y), name, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=name_font)

            # Trend indicator
            trend_colors = {"surging": (52, 211, 153), "hot": (52, 211, 153), "stable": (160, 160, 170), "cooling": (251, 191, 36), "cold": (251, 113, 133)}
            trend_color = trend_colors.get(trend.lower(), (160, 160, 170))
            trend_text = f"• {trend.upper()}"
            name_bbox = draw.textbbox((0, 0), name, font=name_font)
            draw.text((g_x + (name_bbox[2] - name_bbox[0]) + S(8), goalie_y + S(2)), trend_text, fill=trend_color, font=get_font(S(11), bold=True))

            draw.text((g_x, goalie_y + S(22)), f"{record}  •  .{int(sv_pct * 1000)} SV%  •  {gaa:.2f} GAA", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=stat_font)
    else:
        draw.text((margin, goalie_y), "No goalie data available", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=get_font(S(14), bold=False))

    draw_footer(img)
    return img


def generate_team_overviews(team_abbrev: Optional[str] = None) -> list[Path]:
    """Generate team overview graphics."""
    print("Generating Team Overview graphics...")

    teams, power_index, goalies = load_data()

    if not teams:
        print("  No team data found")
        return []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = []

    if team_abbrev:
        team_list = [team_abbrev.upper()]
    else:
        sorted_teams = sorted(power_index.values(), key=lambda x: x.get("rank", 99))
        team_list = [t["abbrev"] for t in sorted_teams[:3]]

    for abbrev in team_list:
        if abbrev not in teams:
            print(f"  Team '{abbrev}' not found")
            continue

        img = generate_team_overview(abbrev, teams, power_index, goalies)
        output_path = OUTPUT_DIR / f"team_overview_{abbrev.lower()}.png"
        save_high_quality(img, output_path)
        print(f"  Saved: {output_path}")
        paths.append(output_path)

    return paths


def main():
    try:
        team_abbrev = sys.argv[1] if len(sys.argv) > 1 else None
        paths = generate_team_overviews(team_abbrev)
        if paths:
            print(f"\nGenerated {len(paths)} team overview image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
