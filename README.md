# ansi-pixel

Convert images into true-color ANSI art for display in a terminal.

## Requirements

- Python 3.9+
- Pillow

Install Pillow in your virtual environment:

```bash
python3 -m pip install Pillow
```

## Usage

Pass the input image path to `main.py`:

```bash
python3 main.py path/to/image.png
```

Set a custom output width with `--width` or `-w`:

```bash
python3 main.py path/to/image.png --width 80
```

Write copyable Python source, with ANSI escape sequences represented as
`\\x1b` literals:

```bash
python3 main.py path/to/image.png --output py --no-print
```

This creates `output.py` containing an `art` list, like the sample in
`render.py`. The default `txt` format contains real terminal control
characters and is intended for terminal display, not source-code copy/paste.

The conversion logic lives in `img_to_ansi.py`, while `main.py` handles the
command-line interface.
