"""Tests for package metadata, exports, and backward compatibility."""

from __future__ import annotations

import importlib.util
import subprocess
import sys
from pathlib import Path

import ansi_pixel
from ansi_pixel.converter import ResamplingFilter, image_to_ansi
from ansi_pixel.optimizer import AnsiOptimizer


def test_package_exports() -> None:
    """Verify that public API symbols are properly exposed at package root."""
    assert hasattr(ansi_pixel, "__version__")
    assert ansi_pixel.image_to_ansi is image_to_ansi
    assert ansi_pixel.AnsiOptimizer is AnsiOptimizer
    assert ansi_pixel.ResamplingFilter is ResamplingFilter


def test_py_typed_exists() -> None:
    """Ensure py.typed marker file exists in the package directory for PEP 561 compliance."""
    package_dir = Path(ansi_pixel.__file__).parent
    py_typed = package_dir / "py.typed"
    assert py_typed.is_file()


def test_backward_compat_img_to_ansi() -> None:
    """Verify that the legacy root img_to_ansi.py re-exports converter functions."""
    import img_to_ansi

    assert hasattr(img_to_ansi, "image_to_ansi")
    assert img_to_ansi.image_to_ansi is image_to_ansi
    assert hasattr(img_to_ansi, "ResamplingFilter")


def test_backward_compat_main_py_importable() -> None:
    """Verify that legacy root main.py is importable and has main function."""
    spec = importlib.util.spec_from_file_location("legacy_main", "main.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    assert hasattr(module, "main")


def test_cli_help_flag() -> None:
    """Verify that ansi-pixel CLI entrypoint runs --help without errors."""
    result = subprocess.run(
        [sys.executable, "-m", "ansi_pixel.cli", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0
    assert "usage: ansi-pixel" in result.stdout
    assert "--filter" in result.stdout
    assert "--trim-bg" in result.stdout
    assert "--chroma-key" in result.stdout
