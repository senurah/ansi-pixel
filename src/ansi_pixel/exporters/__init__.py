"""Target-specific serialization exporters for ansi-pixel."""

from __future__ import annotations

from collections.abc import Sequence
from enum import Enum
from pathlib import Path

from ansi_pixel.exporters.ansi import export_ansi
from ansi_pixel.exporters.code import export_javascript, export_python
from ansi_pixel.exporters.html import export_html
from ansi_pixel.exporters.markdown import export_markdown


class OutputFormat(str, Enum):
    """Supported output serialization formats."""

    ANSI = "ansi"
    MD = "md"
    PY = "py"
    JS = "js"
    HTML = "html"
    TXT = "txt"


def infer_format_from_path(path: str | Path | None) -> OutputFormat:
    """Infer output serialization format from a destination file extension.

    Args:
        path: Destination file path or None.

    Returns:
        Matching OutputFormat, defaulting to ANSI.
    """
    if not path:
        return OutputFormat.ANSI
    ext = Path(path).suffix.lower().lstrip(".")
    if ext in ("md", "markdown"):
        return OutputFormat.MD
    if ext == "py":
        return OutputFormat.PY
    if ext in ("js", "javascript"):
        return OutputFormat.JS
    if ext in ("html", "htm"):
        return OutputFormat.HTML
    if ext in ("ansi", "ans", "txt"):
        return OutputFormat.ANSI
    return OutputFormat.ANSI


def export_format(
    lines: Sequence[str],
    output_format: OutputFormat | str = OutputFormat.ANSI,
    **kwargs: object,
) -> str:
    """Serialize rendered ANSI lines into the target representation format.

    Args:
        lines: Rendered ANSI art lines.
        output_format: Target format ('ansi', 'md', 'py', 'js', 'html', 'txt' or OutputFormat).
        **kwargs: Optional format-specific options (e.g. standalone, var_name, title).

    Returns:
        Formatted string representation.

    Raises:
        ValueError: If the output format is not recognized.
    """
    fmt_str = (
        output_format.value
        if isinstance(output_format, OutputFormat)
        else str(output_format).lower()
    )
    if fmt_str in ("ansi", "txt"):
        return export_ansi(lines)
    if fmt_str in ("md", "markdown"):
        return export_markdown(lines)
    if fmt_str in ("py", "python"):
        var_name = str(kwargs.get("var_name", "art"))
        return export_python(lines, var_name=var_name)
    if fmt_str in ("js", "javascript"):
        var_name = str(kwargs.get("var_name", "art"))
        return export_javascript(lines, var_name=var_name)
    if fmt_str in ("html", "htm"):
        standalone = bool(kwargs.get("standalone", False))
        title = str(kwargs.get("title", "ANSI Art"))
        return export_html(lines, standalone=standalone, title=title)
    raise ValueError(
        f"Unsupported format '{output_format}'. Valid choices: ansi, md, py, js, html"
    )


__all__ = [
    "OutputFormat",
    "export_ansi",
    "export_format",
    "export_html",
    "export_javascript",
    "export_markdown",
    "export_python",
    "infer_format_from_path",
]
