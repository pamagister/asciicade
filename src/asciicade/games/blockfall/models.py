"""Data structures for the Blockfall game engine."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import StrEnum

from asciicade.core.options import GameOptions


class PieceKind(StrEnum):
    """The seven falling-block shapes."""

    I = "I"  # noqa: E741 - Piece letter, not a variable.
    O = "O"  # noqa: E741 - Piece letter, not a variable.
    T = "T"
    S = "S"
    Z = "Z"
    J = "J"
    L = "L"


@dataclass(frozen=True, slots=True, order=True)
class Position:
    """A cell coordinate on a board."""

    x: int
    y: int


_BASE_CELLS: dict[PieceKind, tuple[Position, ...]] = {
    PieceKind.I: (
        Position(0, 1),
        Position(1, 1),
        Position(2, 1),
        Position(3, 1),
    ),
    PieceKind.O: (
        Position(0, 0),
        Position(1, 0),
        Position(0, 1),
        Position(1, 1),
    ),
    PieceKind.T: (
        Position(1, 0),
        Position(0, 1),
        Position(1, 1),
        Position(2, 1),
    ),
    PieceKind.S: (
        Position(1, 0),
        Position(2, 0),
        Position(0, 1),
        Position(1, 1),
    ),
    PieceKind.Z: (
        Position(0, 0),
        Position(1, 0),
        Position(1, 1),
        Position(2, 1),
    ),
    PieceKind.J: (
        Position(0, 0),
        Position(0, 1),
        Position(1, 1),
        Position(2, 1),
    ),
    PieceKind.L: (
        Position(2, 0),
        Position(0, 1),
        Position(1, 1),
        Position(2, 1),
    ),
}

_BOX_SIZE: dict[PieceKind, int] = {
    PieceKind.I: 4,
    PieceKind.O: 2,
    PieceKind.T: 3,
    PieceKind.S: 3,
    PieceKind.Z: 3,
    PieceKind.J: 3,
    PieceKind.L: 3,
}


def _rotate_clockwise(cells: tuple[Position, ...], size: int) -> tuple[Position, ...]:
    """Rotate cells clockwise inside a square bounding box."""
    return tuple(Position(size - 1 - cell.y, cell.x) for cell in cells)


def _build_rotations(base: tuple[Position, ...], size: int) -> tuple[tuple[Position, ...], ...]:
    """Build the four rotation states for a piece."""
    states = [base]
    for _ in range(3):
        states.append(_rotate_clockwise(states[-1], size))
    return tuple(states)


ROTATIONS: dict[PieceKind, tuple[tuple[Position, ...], ...]] = {
    kind: _build_rotations(cells, _BOX_SIZE[kind]) for kind, cells in _BASE_CELLS.items()
}

BOX_SIZES: dict[PieceKind, int] = dict(_BOX_SIZE)


@dataclass
class ActivePiece:
    """A falling piece and its position on a board."""

    kind: PieceKind
    rotation: int
    x: int
    y: int

    def cells(self) -> tuple[Position, ...]:
        """Return the absolute board cells occupied by the piece."""
        offsets = ROTATIONS[self.kind][self.rotation]
        return tuple(Position(self.x + offset.x, self.y + offset.y) for offset in offsets)


@dataclass
class Board:
    """A mutable rectangular board of locked pieces."""

    width: int
    height: int
    cells: list[PieceKind | None] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Validate dimensions and allocate the cell grid."""
        if self.width <= 0 or self.height <= 0:
            raise ValueError("Board dimensions must be positive.")
        expected = self.width * self.height
        if not self.cells:
            self.cells = [None] * expected
        elif len(self.cells) != expected:
            raise ValueError("Board cell count does not match its dimensions.")

    def index(self, x: int, y: int) -> int:
        """Return the row-major index for a cell."""
        return y * self.width + x

    def is_inside(self, x: int, y: int) -> bool:
        """Return whether a cell is inside the board."""
        return 0 <= x < self.width and 0 <= y < self.height

    def get(self, x: int, y: int) -> PieceKind | None:
        """Return the piece kind at a cell, or ``None`` when empty."""
        return self.cells[self.index(x, y)]

    def is_empty(self, x: int, y: int) -> bool:
        """Return whether an inside cell is empty."""
        return self.is_inside(x, y) and self.get(x, y) is None

    def is_free(self, x: int, y: int) -> bool:
        """Return whether a cell is inside the board and empty."""
        return self.is_empty(x, y)

    def set_cell(self, x: int, y: int, kind: PieceKind | None) -> None:
        """Set the piece kind at a cell."""
        self.cells[self.index(x, y)] = kind

    def clear(self) -> None:
        """Remove every locked piece."""
        self.cells = [None] * (self.width * self.height)

    def full_rows(self) -> tuple[int, ...]:
        """Return the indices of all completely filled rows."""
        return tuple(
            y
            for y in range(self.height)
            if all(self.get(x, y) is not None for x in range(self.width))
        )

    def clear_rows(self, rows: tuple[int, ...]) -> None:
        """Remove the given rows and drop the remaining rows down."""
        if not rows:
            return
        removed = set(rows)
        kept = [
            self.cells[y * self.width : (y + 1) * self.width]
            for y in range(self.height)
            if y not in removed
        ]
        empty = [[None] * self.width for _ in range(len(removed))]
        self.cells = [cell for row in empty + kept for cell in row]

    def occupied(self) -> set[Position]:
        """Return every occupied cell."""
        return {
            Position(x, y)
            for y in range(self.height)
            for x in range(self.width)
            if self.get(x, y) is not None
        }


