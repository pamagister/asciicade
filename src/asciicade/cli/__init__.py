"""Command line interface for asciicade."""

from __future__ import annotations

import argparse


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the asciicade CLI."""
    parser = argparse.ArgumentParser(
        prog="asciicade",
        description="asciicade - blank project CLI starter.",
    )
    parser.add_argument(
        "--name",
        default="World",
        help="Name to greet (default: World)",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the CLI application.

    Args:
        argv: Command line arguments. Defaults to sys.argv if None.

    Returns:
        Exit code (0 for success).
    """
    parser = build_parser()
    args = parser.parse_args(argv)
    print(f"Hello, {args.name}! Welcome to asciicade.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
