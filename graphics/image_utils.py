"""
Image utilities for Puckcast graphic generation.

This module provides common utilities for creating Instagram-ready graphics:
- Background generation with gradients
- Logo loading and caching
- Text rendering with custom fonts
- Common UI elements (tiles, badges, etc.)
"""

from __future__ import annotations

import io
import hashlib
import ssl
from pathlib import Path
from typing import Tuple, Optional
from urllib.request import Request, urlopen

from PIL import Image, ImageDraw, ImageFont, ImageFilter

from puckcast_brand import (
    PuckcastColors,
    hex_to_rgb,
    hex_to_rgba,
    get_team_colors,
    get_team_primary_rgb,
    ImageDimensions,
)

# =============================================================================
# PATHS
# =============================================================================

GRAPHICS_DIR = Path(__file__).resolve().parent
ASSETS_DIR = GRAPHICS_DIR / "assets"
LOGOS_DIR = ASSETS_DIR / "logos"
OUTPUT_DIR = GRAPHICS_DIR / "output"
FONTS_DIR = GRAPHICS_DIR / "fonts"

# Ensure directories exist
LOGOS_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# =============================================================================
# FONT LOADING
# =============================================================================

def get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    """
    Get a font at the specified size.

    Falls back to default font if custom fonts aren't available.
    """
    # Try to use Inter or a system font
    font_names = [
        "Inter-Bold.ttf" if bold else "Inter-Regular.ttf",
        "Inter-SemiBold.ttf" if bold else "Inter-Medium.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]

    for font_name in font_names:
        try:
            if font_name.startswith("/"):
                return ImageFont.truetype(font_name, size)
            else:
                font_path = FONTS_DIR / font_name
                if font_path.exists():
                    return ImageFont.truetype(str(font_path), size)
        except (IOError, OSError):
            continue

    # Fallback to default
    try:
        return ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", size)
    except:
        return ImageFont.load_default()


# Font size presets
class FontSizes:
    TITLE = 64
    SUBTITLE = 42
    HEADING = 36
    BODY = 28
    CAPTION = 22
    SMALL = 18
    TINY = 14


# =============================================================================
# LOGO LOADING & CACHING
# =============================================================================

def download_logo(abbrev: str, force: bool = False) -> Optional[Path]:
    """
    Download and cache team logo as PNG.

    Args:
        abbrev: Team abbreviation (e.g., 'TOR')
        force: Force re-download even if cached

    Returns:
        Path to cached PNG logo, or None if download fails
    """
    abbrev = abbrev.upper()
    cache_path = LOGOS_DIR / f"{abbrev}.png"

    if cache_path.exists() and not force:
        return cache_path

    # Download SVG from NHL CDN
    url = f"https://assets.nhle.com/logos/nhl/svg/{abbrev}_light.svg"

    try:
        req = Request(url, headers={"User-Agent": "Mozilla/5.0"})
        context = ssl._create_unverified_context()

        with urlopen(req, timeout=10, context=context) as response:
            svg_data = response.read()

        # Convert SVG to PNG using cairosvg if available, otherwise save raw
        try:
            import cairosvg
            png_data = cairosvg.svg2png(bytestring=svg_data, output_width=200, output_height=200)
            cache_path.write_bytes(png_data)
        except ImportError:
            # Fallback: save SVG and note that we need cairosvg
            svg_path = LOGOS_DIR / f"{abbrev}.svg"
            svg_path.write_bytes(svg_data)
            print(f"  Note: Install cairosvg for PNG conversion. Saved SVG: {svg_path}")
            return None

        return cache_path

    except Exception as e:
        print(f"  Failed to download logo for {abbrev}: {e}")
        return None


def load_logo(abbrev: str, size: int = 80) -> Optional[Image.Image]:
    """
    Load team logo, downloading if necessary.

    Args:
        abbrev: Team abbreviation
        size: Target size (width and height)

    Returns:
        PIL Image or None if not available
    """
    logo_path = download_logo(abbrev)

    if logo_path is None or not logo_path.exists():
        return None

    try:
        logo = Image.open(logo_path).convert("RGBA")
        logo = logo.resize((size, size), Image.Resampling.LANCZOS)
        return logo
    except Exception as e:
        print(f"  Failed to load logo for {abbrev}: {e}")
        return None


def create_logo_placeholder(abbrev: str, size: int = 80) -> Image.Image:
    """Create a placeholder for missing logos."""
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw circle with team color
    color = get_team_primary_rgb(abbrev)
    draw.ellipse([0, 0, size - 1, size - 1], fill=color)

    # Draw team abbreviation
    font = get_font(size // 3, bold=True)
    text = abbrev[:3]
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (size - text_width) // 2
    y = (size - text_height) // 2 - 4
    draw.text((x, y), text, fill=(255, 255, 255), font=font)

    return img


def get_logo(abbrev: str, size: int = 80) -> Image.Image:
    """Get team logo, with fallback to placeholder."""
    logo = load_logo(abbrev, size)
    if logo is None:
        return create_logo_placeholder(abbrev, size)
    return logo


# =============================================================================
# BACKGROUND GENERATION
# =============================================================================

def create_gradient_background(
    width: int = 1080,
    height: int = 1080,
    top_color: Optional[Tuple[int, int, int]] = None,
    bottom_color: Optional[Tuple[int, int, int]] = None,
) -> Image.Image:
    """Create a vertical gradient background."""
    if top_color is None:
        top_color = hex_to_rgb("#0a0e1a")
    if bottom_color is None:
        bottom_color = hex_to_rgb("#020510")

    img = Image.new("RGB", (width, height))
    pixels = img.load()

    for y in range(height):
        ratio = y / height
        r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
        g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
        b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
        for x in range(width):
            pixels[x, y] = (r, g, b)

    return img


def add_glow_effect(
    img: Image.Image,
    color: Tuple[int, int, int] = None,
    position: Tuple[int, int] = None,
    radius: int = 300,
    opacity: float = 0.15,
) -> Image.Image:
    """Add a subtle glow effect to the background."""
    if color is None:
        color = hex_to_rgb(PuckcastColors.AQUA)
    if position is None:
        position = (img.width // 4, img.height // 6)

    # Create glow layer
    glow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    glow_draw = ImageDraw.Draw(glow)

    # Draw radial gradient
    for r in range(radius, 0, -1):
        alpha = int((1 - r / radius) * opacity * 255)
        glow_draw.ellipse(
            [
                position[0] - r,
                position[1] - r,
                position[0] + r,
                position[1] + r,
            ],
            fill=(*color, alpha),
        )

    # Blur the glow
    glow = glow.filter(ImageFilter.GaussianBlur(radius // 3))

    # Composite
    result = img.convert("RGBA")
    result = Image.alpha_composite(result, glow)
    return result.convert("RGB")


def create_puckcast_background(width: int = 1080, height: int = 1080) -> Image.Image:
    """Create the standard Puckcast background with brand glows."""
    bg = create_gradient_background(width, height)

    # Add aqua glow top-left
    bg = add_glow_effect(
        bg,
        color=hex_to_rgb(PuckcastColors.AQUA),
        position=(int(width * 0.2), int(height * 0.15)),
        radius=350,
        opacity=0.12,
    )

    # Add amber glow top-right
    bg = add_glow_effect(
        bg,
        color=hex_to_rgb(PuckcastColors.AMBER),
        position=(int(width * 0.8), int(height * 0.1)),
        radius=300,
        opacity=0.10,
    )

    return bg


# =============================================================================
# UI ELEMENTS
# =============================================================================

def draw_rounded_rect(
    draw: ImageDraw.Draw,
    coords: Tuple[int, int, int, int],
    radius: int = 20,
    fill: Optional[Tuple] = None,
    outline: Optional[Tuple] = None,
    width: int = 1,
) -> None:
    """Draw a rounded rectangle."""
    x1, y1, x2, y2 = coords

    if fill:
        # Draw filled rounded rectangle
        draw.rounded_rectangle(coords, radius=radius, fill=fill, outline=outline, width=width)
    elif outline:
        draw.rounded_rectangle(coords, radius=radius, outline=outline, width=width)


def draw_tile(
    img: Image.Image,
    y_position: int,
    height: int = 120,
    margin: int = 60,
    fill: Tuple[int, int, int, int] = (255, 255, 255, 8),
    border_color: Tuple[int, int, int, int] = (255, 255, 255, 20),
    radius: int = 16,
) -> None:
    """Draw a semi-transparent tile on the image."""
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    coords = (margin, y_position, img.width - margin, y_position + height)
    draw_rounded_rect(draw, coords, radius=radius, fill=fill, outline=border_color, width=1)

    # Composite
    if img.mode != "RGBA":
        img = img.convert("RGBA")

    result = Image.alpha_composite(img, overlay)
    img.paste(result)


def draw_header(
    img: Image.Image,
    title: str,
    subtitle: str = None,
    margin: int = 60,
) -> int:
    """
    Draw the header section with title and optional subtitle.

    Returns the y position after the header.
    """
    draw = ImageDraw.Draw(img)

    # Title
    title_font = get_font(FontSizes.TITLE, bold=True)
    title_color = hex_to_rgb(PuckcastColors.TEXT_PRIMARY)

    y = margin + 20
    draw.text((margin, y), title, fill=title_color, font=title_font)
    y += FontSizes.TITLE + 10

    # Subtitle
    if subtitle:
        subtitle_font = get_font(FontSizes.SUBTITLE, bold=False)
        subtitle_color = hex_to_rgb(PuckcastColors.TEXT_SECONDARY)
        draw.text((margin, y), subtitle, fill=subtitle_color, font=subtitle_font)
        y += FontSizes.SUBTITLE + 10

    # Draw separator line
    y += 20
    line_color = hex_to_rgba(PuckcastColors.AQUA, 80)
    draw.line([(margin, y), (img.width - margin, y)], fill=line_color[:3], width=2)
    y += 30

    return y


def draw_footer(
    img: Image.Image,
    text: str = "puckcast.ai",
    margin: int = 60,
) -> None:
    """Draw the footer with branding."""
    draw = ImageDraw.Draw(img)

    font = get_font(FontSizes.CAPTION, bold=True)
    color = hex_to_rgb(PuckcastColors.AMBER)

    # Calculate position
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x = (img.width - text_width) // 2
    y = img.height - margin - FontSizes.CAPTION

    draw.text((x, y), text, fill=color, font=font)


def draw_badge(
    draw: ImageDraw.Draw,
    position: Tuple[int, int],
    text: str,
    bg_color: Tuple[int, int, int],
    text_color: Tuple[int, int, int] = (255, 255, 255),
    font_size: int = 20,
    padding: Tuple[int, int] = (12, 6),
) -> Tuple[int, int]:
    """
    Draw a badge with text.

    Returns the width and height of the badge.
    """
    font = get_font(font_size, bold=True)
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    badge_width = text_width + padding[0] * 2
    badge_height = text_height + padding[1] * 2

    x, y = position
    coords = (x, y, x + badge_width, y + badge_height)

    draw_rounded_rect(draw, coords, radius=badge_height // 2, fill=bg_color)
    draw.text((x + padding[0], y + padding[1] - 2), text, fill=text_color, font=font)

    return badge_width, badge_height


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def format_probability(prob: float) -> str:
    """Format probability as percentage string."""
    return f"{prob * 100:.0f}%"


def format_edge(edge: float) -> str:
    """Format edge score."""
    if edge >= 0:
        return f"+{edge * 100:.1f}"
    return f"{edge * 100:.1f}"


def truncate_text(text: str, max_length: int = 20) -> str:
    """Truncate text with ellipsis if too long."""
    if len(text) <= max_length:
        return text
    return text[:max_length - 3] + "..."
