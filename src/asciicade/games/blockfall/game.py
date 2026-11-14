"""Blockfall game registration and metadata."""

from __future__ import annotations

from asciicade.core.game import GameMetadata, GameMode
from asciicade.core.options import (
    BooleanOptionDefinition,
    ChoiceOptionDefinition,
    GameOptionRegistry,
)
from asciicade.games.blockfall.engine import BlockfallEngine

BLOCKFALL_INSTRUCTIONS = """\
Objective: arrange falling tetrominoes into complete horizontal lines.

Single player:
- Move with the arrow keys or WASD.
- Rotate clockwise with Space (or Shift) and counterclockwise with AltGr
  (or Ctrl).
- Press Down or S to move down one row. Hold it to soft drop continuously.
- Complete a horizontal line to clear it. Clearing several lines at once awards
  more points.
- The level rises every 10 cleared lines and the pieces fall faster.
- The game ends when a new piece cannot enter the board.

Two players:
- Player 1 uses the arrow keys, Space (clockwise) and AltGr (counterclockwise).
- Player 2 uses A and D to move, S to soft drop, Ctrl (clockwise) and Shift
  (counterclockwise). Player 2 plays on the left board.
- Both players play at the same time on separate boards.
- The first player to top out loses and the other player wins. If both players
  top out on the same tick, the match is a draw.

Rotation uses wall kicks: if a rotation would collide, the piece is shifted
automatically when possible. The ghost piece shows where the active piece will
land.

See the general controls for pause, leave-game and quit keys.
"""

BLOCKFALL_OPTIONS = GameOptionRegistry(
    definitions=(
        ChoiceOptionDefinition(
            key="start_level",
            label="Start level",
            values=("1", "3", "5", "8", "10"),
            default="1",
        ),
        BooleanOptionDefinition(
            key="next_preview",
            label="Next piece",
            default=True,
        ),
        BooleanOptionDefinition(
            key="ghost_piece",
            label="Ghost piece",
            default=True,
        ),
    )
)


class BlockfallGame(BlockfallEngine):
    """Blockfall as a registered :class:`~asciicade.core.game.Game`."""

    metadata = GameMetadata(
        identifier="blockfall",
        name="Blockfall",
        description="Classic falling-block puzzle for one or two local players.",
        modes=(GameMode.SINGLE_PLAYER, GameMode.MULTIPLAYER),
        instructions=BLOCKFALL_INSTRUCTIONS,
        options=BLOCKFALL_OPTIONS,
    )
