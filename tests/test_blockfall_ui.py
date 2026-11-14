"""Tests for the Blockfall gameplay screen."""

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
from asciicade.games.blockfall import ActivePiece, BlockfallGame, PieceKind
from asciicade.persistence import (
    Database,
    PlayerRepository,
    ResultRepository,
    SettingsRepository,
)
from asciicade.ui.app import AsciicadeApp
from asciicade.ui.screens.blockfall_game import BlockfallGameScreen
from asciicade.ui.screens.game_menu import GameMenuScreen
from asciicade.ui.screens.game_over import GameOverScreen
from asciicade.ui.screens.leave_game import LeaveGameScreen
from asciicade.ui.widgets import ActionButton


@pytest.fixture(autouse=True)
def _skip_expensive_display_update(monkeypatch) -> None:
    """Keep gameplay-state tests fast; rendering tests call render_arena directly."""
    monkeypatch.setattr(BlockfallGameScreen, "_update_display", lambda self: None)


def make_app(tmp_path: Path) -> AsciicadeApp:
    """Create an application backed by a temporary database."""
    database = Database(tmp_path / "blockfall-ui.db")
    database.initialize()
    return AsciicadeApp(
        database=database,
        players=PlayerRepository(database),
        results=ResultRepository(database),
        settings=SettingsRepository(database),
    )


def make_registration() -> GameRegistration:
    """Return a registration for Blockfall without changing the default registry."""
    return GameRegistration(BlockfallGame.metadata, BlockfallGame)


async def push_blockfall(
    app: AsciicadeApp,
    pilot: Pilot,
    *,
    mode: GameMode = GameMode.SINGLE_PLAYER,
    players: tuple[GuestPlayer, ...] | None = None,
    options: GameOptions | None = None,
) -> BlockfallGameScreen:
    """Push a Blockfall screen and return it after it has mounted."""
    app.push_screen(
        BlockfallGameScreen(
            app.context,
            make_registration(),
            mode,
            players or (GuestPlayer(1),),
            options=options,
        )
    )
    await pilot.pause()
    screen = app.screen
    assert isinstance(screen, BlockfallGameScreen)
    return screen


