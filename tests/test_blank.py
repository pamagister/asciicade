"""Tests for the blank asciicade project."""

from asciicade.cli.cli import main


def test_main_runs(capsys):
    """main() should print the welcome message without raising."""
    main([])
    captured = capsys.readouterr()
    assert "Welcome to asciicade" in captured.out


def test_cli_greeting(capsys):
    """CLI should greet the provided name."""
    main(["--name", "Paul"])
    captured = capsys.readouterr()
    assert "Hello, Paul!" in captured.out


def test_cli_default_greeting(capsys):
    """CLI should use the default name when none is given."""
    main([])
    captured = capsys.readouterr()
    assert "Hello, World!" in captured.out
