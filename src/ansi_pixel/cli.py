"""Command-line interface entry point for ansi-pixel."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence
from enum import Enum

from PIL import UnidentifiedImageError

from ansi_pixel.converter import ResamplingFilter, image_to_ansi


class OutputFormat(str, Enum):
    """Supported output serialization formats."""

    TXT = "txt"
    MD = "md"
    PY = "py"


def write_output(lines: list[str], output_format: OutputFormat) -> None:
    """Save rendered ANSI art lines to a file according to the requested format.

    Args:
        lines: Rendered ANSI art lines.
        output_format: Target format (txt, md, or py).
    """
    if output_format is OutputFormat.TXT:
        with open("output.txt", "w", encoding="utf-8") as file:
            file.write("\n".join(lines) + "\n")
    elif output_format is OutputFormat.MD:
        with open("output.md", "w", encoding="utf-8") as file:
            file.write("```ansi\n")
            file.write("\n".join(lines) + "\n")
            file.write("```\n")
    elif output_format is OutputFormat.PY:
        with open("output.py", "w", encoding="utf-8") as file:
            file.write("art = [\n")
            for line in lines:
                file.write(f"    {line!r},\n")
            file.write("]\n")


def build_parser() -> argparse.ArgumentParser:
    """Construct and configure the command-line argument parser.

    Returns:
        Configured ArgumentParser instance.
    """
    parser = argparse.ArgumentParser(
        prog="ansi-pixel",
        description="Convert an image into true-color ANSI art.",
    )
    parser.add_argument("image", help="Path to image file")
    parser.add_argument(
        "-w",
        "--width",
        type=int,
        default=36,
        help="Output width in terminal characters (default: 36)",
    )
    parser.add_argument(
        "-o",
        "--output",
        type=OutputFormat,
        choices=[f.value for f in OutputFormat],
        default=OutputFormat.TXT.value,
        help="Output format: txt, md, or py (default: txt)",
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
        "--print",
        dest="print_output",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Print ANSI output to terminal; use --no-print to disable (default: True)",
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

    try:
        lines = image_to_ansi(
            args.image,
            target_width=args.width,
            filter=args.filter,
            trim_bg=args.trim_bg,
            chroma_key=args.chroma_key,
        )
    except FileNotFoundError:
        sys.stderr.write(f"Error: image not found: {args.image}\n")
        return 1
    except UnidentifiedImageError:
        sys.stderr.write(f"Error: unsupported or invalid image: {args.image}\n")
        return 1
    except ValueError as exc:
        sys.stderr.write(f"Error: {exc}\n")
        return 2
    except OSError as exc:
        sys.stderr.write(f"Error: could not open image: {exc}\n")
        return 1

    write_output(lines, args.output)

    if args.print_output:
        sys.stdout.write("\n".join(lines) + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
