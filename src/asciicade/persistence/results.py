"""Repository for stored game results, leaderboards and match history."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from asciicade.core.game import GameMode
from asciicade.core.results import GameResult, MatchOutcome, PlayerResult
from asciicade.persistence.database import Database


@dataclass(frozen=True, slots=True)
class LeaderboardEntry:
    """A single score entry in a leaderboard."""

    player_id: UUID | None
    player_name: str
    score: int
    finished_at: datetime


@dataclass(frozen=True, slots=True)
class MatchRecord:
    """A stored match together with its participants."""

    result_id: int
    finished_at: datetime
    players: tuple[PlayerResult, ...]
    winner_name: str | None
    is_draw: bool


class ResultRepository:
    """Store and query completed game results."""

    def __init__(self, database: Database) -> None:
        """Store the database used by this repository."""
        self._database = database

    def record(self, result: GameResult) -> int:
        """Persist a completed result and return its identifier.

        Args:
            result: The structured result to store.

        Returns:
            The generated ``game_results`` identifier.
        """
        with self._database.connection() as connection:
            cursor = connection.execute(
                "INSERT INTO game_results (game_id, mode, finished_at) VALUES (?, ?, ?)",
                (result.game_id, result.mode.value, result.finished_at.isoformat()),
            )
            result_id = int(cursor.lastrowid or 0)
            for player_result in result.player_results:
                connection.execute(
                    "INSERT INTO player_results "
                    "(result_id, player_id, player_name, score, outcome) "
                    "VALUES (?, ?, ?, ?, ?)",
                    (
                        result_id,
                        str(player_result.player_id) if player_result.player_id else None,
                        player_result.player_name,
                        player_result.score,
                        player_result.outcome.value,
                    ),
                )
        return result_id

    def leaderboard(
        self,
        game_id: str,
        *,
        limit: int = 10,
        mode: GameMode | None = GameMode.SINGLE_PLAYER,
    ) -> list[LeaderboardEntry]:
        """Return the highest scores for a game.

        Args:
            game_id: The registered game identifier.
            limit: Maximum number of entries to return.
            mode: Optional game mode filter. Defaults to single-player scores.

        Returns:
            Entries ordered by score descending, then by finish time ascending.
        """
        where = "gr.game_id = ?"
        parameters: list[object] = [game_id]
        if mode is not None:
            where += " AND gr.mode = ?"
            parameters.append(mode.value)
        parameters.append(limit)

        with self._database.connection() as connection:
            rows = connection.execute(
                "SELECT pr.player_id, pr.player_name, pr.score, gr.finished_at "
                "FROM player_results AS pr "
                "JOIN game_results AS gr ON gr.id = pr.result_id "
                f"WHERE {where} "
                "ORDER BY pr.score DESC, gr.finished_at ASC, pr.id ASC "
                "LIMIT ?",
                tuple(parameters),
            ).fetchall()
        return [
            LeaderboardEntry(
                player_id=UUID(str(row["player_id"])) if row["player_id"] else None,
                player_name=str(row["player_name"]),
                score=int(row["score"]),
                finished_at=_parse_datetime(str(row["finished_at"])),
            )
            for row in rows
        ]

    def match_history(
        self,
        game_id: str,
        *,
        limit: int = 20,
        mode: GameMode | None = GameMode.MULTIPLAYER,
    ) -> list[MatchRecord]:
        """Return the most recent matches for a game.

        Args:
            game_id: The registered game identifier.
            limit: Maximum number of matches to return.
            mode: Optional game mode filter. Defaults to multiplayer matches.

        Returns:
            Matches ordered from newest to oldest.
        """
        where = "game_id = ?"
        parameters: list[object] = [game_id]
        if mode is not None:
            where += " AND mode = ?"
            parameters.append(mode.value)
        parameters.append(limit)

        with self._database.connection() as connection:
            result_rows = connection.execute(
                "SELECT id, finished_at FROM game_results "
                f"WHERE {where} ORDER BY finished_at DESC, id DESC LIMIT ?",
                tuple(parameters),
            ).fetchall()
            records: list[MatchRecord] = []
            for result_row in result_rows:
                result_id = int(result_row["id"])
                player_rows = connection.execute(
                    "SELECT player_id, player_name, score, outcome "
                    "FROM player_results WHERE result_id = ? ORDER BY id",
                    (result_id,),
                ).fetchall()
                players = tuple(
                    PlayerResult(
                        player_id=(
                            UUID(str(player_row["player_id"])) if player_row["player_id"] else None
                        ),
                        player_name=str(player_row["player_name"]),
                        score=int(player_row["score"]),
                        outcome=MatchOutcome(str(player_row["outcome"])),
                    )
                    for player_row in player_rows
                )
                records.append(
                    MatchRecord(
                        result_id=result_id,
                        finished_at=_parse_datetime(str(result_row["finished_at"])),
                        players=players,
                        winner_name=_winner_name(players),
                        is_draw=_is_draw(players),
                    )
                )
        return records


def _winner_name(players: tuple[PlayerResult, ...]) -> str | None:
    """Return the winner's name, if the match has one."""
    for player in players:
        if player.outcome is MatchOutcome.WIN:
            return player.player_name
    return None


def _is_draw(players: tuple[PlayerResult, ...]) -> bool:
    """Return whether every participant drew."""
    return bool(players) and all(player.outcome is MatchOutcome.DRAW for player in players)


def _parse_datetime(value: str) -> datetime:
    """Parse an ISO timestamp and assume UTC when no timezone is present."""
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
