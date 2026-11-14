"""Pure rules for the Blockfall engine."""

from __future__ import annotations

import random

from asciicade.games.blockfall.models import (
    ROTATIONS,
    ActivePiece,
    Board,
    PieceKind,
    Position,
)

# Candidate offsets tried in order when a rotation would collide. The first
# offset lets a piece rotate in place; the following offsets provide simple wall
# and floor kicks. Offsets use board coordinates (y grows downward).
WALL_KICKS: tuple[tuple[int, int], ...] = (
    (0, 0),
    (-1, 0),
    (1, 0),
    (-2, 0),
    (2, 0),
    (0, -1),
    (-1, -1),
    (1, -1),
    (-2, -1),
    (2, -1),
    (0, -2),
)

_LINE_SCORES: dict[int, int] = {
    1: 100,
    2: 300,
    3: 500,
    4: 800,
}


def piece_cells(kind: PieceKind, rotation: int, x: int, y: int) -> tuple[Position, ...]:
    """Return the absolute cells for a piece kind, rotation and position."""
    offsets = ROTATIONS[kind][rotation]
    return tuple(Position(x + offset.x, y + offset.y) for offset in offsets)


def can_place(board: Board, kind: PieceKind, rotation: int, x: int, y: int) -> bool:
    """Return whether a piece fits at the given position and rotation."""
    return all(board.is_free(cell.x, cell.y) for cell in piece_cells(kind, rotation, x, y))


def ghost_position(board: Board, piece: ActivePiece) -> int:
    """Return the lowest valid ``y`` for the active piece."""
    y = piece.y
    while can_place(board, piece.kind, piece.rotation, piece.x, y + 1):
        y += 1
    return y


def clear_full_rows(board: Board) -> tuple[int, ...]:
    """Clear every full row and return the cleared row indices."""
    rows = board.full_rows()
    if rows:
        board.clear_rows(rows)
    return rows


def line_clear_score(lines: int, level: int) -> int:
    """Return the guideline score for clearing ``lines`` at ``level``."""
    return _LINE_SCORES.get(lines, 0) * max(1, level)


def shuffled_bag(rng: random.Random) -> list[PieceKind]:
    """Return a shuffled seven-piece bag."""
    bag = list(PieceKind)
    rng.shuffle(bag)
    return bag
