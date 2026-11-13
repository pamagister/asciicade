"""Structured game results and match outcomes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from enum import StrEnum
from uuid import UUID

from asciicade.core.game import GameMode
from asciicade.core.player import GuestPlayer, PlayerProfile


class MatchOutcome(StrEnum):
    """The outcome of a player's participation in a match."""

    WIN = "win"
    LOSS = "loss"
    DRAW = "draw"
    ABANDONED = "abandoned"


@dataclass(frozen=True, slots=True)
class PlayerResult:
    """The result of a single player in a match."""

    player_id: UUID | None
    player_name: str
    score: int
    outcome: MatchOutcome

    @property
    def is_guest(self) -> bool:
        """Return whether this result belongs to a guest player."""
        return self.player_id is None


@dataclass(frozen=True, slots=True)
class GameResult:
    """The structured result of a completed game session."""

    game_id: str
    mode: GameMode
    player_results: tuple[PlayerResult, ...]
    finished_at: datetime
    winner_name: str | None = None
    is_draw: bool = False

    def __post_init__(self) -> None:
        """Validate the result invariants."""
        if not self.player_results:
            raise ValueError("A result must contain at least one player.")
        if any(result.score < 0 for result in self.player_results):
            raise ValueError("Scores must not be negative.")

        expected_players = 1 if self.mode is GameMode.SINGLE_PLAYER else 2
        if len(self.player_results) != expected_players:
            raise ValueError(
                f"{self.mode.value} results must contain {expected_players} player(s)."
            )

        if self.is_draw:
            if self.winner_name is not None:
                raise ValueError("A draw must not declare a winner.")
            if len(self.player_results) < 2:
                raise ValueError("Only multiplayer matches can be draws.")
        elif self.winner_name is not None:
            names = {result.player_name for result in self.player_results}
            if self.winner_name not in names:
                raise ValueError("The winner must be one of the participating players.")

    @property
    def scores(self) -> dict[str, int]:
        """Return the score for each player name."""
        return {result.player_name: result.score for result in self.player_results}


def make_player_result(
    player: PlayerProfile | GuestPlayer,
    score: int,
    outcome: MatchOutcome,
) -> PlayerResult:
    """Build a :class:`PlayerResult` for a player.

    Args:
        player: The participating profile or guest player.
        score: The final score.
        outcome: The player's match outcome.

    Returns:
        The structured player result.
    """
    return PlayerResult(
        player_id=player.id if isinstance(player, PlayerProfile) else None,
        player_name=player.name,
        score=score,
        outcome=outcome,
    )


def make_game_result(
    game_id: str,
    mode: GameMode,
    player_results: tuple[PlayerResult, ...],
    *,
    winner_name: str | None = None,
    is_draw: bool = False,
    finished_at: datetime | None = None,
) -> GameResult:
    """Build a :class:`GameResult` with sensible defaults.

    Args:
        game_id: The registered game identifier.
        mode: The game mode.
        player_results: The per-player results.
        winner_name: The winning player's name, if any.
        is_draw: Whether the match ended in a draw.
        finished_at: Optional completion timestamp. Defaults to the current UTC time.

    Returns:
        The structured game result.
    """
    return GameResult(
        game_id=game_id,
        mode=mode,
        player_results=player_results,
        finished_at=finished_at or datetime.now(UTC),
        winner_name=winner_name,
        is_draw=is_draw,
    )
