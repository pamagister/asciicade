"""Snake game registration and metadata."""

from __future__ import annotations

from asciicade.core.game import GameMetadata, GameMode
from asciicade.core.options import (
    BooleanOptionDefinition,
    ChoiceOptionDefinition,
    GameOptionRegistry,
)
from asciicade.games.snake.engine import SnakeEngine

SNAKE_INSTRUCTIONS = """\
Objective: eat food, grow longer and avoid crashing.

Single player:
- Move with the arrow keys or WASD.
- Each food item increases your score and length.
- Hitting a wall or your own body ends the game.

Two players:
- Player 1 uses the arrow keys.
- Player 2 uses W, A, S and D.
- Both snakes share the arena.
- By default each player has their own food in their own color and can only eat
  that food.
- Set "Food per player" to off for the classic shared food that either snake can
  eat.
- Hitting a wall, yourself or the other snake eliminates you.
- The last surviving snake wins. If both crash on the same tick, it is a draw.

Direction changes are buffered and applied on the next game tick. Immediate
180-degree reversals are rejected.

See the general controls for pause, leave-game and quit keys.
"""

SNAKE_OPTIONS = GameOptionRegistry(
    definitions=(
        ChoiceOptionDefinition(
            key="difficulty",
            label="Difficulty",
            values=("Easy", "Medium", "Hard"),
            default="Medium",
        ),
        BooleanOptionDefinition(
            key="wrap_walls",
            label="Wrap walls",
            default=False,
        ),
        BooleanOptionDefinition(
            key="food_per_player",
            label="Food per player",
            default=True,
        ),
    )
)


class SnakeGame(SnakeEngine):
    """Snake as a registered :class:`~asciicade.core.game.Game`."""

    metadata = GameMetadata(
        identifier="snake",
        name="Snake",
        description="Classic arcade Snake for one or two local players.",
        modes=(GameMode.SINGLE_PLAYER, GameMode.MULTIPLAYER),
        instructions=SNAKE_INSTRUCTIONS,
        options=SNAKE_OPTIONS,
    )
