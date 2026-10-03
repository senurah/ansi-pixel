<p align="center">
  <img src="https://raw.githubusercontent.com/senurah/ansi-pixel/main/assets/logo.png" alt="ansi-pixel logo" width="320">
</p>

<h1 align="center">ansi-pixel</h1>

<p align="center">
  <strong>Convert images into true-color ANSI art for terminal banners, SSH previews, and Markdown.</strong>
</p>

<p align="center">
  <a href="https://pypi.org/project/ansi-pixel/"><img src="https://img.shields.io/pypi/v/ansi-pixel.svg" alt="PyPI version"></a>
  <a href="https://pypi.org/project/ansi-pixel/"><img src="https://img.shields.io/pypi/pyversions/ansi-pixel.svg" alt="Python versions"></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License"></a>
  <a href="https://github.com/astral-sh/ruff"><img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff"></a>
  <a href="https://mypy-lang.org/"><img src="https://img.shields.io/badge/type_checker-mypy-blue.svg" alt="mypy"></a>
</p>

---

## Highlights

- 🎨 **True-Color 24-Bit ANSI**: Half-block terminal characters (`▀` and `▄`) pair vertical pixel rows to achieve double vertical resolution without square distortion.
- ⚡ **Optimizer Sequence Compression**: Aggressively collapses redundant foreground/background color escapes, achieving 70%+ byte reduction.
- 🖥️ **Terminal Width Auto-Fitting**: Auto-detects terminal width via `shutil.get_terminal_size()` when width is omitted.
- 🔄 **UNIX Composability**: Writes to `stdout` by default; fully supports pipes and reading from standard input (`cat photo.png | ansi-pixel -`).
- 🌐 **Remote Image URLs**: Convert remote images directly from HTTP/HTTPS URLs (`ansi-pixel https://example.com/logo.png`).
- 📦 **Multi-Format Exporters**: Output to raw ANSI, GitHub Markdown (` ```ansi `), copyable Python snippets (`art = [...]`), JavaScript template strings, and styled HTML (`<pre>` & `<span>`).
- 🚫 **NO_COLOR Standard**: Adheres to the [no-color.org](https://no-color.org) specification and automatic non-TTY pipe detection.
- 🎛️ **Resampling & Transparency**: Multiple resampling filters (`nearest`, `lanczos`, `bilinear`), automatic alpha transparency, background trimming (`--trim-bg`), and hex chroma-keying (`--chroma-key`).

---

## Installation

### With `pip`
```bash
pip install ansi-pixel
```

### With `pipx` (Standalone execution)
```bash
pipx run ansi-pixel logo.png
```

### With `uv`
```bash
# Run ephemerally
uvx ansi-pixel logo.png

# Or add to your project
uv add ansi-pixel
```

### With Homebrew (macOS / Linux)
```bash
brew install senurah/tap/ansi-pixel
```

### Standalone Executable (Zero Dependencies)
Download prebuilt binaries for Linux, macOS, or Windows directly from [GitHub Releases](https://github.com/senurah/ansi-pixel/releases):
```bash
# Example on Linux x86_64
curl -L -o ansi-pixel https://github.com/senurah/ansi-pixel/releases/latest/download/ansi-pixel-linux-x86_64
chmod +x ansi-pixel
./ansi-pixel logo.png
```

---

## Command-Line Usage

### Basic Usage
Convert an image and auto-fit to your current terminal width:
```bash
ansi-pixel logo.png
```

### Specify Output Width
Set an explicit character column width:
```bash
ansi-pixel logo.png -w 60
```

### Read from Standard Input (Pipes)
Read piped image data using `-` or implicit pipe detection:
```bash
cat photo.png | ansi-pixel -
curl -s https://example.com/art.png | ansi-pixel -w 50
```

### Load from Image URLs
Fetch and render remote images directly:
```bash
ansi-pixel "https://raw.githubusercontent.com/senurah/ansi-pixel/main/assets/logo.png" -w 40
```

### Export to Files
Save the rendered art directly to a file using `-o, --output`:
```bash
# Save raw ANSI art for terminal banners (/etc/motd)
ansi-pixel logo.png -o banner.ans

# Save as GitHub-compatible Markdown (automatically inferred from .md extension)
ansi-pixel logo.png -o banner.md

# Save as an executable Python snippet
ansi-pixel logo.png -o art.py

# Save as styled HTML
ansi-pixel logo.png -o banner.html
```

### Select Output Format
Explicitly choose a serialization format using `-f, --format`:
```bash
# Output GitHub-ready Markdown code block to stdout
ansi-pixel logo.png -f md

# Output copy-pasteable JavaScript template literal
ansi-pixel logo.png -f js

# Output HTML snippet
ansi-pixel logo.png -f html
```

### Resampling Filters & Transparency
```bash
# Smooth downsampling for photographs using Lanczos filter
ansi-pixel photo.jpg --filter lanczos -w 80

# Strip near-white solid backgrounds and auto-crop borders
ansi-pixel icon.png --trim-bg

# Chroma-key a specific background color to transparent
ansi-pixel sprite.png --chroma-key "#00FF00"
```

### Color Control & `NO_COLOR`
```bash
# Force ANSI colors even when redirecting or piping into tools like fzf
ansi-pixel --color logo.png | fzf --ansi

# Disable ANSI color sequences explicitly
ansi-pixel --no-color logo.png

# Respects the NO_COLOR standard automatically
NO_COLOR=1 ansi-pixel logo.png
```

---

## CLI Options Reference

| Option | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `image` | `str` | `None` / `stdin` | Path to image file, HTTP/HTTPS URL, or `-` for stdin. |
| `-w, --width` | `int` | Auto (terminal) | Target output width in terminal character columns. |
| `-o, --output` | `FILE` | `stdout` | Write output to a file instead of standard output. |
| `-f, --format` | `choice` | `ansi` | Output format: `ansi`, `md`, `py`, `js`, `html`, `txt`. |
| `--filter` | `choice` | `nearest` | Resampling filter: `nearest`, `lanczos`, `bilinear`. |
| `--trim-bg` | `flag` | `False` | Strip solid white backgrounds and crop empty borders. |
| `--chroma-key` | `HEX` | `None` | Hex color to strip as transparent (e.g. `#FFFFFF` or `00FF00`). |
| `--color` | `choice` | `auto` | When to emit color escapes: `auto`, `always`, `never`. |
| `--no-color` | `flag` | `False` | Disable ANSI color codes (alias for `--color=never`). |
| `--print / --no-print` | `flag` | `True` | Control printing to stdout when `-o/--output` is provided. |
| `-h, --help` | `flag` | | Show help message and exit. |

---

## Python Library API Quickstart

`ansi-pixel` is fully usable as an imported Python library with strict typing and no external runtime dependencies beyond Pillow.

```python
from PIL import Image
from ansi_pixel import OutputFormat, ResamplingFilter, image_to_ansi, render_image

# 1. Quick render to Markdown string
markdown_art = render_image("logo.png", width=40, format="md")
print(markdown_art)

# 2. Render to a styled, standalone HTML document
html_doc = render_image(
    "logo.png",
    width=50,
    format=OutputFormat.HTML,
    standalone=True,
    title="Terminal Logo",
)

# 3. Render copy-pasteable Python snippet
py_code = render_image("logo.png", width=30, format="py", var_name="banner")

# 4. Get raw list of ANSI lines for custom terminal loops
lines = image_to_ansi(
    "logo.png",
    width=36,
    filter=ResamplingFilter.LANCZOS,
    trim_bg=True,
)
for line in lines:
    print(line)

# 5. Accepts paths, PIL Images, raw bytes, BytesIO, and URLs
img = Image.open("logo.png")
ansi_text = render_image(img, width=40)
```

---

## Output Formats Explained

| Format | Option | Description |
| :--- | :--- | :--- |
| **ANSI** | `-f ansi` | Raw 24-bit true-color escape sequences ending with resets. |
| **Markdown** | `-f md` | GitHub-flavored ````ansi` fenced code block rendering colored art in Markdown. |
| **Python** | `-f py` | Executable Python source declaring an `art = [...]` list of lines. |
| **JavaScript** | `-f js` | ES6+ template literal (`const art = `...`;`) with syntax escaping. |
| **HTML** | `-f html` | Inline `<pre>` and `<span>` tags with CSS RGB styles (supports standalone HTML5). |

---

## Project Structure

```text
ansi-pixel/
├── src/
│   └── ansi_pixel/
│       ├── __init__.py      # Public library API (render_image, image_to_ansi, etc.)
│       ├── cli.py           # Command-line interface entry point & argument parsing
│       ├── converter.py     # Image decoding, aspect math, and half-block generation
│       ├── optimizer.py     # ANSI escape sequence state tracking and compression
│       ├── render.py        # Top-level rendering and serialization engine
│       ├── py.typed         # PEP 561 inline type annotation marker
│       └── exporters/       # Target-specific serialization formats
│           ├── __init__.py  # Exporter registry & OutputFormat enum
│           ├── ansi.py      # Raw ANSI string exporter
│           ├── code.py      # Python and JavaScript code snippet exporters
│           ├── html.py      # Styled HTML <pre> and <span> exporter
│           └── markdown.py  # GitHub-compatible Markdown ```ansi code block exporter
├── tests/                   # Comprehensive pytest test suite (112 tests)
├── pyproject.toml           # PEP 621 packaging metadata, hatchling build, ruff & mypy configs
└── README.md
```

---

## Development & Quality Assurance

Run test suite, type checker, and linters:

```bash
# Run unit tests
pytest

# Strict type checking
mypy src tests

# Code formatting and linting
ruff check src tests
ruff format --check src tests
```

---

## License

This project is licensed under the terms of the [MIT License](LICENSE).
