"""Built-in games and the default game registry."""

from __future__ import annotations

from asciicade.core.registry import GameRegistration, GameRegistry
from asciicade.games.pong import PongGame
from asciicade.games.snake import SnakeGame


def build_default_registry() -> GameRegistry:
    """Return a registry containing all built-in games."""
    registry = GameRegistry()
    registry.register(GameRegistration(PongGame.metadata, PongGame))
    registry.register(GameRegistration(SnakeGame.metadata, SnakeGame))
    return registry


__all__ = ["build_default_registry"]
