"""Python snippet and JavaScript template string exporters."""

from __future__ import annotations

from collections.abc import Sequence


def export_python(lines: Sequence[str]) -> str:
    """Export rendered lines as a copy-pasteable Python snippet.

    Args:
        lines: Rendered ANSI art lines.

    Returns:
        Python code string assigning a list of strings to variable 'art'.
    """
    elements = "".join(f"    {line!r},\n" for line in lines)
    return f"art = [\n{elements}]\n"


def export_javascript(lines: Sequence[str]) -> str:
    """Export rendered lines as a copy-pasteable JavaScript template string.

    Args:
        lines: Rendered ANSI art lines.

    Returns:
        JavaScript code snippet declaring a constant 'art' with a template literal.
    """
    escaped_lines: list[str] = []
    for line in lines:
        # Escape backslashes, backticks, and string interpolation syntax
        escaped = line.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        escaped_lines.append(escaped)

    body = "\n".join(escaped_lines)
    return f"const art = `\n{body}\n`;\n"
