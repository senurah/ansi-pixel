"""ansi-pixel: Convert images into true-color ANSI terminal art."""

from __future__ import annotations

from ansi_pixel.converter import ResamplingFilter, image_to_ansi
from ansi_pixel.optimizer import AnsiOptimizer

__version__ = "0.2.0"
__all__ = [
    "AnsiOptimizer",
    "ResamplingFilter",
    "image_to_ansi",
]
