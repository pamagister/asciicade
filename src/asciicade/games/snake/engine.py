"""Deterministic Snake game engine."""

from __future__ import annotations

import random
from collections.abc import Sequence

from asciicade.core.game import GameMode
from asciicade.core.input import Direction, InputEvent, direction_for_action
from asciicade.core.player import Player
from asciicade.core.results import (
    GameResult,
    MatchOutcome,
    make_game_result,
    make_player_result,
)
from asciicade.games.snake.models import (
    Arena,
    Position,
    Snake,
    SnakeConfig,
    SnakeSnapshot,
    SnakeView,
)
from asciicade.games.snake.rules import (
    collides_with_body,
    initial_body,
    occupied_cells,
    spawn_food,
)


class SnakeEngine:
    """A UI-independent, deterministic Snake engine."""

    def __init__(
        self,
        config: SnakeConfig | None = None,
        rng: random.Random | None = None,
    ) -> None:
        """Create an engine.

        Args:
            config: Arena and speed configuration. Defaults to :class:`SnakeConfig`.
            rng: Injectable random generator. Defaults to a new generator.
        """
        self.config = config or SnakeConfig()
        self._rng = rng or random.Random()
        self._players: tuple[Player, ...] = ()
        self._mode = GameMode.SINGLE_PLAYER
        self._snakes: list[Snake] = []
        self._food: Position | None = None
        self._finished = False
        self._winner_index: int | None = None
        self._is_draw = False

    @property
    def arena(self) -> Arena:
        """Return the configured arena."""
        return Arena(self.config.width, self.config.height)

    @property
    def is_finished(self) -> bool:
        """Return whether the current session has ended."""
        return self._finished

    @property
    def snapshot(self) -> SnakeSnapshot:
        """Return an immutable snapshot suitable for rendering."""
        return SnakeSnapshot(
            width=self.arena.width,
            height=self.arena.height,
            snakes=tuple(
                SnakeView(
                    player_index=snake.player_index,
                    body=snake.body,
                    direction=snake.direction,
                    alive=snake.alive,
                    score=snake.score,
                )
                for snake in self._snakes
            ),
            food=self._food,
            finished=self._finished,
            winner_index=self._winner_index,
            is_draw=self._is_draw,
        )

    @property
    def result(self) -> GameResult | None:
        """Return the structured result once the session has ended."""
        if not self._finished or not self._players:
            return None

        player_results = []
        for index, snake in enumerate(self._snakes):
            if self._mode is GameMode.SINGLE_PLAYER:
                outcome = MatchOutcome.LOSS
            elif self._is_draw:
                outcome = MatchOutcome.DRAW
            elif self._winner_index == index:
                outcome = MatchOutcome.WIN
            else:
                outcome = MatchOutcome.LOSS
            player_results.append(make_player_result(self._players[index], snake.score, outcome))

        winner_name = None
        if self._winner_index is not None:
            winner_name = self._players[self._winner_index].name

        return make_game_result(
            "snake",
            self._mode,
            tuple(player_results),
            winner_name=winner_name,
            is_draw=self._is_draw,
        )

    def start(self, mode: GameMode, players: Sequence[Player]) -> None:
        """Initialize a new session.

        Args:
            mode: The game mode.
            players: One player for single-player, two for multiplayer.

        Raises:
            ValueError: If the mode or player count is invalid.
        """
        expected_players = 1 if mode is GameMode.SINGLE_PLAYER else 2
        if mode not in (GameMode.SINGLE_PLAYER, GameMode.MULTIPLAYER):
            raise ValueError(f"Unsupported Snake mode: {mode}")
        if len(players) != expected_players:
            raise ValueError(f"{mode.value} Snake requires {expected_players} player(s).")

        self._mode = mode
        self._players = tuple(players)
        self._snakes = self._create_snakes()
        self._finished = False
        self._winner_index = None
        self._is_draw = False
        self._food = spawn_food(self.arena, occupied_cells(self._snakes), self._rng)
        if self._food is None:
            self._finish_board_full()

    def handle_input(self, event: InputEvent) -> None:
        """Buffer a direction request for one player.

        Args:
            event: A normalized input event.
        """
        if self._finished or event.player is None:
            return
        direction = direction_for_action(event.action)
        if direction is None:
            return
        index = event.player - 1
        if 0 <= index < len(self._snakes):
            snake = self._snakes[index]
            if snake.alive:
                snake.queue_direction(direction)

    def tick(self) -> None:
        """Advance the game by one deterministic tick."""
        if self._finished or not self._snakes:
            return

        for snake in self._snakes:
            if snake.alive:
                snake.consume_direction()

        new_heads: dict[int, Position] = {}
        growing: dict[int, bool] = {}
        for index, snake in enumerate(self._snakes):
            if not snake.alive:
                continue
            head = snake.head.step(snake.direction)
            new_heads[index] = head
            growing[index] = self._food is not None and head == self._food

        dead: set[int] = set()

        # Walls are resolved first; a dead snake stays on the board as an obstacle.
        for index, head in new_heads.items():
            if not self.arena.contains(head):
                dead.add(index)

        # Two snakes entering the same cell eliminate each other.
        indices = list(new_heads)
        for first_position in range(len(indices)):
            for second_position in range(first_position + 1, len(indices)):
                first = indices[first_position]
                second = indices[second_position]
                if new_heads[first] == new_heads[second]:
                    dead.add(first)
                    dead.add(second)

        # Body collisions are resolved against the surviving board state.
        for index, head in new_heads.items():
            if index in dead:
                continue
            snake = self._snakes[index]
            if collides_with_body(head, snake.body, tail_moves=not growing[index]):
                dead.add(index)
                continue
            for other_index, other in enumerate(self._snakes):
                if other_index == index:
                    continue
                other_tail_moves = other_index not in dead and not growing.get(other_index, False)
                if collides_with_body(head, other.body, tail_moves=other_tail_moves):
                    dead.add(index)
                    break

        ate = False
        for index, snake in enumerate(self._snakes):
            if not snake.alive:
                continue
            if index in dead:
                snake.alive = False
                continue
            head = new_heads[index]
            if growing[index]:
                snake.body = (head, *snake.body)
                snake.score += 1
                ate = True
            else:
                snake.body = (head, *snake.body[:-1])

        if ate:
            self._food = spawn_food(self.arena, occupied_cells(self._snakes), self._rng)
            if self._food is None:
                self._finish_board_full()
                return

        self._resolve_end_condition()

    def _create_snakes(self) -> list[Snake]:
        """Create the initial snakes for the current mode."""
        arena = self.arena
        length = self.config.initial_length

        if self._mode is GameMode.SINGLE_PLAYER:
            head = Position(
                max(length, arena.width // 4),
                max(1, arena.height // 2),
            )
            return [Snake(1, initial_body(head, Direction.RIGHT, length), Direction.RIGHT)]

        first_head = Position(
            max(length, arena.width // 4),
            max(1, arena.height // 3),
        )
        second_head = Position(
            min(arena.width - length, arena.width - 1 - max(length, arena.width // 4)),
            min(arena.height - 2, arena.height - 1 - max(1, arena.height // 3)),
        )
        return [
            Snake(
                1,
                initial_body(first_head, Direction.RIGHT, length),
                Direction.RIGHT,
            ),
            Snake(
                2,
                initial_body(second_head, Direction.LEFT, length),
                Direction.LEFT,
            ),
        ]

    def _resolve_end_condition(self) -> None:
        """Finish the session according to the current mode."""
        if self._mode is GameMode.SINGLE_PLAYER:
            if not self._snakes[0].alive:
                self._finish(winner_index=None, is_draw=False)
            return

        alive = [index for index, snake in enumerate(self._snakes) if snake.alive]
        if len(alive) == 1:
            self._finish(winner_index=alive[0], is_draw=False)
        elif not alive:
            self._finish(winner_index=None, is_draw=True)

    def _finish_board_full(self) -> None:
        """Finish the session when no free cell remains for food."""
        if self._mode is GameMode.SINGLE_PLAYER:
            self._finish(winner_index=None, is_draw=False)
        else:
            self._finish(winner_index=None, is_draw=True)

    def _finish(self, *, winner_index: int | None, is_draw: bool) -> None:
        """Mark the session as finished."""
        self._finished = True
        self._winner_index = winner_index
        self._is_draw = is_draw
