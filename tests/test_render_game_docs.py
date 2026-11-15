"""Tests for the generated game documentation renderer."""

from __future__ import annotations

from pathlib import Path

import pytest

import scripts.render_game_docs as renderer
from asciicade.core.game import GameDocs, GameMetadata, GameMode
from asciicade.core.options import (
    BooleanOptionDefinition,
    ChoiceOptionDefinition,
    GameOptionRegistry,
)
from asciicade.core.registry import GameRegistration


def _metadata(
    identifier: str = "demo",
    modes: tuple[GameMode, ...] = (GameMode.SINGLE_PLAYER,),
    docs: GameDocs | None = None,
    options: GameOptionRegistry | None = None,
) -> GameMetadata:
    """Return metadata for a test game."""
    return GameMetadata(
        identifier=identifier,
        name=identifier.title(),
        description="A demo game.",
        modes=modes,
        docs=docs
        or GameDocs(
            summary="Demo summary.",
            long_description="Long demo description.",
            single_player="- Do the single-player thing.",
            controls_short="Press Escape to pause.",
        ),
        options=options,
    )


def _registration(metadata: GameMetadata) -> GameRegistration:
    """Wrap metadata in a registration with a dummy factory."""
    return GameRegistration(metadata, lambda: object())  # type: ignore[arg-type,return-value]


def test_render_page_contains_sections_in_order() -> None:
    registration = _registration(
        _metadata(
            docs=GameDocs(
                summary="s",
                long_description="Long description.",
                single_player="- SP bullet.",
                multiplayer="- MP bullet.",
                controls_short="Esc pauses.",
                controls_long="Esc pauses. See the controls page.",
                sections=(("Scoring", "Points are fun."),),
            ),
            modes=(GameMode.SINGLE_PLAYER, GameMode.MULTIPLAYER),
        )
    )
    page = renderer.render_page(registration)
    assert page.startswith("# Demo\n\nLong description.")
    assert "## Single player" in page
    assert "## Two players" in page
    assert "## Scoring" in page
    assert page.index("## Single player") < page.index("## Two players")
    assert page.index("## Two players") < page.index("## Scoring")
    assert page.endswith("See the controls page.\n")


def test_render_page_omits_multiplayer_section_for_single_player_game() -> None:
    registration = _registration(_metadata())
    page = renderer.render_page(registration)
    assert "## Two players" not in page


def test_render_page_renders_options_table_from_registry() -> None:
    registry = GameOptionRegistry(
        definitions=(
            ChoiceOptionDefinition(
                key="difficulty",
                label="Difficulty",
                values=("Easy", "Hard"),
                default="Easy",
            ),
            BooleanOptionDefinition(key="wrap", label="Wrap walls", default=True),
        )
    )
    registration = _registration(
        _metadata(
            docs=GameDocs(
                summary="s",
                long_description="d",
                single_player="sp",
                controls_short="c",
                sections=(("Options", "{options}"),),
            ),
            options=registry,
        )
    )
    page = renderer.render_page(registration)
    assert "| Option | Values | Default |" in page
    assert "| Difficulty | Easy, Hard | Easy |" in page
    assert "| Wrap walls | On / Off | On |" in page


def test_render_page_is_deterministic() -> None:
    registration = _registration(_metadata())
    assert renderer.render_page(registration) == renderer.render_page(registration)


def test_render_page_wraps_long_bullets() -> None:
    registration = _registration(
        _metadata(
            docs=GameDocs(
                summary="s",
                long_description="d",
                single_player="- " + "word " * 40,
                controls_short="c",
            )
        )
    )
    page = renderer.render_page(registration)
    assert all(len(line) <= 100 for line in page.splitlines())


def test_sync_index_replaces_marked_block() -> None:
    index = "Intro\n\n<!-- games:start -->\nold list\n<!-- games:end -->\n\nOutro"
    registrations = (
        _registration(_metadata("alpha")),
        _registration(_metadata("beta")),
    )
    updated = renderer.sync_index(index, registrations)
    assert "old list" not in updated
    assert "[Alpha](games/alpha.md)" in updated
    assert "[Beta](games/beta.md)" in updated
    assert updated.index("[Alpha]") < updated.index("[Beta]")
    assert updated.startswith("Intro")
    assert updated.endswith("Outro")


def test_sync_index_requires_markers() -> None:
    with pytest.raises(ValueError, match="games:start"):
        renderer.sync_index("no markers", ())


def test_main_check_mode_detects_stale_output(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    games_dir = tmp_path / "docs" / "games"
    games_dir.mkdir(parents=True)
    index_file = tmp_path / "docs" / "index.md"
    index_file.write_text("<!-- games:start -->\n<!-- games:end -->\n", encoding="utf-8")
    monkeypatch.setattr(renderer, "GAMES_DIR", games_dir)
    monkeypatch.setattr(renderer, "INDEX_FILE", index_file)

    assert renderer.main([]) == 0
    pages = list(games_dir.glob("*.md"))
    assert pages, "expected at least one generated game page"
    for page in pages:
        assert page.read_text(encoding="utf-8").startswith("# ")

    pages[0].write_text("stale", encoding="utf-8")
    assert renderer.main(["--check"]) == 1
