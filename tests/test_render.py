"""Unit tests for public render_image API and top-level package exports."""

from __future__ import annotations

import io
import subprocess
import sys
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

import ansi_pixel
from ansi_pixel import (
    OutputFormat,
    ResamplingFilter,
    image_to_ansi,
    render_image,
)


def test_top_level_package_exports() -> None:
    """Verify that all public symbols are exposed at top-level ansi_pixel package."""
    assert hasattr(ansi_pixel, "render_image")
    assert hasattr(ansi_pixel, "image_to_ansi")
    assert hasattr(ansi_pixel, "OutputFormat")
    assert hasattr(ansi_pixel, "ResamplingFilter")
    assert hasattr(ansi_pixel, "export_ansi")
    assert hasattr(ansi_pixel, "export_format")
    assert hasattr(ansi_pixel, "export_html")
    assert hasattr(ansi_pixel, "export_javascript")
    assert hasattr(ansi_pixel, "export_markdown")
    assert hasattr(ansi_pixel, "export_python")
    assert hasattr(ansi_pixel, "get_terminal_width")
    assert hasattr(ansi_pixel, "strip_ansi")
    assert hasattr(ansi_pixel, "AnsiOptimizer")
    assert hasattr(ansi_pixel, "__version__")


def test_render_image_default_ansi() -> None:
    """Verify render_image with default format (ANSI string)."""
    img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
    result = render_image(img, width=10, filter=ResamplingFilter.LANCZOS)
    assert isinstance(result, str)
    assert "\033[" in result
    assert result.endswith("\n")


@pytest.mark.parametrize(
    ("fmt", "prefix"),
    [
        ("ansi", "\033["),
        (OutputFormat.ANSI, "\033["),
        ("md", "```ansi\n"),
        ("markdown", "```ansi\n"),
        (OutputFormat.MD, "```ansi\n"),
        ("py", "art = [\n"),
        ("python", "art = [\n"),
        (OutputFormat.PY, "art = [\n"),
        ("js", "const art = `\n"),
        ("javascript", "const art = `\n"),
        (OutputFormat.JS, "const art = `\n"),
        ("html", '<pre style="background-color: #000000;'),
        ("htm", '<pre style="background-color: #000000;'),
        (OutputFormat.HTML, '<pre style="background-color: #000000;'),
    ],
)
def test_render_image_formats(fmt: OutputFormat | str, prefix: str) -> None:
    """Verify render_image with all supported format strings and enums."""
    img = Image.new("RGBA", (6, 6), (50, 150, 250, 255))
    result = render_image(img, width=6, format=fmt)
    assert result.startswith(prefix)


def test_render_image_kwargs_forwarding() -> None:
    """Verify that kwargs are passed through to the format exporter."""
    img = Image.new("RGBA", (4, 4), (100, 200, 50, 255))

    # Python custom var_name
    py_result = render_image(img, width=4, format="py", var_name="custom_var")
    assert py_result.startswith("custom_var = [\n")

    # JavaScript custom var_name
    js_result = render_image(img, width=4, format="js", var_name="logoData")
    assert js_result.startswith("const logoData = `\n")

    # HTML standalone
    html_result = render_image(img, width=4, format="html", standalone=True, title="Test Art")
    assert "<title>Test Art</title>" in html_result


def test_render_image_sources(tmp_path: Path) -> None:
    """Verify render_image accepts Path, str, BytesIO, bytes, and PIL Image."""
    img = Image.new("RGBA", (6, 6), (200, 100, 50, 255))

    # 1. PIL Image
    assert len(render_image(img, width=6)) > 0

    # 2. File path (str)
    file_path = str(tmp_path / "art.png")
    img.save(file_path)
    assert len(render_image(file_path, width=6)) > 0

    # 3. Path object
    assert len(render_image(Path(file_path), width=6)) > 0

    # 4. BytesIO
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    assert len(render_image(buf, width=6)) > 0

    # 5. Raw bytes
    assert len(render_image(buf.getvalue(), width=6)) > 0


def test_render_image_url_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify render_image accepts an HTTP/HTTPS URL."""
    img = Image.new("RGBA", (4, 4), (0, 128, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    mock_resp = MagicMock()
    mock_resp.read.return_value = buf.getvalue()
    mock_resp.__enter__.return_value = mock_resp
    mock_resp.__exit__.return_value = None

    monkeypatch.setattr(
        "ansi_pixel.converter.urllib.request.urlopen",
        lambda req, timeout=15.0: mock_resp,
    )

    result = render_image("https://example.com/badge.png", width=4, format="md")
    assert result.startswith("```ansi\n")


def test_render_image_stdin_source(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify render_image accepts '-' reading from stdin."""
    img = Image.new("RGBA", (4, 4), (128, 0, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")

    fake_stdin = MagicMock()
    fake_stdin.buffer = io.BytesIO(buf.getvalue())
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    result = render_image("-", width=4, format="py")
    assert result.startswith("art = [\n")


def test_render_image_color_false() -> None:
    """Verify render_image with color=False produces uncolored output."""
    img = Image.new("RGBA", (6, 6), (255, 0, 0, 255))
    result = render_image(img, width=6, color=False)
    assert "\033[" not in result
    assert "▀" in result


def test_image_to_ansi_width_kwarg() -> None:
    """Verify image_to_ansi accepts width keyword argument as defined in Phase 4.2."""
    img = Image.new("RGBA", (8, 8), (0, 255, 0, 255))
    lines = image_to_ansi(img, width=4)
    assert len(lines) > 0


def test_external_python_script_execution(tmp_path: Path) -> None:
    """Phase 4.3: Verify that an external Python script can import and use ansi_pixel cleanly."""
    img_path = tmp_path / "sample.png"
    Image.new("RGBA", (8, 8), (255, 50, 100, 255)).save(img_path)

    # Script executing from an outside directory (/tmp)
    script = f"""
import sys
import ansi_pixel
from ansi_pixel import render_image, image_to_ansi, OutputFormat

# 1. Test image_to_ansi
lines = image_to_ansi({str(img_path)!r}, width=8)
assert len(lines) > 0, "image_to_ansi failed"

# 2. Test render_image with Markdown format
md = render_image({str(img_path)!r}, width=8, format=OutputFormat.MD)
assert md.startswith("```ansi\\n"), "render_image MD failed"

# 3. Test render_image with Python snippet format
py_code = render_image({str(img_path)!r}, width=8, format="py", var_name="banner")
assert py_code.startswith("banner = [\\n"), "render_image PY failed"

# 4. Test render_image with HTML format
html_code = render_image({str(img_path)!r}, width=8, format="html", standalone=True)
assert "<!DOCTYPE html>" in html_code, "render_image HTML failed"

print("OK")
"""
    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=False,
    )
    err_msg = f"External script failed:\nSTDOUT: {result.stdout}\nSTDERR: {result.stderr}"
    assert result.returncode == 0, err_msg
    assert "OK" in result.stdout
