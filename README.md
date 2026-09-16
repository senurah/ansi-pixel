<p align="center">
	<img src="logo.png" alt="ansi-pixel logo" width="320">
</p>

<h1 align="center">ansi-pixel</h1>

<p align="center">Convert images into true-color ANSI art for display in a terminal.</p>

## Features

- Converts PNG, JPEG, and other Pillow-supported images to ANSI true-color output.
- Preserves the image aspect ratio while rendering with terminal half-block characters.
- Writes output as terminal text, Markdown, or copyable Python source.
- Supports a configurable output width.

## Requirements

- Python 3.9 or newer
- Pillow

Set up a virtual environment and install the dependency:

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
```

## Usage

Convert an image with the default output width of 36 characters:

```bash
python3 main.py path/to/image.png
```

The default `txt` output is written to `output.txt` and also printed to the terminal. Use `--width` or `-w` to change the output width:

```bash
python3 main.py path/to/image.png --width 80
```

Use `--no-print` when you only want to create an output file:

```bash
python3 main.py path/to/image.png --no-print
```

## Output formats

Select an output format with `--output` or `-o`:

| Format | File         | Purpose                                         |
| ------ | ------------ | ----------------------------------------------- |
| `txt`  | `output.txt` | ANSI control characters for terminal display    |
| `md`   | `output.md`  | ANSI art wrapped in a Markdown code block       |
| `py`   | `output.py`  | A Python `art` list with escaped ANSI sequences |

For example, generate copyable Python source without printing the art:

```bash
python3 main.py path/to/image.png --output py --no-print
```

Run `python3 main.py --help` to see all available options.

## Project structure

- `main.py` handles command-line arguments and output files.
- `img_to_ansi.py` contains the image conversion logic.
- `logo.png` is the project logo used in this README.

## Contributing

Bug reports and feature ideas are welcome. Before opening a pull request, please run the command you changed and include the input, options, and output format you tested. See the templates in `.github/` for the information requested in issues and pull requests.

## License

This project is licensed under the terms in [LICENSE](LICENSE).
