#!/usr/bin/env python3
"""
A/B testing framework for Twitter posts.

Tests different post formats and tracks engagement to optimize content strategy.
"""

import argparse
import csv
import json
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List

REPO_ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS_FILE = REPO_ROOT / "web" / "src" / "data" / "todaysPredictions.json"
AB_TRACKER = REPO_ROOT / "data" / "archive" / "twitter_ab_tests.csv"
AB_VARIANTS = REPO_ROOT / "config" / "twitter_variants.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate A/B test variants for Twitter posts."
    )
    parser.add_argument(
        "--post-type",
        choices=["morning_preview", "afternoon_update", "evening_recap"],
        required=True,
        help="Type of post to generate",
    )
    parser.add_argument(
        "--variant",
        help="Force specific variant (A, B, C, etc.). Random if not specified.",
    )
    return parser.parse_args()


def load_predictions() -> Dict[str, Any]:
    """Load today's predictions."""
    with open(PREDICTIONS_FILE) as f:
        return json.load(f)


def load_variants() -> Dict[str, List[Dict[str, str]]]:
    """Load post format variants."""
    if not AB_VARIANTS.exists():
        # Create default variants if not exists
        default_variants = {
            "morning_preview": [
                {
                    "id": "A",
                    "format": "emoji_heavy",
                    "template": "🏒 NHL TODAY: {games} games\n\n🔥 TOP PICK:\n{top_game}\n📊 {grade} confidence\n\n{url}",
                },
                {
                    "id": "B",
                    "format": "minimal",
                    "template": "Today's NHL predictions:\n\n{top_game}\nConfidence: {grade}\n\nFull slate → {url}",
                },
                {
                    "id": "C",
                    "format": "stats_focused",
                    "template": "{games} NHL games today\n\nBest pick: {top_game}\n📊 {home_prob}% vs {away_prob}%\nGrade: {grade}\n\n{url}",
                },
                {
                    "id": "D",
                    "format": "question_hook",
                    "template": "Who wins tonight? 🤔\n\n{top_game}\n\nOur model says: {grade} confidence\nFull predictions → {url}",
                },
            ],
            "afternoon_update": [
                {
                    "id": "A",
                    "format": "excitement",
                    "template": "⚡️ TONIGHT'S ACTION\n\n{high_conf} high-confidence picks\n{games} total games\n\nGet the edge → {url}",
                },
                {
                    "id": "B",
                    "format": "value_prop",
                    "template": "60%+ accuracy all season 📈\n\n{games} games tonight\n{high_conf} A/B grade picks\n\n{url}",
                },
            ],
            "evening_recap": [
                {
                    "id": "A",
                    "format": "tomorrow_tease",
                    "template": "🌙 Tonight's games wrapping up\n\nTomorrow's picks drop at 8am ET\n📊 Analytics live now\n\n{url}",
                },
                {
                    "id": "B",
                    "format": "call_to_action",
                    "template": "Tonight's results coming in 🏒\n\nCheck tomorrow's predictions early → {url}",
                },
            ],
        }

        AB_VARIANTS.parent.mkdir(parents=True, exist_ok=True)
        with open(AB_VARIANTS, "w") as f:
            json.dump(default_variants, f, indent=2)

        return default_variants

    with open(AB_VARIANTS) as f:
        return json.load(f)


def select_variant(
    post_type: str, variants: Dict[str, List[Dict[str, str]]], forced_variant: str | None
) -> Dict[str, str]:
    """Select which variant to use (random or forced)."""
    available = variants.get(post_type, [])

    if not available:
        raise ValueError(f"No variants found for post type: {post_type}")

    if forced_variant:
        variant = next((v for v in available if v["id"] == forced_variant), None)
        if not variant:
            raise ValueError(f"Variant {forced_variant} not found")
        return variant

    # Random selection (A/B testing)
    return random.choice(available)


