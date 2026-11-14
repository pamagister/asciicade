"""Player identities and player selection rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID, uuid4


class PlayerColor(StrEnum):
    """A terminal color available for player profiles."""

    BLACK = "black"
    RED = "red"
    GREEN = "green"
    YELLOW = "yellow"
    BLUE = "blue"
    MAGENTA = "magenta"
    CYAN = "cyan"
    WHITE = "white"

    @property
    def label(self) -> str:
        """Return a human-readable color name."""
        return self.value.replace("_", " ").title()


@dataclass(frozen=True, slots=True)
class PlayerProfile:
    """A persistent player profile."""

    id: UUID
    name: str
    created_at: datetime
    color: PlayerColor = PlayerColor.GREEN

    @classmethod
    def create(
        cls,
        name: str,
        *,
        created_at: datetime | None = None,
        color: PlayerColor = PlayerColor.GREEN,
    ) -> PlayerProfile:
        """Create a new profile with a generated identifier.

        Args:
            name: Display name. Surrounding whitespace is removed.
            created_at: Optional creation timestamp. Defaults to the current UTC time.
            color: Display color used by the terminal UI.

        Returns:
            The new profile.

        Raises:
            ValueError: If the name is empty after normalization.
        """
        normalized = name.strip()
        if not normalized:
            raise ValueError("Player name must not be empty.")
        return cls(
            id=uuid4(),
            name=normalized,
            created_at=created_at or datetime.now(UTC),
            color=color,
        )


@dataclass(frozen=True, slots=True)
class GuestPlayer:
    """A transient player that is not stored in the database."""

    slot: int
    name: str = ""
    color: PlayerColor | None = None

    def __post_init__(self) -> None:
        """Validate the guest slot and fill in default display values."""
        if self.slot not in (1, 2):
            raise ValueError("Guest slot must be 1 or 2.")
        if not self.name:
            object.__setattr__(self, "name", f"Guest {self.slot}")
        elif not self.name.strip():
            raise ValueError("Guest name must not be empty.")
        else:
            object.__setattr__(self, "name", self.name.strip())
        if self.color is None:
            object.__setattr__(
                self,
                "color",
                PlayerColor.GREEN if self.slot == 1 else PlayerColor.CYAN,
            )


@dataclass(frozen=True, slots=True)
class PlayerSelection:
    """A validated selection of one or two distinct players."""

    players: tuple[PlayerProfile | GuestPlayer, ...]

    def __post_init__(self) -> None:
        """Validate the selection size and uniqueness of player identities."""
        if len(self.players) not in (1, 2):
            raise ValueError("A selection must contain one or two players.")
        identities = [player_identity(player) for player in self.players]
        if len(set(identities)) != len(identities):
            raise ValueError("The same player cannot occupy two slots.")

    @property
    def is_multiplayer(self) -> bool:
        """Return whether this selection contains two players."""
        return len(self.players) == 2


def player_identity(player: PlayerProfile | GuestPlayer) -> str:
    """Return a stable identity string for a player.

    Args:
        player: A persistent profile or a guest player.

    Returns:
        A string that uniquely identifies the player within a selection.
    """
    if isinstance(player, PlayerProfile):
        return f"profile:{player.id}"
    return f"guest:{player.slot}"


Player = PlayerProfile | GuestPlayer


def player_color(player: Player) -> PlayerColor:
    """Return the display color for a profile or guest player."""
    if isinstance(player, PlayerProfile):
        return player.color
    return player.color or (PlayerColor.GREEN if player.slot == 1 else PlayerColor.CYAN)
