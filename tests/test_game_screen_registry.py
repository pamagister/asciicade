"""Tests for the gameplay screen registry."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import pytest

from asciicade.core.game import GameMetadata, GameMode
from asciicade.core.options import GameOptions
from asciicade.core.player import GuestPlayer
from asciicade.core.registry import GameRegistration
from asciicade.ui.context import AppContext
from asciicade.ui.screens.game_screen_factory import (
    GameScreenNotFoundError,
    GameScreenRegistry,
    build_default_screen_registry,
    create_game_screen,
)
from asciicade.ui.screens.pong_game import PongGameScreen
from asciicade.ui.screens.snake_game import SnakeGameScreen


@dataclass
class FakeScreen:
    """A screen stand-in that records how it was created."""

    context: object
    registration: GameRegistration
    mode: GameMode
    players: tuple[object, ...]
    options: GameOptions | None


def _registration(identifier: str) -> GameRegistration:
    """Return a registration for a test game."""
    metadata = GameMetadata(
        identifier=identifier,
        name=identifier.title(),
        description="A test game.",
        modes=(GameMode.SINGLE_PLAYER,),
        instructions="Test instructions.",
    )
    return GameRegistration(metadata, lambda: cast(object, None))


def test_default_registry_maps_builtin_screens() -> None:
    registry = build_default_screen_registry()

    assert registry.get("snake") is SnakeGameScreen
    assert registry.get("pong") is PongGameScreen
    assert len(registry) == 2
    assert "pong" in registry


def test_registry_creates_screen_with_factory() -> None:
    registry = GameScreenRegistry()
    registration = _registration("fake")
    options = GameOptions((("difficulty", "Hard"),))
    players = (GuestPlayer(1),)

    registry.register("fake", FakeScreen)
    screen = registry.create(
        cast(AppContext, object()),
        registration,
        GameMode.SINGLE_PLAYER,
        players,
        options=options,
    )

    assert isinstance(screen, FakeScreen)
    assert screen.options is options
    assert screen.players is players


def test_create_game_screen_uses_injected_registry() -> None:
    registry = GameScreenRegistry()
    registration = _registration("fake")
    registry.register("fake", FakeScreen)

    screen = create_game_screen(
        cast(AppContext, object()),
        registration,
        GameMode.SINGLE_PLAYER,
        (GuestPlayer(1),),
        registry=registry,
    )

    assert isinstance(screen, FakeScreen)


def test_registry_rejects_unknown_identifier() -> None:
    registry = GameScreenRegistry()

    with pytest.raises(GameScreenNotFoundError, match="missing"):
        registry.get("missing")


def test_registry_rejects_duplicate_registration() -> None:
    registry = GameScreenRegistry()
    registry.register("fake", FakeScreen)

    with pytest.raises(ValueError, match="already registered"):
        registry.register("fake", FakeScreen)


def test_create_game_screen_raises_for_unregistered_game() -> None:
    registry = GameScreenRegistry()
    registration = _registration("missing")

    with pytest.raises(GameScreenNotFoundError, match="missing"):
        create_game_screen(
            cast(AppContext, object()),
            registration,
            GameMode.SINGLE_PLAYER,
            (GuestPlayer(1),),
            registry=registry,
        )
