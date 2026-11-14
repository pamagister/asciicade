"""Tests for the built-in game registry."""

from __future__ import annotations

from asciicade.core.game import GameMode
from asciicade.games import build_default_registry
from asciicade.games.pong import PongGame
from asciicade.games.snake import SnakeGame


def test_default_registry_contains_snake() -> None:
    registry = build_default_registry()

    registration = registry.get("snake")

    assert registration.metadata.name == "Snake"
    assert registration.modes == (
        GameMode.SINGLE_PLAYER,
        GameMode.MULTIPLAYER,
    )


def test_default_registry_contains_pong() -> None:
    registry = build_default_registry()

    registration = registry.get("pong")

    assert registration.metadata.name == "Pong"
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


def test_registered_factory_creates_pong_game() -> None:
    registry = build_default_registry()

    game = registry.get("pong").factory()

    assert isinstance(game, PongGame)
    assert game.metadata.identifier == "pong"
    assert not game.is_finished


def test_default_registry_contains_both_builtin_games() -> None:
    registry = build_default_registry()

    assert len(registry) == 2
    assert registry.identifiers() == ("pong", "snake")


def test_builtin_games_expose_the_tick_contract() -> None:
    registry = build_default_registry()

    for registration in registry.all():
        game = registration.factory()

        assert game.tick_rate > 0
        game.clear_pending()
        assert not game.is_finished
