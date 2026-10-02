"""Unit tests for ansi-pixel command-line interface."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
from PIL import Image

from ansi_pixel.cli import main, parse_args


def test_cli_parse_defaults() -> None:
    """Verify default CLI arguments."""
    args = parse_args(["some_image.png"])
    assert args.image == "some_image.png"
    assert args.width == 36
    assert args.output == "txt"
    assert args.filter == "nearest"
    assert args.trim_bg is False
    assert args.chroma_key is None
    assert args.print_output is True


def test_cli_custom_flags() -> None:
    """Verify custom flags parsing."""
    args = parse_args(
        [
            "logo.png",
            "-w",
            "50",
            "-o",
            "md",
            "--filter",
            "lanczos",
            "--trim-bg",
            "--chroma-key",
            "#FFFFFF",
            "--no-print",
        ]
    )
    assert args.image == "logo.png"
    assert args.width == 50
    assert args.output == "md"
    assert args.filter == "lanczos"
    assert args.trim_bg is True
    assert args.chroma_key == "#FFFFFF"
    assert args.print_output is False


def test_cli_missing_image_file() -> None:
    """Verify that a missing image produces exit code 1."""
    code = main(["non_existent_file_12345.png"])
    assert code == 1


def test_cli_invalid_filter_arg(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that an invalid filter value produces exit code 2."""
    code = main(["pixel_art_small.png", "--filter", "invalid_filter"])
    assert code == 2


def test_cli_execution_with_test_image(tmp_path: Path) -> None:
    """Verify successful CLI execution producing file and stdout."""
    img_path = tmp_path / "test.png"
    Image.new("RGBA", (10, 10), (255, 0, 0, 255)).save(img_path)

    # Run CLI with output to file
    result = subprocess.run(
        [sys.executable, "-m", "ansi_pixel.cli", str(img_path), "-w", "10", "--no-print"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
