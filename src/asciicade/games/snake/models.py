"""Data structures for the Snake game engine."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass, field

from asciicade.core.input import Direction


@dataclass(frozen=True, slots=True, order=True)
class Position:
    """A cell coordinate in the arena."""

    x: int
    y: int

    def step(self, direction: Direction) -> Position:
        """Return the adjacent position in a direction."""
        delta_x, delta_y = direction.delta
        return Position(self.x + delta_x, self.y + delta_y)


@dataclass(frozen=True, slots=True)
class Arena:
    """The rectangular play area."""

    width: int
    height: int

    def __post_init__(self) -> None:
        """Validate arena dimensions."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Arena dimensions must be positive.")

    def contains(self, position: Position) -> bool:
        """Return whether a position is inside the arena."""
        return 0 <= position.x < self.width and 0 <= position.y < self.height

    @property
    def cells(self) -> tuple[Position, ...]:
        """Return all cells in row-major order."""
        return tuple(Position(x, y) for y in range(self.height) for x in range(self.width))


@dataclass
class Snake:
    """Mutable snake state used by the engine."""

    player_index: int
    body: tuple[Position, ...]
    direction: Direction
    alive: bool = True
    score: int = 0
    pending: deque[Direction] = field(default_factory=deque, repr=False)

    @property
    def head(self) -> Position:
        """Return the current head position."""
        return self.body[0]

    def queue_direction(self, direction: Direction) -> None:
        """Buffer a requested direction for a future tick."""
        self.pending.append(direction)

    def consume_direction(self) -> Direction:
        """Apply the next valid buffered direction.

        Rejected 180-degree turns are discarded. At most one direction is
        applied per tick so rapid inputs cannot fold the snake into itself.

        Returns:
            The direction used for this tick.
        """
        while self.pending:
            candidate = self.pending.popleft()
            if candidate is not self.direction.opposite:
                self.direction = candidate
                break
        return self.direction


@dataclass(frozen=True, slots=True)
class SnakeView:
    """An immutable snapshot of one snake for rendering."""

    player_index: int
    body: tuple[Position, ...]
    direction: Direction
    alive: bool
    score: int


@dataclass(frozen=True, slots=True)
class SnakeSnapshot:
    """An immutable snapshot of the complete game state."""

    width: int
    height: int
    snakes: tuple[SnakeView, ...]
    food: Position | None
    finished: bool
    winner_index: int | None
    is_draw: bool


@dataclass(frozen=True, slots=True)
class SnakeConfig:
    """Configuration for the Snake engine."""

    width: int = 30
    height: int = 15
    initial_length: int = 3
    tick_rate: float = 8.0
    wrap_walls: bool = False

    def __post_init__(self) -> None:
        """Validate the configuration."""
        if self.width < 10 or self.height < 8:
            raise ValueError("Arena must be at least 10x8.")
        if self.initial_length < 2:
            raise ValueError("Initial snake length must be at least 2.")
        if self.initial_length >= min(self.width, self.height):
            raise ValueError("Initial snake length does not fit in the arena.")
        if self.tick_rate <= 0:
            raise ValueError("Tick rate must be positive.")
