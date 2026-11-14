"""Shared game contracts and metadata."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Protocol

from asciicade.core.options import GameOptionRegistry, GameOptions
from asciicade.core.player import Player

if TYPE_CHECKING:
    from asciicade.core.input import InputEvent
    from asciicade.core.results import GameResult


class GameMode(StrEnum):
    """A supported way to play a game."""

    SINGLE_PLAYER = "single-player"
    MULTIPLAYER = "multiplayer"


@dataclass(frozen=True, slots=True)
class GameMetadata:
    """Static metadata describing a game."""

    identifier: str
    name: str
    description: str
    modes: tuple[GameMode, ...]
    instructions: str
    options: GameOptionRegistry | None = None

    def __post_init__(self) -> None:
        """Validate the metadata fields."""
        if not self.identifier.strip():
            raise ValueError("Game identifier must not be empty.")
        if not self.name.strip():
            raise ValueError("Game name must not be empty.")
        if not self.modes:
            raise ValueError("A game must declare at least one mode.")
        if len(set(self.modes)) != len(self.modes):
            raise ValueError("Game modes must be unique.")
        if self.options is not None:
            keys = [definition.key for definition in self.options.definitions]
            if len(set(keys)) != len(keys):
                raise ValueError("Option keys must be unique.")


class Game(Protocol):
    """The minimal interface implemented by every game."""

    @property
    def metadata(self) -> GameMetadata:
        """Return the static metadata for this game."""
        ...

    def start(
        self,
        mode: GameMode,
        players: Sequence[Player],
        *,
        options: GameOptions | None = None,
    ) -> None:
        """Initialize a new session for the given mode and players.

        Args:
            mode: The game mode.
            players: One player for single-player, two for multiplayer.
            options: Optional resolved game options. Defaults to the game's
                declared option defaults.
        """
        ...

    def handle_input(self, event: InputEvent) -> None:
        """Feed a normalized input event into the game."""
        ...

    def tick(self) -> None:
        """Advance the game state by one deterministic tick."""
        ...

    @property
    def is_finished(self) -> bool:
        """Return whether the current session has ended."""
        ...

    @property
    def result(self) -> GameResult | None:
        """Return the structured result once the session has ended."""
        ...
