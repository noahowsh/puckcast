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
from zoneinfo import ZoneInfo
from pathlib import Path
from typing import Any, Dict, List, Iterable

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
    if not PREDICTIONS_FILE.exists():
        raise FileNotFoundError(f"Predictions file not found at {PREDICTIONS_FILE}")

    with open(PREDICTIONS_FILE) as f:
        data = json.load(f)

    # Guard against stale data
    generated_at = data.get("generatedAt")
    if generated_at:
        try:
          # Normalize to ET and require same calendar day
            generated_dt = datetime.fromisoformat(generated_at.replace("Z", "+00:00"))
            now_utc = datetime.now(timezone.utc)
            now_et = now_utc.astimezone(ZoneInfo("America/New_York"))
            gen_et = generated_dt.astimezone(ZoneInfo("America/New_York"))
            if (now_et.date() != gen_et.date()) or (now_utc - generated_dt).total_seconds() > 60 * 60 * 24:
                raise RuntimeError(
                    f"Stale predictions: generated {generated_dt.isoformat()}Z, today is {now_et.date()} ET"
                )
        except Exception as exc:
            raise RuntimeError(f"Unable to validate predictions freshness: {exc}") from exc

    return data


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


def get_team_hashtag(team_name: str) -> str:
    """Convert team name to hashtag format."""
    hashtag_map = {
        "ANA": "Ducks",
        "ARI": "Yotes",
        "BOS": "NHLBruins",
        "BUF": "Sabres",
        "CAR": "Canes",
        "CBJ": "CBJ",
        "CGY": "Flames",
        "CHI": "Blackhawks",
        "COL": "GoAvsGo",
        "DAL": "TexasHockey",
        "DET": "LGRW",
        "EDM": "LetsGoOilers",
        "FLA": "FlaPanthers",
        "LAK": "GoKingsGo",
        "MIN": "MNWild",
        "MTL": "GoHabsGo",
        "NJD": "NJDevils",
        "NSH": "Smashville",
        "NYI": "Isles",
        "NYR": "NYR",
        "OTT": "GoSensGo",
        "PHI": "LetsGoFlyers",
        "PIT": "LetsGoPens",
        "SEA": "SeaKraken",
        "SJS": "SJSharks",
        "STL": "STLBlues",
        "TBL": "GoBolts",
        "TOR": "LeafsForever",
        "VAN": "Canucks",
        "VGK": "VegasBorn",
        "WPG": "GoJetsGo",
        "WSH": "ALLCAPS",
    }
    return hashtag_map.get(team_name, hashtag_map.get(team_name.split()[-1], team_name.split()[-1]))


def get_team_handle(team_name: str, abbrev: str) -> str | None:
    handles = {
        "ANA": "AnaheimDucks",
        "ARI": "ArizonaCoyotes",
        "BOS": "NHLBruins",
        "BUF": "BuffaloSabres",
        "CAR": "Canes",
        "CBJ": "BlueJacketsNHL",
        "CGY": "NHLFlames",
        "CHI": "NHLBlackhawks",
        "COL": "Avalanche",
        "DAL": "DallasStars",
        "DET": "DetroitRedWings",
        "EDM": "EdmontonOilers",
        "FLA": "FlaPanthers",
        "LAK": "LAKings",
        "MIN": "mnwild",
        "MTL": "CanadiensMTL",
        "NJD": "NJDevils",
        "NSH": "PredsNHL",
        "NYI": "NYIslanders",
        "NYR": "NYRangers",
        "OTT": "Senators",
        "PHI": "NHLFlyers",
        "PIT": "penguins",
        "SEA": "SeattleKraken",
        "SJS": "SanJoseSharks",
        "STL": "StLouisBlues",
        "TBL": "TBLightning",
        "TOR": "MapleLeafs",
        "VAN": "Canucks",
        "VGK": "GoldenKnights",
        "WPG": "NHLJets",
        "WSH": "Capitals",
    }
    return handles.get(abbrev) or handles.get(team_name)


