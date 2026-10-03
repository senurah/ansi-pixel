"""Image processing, resizing, and pixel extraction engine for ansi-pixel."""

from __future__ import annotations

import io
import os
import shutil
import sys
import urllib.error
import urllib.parse
import urllib.request
from enum import Enum
from typing import BinaryIO, Union, cast

from PIL import Image

from ansi_pixel.optimizer import AnsiOptimizer, RGBColor, strip_ansi

# Type aliases for public API inputs
ImageSource = Union[str, "os.PathLike[str]", BinaryIO, Image.Image, bytes]


def get_terminal_width(fallback: int = 80) -> int:
    """Auto-detect current terminal width using shutil.get_terminal_size().

    Args:
        fallback: Fallback column count if terminal width cannot be determined.

    Returns:
        Terminal width in character columns (at least 1).
    """
    try:
        cols = shutil.get_terminal_size(fallback=(fallback, 24)).columns
        return max(1, cols)
    except Exception:
        return max(1, fallback)


def is_url(source: str) -> bool:
    """Determine whether a string represents an HTTP or HTTPS URL.

    Args:
        source: Path or URL candidate string.

    Returns:
        True if source is an HTTP/HTTPS URL, False otherwise.
    """
    try:
        parsed = urllib.parse.urlparse(source)
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)
    except Exception:
        return False


def fetch_url(url: str, timeout: float = 15.0) -> bytes:
    """Fetch binary image content from an HTTP or HTTPS URL.

    Args:
        url: Direct image URL to download.
        timeout: Network timeout in seconds (default: 15.0).

    Returns:
        Raw downloaded image bytes.

    Raises:
        urllib.error.HTTPError: If server responds with HTTP error code.
        urllib.error.URLError: If network error or host unreachable.
        TimeoutError: If the request exceeds timeout seconds.
    """
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "ansi-pixel (https://github.com/senurah/ansi-pixel)",
            "Accept": "image/*,*/*;q=0.8",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as response:
        return cast(bytes, response.read())


class ResamplingFilter(str, Enum):
    """Supported image resampling filters."""

    NEAREST = "nearest"
    LANCZOS = "lanczos"
    BILINEAR = "bilinear"

    def to_pil(self) -> Image.Resampling:
        """Convert to the corresponding Pillow Resampling enum."""
        if self is ResamplingFilter.NEAREST:
            return Image.Resampling.NEAREST
        if self is ResamplingFilter.LANCZOS:
            return Image.Resampling.LANCZOS
        if self is ResamplingFilter.BILINEAR:
            return Image.Resampling.BILINEAR
        raise ValueError(f"Unsupported resampling filter: {self}")


FilterInput = Union[str, ResamplingFilter, Image.Resampling]


def parse_resampling_filter(filter_val: FilterInput) -> Image.Resampling:
    """Resolve a filter argument into a Pillow Resampling enum.

    Args:
        filter_val: String name ('nearest', 'lanczos', 'bilinear'), ResamplingFilter,
            or PIL Image.Resampling enum.

    Returns:
        Pillow Image.Resampling value.

    Raises:
        ValueError: If the filter name is not recognized.
        TypeError: If filter_val has an invalid type.
    """
    if isinstance(filter_val, Image.Resampling):
        return filter_val
    if isinstance(filter_val, ResamplingFilter):
        return filter_val.to_pil()
    if isinstance(filter_val, str):
        try:
            return ResamplingFilter(filter_val.lower()).to_pil()
        except ValueError as exc:
            valid = ", ".join(f.value for f in ResamplingFilter)
            raise ValueError(f"Unknown filter '{filter_val}'. Valid choices: {valid}") from exc
    raise TypeError(f"Invalid filter type: {type(filter_val).__name__}")


