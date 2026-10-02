"""Raw ANSI terminal string exporter."""

from __future__ import annotations

from collections.abc import Sequence


def export_ansi(lines: Sequence[str]) -> str:
    """Export rendered lines as a raw ANSI terminal string joined by newlines.

    Args:
        lines: Rendered ANSI art lines.

    Returns:
        New-line separated ANSI string ending with a trailing newline.
    """
    if not lines:
        return ""
    return "\n".join(lines) + "\n"