def generate_post(
    post_type: str, variant: Dict[str, str], data: Dict[str, Any]
) -> str:
    """Generate post content using selected variant template."""

    games = data.get("games", [])
    games_count = len(games)

    # Get top game (highest confidence)
    if games:
        top_game_data = max(games, key=lambda g: abs(g.get("edge", 0)))
        top_game = f"{top_game_data['awayTeam']['abbrev']} @ {top_game_data['homeTeam']['abbrev']}"
        grade = top_game_data.get("confidenceGrade", "C")
        home_prob = int(top_game_data.get("homeWinProb", 0.5) * 100)
        away_prob = 100 - home_prob
    else:
        top_game = "No games scheduled"
        grade = "N/A"
        home_prob = 50
        away_prob = 50

    # Count high confidence games
    high_conf = sum(1 for g in games if g.get("confidenceGrade", "C")[0] in ["A", "B"])

    # Fill template
    template = variant["template"]
    post = template.format(
        games=games_count,
        top_game=top_game,
        grade=grade,
        home_prob=home_prob,
        away_prob=away_prob,
        high_conf=high_conf,
        url="[your-site-url]",  # Replace with actual URL
    )

    return post


def log_variant_usage(post_type: str, variant: Dict[str, str]) -> None:
    """Log which variant was used for later analysis."""

    # Initialize CSV if doesn't exist
    if not AB_TRACKER.exists():
        AB_TRACKER.parent.mkdir(parents=True, exist_ok=True)
        with open(AB_TRACKER, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=[
                    "timestamp",
                    "post_type",
                    "variant_id",
                    "variant_format",
                    "impressions",
                    "engagements",
                    "engagement_rate",
                ],
            )
            writer.writeheader()

    # Append usage record
    with open(AB_TRACKER, "a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "timestamp",
                "post_type",
                "variant_id",
                "variant_format",
                "impressions",
                "engagements",
                "engagement_rate",
            ],
        )

        writer.writerow(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "post_type": post_type,
                "variant_id": variant["id"],
                "variant_format": variant["format"],
                "impressions": "",  # Fill in later from Twitter API
                "engagements": "",  # Fill in later from Twitter API
                "engagement_rate": "",  # Calculate later
            }
        )

    print(f"📝 Logged variant usage: {post_type} - Variant {variant['id']}")


def analyze_ab_results() -> None:
    """Analyze A/B test results to find winning formats."""

    if not AB_TRACKER.exists():
        print("ℹ️  No A/B test data yet")
        return

    with open(AB_TRACKER, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    if not rows:
        return

    # Group by variant
    variant_stats: Dict[str, Dict[str, Any]] = {}

    for row in rows:
        variant_key = f"{row['post_type']}-{row['variant_id']}"

        if variant_key not in variant_stats:
            variant_stats[variant_key] = {
                "post_type": row["post_type"],
                "variant_id": row["variant_id"],
                "format": row["variant_format"],
                "count": 0,
                "total_impressions": 0,
                "total_engagements": 0,
            }

        variant_stats[variant_key]["count"] += 1

        # Add metrics if available
        try:
            if row["impressions"]:
                variant_stats[variant_key]["total_impressions"] += int(
                    row["impressions"]
                )
            if row["engagements"]:
                variant_stats[variant_key]["total_engagements"] += int(
                    row["engagements"]
                )
        except (ValueError, KeyError):
            pass

    # Print results
    print("\n" + "=" * 70)
    print("📊 A/B TEST RESULTS")
    print("=" * 70)
    print(
        f"{'Variant':<15} {'Count':<8} {'Impressions':<12} {'Engagements':<12} {'Rate':<8}"
    )
    print("-" * 70)

    for variant_key, stats in sorted(variant_stats.items()):
        impressions = stats["total_impressions"]
        engagements = stats["total_engagements"]
        rate = (engagements / impressions * 100) if impressions > 0 else 0

        print(
            f"{variant_key:<15} {stats['count']:<8} {impressions:<12} "
            f"{engagements:<12} {rate:<8.2f}%"
        )

    print("=" * 70 + "\n")


def main() -> None:
    args = parse_args()

    # Load data
    data = load_predictions()
    variants = load_variants()

    # Select variant
    variant = select_variant(args.post_type, variants, args.variant)

    print(f"📋 Selected variant: {variant['id']} ({variant['format']})")

    # Generate post
    post = generate_post(args.post_type, variant, data)

    # Log usage
    log_variant_usage(args.post_type, variant)

    # Output post content
    print("\n" + "=" * 70)
    print("📱 GENERATED POST")
    print("=" * 70)
    print(post)
    print("=" * 70 + "\n")

    # Save to file for GitHub Actions to use
    output_file = Path("/tmp/twitter_post.txt")
    output_file.write_text(post)
    print(f"💾 Saved to {output_file}")

    # Show A/B test results
    analyze_ab_results()


if __name__ == "__main__":
    main()
