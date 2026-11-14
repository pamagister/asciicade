"""Tests for the Pong gameplay screen."""

from __future__ import annotations

import asyncio
import time
from pathlib import Path

import pytest
from textual import events
from textual.pilot import Pilot
from textual.widgets import OptionList

from asciicade.core.game import GameMode
from asciicade.core.options import GameOptions
from asciicade.core.player import GuestPlayer, PlayerColor
from asciicade.core.registry import GameRegistration
from asciicade.games.pong import Ball, PongGame
from asciicade.persistence import (
    Database,
    PlayerRepository,
    ResultRepository,
    SettingsRepository,
)
from asciicade.ui.app import AsciicadeApp
from asciicade.ui.keyboard import (
    ReleaseXTermParser,
    release_reporting_available,
    reset_release_reporting,
)
from asciicade.ui.screens.game_menu import GameMenuScreen
from asciicade.ui.screens.game_over import GameOverScreen
from asciicade.ui.screens.leave_game import LeaveGameScreen
from asciicade.ui.screens.pong_game import PongGameScreen
from asciicade.ui.widgets import ActionButton


@pytest.fixture(autouse=True)
def _skip_expensive_display_update(monkeypatch) -> None:
    """Keep gameplay-state tests fast; rendering tests call render_arena directly."""
    monkeypatch.setattr(PongGameScreen, "_update_display", lambda self: None)


def make_app(tmp_path: Path) -> AsciicadeApp:
    """Create an application backed by a temporary database."""
    database = Database(tmp_path / "pong-ui.db")
    database.initialize()
    return AsciicadeApp(
        database=database,
        players=PlayerRepository(database),
        results=ResultRepository(database),
        settings=SettingsRepository(database),
    )


def make_registration() -> GameRegistration:
    """Return a registration for Pong without changing the default registry."""
    return GameRegistration(PongGame.metadata, PongGame)


async def push_pong(
    app: AsciicadeApp,
    pilot: Pilot,
    *,
    mode: GameMode = GameMode.SINGLE_PLAYER,
    players: tuple[GuestPlayer, ...] | None = None,
    options: GameOptions | None = None,
) -> PongGameScreen:
    """Push a Pong screen and return it after it has mounted."""
    app.push_screen(
        PongGameScreen(
            app.context,
            make_registration(),
            mode,
            players or (GuestPlayer(1),),
            options=options,
        )
    )
    await pilot.pause()
    screen = app.screen
    assert isinstance(screen, PongGameScreen)
    return screen


