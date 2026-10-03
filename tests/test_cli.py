"""Unit tests for ansi-pixel command-line interface."""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
import urllib.error
from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image

from ansi_pixel.cli import main, parse_args
from ansi_pixel.optimizer import ANSI_ESCAPE_PATTERN


def test_cli_parse_defaults() -> None:
    """Verify default CLI arguments under Phase 3."""
    args = parse_args(["some_image.png"])
    assert args.image == "some_image.png"
    assert args.width is None
    assert args.output is None
    assert args.format is None
    assert args.filter == "nearest"
    assert args.trim_bg is False
    assert args.chroma_key is None
    assert args.color == "auto"
    assert args.print_output is None


def test_cli_custom_flags() -> None:
    """Verify custom flags parsing."""
    args = parse_args(
        [
            "logo.png",
            "-w",
            "50",
            "-o",
            "out.md",
            "-f",
            "md",
            "--filter",
            "lanczos",
            "--trim-bg",
            "--chroma-key",
            "#FFFFFF",
            "--color",
            "always",
            "--no-print",
        ]
    )
    assert args.image == "logo.png"
    assert args.width == 50
    assert args.output == "out.md"
    assert args.format == "md"
    assert args.filter == "lanczos"
    assert args.trim_bg is True
    assert args.chroma_key == "#FFFFFF"
    assert args.color == "always"
    assert args.print_output is False


def test_cli_no_color_flag_parsing() -> None:
    """Verify that --no-color flag sets color to 'never'."""
    args = parse_args(["logo.png", "--no-color"])
    assert args.color == "never"


def test_cli_color_flag_without_value() -> None:
    """Verify that standalone --color flag sets color to 'always'."""
    args = parse_args(["logo.png", "--color"])
    assert args.color == "always"


def test_cli_missing_image_file() -> None:
    """Verify that a missing image file produces exit code 1."""
    code = main(["non_existent_file_12345.png"])
    assert code == 1


def test_cli_missing_image_tty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that omitting image in an interactive TTY produces exit code 2."""
    monkeypatch.setattr(sys.stdin, "isatty", lambda: True)
    code = main([])
    assert code == 2


def test_cli_invalid_filter_arg() -> None:
    """Verify that an invalid filter value produces exit code 2."""
    code = main(["pixel_art_small.png", "--filter", "invalid_filter"])
    assert code == 2


def test_cli_invalid_width_arg() -> None:
    """Verify that a non-positive width produces exit code 2."""
    code = main(["pixel_art_small.png", "-w", "0"])
    assert code == 2
    code_neg = main(["pixel_art_small.png", "-w", "-5"])
    assert code_neg == 2


def test_cli_terminal_width_autodetect(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that terminal width is auto-detected via shutil.get_terminal_size() when omitted."""
    img_path = tmp_path / "detect.png"
    Image.new("RGBA", (100, 100), (0, 255, 0, 255)).save(img_path)

    # Mock terminal width to 42 columns
    monkeypatch.setattr(
        shutil, "get_terminal_size", lambda fallback=(80, 24): os.terminal_size((42, 24))
    )

    captured_out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured_out)

    code = main([str(img_path), "--color", "always"])
    assert code == 0

    lines = captured_out.getvalue().splitlines()
    assert len(lines) > 0
    # Strip ANSI escape codes to measure rendered character cell width
    plain_first_line = ANSI_ESCAPE_PATTERN.sub("", lines[0])
    assert len(plain_first_line) == 42