def test_blockfall_screen_renders_board_and_info(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            screen = await push_blockfall(app, pilot)
            screen._timer.stop()

            rendered = screen.render_arena()
            plain = rendered.plain
            lines = plain.splitlines()

            assert "BLOCKFALL — SINGLE-PLAYER" in plain
            assert "Guest 1" in plain
            assert "Score 0" in plain
            assert "Lines 0" in plain
            assert "Level 1" in plain
            assert "╔" in plain
            assert "╚" in plain
            assert "║" in plain
            assert "██" in plain
            assert len(lines) <= 24
            assert max(len(line) for line in lines) <= 80

            border = next(line for line in lines if line.startswith("╔"))
            bottom = next(line for line in lines if line.startswith("╚"))
            row = next(line for line in lines if line.startswith("║"))

            # Border width must match the board row width: each cell renders
            # as two block characters plus both side borders.
            snapshot = screen._game.snapshot
            view = snapshot.players[0]
            board_lines = screen._board_lines(view)
            border = board_lines[0].plain
            bottom = board_lines[-1].plain
            row = board_lines[1].plain

            # Border width must match the board row width: each cell renders
            # as two block characters plus both side borders.
            width_chars = view.board.width * 2
            assert len(border) == len(row)
            assert len(bottom) == len(row)
            assert len(row) == 1 + width_chars + 1

            styles = {str(span.style) for span in rendered.spans}
            assert any(
                color in style
                for style in styles
                for color in ("cyan", "yellow", "magenta", "green", "red", "blue", "white")
            )

    asyncio.run(scenario())


def test_blockfall_screen_uses_player_color(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            profile = app.context.players.create("Paul", color=PlayerColor.RED)
            app.push_screen(
                BlockfallGameScreen(
                    app.context,
                    make_registration(),
                    GameMode.SINGLE_PLAYER,
                    (profile,),
                )
            )
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, BlockfallGameScreen)
            screen._timer.stop()

            rendered = screen.render_arena()
            styles = {str(span.style) for span in rendered.spans}
            assert any("red" in style for style in styles)

    asyncio.run(scenario())


def test_blockfall_two_player_layout_puts_player_two_left(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            screen = await push_blockfall(
                app,
                pilot,
                mode=GameMode.MULTIPLAYER,
                players=(GuestPlayer(1), GuestPlayer(2)),
            )
            screen._timer.stop()

            plain = screen.render_arena().plain
            lines = plain.splitlines()

            assert "BLOCKFALL — TWO PLAYERS" in plain
            assert "Guest 1" in plain
            assert "Guest 2" in plain
            assert plain.count("╔") == 2
            assert plain.count("╚") == 2
            assert plain.index("P2") < plain.index("P1")
            assert plain.index("P2") < plain.index("╔")
            assert plain.rindex("P1") > plain.rindex("╚")

            snapshot = screen._game.snapshot
            width_chars = snapshot.players[0].board.width * 2
            assert len(lines) <= 24
            assert max(len(line) for line in lines) <= 80
            for player_view in snapshot.players:
                board_lines = screen._board_lines(player_view)
                assert len(board_lines[0].plain) == width_chars + 2
                assert len(board_lines[-1].plain) == width_chars + 2
                assert len(board_lines[1].plain) == width_chars + 2

    asyncio.run(scenario())


def test_blockfall_single_player_controls(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            screen = await push_blockfall(app, pilot)
            screen._timer.stop()
            state = screen._game._states[0]
            assert state.active is not None
            start_x = state.active.x
            start_y = state.active.y
            start_rotation = state.active.rotation

            await pilot.press("left")
            assert state.active is not None
            assert state.active.x == start_x - 1

            await pilot.press("right")
            assert state.active is not None
            assert state.active.x == start_x

            await pilot.press("down")
            assert state.active is not None
            assert state.active.y == start_y + 1
            assert state.score == 1

            screen.on_key(events.Key("iso_level3_shift", None))
            assert state.active is not None
            assert state.active.rotation == (start_rotation - 1) % 4

            await pilot.press("space")
            assert state.active is not None
            assert state.active.rotation == start_rotation

    asyncio.run(scenario())


def test_blockfall_two_player_controls_are_separate(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            screen = await push_blockfall(
                app,
                pilot,
                mode=GameMode.MULTIPLAYER,
                players=(GuestPlayer(1), GuestPlayer(2)),
            )
            screen._timer.stop()
            first = screen._game._states[0]
            second = screen._game._states[1]
            assert first.active is not None
            assert second.active is not None
            first_start_x = first.active.x
            second_start_x = second.active.x

            await pilot.press("right")
            await pilot.press("d")
            assert first.active is not None
            assert second.active is not None
            assert first.active.x == first_start_x + 1
            assert second.active.x == second_start_x + 1

            first_start_y = first.active.y
            second_start_y = second.active.y
            await pilot.press("down")
            await pilot.press("s")
            assert first.active is not None
            assert second.active is not None
            assert first.active.y == first_start_y + 1
            assert second.active.y == second_start_y + 1
            assert first.score == 1
            assert second.score == 1

            first_rotation = first.active.rotation
            second_rotation = second.active.rotation
            await pilot.press("space")
            screen.on_key(events.Key("control", None))
            screen.on_key(events.Key("shift", None))
            assert first.active is not None
            assert second.active is not None
            assert first.active.rotation == (first_rotation + 1) % 4
            assert second.active.rotation == second_rotation

    asyncio.run(scenario())


def test_blockfall_soft_drop_hold_repeats_and_release_stops(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            screen = await push_blockfall(app, pilot)
            screen._timer.stop()
            state = screen._game._states[0]
            assert state.active is not None
            start_y = state.active.y

            await pilot.press("down")
            assert state.active is not None
            assert state.active.y == start_y + 1

            now = time.monotonic()
            screen._held_soft_drop[1] = now - 0.2
            screen._last_soft_drop_at[1] = now - 0.2
            screen._last_key_at[1] = now
            screen._on_tick()
            assert state.active is not None
            assert state.active.y == start_y + 2

            screen.on_key(events.Key("down_release", None))
            assert 1 not in screen._held_soft_drop
            screen._on_tick()
            assert state.active is not None
            assert state.active.y == start_y + 2

    asyncio.run(scenario())


def test_blockfall_pause_resume_and_leave_dialog(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            screen = await push_blockfall(app, pilot)
            screen._timer.stop()

            await pilot.press("escape")
            assert screen._paused

            await pilot.press("escape")
            assert not screen._paused

            await pilot.press("escape")
            await pilot.press("enter")
            assert isinstance(app.screen, LeaveGameScreen)

    asyncio.run(scenario())


def test_blockfall_game_over_records_result_and_replays(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            screen = await push_blockfall(app, pilot)
            screen._timer.stop()
            state = screen._game._states[0]
            for x in range(3, 6):
                state.board.set_cell(x, 0, PieceKind.J)
                state.board.set_cell(x, 1, PieceKind.J)
            state.active = None
            state.alive = True
            screen._game._spawn(state)
            screen._game._resolve_end_condition()

            screen._on_tick()
            await pilot.pause()

            assert isinstance(app.screen, GameOverScreen)
            assert len(app.context.results.match_history("blockfall", mode=None)) == 1
            assert "Result: Game over" in app.screen._summary()

            app.screen.query_one("#play-again", ActionButton).press()
            for _ in range(10):
                await pilot.pause()
                if isinstance(app.screen, BlockfallGameScreen):
                    break
            assert isinstance(app.screen, BlockfallGameScreen)

    asyncio.run(scenario())


def test_blockfall_line_clear_flash_is_rendered(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            screen = await push_blockfall(app, pilot)
            screen._timer.stop()
            state = screen._game._states[0]
            for x in range(6):
                state.board.set_cell(x, 19, PieceKind.J)
            state.active = ActivePiece(PieceKind.I, 0, 6, 18)
            state.gravity_counter = 0
            state.lock_delay = None

            screen._game._lock_piece(state)

            assert screen._game.snapshot.players[0].flash_rows == (19,)
            rendered = screen.render_arena()
            styles = {str(span.style) for span in rendered.spans}
            assert "bold white" in styles

            for _ in range(screen._game.config.flash_ticks):
                screen._game.tick()
            assert screen._game.snapshot.players[0].flash_rows == ()

    asyncio.run(scenario())


def test_blockfall_ghost_and_next_preview_can_be_disabled(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            screen = await push_blockfall(
                app,
                pilot,
                options=GameOptions(
                    (
                        ("start_level", "1"),
                        ("next_preview", "off"),
                        ("ghost_piece", "off"),
                    )
                ),
            )
            screen._timer.stop()

            plain = screen.render_arena().plain
            assert "Next" not in plain
            assert screen._game.snapshot.players[0].ghost == ()

    asyncio.run(scenario())


def test_blockfall_game_menu_starts_with_selected_options(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("blockfall")
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
            assert app.screen._options.value_for("start_level") == "3"

            option_list.highlighted = 4
            option_list.focus()
            await pilot.pause()
            await pilot.press("space")
            assert app.screen._options.value_for("next_preview") == "off"

            option_list.highlighted = 5
            option_list.focus()
            await pilot.pause()
            await pilot.press("space")
            assert app.screen._options.value_for("ghost_piece") == "off"

            option_list.highlighted = 0
            option_list.focus()
            await pilot.pause()
            await pilot.press("enter")

            assert isinstance(app.screen, BlockfallGameScreen)
            screen = app.screen
            screen._timer.stop()
            assert screen._game.config.start_level == 3
            assert screen._game.config.next_preview is False
            assert screen._game.config.ghost_piece is False

    asyncio.run(scenario())


def test_blockfall_is_first_in_game_menu_and_starts(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.press("enter")

            await pilot.press("enter")
            assert isinstance(app.screen, GameMenuScreen)

            await pilot.press("enter")
            assert isinstance(app.screen, BlockfallGameScreen)
            app.screen._timer.stop()

    asyncio.run(scenario())
