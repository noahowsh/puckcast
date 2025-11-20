"""Travel distance and timezone features for NHL predictions."""

from __future__ import annotations

import math
from typing import Dict, Tuple

import pandas as pd


# NHL Team Locations (latitude, longitude, timezone offset from ET)
# Timezone offset: ET=0, CT=-1, MT=-2, PT=-3
TEAM_LOCATIONS: Dict[str, Tuple[float, float, int]] = {
    # Atlantic Division
    "BOS": (42.3662, -71.0621, 0),    # Boston, MA (ET)
    "BUF": (42.8750, -78.8761, 0),    # Buffalo, NY (ET)
    "DET": (42.3410, -83.0550, 0),    # Detroit, MI (ET)
    "FLA": (26.1583, -80.3256, 0),    # Sunrise, FL (ET)
    "MTL": (45.4961, -73.5694, 0),    # Montreal, QC (ET)
    "OTT": (45.2968, -75.9270, 0),    # Ottawa, ON (ET)
    "TBL": (27.9425, -82.4518, 0),    # Tampa, FL (ET)
    "TOR": (43.6434, -79.3791, 0),    # Toronto, ON (ET)

    # Metropolitan Division
    "CAR": (35.8031, -78.7219, 0),    # Raleigh, NC (ET)
    "CBJ": (39.9692, -82.9911, 0),    # Columbus, OH (ET)
    "NJD": (40.7334, -74.1711, 0),    # Newark, NJ (ET)
    "NYI": (40.7225, -73.5907, 0),    # Uniondale, NY (ET)
    "NYR": (40.7505, -73.9934, 0),    # New York, NY (ET)
    "PHI": (39.9012, -75.1720, 0),    # Philadelphia, PA (ET)
    "PIT": (40.4394, -79.9890, 0),    # Pittsburgh, PA (ET)
    "WSH": (38.8981, -77.0209, 0),    # Washington, DC (ET)

    # Central Division
    "CHI": (41.8807, -87.6742, -1),   # Chicago, IL (CT)
    "COL": (39.7487, -105.0077, -2),  # Denver, CO (MT)
    "DAL": (32.7905, -96.8103, -1),   # Dallas, TX (CT)
    "MIN": (44.9449, -93.1011, -1),   # St. Paul, MN (CT)
    "NSH": (36.1591, -86.7784, -1),   # Nashville, TN (CT)
    "STL": (38.6265, -90.2026, -1),   # St. Louis, MO (CT)
    "UTA": (40.7683, -111.9011, -2),  # Salt Lake City, UT (MT) - formerly ARI
    "WPG": (49.8929, -97.1436, -1),   # Winnipeg, MB (CT)

    # Pacific Division
    "ANA": (33.8078, -117.8761, -3),  # Anaheim, CA (PT)
    "CGY": (51.0373, -114.0519, -2),  # Calgary, AB (MT)
    "EDM": (53.5467, -113.4978, -2),  # Edmonton, AB (MT)
    "LAK": (34.0430, -118.2673, -3),  # Los Angeles, CA (PT)
    "SEA": (47.6220, -122.3540, -3),  # Seattle, WA (PT)
    "SJS": (37.3327, -121.9010, -3),  # San Jose, CA (PT)
    "VAN": (49.2778, -123.1089, -3),  # Vancouver, BC (PT)
    "VGK": (36.1027, -115.1783, -3),  # Las Vegas, NV (PT)

    # Legacy teams (for historical data)
    "ARI": (33.4484, -112.0740, -2),  # Phoenix, AZ (MT) - now UTA
    "ATL": (33.7573, -84.3963, 0),    # Atlanta, GA (ET) - now WPG
    "PHX": (33.4484, -112.0740, -2),  # Phoenix, AZ (MT) - same as ARI
}


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate great circle distance between two points in miles.

    Uses Haversine formula to calculate distance on Earth's surface.
    """
    # Earth radius in miles
    R = 3959.0

    # Convert to radians
    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dLat = math.radians(lat2 - lat1)
    dLon = math.radians(lon2 - lon1)

    # Haversine formula
    a = (math.sin(dLat / 2) ** 2 +
         math.cos(lat1_rad) * math.cos(lat2_rad) *
         math.sin(dLon / 2) ** 2)
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c


def add_travel_features(logs: pd.DataFrame) -> pd.DataFrame:
    """
    Add travel distance and timezone features to game logs.

    Features added:
    - travel_distance: Miles traveled from previous game city
    - timezone_change: Timezone difference from previous game (positive = traveling east)
    - is_west_to_east: Whether team traveled from west coast to east coast
    - is_east_to_west: Whether team traveled from east coast to west coast
    """
    logs = logs.copy()

    # Initialize columns
    logs["travel_distance"] = 0.0
    logs["timezone_change"] = 0
    logs["is_west_to_east"] = 0
    logs["is_east_to_west"] = 0

    # Group by team and season to ensure proper ordering
    for (team_id, season), group_df in logs.groupby(["teamId", "season"]):
        # Sort by date
        group_df = group_df.sort_values("gameDate")
        indices = group_df.index

        for i in range(1, len(group_df)):
            prev_idx = indices[i - 1]
            curr_idx = indices[i]

            # Get team abbreviations for current and previous game
            curr_team = group_df.loc[curr_idx, "teamAbbrev"]
            prev_team = group_df.loc[prev_idx, "teamAbbrev"]

            # Determine city locations
            # Previous game: if home, use team's city; if away, use opponent's city
            prev_home_road = group_df.loc[prev_idx, "homeRoad"]
            if prev_home_road == "H":
                prev_city = prev_team
            else:
                prev_opponent = group_df.loc[prev_idx, "opponentTeamAbbrev"]
                prev_city = prev_opponent

            # Current game: if home, use team's city; if away, use opponent's city
            curr_home_road = group_df.loc[curr_idx, "homeRoad"]
            if curr_home_road == "H":
                curr_city = curr_team
            else:
                curr_opponent = group_df.loc[curr_idx, "opponentTeamAbbrev"]
                curr_city = curr_opponent

            # Get location data
            if prev_city in TEAM_LOCATIONS and curr_city in TEAM_LOCATIONS:
                prev_lat, prev_lon, prev_tz = TEAM_LOCATIONS[prev_city]
                curr_lat, curr_lon, curr_tz = TEAM_LOCATIONS[curr_city]

                # Calculate travel distance
                distance = _haversine_distance(prev_lat, prev_lon, curr_lat, curr_lon)
                logs.loc[curr_idx, "travel_distance"] = distance

                # Calculate timezone change
                tz_change = curr_tz - prev_tz
                logs.loc[curr_idx, "timezone_change"] = tz_change

                # Detect coast-to-coast travel
                # West coast = PT (-3), East coast = ET (0)
                is_west_to_east = (prev_tz == -3 and curr_tz == 0)
                is_east_to_west = (prev_tz == 0 and curr_tz == -3)

                logs.loc[curr_idx, "is_west_to_east"] = 1 if is_west_to_east else 0
                logs.loc[curr_idx, "is_east_to_west"] = 1 if is_east_to_west else 0

    return logs
