"""Deterministic Blockfall game engine."""

from __future__ import annotations

import random
from collections.abc import Sequence

from asciicade.core.game import GameMode
from asciicade.core.input import InputAction, InputEvent
from asciicade.core.options import GameOptions
from asciicade.core.player import Player
from asciicade.core.results import (
    GameResult,
    MatchOutcome,
    make_game_result,
    make_player_result,
)
from asciicade.games.blockfall.models import (
    BOX_SIZES,
    ActivePiece,
    ActivePieceView,
    BlockfallConfig,
    BlockfallPlayerView,
    BlockfallSnapshot,
    Board,
    BoardView,
    PlayerState,
    Position,
)
from asciicade.games.blockfall.rules import (
    WALL_KICKS,
    can_place,
    clear_full_rows,
    ghost_position,
    line_clear_score,
    shuffled_bag,
)


class BlockfallEngine:
    """A UI-independent, deterministic falling-block engine."""

    def __init__(
        self,
        config: BlockfallConfig | None = None,
        rng: random.Random | None = None,
    ) -> None:
        """Create an engine.

        Args:
            config: Board and speed configuration. Defaults to
                :class:`BlockfallConfig`.
            rng: Injectable random generator. Defaults to a new generator.
        """
        self.config = config or BlockfallConfig()
        self._rng = rng or random.Random()
        self._players: tuple[Player, ...] = ()
        self._mode = GameMode.SINGLE_PLAYER
        self._states: list[PlayerState] = []
        self._finished = False
        self._winner_index: int | None = None
        self._is_draw = False

    @property
    def tick_rate(self) -> float:
        """Return the number of simulation ticks per second."""
        return self.config.tick_rate

    @property
    def is_finished(self) -> bool:
        """Return whether the current session has ended."""
        return self._finished

    @property
    def snapshot(self) -> BlockfallSnapshot:
        """Return an immutable snapshot suitable for rendering."""
        players = tuple(self._player_view(state) for state in self._states)
        return BlockfallSnapshot(
            width=self.config.width,
            height=self.config.height,
            players=players,
            finished=self._finished,
            winner_index=self._winner_index,
            is_draw=self._is_draw,
        )

    @property
    def result(self) -> GameResult | None:
        """Return the structured result once the session has ended."""
        if not self._finished or not self._players:
            return None

        if self._mode is GameMode.SINGLE_PLAYER:
            state = self._states[0]
            player_result = make_player_result(
                self._players[0],
                state.score,
                MatchOutcome.LOSS,
            )
            return make_game_result("blockfall", self._mode, (player_result,))

        if self._is_draw:
            player_results = tuple(
                make_player_result(player, state.score, MatchOutcome.DRAW)
                for player, state in zip(self._players, self._states, strict=True)
            )
            return make_game_result(
                "blockfall",
                self._mode,
                player_results,
                is_draw=True,
            )

        assert self._winner_index is not None
        player_results = tuple(
            make_player_result(
                player,
                state.score,
                MatchOutcome.WIN if index == self._winner_index else MatchOutcome.LOSS,
            )
            for index, (player, state) in enumerate(zip(self._players, self._states, strict=True))
        )
        return make_game_result(
            "blockfall",
            self._mode,
            player_results,
            winner_name=self._players[self._winner_index].name,
        )

    def start(
        self,
        mode: GameMode,
        players: Sequence[Player],
        *,
        options: GameOptions | None = None,
    ) -> None:
        """Initialize a new session.

        Args:
            mode: The game mode.
            players: One player for single-player, two for multiplayer.
            options: Optional resolved game options. Defaults to the game's
                declared option defaults.

        Raises:
            ValueError: If the mode or player count is invalid.
        """
        expected_players = 1 if mode is GameMode.SINGLE_PLAYER else 2
        if mode not in (GameMode.SINGLE_PLAYER, GameMode.MULTIPLAYER):
            raise ValueError(f"Unsupported Blockfall mode: {mode}")
        if len(players) != expected_players:
            raise ValueError(f"{mode.value} Blockfall requires {expected_players} player(s).")

        self.config = BlockfallConfig.for_options(options, base=self.config)
        self._mode = mode
        self._players = tuple(players)
        self._states = [self._create_state(index + 1) for index in range(expected_players)]
        self._finished = False
        self._winner_index = None
        self._is_draw = False

        for state in self._states:
            self._refill_queue(state)
            self._spawn(state)
        self._resolve_end_condition()

    def handle_input(self, event: InputEvent) -> None:
        """Apply a normalized input event to one player's active piece."""
        if self._finished or event.player is None:
            return
        index = event.player - 1
        if not 0 <= index < len(self._states):
            return
        state = self._states[index]
        if not state.alive or state.active is None:
            return

        if event.action is InputAction.LEFT:
            self._move(state, -1, 0)
        elif event.action is InputAction.RIGHT:
            self._move(state, 1, 0)
        elif event.action is InputAction.DOWN:
            self._soft_drop(state)
        elif event.action is InputAction.ACTION_A:
            self._rotate(state, 1 if event.player == 1 else -1)
        elif event.action is InputAction.ACTION_B:
            self._rotate(state, -1 if event.player == 1 else 1)

    def clear_pending(self) -> None:
        """No-op for API compatibility with buffered-input games."""
        return

    def tick(self) -> None:
        """Advance the game by one deterministic tick."""
        if self._finished or not self._states:
            return

        for state in self._states:
            if not state.alive:
                continue
            self._tick_flash(state)
            if state.active is None:
                continue

            state.gravity_counter += 1
            if state.gravity_counter >= self.config.gravity_interval(state.level):
                state.gravity_counter = 0
                if not self._move_down(state):
                    if state.lock_delay is None:
                        state.lock_delay = self.config.lock_delay_ticks

            if state.lock_delay is not None:
                state.lock_delay -= 1
                if state.lock_delay <= 0:
                    self._lock_piece(state)

        self._resolve_end_condition()

    def _create_state(self, player_index: int) -> PlayerState:
        """Create the initial mutable state for one player."""
        return PlayerState(
            player_index=player_index,
            board=Board(self.config.width, self.config.height),
            level=self.config.start_level,
        )

    def _player_view(self, state: PlayerState) -> BlockfallPlayerView:
        """Build an immutable view of one player's state."""
        active_view: ActivePieceView | None = None
        ghost: tuple[Position, ...] = ()
        if state.active is not None:
            active_view = ActivePieceView(state.active.kind, state.active.cells())
            if self.config.ghost_piece:
                ghost_y = ghost_position(state.board, state.active)
                ghost_piece = ActivePiece(
                    state.active.kind,
                    state.active.rotation,
                    state.active.x,
                    ghost_y,
                )
                ghost = ghost_piece.cells()

        return BlockfallPlayerView(
            player_index=state.player_index,
            board=BoardView(
                self.config.width,
                self.config.height,
                tuple(state.board.cells),
            ),
            active=active_view,
            ghost=ghost,
            next_kind=state.queue[0] if state.queue else None,
            score=state.score,
            lines=state.lines,
            level=state.level,
            alive=state.alive,
            flash_rows=state.flash_rows if state.flash_ticks > 0 else (),
        )

    def _refill_queue(self, state: PlayerState) -> None:
        """Refill a player's preview queue from the seven-bag randomizer."""
        while len(state.queue) < self.config.queue_size:
            if not state.bag:
                state.bag = shuffled_bag(self._rng)
            state.queue.append(state.bag.pop())

    def _spawn(self, state: PlayerState) -> None:
        """Spawn the next piece, or top out when it cannot enter."""
        if not state.queue:
            self._refill_queue(state)
        kind = state.queue.pop(0)
        self._refill_queue(state)

        size = BOX_SIZES[kind]
        x = (self.config.width - size) // 2
        piece = ActivePiece(kind, 0, x, 0)
        if not can_place(state.board, piece.kind, piece.rotation, piece.x, piece.y):
            state.active = None
            state.alive = False
            return

        state.active = piece
        state.gravity_counter = 0
        state.lock_delay = None

    def _move(self, state: PlayerState, delta_x: int, delta_y: int) -> bool:
        """Try to move the active piece and return whether it moved."""
        piece = state.active
        if piece is None:
            return False
        if not can_place(
            state.board,
            piece.kind,
            piece.rotation,
            piece.x + delta_x,
            piece.y + delta_y,
        ):
            return False
        piece.x += delta_x
        piece.y += delta_y
        if delta_y > 0:
            state.gravity_counter = 0
        self._reset_lock_delay(state)
        return True

    def _move_down(self, state: PlayerState) -> bool:
        """Move the active piece down one row for gravity."""
        piece = state.active
        if piece is None:
            return False
        if not can_place(state.board, piece.kind, piece.rotation, piece.x, piece.y + 1):
            return False
        piece.y += 1
        state.gravity_counter = 0
        state.lock_delay = None
        return True

    def _soft_drop(self, state: PlayerState) -> bool:
        """Move the active piece down one row for a manual soft drop."""
        piece = state.active
        if piece is None:
            return False
        if not can_place(state.board, piece.kind, piece.rotation, piece.x, piece.y + 1):
            self._lock_piece(state)
            return False
        piece.y += 1
        state.score += 1
        state.gravity_counter = 0
        state.lock_delay = None
        return True

    def _rotate(self, state: PlayerState, direction: int) -> bool:
        """Rotate the active piece, trying wall kicks when necessary."""
        piece = state.active
        if piece is None:
            return False
        rotation = (piece.rotation + direction) % 4
        for delta_x, delta_y in WALL_KICKS:
            if can_place(
                state.board,
                piece.kind,
                rotation,
                piece.x + delta_x,
                piece.y + delta_y,
            ):
                piece.rotation = rotation
                piece.x += delta_x
                piece.y += delta_y
                self._reset_lock_delay(state)
                return True
        return False

    def _reset_lock_delay(self, state: PlayerState) -> None:
        """Restart the lock delay after a successful adjustment."""
        if state.lock_delay is not None:
            state.lock_delay = self.config.lock_delay_ticks

    def _tick_flash(self, state: PlayerState) -> None:
        """Age the line-clear flash effect."""
        if state.flash_ticks <= 0:
            return
        state.flash_ticks -= 1
        if state.flash_ticks == 0:
            state.flash_rows = ()

    def _lock_piece(self, state: PlayerState) -> None:
        """Lock the active piece, clear lines and spawn the next piece."""
        piece = state.active
        if piece is None:
            return

        for cell in piece.cells():
            if state.board.is_inside(cell.x, cell.y):
                state.board.set_cell(cell.x, cell.y, piece.kind)
            else:
                state.alive = False

        state.active = None
        state.lock_delay = None
        state.gravity_counter = 0

        if not state.alive:
            return

        cleared = clear_full_rows(state.board)
        if cleared:
            state.lines += len(cleared)
            state.score += line_clear_score(len(cleared), state.level)
            state.level = self.config.start_level + state.lines // self.config.lines_per_level
            state.flash_rows = cleared
            state.flash_ticks = self.config.flash_ticks

        self._spawn(state)

    def _resolve_end_condition(self) -> None:
        """Finish the session according to the current mode."""
        if self._finished:
            return

        if self._mode is GameMode.SINGLE_PLAYER:
            if not self._states[0].alive:
                self._finish(winner_index=None, is_draw=False)
            return

        alive = [index for index, state in enumerate(self._states) if state.alive]
        if not alive:
            self._finish(winner_index=None, is_draw=True)
        elif len(alive) == 1:
            self._finish(winner_index=alive[0], is_draw=False)

    def _finish(self, *, winner_index: int | None, is_draw: bool) -> None:
        """Mark the session as finished."""
        self._finished = True
        self._winner_index = winner_index
        self._is_draw = is_draw
