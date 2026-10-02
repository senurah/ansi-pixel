"""GitHub-compatible Markdown exporter for ANSI art."""

from __future__ import annotations

from collections.abc import Sequence


def export_markdown(lines: Sequence[str]) -> str:
    """Export rendered ANSI lines wrapped in a GitHub-compatible ```ansi code block.

    Args:
        lines: Rendered ANSI art lines.

    Returns:
        Markdown string containing a fenced code block with the 'ansi' language identifier.
    """
    body = "\n".join(lines)
    return f"```ansi\n{body}\n```\n"