@dataclass
class PlayerState:
    """Mutable engine state for one player."""

    player_index: int
    board: Board
    active: ActivePiece | None = None
    queue: list[PieceKind] = field(default_factory=list)
    bag: list[PieceKind] = field(default_factory=list)
    score: int = 0
    lines: int = 0
    level: int = 1
    alive: bool = True
    gravity_counter: int = 0
    lock_delay: int | None = None
    flash_rows: tuple[int, ...] = ()
    flash_ticks: int = 0


@dataclass(frozen=True, slots=True)
class BoardView:
    """An immutable snapshot of a board."""

    width: int
    height: int
    cells: tuple[PieceKind | None, ...]

    def cell_at(self, x: int, y: int) -> PieceKind | None:
        """Return the piece kind at a cell, or ``None`` when empty."""
        return self.cells[y * self.width + x]


@dataclass(frozen=True, slots=True)
class ActivePieceView:
    """An immutable snapshot of an active piece."""

    kind: PieceKind
    cells: tuple[Position, ...]


@dataclass(frozen=True, slots=True)
class BlockfallPlayerView:
    """An immutable snapshot of one player's state."""

    player_index: int
    board: BoardView
    active: ActivePieceView | None
    ghost: tuple[Position, ...]
    next_kind: PieceKind | None
    score: int
    lines: int
    level: int
    alive: bool
    flash_rows: tuple[int, ...]


@dataclass(frozen=True, slots=True)
class BlockfallSnapshot:
    """An immutable snapshot of the complete Blockfall state."""

    width: int
    height: int
    players: tuple[BlockfallPlayerView, ...]
    finished: bool
    winner_index: int | None
    is_draw: bool


_DEFAULT_START_LEVEL = 1
_DEFAULT_NEXT_PREVIEW = True
_DEFAULT_GHOST_PIECE = True


class BlockfallGameOptions:
    """Resolved option keys for Blockfall."""

    START_LEVEL_KEY = "start_level"
    NEXT_PREVIEW_KEY = "next_preview"
    GHOST_PIECE_KEY = "ghost_piece"

    @staticmethod
    def defaults() -> GameOptions:
        """Return the default option values for Blockfall."""
        return GameOptions(
            (
                (BlockfallGameOptions.START_LEVEL_KEY, str(_DEFAULT_START_LEVEL)),
                (
                    BlockfallGameOptions.NEXT_PREVIEW_KEY,
                    "on" if _DEFAULT_NEXT_PREVIEW else "off",
                ),
                (
                    BlockfallGameOptions.GHOST_PIECE_KEY,
                    "on" if _DEFAULT_GHOST_PIECE else "off",
                ),
            )
        )


@dataclass(frozen=True, slots=True)
class BlockfallConfig:
    """Configuration for the Blockfall engine."""

    width: int = 10
    height: int = 20
    tick_rate: float = 60.0
    start_level: int = _DEFAULT_START_LEVEL
    next_preview: bool = _DEFAULT_NEXT_PREVIEW
    ghost_piece: bool = _DEFAULT_GHOST_PIECE
    queue_size: int = 3
    lock_delay_ticks: int = 30
    flash_ticks: int = 12
    base_gravity_ticks: int = 48
    gravity_ticks_per_level: int = 3
    min_gravity_ticks: int = 3
    lines_per_level: int = 10

    def __post_init__(self) -> None:
        """Validate the configuration."""
        if self.width < 4 or self.height < 8:
            raise ValueError("Board must be at least 4x8.")
        if self.tick_rate <= 0:
            raise ValueError("Tick rate must be positive.")
        if self.start_level < 1:
            raise ValueError("Start level must be at least 1.")
        if self.queue_size < 1:
            raise ValueError("Queue size must be at least 1.")
        if self.lock_delay_ticks < 0:
            raise ValueError("Lock delay must not be negative.")
        if self.flash_ticks < 0:
            raise ValueError("Flash duration must not be negative.")
        if self.base_gravity_ticks < 1:
            raise ValueError("Base gravity must be positive.")
        if self.gravity_ticks_per_level < 0:
            raise ValueError("Gravity step must not be negative.")
        if self.min_gravity_ticks < 1:
            raise ValueError("Minimum gravity must be positive.")
        if self.min_gravity_ticks > self.base_gravity_ticks:
            raise ValueError("Minimum gravity cannot exceed base gravity.")
        if self.lines_per_level < 1:
            raise ValueError("Lines per level must be at least 1.")

    @classmethod
    def for_options(
        cls,
        options: GameOptions | None = None,
        *,
        base: BlockfallConfig | None = None,
    ) -> BlockfallConfig:
        """Return a configuration resolved from game options.

        Args:
            options: Resolved option values, or ``None`` for the defaults.
            base: Existing configuration whose non-option fields are preserved.
        """
        template = base or cls()
        values = options or BlockfallGameOptions.defaults()
        return replace(
            template,
            start_level=_parse_start_level(values.value_for(BlockfallGameOptions.START_LEVEL_KEY)),
            next_preview=values.value_for(BlockfallGameOptions.NEXT_PREVIEW_KEY) == "on",
            ghost_piece=values.value_for(BlockfallGameOptions.GHOST_PIECE_KEY) == "on",
        )

    def gravity_interval(self, level: int) -> int:
        """Return the number of ticks between gravity steps for a level."""
        level = max(1, level)
        interval = self.base_gravity_ticks - (level - 1) * self.gravity_ticks_per_level
        return max(self.min_gravity_ticks, interval)


def _parse_start_level(value: str) -> int:
    """Parse a start level, falling back to the default."""
    try:
        level = int(value)
    except ValueError:
        return _DEFAULT_START_LEVEL
    return level if level >= 1 else _DEFAULT_START_LEVEL
