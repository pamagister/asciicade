"""Game session bookkeeping."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime

from asciicade.core.game import GameMode
from asciicade.core.player import GuestPlayer, PlayerProfile


@dataclass(frozen=True, slots=True)
class GameSession:
    """An active or completed game session."""

    game_id: str
    mode: GameMode
    players: tuple[PlayerProfile | GuestPlayer, ...]
    started_at: datetime

    @classmethod
    def create(
        cls,
        game_id: str,
        mode: GameMode,
        players: tuple[PlayerProfile | GuestPlayer, ...],
        *,
        started_at: datetime | None = None,
    ) -> GameSession:
        """Create a session with the current UTC timestamp by default."""
        return cls(
            game_id=game_id,
            mode=mode,
            players=players,
            started_at=started_at or datetime.now(UTC),
        )

    @property
    def is_multiplayer(self) -> bool:
        """Return whether the session has two players."""
        return len(self.players) == 2
