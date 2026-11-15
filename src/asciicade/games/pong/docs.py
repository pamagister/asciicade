"""Pong documentation content."""

from __future__ import annotations

from asciicade.core.game import GameDocs

PONG_SUMMARY = (
    "Classic arcade Pong for one or two local players. Return the ball with your paddle, use "
    "the paddle edges to aim, and be first to reach the score limit."
)

PONG_SINGLE_PLAYER = (
    "- You control the right paddle with the arrow keys or WASD.\n"
    "- The computer controls the left paddle.\n"
    "- Move your paddle to return the ball. Hitting nearer the paddle edge produces a steeper "
    "return\n"
    "  angle.\n"
    "- The computer tracks the ball with a capped speed, so it is challenging but beatable.\n"
    "- The first player to the score limit wins."
)

PONG_MULTIPLAYER = (
    "- Player 1 uses the arrow keys and plays on the right side.\n"
    "- Player 2 uses W and S and plays on the left side.\n"
    "- Both players share the same keyboard and playfield.\n"
    "- The same paddle and ball physics apply.\n"
    "- The first player to the score limit wins."
)

PONG_CONTROLS_SHORT = "Arrows/WASD move · Esc/P pause · Q quit"

PONG_CONTROLS_SHORT_MULTIPLAYER = "P1 Arrows · P2 W/S · Esc/P pause · Q quit"

PONG_CONTROLS_LONG = (
    "Tap a direction key to move the paddle one half-block. Hold it longer than 0.1 seconds to "
    "move\n"
    "continuously; releasing the key stops movement immediately. Hold-to-move uses Kitty keyboard\n"
    "release events when the terminal supports them. Terminals without release reporting use a "
    "short\n"
    "fallback timeout before the paddle stops."
)

PONG_SECTIONS = (
    (
        "Options",
        "- **Score limit:** 5, 7, 11 (default) or 15.\n"
        "- **Difficulty:** Easy, Normal (default) or Hard. Difficulty changes the ball speed and, "
        "in\n"
        "  single-player mode, the computer paddle speed.\n"
        "\n"
        "In single-player mode the human can use either the arrow keys or WASD. In two-player "
        "mode\n"
        "the arrow keys belong to Player 1 and W/S to Player 2.",
    ),
    (
        "Physics and rendering",
        "- The ball reflects based on where it hits the paddle. A center hit produces a shallow\n"
        "  return; an edge hit produces a steeper angle.\n"
        "- The ball keeps a consistent speed and gains a small, capped speed increase during long\n"
        "  rallies.\n"
        "- The ball bounces off the top and bottom walls. A point is scored when it passes a "
        "paddle.\n"
        "- After each point the ball resets to the center and a short serve delay gives both "
        "players\n"
        "  time to reposition.\n"
        "- Paddles are one terminal column wide and use half-block characters (`▀`, `▄`, `█`) for\n"
        "  precise vertical movement.\n"
        "- The center line, border, paddles and ball use the eight normal terminal colors. Player\n"
        "  profiles use their selected color; the computer uses red.",
    ),
)

DOCS = GameDocs(
    summary=PONG_SUMMARY,
    single_player=PONG_SINGLE_PLAYER,
    multiplayer=PONG_MULTIPLAYER,
    controls_short=PONG_CONTROLS_SHORT,
    controls_short_multiplayer=PONG_CONTROLS_SHORT_MULTIPLAYER,
    controls_long=PONG_CONTROLS_LONG,
    sections=PONG_SECTIONS,
)
