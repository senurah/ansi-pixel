# Improvements & Evolution Roadmap (`IMPROVEMENTS.md`)

This document identifies all current limitations of `ansi-pixel`, defines real-world use cases, and outlines the technical roadmap to elevate this project into a widely adopted CLI utility and published Python package.

---

## 1. Analysis of Current Limitations & Bugs

### 1.1 Inadvertent White Pixel Erasure (Bug)

- **Current Behavior**:
  ```python
  top_empty = top_a < 128 or (top_r > 245 and top_g > 245 and top_b > 245)
  ```
  The script assumes any pixel with $R > 245, G > 245, B > 245$ is background and replaces it with an empty terminal space.
- **Problem**: In images that legitimately contain white elements (logos, eyes, clouds, text), these regions become transparent voids.
- **Solution**: Decouple alpha transparency from color filtering. Only transparent pixels ($A < 128$) are empty by default. Provide an optional `--chroma-key <HEX>` or `--trim-bg` flag for users who intentionally want to strip a white/solid background.

### 1.2 Dead Code & Broken Border Crop

- **Current Behavior**:
  ```python
  bg = Image.new("RGBA", img.size, (255, 255, 255, 0))
  bbox = img.getbbox()
  ```
  `bg` is allocated and never used. Furthermore, `getbbox()` on an RGBA image only trims where alpha is 0. It does not crop solid white backgrounds.
- **Solution**: Remove unused variables. If auto-trimming borders is desired, implement a robust bounding-box calculator that detects margin borders against background color or alpha.

### 1.3 Bloated ANSI Output (No Sequence Compression)

- **Current Behavior**:
  For every single column, the script emits:
  `\033[38;2;{top_r};{top_g};{top_b}m\033[48;2;{bot_r};{bot_g};{bot_b}m▀\033[0m`
- **Problem**: Every character carries up to 40 bytes of ANSI sequences, even if the entire row has the same color. A $100 \times 50$ output can exceed 150 KB.
- **Solution**: Implement an **ANSI Sequence Optimizer**:
  - Track current foreground and background colors.
  - Only emit color escape sequences when the color transitions.
  - Omit `\033[0m` resets between consecutive characters, resetting only at end-of-line or when entering a transparent block.
  - Result: 50% to 75% reduction in output size and faster rendering over remote SSH connections.

### 1.4 Hardcoded File Overwrites in CWD

- **Current Behavior**:
  `main.py` hardcodes file output paths to `./output.txt`, `./output.md`, or `./output.py`.
- **Problem**: When `ansi-pixel` is installed globally via `pip` or `pipx`, running it inside any project directory will create unwanted files in the user's working folder.
- **Solution**:
  - Follow standard UNIX CLI conventions: Print directly to `stdout` by default.
  - Provide `-o` / `--output <PATH>` to write to a specific destination file.
  - Provide `-f` / `--format <txt|md|py|js|html>` to specify the format.

### 1.5 Suboptimal Pixel Reading Loop

- **Current Behavior**:
  Nested Python loops calling `img.getpixel((x, y))` twice per coordinate.
- **Problem**: `getpixel()` in pure Python has high function-call overhead.
- **Solution**: Use `img.load()` (direct pixel buffer pointer) or byte arrays, which executes 10x–30x faster.

---

## 2. Real-World Purpose & Practical Applications

To make `ansi-pixel` a tool that developers actively seek out and integrate, we target four core use cases:

```
               ┌────────────────────────────────────────────────────────┐
               │                ansi-pixel Real Use Cases               │
               └────────────────────────────────────────────────────────┘
                    │                   │                   │
         ┌──────────┴────────┐ ┌────────┴────────┐ ┌────────┴────────┐
         │ CLI Tool Banners  │ │ Remote Terminal │ │ GitHub README   │
         │ & Startup Mascots │ │  Image Preview  │ │  & Doc Badges   │
         └───────────────────┘ └─────────────────┘ └─────────────────┘
```

1. **CLI Branding & Welcome Screens**:
   - CLI framework authors (FastAPI, Typer, Click, Node.js CLI tools) want branded logos in the console.
   - `ansi-pixel logo.png -f python` generates ready-to-paste Python banner code (`LOGO = "..."`).
   - `ansi-pixel logo.png -f js` generates JavaScript template strings for Node.js / Deno CLIs.
