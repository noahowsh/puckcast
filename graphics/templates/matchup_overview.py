#!/usr/bin/env python3
"""
Matchup Overview Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic with stat comparison bars,
win probability display, and model pick breakdown matching the website.
Uses 2x supersampling for crisp output.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple

from PIL import Image, ImageDraw

GRAPHICS_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(GRAPHICS_DIR))

from puckcast_brand import (
    PuckcastColors,
    hex_to_rgb,
    get_confidence_color_rgb,
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
PREDICTIONS_PATH = REPO_ROOT / "web" / "src" / "data" / "todaysPredictions.json"
STANDINGS_PATH = REPO_ROOT / "web" / "src" / "data" / "currentStandings.json"
SOCIAL_METRICS_PATH = REPO_ROOT / "web" / "src" / "data" / "socialMetrics.json"
GOALIE_PATH = REPO_ROOT / "web" / "src" / "data" / "goaliePulse.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_data() -> tuple[Dict, Dict, Dict]:
    """Load all required data."""
    predictions = {}
    teams = {}
    goalies = {}

    if PREDICTIONS_PATH.exists():
        predictions = json.loads(PREDICTIONS_PATH.read_text())

    if SOCIAL_METRICS_PATH.exists():
        data = json.loads(SOCIAL_METRICS_PATH.read_text())
        for team in data.get("teams", []):
            teams[team["abbrev"]] = team

    if GOALIE_PATH.exists():
        data = json.loads(GOALIE_PATH.read_text())
        for g in data.get("goalies", []):
            if g["team"] not in goalies:
                goalies[g["team"]] = g

    return predictions, teams, goalies


def draw_stat_comparison_bar(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    width: int,
    height: int,
    away_value: float,
    home_value: float,
    label: str,
    format_str: str = "{:.1f}",
    higher_is_better: bool = True,
) -> None:
    """Draw a stat comparison bar with values on each side."""
    # Calculate proportions
    total = away_value + home_value if (away_value + home_value) > 0 else 1
    away_pct = away_value / total
    home_pct = home_value / total

    # Determine which side is better
    if higher_is_better:
        away_better = away_value > home_value
        home_better = home_value > away_value
    else:
        away_better = away_value < home_value
        home_better = home_value < away_value

    # Colors
    away_color = (56, 189, 248) if away_better else (100, 100, 110)  # cyan-400 or gray
    home_color = (56, 189, 248) if home_better else (100, 100, 110)

    # Draw background bar
    draw.rounded_rectangle([x, y, x + width, y + height], radius=height // 2, fill=(40, 45, 60))

    # Draw away portion (left side)
    away_width = int(width * away_pct)
    if away_width > height:
        draw.rounded_rectangle([x, y, x + away_width, y + height], radius=height // 2, fill=away_color)

    # Draw home portion (right side)
    home_width = int(width * home_pct)
    if home_width > height:
        draw.rounded_rectangle([x + width - home_width, y, x + width, y + height], radius=height // 2, fill=home_color)

    # Center gap/label
    center_x = x + width // 2
    label_font = get_font(S(11), bold=True)
    label_bbox = draw.textbbox((0, 0), label, font=label_font)
    label_w = label_bbox[2] - label_bbox[0]
    label_h = label_bbox[3] - label_bbox[1]

    # Draw label background
    label_bg_w = label_w + S(16)
    label_bg_h = height + S(4)
    draw.rounded_rectangle(
        [center_x - label_bg_w // 2, y - S(2), center_x + label_bg_w // 2, y + label_bg_h - S(2)],
        radius=S(6),
        fill=(25, 30, 45)
    )
    draw.text(
        (center_x - label_w // 2, y + (height - label_h) // 2 - label_bbox[1]),
        label,
        fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY),
        font=label_font
    )

    # Value labels
    value_font = get_font(S(14), bold=True)

    # Away value (left)
    away_text = format_str.format(away_value)
    away_bbox = draw.textbbox((0, 0), away_text, font=value_font)
    away_text_color = hex_to_rgb(PuckcastColors.TEXT_PRIMARY) if away_better else hex_to_rgb(PuckcastColors.TEXT_SECONDARY)
    draw.text((x - (away_bbox[2] - away_bbox[0]) - S(8), y + (height - (away_bbox[3] - away_bbox[1])) // 2 - away_bbox[1]), away_text, fill=away_text_color, font=value_font)

    # Home value (right)
    home_text = format_str.format(home_value)
    home_bbox = draw.textbbox((0, 0), home_text, font=value_font)
    home_text_color = hex_to_rgb(PuckcastColors.TEXT_PRIMARY) if home_better else hex_to_rgb(PuckcastColors.TEXT_SECONDARY)
    draw.text((x + width + S(8), y + (height - (home_bbox[3] - home_bbox[1])) // 2 - home_bbox[1]), home_text, fill=home_text_color, font=value_font)


def draw_probability_bar(
    draw: ImageDraw.Draw,
    x: int,
    y: int,
    width: int,
    height: int,
    away_prob: float,
    home_prob: float,
) -> None:
    """Draw the win probability bar."""
    # Background
    draw.rounded_rectangle([x, y, x + width, y + height], radius=height // 2, fill=(40, 45, 60))

    # Away portion (cyan gradient effect)
    away_width = int(width * away_prob)
    if away_width > 0:
        draw.rounded_rectangle([x, y, x + away_width, y + height], radius=height // 2, fill=(6, 182, 212))  # cyan-500

    # Home portion (sky gradient effect)
    home_width = int(width * home_prob)
    if home_width > 0:
        draw.rounded_rectangle([x + width - home_width, y, x + width, y + height], radius=height // 2, fill=(56, 189, 248))  # sky-400


def generate_matchup_overview(game: Dict, teams: Dict, goalies: Dict) -> Image.Image:
    """Generate a matchup overview graphic."""
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(40)

    home = game.get("homeTeam", {})
    away = game.get("awayTeam", {})
    home_abbrev = home.get("abbrev", "???")
    away_abbrev = away.get("abbrev", "???")
    home_prob = game.get("homeWinProb", 0.5)
    away_prob = game.get("awayWinProb", 0.5)
    confidence = game.get("confidenceGrade", "C")
    edge = game.get("edge", 0)
    start_time = game.get("startTimeEt", "TBD")
    venue = game.get("venue", "")

    home_stats = teams.get(home_abbrev, {})
    away_stats = teams.get(away_abbrev, {})

    # Header
    header_font = get_font(S(14), bold=True)
    draw.text((margin, S(24)), "MATCHUP BREAKDOWN", fill=hex_to_rgb(PuckcastColors.AQUA), font=header_font)

    # Game info
    time_font = get_font(S(13), bold=False)
    draw.text((margin, S(48)), f"{start_time}  •  {venue}", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=time_font)

    # Main matchup header with logos
    matchup_y = S(80)
    logo_size = S(100)

    # Away team (left)
    away_logo = get_logo(away_abbrev, logo_size)
    away_logo_x = margin + S(20)
    img.paste(away_logo, (away_logo_x, matchup_y), away_logo)

    # Away team info
    away_name_font = get_font(S(28), bold=True)
    draw.text((away_logo_x + logo_size + S(16), matchup_y + S(20)), away_abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=away_name_font)

    away_record = f"{away_stats.get('wins', 0)}-{away_stats.get('losses', 0)}-{away_stats.get('otLosses', 0)}"
    record_font = get_font(S(14), bold=False)
    draw.text((away_logo_x + logo_size + S(16), matchup_y + S(54)), away_record, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=record_font)

    # Home team (right)
    home_logo = get_logo(home_abbrev, logo_size)
    home_logo_x = RENDER_SIZE - margin - S(20) - logo_size
    img.paste(home_logo, (home_logo_x, matchup_y), home_logo)

    # Home team info (right aligned)
    home_name_bbox = draw.textbbox((0, 0), home_abbrev, font=away_name_font)
    home_name_w = home_name_bbox[2] - home_name_bbox[0]
    draw.text((home_logo_x - S(16) - home_name_w, matchup_y + S(20)), home_abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=away_name_font)

    home_record = f"{home_stats.get('wins', 0)}-{home_stats.get('losses', 0)}-{home_stats.get('otLosses', 0)}"
    home_record_bbox = draw.textbbox((0, 0), home_record, font=record_font)
    home_record_w = home_record_bbox[2] - home_record_bbox[0]
    draw.text((home_logo_x - S(16) - home_record_w, matchup_y + S(54)), home_record, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=record_font)

    # VS / @ in center
    vs_font = get_font(S(20), bold=True)
    draw.text((RENDER_SIZE // 2 - S(8), matchup_y + S(36)), "@", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=vs_font)

    # Win probability section
    prob_y = matchup_y + logo_size + S(24)

    # Probability percentages
    prob_font = get_font(S(36), bold=True)
    away_prob_text = f"{away_prob * 100:.0f}%"
    home_prob_text = f"{home_prob * 100:.0f}%"

    away_prob_color = hex_to_rgb(PuckcastColors.AQUA) if away_prob > home_prob else hex_to_rgb(PuckcastColors.TEXT_SECONDARY)
    home_prob_color = hex_to_rgb(PuckcastColors.AQUA) if home_prob > away_prob else hex_to_rgb(PuckcastColors.TEXT_SECONDARY)

    draw.text((margin + S(40), prob_y), away_prob_text, fill=away_prob_color, font=prob_font)

    home_prob_bbox = draw.textbbox((0, 0), home_prob_text, font=prob_font)
    home_prob_w = home_prob_bbox[2] - home_prob_bbox[0]
    draw.text((RENDER_SIZE - margin - S(40) - home_prob_w, prob_y), home_prob_text, fill=home_prob_color, font=prob_font)

    # Probability bar
    bar_y = prob_y + S(50)
    bar_width = RENDER_SIZE - margin * 2 - S(80)
    bar_x = margin + S(40)
    draw_probability_bar(draw, bar_x, bar_y, bar_width, S(12), away_prob, home_prob)

    # Team comparison section
    compare_y = bar_y + S(40)
    draw.line([(margin, compare_y), (RENDER_SIZE - margin, compare_y)], fill=(255, 255, 255, 30), width=1)

    section_font = get_font(S(12), bold=True)
    compare_y += S(16)

    # Header with team abbreviations
    draw.text((margin, compare_y), away_abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=section_font)
    draw.text((RENDER_SIZE // 2 - S(50), compare_y), "TEAM COMPARISON", fill=hex_to_rgb(PuckcastColors.AQUA), font=section_font)
    home_abbrev_bbox = draw.textbbox((0, 0), home_abbrev, font=section_font)
    draw.text((RENDER_SIZE - margin - (home_abbrev_bbox[2] - home_abbrev_bbox[0]), compare_y), home_abbrev, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=section_font)

    # Stat comparison bars
    stats_y = compare_y + S(32)
    bar_width = S(280)
    bar_height = S(14)
    bar_gap = S(36)
    bar_x = (RENDER_SIZE - bar_width) // 2

    comparisons = [
        ("Points", away_stats.get("points", 0), home_stats.get("points", 0), "{:.0f}", True),
        ("Point %", away_stats.get("pointPct", 0) * 100, home_stats.get("pointPct", 0) * 100, "{:.1f}%", True),
        ("Goal Diff", away_stats.get("goalDifferential", 0) + 50, home_stats.get("goalDifferential", 0) + 50, "{:.0f}", True),  # Offset for display
        ("GF/G", away_stats.get("goalsForPerGame", 0), home_stats.get("goalsForPerGame", 0), "{:.2f}", True),
        ("GA/G", away_stats.get("goalsAgainstPerGame", 0), home_stats.get("goalsAgainstPerGame", 0), "{:.2f}", False),
        ("PP%", away_stats.get("powerPlayPct", 0) * 100, home_stats.get("powerPlayPct", 0) * 100, "{:.1f}%", True),
        ("PK%", away_stats.get("penaltyKillPct", 0) * 100, home_stats.get("penaltyKillPct", 0) * 100, "{:.1f}%", True),
    ]

    for i, (label, away_val, home_val, fmt, higher_better) in enumerate(comparisons):
        y = stats_y + i * bar_gap
        # Fix goal diff display
        if label == "Goal Diff":
            away_display = away_stats.get("goalDifferential", 0)
            home_display = home_stats.get("goalDifferential", 0)
            away_text = f"{away_display:+.0f}"
            home_text = f"{home_display:+.0f}"
            draw_stat_comparison_bar(draw, bar_x, y, bar_width, bar_height, away_val, home_val, label, "{:.0f}", higher_better)
            # Override the value display
            value_font = get_font(S(14), bold=True)
            away_better = away_display > home_display
            home_better = home_display > away_display
            away_color = hex_to_rgb(PuckcastColors.TEXT_PRIMARY) if away_better else hex_to_rgb(PuckcastColors.TEXT_SECONDARY)
            home_color = hex_to_rgb(PuckcastColors.TEXT_PRIMARY) if home_better else hex_to_rgb(PuckcastColors.TEXT_SECONDARY)
            away_bbox = draw.textbbox((0, 0), away_text, font=value_font)
            home_bbox = draw.textbbox((0, 0), home_text, font=value_font)
            # Redraw with +/- format
            draw.rectangle([bar_x - S(50), y - S(2), bar_x - S(4), y + bar_height + S(2)], fill=(10, 14, 26))
            draw.rectangle([bar_x + bar_width + S(4), y - S(2), bar_x + bar_width + S(50), y + bar_height + S(2)], fill=(10, 14, 26))
            draw.text((bar_x - (away_bbox[2] - away_bbox[0]) - S(8), y), away_text, fill=away_color, font=value_font)
            draw.text((bar_x + bar_width + S(8), y), home_text, fill=home_color, font=value_font)
        else:
            draw_stat_comparison_bar(draw, bar_x, y, bar_width, bar_height, away_val, home_val, label, fmt, higher_better)

    # Model Pick section
    pick_y = RENDER_SIZE - S(145)
    draw.line([(margin, pick_y - S(12)), (RENDER_SIZE - margin, pick_y - S(12))], fill=(255, 255, 255, 30), width=1)

    # Favorite team
    favorite = away_abbrev if away_prob > home_prob else home_abbrev
    fav_prob = max(away_prob, home_prob)
    fav_logo = get_logo(favorite, S(56))
    img.paste(fav_logo, (margin, pick_y), fav_logo)

    # Model pick label
    draw.text((margin + S(68), pick_y + S(4)), "MODEL PICK", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=section_font)
    pick_font = get_font(S(24), bold=True)
    draw.text((margin + S(68), pick_y + S(22)), favorite, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=pick_font)

    # Stats boxes (Grade, Edge, Win%)
    box_width = S(80)
    box_height = S(56)
    box_gap = S(10)
    boxes_x = RENDER_SIZE - margin - (box_width * 3 + box_gap * 2)

    # Grade box
    grade_color = get_confidence_color_rgb(confidence)
    draw_rounded_rect(draw, (boxes_x, pick_y, boxes_x + box_width, pick_y + box_height), radius=S(8), fill=(*grade_color, 40), outline=(*grade_color, 100), width=1)
    grade_font = get_font(S(26), bold=True)
    grade_bbox = draw.textbbox((0, 0), confidence, font=grade_font)
    draw.text((boxes_x + (box_width - (grade_bbox[2] - grade_bbox[0])) // 2, pick_y + S(8)), confidence, fill=grade_color, font=grade_font)
    lbl_font = get_font(S(9), bold=True)
    draw.text((boxes_x + S(22), pick_y + box_height - S(16)), "GRADE", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=lbl_font)

    # Edge box
    edge_x = boxes_x + box_width + box_gap
    draw_rounded_rect(draw, (edge_x, pick_y, edge_x + box_width, pick_y + box_height), radius=S(8), fill=(56, 189, 248, 30), outline=(56, 189, 248, 80), width=1)
    edge_text = f"{edge * 100:+.1f}%"
    edge_font = get_font(S(18), bold=True)
    edge_bbox = draw.textbbox((0, 0), edge_text, font=edge_font)
    draw.text((edge_x + (box_width - (edge_bbox[2] - edge_bbox[0])) // 2, pick_y + S(12)), edge_text, fill=(56, 189, 248), font=edge_font)
    draw.text((edge_x + S(26), pick_y + box_height - S(16)), "EDGE", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=lbl_font)

    # Win % box
    win_x = edge_x + box_width + box_gap
    draw_rounded_rect(draw, (win_x, pick_y, win_x + box_width, pick_y + box_height), radius=S(8), fill=(255, 255, 255, 10), outline=(255, 255, 255, 30), width=1)
    win_text = f"{fav_prob * 100:.0f}%"
    win_font = get_font(S(20), bold=True)
    win_bbox = draw.textbbox((0, 0), win_text, font=win_font)
    draw.text((win_x + (box_width - (win_bbox[2] - win_bbox[0])) // 2, pick_y + S(10)), win_text, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=win_font)
    draw.text((win_x + S(22), pick_y + box_height - S(16)), "WIN %", fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY), font=lbl_font)

    draw_footer(img)
    return img


def generate_matchup_overviews(game_index: Optional[int] = None) -> list[Path]:
    """Generate matchup overview graphics."""
    print("Generating Matchup Overview graphics...")

    predictions, teams, goalies = load_data()
    games = predictions.get("games", [])

    if not games:
        print("  No games found")
        return []

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    paths = []

    if game_index is not None:
        games = [games[game_index]] if game_index < len(games) else []

    for game in games[:1]:
        home = game.get("homeTeam", {}).get("abbrev", "UNK")
        away = game.get("awayTeam", {}).get("abbrev", "UNK")

        img = generate_matchup_overview(game, teams, goalies)
        output_path = OUTPUT_DIR / f"matchup_{away}_at_{home}.png"
        save_high_quality(img, output_path)
        print(f"  Saved: {output_path}")
        paths.append(output_path)

    return paths


def main():
    try:
        game_index = int(sys.argv[1]) if len(sys.argv) > 1 else None
        paths = generate_matchup_overviews(game_index)
        if paths:
            print(f"\nGenerated {len(paths)} matchup overview image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
