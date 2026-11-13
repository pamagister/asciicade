"""Tests for the Textual user interface."""

from __future__ import annotations

import asyncio
from pathlib import Path

from textual.widgets import DataTable, Input, OptionList, Static

from asciicade.core.game import GameMode
from asciicade.core.input import Direction
from asciicade.core.player import GuestPlayer
from asciicade.core.results import MatchOutcome, make_game_result, make_player_result
from asciicade.games.snake import Position
from asciicade.persistence import Database, PlayerRepository, ResultRepository
from asciicade.ui.app import AsciicadeApp
from asciicade.ui.screens.confirm_quit import ConfirmQuitScreen
from asciicade.ui.screens.create_player import CreatePlayerScreen
from asciicade.ui.screens.game_over import GameOverScreen
from asciicade.ui.screens.game_select import GameSelectScreen
from asciicade.ui.screens.instructions import InstructionsScreen
from asciicade.ui.screens.leaderboard import LeaderboardScreen
from asciicade.ui.screens.main_menu import MainMenuScreen
from asciicade.ui.screens.match_history import MatchHistoryScreen
from asciicade.ui.screens.mode_select import ModeSelectScreen
from asciicade.ui.screens.player_select import PlayerSelectScreen
from asciicade.ui.screens.snake_game import SnakeGameScreen


def make_app(tmp_path: Path) -> AsciicadeApp:
    """Create an application backed by a temporary database."""
    database = Database(tmp_path / "ui.db")
    database.initialize()
    return AsciicadeApp(
        database=database,
        players=PlayerRepository(database),
        results=ResultRepository(database),
    )


def test_main_menu_lists_entries(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            assert isinstance(app.screen, MainMenuScreen)
            prompts = [str(option.prompt) for option in app.screen.query_one(OptionList).options]
            assert prompts == [
                "Play",
                "High Scores",
                "Match History",
                "Instructions",
                "Quit",
            ]

    asyncio.run(scenario())


def test_play_navigates_to_snake_game(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, GameSelectScreen)

            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, ModeSelectScreen)

            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, PlayerSelectScreen)

            # Single player is highlighted first; choose the guest option.
            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()
            # The list refreshes with Start game; move to it and start.
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()

            assert isinstance(app.screen, SnakeGameScreen)

    asyncio.run(scenario())


def test_global_back_returns_to_main_menu(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, GameSelectScreen)

            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(app.screen, MainMenuScreen)

    asyncio.run(scenario())


def test_snake_screen_renders_and_handles_input(tmp_path: Path) -> None:
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

            assert "SNAKE" in str(screen.render_arena())

            await pilot.press("up")
            await pilot.pause()
            screen._on_tick()
            assert screen._game.snapshot.snakes[0].direction is Direction.UP
            assert screen._game.snapshot.snakes[0].body[0] == Position(7, 6)

            await pilot.press("escape")
            await pilot.pause()
            assert screen._paused
            screen._on_tick()
            assert screen._game.snapshot.snakes[0].body[0] == Position(7, 6)

    asyncio.run(scenario())


def test_snake_screen_supports_two_players(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("snake")
            app.push_screen(
                SnakeGameScreen(
                    app.context,
                    registration,
                    GameMode.MULTIPLAYER,
                    (GuestPlayer(1), GuestPlayer(2)),
                )
            )
            await pilot.pause()
            screen = app.screen
            assert isinstance(screen, SnakeGameScreen)
            screen._timer.stop()

            text = str(screen.render_arena())
            assert "Guest 1" in text
            assert "Guest 2" in text

            await pilot.press("w")
            await pilot.pause()
            screen._on_tick()
            assert screen._game.snapshot.snakes[1].direction is Direction.UP

    asyncio.run(scenario())


def test_arena_cells_are_two_characters_wide(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(120, 30)) as pilot:
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

            rendered = str(screen.render_arena())
            lines = rendered.splitlines()
            border = next(line for line in lines if line.startswith("+"))
            row = next(line for line in lines if line.startswith("|"))

            assert len(border) == screen._game.snapshot.width * 2 + 2
            assert len(row) == screen._game.snapshot.width * 2 + 2
            assert "11" in rendered
            assert "██" in rendered
            assert "**" in rendered

    asyncio.run(scenario())


def test_game_over_records_result_and_restarts(tmp_path: Path) -> None:
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
            screen._game._snakes[0].direction = Direction.RIGHT
            screen._on_tick()
            await pilot.pause()

            assert isinstance(app.screen, GameOverScreen)
            assert len(app.context.results.match_history("snake", mode=None)) == 1

            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, SnakeGameScreen)

    asyncio.run(scenario())