def test_pong_screen_renders_field_scores_and_half_blocks(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            screen = await push_pong(app, pilot)
            screen._timer.stop()

            rendered = str(screen.render_arena())
            lines = rendered.splitlines()

            assert "PONG — SINGLE-PLAYER" in rendered
            assert "Guest 1: 0" in rendered
            assert "CPU: 0" in rendered
            assert "First to 11" in rendered
            assert "╔" in rendered
            assert "╚" in rendered
            assert "║" in rendered
            assert any(character in rendered for character in ("▀", "▄", "█"))
            assert max(len(line) for line in lines) <= 80

    asyncio.run(scenario())


def test_pong_screen_uses_player_color(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            profile = app.context.players.create("Paul", color=PlayerColor.RED)
            app.push_screen(
                PongGameScreen(
                    app.context,
                    make_registration(),
                    GameMode.SINGLE_PLAYER,
                    (profile,),
                )
            )
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, PongGameScreen)
            screen._timer.stop()

            rendered = screen.render_arena()
            styles = {str(span.style) for span in rendered.spans}
            assert any("red" in style for style in styles)

    asyncio.run(scenario())


def test_pong_single_player_uses_arrow_and_wasd_controls(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = await push_pong(app, pilot)
            screen._timer.stop()

            await pilot.press("up")
            assert screen._game.snapshot.players[0].y == 15
            await pilot.press("s")
            assert screen._game.snapshot.players[0].y == 16

    asyncio.run(scenario())


def test_pong_two_player_controls_are_separate(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = await push_pong(
                app,
                pilot,
                mode=GameMode.MULTIPLAYER,
                players=(GuestPlayer(1), GuestPlayer(2)),
            )
            screen._timer.stop()

            await pilot.press("up")
            await pilot.press("w")

            assert screen._game.snapshot.players[0].y == 15
            assert screen._game.snapshot.players[1].y == 15

    asyncio.run(scenario())


def test_pong_pause_resume_and_leave_dialog(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = await push_pong(app, pilot)
            screen._timer.stop()
            screen._game._serve_countdown = 5
            before = screen._game.snapshot.serve_countdown

            await pilot.press("escape")
            assert screen._paused
            screen._on_tick()
            assert screen._game.snapshot.serve_countdown == before

            await pilot.press("escape")
            assert not screen._paused
            screen._on_tick()
            assert screen._game.snapshot.serve_countdown == before - 1

            await pilot.press("escape")
            await pilot.press("enter")
            assert isinstance(app.screen, LeaveGameScreen)

    asyncio.run(scenario())


def test_pong_game_over_records_result_and_replays(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = await push_pong(
                app,
                pilot,
                options=GameOptions((("score_limit", "1"), ("difficulty", "Normal"))),
            )
            screen._timer.stop()
            screen._game._ball = Ball(57, 16, 0.5, 0, 0.5)
            screen._game._serve_countdown = 0

            screen._on_tick()
            await pilot.pause()

            assert isinstance(app.screen, GameOverScreen)
            assert len(app.context.results.match_history("pong", mode=None)) == 1
            assert "Winner: Guest 1" in app.screen._summary()

            app.screen.query_one("#play-again", ActionButton).press()
            for _ in range(10):
                await pilot.pause()
                if isinstance(app.screen, PongGameScreen):
                    break
            assert isinstance(app.screen, PongGameScreen)

    asyncio.run(scenario())


def test_pong_cpu_win_is_labelled_on_game_over(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = await push_pong(
                app,
                pilot,
                options=GameOptions((("score_limit", "1"), ("difficulty", "Normal"))),
            )
            screen._timer.stop()
            screen._game._ball = Ball(-1, 16, -0.5, 0, 0.5)
            screen._game._serve_countdown = 0

            screen._on_tick()
            await pilot.pause()

            assert isinstance(app.screen, GameOverScreen)
            assert "Winner: CPU" in app.screen._summary()

    asyncio.run(scenario())


def test_game_menu_starts_pong_with_selected_options(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("pong")
            app.push_screen(
                GameMenuScreen(
                    app.context,
                    registration,
                    GameMode.SINGLE_PLAYER,
                    (GuestPlayer(1),),
                )
            )
            await pilot.pause()

            option_list = app.screen.query_one(OptionList)
            option_list.highlighted = 3
            option_list.focus()
            await pilot.pause()
            await pilot.press("right")
            assert app.screen._options.value_for("score_limit") == "15"

            option_list.highlighted = 0
            option_list.focus()
            await pilot.pause()
            await pilot.press("enter")

            assert isinstance(app.screen, PongGameScreen)
            screen = app.screen
            screen._timer.stop()
            assert screen._game.config.score_limit == 15

    asyncio.run(scenario())


def test_pong_key_release_stops_paddle_immediately(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = await push_pong(app, pilot)
            screen._timer.stop()
            screen._game._serve_countdown = 0

            await pilot.press("up")
            assert screen._game.snapshot.players[0].y == 15
            assert 1 in screen._held_directions

            screen.on_key(events.Key("up_release", None))
            assert 1 not in screen._held_directions

            for _ in range(2):
                screen._on_tick()
            assert screen._game.snapshot.players[0].y == 15

    asyncio.run(scenario())


def test_release_parser_emits_release_key_events() -> None:
    parser = ReleaseXTermParser(False)

    assert [event.key for event in parser.feed("\x1b[1;1:3A")] == ["up_release"]
    assert [event.key for event in parser.feed("\x1b[119;1:3u")] == ["w_release"]
    assert [event.key for event in parser.feed("\x1b[1;1:1A")] == ["up"]
    assert [event.key for event in parser.feed("\x1b[119;1:1u")] == ["w"]
    assert [event.key for event in parser.feed("\x1b[1;1A")] == ["up"]


def test_release_parser_detects_terminal_capability() -> None:
    reset_release_reporting()
    try:
        parser = ReleaseXTermParser(False)
        list(parser.feed("\x1b[?3u"))
        assert release_reporting_available()

        reset_release_reporting()
        parser = ReleaseXTermParser(False)
        list(parser.feed("\x1b[1;1:3A"))
        assert release_reporting_available()
    finally:
        reset_release_reporting()


def test_pong_tap_moves_one_half_block_without_hold_delay(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = await push_pong(app, pilot)
            screen._timer.stop()
            screen._game._serve_countdown = 0

            await pilot.press("up")
            assert screen._game.snapshot.players[0].y == 15

            # Keep the hold timer inside its delay window so the test is deterministic.
            screen._hold_started_at[1] = time.monotonic()
            screen._on_tick()
            screen._on_tick()
            assert screen._game.snapshot.players[0].y == 15

            screen.on_key(events.Key("up_release", None))
            screen._on_tick()
            assert screen._game.snapshot.players[0].y == 15

    asyncio.run(scenario())


def test_pong_hold_starts_after_delay_and_moves_continuously(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "asciicade.ui.screens.pong_game.release_reporting_available",
        lambda: True,
    )

    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = await push_pong(app, pilot)
            screen._timer.stop()
            screen._game._serve_countdown = 0

            await pilot.press("up")
            assert screen._game.snapshot.players[0].y == 15

            screen._hold_started_at[1] -= 0.2
            for _ in range(4):
                screen._on_tick()

            assert screen._game.snapshot.players[0].y == 13

    asyncio.run(scenario())


def test_pong_paddle_movement_stops_after_key_hold_timeout(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setattr(
        "asciicade.ui.screens.pong_game.release_reporting_available",
        lambda: False,
    )

    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = await push_pong(app, pilot)
            screen._timer.stop()
            screen._game._serve_countdown = 0

            await pilot.press("up")
            assert screen._game.snapshot.players[0].y == 15

            screen._last_key_at[1] = time.monotonic() - 1
            for _ in range(2):
                screen._on_tick()

            assert screen._game.snapshot.players[0].y == 15

    asyncio.run(scenario())


def test_pong_pause_clears_held_paddle_direction(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            screen = await push_pong(app, pilot)
            screen._timer.stop()
            screen._game._serve_countdown = 0

            await pilot.press("up")
            assert screen._game.snapshot.players[0].y == 15

            await pilot.press("escape")
            await pilot.press("escape")
            for _ in range(2):
                screen._on_tick()

            assert screen._game.snapshot.players[0].y == 15

    asyncio.run(scenario())
