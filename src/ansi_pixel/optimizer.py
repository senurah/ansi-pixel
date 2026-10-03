"""ANSI sequence compression optimizer for terminal half-block rendering."""

from __future__ import annotations

import re
from collections.abc import Sequence

# ANSI escape sequence constants
ANSI_RESET: str = "\033[0m"

# Type alias for 24-bit RGB color tuple
RGBColor = tuple[int, int, int]


class AnsiOptimizer:
    """Optimizes ANSI escape sequences by tracking terminal state and omitting redundant codes.

    Terminal half-block rendering pairs two vertical pixels into a single character cell.
    Each cell uses the upper half block character ('▀') or lower half block ('▄') to render
    two sub-pixels using foreground and background colors:
      - Top colored, bottom empty: '▀' with foreground = top color, no background.
      - Top empty, bottom colored: '▄' with foreground = bottom color, no background.
      - Both colored: '▀' with foreground = top color, background = bottom color.
      - Both empty: space ' ' with no colors.

    This optimizer maintains the current active foreground and background colors across cells.
    Redundant color escapes are suppressed when consecutive blocks share colors, and formatting
    is reset only when entering transparent blocks or at the end of each line.
    """

    def __init__(self) -> None:
        """Initialize optimizer state with no active foreground or background colors."""
        self.current_fg: RGBColor | None = None
        self.current_bg: RGBColor | None = None

    def reset_state(self) -> str:
        """Reset internal color tracking and emit an ANSI reset sequence if styled.

        Returns:
            The ANSI reset sequence if any color was active, otherwise an empty string.
        """
        if self.current_fg is not None or self.current_bg is not None:
            self.current_fg = None
            self.current_bg = None
            return ANSI_RESET
        return ""

    def end_line(self) -> str:
        """Terminate the current row, resetting active colors to avoid style bleeding.

        Returns:
            The ANSI reset sequence if any color was active, otherwise an empty string.
        """
        return self.reset_state()

    def draw_cell(self, top: RGBColor | None, bot: RGBColor | None) -> str:
        """Render a single character cell for a pair of vertical pixels with optimized ANSI codes.

        Args:
            top: 24-bit RGB tuple for the top half-pixel, or None if transparent.
            bot: 24-bit RGB tuple for the bottom half-pixel, or None if transparent.

        Returns:
            Optimized ANSI escape string rendering the half-block cell.
        """
        # Case 1: Both sub-pixels are transparent
        if top is None and bot is None:
            if self.current_fg is not None or self.current_bg is not None:
                self.current_fg = None
                self.current_bg = None
                return f"{ANSI_RESET} "
            return " "

        # Case 2: Top transparent, bottom colored (lower half block '▄')
        if top is None and bot is not None:
            parts: list[str] = []
            if self.current_bg is not None:
                parts.append(ANSI_RESET)
                self.current_fg = None
                self.current_bg = None
            if self.current_fg != bot:
                parts.append(f"\033[38;2;{bot[0]};{bot[1]};{bot[2]}m")
                self.current_fg = bot
            parts.append("▄")
            return "".join(parts)

        # Case 3: Top colored, bottom transparent (upper half block '▀')
        if top is not None and bot is None:
            parts = []
            if self.current_bg is not None:
                parts.append(ANSI_RESET)
                self.current_fg = None
                self.current_bg = None
            if self.current_fg != top:
                parts.append(f"\033[38;2;{top[0]};{top[1]};{top[2]}m")
                self.current_fg = top
            parts.append("▀")
            return "".join(parts)

        # Case 4: Both sub-pixels colored (upper half block '▀' with FG=top, BG=bot)
        assert top is not None and bot is not None
        parts = []
        if self.current_fg != top:
            parts.append(f"\033[38;2;{top[0]};{top[1]};{top[2]}m")
            self.current_fg = top
        if self.current_bg != bot:
            parts.append(f"\033[48;2;{bot[0]};{bot[1]};{bot[2]}m")
            self.current_bg = bot
        parts.append("▀")
        return "".join(parts)

    def optimize_row(self, cells: Sequence[tuple[RGBColor | None, RGBColor | None]]) -> str:
        """Render and optimize an entire row of vertical pixel pairs.

        Args:
            cells: Sequence of (top_color, bottom_color) tuples representing each column.

        Returns:
            The complete optimized ANSI string for the row, guaranteed to end cleanly.
        """
        parts: list[str] = [self.draw_cell(top, bot) for top, bot in cells]
        end_seq = self.end_line()
        if end_seq:
            parts.append(end_seq)
        return "".join(parts)


def optimize_row_cells(cells: Sequence[tuple[RGBColor | None, RGBColor | None]]) -> str:
    """Convenience function to render and optimize a single row of cell pairs.

    Args:
        cells: Sequence of (top_color, bottom_color) tuples.

    Returns:
        The optimized ANSI string for the row.
    """
    return AnsiOptimizer().optimize_row(cells)


# Regex matching all ANSI escape sequences (CSI sequences ending in letter)
ANSI_ESCAPE_PATTERN: re.Pattern[str] = re.compile(r"\x1b\[[0-9;]*[a-zA-Z]")


def strip_ansi(text: str) -> str:
    """Remove all ANSI escape sequences from a string.

    Args:
        text: Text containing ANSI escape sequences.

    Returns:
        String with all ANSI escape codes stripped.
    """
    return ANSI_ESCAPE_PATTERN.sub("", text)
