"""Versioned SQLite schema migrations."""

from __future__ import annotations

import sqlite3

SCHEMA_VERSION = 1

_SCHEMA = """
CREATE TABLE players (
    id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE INDEX idx_players_name ON players(name);

CREATE TABLE game_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    game_id TEXT NOT NULL,
    mode TEXT NOT NULL,
    finished_at TEXT NOT NULL
);

CREATE INDEX idx_game_results_game ON game_results(game_id, finished_at DESC);

CREATE TABLE player_results (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    result_id INTEGER NOT NULL REFERENCES game_results(id) ON DELETE CASCADE,
    player_id TEXT,
    player_name TEXT NOT NULL,
    score INTEGER NOT NULL CHECK (score >= 0),
    outcome TEXT NOT NULL
);

CREATE INDEX idx_player_results_result ON player_results(result_id);
"""


def current_version(connection: sqlite3.Connection) -> int:
    """Return the schema version stored in the database."""
    row = connection.execute("PRAGMA user_version").fetchone()
    return int(row[0]) if row is not None else 0


def migrate(connection: sqlite3.Connection) -> None:
    """Apply all pending migrations.

    Args:
        connection: An open SQLite connection.

    Raises:
        RuntimeError: If the database was created by a newer application version.
    """
    version = current_version(connection)
    if version > SCHEMA_VERSION:
        raise RuntimeError(
            f"Database schema version {version} is newer than supported version {SCHEMA_VERSION}."
        )
    if version < 1:
        connection.executescript(_SCHEMA)
        connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
