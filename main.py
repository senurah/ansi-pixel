import argparse
from enum import Enum

from PIL import UnidentifiedImageError

from img_to_ansi import image_to_ansi


class OutputFormat(str, Enum):
	TXT = "txt"
	MD = "md"
	PY = "py"


def write_output(lines: list[str], output_format: OutputFormat) -> None:
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


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Convert an image into true-color ANSI art."
	)
	parser.add_argument("image", help="Image path")
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
		choices=OutputFormat,
		default=OutputFormat.TXT,
		help="Output format: txt, md, or py (default: txt)",
	)
	parser.add_argument(
		"--print",
		dest="print_output",
		action=argparse.BooleanOptionalAction,
		default=True,
		help="Print ANSI output to the terminal; use --no-print to disable",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	try:
		lines = image_to_ansi(args.image, target_width=args.width)
	except FileNotFoundError:
		raise SystemExit(f"Error: image not found: {args.image}")
	except UnidentifiedImageError:
		raise SystemExit(f"Error: unsupported or invalid image: {args.image}")
	except OSError as error:
		raise SystemExit(f"Error: could not open image: {error}")

	write_output(lines, args.output)

	if args.print_output:
		print("\n".join(lines))


if __name__ == "__main__":
	main()
