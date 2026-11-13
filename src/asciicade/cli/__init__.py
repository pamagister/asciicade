"""Command line interface for Asciicade."""

from __future__ import annotations

import argparse
from pathlib import Path

from asciicade import __version__


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser for the Asciicade CLI."""
    parser = argparse.ArgumentParser(
        prog="asciicade",
        description="A modular arcade game collection for the terminal.",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=None,
        help="Override the directory used for persistent game data.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the Asciicade application.

    Args:
        argv: Command line arguments. Defaults to ``sys.argv`` when ``None``.

    Returns:
        The process exit code.
    """
    parser = build_parser()
    args = parser.parse_args(argv)

    # Imported lazily so ``--version`` and ``--help`` stay fast and do not
    # require a terminal-capable environment.
    from asciicade.app import run_app

    return run_app(data_dir=args.data_dir)


if __name__ == "__main__":
    raise SystemExit(main())
