"""ansi-pixel: Convert images into true-color ANSI terminal art."""

from __future__ import annotations

from ansi_pixel.converter import (
    FilterInput,
    ImageSource,
    ResamplingFilter,
    get_terminal_width,
    image_to_ansi,
    parse_hex_color,
    parse_resampling_filter,
)
from ansi_pixel.exporters import (
    OutputFormat,
    export_ansi,
    export_format,
    export_html,
    export_javascript,
    export_markdown,
    export_python,
    infer_format_from_path,
)
from ansi_pixel.optimizer import AnsiOptimizer, RGBColor, strip_ansi
from ansi_pixel.render import render_image

__version__ = "0.2.1"

__all__ = [
    "AnsiOptimizer",
    "FilterInput",
    "ImageSource",
    "OutputFormat",
    "RGBColor",
    "ResamplingFilter",
    "export_ansi",
    "export_format",
    "export_html",
    "export_javascript",
    "export_markdown",
    "export_python",
    "get_terminal_width",
    "image_to_ansi",
    "infer_format_from_path",
    "parse_hex_color",
    "parse_resampling_filter",
    "render_image",
    "strip_ansi",
]
