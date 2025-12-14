"""
Puckcast Brand Design System for Image Generation.

This module contains all brand colors, fonts, and styling utilities
for generating Instagram-ready graphics.
"""

from dataclasses import dataclass
from typing import Tuple

# =============================================================================
# BRAND COLORS (from Puckcast Polaris Design System)
# =============================================================================

@dataclass
class PuckcastColors:
    """Core Puckcast brand colors."""

    # Primary brand colors
    AQUA = "#7ee3ff"
    ICE = "#8ac6ff"
    MINT = "#6ef0c2"
    AMBER = "#f6c177"
    ACCENT_GOLD = "#f1d9a6"
    ROSE = "#ff94a8"

    # Background colors
    PAGE_INK = "#030712"
    PAGE_VOID = "#020510"
    PANEL_DARK = "#050a14"
    PANEL_MEDIUM = "#070c18"

    # Text colors
    TEXT_PRIMARY = "#f6f8fb"
    TEXT_SECONDARY = "#c7cfdf"
    TEXT_TERTIARY = "#9aa7bd"

    # Confidence grade colors
    CONFIDENCE_S = "#7ee3ff"  # S tier
    CONFIDENCE_A = "#6ef0c2"  # A tier
    CONFIDENCE_B = "#f6c177"  # B tier
    CONFIDENCE_C = "#ff94a8"  # C tier

    # Status colors
    SUCCESS = "#22c55e"
    WARNING = "#f59f57"
    ERROR = "#ef4444"

    # Trend colors
    RISING = "#22c55e"
    FALLING = "#ef4444"
    STEADY = "#9aa7bd"


# RGB versions for Pillow
def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    """Convert hex color to RGBA tuple."""
    r, g, b = hex_to_rgb(hex_color)
    return (r, g, b, alpha)


# =============================================================================
# TEAM COLORS
# =============================================================================

TEAM_COLORS = {
    "ANA": {"primary": "#F47A38", "secondary": "#B9975B"},
    "BOS": {"primary": "#FFB81C", "secondary": "#000000"},
    "BUF": {"primary": "#003087", "secondary": "#FDBB2F"},
    "CAR": {"primary": "#CC0000", "secondary": "#000000"},
    "CBJ": {"primary": "#002654", "secondary": "#CE1126"},
    "CGY": {"primary": "#C8102E", "secondary": "#F1BE48"},
    "CHI": {"primary": "#CF0A2C", "secondary": "#000000"},
    "COL": {"primary": "#6F263D", "secondary": "#236192"},
    "DAL": {"primary": "#006847", "secondary": "#8F8F8C"},
    "DET": {"primary": "#CE1126", "secondary": "#FFFFFF"},
    "EDM": {"primary": "#041E42", "secondary": "#FF4C00"},
    "FLA": {"primary": "#041E42", "secondary": "#C8102E"},
    "LAK": {"primary": "#111111", "secondary": "#A2AAAD"},
    "MIN": {"primary": "#154734", "secondary": "#A6192E"},
    "MTL": {"primary": "#AF1E2D", "secondary": "#001E62"},
    "NJD": {"primary": "#CE1126", "secondary": "#000000"},
    "NSH": {"primary": "#FFB81C", "secondary": "#041E42"},
    "NYI": {"primary": "#00539B", "secondary": "#F47D30"},
    "NYR": {"primary": "#0038A8", "secondary": "#CE1126"},
    "OTT": {"primary": "#C8102E", "secondary": "#C8B07E"},
    "PHI": {"primary": "#F74902", "secondary": "#000000"},
    "PIT": {"primary": "#FFB81C", "secondary": "#000000"},
    "SEA": {"primary": "#001628", "secondary": "#99D9D9"},
    "SJS": {"primary": "#006272", "secondary": "#EA7200"},
    "STL": {"primary": "#002F87", "secondary": "#FCB514"},
    "TBL": {"primary": "#002868", "secondary": "#002868"},
    "TOR": {"primary": "#00205B", "secondary": "#FFFFFF"},
    "UTA": {"primary": "#6CACE4", "secondary": "#000000"},
    "VAN": {"primary": "#00205B", "secondary": "#00843D"},
    "VGK": {"primary": "#B4975A", "secondary": "#333F42"},
    "WPG": {"primary": "#041E42", "secondary": "#AC162C"},
    "WSH": {"primary": "#041E42", "secondary": "#C8102E"},
}


