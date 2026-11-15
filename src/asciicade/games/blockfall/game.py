"""Blockfall game registration and metadata."""

from __future__ import annotations

from asciicade.core.game import GameMetadata, GameMode
from asciicade.core.options import (
    BooleanOptionDefinition,
    ChoiceOptionDefinition,
    GameOptionRegistry,
)
from asciicade.games.blockfall.docs import DOCS
from asciicade.games.blockfall.engine import BlockfallEngine

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
        modes=(GameMode.SINGLE_PLAYER, GameMode.MULTIPLAYER),
        options=BLOCKFALL_OPTIONS,
        docs=DOCS,
    )
