"""Snake documentation content."""

from __future__ import annotations

from asciicade.core.game import GameDocs

SNAKE_SUMMARY = (
    "Classic arcade Snake for one or two local players. Eat food, grow longer and avoid "
    "crashing into walls or your own body."
)

SNAKE_SINGLE_PLAYER = (
    "- The snake moves continuously on the grid.\n"
    "- Each food item increases your score and length.\n"
    "- Hitting a wall or your own body ends the game.\n"
    "- Your score is stored in the single-player leaderboard."
)

SNAKE_MULTIPLAYER = (
    "- Both players start at the same time on a shared arena.\n"
    "- By default each player has their own food in their own color. A snake can only eat its own\n"
    "  food.\n"
    '- Turning off "Food per player" restores the classic shared food that either snake can eat.\n'
    "  The shared ball is white.\n"
    "- Hitting a wall, yourself or the other snake eliminates you.\n"
    "- The surviving snake wins.\n"
    "- If both snakes are eliminated on the same tick, the match is a draw."
)

SNAKE_CONTROLS_SHORT = "Arrows/WASD move · Esc/P pause · Q quit"

SNAKE_CONTROLS_SHORT_MULTIPLAYER = "P1 Arrows · P2 WASD · Esc/P pause · Q quit"

SNAKE_CONTROLS_LONG = (
    "Player 1 uses the arrow keys by default. Player 2 uses W/A/S/D. In single-player mode, WASD "
    "is\n"
    "accepted as an alternative to the arrow keys. Direction changes are buffered and applied on "
    "the\n"
    "next game tick. Immediate 180-degree reversals are rejected.\n"
    "Escape or P pauses or resumes during a game. The full, game-independent control list is on "
    "the\n"
    "[controls page](../index.md#controls)."
)

SNAKE_SECTIONS = (
    (
        "Options",
        "- **Difficulty:** Easy, Medium (default), Hard. Changes the game speed.\n"
        "- **Wrap walls:** Off (default), On. When on, the snake reappears on the opposite side "
        "of\n"
        "  the arena when it leaves the play area. Hitting a wall no longer crashes the snake, "
        "but\n"
        "  hitting your own or the other snake's body still ends the game.\n"
        "- **Food per player:** On (default), Off. On gives each player in two-player mode their "
        "own\n"
        "  food in their player color. Off uses one neutral shared food, as in the original game.\n"
        "  This option has no effect in single-player mode.",
    ),
    (
        "Rendering",
        "Snake rendering uses solid block characters: the wall, side walls that are one arena "
        "cell\n"
        "wide. Food is drawn as a ball made of the left and right halves of a filled circle "
        "(`◖◗`).\n"
        "Player-owned food uses the player color, while shared food is white. The head is "
        "emphasized\n"
        "in bold rather than with a number marker. Player 1 is shown in green and player 2 in cyan "
        "by\n"
        "default; player profiles can choose from the eight normal terminal colors. Each logical "
        "arena\n"
        "cell is rendered as two horizontal characters, so the playfield stays visually square in\n"
        "terminals where characters are about twice as tall as they are wide.",
    ),
)

DOCS = GameDocs(
    summary=SNAKE_SUMMARY,
    single_player=SNAKE_SINGLE_PLAYER,
    multiplayer=SNAKE_MULTIPLAYER,
    controls_short=SNAKE_CONTROLS_SHORT,
    controls_short_multiplayer=SNAKE_CONTROLS_SHORT_MULTIPLAYER,
    controls_long=SNAKE_CONTROLS_LONG,
    sections=SNAKE_SECTIONS,
)
