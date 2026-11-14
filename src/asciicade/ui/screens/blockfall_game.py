"""Blockfall gameplay screen."""

from __future__ import annotations

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
from asciicade.core.input import InputAction, InputEvent, input_map_for_mode
from asciicade.core.options import GameOptions
from asciicade.core.player import GuestPlayer, PlayerProfile, player_color
from asciicade.core.registry import GameRegistration
from asciicade.games.blockfall import (
    ROTATIONS,
    BlockfallGame,
    BlockfallPlayerView,
    BlockfallSnapshot,
    PieceKind,
    Position,
)
from asciicade.persistence import LastSession
from asciicade.ui.context import AppContext
from asciicade.ui.keyboard import release_reporting_available
from asciicade.ui.navigation import go_to_game_menu, go_to_main_menu
from asciicade.ui.screens.game_over import GameOverScreen
from asciicade.ui.screens.leave_game import LeaveGameScreen

# Terminal cells are roughly twice as tall as they are wide. Rendering each
# logical cell as two horizontal block characters keeps the board square.
_CELL_WIDTH = 2
_BLOCK = "█" * _CELL_WIDTH
_GHOST = "░" * _CELL_WIDTH
_EMPTY = " " * _CELL_WIDTH

_PIECE_COLORS: dict[PieceKind, str] = {
    PieceKind.I: "cyan",
    PieceKind.O: "yellow",
    PieceKind.T: "magenta",
    PieceKind.S: "green",
    PieceKind.Z: "red",
    PieceKind.J: "blue",
    PieceKind.L: "white",
}

_SOFT_DROP_HOLD_DELAY = 0.08
_SOFT_DROP_REPEAT_INTERVAL = 0.04
_KEY_HOLD_TIMEOUT = 0.3

_SINGLE_PLAYER_FOOTER = "Arrows/WASD move · Space/AltGr rotate · Down soft drop · Esc/P pause"
_TWO_PLAYER_FOOTER = "P1 Arrows+Space/AltGr · P2 WASD+Ctrl/Shift · Esc/P pause"


