#!/usr/bin/env python3
"""
Minimal Twitter post generator for the new 4-post cadence.
"""

import argparse
import csv
import json
import ssl
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Dict, List
from urllib.request import Request, urlopen

REPO_ROOT = Path(__file__).resolve().parents[1]
PREDICTIONS_FILE = REPO_ROOT / "web" / "src" / "data" / "todaysPredictions.json"
ARCHIVE_DIR = REPO_ROOT / "data" / "archive" / "predictions"
AB_TRACKER = REPO_ROOT / "data" / "archive" / "twitter_ab_tests.csv"
AB_VARIANTS = REPO_ROOT / "config" / "twitter_variants.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate Twitter posts.")
    parser.add_argument(
        "--post-type",
        choices=["morning_slate", "team_highlight", "results_recap", "tomorrow_tease"],
        required=True,
    )
    parser.add_argument("--variant", help="Optional variant id to force")
    return parser.parse_args()


def load_predictions() -> Dict[str, Any]:
    if not PREDICTIONS_FILE.exists():
        raise FileNotFoundError(f"Predictions file not found at {PREDICTIONS_FILE}")
    with open(PREDICTIONS_FILE) as f:
        data = json.load(f)
    gen = data.get("generatedAt")
    if gen:
        dt = datetime.fromisoformat(gen.replace("Z", "+00:00"))
        now = datetime.now(timezone.utc)
        now_et = now.astimezone(ZoneInfo("America/New_York"))
        gen_et = dt.astimezone(ZoneInfo("America/New_York"))
        if (now_et.date() != gen_et.date()) or (now - dt).total_seconds() > 60 * 60 * 24:
            raise RuntimeError(f"Stale predictions: generated {dt.isoformat()}Z")
    return data


def load_variants() -> Dict[str, List[Dict[str, str]]]:
    if not AB_VARIANTS.exists():
        AB_VARIANTS.parent.mkdir(parents=True, exist_ok=True)
        AB_VARIANTS.write_text(json.dumps({
            "morning_slate": [{"id": "A", "format": "morning_slate", "template": "{games} NHL games today {url}"}],
            "team_highlight": [{"id": "A", "format": "team_highlight", "template": "Team highlight: {team_name} {url}"}],
            "results_recap": [{"id": "A", "format": "results_recap", "template": "Recap {correct}/{total} {url}"}],
            "tomorrow_tease": [{"id": "A", "format": "tomorrow_tease", "template": "Tomorrow 8am ET {url}"}],
        }, indent=2))
    with open(AB_VARIANTS) as f:
        return json.load(f)


def select_variant(post_type: str, variants: Dict[str, List[Dict[str, str]]], forced: str | None) -> Dict[str, str]:
    pool = variants.get(post_type, [])
    if not pool:
        raise ValueError(f"No variants configured for {post_type}")
    if forced:
        for v in pool:
            if v.get("id") == forced:
                return v
        raise ValueError(f"Variant {forced} not found for {post_type}")
    return pool[0]


def _format_time(et_str: str | None) -> str:
    return et_str.replace(" ET", "") if et_str else "TBD"


def _build_tag_block(teams: List[Dict[str, str]]) -> str:
    tags = [f"#{t['abbrev']}" for t in teams if t.get("abbrev")]
    return " ".join(tags) if tags else "#NHL"


def _fetch_game_result(game_id: str):
    try:
        url = f"https://statsapi.web.nhl.com/api/v1/game/{game_id}/feed/live"
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        context = ssl._create_unverified_context()
        with urlopen(req, timeout=10, context=context) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        line_score = data.get("liveData", {}).get("linescore", {})
        status = data.get("gameData", {}).get("status", {}).get("detailedState", "")
        if status not in ["Final", "Final/OT", "Final/SO"]:
            return None
        home = line_score.get("teams", {}).get("home", {})
        away = line_score.get("teams", {}).get("away", {})
        return {
            "home_score": home.get("goals"),
            "away_score": away.get("goals"),
            "winner": "home" if home.get("goals", 0) > away.get("goals", 0) else "away",
        }
    except Exception:
        return None


def _results_recap_payload() -> Dict[str, Any]:
    # Use yesterday ET
    now_et = datetime.now(timezone.utc).astimezone(ZoneInfo("America/New_York"))
    target_date = now_et.date() - timedelta(days=1)
    date_str = target_date.isoformat()
    archive_file = ARCHIVE_DIR / f"predictions_{date_str}.json"
    if not archive_file.exists():
        return {"date": date_str, "total": 0, "correct": 0, "hits": [], "misses": []}
    data = json.loads(archive_file.read_text())
    games = data.get("games", [])
    hits, misses = [], []
    for game in games:
        result = _fetch_game_result(str(game.get("id")))
        if not result:
            continue
        predicted = game.get("modelFavorite", "home")
        actual = result["winner"]
        line = f"{game['awayTeam']['abbrev']} {result['away_score']} @ {game['homeTeam']['abbrev']} {result['home_score']}"
        if predicted == actual:
            hits.append(line)
        else:
            misses.append(line)
    total = len(hits) + len(misses)
    return {"date": date_str, "total": total, "correct": len(hits), "hits": hits[:3], "misses": misses[:2]}


