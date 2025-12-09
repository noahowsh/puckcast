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
# SUPERSAMPLING FOR CRISP OUTPUT
# =============================================================================

# Render at 2x resolution, then downscale for sharp text and graphics
SUPERSAMPLE_SCALE = 2
RENDER_SIZE = 1080 * SUPERSAMPLE_SCALE  # 2160px
OUTPUT_SIZE = 1080  # Final Instagram size


def S(value: int) -> int:
    """Scale a value for supersampled rendering (multiply by 2x)."""
    return value * SUPERSAMPLE_SCALE


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
        # Use 400x400 for high-quality source logos (crisp when scaled down)
        try:
            import cairosvg
            png_data = cairosvg.svg2png(bytestring=svg_data, output_width=400, output_height=400)
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
    """
    Create a high-quality placeholder for missing logos.

    Uses 2x supersampling for smooth edges on the circle and text.
    """
    # Create at 2x size for anti-aliasing, then scale down
    scale = 2
    large_size = size * scale
    img = Image.new("RGBA", (large_size, large_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Draw circle with team color
    color = get_team_primary_rgb(abbrev)
    draw.ellipse([0, 0, large_size - 1, large_size - 1], fill=color)

    # Draw team abbreviation (scaled font)
    font = get_font(large_size // 3, bold=True)
    text = abbrev[:3]
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x = (large_size - text_width) // 2
    y = (large_size - text_height) // 2 - (4 * scale)
    draw.text((x, y), text, fill=(255, 255, 255), font=font)

    # Scale down with high-quality resampling for smooth result
    img = img.resize((size, size), Image.Resampling.LANCZOS)

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
    width: int = None,
    height: int = None,
    top_color: Optional[Tuple[int, int, int]] = None,
    bottom_color: Optional[Tuple[int, int, int]] = None,
) -> Image.Image:
    """Create a vertical gradient background at render size (2x for supersampling)."""
    if width is None:
        width = RENDER_SIZE
    if height is None:
        height = RENDER_SIZE
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


def create_puckcast_background(width: int = None, height: int = None) -> Image.Image:
    """Create the standard Puckcast background with brand glows at render size."""
    if width is None:
        width = RENDER_SIZE
    if height is None:
        height = RENDER_SIZE

    bg = create_gradient_background(width, height)

    # Scale glow radius based on render size
    scale = width / 1080

    # Add aqua glow top-left
    bg = add_glow_effect(
        bg,
        color=hex_to_rgb(PuckcastColors.AQUA),
        position=(int(width * 0.2), int(height * 0.15)),
        radius=int(350 * scale),
        opacity=0.12,
    )

    # Add amber glow top-right
    bg = add_glow_effect(
        bg,
        color=hex_to_rgb(PuckcastColors.AMBER),
        position=(int(width * 0.8), int(height * 0.1)),
        radius=int(300 * scale),
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


def draw_glass_tile(
    img: Image.Image,
    y_position: int,
    height: int = 110,
    margin: int = 50,
    highlight: bool = False,
    highlight_color: Tuple[int, int, int] = None,
) -> Image.Image:
    """
    Draw a modern glass-morphism style tile with subtle gradients.

    Returns the composited image.
    """
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    overlay_draw = ImageDraw.Draw(overlay)

    coords = (margin, y_position, img.width - margin, y_position + height)

    if highlight and highlight_color:
        # Highlighted tile with accent color
        fill_color = (*highlight_color, 25)
        border_color = (*highlight_color, 60)
    else:
        # Standard glass tile
        fill_color = (255, 255, 255, 10)
        border_color = (255, 255, 255, 30)

    # Draw main tile
    draw_rounded_rect(overlay_draw, coords, radius=14, fill=fill_color, outline=border_color, width=1)

    # Add subtle top highlight for glass effect
    highlight_coords = (margin + 1, y_position + 1, img.width - margin - 1, y_position + 3)
    draw_rounded_rect(overlay_draw, highlight_coords, radius=14, fill=(255, 255, 255, 15))

    # Composite
    img_rgba = img.convert("RGBA")
    result = Image.alpha_composite(img_rgba, overlay)

    return result


def draw_header(
    img: Image.Image,
    title: str,
    subtitle: str = None,
    margin: int = 60,
    compact: bool = False,
) -> int:
    """
    Draw a professional header section with title and optional subtitle.

    Returns the y position after the header.
    """
    draw = ImageDraw.Draw(img)

    # Title - larger and bolder for impact
    title_size = FontSizes.TITLE if not compact else 52
    title_font = get_font(title_size, bold=True)
    title_color = hex_to_rgb(PuckcastColors.TEXT_PRIMARY)

    y = margin + 15 if compact else margin + 25
    draw.text((margin, y), title, fill=title_color, font=title_font)
    y += title_size + 8

    # Subtitle - cleaner secondary text
    if subtitle:
        subtitle_size = 26 if compact else 30
        subtitle_font = get_font(subtitle_size, bold=False)
        subtitle_color = hex_to_rgb(PuckcastColors.TEXT_SECONDARY)
        draw.text((margin, y), subtitle, fill=subtitle_color, font=subtitle_font)
        y += subtitle_size + 8

    # Draw gradient separator line for visual polish
    y += 12

    # Create a subtle gradient line effect
    line_length = img.width - margin * 2
    aqua_rgb = hex_to_rgb(PuckcastColors.AQUA)

    # Main line with glow effect
    for offset in range(3):
        alpha_factor = 1.0 - (offset * 0.3)
        line_y = y + offset
        line_color = tuple(int(c * alpha_factor) for c in aqua_rgb)
        draw.line([(margin, line_y), (margin + line_length // 3, line_y)], fill=line_color, width=2 - offset)

    y += 25

    return y


def draw_footer(
    img: Image.Image,
    margin: int = None,
) -> None:
    """Draw footer with logo and PUCKCAST text. Auto-scales for supersampling."""
    # Auto-detect scale based on image size
    scale = img.width / 1080
    if margin is None:
        margin = int(40 * scale)

    draw = ImageDraw.Draw(img)
    brand_text = "PUCKCAST"
    font_size = int(24 * scale)
    font = get_font(font_size, bold=True)
    text_color = hex_to_rgb(PuckcastColors.AQUA)

    # Get text dimensions
    text_bbox = draw.textbbox((0, 0), brand_text, font=font)
    text_width = text_bbox[2] - text_bbox[0]
    text_height = text_bbox[3] - text_bbox[1]

    # Load the Puckcast logo
    logo_path = ASSETS_DIR / "puckcastai.png"
    logo = None
    logo_width = 0
    logo_height = int(36 * scale)

    if logo_path.exists():
        try:
            logo = Image.open(logo_path).convert("RGBA")
            aspect = logo.width / logo.height
            logo_width = int(logo_height * aspect)
            logo = logo.resize((logo_width, logo_height), Image.Resampling.LANCZOS)
        except Exception:
            logo = None

    # Calculate total width (logo + gap + text)
    gap = int(12 * scale) if logo else 0
    total_width = logo_width + gap + text_width if logo else text_width

    # Center everything horizontally
    start_x = (img.width - total_width) // 2
    y = img.height - margin - max(logo_height, text_height)

    # Draw logo if available
    if logo:
        logo_y = y + (max(logo_height, text_height) - logo_height) // 2
        if img.mode != "RGBA":
            img_rgba = img.convert("RGBA")
            img_rgba.paste(logo, (start_x, logo_y), logo)
            img.paste(img_rgba.convert("RGB"))
        else:
            img.paste(logo, (start_x, logo_y), logo)

    # Draw brand text
    text_x = start_x + logo_width + gap if logo else start_x
    text_y = y + (max(logo_height, text_height) - text_height) // 2 - int(4 * scale)
    draw.text((text_x, text_y), brand_text, fill=text_color, font=font)


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


def save_high_quality(img: Image.Image, output_path: Path, downscale: bool = True) -> None:
    """
    Save image with optimal quality settings for crisp social media graphics.

    - Downscales from 2160px to 1080px using LANCZOS for sharp results
    - Uses PNG format (lossless)
    - Sets 144 DPI for retina/high-density displays
    - Converts to RGB mode for compatibility

    Args:
        img: The image to save (should be rendered at RENDER_SIZE for best quality)
        output_path: Where to save the image
        downscale: If True, downscale from RENDER_SIZE to OUTPUT_SIZE
    """
    # Downscale from 2x render size to final output size
    if downscale and img.width > OUTPUT_SIZE:
        img = img.resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.Resampling.LANCZOS)

    # Ensure RGB mode for final output (social media compatible)
    if img.mode == "RGBA":
        # Create background and composite
        background = Image.new("RGB", img.size, (10, 14, 26))  # Match dark theme
        background.paste(img, mask=img.split()[3])  # Use alpha channel as mask
        img = background
    elif img.mode != "RGB":
        img = img.convert("RGB")

    # Save with high DPI for crisp rendering on retina displays
    img.save(
        output_path,
        "PNG",
        optimize=True,
        dpi=(144, 144),
    )


def clear_logo_cache() -> None:
    """
    Clear the logo cache to force re-download at higher resolution.

    Call this after updating logo resolution settings.
    """
    if LOGOS_DIR.exists():
        for logo_file in LOGOS_DIR.glob("*.png"):
            logo_file.unlink()
        print(f"Cleared {LOGOS_DIR} logo cache")
