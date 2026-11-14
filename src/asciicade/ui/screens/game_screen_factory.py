"""Registry for game-specific Textual screens."""

from __future__ import annotations

from functools import lru_cache
from typing import Protocol

from textual.screen import Screen

from asciicade.core.game import GameMode
from asciicade.core.options import GameOptions
from asciicade.core.player import GuestPlayer, PlayerProfile
from asciicade.core.registry import GameRegistration
from asciicade.ui.context import AppContext


class GameScreenNotFoundError(LookupError):
    """Raised when a registered game has no gameplay screen."""


class GameScreenFactory(Protocol):
    """A callable that builds a gameplay screen for a registered game."""

    def __call__(
        self,
        context: AppContext,
        registration: GameRegistration,
        mode: GameMode,
        players: tuple[PlayerProfile | GuestPlayer, ...],
        *,
        options: GameOptions | None = None,
    ) -> Screen[None]:
        """Create a gameplay screen."""
        ...


class GameScreenRegistry:
    """A collection of gameplay screen factories keyed by game identifier."""

    def __init__(self) -> None:
        """Create an empty screen registry."""
        self._factories: dict[str, GameScreenFactory] = {}

    def register(self, identifier: str, factory: GameScreenFactory) -> None:
        """Register the gameplay screen factory for a game.

        Args:
            identifier: The registered game identifier.
            factory: The callable that builds the gameplay screen.

        Raises:
            ValueError: If a factory is already registered for the identifier.
        """
        if identifier in self._factories:
            raise ValueError(f"A gameplay screen for '{identifier}' is already registered.")
        self._factories[identifier] = factory

    def get(self, identifier: str) -> GameScreenFactory:
        """Return the factory registered for a game.

        Raises:
            GameScreenNotFoundError: If no factory is registered.
        """
        try:
            return self._factories[identifier]
        except KeyError as exc:
            raise GameScreenNotFoundError(
                f"No gameplay screen is registered for game '{identifier}'."
            ) from exc

    def create(
        self,
        context: AppContext,
        registration: GameRegistration,
        mode: GameMode,
        players: tuple[PlayerProfile | GuestPlayer, ...],
        *,
        options: GameOptions | None = None,
    ) -> Screen[None]:
        """Create the gameplay screen registered for a game."""
        factory = self.get(registration.identifier)
        return factory(context, registration, mode, players, options=options)

    def identifiers(self) -> tuple[str, ...]:
        """Return the registered identifiers in sorted order."""
        return tuple(sorted(self._factories))

    def __contains__(self, identifier: object) -> bool:
        """Return whether a factory is registered for a game."""
        return identifier in self._factories

    def __len__(self) -> int:
        """Return the number of registered screen factories."""
        return len(self._factories)


def build_default_screen_registry() -> GameScreenRegistry:
    """Return a registry containing the built-in game screens."""
    from asciicade.ui.screens.blockfall_game import BlockfallGameScreen
    from asciicade.ui.screens.pong_game import PongGameScreen
    from asciicade.ui.screens.snake_game import SnakeGameScreen

    registry = GameScreenRegistry()
    registry.register("blockfall", BlockfallGameScreen)
    registry.register("pong", PongGameScreen)
    registry.register("snake", SnakeGameScreen)
    return registry


@lru_cache(maxsize=1)
def default_screen_registry() -> GameScreenRegistry:
    """Return the process-wide default screen registry."""
    return build_default_screen_registry()


def create_game_screen(
    context: AppContext,
    registration: GameRegistration,
    mode: GameMode,
    players: tuple[PlayerProfile | GuestPlayer, ...],
    *,
    options: GameOptions | None = None,
    registry: GameScreenRegistry | None = None,
) -> Screen[None]:
    """Create the gameplay screen registered for a game.

    Args:
        context: Shared application dependencies.
        registration: The selected game registration.
        mode: The selected game mode.
        players: The participating players.
        options: Optional resolved game options.
        registry: Optional screen registry override, used by tests.

    Raises:
        GameScreenNotFoundError: If the game has no registered screen.
    """
    active = registry or default_screen_registry()
    return active.create(context, registration, mode, players, options=options)
