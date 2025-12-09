#!/usr/bin/env python3
"""
Edge Posts Template Generator - Premium Instagram Design

Creates a square (1080x1080) Instagram graphic showing today's top predictions.
Uses 2x supersampling for crisp output.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

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
    S,  # Scale function for supersampling
    RENDER_SIZE,
)

REPO_ROOT = GRAPHICS_DIR.parents[0]
PREDICTIONS_PATH = REPO_ROOT / "web" / "src" / "data" / "todaysPredictions.json"
OUTPUT_DIR = GRAPHICS_DIR / "output"


def load_predictions() -> Dict[str, Any]:
    """Load today's predictions from JSON."""
    if not PREDICTIONS_PATH.exists():
        raise FileNotFoundError(f"Predictions file not found: {PREDICTIONS_PATH}")
    return json.loads(PREDICTIONS_PATH.read_text())


def draw_prediction_row(
    img: Image.Image,
    draw: ImageDraw.Draw,
    game: Dict[str, Any],
    y_position: int,
    margin: int,
    row_height: int,
) -> None:
    """Draw a single prediction row with large logos and clean layout."""
    away_abbrev = game.get("awayTeam", {}).get("abbrev", "???")
    home_abbrev = game.get("homeTeam", {}).get("abbrev", "???")
    home_prob = game.get("homeWinProb", 0.5)
    away_prob = game.get("awayWinProb", 0.5)
    confidence = game.get("confidenceGrade", "C")
    start_time = game.get("startTimeEt", "TBD")
    model_favorite = game.get("modelFavorite", "home")

    # Determine favorite team and probability
    if model_favorite == "home":
        pick_abbrev = home_abbrev
        pick_prob = home_prob
    else:
        pick_abbrev = away_abbrev
        pick_prob = away_prob

    # Row center for vertical alignment
    row_center_y = y_position + row_height // 2

    # Large team logos (100px at 1x = 200px at 2x)
    logo_size = S(90)
    logo_y = row_center_y - logo_size // 2

    # Away team logo
    away_logo = get_logo(away_abbrev, logo_size)
    logo_x = margin
    img.paste(away_logo, (logo_x, logo_y), away_logo)

    # "at" text between logos
    at_font = get_font(S(24), bold=False)
    at_x = logo_x + logo_size + S(15)
    at_bbox = draw.textbbox((0, 0), "@", font=at_font)
    at_height = at_bbox[3] - at_bbox[1]
    draw.text(
        (at_x, row_center_y - at_height // 2 - S(4)),
        "@",
        fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY),
        font=at_font,
    )

    # Home team logo
    home_logo = get_logo(home_abbrev, logo_size)
    home_logo_x = at_x + S(35)
    img.paste(home_logo, (home_logo_x, logo_y), home_logo)

    # Game info - matchup and time (vertically centered)
    info_x = home_logo_x + logo_size + S(20)

    # Matchup text (larger, bold)
    matchup_font = get_font(S(28), bold=True)
    matchup_text = f"{away_abbrev} @ {home_abbrev}"
    matchup_bbox = draw.textbbox((0, 0), matchup_text, font=matchup_font)
    matchup_height = matchup_bbox[3] - matchup_bbox[1]

    # Time text (smaller)
    time_font = get_font(S(20), bold=False)
    time_bbox = draw.textbbox((0, 0), start_time, font=time_font)
    time_height = time_bbox[3] - time_bbox[1]

    # Stack matchup and time, centered vertically
    total_text_height = matchup_height + S(8) + time_height
    text_start_y = row_center_y - total_text_height // 2

    draw.text(
        (info_x, text_start_y),
        matchup_text,
        fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY),
        font=matchup_font,
    )
    draw.text(
        (info_x, text_start_y + matchup_height + S(8)),
        start_time,
        fill=hex_to_rgb(PuckcastColors.TEXT_TERTIARY),
        font=time_font,
    )

    # Right side: Confidence grade badge + Win probability
    grade_color = get_confidence_color_rgb(confidence)

    # Confidence grade circle/badge - BIGGER for legibility
    badge_size = S(70)
    badge_x = img.width - margin - badge_size
    badge_y = row_center_y - badge_size // 2

    # Draw circular badge background
    draw.ellipse(
        [badge_x, badge_y, badge_x + badge_size, badge_y + badge_size],
        fill=grade_color,
    )

    # Grade letter in badge - LARGER font, dark text for contrast on light bg
    grade_font = get_font(S(38), bold=True)
    grade_bbox = draw.textbbox((0, 0), confidence, font=grade_font)
    grade_w = grade_bbox[2] - grade_bbox[0]
    grade_h = grade_bbox[3] - grade_bbox[1]
    # Center properly: account for font baseline offset
    grade_x = badge_x + (badge_size - grade_w) // 2
    grade_y = badge_y + (badge_size - grade_h) // 2 - S(2)
    # Dark text for better contrast on colored backgrounds
    draw.text(
        (grade_x, grade_y),
        confidence,
        fill=(20, 20, 30),  # Dark color for legibility
        font=grade_font,
    )

    # Win probability (large, next to badge)
    prob_font = get_font(S(44), bold=True)
    prob_text = f"{pick_prob * 100:.0f}%"
    prob_bbox = draw.textbbox((0, 0), prob_text, font=prob_font)
    prob_w = prob_bbox[2] - prob_bbox[0]
    prob_h = prob_bbox[3] - prob_bbox[1]
    prob_x = badge_x - prob_w - S(25)

    # Position probability higher to make room for pick label
    draw.text(
        (prob_x, row_center_y - prob_h // 2 - S(14)),
        prob_text,
        fill=grade_color,
        font=prob_font,
    )

    # Pick label (team abbrev under probability) - MORE SPACING
    pick_font = get_font(S(18), bold=True)
    pick_label = f"Pick: {pick_abbrev}"
    pick_bbox = draw.textbbox((0, 0), pick_label, font=pick_font)
    pick_w = pick_bbox[2] - pick_bbox[0]

    draw.text(
        (prob_x + (prob_w - pick_w) // 2, row_center_y + S(20)),
        pick_label,
        fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY),
        font=pick_font,
    )


def generate_edge_posts_image(games: List[Dict], date_str: str) -> Image.Image:
    """Generate the predictions image at 2x resolution."""
    # Create background at render size (2160x2160)
    img = create_puckcast_background()
    draw = ImageDraw.Draw(img)

    margin = S(60)

    # Header - Title
    title_font = get_font(S(72), bold=True)
    title = "TODAY'S PICKS"
    title_y = S(50)
    draw.text((margin, title_y), title, fill=hex_to_rgb(PuckcastColors.TEXT_PRIMARY), font=title_font)

    # Subtitle
    subtitle_font = get_font(S(28), bold=False)
    subtitle = f"Model Predictions • {date_str}"
    subtitle_y = title_y + S(80)
    draw.text((margin, subtitle_y), subtitle, fill=hex_to_rgb(PuckcastColors.TEXT_SECONDARY), font=subtitle_font)

    # Accent line
    line_y = subtitle_y + S(50)
    line_color = hex_to_rgb(PuckcastColors.AQUA)
    draw.line([(margin, line_y), (margin + S(200), line_y)], fill=line_color, width=S(4))

    # Content area - 6 games with comfortable spacing
    content_start_y = line_y + S(35)
    row_height = S(120)
    row_gap = S(12)

    # Draw prediction rows (6 games fits well with header and footer)
    for i, game in enumerate(games[:6]):
        y_pos = content_start_y + i * (row_height + row_gap)
        draw_prediction_row(img, draw, game, y_pos, margin, row_height)

    # Footer
    draw_footer(img, margin=S(50))

    return img


def generate_edge_posts() -> List[Path]:
    """Generate edge posts graphics."""
    print("Generating Today's Picks graphics...")

    data = load_predictions()
    games = data.get("games", [])

    if not games:
        print("  No games found for today")
        return []

    # Sort by confidence (A > B > C) then by probability
    grade_order = {"A+": 0, "A": 1, "A-": 2, "B+": 3, "B": 4, "B-": 5, "C+": 6, "C": 7, "C-": 8, "D": 9, "F": 10}
    games_sorted = sorted(
        games,
        key=lambda g: (
            grade_order.get(g.get("confidenceGrade", "C"), 7),
            -max(g.get("homeWinProb", 0.5), g.get("awayWinProb", 0.5))
        )
    )

    # Get date
    generated_at = data.get("generatedAt", "")
    if generated_at:
        try:
            dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            date_str = dt.strftime("%B %d, %Y")
        except:
            date_str = datetime.now().strftime("%B %d, %Y")
    else:
        date_str = datetime.now().strftime("%B %d, %Y")

    img = generate_edge_posts_image(games_sorted, date_str)

    output_path = OUTPUT_DIR / "edge_posts.png"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    save_high_quality(img, output_path)
    print(f"  Saved: {output_path}")

    return [output_path]


def main():
    try:
        paths = generate_edge_posts()
        if paths:
            print(f"\nGenerated {len(paths)} prediction image(s)")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
