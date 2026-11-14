"""Tests for the Textual user interface."""

from __future__ import annotations

import asyncio
from pathlib import Path

import pytest
from textual.widgets import DataTable, Input, OptionList, Static

from asciicade.core.game import GameMode
from asciicade.core.input import Direction
from asciicade.core.player import GuestPlayer, PlayerColor
from asciicade.core.results import MatchOutcome, make_game_result, make_player_result
from asciicade.games.snake import Position
from asciicade.persistence import (
    Database,
    LastSession,
    PlayerRepository,
    ResultRepository,
    SettingsRepository,
)
from asciicade.ui.app import AsciicadeApp
from asciicade.ui.screens.confirm_quit import ConfirmQuitScreen
from asciicade.ui.screens.create_player import CreatePlayerScreen
from asciicade.ui.screens.edit_player_picker import EditPlayerPickerScreen
from asciicade.ui.screens.game_menu import GameMenuScreen
from asciicade.ui.screens.game_over import GameOverScreen
from asciicade.ui.screens.game_select import GameSelectScreen
from asciicade.ui.screens.instructions import InstructionsScreen
from asciicade.ui.screens.leaderboard import LeaderboardScreen
from asciicade.ui.screens.main_menu import MainMenuScreen
from asciicade.ui.screens.match_history import MatchHistoryScreen
from asciicade.ui.screens.player_select import PlayerSelectScreen
from asciicade.ui.screens.snake_game import SnakeGameScreen


@pytest.fixture(autouse=True)
def _skip_expensive_display_update(monkeypatch) -> None:
    """Keep gameplay-state tests fast; rendering is covered where asserted."""
    monkeypatch.setattr(SnakeGameScreen, "_update_display", lambda self: None)


def make_app(tmp_path: Path) -> AsciicadeApp:
    """Create an application backed by a temporary database."""
    database = Database(tmp_path / "ui.db")
    database.initialize()
    return AsciicadeApp(
        database=database,
        players=PlayerRepository(database),
        results=ResultRepository(database),
        settings=SettingsRepository(database),
    )


def make_prepared_app(
    tmp_path: Path,
    *,
    last_mode: GameMode | None = None,
) -> AsciicadeApp:
    """Create an application with an optional stored last session."""
    database = Database(tmp_path / "ui.db")
    database.initialize()
    settings = SettingsRepository(database)
    if last_mode is not None:
        settings.save_last_session(LastSession("snake", last_mode, ()))
    return AsciicadeApp(
        database=database,
        players=PlayerRepository(database),
        results=ResultRepository(database),
        settings=settings,
    )


