"""Application layer for Asciicade.

The application layer coordinates the terminal UI, the game registry, game
sessions and the persistence layer. It must not contain game-specific rules.
"""

from __future__ import annotations

from pathlib import Path


def run_app(data_dir: Path | None = None) -> int:
    """Run the Asciicade application.

    Args:
        data_dir: Optional override for the persistent data directory.

    Returns:
        The process exit code.
    """
    _ = data_dir
    print("Asciicade is starting up.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_app())
