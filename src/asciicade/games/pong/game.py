"""Pong game registration and metadata."""

from __future__ import annotations

from asciicade.core.game import GameMetadata, GameMode
from asciicade.core.options import ChoiceOptionDefinition, GameOptionRegistry
from asciicade.games.pong.docs import DOCS
from asciicade.games.pong.engine import PongEngine

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
        modes=(GameMode.SINGLE_PLAYER, GameMode.MULTIPLAYER),
        options=PONG_OPTIONS,
        docs=DOCS,
    )
