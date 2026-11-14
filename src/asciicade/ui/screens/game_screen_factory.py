"""Factory for game-specific Textual screens."""

from __future__ import annotations

from textual.screen import Screen

from asciicade.core.game import GameMode
from asciicade.core.options import GameOptions
from asciicade.core.player import GuestPlayer, PlayerProfile
from asciicade.core.registry import GameRegistration
from asciicade.ui.context import AppContext


def create_game_screen(
    context: AppContext,
    registration: GameRegistration,
    mode: GameMode,
    players: tuple[PlayerProfile | GuestPlayer, ...],
    *,
    options: GameOptions | None = None,
) -> Screen[None]:
    """Create the gameplay screen registered for a game."""
    if registration.identifier == "snake":
        from asciicade.ui.screens.snake_game import SnakeGameScreen

        return SnakeGameScreen(context, registration, mode, players, options=options)
    if registration.identifier == "pong":
        from asciicade.ui.screens.pong_game import PongGameScreen

        return PongGameScreen(context, registration, mode, players, options=options)
    raise ValueError(f"No gameplay screen is registered for game '{registration.identifier}'.")
