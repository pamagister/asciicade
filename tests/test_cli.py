"""Tests for the Asciicade command line interface."""

from __future__ import annotations

import pytest

from asciicade import __version__
from asciicade.cli import build_parser, main


def test_parser_exposes_data_dir_option() -> None:
    """The parser should accept an optional data directory override."""
    parser = build_parser()
    args = parser.parse_args(["--data-dir", "/tmp/asciicade-test"])
    assert str(args.data_dir) == "/tmp/asciicade-test"


def test_parser_defaults_data_dir_to_none() -> None:
    """Without an override the application chooses the platform data directory."""
    parser = build_parser()
    args = parser.parse_args([])
    assert args.data_dir is None


def test_version_flag_exits_successfully(capsys: pytest.CaptureFixture[str]) -> None:
    """``--version`` should print the package version and exit cleanly."""
    with pytest.raises(SystemExit) as exc_info:
        main(["--version"])

    assert exc_info.value.code == 0
    assert __version__ in capsys.readouterr().out
