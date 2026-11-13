"""Tests for the built-in game registry."""

from __future__ import annotations

from asciicade.core.game import GameMode
from asciicade.games import build_default_registry
from asciicade.games.snake import SnakeGame


def test_default_registry_contains_snake() -> None:
    registry = build_default_registry()

    registration = registry.get("snake")

    assert registration.metadata.name == "Snake"
    assert registration.modes == (
        GameMode.SINGLE_PLAYER,
        GameMode.MULTIPLAYER,
    )


def test_registered_factory_creates_snake_game() -> None:
    registry = build_default_registry()

    game = registry.get("snake").factory()

    assert isinstance(game, SnakeGame)
    assert game.metadata.identifier == "snake"
    assert not game.is_finished


def test_default_registry_is_not_empty() -> None:
    registry = build_default_registry()

    assert len(registry) == 1
    assert registry.identifiers() == ("snake",)
