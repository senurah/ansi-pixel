"""Python snippet and JavaScript template string exporters."""

from __future__ import annotations

from collections.abc import Sequence


def export_python(lines: Sequence[str], var_name: str = "art") -> str:
    """Export rendered lines as a copy-pasteable Python snippet.

    Args:
        lines: Rendered ANSI art lines.
        var_name: Target variable name (default: 'art').

    Returns:
        Python code string assigning a list of strings to variable var_name.
    """
    if not lines:
        return f"{var_name} = []\n"
    elements = "".join(f"    {line!r},\n" for line in lines)
    return f"{var_name} = [\n{elements}]\n"


def export_javascript(lines: Sequence[str], var_name: str = "art") -> str:
    """Export rendered lines as a copy-pasteable JavaScript template string.

    Args:
        lines: Rendered ANSI art lines.
        var_name: Target constant name (default: 'art').

    Returns:
        JavaScript code snippet declaring a constant with a template literal.
    """
    if not lines:
        return f"const {var_name} = ``;\n"

    escaped_lines: list[str] = []
    for line in lines:
        # Escape backslashes, backticks, and string interpolation syntax
        escaped = line.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
        escaped_lines.append(escaped)

    body = "\n".join(escaped_lines)
    return f"const {var_name} = `\n{body}\n`;\n"
