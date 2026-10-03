"""Unit tests for the ANSI sequence compression optimizer."""

from __future__ import annotations

from ansi_pixel.optimizer import ANSI_RESET, AnsiOptimizer, optimize_row_cells


def test_suppress_redundant_codes_same_row() -> None:
    """Verify that consecutive cells sharing identical colors do not re-emit escape sequences."""
    color_top = (255, 0, 0)
    color_bot = (0, 0, 255)
    # 10 identical cells
    cells = [(color_top, color_bot)] * 10

    optimizer = AnsiOptimizer()
    line = optimizer.optimize_row(cells)

    # Color codes should each appear only once
    fg_escape = f"\033[38;2;{color_top[0]};{color_top[1]};{color_top[2]}m"
    bg_escape = f"\033[48;2;{color_bot[0]};{color_bot[1]};{color_bot[2]}m"

    assert line.count(fg_escape) == 1
    assert line.count(bg_escape) == 1
    # 10 half-block characters
    assert line.count("▀") == 10
    # Line must end with ANSI_RESET
    assert line.endswith(ANSI_RESET)


def test_compression_ratio_savings() -> None:
    """Verify significant byte reduction for repeated colors vs unoptimized output."""
    color_top = (200, 100, 50)
    color_bot = (50, 100, 200)
    count = 40
    cells = [(color_top, color_bot)] * count

    # Unoptimized: emit FG + BG + char + RESET for every single column
    unoptimized_cell_len = len(
        f"\033[38;2;{color_top[0]};{color_top[1]};{color_top[2]}m"
        f"\033[48;2;{color_bot[0]};{color_bot[1]};{color_bot[2]}m▀\033[0m"
    )
    unoptimized_bytes = unoptimized_cell_len * count

    optimizer = AnsiOptimizer()
    optimized_line = optimizer.optimize_row(cells)
    optimized_bytes = len(optimized_line.encode("utf-8"))

    # Savings should exceed 70%
    savings = (1 - (optimized_bytes / unoptimized_bytes)) * 100
    assert savings > 70.0, f"Expected savings > 70%, got {savings:.1f}%"


def test_transition_to_transparent() -> None:
    """Verify reset sequence is emitted when transitioning to a transparent block."""
    color = (255, 0, 0)
    cells = [
        (color, color),  # Colored cell
        (None, None),  # Transparent cell -> triggers reset
        (None, None),  # Consecutive transparent -> just space, no redundant reset
        (color, None),  # Upper block
    ]

    optimizer = AnsiOptimizer()
    line = optimizer.optimize_row(cells)

    # First transparent block triggers reset
    assert f"{ANSI_RESET} " in line
    # Consecutive spaces are present
    assert "  " in line


def test_half_block_characters() -> None:
    """Verify proper character selection for top-only, bottom-only, both, and none."""
    optimizer = AnsiOptimizer()

    # Top only -> '▀' (upper half block)
    cell_top = optimizer.draw_cell((255, 0, 0), None)
    assert "▀" in cell_top
    assert "\033[38;2;255;0;0m" in cell_top
    assert "\033[48;2;" not in cell_top

    # Reset
    optimizer.reset_state()

    # Bottom only -> '▄' (lower half block)
    cell_bot = optimizer.draw_cell(None, (0, 255, 0))
    assert "▄" in cell_bot
    assert "\033[38;2;0;255;0m" in cell_bot
    assert "\033[48;2;" not in cell_bot

    # Reset
    optimizer.reset_state()

    # Both -> '▀' with FG and BG
    cell_both = optimizer.draw_cell((255, 0, 0), (0, 0, 255))
    assert "▀" in cell_both
    assert "\033[38;2;255;0;0m" in cell_both
    assert "\033[48;2;0;0;255m" in cell_both

    # None -> ' '
    optimizer.reset_state()
    cell_none = optimizer.draw_cell(None, None)
    assert cell_none == " "


def test_optimize_row_cells_helper() -> None:
    """Verify that optimize_row_cells function produces equivalent output."""
    cells = [((10, 20, 30), (40, 50, 60)), ((10, 20, 30), (40, 50, 60))]
    res1 = optimize_row_cells(cells)
    res2 = AnsiOptimizer().optimize_row(cells)
    assert res1 == res2


def test_consecutive_color_transitions() -> None:
    """Verify state transitions where only foreground or only background changes."""
    optimizer = AnsiOptimizer()

    # Initial cell: FG=(255, 0, 0), BG=(0, 0, 255)
    c1 = optimizer.draw_cell((255, 0, 0), (0, 0, 255))
    assert "\033[38;2;255;0;0m" in c1
    assert "\033[48;2;0;0;255m" in c1

    # Second cell: same FG, different BG -> only BG should be emitted
    c2 = optimizer.draw_cell((255, 0, 0), (0, 255, 0))
    assert "\033[38;2;255;0;0m" not in c2
    assert "\033[48;2;0;255;0m" in c2

    # Third cell: different FG, same BG -> only FG should be emitted
    c3 = optimizer.draw_cell((0, 0, 255), (0, 255, 0))
    assert "\033[38;2;0;0;255m" in c3
    assert "\033[48;2;0;255;0m" not in c3


def test_strip_ansi_comprehensive() -> None:
    """Verify strip_ansi removes all ANSI SGR and CSI escape sequences."""
    from ansi_pixel.optimizer import strip_ansi

    sample = (
        "\033[38;2;255;0;0mRed Text\033[0m "
        "\033[48;2;0;255;0mGreen BG\033[0m "
        "\033[1;34mBold Blue\033[0m"
    )
    clean = strip_ansi(sample)
    assert clean == "Red Text Green BG Bold Blue"
    assert "\033[" not in clean

    # Plain text remains unchanged
    assert strip_ansi("Plain string") == "Plain string"
    assert strip_ansi("") == ""
