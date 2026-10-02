# Master Task Plan (`TASK_PLAN.md`)

This document outlines the step-by-step roadmap to transform `ansi-pixel` into a production-grade tool and published package. Each phase contains concrete tasks, verification steps, and checkboxes for tracking progress during CLI execution.

---

## Progress Overview

- [x] **Phase 1**: Modern Packaging & Project Structure
- [ ] **Phase 2**: Core Engine Refactoring & ANSI Optimization
- [ ] **Phase 3**: CLI & Terminal Experience Modernization
- [ ] **Phase 4**: Multi-Format Exporters & Public Library API
- [ ] **Phase 5**: Test Suite, Documentation & Linting
- [ ] **Phase 6**: CI/CD Workflows, PyPI Release & Binaries

---

## Detailed Phases & Tasks

### Phase 1: Modern Packaging & Project Structure

- [x] **1.1** Initialize `pyproject.toml` using `hatchling` backend with PEP 621 metadata (version, authors, license, dependencies, classifiers).
- [x] **1.2** Declare CLI console script entry point: `ansi-pixel = "ansi_pixel.cli:main"`.
- [x] **1.3** Restructure project into standard `src/` layout:
  - Create `src/ansi_pixel/`.
  - Add `src/ansi_pixel/__init__.py` and `py.typed`.
  - Migrate `img_to_ansi.py` logic into `src/ansi_pixel/converter.py`.
  - Migrate `main.py` CLI logic into `src/ansi_pixel/cli.py`.
- [x] **1.4** Provide backward compatibility root `main.py` acting as a thin wrapper around `ansi_pixel.cli:main`.
- [x] **1.5** Verify local editable install via `pip install -e .` and check that `ansi-pixel --help` is accessible in the shell.

---

### Phase 2: Core Engine Refactoring & ANSI Optimization

- [ ] **2.1** Remove dead code (unused `bg` image allocation in `img_to_ansi.py`).
- [ ] **2.2** Fix the white-pixel erasure bug:
  - Default transparency strictly to alpha channel ($A < 128$).
  - Add optional `--trim-bg` or `--chroma-key` flags for intentional white/solid background stripping.
- [ ] **2.3** Refactor pixel access from `img.getpixel((x, y))` to fast direct buffer access via `img.load()`.
- [ ] **2.4** Implement ANSI sequence compression optimizer (`src/ansi_pixel/optimizer.py`):
  - Track active foreground and background color escape states.
  - Suppress redundant escape codes when consecutive blocks share the same color.
  - Reset formatting only at end-of-line or when entering a transparent block.
- [ ] **2.5** Add resampling filter support: `--filter [nearest|lanczos|bilinear]`.

---

### Phase 3: CLI & Terminal Experience Modernization

- [ ] **3.1** Implement automatic terminal width detection using `shutil.get_terminal_size()`.
- [ ] **3.2** Refactor CLI argument parsing:
  - Output to `stdout` by default (UNIX composability).
  - Add `-o, --output <FILE>` for saving output to a file.
  - Add `-f, --format <FORMAT>` (choices: `ansi`, `md`, `py`, `js`, `html`).
  - Add `-w, --width <INT>` with automatic terminal fitting when omitted.
- [ ] **3.3** Add support for reading from standard input: `cat photo.png | ansi-pixel -`.
- [ ] **3.4** Add support for direct image URLs: `ansi-pixel https://example.com/logo.png`.
- [ ] **3.5** Implement `NO_COLOR` standard and non-TTY pipe detection.

---

### Phase 4: Multi-Format Exporters & Public Library API

- [ ] **4.1** Implement dedicated exporter modules under `src/ansi_pixel/exporters/`:
  - `ansi.py`: Raw ANSI terminal string.
  - `markdown.py`: GitHub-compatible ``ansi` code block.
  - `code.py`: Copy-pasteable Python snippet and JavaScript template string.
  - `html.py`: Styled `<pre>` and `<span>` markup.
- [ ] **4.2** Define public library interface in `src/ansi_pixel/__init__.py`:
  - `render_image(source, width=..., format=...) -> str`
  - `image_to_ansi(source, width=...) -> list[str]`
- [ ] **4.3** Verify that external Python scripts can import and use `ansi_pixel` cleanly.

---

### Phase 5: Test Suite, Documentation & Linting

- [ ] **5.1** Configure `pytest` with comprehensive test cases in `tests/`:
  - `test_converter.py`: Half-block generation, aspect ratio math, alpha handling.
  - `test_optimizer.py`: Escape sequence compression ratio and formatting validation.
  - `test_exporters.py`: Verify validity of Markdown, Python, JS, and HTML outputs.
  - `test_cli.py`: Test CLI flags, help text, stdout redirection, and error exit codes.
- [ ] **5.2** Set up code quality tools:
  - Configure `ruff` in `pyproject.toml` for linting and formatting.
  - Configure `mypy` for strict type checking.
- [ ] **5.3** Overhaul `README.md`:
  - Add PyPI install instructions (`pip install ansi-pixel`, `pipx`, `uv`).
  - Document CLI usage with options table and pipe examples.
  - Add Python library usage quickstart.
  - Showcase updated screenshots and feature highlights.

---

### Phase 6: CI/CD Workflows, PyPI Release & Binaries

- [ ] **6.1** Create `.github/workflows/ci.yml` running tests and linters across Python 3.9–3.14 on Linux, macOS, and Windows.
- [ ] **6.2** Create `.github/workflows/publish.yml` using PyPI Trusted Publishing (OIDC) for automated release upon pushing git tags (`v*.*.*`).
- [ ] **6.3** Create `.github/workflows/release-binaries.yml` generating standalone executables with PyInstaller for GitHub Releases.
- [ ] **6.4** Create Homebrew formula template in documentation for macOS/Linux distribution.
