import argparse

from img_to_ansi import image_to_ansi


def parse_args() -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		description="Convert an image into true-color ANSI art."
	)
	parser.add_argument("image", help="Path to the input image")
	parser.add_argument(
		"-w",
		"--width",
		type=int,
		default=40,
		help="Output width in terminal characters (default: 40)",
	)
	return parser.parse_args()


def main() -> None:
	args = parse_args()
	for line in image_to_ansi(args.image, target_width=args.width):
		print(line)


if __name__ == "__main__":
	main()
