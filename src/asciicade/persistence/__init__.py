"""Persistence layer public API."""

from __future__ import annotations

from asciicade.persistence.database import (
    Database,
    data_dir,
    database_path,
)
from asciicade.persistence.migrations import SCHEMA_VERSION, current_version, migrate
from asciicade.persistence.players import PlayerRepository
from asciicade.persistence.results import (
    LeaderboardEntry,
    MatchRecord,
    ResultRepository,
)

__all__ = [
    "SCHEMA_VERSION",
    "Database",
    "LeaderboardEntry",
    "MatchRecord",
    "PlayerRepository",
    "ResultRepository",
    "current_version",
    "data_dir",
    "database_path",
    "migrate",
]