2. **Headless & SSH Image Previewer**:
   - Developers and sysadmins on remote servers or inside Docker containers lack GUI viewers.
   - Running `ansi-pixel cat.png` provides an immediate visual preview right in their shell.
   - Support streaming from pipes: `curl -sL https://site.com/image.png | ansi-pixel -`.
3. **Rich & Textual TUI Dashboard Avatars**:
   - Python terminal applications need to display user avatars, status badges, or product icons in terminal user interfaces.
   - Providing an importable Python API (`import ansi_pixel`) allows direct embedding into Rich consoles, Textual widgets, and prompt_toolkit applications.
4. **GitHub Markdown Colored Art**:
   - Modern GitHub Markdown renders ``ansi` code blocks. `ansi-pixel` produces ready-to-paste ANSI markdown blocks to spice up repository READMEs.

---

## 3. High-Priority Feature Improvements

### 3.1 Terminal Dimensions Auto-Detection

- Automatically read the user's terminal column width using `shutil.get_terminal_size()`.
- Default to fitting cleanly within the terminal (e.g. `width = min(terminal_cols, 80)`), eliminating horizontal line-wrapping on small screens while keeping images crisp.

### 3.2 Flexible Resampling Filters

- Pixel art logos look best with `Image.Resampling.NEAREST` (sharp pixels).
- Photographs and gradients look best with `Image.Resampling.LANCZOS` or `BILINEAR`.
- Provide `--filter <nearest|lanczos|bilinear>` (default: `nearest` for small images, `lanczos` for large photos).

### 3.3 Color Mode Reductions & Fallbacks

- **TrueColor (24-bit)**: `\033[38;2;r;g;bm` (Default).
- **256-Color (8-bit)**: Maps RGB to the standard xterm 256-color palette for older terminals or restricted SSH sessions.
- **16-Color (4-bit)**: Basic ANSI colors.
- **Grayscale / Monochromatic**: For clean ASCII/block aesthetic.
- **`NO_COLOR` Compliance**: Automatically disable ANSI escape sequences when the `NO_COLOR` environment variable is detected or when redirected to a non-TTY pipe without forced color flags.

### 3.4 Extended Exporters

- `-f ansi` (default): Pure ANSI escape strings.
- `-f md`: GitHub-compliant ``ansi` Markdown block.
- `-f py`: Clean Python snippet (`BANNER = "..."` or list of lines).
- `-f js`: ES6 JavaScript template literal (`export const banner = \`...\``).
- `-f html`: HTML `<pre>` block using styled `<span style="color:...;background:...">` for web pages.

---

## 4. Packaging & Distribution Plan

### Where to Release:

| Platform            | Channel                | Install Method                                                                    | Target Audience                         |
| :------------------ | :--------------------- | :-------------------------------------------------------------------------------- | :-------------------------------------- |
| **PyPI**            | Official Python Index  | `pip install ansi-pixel`<br>`pipx run ansi-pixel`<br>`uv tool install ansi-pixel` | Python developers, CLI users, sysadmins |
| **GitHub Releases** | Binaries & Assets      | Download pre-built binary                                                         | Users without Python runtime installed  |
| **Homebrew Tap**    | macOS / Linux packages | `brew install senuradesilva/tap/ansi-pixel`                                       | Mac / Linux terminal power users        |
| **Docker / GHCR**   | Container image        | `docker run --rm ghcr.io/senuradesilva/ansi-pixel`                                | CI/CD automation & pipeline inspection  |

### How to Package:

1. **Modern PEP 621 Standard**:
   - Adopt `pyproject.toml` with `hatchling` build backend.
   - Declare entrypoint script: `ansi-pixel = "ansi_pixel.cli:main"`.
2. **Source Code Structure**:
   ```
   ansi-pixel/
   ├── pyproject.toml
   ├── README.md
   ├── LICENSE
   ├── src/
   │   └── ansi_pixel/
   │       ├── __init__.py
   │       ├── cli.py
   │       ├── converter.py
   │       ├── optimizer.py
   │       ├── exporters.py
   │       └── py.typed
   └── tests/
       ├── test_cli.py
       ├── test_converter.py
       ├── test_optimizer.py
       └── test_exporters.py
   ```
3. **Automated Publishing via GitHub Actions**:
   - Configure **PyPI Trusted Publishing (OIDC)**: No manual API tokens or passwords needed.
   - Pushing a new git tag (e.g., `git tag v0.2.0 && git push origin v0.2.0`) builds the distribution wheels and securely publishes directly to PyPI.