def test_cli_stdin_pipe_dash(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify reading image from standard input using '-'."""
    img = Image.new("RGBA", (10, 10), (255, 0, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    stdin_bytes = buf.getvalue()

    fake_stdin = MagicMock()
    fake_stdin.buffer = io.BytesIO(stdin_bytes)
    fake_stdin.isatty.return_value = False
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    captured_out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured_out)

    code = main(["-", "-w", "8", "--color", "always"])
    assert code == 0
    assert len(captured_out.getvalue()) > 0


def test_cli_stdin_pipe_no_arg(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify piped standard input auto-detection when image argument is omitted."""
    img = Image.new("RGBA", (10, 10), (0, 0, 255, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    stdin_bytes = buf.getvalue()

    fake_stdin = MagicMock()
    fake_stdin.buffer = io.BytesIO(stdin_bytes)
    fake_stdin.isatty.return_value = False
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    captured_out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured_out)

    code = main(["-w", "8", "--color", "always"])
    assert code == 0
    assert len(captured_out.getvalue()) > 0


def test_cli_empty_stdin(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that an empty stdin produces an error and exit code 1."""
    fake_stdin = MagicMock()
    fake_stdin.buffer = io.BytesIO(b"")
    fake_stdin.isatty.return_value = False
    monkeypatch.setattr(sys, "stdin", fake_stdin)

    code = main(["-"])
    assert code == 1


def test_cli_url_loading(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify loading and rendering an image directly from a URL."""
    img = Image.new("RGBA", (12, 12), (255, 255, 0, 255))
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    img_bytes = buf.getvalue()

    # Mock urllib.request.urlopen
    mock_response = MagicMock()
    mock_response.read.return_value = img_bytes
    mock_response.__enter__.return_value = mock_response
    mock_response.__exit__.return_value = None

    monkeypatch.setattr(
        "ansi_pixel.converter.urllib.request.urlopen",
        lambda req, timeout=15.0: mock_response,
    )

    captured_out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured_out)

    code = main(["https://example.com/art.png", "-w", "6", "--color", "always"])
    assert code == 0
    assert len(captured_out.getvalue()) > 0


def test_cli_url_network_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that a network error when fetching a URL produces exit code 1."""

    def fail_urlopen(*args: object, **kwargs: object) -> MagicMock:
        raise urllib.error.URLError("Connection refused")

    monkeypatch.setattr("ansi_pixel.converter.urllib.request.urlopen", fail_urlopen)

    code = main(["https://example.com/missing.png"])
    assert code == 1


def test_cli_url_http_error(monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that an HTTP 404 error produces exit code 1."""
    from email.message import Message

    def fail_http(*args: object, **kwargs: object) -> MagicMock:
        raise urllib.error.HTTPError(
            "https://example.com/notfound.png",
            404,
            "Not Found",
            Message(),
            None,
        )

    monkeypatch.setattr("ansi_pixel.converter.urllib.request.urlopen", fail_http)

    code = main(["https://example.com/notfound.png"])
    assert code == 1


def test_cli_stdout_default(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that output is directed to stdout by default."""
    img_path = tmp_path / "stdout_test.png"
    Image.new("RGBA", (8, 8), (100, 150, 200, 255)).save(img_path)

    captured_out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured_out)

    code = main([str(img_path), "-w", "8", "--color", "always"])
    assert code == 0
    assert len(captured_out.getvalue()) > 0


def test_cli_file_output_redirection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that -o/--output saves to file and suppresses stdout unless --print is used."""
    img_path = tmp_path / "file_test.png"
    out_path = tmp_path / "banner.ans"
    Image.new("RGBA", (8, 8), (100, 150, 200, 255)).save(img_path)

    captured_out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured_out)

    code = main([str(img_path), "-w", "8", "-o", str(out_path)])
    assert code == 0
    # stdout should be silent when -o is given
    assert captured_out.getvalue() == ""
    # File must exist and contain content
    assert out_path.exists()
    assert len(out_path.read_text(encoding="utf-8")) > 0


def test_cli_file_output_with_print(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that --print prints to stdout even when -o is given."""
    img_path = tmp_path / "file_print.png"
    out_path = tmp_path / "banner_print.ans"
    Image.new("RGBA", (8, 8), (100, 150, 200, 255)).save(img_path)

    captured_out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured_out)

    code = main([str(img_path), "-w", "8", "-o", str(out_path), "--print"])
    assert code == 0
    assert len(captured_out.getvalue()) > 0
    assert out_path.exists()


@pytest.mark.parametrize("fmt", ["ansi", "md", "py", "js", "html"])
def test_cli_output_formats(fmt: str, tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify all supported output format choices (-f)."""
    img_path = tmp_path / f"test_{fmt}.png"
    Image.new("RGBA", (6, 6), (200, 50, 100, 255)).save(img_path)

    captured_out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured_out)

    code = main([str(img_path), "-w", "6", "-f", fmt, "--color", "always"])
    assert code == 0
    content = captured_out.getvalue()
    if fmt == "md":
        assert content.startswith("```ansi\n") and content.endswith("```\n")
    elif fmt == "py":
        assert content.startswith("art = [\n") and content.endswith("]\n")
    elif fmt == "js":
        assert content.startswith("const art = `\n") and content.endswith("`;\n")
    elif fmt == "html":
        assert "<pre" in content and "</pre>" in content
    elif fmt == "ansi":
        assert "\033[" in content


def test_cli_inferred_format_from_output_extension(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Verify that format is inferred from the -o file extension."""
    img_path = tmp_path / "infer_test.png"
    Image.new("RGBA", (6, 6), (200, 50, 100, 255)).save(img_path)

    md_out = tmp_path / "result.md"
    code = main([str(img_path), "-w", "6", "-o", str(md_out)])
    assert code == 0
    assert md_out.read_text(encoding="utf-8").startswith("```ansi\n")

    py_out = tmp_path / "result.py"
    code = main([str(img_path), "-w", "6", "-o", str(py_out)])
    assert code == 0
    assert py_out.read_text(encoding="utf-8").startswith("art = [\n")


def test_cli_no_color_env_var(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that NO_COLOR environment variable suppresses ANSI color escape sequences."""
    img_path = tmp_path / "nocolor.png"
    Image.new("RGBA", (6, 6), (255, 0, 0, 255)).save(img_path)

    monkeypatch.setenv("NO_COLOR", "1")
    captured_out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured_out)

    code = main([str(img_path), "-w", "6"])
    assert code == 0
    output = captured_out.getvalue()
    assert "\033[" not in output
    assert len(output.strip()) > 0


def test_cli_no_color_flag(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that --no-color flag suppresses ANSI color escape sequences."""
    img_path = tmp_path / "nocolor_flag.png"
    Image.new("RGBA", (6, 6), (255, 0, 0, 255)).save(img_path)

    captured_out = io.StringIO()
    monkeypatch.setattr(sys, "stdout", captured_out)

    code = main([str(img_path), "-w", "6", "--no-color"])
    assert code == 0
    output = captured_out.getvalue()
    assert "\033[" not in output


def test_cli_non_tty_pipe_detection(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that in default 'auto' mode, piping to a non-TTY suppresses ANSI color escapes."""
    img_path = tmp_path / "nontty.png"
    Image.new("RGBA", (6, 6), (255, 0, 0, 255)).save(img_path)

    fake_stdout = io.StringIO()
    # StringIO does not have isatty() returning True
    assert not fake_stdout.isatty()
    monkeypatch.setattr(sys, "stdout", fake_stdout)

    code = main([str(img_path), "-w", "6"])
    assert code == 0
    output = fake_stdout.getvalue()
    assert "\033[" not in output


def test_cli_color_always_overrides_pipe(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Verify that --color=always emits ANSI color escapes even when piped to non-TTY."""
    img_path = tmp_path / "color_always.png"
    Image.new("RGBA", (6, 6), (255, 0, 0, 255)).save(img_path)

    fake_stdout = io.StringIO()
    monkeypatch.setattr(sys, "stdout", fake_stdout)

    code = main([str(img_path), "-w", "6", "--color", "always"])
    assert code == 0
    output = fake_stdout.getvalue()
    assert "\033[" in output


def test_cli_execution_with_test_image(tmp_path: Path) -> None:
    """Verify subprocess execution with test image."""
    img_path = tmp_path / "test.png"
    Image.new("RGBA", (10, 10), (255, 0, 0, 255)).save(img_path)

    result = subprocess.run(
        [sys.executable, "-m", "ansi_pixel.cli", str(img_path), "-w", "10", "--no-print"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0


def test_cli_version_flag(capsys: pytest.CaptureFixture[str]) -> None:
    """Verify that -V and --version output the program name and version string."""
    from ansi_pixel import __version__

    code = main(["--version"])
    assert code == 0
    captured = capsys.readouterr()
    assert (
        f"ansi-pixel {__version__}" in captured.out or f"ansi-pixel {__version__}" in captured.err
    )

    code = main(["-V"])
    assert code == 0
    captured = capsys.readouterr()
    assert (
        f"ansi-pixel {__version__}" in captured.out or f"ansi-pixel {__version__}" in captured.err
    )
