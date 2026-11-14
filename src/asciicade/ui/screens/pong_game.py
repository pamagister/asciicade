"""Pong gameplay screen."""

from __future__ import annotations

import math
import time
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
from asciicade.core.input import (
    Direction,
    InputAction,
    InputEvent,
    direction_for_action,
    input_map_for_mode,
)
from asciicade.core.options import GameOptions
from asciicade.core.player import GuestPlayer, PlayerProfile, player_color
from asciicade.core.registry import GameRegistration
from asciicade.games.pong import PongGame, PongSnapshot
from asciicade.persistence import LastSession
from asciicade.ui.context import AppContext
from asciicade.ui.keyboard import release_reporting_available
from asciicade.ui.navigation import go_to_game_menu, go_to_main_menu
from asciicade.ui.screens.game_over import GameOverScreen
from asciicade.ui.screens.leave_game import LeaveGameScreen

_DIRECTION_ACTIONS = {
    InputAction.UP,
    InputAction.DOWN,
    InputAction.LEFT,
    InputAction.RIGHT,
}

# With Kitty release events enabled, the direction is cleared immediately.
# This timeout is a fallback for terminals without release reporting.
_PADDLE_REPEAT_TICKS = 2
_HOLD_DELAY = 0.1
_KEY_HOLD_TIMEOUT = 0.3


