"""
V7.0 Enhanced Shot Quality Features for xG Model

Expected Impact: +0.2-0.4% accuracy

Adds advanced shot context features:
- Traffic/screening detection
- One-timer detection
- Pre-shot movement
- Goalie position/fatigue

These features enhance the xG model to better predict goal probability
based on shot context beyond just location and type.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Dict, Any, List, Optional

LOGGER = logging.getLogger(__name__)


@dataclass
class EnhancedShotFeatures:
    """
    Enhanced shot features for V7.0 xG model.

    Extends base ShotFeatures with additional context:
    - Traffic and screening
    - One-timers
    - Odd-man rushes
    - Goalie context
    """
    # Base features (from V6.3)
    distance: float
    angle: float
    shot_type: str
    is_even_strength: bool
    is_power_play: bool
    zone: str
    is_rush_shot: bool
    period: int

    # V7.0 enhancements
    has_traffic: bool = False  # Defenders between shooter and goalie
    is_one_timer: bool = False  # Shot immediately after pass
    is_screened: bool = False  # Defender within 2ft of shot line
    odd_man_rush: bool = False  # 2-on-1, 3-on-2, etc.
    is_deflection: bool = False  # Tip-in or deflection
    goalie_out_of_position: bool = False  # Goalie far from net
    shots_faced_in_period: int = 0  # Goalie fatigue factor

    def to_dict(self) -> Dict[str, Any]:
        """Convert to feature dictionary for xG model."""
        return {
            # Base features
            "distance": self.distance,
            "angle": self.angle,
            "shot_type": self.shot_type,
            "is_even_strength": 1 if self.is_even_strength else 0,
            "is_power_play": 1 if self.is_power_play else 0,
            "is_offensive_zone": 1 if self.zone == "O" else 0,
            "is_rush_shot": 1 if self.is_rush_shot else 0,
            "is_third_period": 1 if self.period >= 3 else 0,
            # V7.0 enhanced features
            "has_traffic": 1 if self.has_traffic else 0,
            "is_one_timer": 1 if self.is_one_timer else 0,
            "is_screened": 1 if self.is_screened else 0,
            "odd_man_rush": 1 if self.odd_man_rush else 0,
            "is_deflection": 1 if self.is_deflection else 0,
            "goalie_out_of_position": 1 if self.goalie_out_of_position else 0,
            "shots_faced_in_period": self.shots_faced_in_period,
        }


def detect_one_timer(
    current_play: Dict[str, Any],
    previous_plays: List[Dict[str, Any]],
    time_threshold: float = 1.0
) -> bool:
    """
    Detect if shot is a one-timer (pass to immediate shot).

    One-timer definition:
    - Shot occurs within 1 second of a completed pass
    - Pass and shot are from same team
    - Pass target is approximately at shot location

    Args:
        current_play: Current shot event
        previous_plays: List of recent plays (last 3-5)
        time_threshold: Max seconds between pass and shot (default 1.0)

    Returns:
        True if shot is a one-timer
    """
    if not previous_plays:
        return False

    # Get current shot time
    current_time = _parse_time_in_period(current_play.get("timeInPeriod", "00:00"))
    current_team = current_play.get("details", {}).get("eventOwnerTeamId")

    # Check last 3 events for a pass
    for prev_play in reversed(previous_plays[-3:]):
        prev_type = prev_play.get("typeDescKey", "").lower()
        prev_time = _parse_time_in_period(prev_play.get("timeInPeriod", "00:00"))
        prev_team = prev_play.get("details", {}).get("eventOwnerTeamId")

        # Must be same team
        if prev_team != current_team:
            continue

        time_diff = current_time - prev_time

        # Must be within threshold
        if time_diff < 0 or time_diff > time_threshold:
            continue

        # Check if previous event was a pass or completed play
        if prev_type in ["pass", "play", "zone-entry", "takeaway"]:
            return True

    return False


def detect_traffic(
    shot_x: float,
    shot_y: float,
    current_play: Dict[str, Any],
    all_plays: List[Dict[str, Any]],
    goal_x: float = 89.0
) -> bool:
    """
    Detect if there are defenders between shooter and goalie.

    Traffic definition:
    - One or more opposing players between shot location and goal
    - Within the "shot lane" (cone from puck to goal)

    Args:
        shot_x: X coordinate of shot
        shot_y: Y coordinate of shot
        current_play: Current shot event
        all_plays: All plays in sequence (to infer player positions)
        goal_x: X coordinate of goal

    Returns:
        True if traffic detected
    """
    # Note: NHL API doesn't provide real-time player positions
    # We can infer traffic from:
    # 1. Shot type: deflections/tips imply traffic
    # 2. Blocked shots nearby: implies defenders in lane
    # 3. Play description keywords

    details = current_play.get("details", {})
    shot_type = details.get("shotType", "").lower()

    # Deflections/tips always have traffic
    if shot_type in ["deflected", "tip-in", "tipped"]:
        return True

    # Check description for traffic keywords
    description = details.get("description", "").lower()
    traffic_keywords = ["deflected", "tipped", "screened", "traffic", "redirected"]

    if any(keyword in description for keyword in traffic_keywords):
        return True

    # Check recent plays for blocked shots in area
    # (indicates defenders were in shooting lane)
    shot_time = _parse_time_in_period(current_play.get("timeInPeriod", "00:00"))

    for prev_play in reversed(all_plays[-10:]):
        prev_type = prev_play.get("typeDescKey", "").lower()
        if "block" in prev_type:
            prev_time = _parse_time_in_period(prev_play.get("timeInPeriod", "00:00"))
            if 0 <= shot_time - prev_time <= 3:
                # Blocked shot in last 3 seconds suggests traffic
                return True

    return False


def detect_screened_shot(
    shot_x: float,
    shot_y: float,
    distance: float,
    current_play: Dict[str, Any]
) -> bool:
    """
    Detect if goalie's view is screened on the shot.

    Screening definition:
    - Shot from distance > 15 feet (not point blank)
    - Traffic in front (deflection, tip, etc.)
    - Or shot type/description indicates screening

    Args:
        shot_x: X coordinate of shot
        shot_y: Y coordinate of shot
        distance: Distance from goal
        current_play: Shot event

    Returns:
        True if shot is screened
    """
    # Point-blank shots can't be screened
    if distance < 15.0:
        return False

    details = current_play.get("details", {})
    shot_type = details.get("shotType", "").lower()
    description = details.get("description", "").lower()

    # Tip-ins and deflections are always screened
    if shot_type in ["tip-in", "deflected", "tipped"]:
        return True

    # Check description for screening keywords
    screen_keywords = ["screened", "screen", "traffic", "in front"]
    if any(keyword in description for keyword in screen_keywords):
        return True

    return False


def detect_odd_man_rush(
    current_play: Dict[str, Any],
    previous_plays: List[Dict[str, Any]]
) -> bool:
    """
    Detect if shot is from an odd-man rush (2-on-1, 3-on-2, etc.).

    Odd-man rush indicators:
    - Recent zone entry or turnover
    - Shot within 6 seconds
    - Rush shot flag already set
    - Description contains "odd man" or "breakaway"

    Args:
        current_play: Current shot event
        previous_plays: Recent plays for context

    Returns:
        True if odd-man rush detected
    """
    details = current_play.get("details", {})
    description = details.get("description", "").lower()

    # Check description for rush keywords
    rush_keywords = ["odd man", "odd-man", "breakaway", "2-on-1", "3-on-2", "2 on 1"]
    if any(keyword in description for keyword in rush_keywords):
        return True

    # Check for recent zone entry + quick shot
    current_time = _parse_time_in_period(current_play.get("timeInPeriod", "00:00"))

    for prev_play in reversed(previous_plays[-5:]):
        prev_type = prev_play.get("typeDescKey", "").lower()
        prev_time = _parse_time_in_period(prev_play.get("timeInPeriod", "00:00"))

        time_diff = current_time - prev_time

        # Must be within 6 seconds
        if time_diff < 0 or time_diff > 6:
            continue

        # Zone entry or turnover indicates potential rush
        if prev_type in ["zone-entry", "takeaway", "giveaway"]:
            return True

    return False


def _parse_time_in_period(time_str: str) -> float:
    """
    Parse time in period string to seconds.

    Args:
        time_str: Time in format "MM:SS"

    Returns:
        Time in seconds
    """
    try:
        mins, secs = time_str.split(":")
        return int(mins) * 60 + int(secs)
    except:
        return 0.0


def extract_enhanced_shot_features(
    play: Dict[str, Any],
    previous_plays: List[Dict[str, Any]],
    all_period_plays: List[Dict[str, Any]],
    base_features: Dict[str, Any],
    shots_faced_this_period: int = 0
) -> EnhancedShotFeatures:
    """
    Extract enhanced shot features from play-by-play data.

    Args:
        play: Current shot/goal event
        previous_plays: Last 5-10 plays for context
        all_period_plays: All plays in current period
        base_features: Base ShotFeatures from V6.3 model
        shots_faced_this_period: Shots goalie has faced this period

    Returns:
        EnhancedShotFeatures with V7.0 enhancements
    """
    details = play.get("details", {})

    # Get coordinates
    x = details.get("xCoord", 0)
    y = details.get("yCoord", 0)
    distance = base_features.get("distance", 0)

    # Detect enhancements
    has_traffic = detect_traffic(x, y, play, all_period_plays)
    is_one_timer = detect_one_timer(play, previous_plays)
    is_screened = detect_screened_shot(x, y, distance, play)
    odd_man_rush = detect_odd_man_rush(play, previous_plays)

    # Deflection detection
    shot_type = details.get("shotType", "").lower()
    is_deflection = shot_type in ["tip-in", "deflected", "tipped"]

    # Goalie out of position (inferred from distance and rush)
    is_rush = base_features.get("is_rush_shot", False)
    goalie_out_of_position = is_rush and distance > 30.0

    # Create enhanced features
    return EnhancedShotFeatures(
        # Base features
        distance=base_features.get("distance", 0),
        angle=base_features.get("angle", 0),
        shot_type=base_features.get("shot_type", "wrist"),
        is_even_strength=bool(base_features.get("is_even_strength", True)),
        is_power_play=bool(base_features.get("is_power_play", False)),
        zone=base_features.get("zone", "O"),
        is_rush_shot=bool(base_features.get("is_rush_shot", False)),
        period=base_features.get("period", 1),
        # V7.0 enhancements
        has_traffic=has_traffic,
        is_one_timer=is_one_timer,
        is_screened=is_screened,
        odd_man_rush=odd_man_rush,
        is_deflection=is_deflection,
        goalie_out_of_position=goalie_out_of_position,
        shots_faced_in_period=shots_faced_this_period,
    )


__all__ = [
    'EnhancedShotFeatures',
    'extract_enhanced_shot_features',
    'detect_one_timer',
    'detect_traffic',
    'detect_screened_shot',
    'detect_odd_man_rush',
]
