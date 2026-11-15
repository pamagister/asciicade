"""Tests for headless gameplay preview rendering."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, cast

from asciicade.core.game import GameDocs, GameMetadata, GameMode
from asciicade.core.player import Player
from asciicade.core.registry import GameRegistration
from asciicade.games import build_default_registry
from asciicade.ui.preview import render_game_preview


def _docs() -> GameDocs:
    return GameDocs(
        summary="Preview game.",
        single_player="Single player body.",
        controls_short="Arrows/WASD move · Esc/P pause",
    )


def _metadata(identifier: str = "missing") -> GameMetadata:
    return GameMetadata(
        identifier=identifier,
        name=identifier.title(),
        modes=(GameMode.SINGLE_PLAYER,),
        docs=_docs(),
    )


class _DummyGame:
    """Minimal game stand-in without a registered screen."""

    def start(
        self,
        mode: GameMode,
        players: Sequence[Player],
        *,
        options: object | None = None,
    ) -> None:
        _ = mode, players, options

    def tick(self) -> None:
        pass


def test_preview_is_deterministic_for_builtin_games() -> None:
    for registration in build_default_registry().all():
        first = render_game_preview(registration)
        second = render_game_preview(registration)
        assert first is not None
        assert first == second


def test_preview_uses_single_player_defaults() -> None:
    for registration in build_default_registry().all():
        preview = render_game_preview(registration)
        assert preview is not None
        assert "SINGLE-PLAYER" in preview
        assert registration.metadata.name.upper() in preview
        assert "Guest 1" in preview


def test_preview_returns_none_without_a_game_instance() -> None:
    registration = GameRegistration(_metadata("fake"), cast(Any, lambda: None))

    assert render_game_preview(registration) is None


def test_preview_returns_none_without_a_registered_screen() -> None:
    registration = GameRegistration(_metadata("missing"), cast(Any, _DummyGame))

    assert render_game_preview(registration) is None
