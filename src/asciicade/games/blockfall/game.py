"""Blockfall game registration and metadata."""

from __future__ import annotations

from asciicade.core.game import GameDocs, GameMetadata, GameMode
from asciicade.core.options import (
    BooleanOptionDefinition,
    ChoiceOptionDefinition,
    GameOptionRegistry,
)
from asciicade.games.blockfall.engine import BlockfallEngine

BLOCKFALL_SUMMARY = (
    "Classic falling-block puzzle for one or two local players. Arrange tetrominoes into "
    "complete horizontal lines, clear them before the stack reaches the top and survive as "
    "the pieces fall faster."
)

BLOCKFALL_SINGLE_PLAYER = (
    "- Move the active piece with the arrow keys or WASD.\n"
    "- Rotate clockwise with Space, Shift, Up or W and counterclockwise with AltGr or Ctrl.\n"
    "- Press Down or S to move down one row. Hold the key to soft drop continuously.\n"
    "- Complete a horizontal line to clear it. Clearing several lines at once awards more points.\n"
    "- The level rises every 10 cleared lines and gravity becomes faster.\n"
    "- The game ends when a newly generated piece cannot enter the board.\n"
    "- Your score is stored in the single-player leaderboard."
)

BLOCKFALL_MULTIPLAYER = (
    "- Player 1 uses the arrow keys, Space or Up (clockwise) and AltGr (counterclockwise).\n"
    "- Player 2 uses A and D to move, S to soft drop, Shift or W (counterclockwise) and Ctrl "
    "(clockwise).\n"
    "  Player 2 plays on the left board.\n"
    "- Both players play at the same time on separate 10x20 boards.\n"
    "- The first player to top out loses and the other player wins. If both players top out on "
    "the\n"
    "  same tick, the match is a draw.\n"
    "- Each player has an independent score, line count, level and next-piece queue."
)

BLOCKFALL_CONTROLS_SHORT = (
    "Player 1 uses the arrow keys by default. Player 2 uses W/A/S/D. In single-player mode, WASD "
    "is\n"
    "accepted as an alternative to the arrow keys.\n"
    "Up (Player 1) and W (Player 2) rotate the active piece in addition to the action keys.\n"
    "Escape or P pauses or resumes during a game. See the general controls for leave-game and "
    "quit\n"
    "keys."
)

BLOCKFALL_CONTROLS_LONG = (
    "Player 1 uses the arrow keys by default. Player 2 uses W/A/S/D. In single-player mode, WASD "
    "is\n"
    "accepted as an alternative to the arrow keys.\n"
    "Up (Player 1) and W (Player 2) rotate the active piece in addition to the action keys; this "
    "is a portable alternative when Shift, Ctrl or AltGr are not reported by the terminal.\n"
    "Escape or P pauses or resumes during a game. The full, game-independent control list is on "
    "the\n"
    "[controls page](../index.md#controls)."
)

BLOCKFALL_SECTIONS = (
    (
        "Options",
        "- **Start level:** 1, 3, 5, 8 or 10. A higher start level increases the initial fall "
        "speed\n"
        "  and the score multiplier.\n"
        "- **Next piece:** On (default) or Off. Shows the next tetromino in the information "
        "panel.\n"
        "- **Ghost piece:** On (default) or Off. Shows a dim outline where the active piece will\n"
        "  land.",
    ),
    (
        "Rotation and wall kicks",
        "Rotation uses wall kicks: if a rotation would collide with a wall or a locked block,\n"
        "Blockfall tries a series of small horizontal and upward offsets and uses the first one "
        "that\n"
        "fits. This keeps rotation predictable near walls, the floor and uneven stacks.\n"
        "\n"
        "A short lock delay follows a failed downward move. During the lock delay the piece can "
        "still\n"
        "be moved or rotated; a successful adjustment restarts the delay. Pressing Down while the\n"
        "piece is resting locks it immediately.",
    ),
    (
        "Scoring and levels",
        "| Lines cleared | Base score |\n"
        "|---|---|\n"
        "| 1 | 100 |\n"
        "| 2 | 300 |\n"
        "| 3 | 500 |\n"
        "| 4 | 800 |\n"
        "\n"
        "The base score is multiplied by the current level. Soft drop awards one point per cell. "
        "The\n"
        "level rises every 10 cleared lines; the score for a clear uses the level before the\n"
        "level-up.\n"
        "\n"
        "Pieces are drawn from a seven-bag randomizer, so every group of seven pieces contains "
        "each\n"
        "tetromino exactly once. The next-piece queue is deterministic for a given random seed.",
    ),
    (
        "Rendering",
        "- Each logical cell is rendered as two horizontal block characters (`██`), so the "
        "playfield\n"
        "  stays visually square in terminals where characters are about twice as tall as they "
        "are\n"
        "  wide.\n"
        "- Locked and active blocks use distinct colors for each tetromino: I is cyan, O is "
        "yellow, T\n"
        "  is magenta, S is green, Z is red, J is blue and L is white.\n"
        "- The active piece is bold, the ghost piece is a dim outline and completed rows flash "
        "white\n"
        "  briefly before they disappear.\n"
        "- The 10x20 board is surrounded by a visible one-character border. The information panel\n"
        "  shows the player name, score, cleared lines, level and next piece.\n"
        "- In two-player mode, Player 2's board and information panel are on the left and Player "
        "1's\n"
        "  are on the right.",
    ),
)

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
        options=BLOCKFALL_OPTIONS,
        docs=GameDocs(
            summary=BLOCKFALL_SUMMARY,
            long_description=BLOCKFALL_SUMMARY,
            single_player=BLOCKFALL_SINGLE_PLAYER,
            multiplayer=BLOCKFALL_MULTIPLAYER,
            controls_short=BLOCKFALL_CONTROLS_SHORT,
            controls_long=BLOCKFALL_CONTROLS_LONG,
            sections=BLOCKFALL_SECTIONS,
        ),
    )
