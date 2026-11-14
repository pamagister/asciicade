"""Deterministic Snake game engine."""

from __future__ import annotations

import random
from collections.abc import Sequence

from asciicade.core.game import GameMode
from asciicade.core.input import Direction, InputEvent, direction_for_action
from asciicade.core.options import GameOptions
from asciicade.core.player import Player
from asciicade.core.results import (
    GameResult,
    MatchOutcome,
    make_game_result,
    make_player_result,
)
from asciicade.games.snake.models import (
    Arena,
    FoodView,
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

# Ticks per second per difficulty.
_DIFFICULTY_TICK_RATES = {
    "Easy": 5.0,
    "Medium": 8.0,
    "Hard": 12.0,
}

_DEFAULT_DIFFICULTY = "Medium"


def _tick_rate_for(difficulty: str) -> float:
    """Return the tick rate for a difficulty value."""
    return _DIFFICULTY_TICK_RATES.get(difficulty, _DIFFICULTY_TICK_RATES[_DEFAULT_DIFFICULTY])


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
        self._foods: dict[int, Position] = {}
        self._separate_food = True
        self._finished = False
        self._winner_index: int | None = None
        self._is_draw = False

    @property
    def arena(self) -> Arena:
        """Return the configured arena."""
        return Arena(self.config.width, self.config.height)

    @property
    def tick_rate(self) -> float:
        """Return the number of simulation ticks per second."""
        return self.config.tick_rate

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
            foods=tuple(
                FoodView(player_index, position)
                for player_index, position in sorted(self._foods.items())
            ),
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
            raise ValueError(f"Unsupported Snake mode: {mode}")
        if len(players) != expected_players:
            raise ValueError(f"{mode.value} Snake requires {expected_players} player(s).")

        resolved_options = options or SnakeGameOptions.defaults()
        self._mode = mode
        self._players = tuple(players)
        self._separate_food = (
            resolved_options.value_for(SnakeGameOptions.FOOD_PER_PLAYER_KEY) == "on"
        )
        self.config = SnakeConfig(
            width=self.config.width,
            height=self.config.height,
            initial_length=self.config.initial_length,
            tick_rate=_tick_rate_for(resolved_options.value_for("difficulty")),
            wrap_walls=resolved_options.value_for("wrap_walls") == "on",
        )
        self._snakes = self._create_snakes()
        self._finished = False
        self._winner_index = None
        self._is_draw = False
        self._foods = {}
        self._spawn_initial_food()

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

    def clear_pending(self) -> None:
        """Discard all buffered direction requests."""
        for snake in self._snakes:
            snake.clear_pending()

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
            new_heads[index] = self._wrap_position(head)
            food = self._food_position(snake.player_index)
            growing[index] = food is not None and new_heads[index] == food

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
            for index, snake in enumerate(self._snakes):
                if not snake.alive or not growing.get(index, False):
                    continue
                owner = self._food_owner(snake.player_index)
                if not self._spawn_food_for(owner):
                    self._foods.pop(owner, None)
                    self._finish_board_full()
                    return

        self._resolve_end_condition()

    def _food_owner(self, player_index: int) -> int:
        """Return the food owner for a snake.

        Player-owned food uses the one-based player index. Shared food uses the
        neutral owner index ``0``.
        """
        if self._mode is GameMode.SINGLE_PLAYER:
            return 1
        if self._separate_food:
            return player_index
        return 0

    def _food_position(self, player_index: int) -> Position | None:
        """Return the food position a snake can eat, if any."""
        return self._foods.get(self._food_owner(player_index))

    def _spawn_initial_food(self) -> None:
        """Place the initial food items for the current mode."""
        if self._mode is GameMode.SINGLE_PLAYER:
            owners: tuple[int, ...] = (1,)
        elif self._separate_food:
            owners = tuple(snake.player_index for snake in self._snakes)
        else:
            owners = (0,)

        for owner in owners:
            if not self._spawn_food_for(owner):
                self._finish_board_full()
                return

    def _spawn_food_for(self, owner_index: int) -> bool:
        """Place or replace food for one owner.

        Returns:
            ``True`` when a free cell was found, ``False`` when the board is
            full.
        """
        occupied = occupied_cells(self._snakes)
        occupied.update(position for index, position in self._foods.items() if index != owner_index)
        position = spawn_food(self.arena, occupied, self._rng)
        if position is None:
            return False
        self._foods[owner_index] = position
        return True

    def _wrap_position(self, position: Position) -> Position:
        """Wrap a position onto the opposite side when wrap walls are enabled."""
        if not self.config.wrap_walls:
            return position
        arena = self.arena
        return Position(position.x % arena.width, position.y % arena.height)

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


class SnakeGameOptions:
    """Resolved option values for Snake."""

    DIFFICULTY_KEY = "difficulty"
    WRAP_WALLS_KEY = "wrap_walls"
    FOOD_PER_PLAYER_KEY = "food_per_player"

    @staticmethod
    def defaults() -> GameOptions:
        """Return the default option values for Snake."""
        return GameOptions(
            (
                (SnakeGameOptions.DIFFICULTY_KEY, "Medium"),
                (SnakeGameOptions.WRAP_WALLS_KEY, "off"),
                (SnakeGameOptions.FOOD_PER_PLAYER_KEY, "on"),
            )
        )
