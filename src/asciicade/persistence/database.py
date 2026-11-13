"""SQLite persistence for profiles, results and match history."""

from __future__ import annotations

import os
import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from asciicade.persistence.migrations import migrate

APP_NAME = "asciicade"
DATABASE_FILENAME = "asciicade.db"


def data_dir(override: Path | None = None) -> Path:
    """Return the XDG data directory used by Asciicade.

    Args:
        override: Optional explicit directory that takes precedence.

    Returns:
        The resolved data directory.
    """
    if override is not None:
        return Path(override)
    xdg_data_home = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg_data_home) if xdg_data_home else Path.home() / ".local" / "share"
    return base / APP_NAME


def database_path(override: Path | None = None) -> Path:
    """Return the path of the SQLite database file."""
    return data_dir(override) / DATABASE_FILENAME


class Database:
    """A thin wrapper around a SQLite database file."""

    def __init__(self, path: str | Path) -> None:
        """Store the database path."""
        self.path = Path(path)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        """Open a configured connection and commit on success.

        Yields:
            A SQLite connection with row access by name and foreign keys enabled.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        """Create the schema and apply pending migrations."""
        with self.connection() as connection:
            migrate(connection)