class PongGameScreen(Screen[None]):
    """Render and drive a Pong session."""

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
        self._game: PongGame | None = None
        self._input_map = input_map_for_mode(mode)
        self._timer: Timer | None = None
        self._paused = False
        self._finished = False
        self._held_directions: dict[int, Direction] = {}
        self._hold_started_at: dict[int, float] = {}
        self._last_key_at: dict[int, float] = {}
        self._tick_count = 0

    def compose(self) -> ComposeResult:
        """Build the arena view."""
        yield Vertical(
            Static("", id="arena"),
            classes="game-screen",
        )

    def on_mount(self) -> None:
        """Start the game and the tick timer."""
        self._game = cast(PongGame, self._registration.factory())
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
        self._clear_held_paddles()
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def on_key(self, event: events.Key) -> None:
        """Feed direction keys into the engine and handle pause actions."""
        if self._game is None or self._finished:
            return
        if event.key.endswith("_release"):
            release_event = self._input_map.resolve(event.key.removesuffix("_release"))
            if (
                release_event is not None
                and release_event.action in _DIRECTION_ACTIONS
                and release_event.player is not None
            ):
                event.stop()
                event.prevent_default()
                release_direction = direction_for_action(release_event.action)
                if (
                    release_direction is not None
                    and self._held_directions.get(release_event.player) == release_direction
                ):
                    self._held_directions.pop(release_event.player, None)
                    self._hold_started_at.pop(release_event.player, None)
                    self._last_key_at.pop(release_event.player, None)
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
                direction = direction_for_action(input_event.action)
                if direction is not None and input_event.player is not None:
                    now = time.monotonic()
                    previous = self._held_directions.get(input_event.player)
                    if previous != direction:
                        self._held_directions[input_event.player] = direction
                        self._hold_started_at[input_event.player] = now
                        self._game.handle_input(input_event)
                        self._update_display()
                    # Repeated press events keep the no-release fallback alive.
                    self._last_key_at[input_event.player] = now

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
        """Discard buffered input requests and held paddle directions."""
        self._clear_held_paddles()
        if self._game is not None:
            self._game.clear_pending()

    def _clear_held_paddles(self) -> None:
        """Stop continuous paddle movement."""
        self._held_directions.clear()
        self._hold_started_at.clear()
        self._last_key_at.clear()

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
        self._tick_count += 1
        if self._tick_count % _PADDLE_REPEAT_TICKS == 0:
            self._move_held_paddles()
        self._game.tick()
        self._update_display()
        if self._game.is_finished:
            self._finish()

    def _move_held_paddles(self) -> None:
        """Move paddles whose direction key has been held long enough."""
        if self._game is None:
            return
        now = time.monotonic()
        release_supported = release_reporting_available()
        for player, direction in tuple(self._held_directions.items()):
            if not release_supported:
                last_key_at = self._last_key_at.get(player)
                if last_key_at is None or now - last_key_at > _KEY_HOLD_TIMEOUT:
                    self._held_directions.pop(player, None)
                    self._hold_started_at.pop(player, None)
                    self._last_key_at.pop(player, None)
                    continue
            started_at = self._hold_started_at.get(player)
            if started_at is None or now - started_at < _HOLD_DELAY:
                continue
            action = InputAction.UP if direction is Direction.UP else InputAction.DOWN
            self._game.handle_input(InputEvent(action, player=player))

    def _finish(self) -> None:
        """Persist the result and show the game-over screen."""
        if self._game is None or self._finished:
            return
        self._finished = True
        self._clear_held_paddles()
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
                winner_label=self._winner_label(),
            )
        )
        self._update_display()

    def _winner_label(self) -> str | None:
        """Return the winner name shown on the game-over screen."""
        if self._game is None:
            return None
        winner_index = self._game.snapshot.winner_index
        if winner_index is None:
            return None
        if self._mode is GameMode.SINGLE_PLAYER and winner_index == 1:
            return "CPU"
        return self._players[winner_index].name

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
            f"PONG — {self._mode.value.upper()}\n",
            style="bold yellow",
        )
        self._append_scores(text, snapshot)
        text.append(f"First to {snapshot.score_limit}\n", style="white")

        border = "═" * snapshot.width
        text.append(f"╔{border}╗\n", style="blue")
        for row in range(snapshot.height):
            text.append("║", style="blue")
            text.append_text(self._render_row(snapshot, row))
            text.append("║\n", style="blue")
        text.append(f"╚{border}╝\n", style="blue")

        if self._finished:
            text.append("\nGAME OVER\n", style="bold red")
        elif self._paused:
            text.append(
                "\nPAUSED — Esc/P resume · Enter leave · Q quit\n",
                style="bold yellow",
            )
        elif self._mode is GameMode.SINGLE_PLAYER:
            text.append(
                "\nArrows/WASD move · Esc/P pause · Q quit\n",
                style="white",
            )
        else:
            text.append(
                "\nP1 Arrows · P2 W/S · Esc/P pause · Q quit\n",
                style="white",
            )
        return text

    def _append_scores(self, text: Text, snapshot: PongSnapshot) -> None:
        """Append the scoreboard for the current mode."""
        if self._mode is GameMode.SINGLE_PLAYER:
            human_color = player_color(self._players[0]).value
            text.append(
                f"{self._players[0].name}: {snapshot.players[0].score}",
                style=f"bold {human_color}",
            )
            text.append("    ", style="")
            text.append(f"CPU: {snapshot.players[1].score}", style="bold red")
        else:
            first_color = player_color(self._players[0]).value
            second_color = player_color(self._players[1]).value
            text.append(
                f"{self._players[0].name}: {snapshot.players[0].score}",
                style=f"bold {first_color}",
            )
            text.append("    ", style="")
            text.append(
                f"{self._players[1].name}: {snapshot.players[1].score}",
                style=f"bold {second_color}",
            )
        text.append("\n", style="")

    def _render_row(self, snapshot: PongSnapshot, row: int) -> Text:
        """Render one terminal row as two independently colored half-cells."""
        occupancy: dict[tuple[int, int], str] = {}
        center = snapshot.width // 2
        for subrow in (row * 2, row * 2 + 1):
            if subrow % 2 == 0:
                occupancy[(center, subrow)] = "white"

        for player in snapshot.players:
            color = self._player_color(player.player_index)
            x = 1 if player.player_index == 1 else snapshot.width - 2
            top = player.y - player.height / 2
            bottom = player.y + player.height / 2
            for subrow in range(snapshot.height * 2):
                if top <= subrow + 0.5 < bottom:
                    occupancy[(x, subrow)] = color

        ball_x = max(0, min(snapshot.width - 1, math.floor(snapshot.ball.x)))
        for subrow in {
            math.floor(snapshot.ball.y - 0.5),
            math.floor(snapshot.ball.y + 0.5),
        }:
            if 0 <= subrow < snapshot.height * 2:
                occupancy[(ball_x, subrow)] = "white"

        text = Text()
        for x in range(snapshot.width):
            upper = occupancy.get((x, row * 2))
            lower = occupancy.get((x, row * 2 + 1))
            if upper is not None and lower is not None:
                if upper == lower:
                    text.append("█", style=upper)
                else:
                    text.append("▀", style=f"{upper} on {lower}")
            elif upper is not None:
                text.append("▀", style=upper)
            elif lower is not None:
                text.append("▄", style=lower)
            else:
                text.append(" ")
        return text

    def _player_color(self, player_index: int) -> str:
        """Return the display color for a player or the CPU."""
        if 1 <= player_index <= len(self._players):
            return player_color(self._players[player_index - 1]).value
        return "red"