def parse_hex_color(hex_str: str) -> RGBColor:
    """Parse a 3 or 6-character hex color string into an (R, G, B) tuple.

    Args:
        hex_str: Hex color string (e.g. '#FFFFFF', 'FFFFFF', '#FFF', 'FFF').

    Returns:
        A tuple of 3 integers (0-255) representing (Red, Green, Blue).

    Raises:
        ValueError: If hex_str is not a valid 3-digit or 6-digit hex color.
    """
    clean = hex_str.strip().lstrip("#")
    if len(clean) == 3:
        clean = "".join(c * 2 for c in clean)
    if len(clean) != 6:
        raise ValueError(
            f"Invalid hex color '{hex_str}'. Expected 3 or 6 hex digits (e.g. '#FFFFFF' or 'FFF')."
        )
    try:
        r = int(clean[0:2], 16)
        g = int(clean[2:4], 16)
        b = int(clean[4:6], 16)
        return (r, g, b)
    except ValueError as exc:
        raise ValueError(f"Invalid hex color '{hex_str}': non-hexadecimal characters.") from exc


def _is_pixel_empty(
    r: int,
    g: int,
    b: int,
    a: int,
    *,
    alpha_threshold: int = 128,
    trim_bg: bool = False,
    chroma_color: RGBColor | None = None,
    chroma_tolerance: int = 15,
) -> bool:
    """Determine whether a pixel should be treated as transparent space.

    By default, transparency is governed strictly by the alpha channel (a < alpha_threshold).
    White pixels are fully preserved unless intentional stripping is requested via trim_bg
    or chroma_color.
    """
    if a < alpha_threshold:
        return True
    if trim_bg and (r > 245 and g > 245 and b > 245):
        return True
    if chroma_color is not None:
        cr, cg, cb = chroma_color
        if (
            abs(r - cr) <= chroma_tolerance
            and abs(g - cg) <= chroma_tolerance
            and abs(b - cb) <= chroma_tolerance
        ):
            return True
    return False


def _find_content_bbox(
    img: Image.Image,
    *,
    alpha_threshold: int = 128,
    trim_bg: bool = False,
    chroma_color: RGBColor | None = None,
    chroma_tolerance: int = 15,
) -> tuple[int, int, int, int] | None:
    """Find the non-empty bounding box of an image using fast direct buffer access."""
    width, height = img.size
    pixels = img.load()
    if pixels is None:
        raise RuntimeError("Failed to load image pixel buffer.")

    min_x = width
    min_y = height
    max_x = -1
    max_y = -1

    for y in range(height):
        for x in range(width):
            r, g, b, a = cast("tuple[int, int, int, int]", pixels[x, y])
            if not _is_pixel_empty(
                r,
                g,
                b,
                a,
                alpha_threshold=alpha_threshold,
                trim_bg=trim_bg,
                chroma_color=chroma_color,
                chroma_tolerance=chroma_tolerance,
            ):
                if x < min_x:
                    min_x = x
                if x > max_x:
                    max_x = x
                if y < min_y:
                    min_y = y
                if y > max_y:
                    max_y = y

    if max_x < min_x or max_y < min_y:
        return None

    return (min_x, min_y, max_x + 1, max_y + 1)


