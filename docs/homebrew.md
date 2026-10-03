# Homebrew Distribution Guide

This guide describes how to distribute `ansi-pixel` via Homebrew on macOS and Linux using a custom Homebrew tap.

---

## 1. Setting Up a Personal Homebrew Tap

Homebrew allows distributing third-party formulas via custom taps. A tap is simply a Git repository named `homebrew-<name>`.

1. Create a public repository on GitHub named `homebrew-tap` (e.g. `https://github.com/senurah/homebrew-tap`).
2. Create a `Formula/` directory in the repository:
   ```bash
   mkdir -p Formula
   ```
3. Copy the formula template from [`packaging/homebrew/ansi-pixel.rb`](../packaging/homebrew/ansi-pixel.rb) into `Formula/ansi-pixel.rb`.

---

## 2. Updating Formula for a New Release

Whenever a new version (e.g. `v0.2.0`) is released:

1. Download the release binaries and the generated `checksums.txt` from the GitHub Release page:
   - `ansi-pixel-darwin-arm64` (macOS Apple Silicon)
   - `ansi-pixel-darwin-x86_64` (macOS Intel)
   - `ansi-pixel-linux-x86_64` (Linux x86_64)

2. Read the SHA256 hashes from `checksums.txt`:
   ```bash
   cat checksums.txt
   ```

3. Update `Formula/ansi-pixel.rb` in your tap repo:
   - Set `version "0.2.0"`
   - Fill in the corresponding `sha256` checksum for each architecture.

4. Commit and push:
   ```bash
   git add Formula/ansi-pixel.rb
   git commit -m "feat: release ansi-pixel 0.2.0"
   git push origin main
   ```

---

## 3. User Installation

Once the tap is published, users can install `ansi-pixel` with:

```bash
# Tap and install in one step
brew install senurah/tap/ansi-pixel
```

Or by explicitly adding the tap:

```bash
brew tap senurah/tap
brew install ansi-pixel
```

### Upgrading

```bash
brew update
brew upgrade ansi-pixel
```

---

## 4. Alternative: Source Virtualenv Formula

If you prefer building from the PyPI source distribution (`sdist`) using Homebrew's built-in Python virtualenv builder, use `homebrew-pypi-poet` to generate resource stanzas:

```bash
pip install homebrew-pypi-poet
poet -f ansi-pixel > Formula/ansi-pixel.rb
```