def generate_post(post_type: str, variant: Dict[str, str], data: Dict[str, Any]) -> str:
    games = data.get("games", [])
    date_label = datetime.now(ZoneInfo("America/New_York")).strftime("%b %d")
    template = variant["template"]

    if post_type == "morning_slate":
        games_sorted = sorted(
            games,
            key=lambda g: (g.get("startTimeEt") or "ZZZ", -abs(g.get("edge", 0))),
        )
        lines = []
        for g in games_sorted:
            fav_is_home = g.get("modelFavorite", "home") == "home"
            fav = g["homeTeam"] if fav_is_home else g["awayTeam"]
            prob = int((g["homeWinProb"] if fav_is_home else g["awayWinProb"]) * 100)
            away_tag = g["awayTeam"].get("abbrev") or ""
            home_tag = g["homeTeam"].get("abbrev") or ""
            fav_tag = fav.get("abbrev", fav.get("name", ""))
            line = (
                f"{away_tag} @ {home_tag} — {fav_tag} {prob}% "
                f"@{g['awayTeam'].get('abbrev','')} @{g['homeTeam'].get('abbrev','')}"
            )
            lines.append(line)
        slate_lines = "\n".join(lines) if lines else "No NHL games today. Next slate drops at 8am ET."
        mapping = {
            "date_label": date_label,
            "slate_lines": slate_lines,
            "team_tags": "",
            "games": len(games),
            "favorite_team": "",
            "favorite_prob": "",
            "first_time": "",
            "url": "",
        }
        return template.format(**mapping)

    if post_type == "team_highlight":
        top = max(games, key=lambda g: abs(g.get("edge", 0)), default=None)
        if not top:
            return f"No games on {date_label}. { '[your-site-url]'}"
        fav_is_home = top.get("modelFavorite", "home") == "home"
        fav = top["homeTeam"] if fav_is_home else top["awayTeam"]
        under = top["awayTeam"] if fav_is_home else top["homeTeam"]
        favorite_prob = int((top["homeWinProb"] if fav_is_home else top["awayWinProb"]) * 100)
        edge_label = f"{abs(top.get('edge', 0)) * 100:.1f} pts"
        tag_block = _build_tag_block([fav, under])
        return template.format(
            date_label=date_label,
            team_name=fav.get("name", fav.get("abbrev")),
            opponent_label=f"{under.get('abbrev')} @ {fav.get('abbrev')}" if fav_is_home else f"{fav.get('abbrev')} @ {under.get('abbrev')}",
            start_time=_format_time(top.get("startTimeEt")),
            favorite_team=fav.get("name", fav.get("abbrev")),
            favorite_prob=favorite_prob,
            edge_label=edge_label,
            url="[your-site-url]",
            team_tags=tag_block,
        )

    if post_type == "results_recap":
        recap = _results_recap_payload()
        total = recap["total"]
        correct = recap["correct"]
        accuracy = f"{(correct / total * 100):.0f}" if total else "0"
        hits = ", ".join(recap["hits"]) if recap["hits"] else "None"
        misses = ", ".join(recap["misses"]) if recap["misses"] else "None"
        return template.format(
            date_label=recap["date"],
            correct=correct,
            total=total,
            accuracy=accuracy,
            hits=hits,
            misses=misses,
            url="[your-site-url]",
        )

    if post_type == "tomorrow_tease":
        return template.format(date_label=date_label, url="[your-site-url]")

    raise ValueError(f"Unsupported post type: {post_type}")


def log_variant_usage(post_type: str, variant: Dict[str, str]) -> None:
    if not AB_TRACKER.exists():
        AB_TRACKER.parent.mkdir(parents=True, exist_ok=True)
        with open(AB_TRACKER, "w", newline="") as f:
            writer = csv.DictWriter(
                f,
                fieldnames=["timestamp", "post_type", "variant_id", "variant_format"],
            )
            writer.writeheader()
    with open(AB_TRACKER, "a", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["timestamp", "post_type", "variant_id", "variant_format"],
        )
        writer.writerow(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "post_type": post_type,
                "variant_id": variant.get("id"),
                "variant_format": variant.get("format"),
            }
        )


def main() -> None:
    args = parse_args()
    data = load_predictions()
    variants = load_variants()
    variant = select_variant(args.post_type, variants, args.variant)
    post = generate_post(args.post_type, variant, data)
    log_variant_usage(args.post_type, variant)
    print(post)


if __name__ == "__main__":
    main()
