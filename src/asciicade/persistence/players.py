"""Repository for persistent player profiles."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable
from datetime import UTC, datetime
from uuid import UUID

from asciicade.core.player import PlayerColor, PlayerProfile
from asciicade.persistence.database import Database


class PlayerRepository:
    """Create, read and list player profiles."""

    def __init__(self, database: Database) -> None:
        """Store the database used by this repository."""
        self._database = database

    def create(self, name: str, *, color: PlayerColor = PlayerColor.GREEN) -> PlayerProfile:
        """Persist a new player profile.

        Args:
            name: The display name.
            color: The terminal color used by the UI.

        Returns:
            The created profile.
        """
        profile = PlayerProfile.create(name, color=color)
        with self._database.connection() as connection:
            connection.execute(
                "INSERT INTO players (id, name, created_at, color) VALUES (?, ?, ?, ?)",
                (
                    str(profile.id),
                    profile.name,
                    profile.created_at.isoformat(),
                    profile.color.value,
                ),
            )
        return profile

    def get(self, player_id: UUID) -> PlayerProfile | None:
        """Return a profile by identifier, or ``None`` when it does not exist."""
        with self._database.connection() as connection:
            row = connection.execute(
                "SELECT id, name, created_at, color FROM players WHERE id = ?",
                (str(player_id),),
            ).fetchone()
        return _row_to_profile(row) if row is not None else None

    def list(self) -> list[PlayerProfile]:
        """Return profiles ordered by last played time, then creation time."""
        with self._database.connection() as connection:
            rows = connection.execute(
                "SELECT id, name, created_at, color FROM players "
                "ORDER BY last_played_at IS NULL, last_played_at DESC, created_at DESC, name"
            ).fetchall()
        return [_row_to_profile(row) for row in rows]

    def update(self, profile: PlayerProfile) -> None:
        """Update a profile's name and color."""
        with self._database.connection() as connection:
            cursor = connection.execute(
                "UPDATE players SET name = ?, color = ? WHERE id = ?",
                (profile.name, profile.color.value, str(profile.id)),
            )
            rowcount = cursor.rowcount
        if rowcount == 0:
            raise ValueError("Player profile does not exist.")

    def mark_played(self, player_ids: Iterable[UUID]) -> None:
        """Record that the given profiles played a session."""
        ids = tuple(player_ids)
        if not ids:
            return
        now = datetime.now(UTC).isoformat()
        with self._database.connection() as connection:
            connection.executemany(
                "UPDATE players SET last_played_at = ? WHERE id = ?",
                ((now, str(player_id)) for player_id in ids),
            )

    def count(self) -> int:
        """Return the number of stored profiles."""
        with self._database.connection() as connection:
            row = connection.execute("SELECT COUNT(*) FROM players").fetchone()
        return int(row[0]) if row is not None else 0


def _row_to_profile(row: sqlite3.Row) -> PlayerProfile:
    """Convert a database row to a :class:`PlayerProfile`."""
    return PlayerProfile(
        id=UUID(str(row["id"])),
        name=str(row["name"]),
        created_at=_parse_datetime(str(row["created_at"])),
        color=PlayerColor(str(row["color"])),
    )


def _parse_datetime(value: str) -> datetime:
    """Parse an ISO timestamp and assume UTC when no timezone is present."""
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
