"""Unit tests for ansi-pixel exporters."""

from __future__ import annotations

from ansi_pixel.exporters import (
    export_ansi,
    export_html,
    export_javascript,
    export_markdown,
    export_python,
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


def test_export_javascript() -> None:
    """Verify JavaScript exporter produces valid template literal."""
    lines = ["hello `world` ${interpolated}"]
    result = export_javascript(lines)
    assert result.startswith("const art = `\n")
    assert result.endswith("`;\n")
    # Backticks and dollar-brace should be escaped
    assert "\\`world\\`" in result
    assert "\\${interpolated}" in result


def test_export_html() -> None:
    """Verify HTML exporter produces styled <pre> and <span> tags."""
    line = "\033[38;2;255;0;0m\033[48;2;0;0;255m▀\033[0m"
    result = export_html([line])
    assert result.startswith('<pre style="background-color: #000000;')
    expected_span = (
        '<span style="color: rgb(255, 0, 0); background-color: rgb(0, 0, 255);">▀</span>'
    )
    assert expected_span in result

