"""Unit tests for image conversion, white-pixel preservation, and filters."""

from __future__ import annotations

import io
from pathlib import Path

import pytest
from PIL import Image

from ansi_pixel.converter import (
    ResamplingFilter,
    image_to_ansi,
    parse_hex_color,
    parse_resampling_filter,
)


def test_white_pixel_preservation() -> None:
    """Verify that opaque white pixels (255, 255, 255) are preserved and NOT erased."""
    # Create an image with solid opaque white
    img = Image.new("RGBA", (4, 4), (255, 255, 255, 255))
    lines = image_to_ansi(img, target_width=4)

    assert len(lines) > 0
    full_output = "".join(lines)
    # The output must contain white escape codes, not empty spaces
    assert "255;255;255" in full_output
    assert "▀" in full_output
    # Must NOT be just spaces
    assert full_output.strip(" \033[0m") != ""


def test_alpha_transparency() -> None:
    """Verify that pixels with alpha < 128 are treated as transparent."""
    # Top row opaque red, bottom row transparent red
    img = Image.new("RGBA", (4, 2), (0, 0, 0, 0))
    for x in range(4):
        img.putpixel((x, 0), (255, 0, 0, 255))  # Top: colored
        img.putpixel((x, 1), (255, 0, 0, 50))  # Bottom: transparent (alpha < 128)

    lines = image_to_ansi(img, target_width=4)
    # Top is colored, bottom is empty -> upper half block '▀'
    assert len(lines) == 1
    assert "▀" in lines[0]
    # No background color escape sequence should be emitted
    assert "\033[48;2;" not in lines[0]


def test_trim_bg_flag() -> None:
    """Verify that --trim-bg strips near-white background when explicitly requested."""
    # Red 2x2 box inside a 6x6 white canvas
    img = Image.new("RGBA", (6, 6), (255, 255, 255, 255))
    for y in range(2, 4):
        for x in range(2, 4):
            img.putpixel((x, y), (255, 0, 0, 255))

    # Without trim_bg, white pixels are preserved
    lines_untrimmed = image_to_ansi(img, target_width=6, trim_bg=False)
    assert "255;255;255" in "".join(lines_untrimmed)

    # With trim_bg, white pixels are stripped and borders cropped
    lines_trimmed = image_to_ansi(img, target_width=2, trim_bg=True)
    full_trimmed = "".join(lines_trimmed)
    assert "255;255;255" not in full_trimmed
    assert "255;0;0" in full_trimmed


def test_chroma_key_hex() -> None:
    """Verify chroma-key color stripping for specified hex colors."""
    # Green background (0, 255, 0) with a blue pixel
    img = Image.new("RGBA", (4, 4), (0, 255, 0, 255))
    img.putpixel((2, 2), (0, 0, 255, 255))

    lines = image_to_ansi(img, target_width=4, chroma_key="#00FF00")
    full_output = "".join(lines)
    # Green should be stripped out
    assert "0;255;0" not in full_output
    # Blue pixel should remain
    assert "0;0;255" in full_output


def test_parse_hex_color() -> None:
    """Verify hex color parsing for 3-digit and 6-digit hex values."""
    assert parse_hex_color("#FFFFFF") == (255, 255, 255)
    assert parse_hex_color("00FF00") == (0, 255, 0)
    assert parse_hex_color("#FFF") == (255, 255, 255)
    assert parse_hex_color("123") == (17, 34, 51)

    with pytest.raises(ValueError, match="Invalid hex color"):
        parse_hex_color("invalid")

    with pytest.raises(ValueError, match="Invalid hex color"):
        parse_hex_color("#12345")


def test_resampling_filters() -> None:
    """Verify supported resampling filters and parse_resampling_filter."""
    img = Image.new("RGBA", (10, 10), (100, 150, 200, 255))

    for f_name in ["nearest", "lanczos", "bilinear"]:
        lines = image_to_ansi(img, target_width=4, filter=f_name)
        assert len(lines) > 0

    assert parse_resampling_filter(ResamplingFilter.NEAREST) == Image.Resampling.NEAREST
    assert parse_resampling_filter("lanczos") == Image.Resampling.LANCZOS
    assert parse_resampling_filter("BILINEAR") == Image.Resampling.BILINEAR

    with pytest.raises(ValueError, match="Unknown filter"):
        parse_resampling_filter("invalid_filter")

    with pytest.raises(TypeError, match="Invalid filter type"):
        parse_resampling_filter(123)  # type: ignore[arg-type]


def test_image_source_types(tmp_path: Path) -> None:
    """Verify that image_to_ansi accepts Path, str, BytesIO, and Image.Image."""
    img = Image.new("RGBA", (4, 4), (50, 100, 150, 255))

    # 1. PIL Image
    assert len(image_to_ansi(img, target_width=4)) > 0

    # 2. File path (str)
    file_path = str(tmp_path / "test.png")
    img.save(file_path)
    assert len(image_to_ansi(file_path, target_width=4)) > 0

    # 3. Path object
    assert len(image_to_ansi(Path(file_path), target_width=4)) > 0

    # 4. BytesIO
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    assert len(image_to_ansi(buf, target_width=4)) > 0


def test_edge_cases() -> None:
    """Verify edge cases such as 1x1 image, odd dimensions, and invalid width."""
    # 1x1 pixel image
    img_1x1 = Image.new("RGBA", (1, 1), (255, 0, 0, 255))
    lines_1x1 = image_to_ansi(img_1x1, target_width=2)
    assert len(lines_1x1) == 1

    # Odd dimensions
    img_odd = Image.new("RGBA", (5, 7), (0, 255, 0, 255))
    lines_odd = image_to_ansi(img_odd, target_width=4)
    assert len(lines_odd) > 0

    # Fully transparent image
    img_trans = Image.new("RGBA", (4, 4), (0, 0, 0, 0))
    lines_trans = image_to_ansi(img_trans, target_width=4)
    assert len(lines_trans) > 0
    # Transparent image should contain no color escapes
    assert "\033[38;2;" not in "".join(lines_trans)

    # Invalid target width (< 1)
    with pytest.raises(ValueError, match="target_width must be at least 1"):
        image_to_ansi(img_1x1, target_width=0)