def build_tag_block(teams: Iterable[tuple[str, str]]) -> str:
    """Return a string of hashtags + team mentions."""
    hashtags = {"NHL"}  # Always include league tag
    mentions: set[str] = set()
    for name, abbrev in teams:
        hashtags.add(get_team_hashtag(abbrev or name))
        handle = get_team_handle(name, abbrev)
        if handle:
            mentions.add(f"@{handle}")
    hashtag_str = " ".join(f"#{tag}" for tag in sorted(hashtags))
    mention_str = " ".join(sorted(mentions))
    if hashtag_str and mention_str:
        return f"{hashtag_str} {mention_str}".strip()
    return (hashtag_str or mention_str).strip()


def generate_micro_insight(data: Dict[str, Any]) -> Dict[str, str]:
    """Generate a random micro-insight from the data."""
    import random

    games = data.get("games", [])
    if not games:
        return {
            "insight": "Model running analytics on all 32 NHL teams",
            "secondary_stat": "Power rankings updated daily",
            "rank": "1",
            "tag_block": "#NHL",
        }

    # Get a random team from today's games
    game = random.choice(games)
    team_choice = random.choice(["home", "away"])

    if team_choice == "home":
        team_data = game["homeTeam"]
        win_prob = game.get("homeWinProb", 0.5)
        opp_team = game["awayTeam"]["abbrev"]
    else:
        team_data = game["awayTeam"]
        win_prob = 1 - game.get("homeWinProb", 0.5)
        opp_team = game["homeTeam"]["abbrev"]

    team_name = team_data.get("name", team_data["abbrev"])
    team_abbrev = team_data["abbrev"]
    tag_block = build_tag_block([(team_name, team_abbrev)])

    # Generate different types of insights
    insight_types = []

    # Win probability insight
    if win_prob > 0.65:
        insight_types.append({
            "insight": f"The {team_abbrev} are heavily favored tonight vs {opp_team}",
            "secondary_stat": f"Model gives them {int(win_prob * 100)}% win probability",
            "rank": str(random.randint(5, 15)),
            "tag_block": tag_block,
        })
    elif win_prob < 0.35:
        insight_types.append({
            "insight": f"The {team_abbrev} are big underdogs tonight vs {opp_team}",
            "secondary_stat": f"Model gives them just {int(win_prob * 100)}% win probability",
            "rank": str(random.randint(18, 28)),
            "tag_block": tag_block,
        })

    # High confidence game
    grade = game.get("confidenceGrade", "C")
    if grade in ["A+", "A", "A-", "B+"]:
        insight_types.append({
            "insight": f"{team_abbrev} vs {opp_team} is our highest confidence pick today",
            "secondary_stat": f"Grade: {grade}",
            "rank": str(random.randint(1, 20)),
            "tag_block": tag_block,
        })

    # Edge insight
    edge = abs(game.get("edge", 0))
    if edge > 0.12:
        insight_types.append({
            "insight": f"Big edge detected: {team_abbrev} vs {opp_team}",
            "secondary_stat": f"Model sees a {int(edge * 100)}% value play here",
            "rank": str(random.randint(8, 18)),
            "tag_block": tag_block,
        })

    # Default insight if none generated
    if not insight_types:
        insight_types.append({
            "insight": f"{team_abbrev} taking on {opp_team} tonight",
            "secondary_stat": f"Win probability: {int(win_prob * 100)}%",
            "rank": str(random.randint(10, 25)),
            "tag_block": tag_block,
        })

    return random.choice(insight_types)


def format_team_display(team: Dict[str, Any]) -> str:
    """Return team handle if available, else name/abbrev."""
    name = team.get("name") or team.get("abbrev")
    abbrev = team.get("abbrev")
    handle = get_team_handle(name or "", abbrev or "")
    return f"@{handle}" if handle else (name or abbrev or "Team")


