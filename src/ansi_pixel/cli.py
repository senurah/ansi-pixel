"""Command-line interface entry point for ansi-pixel."""

from __future__ import annotations

import argparse
import os
import sys
import urllib.error
from collections.abc import Sequence
from pathlib import Path
from typing import TextIO

from PIL import UnidentifiedImageError

from ansi_pixel import __version__
from ansi_pixel.converter import ResamplingFilter, get_terminal_width, image_to_ansi
from ansi_pixel.exporters import (
    OutputFormat,
    export_format,
    infer_format_from_path,
)


def format_lines(lines: list[str], output_format: OutputFormat | str) -> str:
    """Serialize rendered ANSI lines into the target representation format.

    Args:
        lines: Rendered ANSI art lines.
        output_format: Desired OutputFormat or format name.

    Returns:
        Formatted string suitable for writing to stdout or a file.
    """
    return export_format(lines, output_format)


def write_output(
    lines: list[str],
    output_format: OutputFormat | str = OutputFormat.ANSI,
    file_path: str | Path | None = None,
) -> None:
    """Save rendered ANSI art lines to a file according to the requested format.

    Args:
        lines: Rendered ANSI art lines.
        output_format: Target format (ansi, md, py, js, html, txt).
        file_path: Destination path. If None, defaults to 'output.<ext>'.
    """
    fmt = (
        output_format
        if isinstance(output_format, OutputFormat)
        else OutputFormat(str(output_format).lower())
    )
    if file_path is None:
        file_path = f"output.{fmt.value}"
    content = format_lines(lines, fmt)
    Path(file_path).write_text(content, encoding="utf-8")


def is_color_enabled(color_mode: str = "auto", stream: TextIO | None = None) -> bool:
    """Determine whether ANSI color escape codes should be emitted.

    Adheres strictly to the NO_COLOR standard (https://no-color.org) and non-TTY pipe detection.

    Args:
        color_mode: Color choice ('auto', 'always', or 'never').
        stream: Output stream to inspect for interactive TTY (defaults to sys.stdout).

    Returns:
        True if ANSI color codes should be included, False if suppressed.
    """
    if color_mode == "never":
        return False
    if color_mode == "always":
        return True

    # color_mode == "auto":
    # 1. NO_COLOR standard: if NO_COLOR environment variable is present and non-empty, disable color
    if os.environ.get("NO_COLOR", "") != "":
        return False

    target_stream = stream if stream is not None else sys.stdout
    return bool(getattr(target_stream, "isatty", lambda: False)())


