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


MAX_CONTROLS_HINT_LENGTH = 80


@dataclass(frozen=True, slots=True)
class GameDocs:
    """Single source of truth for a game's documentation.

    All Markdown bodies use a small, fixed subset: paragraphs and ``-`` bullet
    lists. The docs pages under ``docs/games/`` and the in-game instructions are
    rendered from these fields.

    Attributes:
        summary: Short description used in game lists and page summaries.
        single_player: Markdown body for the single-player section.
        controls_short: One-line control hint for the game menu and the gameplay
            footer.
        controls_short_multiplayer: Optional one-line hint for two-player mode;
            falls back to ``controls_short``.
        multiplayer: Markdown body for the two-player section; required when the
            game declares :attr:`GameMode.MULTIPLAYER`.
        controls_long: Longer control explanation for the instructions screen
            and the docs page.
        long_description: Optional Markdown body shown under the page title;
            falls back to ``summary``.
        sections: Extra titled Markdown sections, e.g. scoring rules. A body may
            contain a ``{options}`` placeholder that is replaced by the options
            table rendered from the game's option registry.
    """

    summary: str
    single_player: str
    controls_short: str
    multiplayer: str | None = None
    controls_short_multiplayer: str | None = None
    controls_long: str | None = None
    long_description: str | None = None
    sections: tuple[tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        """Validate the documentation fields."""
        if not self.summary.strip():
            raise ValueError("Game docs summary must not be empty.")
        if not self.single_player.strip():
            raise ValueError("Game docs must describe the single-player mode.")
        _validate_controls_hint("controls_short", self.controls_short)
        if self.controls_short_multiplayer is not None:
            _validate_controls_hint("controls_short_multiplayer", self.controls_short_multiplayer)

    def controls_hint(self, mode: GameMode) -> str:
        """Return the one-line control hint for the given game mode."""
        if mode is GameMode.MULTIPLAYER and self.controls_short_multiplayer:
            return self.controls_short_multiplayer
        return self.controls_short

    @property
    def page_description(self) -> str:
        """Return the description shown on the generated docs page."""
        return self.long_description or self.summary


def _validate_controls_hint(name: str, value: str) -> None:
    """Validate a one-line controls hint."""
    if not value.strip():
        raise ValueError(f"Game docs {name} must not be empty.")
    if "\n" in value or "\r" in value:
        raise ValueError(f"Game docs {name} must be a single line.")
    if len(value) > MAX_CONTROLS_HINT_LENGTH:
        raise ValueError(f"Game docs {name} must be at most {MAX_CONTROLS_HINT_LENGTH} characters.")


@dataclass(frozen=True, slots=True)
class GameMetadata:
    """Static metadata describing a game."""

    identifier: str
    name: str
    modes: tuple[GameMode, ...]
    docs: GameDocs
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
        if GameMode.MULTIPLAYER in self.modes and not self.docs.multiplayer:
            raise ValueError("Multiplayer games must document the two-player mode.")
        if self.options is not None:
            keys = [definition.key for definition in self.options.definitions]
            if len(set(keys)) != len(keys):
                raise ValueError("Option keys must be unique.")

    @property
    def instructions(self) -> str:
        """Return the in-game instructions derived from the documentation."""
        parts = [self.docs.summary]
        if self.docs.single_player:
            parts.append(f"Single player:\n{self.docs.single_player}")
        if self.docs.multiplayer:
            parts.append(f"Two players:\n{self.docs.multiplayer}")
        parts.append(self.docs.controls_long or self.docs.controls_short)
        return "\n\n".join(part.strip() for part in parts if part.strip())


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

    def clear_pending(self) -> None:
        """Discard buffered input that has not been applied yet."""
        ...

    def tick(self) -> None:
        """Advance the game state by one deterministic tick."""
        ...

    @property
    def tick_rate(self) -> float:
        """Return the number of simulation ticks per second."""
        ...

    @property
    def is_finished(self) -> bool:
        """Return whether the current session has ended."""
        ...

    @property
    def result(self) -> GameResult | None:
        """Return the structured result once the session has ended."""
        ...