def test_main_menu_lists_entries(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            assert isinstance(app.screen, MainMenuScreen)
            prompts = [str(option.prompt) for option in app.screen.query_one(OptionList).options]
            assert prompts == [
                "Single Player",
                "Two Players",
                "High Scores",
                "Match History",
                "Instructions",
                "Quit",
            ]

    asyncio.run(scenario())


def test_main_menu_preselects_last_mode(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_prepared_app(tmp_path, last_mode=GameMode.MULTIPLAYER)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            assert app.screen.query_one(OptionList).highlighted == 1

    asyncio.run(scenario())


def test_play_navigates_to_snake_game(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            assert isinstance(app.screen, PlayerSelectScreen)

            # No profiles exist, so the guest option is highlighted and starts immediately.
            await pilot.press("enter")
            assert isinstance(app.screen, GameSelectScreen)

            # Blockfall and Pong sort before Snake; move down twice to select Snake.
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")
            assert isinstance(app.screen, GameMenuScreen)

            # Press Play to start the game.
            await pilot.press("enter")

            assert isinstance(app.screen, SnakeGameScreen)

    asyncio.run(scenario())


def test_global_back_returns_to_main_menu(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("enter")
            assert isinstance(app.screen, PlayerSelectScreen)

            await pilot.press("escape")
            assert isinstance(app.screen, MainMenuScreen)

    asyncio.run(scenario())


def test_right_confirms_and_left_goes_back(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("right")
            assert isinstance(app.screen, PlayerSelectScreen)

            await pilot.press("left")
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
            head_before = screen._game.snapshot.snakes[0].body[0]
            screen._on_tick()
            assert screen._game.snapshot.snakes[0].direction is Direction.UP
            assert screen._game.snapshot.snakes[0].body[0] == head_before.step(Direction.UP)

            await pilot.press("escape")
            assert screen._paused
            head_paused = screen._game.snapshot.snakes[0].body[0]
            screen._on_tick()
            assert screen._game.snapshot.snakes[0].body[0] == head_paused

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
            assert "11" not in text
            assert "22" not in text
            assert "▓" not in text

            await pilot.press("w")
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
            border = next(line for line in lines if line.startswith("█") and set(line) == {"█"})
            row = next(line for line in lines if line.startswith("█") and set(line) != {"█"})

            assert len(border) == screen._game.snapshot.width * 2 + 4
            assert len(row) == screen._game.snapshot.width * 2 + 4
            assert set(border) == {"█"}
            assert row.startswith("██")
            assert row.endswith("██")
            assert "11" not in rendered
            assert "22" not in rendered
            assert "██" in rendered
            assert "◖◗" in rendered

    asyncio.run(scenario())


def test_snake_uses_player_color(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            profile = app.context.players.create("Paul", color=PlayerColor.RED)
            app.push_screen(PlayerSelectScreen(app.context, GameMode.SINGLE_PLAYER))
            await pilot.pause()
            assert isinstance(app.screen, PlayerSelectScreen)
            assert app.screen.query_one(OptionList).highlighted == 3

            await pilot.press("enter")
            assert isinstance(app.screen, GameSelectScreen)

            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")
            assert isinstance(app.screen, GameMenuScreen)

            await pilot.press("enter")
            assert isinstance(app.screen, SnakeGameScreen)
            screen = app.screen
            screen._timer.stop()

            rendered = screen.render_arena()
            styles = {str(span.style) for span in rendered.spans}
            assert any("red" in style for style in styles)
            assert screen._players[0].id == profile.id

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


def test_player_list_orders_and_preselects_profiles(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            paul = app.context.players.create("Paul")
            ada = app.context.players.create("Ada")
            app.context.players.mark_played([ada.id])
            app.push_screen(PlayerSelectScreen(app.context, GameMode.SINGLE_PLAYER))
            await pilot.pause()
            option_list = app.screen.query_one(OptionList)
            prompts = [str(option.prompt) for option in option_list.options]
            assert prompts == ["Play as guest", "New player", "Edit player", "Ada", "Paul"]
            assert option_list.highlighted == 3
            assert app.screen._selected == []
            assert paul.name == "Paul"

    asyncio.run(scenario())


def test_create_player_dialog_creates_profile_and_starts(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.push_screen(PlayerSelectScreen(app.context, GameMode.SINGLE_PLAYER))
            await pilot.pause()

            await pilot.press("down")
            await pilot.press("enter")
            assert isinstance(app.screen, CreatePlayerScreen)

            app.screen.query_one(Input).value = "Paul"
            app.screen._color = PlayerColor.BLUE
            await pilot.press("enter")
            assert isinstance(app.screen, GameSelectScreen)

            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")
            assert isinstance(app.screen, GameMenuScreen)

            await pilot.press("enter")
            assert isinstance(app.screen, SnakeGameScreen)
            profiles = app.context.players.list()
            assert [profile.name for profile in profiles] == ["Paul"]
            assert profiles[0].color is PlayerColor.BLUE
            assert app.context.settings.get_last_session() is not None

    asyncio.run(scenario())


def test_edit_profile_changes_name_and_color(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.context.players.create("Paul")
            app.push_screen(PlayerSelectScreen(app.context, GameMode.SINGLE_PLAYER))
            await pilot.pause()

            await pilot.press("e")
            assert isinstance(app.screen, CreatePlayerScreen)

            app.screen.query_one(Input).value = "Paula"
            app.screen._color = PlayerColor.MAGENTA
            await pilot.press("enter")

            assert isinstance(app.screen, PlayerSelectScreen)
            profiles = app.context.players.list()
            assert [profile.name for profile in profiles] == ["Paula"]
            assert profiles[0].color is PlayerColor.MAGENTA

    asyncio.run(scenario())


def test_edit_player_menu_option(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.context.players.create("Paul")
            app.push_screen(PlayerSelectScreen(app.context, GameMode.SINGLE_PLAYER))
            await pilot.pause()

            # Default highlight is the profile; move up to Edit player.
            await pilot.press("up")
            await pilot.press("enter")
            assert isinstance(app.screen, EditPlayerPickerScreen)

            await pilot.press("enter")
            assert isinstance(app.screen, CreatePlayerScreen)

    asyncio.run(scenario())


def test_two_player_flow_selects_two_profiles(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            paul = app.context.players.create("Paul")
            ada = app.context.players.create("Ada")
            app.push_screen(PlayerSelectScreen(app.context, GameMode.MULTIPLAYER))
            await pilot.pause()

            # Newest profile is first; select Ada, then Paul.
            await pilot.press("enter")
            assert isinstance(app.screen, PlayerSelectScreen)
            assert [player.name for player in app.screen._selected] == ["Ada"]

            await pilot.press("enter")
            assert isinstance(app.screen, GameSelectScreen)

            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")
            assert isinstance(app.screen, GameMenuScreen)

            await pilot.press("enter")
            assert isinstance(app.screen, SnakeGameScreen)
            assert {player.id for player in app.screen._players} == {paul.id, ada.id}
            session = app.context.settings.get_last_session()
            assert session is not None
            assert session.mode is GameMode.MULTIPLAYER
            assert set(session.player_ids) == {paul.id, ada.id}

    asyncio.run(scenario())


def test_main_menu_high_scores_navigation(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")
            assert isinstance(app.screen, GameSelectScreen)

            await pilot.press("enter")
            assert isinstance(app.screen, LeaderboardScreen)

    asyncio.run(scenario())


def test_main_menu_match_history_navigation(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("down")
            await pilot.press("enter")
            assert isinstance(app.screen, GameSelectScreen)

            await pilot.press("enter")
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
            await pilot.press("down")
            await pilot.press("enter")
            assert isinstance(app.screen, GameSelectScreen)

            await pilot.press("enter")
            assert isinstance(app.screen, InstructionsScreen)

    asyncio.run(scenario())


def test_typing_q_in_player_name_does_not_quit(tmp_path: Path) -> None:
    async def scenario() -> None:
        app = make_app(tmp_path)
        async with app.run_test(size=(100, 30)) as pilot:
            await pilot.pause()
            app.push_screen(PlayerSelectScreen(app.context, GameMode.SINGLE_PLAYER))
            await pilot.pause()
            await pilot.press("down")
            await pilot.press("enter")
            assert isinstance(app.screen, CreatePlayerScreen)

            await pilot.press("q")

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
            assert isinstance(app.screen, MainMenuScreen)

    asyncio.run(scenario())


def test_game_menu_lists_play_instructions_and_options(tmp_path: Path) -> None:
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
            assert isinstance(app.screen, GameMenuScreen)
            option_list = app.screen.query_one(OptionList)
            prompts = [str(option.prompt) for option in option_list.options]
            assert prompts == [
                "Play",
                "Instructions",
                "--- Options ---",
                "Difficulty: Medium",
                "Wrap walls: Off",
                "Food per player: On",
            ]
            assert option_list.highlighted == 0

            # The separator is disabled and skipped while navigating.
            separator = option_list.options[2]
            assert separator.id == "options-separator"
            assert separator.disabled

            await pilot.press("down")
            assert option_list.highlighted == 1  # Instructions

            await pilot.press("down")
            assert option_list.highlighted == 3  # Difficulty (separator skipped)

            await pilot.press("down")
            assert option_list.highlighted == 4  # Wrap walls

            await pilot.press("down")
            assert option_list.highlighted == 5  # Food per player

            await pilot.press("down")
            assert option_list.highlighted == 0  # Wraps to Play


def test_game_menu_space_toggles_boolean_option(tmp_path: Path) -> None:
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
            option_list = app.screen.query_one(OptionList)

            # Move to Wrap walls (index 4) and toggle it on with Space.
            option_list.highlighted = 4
            option_list.focus()
            await pilot.pause()
            await pilot.press("space")

            # The cursor stays on the edited option instead of jumping back to Play.
            assert option_list.highlighted == 4
            prompts = [str(option.prompt) for option in option_list.options]
            assert "Wrap walls: On" in prompts
            assert app.screen._options.value_for("wrap_walls") == "on"

            # Toggle it off again.
            await pilot.press("space")
            prompts = [str(option.prompt) for option in option_list.options]
            assert "Wrap walls: Off" in prompts
            assert app.screen._options.value_for("wrap_walls") == "off"


def test_game_menu_left_right_change_choice_option(tmp_path: Path) -> None:
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
            option_list = app.screen.query_one(OptionList)

            # Move to Difficulty (index 3) and change it with left/right.
            option_list.highlighted = 3
            option_list.focus()
            await pilot.pause()

            await pilot.press("right")
            prompts = [str(option.prompt) for option in option_list.options]
            assert "Difficulty: Hard" in prompts
            assert app.screen._options.value_for("difficulty") == "Hard"

            await pilot.press("left")
            prompts = [str(option.prompt) for option in option_list.options]
            assert "Difficulty: Medium" in prompts
            assert app.screen._options.value_for("difficulty") == "Medium"


def test_game_menu_enter_cycles_option(tmp_path: Path) -> None:
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
            option_list = app.screen.query_one(OptionList)

            option_list.highlighted = 4  # Wrap walls
            option_list.focus()
            await pilot.pause()

            await pilot.press("enter")
            prompts = [str(option.prompt) for option in option_list.options]
            assert "Wrap walls: On" in prompts

            await pilot.press("enter")
            prompts = [str(option.prompt) for option in option_list.options]
            assert "Wrap walls: Off" in prompts


def test_game_menu_play_starts_snake_with_options(tmp_path: Path) -> None:
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
            option_list = app.screen.query_one(OptionList)

            # Change Difficulty to Easy.
            option_list.highlighted = 3
            option_list.focus()
            await pilot.pause()
            await pilot.press("left")
            assert app.screen._options.value_for("difficulty") == "Easy"

            # Press Play.
            option_list.highlighted = 0
            option_list.focus()
            await pilot.pause()
            await pilot.press("enter")

            assert isinstance(app.screen, SnakeGameScreen)
            screen = app.screen
            screen._timer.stop()
            assert screen._game.config.tick_rate == 5.0

    asyncio.run(scenario())
