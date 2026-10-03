"""Backward-compatibility wrapper for ansi-pixel CLI."""

from __future__ import annotations

import sys
from pathlib import Path

# Ensure src layout is discoverable when executing directly from repository root
_src_dir = str(Path(__file__).resolve().parent / "src")
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

from ansi_pixel.cli import main  # noqa: E402

if __name__ == "__main__":
    sys.exit(main())