def image_to_ansi(
    image: ImageSource,
    target_width: int | None = None,
    *,
    width: int | None = None,
    filter: FilterInput = ResamplingFilter.NEAREST,
    trim_bg: bool = False,
    chroma_key: str | RGBColor | None = None,
    chroma_tolerance: int = 15,
    alpha_threshold: int = 128,
    color: bool = True,
) -> list[str]:
    """Convert an image into an optimized list of true-color ANSI art strings.

    Args:
        image: Path to image file, URL, '-' for stdin, open binary file-like object,
            raw bytes, or PIL Image.Image.
        target_width: Desired output width in terminal characters (default: auto-detected).
        width: Alias for target_width.
        filter: Resampling filter ('nearest', 'lanczos', 'bilinear').
        trim_bg: If True, treat near-white backgrounds as transparent and crop borders.
        chroma_key: Hex color string (e.g. '#FFFFFF') or RGB tuple to strip as transparent.
        chroma_tolerance: Matching tolerance for chroma key (default: 15).
        alpha_threshold: Alpha cutoff for transparency (0-255, default: 128).
        color: If False, strip ANSI color sequences from output (default: True).

    Returns:
        A list of strings, each representing one terminal line with optimized ANSI sequences.
    """
    resolved_width = width if width is not None else target_width
    if resolved_width is None:
        resolved_width = get_terminal_width()

    if resolved_width < 1:
        raise ValueError("target_width must be at least 1.")

    target_width = resolved_width

    if isinstance(image, Image.Image):
        img = image.convert("RGBA")
    elif isinstance(image, str) and image == "-":
        data = sys.stdin.buffer.read()
        if not data:
            raise ValueError("Standard input is empty.")
        with Image.open(io.BytesIO(data)) as opened:
            img = opened.convert("RGBA")
    elif isinstance(image, str) and is_url(image):
        data = fetch_url(image)
        with Image.open(io.BytesIO(data)) as opened:
            img = opened.convert("RGBA")
    elif isinstance(image, bytes):
        with Image.open(io.BytesIO(image)) as opened:
            img = opened.convert("RGBA")
    else:
        with Image.open(image) as opened:
            img = opened.convert("RGBA")

    chroma_color: RGBColor | None = None
    if isinstance(chroma_key, str):
        chroma_color = parse_hex_color(chroma_key)
    elif chroma_key is not None:
        chroma_color = chroma_key

    # 1. Auto-crop empty borders
    if trim_bg or chroma_color is not None:
        bbox = _find_content_bbox(
            img,
            alpha_threshold=alpha_threshold,
            trim_bg=trim_bg,
            chroma_color=chroma_color,
            chroma_tolerance=chroma_tolerance,
        )
        if bbox:
            img = img.crop(bbox)
    else:
        bbox = img.getbbox()
        if bbox:
            img = img.crop(bbox)

    # 2. Resize keeping aspect ratio
    aspect = img.height / img.width
    # Target height must be even because each line renders 2 vertical pixels
    target_height = int(target_width * aspect)
    if target_height % 2 != 0:
        target_height += 1
    if target_height < 2:
        target_height = 2

    pil_filter = parse_resampling_filter(filter)
    img = img.resize((target_width, target_height), pil_filter)

    # 3. Process pairs of vertical rows via direct pixel buffer and ANSI optimizer
    pixels = img.load()
    if pixels is None:
        raise RuntimeError("Failed to load image pixel buffer.")
    lines: list[str] = []
    optimizer = AnsiOptimizer()

    for y in range(0, target_height, 2):
        row_cells: list[tuple[RGBColor | None, RGBColor | None]] = []
        has_bottom = y + 1 < target_height
        for x in range(target_width):
            top_r, top_g, top_b, top_a = cast("tuple[int, int, int, int]", pixels[x, y])
            if has_bottom:
                bot_r, bot_g, bot_b, bot_a = cast("tuple[int, int, int, int]", pixels[x, y + 1])
            else:
                bot_r, bot_g, bot_b, bot_a = (0, 0, 0, 0)

            top_empty = _is_pixel_empty(
                top_r,
                top_g,
                top_b,
                top_a,
                alpha_threshold=alpha_threshold,
                trim_bg=trim_bg,
                chroma_color=chroma_color,
                chroma_tolerance=chroma_tolerance,
            )
            bot_empty = _is_pixel_empty(
                bot_r,
                bot_g,
                bot_b,
                bot_a,
                alpha_threshold=alpha_threshold,
                trim_bg=trim_bg,
                chroma_color=chroma_color,
                chroma_tolerance=chroma_tolerance,
            )

            top_color: RGBColor | None = None if top_empty else (top_r, top_g, top_b)
            bot_color: RGBColor | None = None if bot_empty else (bot_r, bot_g, bot_b)
            row_cells.append((top_color, bot_color))

        lines.append(optimizer.optimize_row(row_cells))

    if not color:
        lines = [strip_ansi(line) for line in lines]

    return lines
