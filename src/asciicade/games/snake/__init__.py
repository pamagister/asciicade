"""Snake game package."""

from __future__ import annotations

from asciicade.games.snake.engine import SnakeEngine
from asciicade.games.snake.game import SNAKE_INSTRUCTIONS, SnakeGame
from asciicade.games.snake.models import (
    Arena,
    FoodView,
    Position,
    Snake,
    SnakeConfig,
    SnakeSnapshot,
    SnakeView,
)
from asciicade.games.snake.rules import (
    collides_with_body,
    initial_body,
    occupied_cells,
    spawn_food,
)

__all__ = [
    "SNAKE_INSTRUCTIONS",
    "Arena",
    "FoodView",
    "Position",
    "Snake",
    "SnakeConfig",
    "SnakeEngine",
    "SnakeGame",
    "SnakeSnapshot",
    "SnakeView",
    "collides_with_body",
    "initial_body",
    "occupied_cells",
    "spawn_food",
]