def build_parser() -> argparse.ArgumentParser:
    """Construct and configure the command-line argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="ansi-pixel",
        description=(
            "Convert an image into true-color ANSI art for terminal banners, "
            "SSH previews, and Markdown."
        ),
    )
    parser.add_argument(
        "-V",
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
        help="Show program's version number and exit",
    )
    parser.add_argument(
        "image",
        nargs="?",
        default=None,
        help="Path to image file, image URL, or '-' to read from standard input",
    )
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=None,
        help="Output width in terminal characters (default: auto-detected terminal width)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=str,
        default=None,
        metavar="FILE",
        help="Path to save output file instead of writing solely to stdout",
    )
    parser.add_argument(
        "-f",
        "--format",
        type=str,
        choices=[f.value for f in OutputFormat],
        default=None,
        help="Output format: ansi, md, py, js, html (default: ansi or inferred from --output)",
    )
    parser.add_argument(
        "--filter",
        type=str,
        choices=[f.value for f in ResamplingFilter],
        default=ResamplingFilter.NEAREST.value,
        help="Resampling filter: nearest, lanczos, or bilinear (default: nearest)",
    )
    parser.add_argument(
        "--trim-bg",
        action="store_true",
        help="Strip white/solid background (treat near-white pixels as transparent)",
    )
    parser.add_argument(
        "--chroma-key",
        type=str,
        default=None,
        help="Hex color to treat as transparent (e.g. #FFFFFF or 00FF00)",
    )
    parser.add_argument(
        "--color",
        dest="color",
        choices=["auto", "always", "never"],
        default="auto",
        nargs="?",
        const="always",
        help=(
            "When to output ANSI colors: auto, always, never (default: auto). "
            "Follows NO_COLOR standard."
        ),
    )
    parser.add_argument(
        "--no-color",
        dest="color",
        action="store_const",
        const="never",
        help="Disable ANSI color codes (alias for --color=never)",
    )
    parser.add_argument(
        "--print",
        dest="print_output",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Control printing to stdout when -o/--output is provided; use --no-print to silence",
    )
    return parser


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    """Parse command line arguments.

    Args:
        argv: Optional sequence of argument strings. Defaults to sys.argv[1:].

    Returns:
        Parsed arguments Namespace.
    """
    parser = build_parser()
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    """Main CLI execution entry point.

    Args:
        argv: Optional sequence of CLI arguments.

    Returns:
        POSIX exit code: 0 on success, 1 on input/runtime error, 2 on usage error.
    """
    try:
        args = parse_args(argv)
    except SystemExit as exc:
        return int(exc.code) if isinstance(exc.code, int) else 2

    # Handle image argument: if omitted, check whether stdin is piped
    image_source: str | None = args.image
    if image_source is None:
        if not sys.stdin.isatty():
            image_source = "-"
        else:
            sys.stderr.write("ansi-pixel: error: the following arguments are required: image\n")
            return 2

    # Validate width if explicitly provided
    if args.width is not None and args.width < 1:
        sys.stderr.write("Error: target_width must be at least 1.\n")
        return 2

    target_width: int = args.width if args.width is not None else get_terminal_width()

    # Determine whether color codes should be generated
    if args.output is not None:
        # Saving to file: honor explicit --color flag and NO_COLOR env var
        color_enabled = (args.color != "never") and (
            os.environ.get("NO_COLOR", "") == "" or args.color == "always"
        )
    else:
        # Outputting to stdout: check non-TTY pipe detection and NO_COLOR standard
        color_enabled = is_color_enabled(args.color, sys.stdout)

    try:
        lines = image_to_ansi(
            image_source,
            target_width=target_width,
            filter=args.filter,
            trim_bg=args.trim_bg,
            chroma_key=args.chroma_key,
            color=color_enabled,
        )
    except FileNotFoundError:
        sys.stderr.write(f"Error: image not found: {image_source}\n")
        return 1
    except UnidentifiedImageError:
        desc = "standard input" if image_source == "-" else repr(image_source)
        sys.stderr.write(f"Error: unsupported or invalid image: {desc}\n")
        return 1
    except urllib.error.HTTPError as exc:
        sys.stderr.write(f"Error: HTTP {exc.code} {exc.reason}: {image_source}\n")
        return 1
    except urllib.error.URLError as exc:
        sys.stderr.write(f"Error: failed to fetch URL '{image_source}': {exc.reason}\n")
        return 1
    except TimeoutError:
        sys.stderr.write(f"Error: request timed out fetching URL: {image_source}\n")
        return 1
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        err_msg = str(exc).lower()
        if any(keyword in err_msg for keyword in ("target_width", "filter", "hex", "choice")):
            return 2
        return 1
    except OSError as exc:
        sys.stderr.write(f"Error: could not open image: {exc}\n")
        return 1

    # Determine output serialization format
    if args.format is not None:
        out_format = OutputFormat(args.format.lower())
    elif args.output is not None:
        out_format = infer_format_from_path(args.output)
    else:
        out_format = OutputFormat.ANSI

    formatted_output = format_lines(lines, out_format)

    # Write to destination file if -o/--output was specified
    if args.output is not None:
        try:
            target_path = Path(args.output)
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(formatted_output, encoding="utf-8")
        except OSError as exc:
            sys.stderr.write(f"Error: failed to write output file '{args.output}': {exc}\n")
            return 1

    # Output to stdout by default (when -o is omitted) or when --print is explicitly enabled
    should_print = args.print_output if args.print_output is not None else (args.output is None)
    if should_print:
        sys.stdout.write(formatted_output)

    return 0


if __name__ == "__main__":
    sys.exit(main())
