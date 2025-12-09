#!/usr/bin/env python3
"""
Master Graphics Generator

Generates all Instagram graphics templates at once.
"""

from __future__ import annotations

import sys
import argparse
from pathlib import Path
from typing import List

# Add templates directory to path
GRAPHICS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(GRAPHICS_DIR))
sys.path.insert(0, str(GRAPHICS_DIR / "templates"))

from templates.todays_slate import generate_todays_slate
from templates.power_rankings import generate_power_rankings
from templates.goalie_leaderboard import generate_goalie_leaderboard
from templates.luck_report import generate_luck_report
from templates.risers_fallers import generate_risers_fallers
from templates.model_receipts import generate_model_receipts
from templates.team_trends import generate_team_trends


GENERATORS = {
    "slate": ("Today's Slate", generate_todays_slate),
    "rankings": ("Power Rankings", generate_power_rankings),
    "goalies": ("Goalie Leaderboard", generate_goalie_leaderboard),
    "luck": ("Luck Report", generate_luck_report),
    "trends": ("Risers/Fallers", generate_risers_fallers),
    "receipts": ("Model Receipts", generate_model_receipts),
    "team_trends": ("Team Trends", generate_team_trends),
}


def generate_all(templates: List[str] = None) -> dict:
    """
    Generate all or specified graphics.

    Args:
        templates: List of template keys to generate. If None, generates all.

    Returns:
        Dictionary mapping template names to list of output paths.
    """
    results = {}

    if templates is None:
        templates = list(GENERATORS.keys())

    print("=" * 60)
    print("PUCKCAST GRAPHICS GENERATOR")
    print("=" * 60)
    print()

    for key in templates:
        if key not in GENERATORS:
            print(f"  Unknown template: {key}")
            continue

        name, generator = GENERATORS[key]
        print(f"  Generating {name}...")

        try:
            paths = generator()
            results[key] = paths
            print(f"    Generated {len(paths)} image(s)")
        except Exception as e:
            print(f"    Error: {e}")
            results[key] = []

        print()

    # Summary
    total = sum(len(paths) for paths in results.values())
    print("=" * 60)
    print(f"COMPLETE: Generated {total} total images")
    print("=" * 60)

    return results


def main():
    parser = argparse.ArgumentParser(description="Generate Puckcast Instagram graphics")
    parser.add_argument(
        "--templates",
        "-t",
        nargs="+",
        choices=list(GENERATORS.keys()),
        help="Specific templates to generate (default: all)",
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List available templates",
    )

    args = parser.parse_args()

    if args.list:
        print("Available templates:")
        for key, (name, _) in GENERATORS.items():
            print(f"  {key:12s} - {name}")
        return 0

    generate_all(args.templates)
    return 0


if __name__ == "__main__":
    sys.exit(main())
