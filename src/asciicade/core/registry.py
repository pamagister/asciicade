"""Internal registry for games."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from asciicade.core.game import Game, GameMetadata, GameMode


class GameNotFoundError(LookupError):
    """Raised when a requested game is not registered."""


@dataclass(frozen=True, slots=True)
class GameRegistration:
    """A game together with its metadata and factory."""

    metadata: GameMetadata
    factory: Callable[[], Game]

    @property
    def identifier(self) -> str:
        """Return the game identifier."""
        return self.metadata.identifier

    @property
    def modes(self) -> tuple[GameMode, ...]:
        """Return the supported game modes."""
        return self.metadata.modes


class GameRegistry:
    """A mutable collection of registered games."""

    def __init__(self) -> None:
        """Create an empty registry."""
        self._games: dict[str, GameRegistration] = {}

    def register(self, registration: GameRegistration) -> None:
        """Register a game.

        Args:
            registration: The metadata and factory to register.

        Raises:
            ValueError: If a game with the same identifier is already registered.
        """
        identifier = registration.identifier
        if identifier in self._games:
            raise ValueError(f"Game '{identifier}' is already registered.")
        self._games[identifier] = registration

    def get(self, identifier: str) -> GameRegistration:
        """Return the registration for a game identifier.

        Raises:
            GameNotFoundError: If the game is not registered.
        """
        try:
            return self._games[identifier]
        except KeyError as exc:
            raise GameNotFoundError(f"Game '{identifier}' is not registered.") from exc

    def all(self) -> tuple[GameRegistration, ...]:
        """Return all registrations sorted by display name."""
        return tuple(sorted(self._games.values(), key=lambda item: item.metadata.name.lower()))

    def identifiers(self) -> tuple[str, ...]:
        """Return all registered identifiers in display order."""
        return tuple(item.identifier for item in self.all())

    def __contains__(self, identifier: object) -> bool:
        """Return whether a game identifier is registered."""
        return identifier in self._games

    def __len__(self) -> int:
        """Return the number of registered games."""
        return len(self._games)
