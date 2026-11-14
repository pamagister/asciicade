"""Snake gameplay screen."""

from __future__ import annotations

from typing import cast

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.timer import Timer
from textual.widgets import Static

from asciicade.core.game import GameMode
from asciicade.core.input import InputAction, input_map_for_mode
from asciicade.core.options import GameOptions
from asciicade.core.player import GuestPlayer, PlayerProfile, player_color
from asciicade.core.registry import GameRegistration
from asciicade.games.snake import Position, SnakeGame
from asciicade.persistence import LastSession
from asciicade.ui.audio import SoundEffect
from asciicade.ui.context import AppContext
from asciicade.ui.navigation import go_to_game_menu, go_to_main_menu
from asciicade.ui.screens.game_over import GameOverScreen
from asciicade.ui.screens.leave_game import LeaveGameScreen

_DIRECTION_ACTIONS = {
    InputAction.UP,
    InputAction.DOWN,
    InputAction.LEFT,
    InputAction.RIGHT,
}

# Terminal cells are roughly twice as tall as they are wide. Rendering each
# logical cell as two horizontal characters keeps the playfield visually square.
_CELL_WIDTH = 2

# A food ball made of the left and right halves of a filled circle.
_FOOD_GLYPH = "◖◗"


class SnakeGameScreen(Screen[None]):
    """Render and drive a Snake session."""

    BINDINGS = [
        Binding("escape", "toggle_pause", "Pause", show=True),
        Binding("p", "toggle_pause", "Pause", show=False),
    ]

    def __init__(
        self,
        context: AppContext,
        registration: GameRegistration,
        mode: GameMode,
        players: tuple[PlayerProfile | GuestPlayer, ...],
        *,
        options: GameOptions | None = None,
    ) -> None:
        """Store the session configuration."""
        super().__init__()
        self._app_context = context
        self._registration = registration
        self._mode = mode
        self._players = players
        self._options = options
        self._game: SnakeGame | None = None
        self._input_map = input_map_for_mode(mode)
        self._timer: Timer | None = None
        self._paused = False
        self._finished = False
        self._last_score = 0

    def compose(self) -> ComposeResult:
        """Build the arena view."""
        yield Vertical(
            Static("", id="arena"),
            classes="game-screen",
        )

    def on_mount(self) -> None:
        """Start the game and the tick timer."""
        self._game = cast(SnakeGame, self._registration.factory())
        self._game.start(self._mode, self._players, options=self._options)
        profile_ids = tuple(
            player.id for player in self._players if isinstance(player, PlayerProfile)
        )
        self._app_context.settings.save_last_session(
            LastSession(self._registration.identifier, self._mode, profile_ids)
        )
        self._app_context.players.mark_played(profile_ids)
        self._timer = self.set_interval(1.0 / self._game.config.tick_rate, self._on_tick)
        self._update_display()
        self.focus()

    def on_unmount(self) -> None:
        """Stop the timer when the screen closes."""
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def on_key(self, event: events.Key) -> None:
        """Feed direction keys into the engine and handle pause actions."""
        if self._game is None or self._finished:
            return
        if self._paused and event.key == "enter":
            event.stop()
            event.prevent_default()
            self._open_leave_dialog()
            return
        input_event = self._input_map.resolve(event.key)
        if input_event is None:
            return
        if input_event.action in _DIRECTION_ACTIONS:
            event.stop()
            event.prevent_default()
            if not self._paused:
                self._game.handle_input(input_event)

    def action_toggle_pause(self) -> None:
        """Pause or resume the game."""
        if self._game is None:
            return
        if self._finished:
            self._open_leave_dialog()
            return
        self._paused = not self._paused
        self._clear_pending()
        self._update_display()
        self.notify("Paused" if self._paused else "Resumed")

    def _clear_pending(self) -> None:
        """Discard buffered direction requests."""
        if self._game is not None:
            self._game.clear_pending()

    def _open_leave_dialog(self) -> None:
        """Ask whether to leave the current game."""
        self.app.push_screen(
            LeaveGameScreen(self._registration.metadata.name, self._mode),
            self._on_leave_choice,
        )

    def _on_leave_choice(self, choice: str | None) -> None:
        """Handle the leave-game dialog result."""
        if choice == "game-menu":
            go_to_game_menu(
                self.app,
                self._app_context,
                self._registration,
                self._mode,
                self._players,
                self._options,
            )
            return
        if choice == "main-menu":
            go_to_main_menu(self.app, self._app_context)
            return
        self._paused = False
        self._clear_pending()
        self._update_display()
        self.notify("Resumed")

    def _on_tick(self) -> None:
        """Advance the engine and refresh the display."""
        if self._game is None or self._paused or self._finished:
            return
        self._game.tick()
        self._play_food_sound()
        self._update_display()
        if self._game.is_finished:
            self._finish()

    def _play_food_sound(self) -> None:
        """Play the collect effect when a snake eats food."""
        if self._game is None:
            return
        score = sum(snake.score for snake in self._game.snapshot.snakes)
        if score > self._last_score:
            self._app_context.audio.play(SoundEffect.FOOD_EATEN)
        self._last_score = score

    def _finish(self) -> None:
        """Persist the result and show the game-over screen."""
        if self._game is None or self._finished:
            return
        self._finished = True
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        result = self._game.result
        if result is None:
            self.notify("The game finished without a result.", severity="error")
            go_to_game_menu(
                self.app,
                self._app_context,
                self._registration,
                self._mode,
                self._players,
                self._options,
            )
            return
        self._app_context.results.record(result)
        self.app.push_screen(
            GameOverScreen(
                self._app_context,
                self._registration,
                self._mode,
                self._players,
                result,
                options=self._options,
            )
        )
        self._update_display()

    def _update_display(self) -> None:
        """Render the current snapshot."""
        if self._game is not None:
            self.query_one("#arena", Static).update(self.render_arena())

    def render_arena(self) -> Text:
        """Build a text rendering of the arena."""
        if self._game is None:
            return Text("Starting...")

        snapshot = self._game.snapshot
        text = Text()
        text.append(
            f"SNAKE — {self._mode.value.upper()}\n",
            style="bold yellow",
        )
        for player, snake in zip(self._players, snapshot.snakes):
            color = player_color(player).value
            text.append(
                f"{player.name}: {snake.score}   ",
                style=f"bold {color}",
            )
        text.append("\n")

        cells: dict[Position, tuple[str, str]] = {}
        for food in snapshot.foods:
            if food.player_index == 0:
                # Shared food is neutral so neither player owns it.
                style = "bold white"
            else:
                player = self._players[food.player_index - 1]
                style = f"bold {player_color(player).value}"
            cells[food.position] = (_FOOD_GLYPH, style)
        for player, snake in zip(self._players, snapshot.snakes):
            color = player_color(player).value
            for index, position in enumerate(snake.body):
                style = f"bold {color}" if index == 0 else color
                cells[position] = ("█" * _CELL_WIDTH, style)

        wall = "█" * _CELL_WIDTH
        border = wall * (snapshot.width + 2)
        text.append(f"{border}\n", style="white")
        for y in range(snapshot.height):
            text.append(wall, style="white")
            for x in range(snapshot.width):
                char, style = cells.get(Position(x, y), (" " * _CELL_WIDTH, ""))
                text.append(char, style=style)
            text.append(f"{wall}\n", style="white")
        text.append(f"{border}\n", style="white")

        if self._paused:
            text.append(
                "\nPAUSED — Esc/P resume · Enter leave · Q quit\n",
                style="bold yellow",
            )
        else:
            text.append(
                "\nArrows/WASD move · Esc/P pause · Q quit\n",
                style="white",
            )
        if self._finished:
            text.append("\nGAME OVER\n", style="bold red")
        return text
