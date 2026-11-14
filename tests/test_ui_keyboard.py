"""Tests for keyboard navigation and interaction behavior."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from textual.containers import VerticalScroll
from textual.widgets import DataTable, OptionList, Static

from asciicade.core.game import GameMode
from asciicade.core.input import Direction
from asciicade.core.player import GuestPlayer, PlayerColor
from asciicade.games.snake import Position
from asciicade.persistence import (
    Database,
    PlayerRepository,
    ResultRepository,
    SettingsRepository,
)
from asciicade.ui.app import AsciicadeApp
from asciicade.ui.screens.confirm_quit import ConfirmQuitScreen
from asciicade.ui.screens.create_player import CreatePlayerScreen
from asciicade.ui.screens.game_menu import GameMenuScreen
from asciicade.ui.screens.game_select import GameSelectScreen
from asciicade.ui.screens.instructions import InstructionsScreen
from asciicade.ui.screens.leaderboard import LeaderboardScreen
from asciicade.ui.screens.leave_game import LeaveGameScreen
from asciicade.ui.screens.player_select import PlayerSelectScreen
from asciicade.ui.screens.snake_game import SnakeGameScreen
from asciicade.ui.widgets import ActionButton


@pytest.fixture(autouse=True)
def _skip_expensive_display_update(monkeypatch) -> None:
    """Keep gameplay-state tests fast; rendering is covered where asserted."""
    monkeypatch.setattr(SnakeGameScreen, "_update_display", lambda self: None)


def make_app(tmp_path: Path) -> AsciicadeApp:
    """Create an application backed by a temporary database."""
    database = Database(tmp_path / "keyboard.db")
    database.initialize()
    return AsciicadeApp(
        database=database,
        players=PlayerRepository(database),
        results=ResultRepository(database),
        settings=SettingsRepository(database),
    )


def test_menu_space_confirms(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("space")
            assert isinstance(app.screen, PlayerSelectScreen)

    asyncio.run(scenario())


def test_main_menu_three_escape_presses_exit(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("escape")
            footer = str(app.screen.query_one("#menu-footer", Static).content)
            assert "2 more" in footer

            await pilot.press("escape")
            footer = str(app.screen.query_one("#menu-footer", Static).content)
            assert "1 more" in footer

            await pilot.press("escape")
            assert app.return_code == 0
            assert not app.is_running

    asyncio.run(scenario())


def test_main_menu_escape_sequence_timeout_resets(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.screen._ESCAPE_WINDOW = 0.2
            await pilot.press("escape")
            await pilot.pause(0.3)

            footer = str(app.screen.query_one("#menu-footer", Static).content)
            assert "Esc×3 exit" in footer

            await pilot.press("escape")
            footer = str(app.screen.query_one("#menu-footer", Static).content)
            assert "2 more" in footer

    asyncio.run(scenario())


def test_confirm_quit_arrow_focus_and_space_activation(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.push_screen(ConfirmQuitScreen())
            await pilot.pause()

            assert app.focused is not None
            assert app.focused.id == "cancel"

            await pilot.press("right")
            assert app.focused is not None
            assert app.focused.id == "quit"

            await pilot.press("left")
            assert app.focused is not None
            assert app.focused.id == "cancel"

            app.screen.query_one("#quit", ActionButton).focus()
            await pilot.pause()
            await pilot.press("space")
            assert app.return_code == 0

    asyncio.run(scenario())


def test_game_menu_left_on_play_goes_back(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.push_screen(
                GameSelectScreen(
                    app.context,
                    "play",
                    mode=GameMode.SINGLE_PLAYER,
                    players=(GuestPlayer(1),),
                )
            )
            await pilot.pause()

            await pilot.press("enter")
            assert isinstance(app.screen, GameMenuScreen)

            await pilot.press("left")
            assert isinstance(app.screen, GameSelectScreen)

    asyncio.run(scenario())


def test_game_over_arrow_focus_wraps(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("snake")
            app.push_screen(
                SnakeGameScreen(
                    app.context,
                    registration,
                    GameMode.SINGLE_PLAYER,
                    (GuestPlayer(1),),
                )
            )
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, SnakeGameScreen)
            screen._timer.stop()
            screen._game._food = Position(0, 0)
            screen._game._snakes[0].body = (
                Position(29, 7),
                Position(28, 7),
                Position(27, 7),
            )
            screen._on_tick()
            await pilot.pause()

            assert app.focused is not None
            assert app.focused.id == "play-again"

            await pilot.press("right")
            assert app.focused is not None
            assert app.focused.id == "main-menu"

            await pilot.press("right")
            assert app.focused is not None
            assert app.focused.id == "high-scores"

            await pilot.press("right")
            assert app.focused is not None
            assert app.focused.id == "play-again"

    asyncio.run(scenario())


def test_pause_ignores_movement_and_clears_pending(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("snake")
            app.push_screen(
                SnakeGameScreen(
                    app.context,
                    registration,
                    GameMode.SINGLE_PLAYER,
                    (GuestPlayer(1),),
                )
            )
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, SnakeGameScreen)
            screen._timer.stop()

            await pilot.press("escape")
            assert screen._paused
            assert list(screen._game._snakes[0].pending) == []

            await pilot.press("up")
            await pilot.press("left")
            assert list(screen._game._snakes[0].pending) == []

            await pilot.press("escape")
            assert not screen._paused
            screen._on_tick()
            assert screen._game.snapshot.snakes[0].direction is Direction.RIGHT

    asyncio.run(scenario())


def test_pause_enter_opens_leave_dialog_and_stay_resumes(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("snake")
            app.push_screen(
                SnakeGameScreen(
                    app.context,
                    registration,
                    GameMode.SINGLE_PLAYER,
                    (GuestPlayer(1),),
                )
            )
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, SnakeGameScreen)
            screen._timer.stop()

            await pilot.press("escape")
            await pilot.press("enter")

            assert isinstance(app.screen, LeaveGameScreen)
            assert app.focused is not None
            assert app.focused.id == "stay"

            await pilot.press("enter")
            assert isinstance(app.screen, SnakeGameScreen)
            assert not screen._paused

    asyncio.run(scenario())


def test_leave_game_routes_to_game_menu(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("snake")
            app.push_screen(
                GameMenuScreen(
                    app.context,
                    registration,
                    GameMode.SINGLE_PLAYER,
                    (GuestPlayer(1),),
                )
            )
            app.push_screen(
                SnakeGameScreen(
                    app.context,
                    registration,
                    GameMode.SINGLE_PLAYER,
                    (GuestPlayer(1),),
                )
            )
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, SnakeGameScreen)
            screen._timer.stop()

            await pilot.press("escape")
            await pilot.press("enter")
            assert isinstance(app.screen, LeaveGameScreen)

            app.screen.query_one("#game-menu", ActionButton).focus()
            await pilot.pause()
            await pilot.press("space")

            assert isinstance(app.screen, GameMenuScreen)
            assert [type(item).__name__ for item in app.screen_stack] == [
                "Screen",
                "MainMenuScreen",
                "GameMenuScreen",
            ]

    asyncio.run(scenario())


def test_player_select_shows_selected_player_and_undo(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.context.players.create("Paul")
            app.context.players.create("Ada")
            app.push_screen(PlayerSelectScreen(app.context, GameMode.MULTIPLAYER))
            await pilot.pause()

            await pilot.press("enter")
            status = str(app.screen.query_one("#player-selection-status", Static).content)
            assert "Ada" in status
            assert "player 2 of 2" in status
            assert [player.name for player in app.screen._selected] == ["Ada"]

            await pilot.press("backspace")
            assert app.screen._selected == []

    asyncio.run(scenario())


def test_instructions_are_scrollable_at_80x24(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("snake")
            app.push_screen(InstructionsScreen(registration))
            await pilot.pause()

            scroll = app.screen.query_one(VerticalScroll)
            assert scroll.max_scroll_y > 0

            await pilot.press("end")
            assert scroll.scroll_offset.y == scroll.max_scroll_y

            footer = str(app.screen.query_one("#menu-footer", Static).content)
            assert "scroll" in footer

    asyncio.run(scenario())


def test_game_description_and_info_are_visible_at_80_columns(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            app.push_screen(
                GameSelectScreen(
                    app.context,
                    "play",
                    mode=GameMode.SINGLE_PLAYER,
                    players=(GuestPlayer(1),),
                )
            )
            await pilot.pause()

            description = app.screen.query_one("#game-description", Static)
            assert description.region.x < 80
            assert description.region.width > 0
            assert str(description.content)

            await pilot.press("enter")
            assert isinstance(app.screen, GameMenuScreen)

            option_list = app.screen.query_one(OptionList)
            option_list.highlighted = 3
            option_list.focus()
            await pilot.pause()
            info = app.screen.query_one("#game-info-panel", Static)
            assert info.region.x < 80
            assert info.region.width > 0
            assert str(info.content)

    asyncio.run(scenario())


def test_datatable_fits_80_columns(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            app.push_screen(LeaderboardScreen(app.context, "snake"))
            await pilot.pause()

            table = app.screen.query_one(DataTable)
            assert table.region.width <= 80

    asyncio.run(scenario())


def test_q_opens_quit_confirmation_and_escape_cancels(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("snake")
            app.push_screen(
                SnakeGameScreen(
                    app.context,
                    registration,
                    GameMode.SINGLE_PLAYER,
                    (GuestPlayer(1),),
                )
            )
            await pilot.pause()

            await pilot.press("q")
            assert isinstance(app.screen, ConfirmQuitScreen)

            await pilot.press("escape")
            assert isinstance(app.screen, SnakeGameScreen)

    asyncio.run(scenario())


def test_create_player_space_selects_color(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.push_screen(CreatePlayerScreen(app.context.players))
            await pilot.pause()

            color_list = app.screen.query_one("#color-list", OptionList)
            color_list.highlighted = 3
            color_list.focus()
            await pilot.pause()

            await pilot.press("space")
            assert app.screen._color is PlayerColor.YELLOW

    asyncio.run(scenario())


def test_main_menu_wasd_navigation(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            option_list = app.screen.query_one("OptionList")
            assert option_list.highlighted == 0

            await pilot.press("s")
            assert option_list.highlighted == 1

            await pilot.press("w")
            assert option_list.highlighted == 0

    asyncio.run(scenario())


def test_player_select_wasd_navigation(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.push_screen(PlayerSelectScreen(app.context, GameMode.SINGLE_PLAYER))
            await pilot.pause()

            option_list = app.screen.query_one("OptionList")
            first = option_list.highlighted

            await pilot.press("s")
            assert option_list.highlighted != first

            await pilot.press("w")
            assert option_list.highlighted == first

    asyncio.run(scenario())


def test_game_menu_wasd_changes_option(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("snake")
            app.push_screen(
                GameMenuScreen(
                    app.context,
                    registration,
                    GameMode.SINGLE_PLAYER,
                    (GuestPlayer(1),),
                )
            )
            await pilot.pause()

            option_list = app.screen.query_one("OptionList")
            option_list.highlighted = 3  # Difficulty
            option_list.focus()
            await pilot.pause()

            await pilot.press("d")
            assert app.screen._options.value_for("difficulty") == "Hard"

            await pilot.press("a")
            assert app.screen._options.value_for("difficulty") == "Medium"

    asyncio.run(scenario())


def test_dialog_button_focus_wasd(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.push_screen(ConfirmQuitScreen())
            await pilot.pause()

            assert app.focused is not None
            assert app.focused.id == "cancel"

            await pilot.press("d")
            assert app.focused is not None
            assert app.focused.id == "quit"

            await pilot.press("a")
            assert app.focused is not None
            assert app.focused.id == "cancel"

    asyncio.run(scenario())


def test_instructions_wasd_scroll(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("snake")
            app.push_screen(InstructionsScreen(registration))
            await pilot.pause()

            scroll = app.screen.query_one(VerticalScroll)
            start = scroll.scroll_offset.y

            await pilot.press("s")
            assert scroll.scroll_offset.y > start

            await pilot.press("w")
            assert scroll.scroll_offset.y == start

    asyncio.run(scenario())


def test_create_player_wasd_navigates_color_list(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.push_screen(CreatePlayerScreen(app.context.players))
            await pilot.pause()

            color_list = app.screen.query_one("#color-list", OptionList)
            color_list.focus()
            await pilot.pause()

            first = color_list.highlighted

            await pilot.press("s")
            assert color_list.highlighted != first

            await pilot.press("w")
            assert color_list.highlighted == first

    asyncio.run(scenario())
