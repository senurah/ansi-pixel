# Project Engineering & Development Rules (`rules.md`)

This document defines the architectural principles, engineering standards, commit guidelines, and release criteria for the **`ansi-pixel`** project.

---

## 1. Core Principles

1. **Lightweight & Portable**:
   - Runtime dependencies must remain minimal. `Pillow` is currently the only required dependency.
   - Avoid introducing heavy dependencies (like `numpy`, `click`, or `rich`) unless strictly optional or proven essential.
   - Fast startup time (< 50ms) is a hard requirement for a responsive CLI tool.

2. **Unix Philosophy**:
   - Write programs that do one thing and do it well.
   - Output to `stdout` by default to enable composability (pipes, redirects: `ansi-pixel cat.png | fzf`, `ansi-pixel logo.png > logo.ansi`).
   - Diagnostic messages and progress bars must go to `stderr`, never polluting `stdout`.
   - Adhere to the [NO_COLOR](https://no-color.org) standard when the `NO_COLOR` environment variable is present or `stdout` is not a TTY.

3. **Performance First**:
   - Avoid slow per-pixel operations like repeated `Image.getpixel((x, y))` calls in pure Python loops. Use `Image.load()` or bulk memory access.
   - Optimize ANSI escape sequences: do not emit duplicate color codes for consecutive identical pixels. Compress sequences aggressively.

---

## 2. Python Code Standards

- **Target Versions**: Python 3.9 through Python 3.14.
- **Type Annotations**:
  - Full typing coverage is mandatory across all modules (`src/ansi_pixel/`).
  - Code must pass `mypy --strict` without errors.
  - Package must include a `py.typed` marker file.
- **Formatting & Linting**:
  - Code formatting and linting is enforced via [Ruff](https://github.com/astral-sh/ruff).
  - Maximum line length: 100 characters.
  - Docstrings must follow the Google or PEP 257 format and explain non-obvious algorithm details (such as terminal half-block color mapping).
- **Error Handling**:
  - Never let unhandled exceptions leak stack traces to end users for predictable errors (missing file, invalid format, permission denied).
  - Clean error exits must use standard POSIX exit codes:
    - `0`: Success
    - `1`: General error / Bad input
    - `2`: CLI usage / argument syntax error

---

## 3. Architecture & Modularity

- **Source Layout**: All application code lives in `src/ansi_pixel/`. Root directory is reserved for configuration and project documentation.
- **Separation of Concerns**:
  - `converter.py`: Pure image processing, resizing, and pixel extraction.
  - `optimizer.py`: ANSI escape sequence compression and color reduction.
  - `exporters/`: Target-specific rendering (raw ANSI, GitHub Markdown, Python code, JavaScript template, HTML).
  - `cli.py`: Argument parsing, terminal dimension detection, stdin/URL fetching, and exit handling.
- **Library Usability**:
  - `ansi_pixel` must be fully usable as an imported Python library, not just a standalone script.
  - Public API functions must accept either file paths, `io.BytesIO`, or `PIL.Image.Image` objects.

---

## 4. Git & Commit Conventions

Commit messages must strictly follow the **Conventional Commits** specification:

```text
<type>(<scope>): <short description>

[optional body]

[optional footer]
```

### Allowed Types:

- `feat`: A new user-facing feature or option.
- `fix`: A bug fix or correction.
- `perf`: A code change that improves rendering speed or reduces ANSI output size.
- `docs`: Documentation changes only (README, docstrings, guides).
- `refactor`: Code change that neither fixes a bug nor adds a feature.
- `test`: Adding missing tests or correcting existing tests.
- `chore`: Build process, dependency updates, CI/CD workflow adjustments.

### Examples:

- `feat(cli): auto-detect terminal width using shutil`
- `fix(converter): preserve white pixels unless explicit chroma-key is set`
- `perf(optimizer): collapse consecutive duplicate ANSI background sequences`
- `docs: add PyPI installation and library usage guide`

---

## 5. Testing & Quality Assurance

- **Framework**: `pytest`.
- **Requirements for Pull Requests**:
  - All new features and bug fixes must have corresponding unit tests in `tests/`.
  - Regression tests for edge cases (e.g., 1x1 pixel images, odd-height images, transparent PNGs, corrupted files).
  - Output format tests verifying that generated Python, Markdown, and ANSI strings parse without errors.
- **Test Automation**:
  - GitHub Actions must pass on all supported OS platforms (Ubuntu, macOS, Windows) and Python versions before merging.

---

## 6. Release & Versioning Policy

- Follow **Semantic Versioning (SemVer 2.0.0)** (`MAJOR.MINOR.PATCH`):
  - `MAJOR`: Breaking changes to public Python API or CLI arguments.
  - `MINOR`: New features or export formats added in a backwards-compatible manner.
  - `PATCH`: Backwards-compatible bug fixes and performance improvements.
- **Release Channels**:
  - PyPI: Production releases published automatically on git tag push (`v*.*.*`) via GitHub Actions OIDC Trusted Publishing.
  - TestPyPI: Pre-release validation before pushing to production PyPI.
  - GitHub Releases: Release notes with attached standalone binary executables.
