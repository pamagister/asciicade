"""Pong game package."""

from __future__ import annotations

from asciicade.games.pong.engine import PongEngine
from asciicade.games.pong.game import PONG_INSTRUCTIONS, PONG_OPTIONS, PongGame
from asciicade.games.pong.models import (
    Ball,
    Paddle,
    Point,
    PongConfig,
    PongGameOptions,
    PongPlayerView,
    PongSnapshot,
    clamp,
)

__all__ = [
    "PONG_INSTRUCTIONS",
    "PONG_OPTIONS",
    "Ball",
    "Paddle",
    "PongConfig",
    "PongEngine",
    "PongGame",
    "PongGameOptions",
    "PongPlayerView",
    "PongSnapshot",
    "Point",
    "clamp",
]