def test_leaderboard_shows_scores(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.context.results.record(
                make_game_result(
                    "snake",
                    GameMode.SINGLE_PLAYER,
                    (make_player_result(GuestPlayer(1), 42, MatchOutcome.LOSS),),
                )
            )
            app.push_screen(LeaderboardScreen(app.context, "snake"))
            await pilot.pause()

            table = app.screen.query_one(DataTable)
            assert table.row_count == 1
            assert "Guest 1" in table.get_row_at(0)
            assert "42" in table.get_row_at(0)

    asyncio.run(scenario())


def test_leaderboard_handles_empty_results(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.push_screen(LeaderboardScreen(app.context, "snake"))
            await pilot.pause()

            table = app.screen.query_one(DataTable)
            assert table.row_count == 1
            assert "No scores yet" in table.get_row_at(0)

    asyncio.run(scenario())


def test_match_history_shows_participants(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.context.results.record(
                make_game_result(
                    "snake",
                    GameMode.MULTIPLAYER,
                    (
                        make_player_result(GuestPlayer(1), 3, MatchOutcome.LOSS),
                        make_player_result(GuestPlayer(2), 8, MatchOutcome.WIN),
                    ),
                    winner_name="Guest 2",
                )
            )
            app.push_screen(MatchHistoryScreen(app.context, "snake"))
            await pilot.pause()

            table = app.screen.query_one(DataTable)
            assert table.row_count == 1
            row = table.get_row_at(0)
            assert "Guest 1" in row
            assert "Guest 2" in row
            assert "Guest 2" in row

    asyncio.run(scenario())


def test_instructions_screen_shows_game_instructions(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("snake")
            app.push_screen(InstructionsScreen(registration))
            await pilot.pause()

            body = app.screen.query_one("#instructions-body", Static)
            assert "Objective" in str(body.content)

    asyncio.run(scenario())


def test_create_player_dialog_creates_profile(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("snake")
            app.push_screen(PlayerSelectScreen(app.context, registration, GameMode.SINGLE_PLAYER))
            await pilot.pause()
            assert isinstance(app.screen, PlayerSelectScreen)

            # The first option is "Create new player".
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, CreatePlayerScreen)

            app.screen.query_one(Input).value = "Paul"
            await pilot.press("enter")
            await pilot.pause()

            assert isinstance(app.screen, PlayerSelectScreen)
            assert [player.name for player in app.screen._selected] == ["Paul"]
            assert [profile.name for profile in app.context.players.list()] == ["Paul"]

    asyncio.run(scenario())


def test_main_menu_high_scores_navigation(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, GameSelectScreen)

            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, LeaderboardScreen)

    asyncio.run(scenario())


def test_main_menu_match_history_navigation(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, GameSelectScreen)

            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, MatchHistoryScreen)

    asyncio.run(scenario())


def test_main_menu_instructions_navigation(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, GameSelectScreen)

            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, InstructionsScreen)

    asyncio.run(scenario())


def test_typing_q_in_player_name_does_not_quit(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            registration = app.context.registry.get("snake")
            app.push_screen(PlayerSelectScreen(app.context, registration, GameMode.SINGLE_PLAYER))
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()
            assert isinstance(app.screen, CreatePlayerScreen)

            await pilot.press("q")
            await pilot.pause()

            assert isinstance(app.screen, CreatePlayerScreen)
            assert app.screen.query_one(Input).value == "q"

    asyncio.run(scenario())


def test_app_renders_at_multiple_terminal_sizes(tmp_path: Path) -> None:
    async def scenario() -> None:
        for size in ((80, 24), (120, 40)):
            app = make_app(tmp_path)
            async with app.run_test(size=size) as pilot:
                await pilot.pause()
                assert isinstance(app.screen, MainMenuScreen)

    asyncio.run(scenario())


def test_confirm_quit_can_be_cancelled(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.push_screen(ConfirmQuitScreen())
            await pilot.pause()
            assert isinstance(app.screen, ConfirmQuitScreen)

            await pilot.press("escape")
            await pilot.pause()
            assert isinstance(app.screen, MainMenuScreen)

    asyncio.run(scenario())