def format_matchup(game: Dict[str, Any], sep: str = " at ") -> str:
    """Human-friendly matchup string with handles when possible."""
    away = format_team_display(game["awayTeam"])
    home = format_team_display(game["homeTeam"])
    return f"{away}{sep}{home}"


def build_fun_facts(games: List[Dict[str, Any]]) -> List[tuple[str, List[tuple[str, str]]]]:
    """Assemble varied fun-fact snippets from the slate. Returns (fact, teams) tuples."""
    facts: List[tuple[str, List[tuple[str, str]]]] = []
    if not games:
        return [("Model crunching numbers for all 32 teams today.", [("NHL", "NHL")])]

    # Biggest model edge
    best_edge = max(games, key=lambda g: abs(g.get("edge", 0.0)))
    edge_pts = abs(best_edge.get("edge", 0.0)) * 100
    facts.append(
        (
            f"Biggest model edge: {format_matchup(best_edge)} (Grade {best_edge.get('confidenceGrade', 'B')}, {edge_pts:.1f} pts)",
            [
                (best_edge["awayTeam"].get("name", best_edge["awayTeam"]["abbrev"]), best_edge["awayTeam"]["abbrev"]),
                (best_edge["homeTeam"].get("name", best_edge["homeTeam"]["abbrev"]), best_edge["homeTeam"]["abbrev"]),
            ],
        )
    )

    # Tightest game (closest to coin flip)
    close_game = min(games, key=lambda g: abs(g.get("edge", 1.0)))
    home_prob = close_game.get("homeWinProb", 0.5)
    away_prob = 1 - home_prob
    facts.append(
        (
            f"Toss-up alert: {format_matchup(close_game)} ({int(home_prob*100)}% vs {int(away_prob*100)}%)",
            [
                (close_game["awayTeam"].get("name", close_game["awayTeam"]["abbrev"]), close_game["awayTeam"]["abbrev"]),
                (close_game["homeTeam"].get("name", close_game["homeTeam"]["abbrev"]), close_game["homeTeam"]["abbrev"]),
            ],
        )
    )

    # Road favorite
    road_favs = [g for g in games if g.get("modelFavorite") == "away" and (1 - g.get("homeWinProb", 0.5)) >= 0.55]
    if road_favs:
        road = max(road_favs, key=lambda g: (1 - g.get("homeWinProb", 0.5)))
        road_prob = int((1 - road.get("homeWinProb", 0.5)) * 100)
        facts.append(
            (
                f"Road lean: {format_team_display(road['awayTeam'])} at {format_team_display(road['homeTeam'])} ({road_prob}% on the road)",
                [
                    (road["awayTeam"].get("name", road["awayTeam"]["abbrev"]), road["awayTeam"]["abbrev"]),
                    (road["homeTeam"].get("name", road["homeTeam"]["abbrev"]), road["homeTeam"]["abbrev"]),
                ],
            )
        )

    # High-confidence (A grade)
    a_games = [g for g in games if str(g.get("confidenceGrade", "C")).startswith("A")]
    if a_games:
        a_game = max(a_games, key=lambda g: abs(g.get("edge", 0.0)))
        prob = a_game.get("homeWinProb", 0.5)
        fav = a_game["homeTeam"] if prob >= 0.5 else a_game["awayTeam"]
        opp = a_game["awayTeam"] if prob >= 0.5 else a_game["homeTeam"]
        fav_prob = int(max(prob, 1 - prob) * 100)
        facts.append(
            (
                f"Grade A edge: {format_team_display(fav)} ({fav_prob}% win chance, {a_game.get('startTimeEt', 'TBD')})",
                [
                    (fav.get("name", fav.get("abbrev")), fav.get("abbrev")),
                    (opp.get("name", opp.get("abbrev")), opp.get("abbrev")),
                ],
            )
        )

    # Upset radar (35-45% underdog)
    upset_games = [
        g for g in games if 0.35 <= g.get("homeWinProb", 0.5) <= 0.45 or 0.35 <= (1 - g.get("homeWinProb", 0.5)) <= 0.45
    ]
    if upset_games:
        g = max(upset_games, key=lambda g: abs(g.get("edge", 0.0)))
        home_prob = g.get("homeWinProb", 0.5)
        if home_prob < 0.5:
            dog = g["homeTeam"]
            fav = g["awayTeam"]
            dog_prob = int(home_prob * 100)
        else:
            dog = g["awayTeam"]
            fav = g["homeTeam"]
            dog_prob = int((1 - home_prob) * 100)
        facts.append(
            (
                f"Upset watch: {format_team_display(dog)} at {format_team_display(fav)} ({dog_prob}% upset shot)",
                [
                    (dog.get("name", dog.get("abbrev")), dog.get("abbrev")),
                    (fav.get("name", fav.get("abbrev")), fav.get("abbrev")),
                ],
            )
        )

    return facts


