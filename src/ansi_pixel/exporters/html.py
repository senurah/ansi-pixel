"""Styled HTML exporter converting ANSI true-color sequences to styled <pre> and <span>."""

from __future__ import annotations

import html
import re
from collections.abc import Sequence

# Regex matching ANSI escape sequences: SGR codes (\033[...m)
_ANSI_SGR_REGEX = re.compile(r"\x1b\[([0-9;]*)m")


def _line_to_html(line: str) -> str:
    """Convert a single ANSI-colored line to HTML spans.

    Args:
        line: ANSI-escaped string for a single row.

    Returns:
        HTML snippet with spans applying color and background-color styles.
    """
    parts: list[str] = []
    current_fg: str | None = None
    current_bg: str | None = None

    last_end = 0
    for match in _ANSI_SGR_REGEX.finditer(line):
        text_before = line[last_end:match.start()]
        if text_before:
            escaped_text = html.escape(text_before)
            if current_fg or current_bg:
                styles: list[str] = []
                if current_fg:
                    styles.append(f"color: {current_fg};")
                if current_bg:
                    styles.append(f"background-color: {current_bg};")
                style_str = " ".join(styles)
                parts.append(f'<span style="{style_str}">{escaped_text}</span>')
            else:
                parts.append(escaped_text)

        last_end = match.end()
        code = match.group(1)
        if not code or code == "0":
            current_fg = None
            current_bg = None
        else:
            subcodes = [int(c) for c in code.split(";") if c.isdigit()]
            idx = 0
            while idx < len(subcodes):
                c = subcodes[idx]
                if c == 38 and idx + 4 < len(subcodes) and subcodes[idx + 1] == 2:
                    # 24-bit foreground: 38;2;r;g;b
                    r, g, b = subcodes[idx + 2], subcodes[idx + 3], subcodes[idx + 4]
                    current_fg = f"rgb({r}, {g}, {b})"
                    idx += 5
                elif c == 48 and idx + 4 < len(subcodes) and subcodes[idx + 1] == 2:
                    # 24-bit background: 48;2;r;g;b
                    r, g, b = subcodes[idx + 2], subcodes[idx + 3], subcodes[idx + 4]
                    current_bg = f"rgb({r}, {g}, {b})"
                    idx += 5
                elif c == 39:
                    current_fg = None
                    idx += 1
                elif c == 49:
                    current_bg = None
                    idx += 1
                elif c == 0:
                    current_fg = None
                    current_bg = None
                    idx += 1
                else:
                    idx += 1

    text_tail = line[last_end:]
    if text_tail:
        escaped_tail = html.escape(text_tail)
        if current_fg or current_bg:
            styles = []
            if current_fg:
                styles.append(f"color: {current_fg};")
            if current_bg:
                styles.append(f"background-color: {current_bg};")
            style_str = " ".join(styles)
            parts.append(f'<span style="{style_str}">{escaped_tail}</span>')
        else:
            parts.append(escaped_tail)

    return "".join(parts)


def export_html(lines: Sequence[str]) -> str:
    """Export lines as styled HTML <pre> block with <span> tags for true-color ANSI styles.

    Args:
        lines: Rendered ANSI art lines.

    Returns:
        Complete HTML snippet wrapped in a <pre> element.
    """
    html_lines = [_line_to_html(line) for line in lines]
    body = "\n".join(html_lines)
    return (
        '<pre style="background-color: #000000; color: #ffffff; '
        'font-family: monospace; line-height: 1; letter-spacing: 0; '
        'display: inline-block; padding: 8px;">\n'
        f"{body}\n"
        "</pre>\n"
    )