class BlockfallGameScreen(Screen[None]):
    """Render and drive a Blockfall session."""

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
        self._game: BlockfallGame | None = None
        self._input_map = input_map_for_mode(mode)
        self._timer: Timer | None = None
        self._paused = False
        self._finished = False
        self._held_soft_drop: dict[int, float] = {}
        self._last_soft_drop_at: dict[int, float] = {}
        self._last_key_at: dict[int, float] = {}

    def compose(self) -> ComposeResult:
        """Build the board view."""
        yield Vertical(
            Static("", id="arena"),
            classes="game-screen",
        )

    def on_mount(self) -> None:
        """Start the game and the tick timer."""
        self._game = cast(BlockfallGame, self._registration.factory())
        self._game.start(self._mode, self._players, options=self._options)
        profile_ids = tuple(
            player.id for player in self._players if isinstance(player, PlayerProfile)
        )
        self._app_context.settings.save_last_session(
            LastSession(self._registration.identifier, self._mode, profile_ids)
        )
        self._app_context.players.mark_played(profile_ids)
        self._timer = self.set_interval(1.0 / self._game.tick_rate, self._on_tick)
        self._update_display()
        self.focus()

    def on_unmount(self) -> None:
        """Stop the timer when the screen closes."""
        self._clear_soft_drop()
        if self._timer is not None:
            self._timer.stop()
            self._timer = None

    def on_key(self, event: events.Key) -> None:
        """Feed movement and rotation keys into the engine."""
        if self._game is None or self._finished:
            return
        if event.key.endswith("_release"):
            release_event = self._input_map.resolve(event.key.removesuffix("_release"))
            if release_event is not None and release_event.action is InputAction.DOWN:
                if release_event.player is not None:
                    self._stop_soft_drop(release_event.player)
                event.stop()
                event.prevent_default()
            return
        if self._paused and event.key == "enter":
            event.stop()
            event.prevent_default()
            self._open_leave_dialog()
            return
        input_event = self._input_map.resolve(event.key)
        if input_event is None:
            return
        if input_event.action not in {
            InputAction.LEFT,
            InputAction.RIGHT,
            InputAction.DOWN,
            InputAction.ACTION_A,
            InputAction.ACTION_B,
        }:
            return

        event.stop()
        event.prevent_default()
        if self._paused or input_event.player is None:
            return

        if input_event.action is InputAction.DOWN:
            now = time.monotonic()
            if input_event.player not in self._held_soft_drop:
                self._held_soft_drop[input_event.player] = now
                self._last_soft_drop_at[input_event.player] = now
                self._last_key_at[input_event.player] = now
                self._game.handle_input(input_event)
                self._update_display()
            else:
                # The repeat timer drives continuous soft drop. Repeated press
                # events only keep the no-release fallback alive.
                self._last_key_at[input_event.player] = now
            return

        self._game.handle_input(input_event)
        self._update_display()

    def action_toggle_pause(self) -> None:
        """Pause or resume the game."""
        if self._game is None:
            return
        if self._finished:
            self._open_leave_dialog()
            return
        self._paused = not self._paused
        self._clear_input_state()
        self._update_display()
        self.notify("Paused" if self._paused else "Resumed")

    def _clear_input_state(self) -> None:
        """Discard held soft-drop state and buffered input."""
        self._clear_soft_drop()
        if self._game is not None:
            self._game.clear_pending()

    def _clear_soft_drop(self) -> None:
        """Stop continuous soft drop for every player."""
        self._held_soft_drop.clear()
        self._last_soft_drop_at.clear()
        self._last_key_at.clear()

    def _stop_soft_drop(self, player: int) -> None:
        """Stop continuous soft drop for one player."""
        self._held_soft_drop.pop(player, None)
        self._last_soft_drop_at.pop(player, None)
        self._last_key_at.pop(player, None)

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
        self._clear_input_state()
        self._update_display()
        self.notify("Resumed")

    def _on_tick(self) -> None:
        """Advance the engine and refresh the display."""
        if self._game is None or self._paused or self._finished:
            return
        self._process_soft_drop()
        self._game.tick()
        self._update_display()
        if self._game.is_finished:
            self._finish()

    def _process_soft_drop(self) -> None:
        """Apply held soft-drop repeats."""
        if self._game is None or not self._held_soft_drop:
            return
        now = time.monotonic()
        release_supported = release_reporting_available()
        for player in tuple(self._held_soft_drop):
            if not release_supported:
                last_key_at = self._last_key_at.get(player)
                if last_key_at is None or now - last_key_at > _KEY_HOLD_TIMEOUT:
                    self._stop_soft_drop(player)
                    continue
            started_at = self._held_soft_drop[player]
            if now - started_at < _SOFT_DROP_HOLD_DELAY:
                continue
            last_at = self._last_soft_drop_at.get(player, started_at)
            if now - last_at < _SOFT_DROP_REPEAT_INTERVAL:
                continue
            self._last_soft_drop_at[player] = now
            self._game.handle_input(InputEvent(InputAction.DOWN, player=player))

    def _finish(self) -> None:
        """Persist the result and show the game-over screen."""
        if self._game is None or self._finished:
            return
        self._finished = True
        self._clear_soft_drop()
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
        title = "TWO PLAYERS" if self._mode is GameMode.MULTIPLAYER else "SINGLE-PLAYER"
        text.append(f"BLOCKFALL — {title}\n", style="bold yellow")

        middle = self._render_middle(snapshot)
        text.append_text(middle)
        text.append("\n")
        text.append(self._footer(), style=self._footer_style())
        return text

    def _render_middle(self, snapshot: BlockfallSnapshot) -> Text:
        """Render the player boards and information columns."""
        players = snapshot.players
        if self._mode is GameMode.SINGLE_PLAYER:
            view = players[0]
            board = self._board_lines(view)
            info = self._single_player_info_lines(view)
            return self._combine_columns([(22, board), (18, info)], gap=2)

        second = players[1]
        first = players[0]
        left_info = self._two_player_info_lines(second)
        left_board = self._board_lines(second)
        right_board = self._board_lines(first)
        right_info = self._two_player_info_lines(first)
        return self._combine_columns(
            [
                (12, left_info),
                (22, left_board),
                (22, right_board),
                (12, right_info),
            ],
            gap=2,
        )

    def _board_lines(self, view: BlockfallPlayerView) -> list[Text]:
        """Build the bordered board lines for one player."""
        # Each logical cell renders as two horizontal block characters, so the
        # visible row width is 2 * width plus both side borders. The top and
        # bottom borders must match this width.
        border = "═" * (view.board.width * 2)
        lines = [Text(f"╔{border}╗", style="blue")]
        occupancy = self._occupancy(view)
        for y in range(view.board.height):
            row = Text()
            row.append("║", style="blue")
            for x in range(view.board.width):
                character, style = occupancy.get(Position(x, y), (_EMPTY, ""))
                row.append(character, style=style)
            row.append("║", style="blue")
            lines.append(row)
        lines.append(Text(f"╚{border}╝", style="blue"))
        return lines

    def _occupancy(self, view: BlockfallPlayerView) -> dict[Position, tuple[str, str]]:
        """Return the rendered character and style for each occupied cell."""
        cells: dict[Position, tuple[str, str]] = {}
        for y in range(view.board.height):
            for x in range(view.board.width):
                kind = view.board.cell_at(x, y)
                if kind is not None:
                    cells[Position(x, y)] = (_BLOCK, _PIECE_COLORS[kind])

        if view.active is not None and view.ghost:
            ghost_style = f"dim {_PIECE_COLORS[view.active.kind]}"
            for position in view.ghost:
                if position not in cells:
                    cells[position] = (_GHOST, ghost_style)

        if view.active is not None:
            active_style = f"bold {_PIECE_COLORS[view.active.kind]}"
            for position in view.active.cells:
                cells[position] = (_BLOCK, active_style)

        for y in view.flash_rows:
            for x in range(view.board.width):
                cells[Position(x, y)] = (_BLOCK, "bold white")
        return cells

    def _single_player_info_lines(self, view: BlockfallPlayerView) -> list[Text]:
        """Build the information column for single-player mode."""
        lines = self._player_info_lines(view, width=18, control="ARROWS / WASD")
        lines.append(Text())
        lines.append(Text("SCORING (x level)", style="bold white"))
        lines.append(Text("1 line   100", style="white"))
        lines.append(Text("2 lines  300", style="white"))
        lines.append(Text("3 lines  500", style="white"))
        lines.append(Text("4 lines  800", style="white"))
        return lines

    def _two_player_info_lines(self, view: BlockfallPlayerView) -> list[Text]:
        """Build the information column for two-player mode."""
        control = "ARROWS" if view.player_index == 1 else "WASD"
        return self._player_info_lines(view, width=12, control=control)

    def _player_info_lines(
        self,
        view: BlockfallPlayerView,
        *,
        width: int,
        control: str,
    ) -> list[Text]:
        """Build the shared player information lines."""
        player = self._players[view.player_index - 1]
        color = player_color(player).value
        lines = [
            Text(f"P{view.player_index}", style=f"bold {color}"),
            Text(player.name[:width], style=f"bold {color}"),
            Text(control, style="white"),
            Text(f"Score {view.score}", style="white"),
            Text(f"Lines {view.lines}", style="white"),
            Text(f"Level {view.level}", style="white"),
            Text(),
        ]
        if self._game is not None and self._game.config.next_preview:
            lines.extend(self._next_lines(view.next_kind))
        return lines

    def _next_lines(self, kind: PieceKind | None) -> list[Text]:
        """Build a compact two-row next-piece preview."""
        lines = [Text("Next", style="white")]
        if kind is None:
            lines.append(Text("—", style="white"))
            lines.append(Text())
            return lines

        grid = [[" "] * 4 for _ in range(2)]
        for cell in ROTATIONS[kind][0]:
            x = cell.x
            y = cell.y - 1 if kind is PieceKind.I else cell.y
            if 0 <= x < 4 and 0 <= y < 2:
                grid[y][x] = _BLOCK
        style = f"bold {_PIECE_COLORS[kind]}"
        for row in grid:
            lines.append(Text("".join(row), style=style))
        return lines

    def _combine_columns(self, columns: list[tuple[int, list[Text]]], *, gap: int) -> Text:
        """Combine fixed-width columns into one text block."""
        height = max(len(lines) for _, lines in columns)
        result = Text()
        for row in range(height):
            if row:
                result.append("\n")
            for index, (width, lines) in enumerate(columns):
                if index:
                    result.append(" " * gap)
                if row < len(lines):
                    line = lines[row]
                    result.append_text(line)
                    padding = width - len(line.plain)
                    if padding > 0:
                        result.append(" " * padding)
                else:
                    result.append(" " * width)
        return result

    def _footer(self) -> str:
        """Return the footer hint for the current state."""
        if self._finished:
            return "GAME OVER"
        if self._paused:
            return "PAUSED — Esc/P resume · Enter leave · Q quit"
        if self._mode is GameMode.SINGLE_PLAYER:
            return _SINGLE_PLAYER_FOOTER
        return _TWO_PLAYER_FOOTER

    def _footer_style(self) -> str:
        """Return the footer style for the current state."""
        if self._finished:
            return "bold red"
        if self._paused:
            return "bold yellow"
        return "white"
