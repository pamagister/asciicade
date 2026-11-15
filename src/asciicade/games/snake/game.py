"""Snake game registration and metadata."""

from __future__ import annotations

from asciicade.core.game import GameMetadata, GameMode
from asciicade.core.options import (
    BooleanOptionDefinition,
    ChoiceOptionDefinition,
    GameOptionRegistry,
)
from asciicade.games.snake.docs import DOCS
from asciicade.games.snake.engine import SnakeEngine

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
        modes=(GameMode.SINGLE_PLAYER, GameMode.MULTIPLAYER),
        options=SNAKE_OPTIONS,
        docs=DOCS,
    )
