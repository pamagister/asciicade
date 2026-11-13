"""Shared application-independent models and contracts."""

from __future__ import annotations

from asciicade.core.game import Game, GameMetadata, GameMode
from asciicade.core.input import (
    Direction,
    InputAction,
    InputBinding,
    InputEvent,
    InputMap,
    bindings_for_mode,
    direction_for_action,
    input_map_for_mode,
    normalize_key,
)
from asciicade.core.player import (
    GuestPlayer,
    Player,
    PlayerProfile,
    PlayerSelection,
    player_identity,
)
from asciicade.core.registry import (
    GameNotFoundError,
    GameRegistration,
    GameRegistry,
)
from asciicade.core.results import (
    GameResult,
    MatchOutcome,
    PlayerResult,
    make_game_result,
    make_player_result,
)
from asciicade.core.session import GameSession

__all__ = [
    "Direction",
    "Game",
    "GameMetadata",
    "GameMode",
    "GameNotFoundError",
    "GameRegistration",
    "GameRegistry",
    "GameResult",
    "GameSession",
    "GuestPlayer",
    "InputAction",
    "InputBinding",
    "InputEvent",
    "InputMap",
    "MatchOutcome",
    "Player",
    "PlayerProfile",
    "PlayerResult",
    "PlayerSelection",
    "bindings_for_mode",
    "direction_for_action",
    "input_map_for_mode",
    "make_game_result",
    "make_player_result",
    "normalize_key",
    "player_identity",
]
