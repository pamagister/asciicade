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
from asciicade.ui.context import AppContext
from asciicade.ui.screens.game_over import GameOverScreen

_DIRECTION_ACTIONS = {
    InputAction.UP,
    InputAction.DOWN,
    InputAction.LEFT,
    InputAction.RIGHT,
}

# Terminal cells are roughly twice as tall as they are wide. Rendering each
# logical cell as two horizontal characters keeps the playfield visually square.
_CELL_WIDTH = 2


class SnakeGameScreen(Screen[None]):
    """Render and drive a Snake session."""

    BINDINGS = [Binding("escape", "toggle_pause", "Pause", show=True)]

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
        """Feed direction keys into the engine."""
        if self._game is None or self._finished:
            return
        input_event = self._input_map.resolve(event.key)
        if input_event is None:
            return
        if input_event.action in _DIRECTION_ACTIONS:
            self._game.handle_input(input_event)
            event.stop()
            event.prevent_default()

    def action_toggle_pause(self) -> None:
        """Pause or resume the game."""
        if self._game is None or self._finished:
            return
        self._paused = not self._paused
        self._update_display()
        self.notify("Paused" if self._paused else "Resumed")

    def _on_tick(self) -> None:
        """Advance the engine and refresh the display."""
        if self._game is None or self._paused or self._finished:
            return
        self._game.tick()
        self._update_display()
        if self._game.is_finished:
            self._finish()

    def _finish(self) -> None:
        """Persist the result and show the game-over screen."""
        if self._game is None or self._finished:
            return
        self._finished = True
        if self._timer is not None:
            self._timer.stop()
            self._timer = None
        result = self._game.result
        if result is not None:
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
        for player, snake in zip(self._players, snapshot.snakes):
            color = player_color(player).value
            for index, position in enumerate(snake.body):
                style = f"bold {color}" if index == 0 else color
                cells[position] = ("█" * _CELL_WIDTH, style)
        if snapshot.food is not None:
            cells[snapshot.food] = ("*" * _CELL_WIDTH, "bold yellow")

        wall = "█" * _CELL_WIDTH
        border = wall * (snapshot.width + 2)
        text.append(f"{border}\n", style="bright_black")
        for y in range(snapshot.height):
            text.append(wall, style="bright_black")
            for x in range(snapshot.width):
                char, style = cells.get(Position(x, y), (" " * _CELL_WIDTH, ""))
                text.append(char, style=style)
            text.append(f"{wall}\n", style="bright_black")
        text.append(f"{border}\n", style="bright_black")

        if self._paused:
            text.append("\nPAUSED — Escape to resume\n", style="bold yellow")
        if self._finished:
            text.append("\nGAME OVER\n", style="bold red")
        return text
