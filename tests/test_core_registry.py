"""Tests for game metadata and the internal game registry."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field

import pytest

from asciicade.core.game import GameDocs, GameMetadata, GameMode
from asciicade.core.input import InputEvent
from asciicade.core.player import Player
from asciicade.core.registry import (
    GameNotFoundError,
    GameRegistration,
    GameRegistry,
)
from asciicade.core.results import GameResult


@dataclass
class FakeGame:
    """A minimal game implementation used only for registry tests."""

    metadata: GameMetadata
    started: list[tuple[GameMode, Sequence[Player]]] = field(default_factory=list)
    finished: bool = False

    def start(self, mode: GameMode, players: Sequence[Player]) -> None:
        self.started.append((mode, tuple(players)))

    def handle_input(self, event: InputEvent) -> None:
        _ = event

    def clear_pending(self) -> None:
        pass

    def tick(self) -> None:
        self.finished = True

    @property
    def tick_rate(self) -> float:
        return 60.0

    @property
    def is_finished(self) -> bool:
        return self.finished

    @property
    def result(self) -> GameResult | None:
        return None


def _metadata(identifier: str, name: str) -> GameMetadata:
    return GameMetadata(
        identifier=identifier,
        name=name,
        modes=(GameMode.SINGLE_PLAYER,),
        docs=_docs(),
    )


def _docs() -> GameDocs:
    """Return minimal valid docs for a test game."""
    return GameDocs(
        summary="Test game.",
        single_player="Single player body.",
        controls_short="Arrows/WASD move · Esc/P pause",
    )


def test_metadata_requires_identifier_name_and_modes() -> None:
    with pytest.raises(ValueError, match="identifier"):
        GameMetadata("", "Game", (GameMode.SINGLE_PLAYER,), _docs())
    with pytest.raises(ValueError, match="name"):
        GameMetadata("id", "  ", (GameMode.SINGLE_PLAYER,), _docs())
    with pytest.raises(ValueError, match="at least one mode"):
        GameMetadata("id", "Game", (), _docs())


def test_metadata_rejects_duplicate_modes() -> None:
    with pytest.raises(ValueError, match="unique"):
        GameMetadata(
            "id",
            "Game",
            (GameMode.SINGLE_PLAYER, GameMode.SINGLE_PLAYER),
            _docs(),
        )


def test_metadata_requires_multiplayer_docs_for_multiplayer_games() -> None:
    with pytest.raises(ValueError, match="two-player"):
        GameMetadata(
            "id",
            "Game",
            (GameMode.MULTIPLAYER,),
            GameDocs(
                summary="s",
                single_player="sp",
                controls_short="Press Escape to pause.",
            ),
        )


def test_metadata_instructions_are_derived_from_docs() -> None:
    metadata = GameMetadata(
        "id",
        "Game",
        (GameMode.SINGLE_PLAYER, GameMode.MULTIPLAYER),
        GameDocs(
            summary="Objective: win.",
            single_player="Do the single-player thing.",
            multiplayer="Do the two-player thing.",
            controls_short="Press Escape to pause.",
            controls_long="Press Escape or P to pause during a game.",
        ),
    )
    assert "Objective: win." in metadata.instructions
    assert "Single player:\nDo the single-player thing." in metadata.instructions
    assert "Two players:\nDo the two-player thing." in metadata.instructions
    assert "Press Escape or P to pause during a game." in metadata.instructions
    assert "Press Escape to pause." not in metadata.instructions


def test_docs_controls_hint_uses_mode_specific_hint() -> None:
    docs = GameDocs(
        summary="s",
        single_player="sp",
        controls_short="Short hint.",
        controls_short_multiplayer="Two-player hint.",
    )

    assert docs.controls_hint(GameMode.SINGLE_PLAYER) == "Short hint."
    assert docs.controls_hint(GameMode.MULTIPLAYER) == "Two-player hint."


def test_docs_controls_hint_falls_back_to_short_hint() -> None:
    docs = GameDocs(summary="s", single_player="sp", controls_short="Short hint.")

    assert docs.controls_hint(GameMode.MULTIPLAYER) == "Short hint."


def test_docs_page_description_falls_back_to_summary() -> None:
    docs = GameDocs(summary="Summary.", single_player="sp", controls_short="Hint.")

    assert docs.page_description == "Summary."

    with_long = GameDocs(
        summary="Summary.",
        single_player="sp",
        controls_short="Hint.",
        long_description="Long description.",
    )
    assert with_long.page_description == "Long description."


def test_docs_controls_hint_must_be_single_line() -> None:
    with pytest.raises(ValueError, match="single line"):
        GameDocs(
            summary="s",
            single_player="sp",
            controls_short="First line.\nSecond line.",
        )
    with pytest.raises(ValueError, match="single line"):
        GameDocs(
            summary="s",
            single_player="sp",
            controls_short="Hint.",
            controls_short_multiplayer="First line.\nSecond line.",
        )


def test_docs_controls_hint_has_a_length_limit() -> None:
    with pytest.raises(ValueError, match="at most"):
        GameDocs(
            summary="s",
            single_player="sp",
            controls_short="x" * 81,
        )


def test_registry_registers_and_retrieves_games() -> None:
    registry = GameRegistry()
    registration = GameRegistration(
        _metadata("snake", "Snake"), lambda: FakeGame(_metadata("snake", "Snake"))
    )

    registry.register(registration)

    assert "snake" in registry
    assert len(registry) == 1
    assert registry.get("snake") is registration
    assert registry.identifiers() == ("snake",)
    assert isinstance(registry.get("snake").factory(), FakeGame)


def test_registry_rejects_duplicate_identifier() -> None:
    registry = GameRegistry()
    registration = GameRegistration(
        _metadata("snake", "Snake"), lambda: FakeGame(_metadata("snake", "Snake"))
    )

    registry.register(registration)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(registration)


def test_registry_raises_for_unknown_game() -> None:
    registry = GameRegistry()

    with pytest.raises(GameNotFoundError, match="not registered"):
        registry.get("missing")


def test_registry_returns_games_sorted_by_name() -> None:
    registry = GameRegistry()
    for identifier, name in (("z", "Zed"), ("a", "Alpha"), ("m", "Mango")):
        metadata = _metadata(identifier, name)
        registry.register(GameRegistration(metadata, lambda metadata=metadata: FakeGame(metadata)))

    assert registry.identifiers() == ("a", "m", "z")
    assert [item.metadata.name for item in registry.all()] == ["Alpha", "Mango", "Zed"]


def test_registration_exposes_metadata_helpers() -> None:
    metadata = _metadata("snake", "Snake")
    registration = GameRegistration(metadata, lambda: FakeGame(metadata))

    assert registration.identifier == "snake"
    assert registration.modes == (GameMode.SINGLE_PLAYER,)
