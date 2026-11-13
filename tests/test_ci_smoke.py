"""Minimal smoke test to keep GitHub Actions CI green."""

from asciicade.cli.cli import main


def test_cli_smoke(capsys):
    """The CLI entry point must run and print a greeting without raising."""
    return_code = main([])
    captured = capsys.readouterr()
    assert return_code == 0
    assert "Welcome to asciicade" in captured.out
