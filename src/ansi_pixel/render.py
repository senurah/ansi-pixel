"""Public image rendering engine combining image conversion and multi-format serialization."""

from __future__ import annotations

from ansi_pixel.converter import (
    FilterInput,
    ImageSource,
    ResamplingFilter,
    image_to_ansi,
)
from ansi_pixel.exporters import OutputFormat, export_format
from ansi_pixel.optimizer import RGBColor


def render_image(
    source: ImageSource,
    width: int | None = None,
    *,
    format: OutputFormat | str = OutputFormat.ANSI,
    filter: FilterInput = ResamplingFilter.NEAREST,
    trim_bg: bool = False,
    chroma_key: str | RGBColor | None = None,
    chroma_tolerance: int = 15,
    alpha_threshold: int = 128,
    color: bool = True,
    **kwargs: object,
) -> str:
    """Render an image into a formatted string (ANSI, Markdown, Python, JavaScript, HTML).

    Args:
        source: Image file path, URL, '-' for stdin, open binary file-like object,
            raw bytes, or PIL Image.Image.
        width: Desired output width in terminal characters (default: auto-detected).
        format: Target serialization format (OutputFormat or 'ansi', 'md', 'py', 'js', 'html').
        filter: Resampling filter ('nearest', 'lanczos', 'bilinear').
        trim_bg: If True, treat near-white backgrounds as transparent and crop borders.
        chroma_key: Hex color string (e.g. '#FFFFFF') or RGB tuple to strip as transparent.
        chroma_tolerance: Matching tolerance for chroma key (default: 15).
        alpha_threshold: Alpha cutoff for transparency (0-255, default: 128).
        color: If False, suppress ANSI color escape codes (default: True).
        **kwargs: Optional format-specific options forwarded to the exporter
            (e.g., var_name='art', standalone=True, title='My Art').

    Returns:
        Rendered string representation according to the requested format.
    """
    lines = image_to_ansi(
        source,
        width=width,
        filter=filter,
        trim_bg=trim_bg,
        chroma_key=chroma_key,
        chroma_tolerance=chroma_tolerance,
        alpha_threshold=alpha_threshold,
        color=color,
    )
    return export_format(lines, format, **kwargs)
