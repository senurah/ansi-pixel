"""Unit tests for ansi-pixel exporters."""

from __future__ import annotations

from pathlib import Path

import pytest

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


def test_export_ansi() -> None:
    """Verify raw ANSI exporter output."""
    lines = ["\033[38;2;255;0;0m▀\033[0m", "\033[38;2;0;255;0m▀\033[0m"]
    result = export_ansi(lines)
    assert result == f"{lines[0]}\n{lines[1]}\n"
    assert export_ansi([]) == ""


def test_export_markdown() -> None:
    """Verify Markdown exporter creates fenced ```ansi code block."""
    lines = ["\033[38;2;255;0;0m▀\033[0m"]
    result = export_markdown(lines)
    assert result.startswith("```ansi\n")
    assert result.endswith("```\n")
    assert lines[0] in result
    assert export_markdown([]) == "```ansi\n\n```\n"


def test_export_python() -> None:
    """Verify Python code exporter generates executable snippet."""
    lines = ["\033[38;2;255;0;0m▀\033[0m", "hello 'world'"]
    result = export_python(lines)
    assert result.startswith("art = [\n")
    assert result.endswith("]\n")

    # Verify snippet can be safely executed
    namespace: dict[str, object] = {}
    exec(result, namespace)
    assert namespace["art"] == lines

    # Verify custom variable name
    custom_res = export_python(lines, var_name="banner")
    assert custom_res.startswith("banner = [\n")

    # Empty lines
    empty_res = export_python([], var_name="empty_art")
    assert empty_res == "empty_art = []\n"


def test_export_javascript() -> None:
    """Verify JavaScript exporter produces valid template literal."""
    lines = ["hello `world` ${interpolated}"]
    result = export_javascript(lines)
    assert result.startswith("const art = `\n")
    assert result.endswith("`;\n")
    # Backticks and dollar-brace should be escaped
    assert "\\`world\\`" in result
    assert "\\${interpolated}" in result

    # Custom variable name
    custom_js = export_javascript(lines, var_name="myLogo")
    assert custom_js.startswith("const myLogo = `\n")

    # Empty lines
    empty_js = export_javascript([], var_name="emptyLogo")
    assert empty_js == "const emptyLogo = ``;\n"


def test_export_html_snippet() -> None:
    """Verify HTML exporter produces styled <pre> and <span> tags."""
    line = "\033[38;2;255;0;0m\033[48;2;0;0;255m▀\033[0m"
    result = export_html([line])
    assert result.startswith('<pre style="background-color: #000000;')
    assert result.endswith("</pre>\n")
    expected_span = (
        '<span style="color: rgb(255, 0, 0); background-color: rgb(0, 0, 255);">▀</span>'
    )
    assert expected_span in result


def test_export_html_standalone() -> None:
    """Verify standalone HTML document generation with HTML5 doctype and title."""
    line = "\033[38;2;0;255;0m▀\033[0m"
    result = export_html([line], standalone=True, title="Banner Preview")
    assert result.startswith('<!DOCTYPE html>\n<html lang="en">\n')
    assert "<title>Banner Preview</title>" in result
    assert "</pre>\n</body>\n</html>\n" in result


def test_export_html_uncolored_and_reset() -> None:
    """Verify HTML exporter handles plain text and resets properly."""
    line = "Plain text \033[38;2;100;100;100mColored\033[0m Rest"
    result = export_html([line])
    assert "Plain text " in result
    assert '<span style="color: rgb(100, 100, 100);">Colored</span>' in result
    assert " Rest" in result


@pytest.mark.parametrize(
    ("fmt", "prefix"),
    [
        ("ansi", "\033["),
        ("txt", "\033["),
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
def test_export_format_dispatcher(fmt: OutputFormat | str, prefix: str) -> None:
    """Verify export_format correctly routes to all format handlers."""
    lines = ["\033[38;2;255;0;0m▀\033[0m"]
    result = export_format(lines, fmt)
    assert result.startswith(prefix)


def test_export_format_invalid() -> None:
    """Verify ValueError when requesting an invalid format."""
    with pytest.raises(ValueError, match="Unsupported format 'invalid_fmt'"):
        export_format(["\033[0m"], "invalid_fmt")


@pytest.mark.parametrize(
    ("path", "expected"),
    [
        ("logo.ansi", OutputFormat.ANSI),
        ("banner.ans", OutputFormat.ANSI),
        ("output.txt", OutputFormat.ANSI),
        ("README.md", OutputFormat.MD),
        ("doc.markdown", OutputFormat.MD),
        ("art.py", OutputFormat.PY),
        ("script.js", OutputFormat.JS),
        ("preview.html", OutputFormat.HTML),
        ("index.htm", OutputFormat.HTML),
        (Path("/tmp/art.md"), OutputFormat.MD),
        ("unknown.xyz", OutputFormat.ANSI),
        (None, OutputFormat.ANSI),
    ],
)
def test_infer_format_from_path(path: str | Path | None, expected: OutputFormat) -> None:
    """Verify extension-based output format inference."""
    assert infer_format_from_path(path) == expected
