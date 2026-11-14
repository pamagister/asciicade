"""Blockfall game package."""

from __future__ import annotations

from asciicade.games.blockfall.engine import BlockfallEngine
from asciicade.games.blockfall.game import (
    BLOCKFALL_INSTRUCTIONS,
    BLOCKFALL_OPTIONS,
    BlockfallGame,
)
from asciicade.games.blockfall.models import (
    BOX_SIZES,
    ROTATIONS,
    ActivePiece,
    ActivePieceView,
    BlockfallConfig,
    BlockfallGameOptions,
    BlockfallPlayerView,
    BlockfallSnapshot,
    Board,
    BoardView,
    PieceKind,
    PlayerState,
    Position,
)
from asciicade.games.blockfall.rules import (
    WALL_KICKS,
    can_place,
    clear_full_rows,
    ghost_position,
    line_clear_score,
    piece_cells,
    shuffled_bag,
)

__all__ = [
    "BLOCKFALL_INSTRUCTIONS",
    "BLOCKFALL_OPTIONS",
    "BOX_SIZES",
    "ROTATIONS",
    "WALL_KICKS",
    "ActivePiece",
    "ActivePieceView",
    "BlockfallConfig",
    "BlockfallEngine",
    "BlockfallGame",
    "BlockfallGameOptions",
    "BlockfallPlayerView",
    "BlockfallSnapshot",
    "Board",
    "BoardView",
    "PieceKind",
    "PlayerState",
    "Position",
    "can_place",
    "clear_full_rows",
    "ghost_position",
    "line_clear_score",
    "piece_cells",
    "shuffled_bag",
]
