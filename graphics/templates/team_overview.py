#!/usr/bin/env python3
"""
Team Overview Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing a detailed
breakdown of a specific team's stats, ranking, and performance.
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
STANDINGS_PATH = REPO_ROOT / "web" / "src" / "data" / "currentStandings.json"
POWER_INDEX_PATH = REPO_ROOT / "web" / "src" / "data" / "powerIndexSnapshot.json"
GOALIE_PATH = REPO_ROOT / "web" / "src" / "data" / "goaliePulse.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"

# Team full names
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
    "contender": (80, 220, 160),
    "playoff": (255, 200, 100),
    "bubble": (120, 120, 130),
    "lottery": (255, 100, 120),
}


def load_data() -> tuple[Dict, Dict, list]:
    """Load all required data."""
    standings = {}
    power_index = {}
    goalies = []

    if STANDINGS_PATH.exists():
        data = json.loads(STANDINGS_PATH.read_text())
        for team in data.get("teams", []):
            standings[team["abbrev"]] = team

    if POWER_INDEX_PATH.exists():
        data = json.loads(POWER_INDEX_PATH.read_text())
        for team in data.get("rankings", []):
            power_index[team["abbrev"]] = team

    if GOALIE_PATH.exists():
        data = json.loads(GOALIE_PATH.read_text())
        goalies = data.get("goalies", [])

    return standings, power_index, goalies


def draw_stat_row(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    width: int,
    label: str,
    value: str,
    highlight: bool = False,
) -> None:
    """Draw a stat row with label and value."""
    label_font = get_font(S(14), bold=False)
    value_font = get_font(S(18), bold=True)

    # Label
    draw.text((x, y), label, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=label_font)

    # Value (right aligned)
    val_bbox = draw.textbbox((0, 0), value, font=value_font)
    val_w = val_bbox[2] - val_bbox[0]
    val_color = hex_to_rgb(PuckcastColors.AQUA) if highlight else hex_to_rgb(PuckcastColors.TEXT_PRIMARY)
    draw.text((x + width - val_w, y), value, fill=val_color, font=value_font)


def generate_team_overview(team_abbrev: str, standings: Dict, power_index: Dict, goalies: list) -> Image.Image:
    """Generate a team overview graphic."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(48)
    team_stats = standings.get(team_abbrev, {})
    power_stats = power_index.get(team_abbrev, {})
    team_goalies = [g for g in goalies if g.get("team") == team_abbrev]

    team_name = TEAM_NAMES.get(team_abbrev, team_abbrev)
    tier = power_stats.get("tier", "bubble")
    tier_color = TIER_COLORS.get(tier, TIER_COLORS["bubble"])

    # Header
    header_font = get_font(S(16), bold=True)
    draw.text((margin, S(28)), "TEAM SPOTLIGHT", fill=hex_to_rgb(PuckcastColors.AQUA), font=header_font)

    # Team logo (large, centered)
    logo_size = S(140)
    logo = get_logo(team_abbrev, logo_size)
    logo_x = (RENDER_SIZE - logo_size) // 2
    logo_y = S(60)
    img.paste(logo, (logo_x, logo_y), logo)

    # Team name
    name_font = get_font(S(36), bold=True)
    name_bbox = draw.textbbox((0, 0), team_name.upper(), font=name_font)
    name_w = name_bbox[2] - name_bbox[0]
    draw.text(((RENDER_SIZE - name_w) // 2, logo_y + logo_size + S(12)), team_name.upper(), fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=name_font)

    # Tier badge
    tier_y = logo_y + logo_size + S(56)
    tier_text = tier.upper()
    tier_font = get_font(S(14), bold=True)
    tier_bbox = draw.textbbox((0, 0), tier_text, font=tier_font)
    tier_w = tier_bbox[2] - tier_bbox[0]
    tier_x = (RENDER_SIZE - tier_w - S(24)) // 2

    pill_coords = (tier_x, tier_y, tier_x + tier_w + S(24), tier_y + S(28))
    draw_rounded_rect(draw, pill_coords, radius=S(14), fill=(*tier_color, 50), outline=(*tier_color, 120), width=1)
    draw.text((tier_x + S(12), tier_y + S(5)), tier_text, fill=tier_color, font=tier_font)

    # Power Index rank
    rank = power_stats.get("rank", "?")
    rank_delta = power_stats.get("rankDelta", 0)
    rank_y = tier_y + S(44)

    rank_font = get_font(S(14), bold=False)
    rank_num_font = get_font(S(24), bold=True)
    rank_text = f"#{rank}"
    rank_bbox = draw.textbbox((0, 0), rank_text, font=rank_num_font)
    rank_w = rank_bbox[2] - rank_bbox[0]

    # "POWER INDEX" label
    pi_label = "POWER INDEX"
    pi_bbox = draw.textbbox((0, 0), pi_label, font=rank_font)
    pi_w = pi_bbox[2] - pi_bbox[0]

    total_rank_w = pi_w + S(8) + rank_w
    if rank_delta != 0:
        delta_text = f"+{rank_delta}" if rank_delta > 0 else str(rank_delta)
        delta_font = get_font(S(14), bold=True)
        delta_bbox = draw.textbbox((0, 0), delta_text, font=delta_font)
        total_rank_w += S(8) + (delta_bbox[2] - delta_bbox[0])

    start_x = (RENDER_SIZE - total_rank_w) // 2
    draw.text((start_x, rank_y + S(4)), pi_label, fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=rank_font)
    draw.text((start_x + pi_w + S(8), rank_y), rank_text, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=rank_num_font)

    if rank_delta != 0:
        delta_color = hex_to_rgb(PuckcastColors.RISING) if rank_delta > 0 else hex_to_rgb(PuckcastColors.FALLING)
        draw.text((start_x + pi_w + S(8) + rank_w + S(8), rank_y + S(6)), delta_text, fill=delta_color, font=delta_font)

    # Stats sections
    stats_y = rank_y + S(50)
    draw.line([(margin, stats_y), (RENDER_SIZE - margin, stats_y)], fill=(255, 255, 255, 30), width=1)

    # Two-column stats layout
    col_width = S(200)
    col1_x = margin + S(40)
    col2_x = RENDER_SIZE - margin - col_width - S(40)
    row_height = S(32)

    section_y = stats_y + S(20)

    # Left column: Record stats
    section_font = get_font(S(12), bold=True)
    draw.text((col1_x, section_y), "RECORD", fill=hex_to_rgb(PuckcastColors.AQUA), font=section_font)

    record = f"{team_stats.get('wins', 0)}-{team_stats.get('losses', 0)}-{team_stats.get('ot', 0)}"
    points = team_stats.get('points', 0)
    gp = team_stats.get('gamesPlayed', 0)
    pt_pct = team_stats.get('pointPctg', 0) * 100

    left_stats = [
        ("Record", record, True),
        ("Points", str(points), True),
        ("Games Played", str(gp), False),
        ("Point %", f"{pt_pct:.1f}%", False),
    ]

    for i, (label, value, highlight) in enumerate(left_stats):
        draw_stat_row(draw, col1_x, section_y + S(24) + i * row_height, col_width, label, value, highlight)

    # Right column: Performance stats
    draw.text((col2_x, section_y), "PERFORMANCE", fill=hex_to_rgb(PuckcastColors.AQUA), font=section_font)

    gf = team_stats.get('goalsForPerGame', 0)
    ga = team_stats.get('goalsAgainstPerGame', 0)
    diff = team_stats.get('goalDifferential', 0)
    pp = team_stats.get('powerPlayPct', 0) * 100
    pk = team_stats.get('penaltyKillPct', 0) * 100

    right_stats = [
        ("Goals For/G", f"{gf:.2f}", False),
        ("Goals Against/G", f"{ga:.2f}", False),
        ("Goal Diff", f"{diff:+d}", diff > 0),
        ("PP%", f"{pp:.1f}%", False),
        ("PK%", f"{pk:.1f}%", False),
    ]

    for i, (label, value, highlight) in enumerate(right_stats):
        draw_stat_row(draw, col2_x, section_y + S(24) + i * row_height, col_width, label, value, highlight)

    # Goaltending section
    goalie_y = section_y + S(24) + max(len(left_stats), len(right_stats)) * row_height + S(32)
    draw.line([(margin, goalie_y), (RENDER_SIZE - margin, goalie_y)], fill=(255, 255, 255, 30), width=1)

    goalie_y += S(16)
    draw.text((margin + S(40), goalie_y), "GOALTENDING", fill=hex_to_rgb(PuckcastColors.AQUA), font=section_font)

    if team_goalies:
        goalie_y += S(28)
        for i, goalie in enumerate(team_goalies[:2]):  # Top 2 goalies
            g_x = margin + S(40) + i * S(260)

            name = goalie.get("name", "Unknown")
            sv_pct = goalie.get("savePct", 0)
            gaa = goalie.get("gaa", 0)
            record = goalie.get("record", "0-0-0")

            name_font = get_font(S(16), bold=True)
            stat_font = get_font(S(13), bold=False)

            draw.text((g_x, goalie_y), name, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=name_font)
            draw.text((g_x, goalie_y + S(22)), f"{record}  •  .{int(sv_pct * 1000)} SV%  •  {gaa:.2f} GAA", fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=stat_font)
    else:
        goalie_y += S(28)
        draw.text((margin + S(40), goalie_y), "No goalie data available", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=get_font(S(14), bold=False))

    draw_footer(img)
    return img


def generate_team_overviews(team_abbrev: Optional[str] = None) -> list[Path]:
    """Generate team overview graphics."""
    print("Generating Team Overview graphics...")

    standings, power_index, goalies = load_data()

    if not standings:
        print("  No standings data found")
        return []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = []

    # Generate for specific team or top teams
    if team_abbrev:
        teams = [team_abbrev.upper()]
    else:
        # Default to top 3 in power index
        sorted_teams = sorted(power_index.values(), key=lambda x: x.get("rank", 99))
        teams = [t["abbrev"] for t in sorted_teams[:3]]

    for abbrev in teams:
        if abbrev not in standings:
            print(f"  Team '{abbrev}' not found in standings")
            continue

        img = generate_team_overview(abbrev, standings, power_index, goalies)
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
