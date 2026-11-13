"""Repository for persistent player profiles."""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from uuid import UUID

from asciicade.core.player import PlayerProfile
from asciicade.persistence.database import Database


class PlayerRepository:
    """Create, read and list player profiles."""

    def __init__(self, database: Database) -> None:
        """Store the database used by this repository."""
        self._database = database

    def create(self, name: str) -> PlayerProfile:
        """Persist a new player profile.

        Args:
            name: The display name.

        Returns:
            The created profile.
        """
        profile = PlayerProfile.create(name)
        with self._database.connection() as connection:
            connection.execute(
                "INSERT INTO players (id, name, created_at) VALUES (?, ?, ?)",
                (str(profile.id), profile.name, profile.created_at.isoformat()),
            )
        return profile

    def get(self, player_id: UUID) -> PlayerProfile | None:
        """Return a profile by identifier, or ``None`` when it does not exist."""
        with self._database.connection() as connection:
            row = connection.execute(
                "SELECT id, name, created_at FROM players WHERE id = ?",
                (str(player_id),),
            ).fetchone()
        return _row_to_profile(row) if row is not None else None

    def list(self) -> list[PlayerProfile]:
        """Return all profiles ordered by creation time and name."""
        with self._database.connection() as connection:
            rows = connection.execute(
                "SELECT id, name, created_at FROM players ORDER BY created_at, name"
            ).fetchall()
        return [_row_to_profile(row) for row in rows]

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
    )


def _parse_datetime(value: str) -> datetime:
    """Parse an ISO timestamp and assume UTC when no timezone is present."""
    parsed = datetime.fromisoformat(value)
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
