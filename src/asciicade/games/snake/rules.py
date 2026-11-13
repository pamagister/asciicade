"""Pure rules and helpers for the Snake game."""

from __future__ import annotations

import random
from collections.abc import Iterable

from asciicade.core.input import Direction
from asciicade.games.snake.models import Arena, Position, Snake


def initial_body(
    head: Position,
    direction: Direction,
    length: int,
) -> tuple[Position, ...]:
    """Build a straight snake body ending at ``head``.

    Args:
        head: The head position.
        direction: The direction the snake is facing.
        length: The number of segments.

    Returns:
        The body ordered from head to tail.
    """
    delta_x, delta_y = direction.delta
    return tuple(
        Position(head.x - delta_x * offset, head.y - delta_y * offset) for offset in range(length)
    )


def collides_with_body(
    head: Position,
    body: tuple[Position, ...],
    *,
    tail_moves: bool,
) -> bool:
    """Return whether a new head collides with a snake body.

    Args:
        head: The proposed new head position.
        body: The current body ordered from head to tail.
        tail_moves: Whether the tail will vacate its cell this tick.

    Returns:
        ``True`` when the head hits a segment that remains occupied.
    """
    segments = body[:-1] if tail_moves else body
    return head in segments


def spawn_food(
    arena: Arena,
    occupied: Iterable[Position],
    rng: random.Random,
) -> Position | None:
    """Choose a uniformly random free cell for food.

    Args:
        arena: The play area.
        occupied: Cells that must not receive food.
        rng: Injectable random generator for deterministic tests.

    Returns:
        The chosen position, or ``None`` when the arena is full.
    """
    occupied_set = set(occupied)
    free = [cell for cell in arena.cells if cell not in occupied_set]
    if not free:
        return None
    return rng.choice(free)


def occupied_cells(snakes: Iterable[Snake]) -> set[Position]:
    """Return every cell occupied by the supplied snakes."""
    cells: set[Position] = set()
    for snake in snakes:
        cells.update(snake.body)
    return cells