def generate_post(
    post_type: str, variant: Dict[str, str], data: Dict[str, Any]
) -> str:
    """Generate post content using selected variant template."""

    games = data.get("games", [])
    games_count = len(games)
    tag_block = "#NHL"
    template = variant["template"]
    template_uses_tags = "{team_tags}" in template or "{team_tag}" in template or "{team_mentions}" in template

    # Get top game (highest confidence)
    if games:
        top_game_data = max(games, key=lambda g: abs(g.get("edge", 0)))
        away_team_name = top_game_data['awayTeam'].get('name', top_game_data['awayTeam']['abbrev'])
        home_team_name = top_game_data['homeTeam'].get('name', top_game_data['homeTeam']['abbrev'])
        away_abbrev = top_game_data['awayTeam']['abbrev']
        home_abbrev = top_game_data['homeTeam']['abbrev']
        tag_block = build_tag_block([(away_team_name, away_abbrev), (home_team_name, home_abbrev)])

        grade = top_game_data.get("confidenceGrade", "C")
        home_prob = int(top_game_data.get("homeWinProb", 0.5) * 100)
        away_prob = 100 - home_prob
        # Prefer @handles in-line if available
        away_team_display = format_team_display(top_game_data["awayTeam"])
        home_team_display = format_team_display(top_game_data["homeTeam"])
    else:
        away_abbrev = "TBD"
        home_abbrev = "TBD"
        away_team_name = "TBD"
        home_team_name = "TBD"
        grade = "N/A"
        home_prob = 50
        away_prob = 50
        tag_block = "#NHL #HockeyTwitter"
        away_team_display = away_team_name
        home_team_display = home_team_name

    # Count high confidence games
    high_conf = sum(1 for g in games if g.get("confidenceGrade", "C")[0] in ["A", "B"])

    # Handle special post types
    if post_type == "micro_insights":
        insight_data = generate_micro_insight(data)
        post = template.format(
            insight=insight_data["insight"],
            secondary_stat=insight_data["secondary_stat"],
            rank=insight_data["rank"],
            team_tag=insight_data["tag_block"],
            url="[your-site-url]",
        )
        return post if template_uses_tags else f"{post}\n\n{insight_data['tag_block']}"

    if post_type == "game_of_night" and games:
        # Highest confidence game
        top_game_data = max(games, key=lambda g: abs(g.get("edge", 0)))
        confidence = int(max(top_game_data.get("homeWinProb", 0.5), 1 - top_game_data.get("homeWinProb", 0.5)) * 100)
        time = top_game_data.get("startTimeEt", "TBD")

        away_name = top_game_data['awayTeam'].get('name', top_game_data['awayTeam']['abbrev'])
        home_name = top_game_data['homeTeam'].get('name', top_game_data['homeTeam']['abbrev'])
        tag_block = build_tag_block([(away_name, top_game_data['awayTeam']['abbrev']), (home_name, top_game_data['homeTeam']['abbrev'])])

        post = template.format(
            confidence=confidence,
            matchup=format_matchup(top_game_data),
            time=time,
            factor1="High model confidence",
            factor2=f"Grade: {top_game_data.get('confidenceGrade', 'B')}",
            factor3=f"Edge: {abs(top_game_data.get('edge', 0)) * 100:.0f}%",
            team_tags=tag_block,
            url="[your-site-url]",
        )
        return post if template_uses_tags else f"{post}\n\n{tag_block}"

    if post_type == "upset_watch" and games:
        # Find games where underdog has 35-45% chance
        upset_games = [g for g in games if 0.35 <= g.get("homeWinProb", 0.5) <= 0.45 or 0.35 <= (1 - g.get("homeWinProb", 0.5)) <= 0.45]
        if upset_games:
            game = max(upset_games, key=lambda g: abs(g.get("edge", 0)))
            home_prob = game.get("homeWinProb", 0.5)

            if home_prob < 0.5:
                underdog = format_team_display(game['homeTeam'])
                favorite = format_team_display(game['awayTeam'])
                underdog_prob = int(home_prob * 100)
                underdog_name = game['homeTeam'].get('name', game['homeTeam']['abbrev'])
                favorite_name = game['awayTeam'].get('name', game['awayTeam']['abbrev'])
            else:
                underdog = format_team_display(game['awayTeam'])
                favorite = format_team_display(game['homeTeam'])
                underdog_prob = int((1 - home_prob) * 100)
                underdog_name = game['awayTeam'].get('name', game['awayTeam']['abbrev'])
                favorite_name = game['homeTeam'].get('name', game['homeTeam']['abbrev'])
            tag_block = build_tag_block([(underdog_name, game['homeTeam']['abbrev']), (favorite_name, game['awayTeam']['abbrev'])])

            post = template.format(
                underdog=underdog,
                favorite=favorite,
                underdog_prob=underdog_prob,
                edge1=f"Grade: {game.get('confidenceGrade', 'B')}",
                edge2="Value opportunity detected",
                edge3=f"Model edge: {abs(game.get('edge', 0)) * 100:.0f}%",
                team_tags=tag_block,
                url="[your-site-url]",
            )
            return post if template_uses_tags else f"{post}\n\n{tag_block}"

    if post_type == "team_spotlight" and games:
        # Rotate through teams based on day of year
        import datetime
        day_of_year = datetime.datetime.now().timetuple().tm_yday
        # Get a team from today's games, cycling through
        team_idx = day_of_year % len(games)
        game = games[team_idx]
        team_choice = random.choice(["home", "away"])

        team_data = game["homeTeam"] if team_choice == "home" else game["awayTeam"]
        team_name = team_data.get("name", team_data["abbrev"])
        team_display = format_team_display(team_data)
        tag_block = build_tag_block([(team_name, team_data["abbrev"])])

        post = template.format(
            team_name=team_display,
            rank=random.randint(5, 25),
            power_score=random.randint(65, 85),
            accuracy="7-3",
            trend="Upward" if random.random() > 0.5 else "Steady",
            insight="Showing strong fundamentals",
            team_tag=tag_block,
            url="[your-site-url]",
        )
        return post if template_uses_tags else f"{post}\n\n{tag_block}"

    if post_type == "fun_fact" and games:
        # Generate a fun fact from game data
        facts = build_fun_facts(games)
        fact_text, fact_teams = random.choice(facts)
        tag_block = build_tag_block(fact_teams)

        post = template.format(
            fact=fact_text,
            team_tag=tag_block,
            url="[your-site-url]",
        )
        return post if template_uses_tags else f"{post}\n\n{tag_block}"

    # Fill template for regular posts
    post = template.format(
        games=games_count,
        away_team=away_team_display,
        home_team=home_team_display,
        grade=grade,
        home_prob=home_prob,
        away_prob=away_prob,
        high_conf=high_conf,
        team_tags=tag_block,
        url="[your-site-url]",  # Replace with actual URL
    )

    return post if template_uses_tags else f"{post}\n\n{tag_block}"


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
