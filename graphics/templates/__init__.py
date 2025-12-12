"""
Puckcast Graphics Templates

Instagram-ready graphics generators for NHL predictions and analytics.
"""

from .todays_slate import generate_todays_slate
from .power_rankings import generate_power_rankings
from .goalie_leaderboard import generate_goalie_leaderboard
from .luck_report import generate_luck_report
from .risers_fallers import generate_risers_fallers
from .model_receipts import generate_model_receipts
from .edge_posts import generate_edge_posts
from .team_trends import generate_team_trends

__all__ = [
    "generate_todays_slate",
    "generate_power_rankings",
    "generate_goalie_leaderboard",
    "generate_luck_report",
    "generate_risers_fallers",
    "generate_model_receipts",
    "generate_edge_posts",
    "generate_team_trends",
]