def get_team_colors(abbrev: str) -> dict:
    """Get team colors by abbreviation."""
    return TEAM_COLORS.get(abbrev.upper(), {"primary": "#7ee3ff", "secondary": "#6ef0c2"})


def get_team_primary_rgb(abbrev: str) -> Tuple[int, int, int]:
    """Get team primary color as RGB."""
    colors = get_team_colors(abbrev)
    return hex_to_rgb(colors["primary"])


def get_team_secondary_rgb(abbrev: str) -> Tuple[int, int, int]:
    """Get team secondary color as RGB."""
    colors = get_team_colors(abbrev)
    return hex_to_rgb(colors["secondary"])


# =============================================================================
# TEAM NAMES
# =============================================================================

TEAM_NAMES = {
    "ANA": "Ducks",
    "BOS": "Bruins",
    "BUF": "Sabres",
    "CGY": "Flames",
    "CAR": "Hurricanes",
    "CHI": "Blackhawks",
    "COL": "Avalanche",
    "CBJ": "Blue Jackets",
    "DAL": "Stars",
    "DET": "Red Wings",
    "EDM": "Oilers",
    "FLA": "Panthers",
    "LAK": "Kings",
    "MIN": "Wild",
    "MTL": "Canadiens",
    "NSH": "Predators",
    "NJD": "Devils",
    "NYI": "Islanders",
    "NYR": "Rangers",
    "OTT": "Senators",
    "PHI": "Flyers",
    "PIT": "Penguins",
    "SJS": "Sharks",
    "SEA": "Kraken",
    "STL": "Blues",
    "TBL": "Lightning",
    "TOR": "Maple Leafs",
    "UTA": "Utah HC",
    "VAN": "Canucks",
    "VGK": "Golden Knights",
    "WSH": "Capitals",
    "WPG": "Jets",
}


def get_team_name(abbrev: str) -> str:
    """Get team name by abbreviation."""
    return TEAM_NAMES.get(abbrev.upper(), abbrev)


# =============================================================================
# IMAGE DIMENSIONS
# =============================================================================

@dataclass
class ImageDimensions:
    """Standard image dimensions for social media."""

    # Instagram square
    SQUARE = (1080, 1080)

    # Instagram story / reels
    STORY = (1080, 1920)

    # Twitter / X
    TWITTER = (1200, 675)

    # Margins and padding
    MARGIN = 60
    PADDING = 40

    # Header heights
    HEADER_HEIGHT = 180
    SUBHEADER_HEIGHT = 80

    # Tile dimensions
    TILE_HEIGHT = 140
    LOGO_SIZE = 80
    LOGO_SIZE_SMALL = 60


# =============================================================================
# GRADIENT UTILITIES
# =============================================================================

def create_gradient_background(
    width: int,
    height: int,
    top_color: Tuple[int, int, int] = None,
    bottom_color: Tuple[int, int, int] = None,
) -> list:
    """Create a vertical gradient as a list of RGB tuples for each row."""
    if top_color is None:
        top_color = hex_to_rgb(PuckcastColors.PANEL_DARK)
    if bottom_color is None:
        bottom_color = hex_to_rgb(PuckcastColors.PAGE_VOID)

    gradient = []
    for y in range(height):
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        gradient.append((r, g, b))

    return gradient


# =============================================================================
# CONFIDENCE GRADE UTILITIES
# =============================================================================

def get_confidence_color(grade: str) -> str:
    """Get color for confidence grade."""
    grade = grade.upper().replace("-", "").replace("+", "")
    if grade.startswith("A"):
        return PuckcastColors.CONFIDENCE_A
    elif grade.startswith("B"):
        return PuckcastColors.CONFIDENCE_B
    elif grade.startswith("C"):
        return PuckcastColors.CONFIDENCE_C
    else:
        return PuckcastColors.CONFIDENCE_S


def get_confidence_color_rgb(grade: str) -> Tuple[int, int, int]:
    """Get RGB color for confidence grade."""
    return hex_to_rgb(get_confidence_color(grade))


# =============================================================================
# LOGO UTILITIES
# =============================================================================

def get_logo_url(abbrev: str) -> str:
    """Get NHL team logo URL."""
    return f"https://assets.nhle.com/logos/nhl/svg/{abbrev.upper()}_light.svg"


def get_logo_url_dark(abbrev: str) -> str:
    """Get NHL team logo URL (dark version)."""
    return f"https://assets.nhle.com/logos/nhl/svg/{abbrev.upper()}_dark.svg"
