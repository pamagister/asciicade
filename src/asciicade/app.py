"""Application layer for Asciicade.

The application layer coordinates the terminal UI, the game registry, game
sessions and the persistence layer. It must not contain game-specific rules.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol
from uuid import UUID

from asciicade.core.player import PlayerProfile
from asciicade.core.registry import GameRegistry
from asciicade.core.results import GameResult


class PlayerStore(Protocol):
    """Persistence boundary for player profiles."""

    def list(self) -> Sequence[PlayerProfile]:
        """Return all stored profiles."""
        ...

    def get(self, player_id: UUID) -> PlayerProfile | None:
        """Return a profile by identifier, or ``None`` when missing."""
        ...

    def create(self, name: str) -> PlayerProfile:
        """Create and persist a new profile."""
        ...


class ResultStore(Protocol):
    """Persistence boundary for completed game results."""

    def record(self, result: GameResult) -> int:
        """Persist a result and return its storage identifier."""
        ...


UIRunner = Callable[["ArcadeApplication"], int]


@dataclass
class ArcadeApplication:
    """Coordinate the UI, registry and persistence for one application run."""

    registry: GameRegistry
    players: PlayerStore
    results: ResultStore
    data_dir: Path | None = None

    def run(self, runner: UIRunner) -> int:
        """Run the application through the supplied UI runner.

        Args:
            runner: A callable that starts the terminal UI and returns an exit code.

        Returns:
            The process exit code.
        """
        return runner(self)


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
