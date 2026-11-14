"""Persistent application settings."""

from __future__ import annotations

import json
from dataclasses import dataclass
from uuid import UUID

from asciicade.core.game import GameMode
from asciicade.persistence.database import Database

_LAST_SESSION_KEY = "last_session"


@dataclass(frozen=True, slots=True)
class LastSession:
    """The most recent game setup used by the player."""

    game_id: str
    mode: GameMode
    player_ids: tuple[UUID, ...]


class SettingsRepository:
    """Read and write small application-level settings."""

    def __init__(self, database: Database) -> None:
        """Store the database used by this repository."""
        self._database = database

    def get_last_session(self) -> LastSession | None:
        """Return the last played game setup, if one was stored."""
        with self._database.connection() as connection:
            row = connection.execute(
                "SELECT value FROM settings WHERE key = ?",
                (_LAST_SESSION_KEY,),
            ).fetchone()
        if row is None:
            return None

        data = json.loads(str(row["value"]))
        return LastSession(
            game_id=str(data["game_id"]),
            mode=GameMode(str(data["mode"])),
            player_ids=tuple(UUID(str(player_id)) for player_id in data.get("player_ids", ())),
        )

    def save_last_session(self, session: LastSession) -> None:
        """Persist the most recent game setup."""
        value = json.dumps(
            {
                "game_id": session.game_id,
                "mode": session.mode.value,
                "player_ids": [str(player_id) for player_id in session.player_ids],
            }
        )
        with self._database.connection() as connection:
            connection.execute(
                "INSERT INTO settings (key, value) VALUES (?, ?) "
                "ON CONFLICT(key) DO UPDATE SET value = excluded.value",
                (_LAST_SESSION_KEY, value),
            )
