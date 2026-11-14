"""Pong game registration and metadata."""

from __future__ import annotations

from asciicade.core.game import GameMetadata, GameMode
from asciicade.core.options import ChoiceOptionDefinition, GameOptionRegistry
from asciicade.games.pong.engine import PongEngine

PONG_INSTRUCTIONS = """\
Objective: be the first player to reach the score limit.

Single player:
- You control the left paddle with the arrow keys or WASD.
- The computer controls the right paddle.
- Move your paddle to return the ball. Hitting nearer the paddle edge produces a
  steeper return angle.
- The first player to the score limit wins.

Two players:
- Player 1 uses the arrow keys.
- Player 2 uses W and S.
- The same paddle and ball physics apply.
- The first player to the score limit wins.

Global controls:
- Escape or P pauses or resumes during a game.
- While paused, Enter opens the leave-game dialog.
- Q opens the quit confirmation and exits the application when confirmed.
- On the game-over screen, Escape returns to the game menu.
"""

PONG_OPTIONS = GameOptionRegistry(
    definitions=(
        ChoiceOptionDefinition(
            key="score_limit",
            label="Score limit",
            values=("5", "7", "11", "15"),
            default="11",
        ),
        ChoiceOptionDefinition(
            key="difficulty",
            label="Difficulty",
            values=("Easy", "Normal", "Hard"),
            default="Normal",
        ),
    )
)


class PongGame(PongEngine):
    """Pong as a registered :class:`~asciicade.core.game.Game`."""

    metadata = GameMetadata(
        identifier="pong",
        name="Pong",
        description="Classic arcade Pong for one or two local players.",
        modes=(GameMode.SINGLE_PLAYER, GameMode.MULTIPLAYER),
        instructions=PONG_INSTRUCTIONS,
        options=PONG_OPTIONS,
    )
