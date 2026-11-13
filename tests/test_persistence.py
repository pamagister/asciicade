"""Tests for SQLite persistence and repositories."""

from __future__ import annotations

import sqlite3
from pathlib import Path
from uuid import UUID

import pytest

from asciicade.core.game import GameMode
from asciicade.core.player import GuestPlayer, PlayerProfile, PlayerSelection
from asciicade.core.results import MatchOutcome, make_game_result, make_player_result
from asciicade.persistence import (
    SCHEMA_VERSION,
    Database,
    PlayerRepository,
    ResultRepository,
    current_version,
    data_dir,
    database_path,
)


@pytest.fixture
def database(tmp_path: Path) -> Database:
    """Return an initialized database in a temporary directory."""
    db = Database(tmp_path / "asciicade.db")
    db.initialize()
    return db


def test_initialize_creates_schema_and_sets_version(database: Database) -> None:
    with database.connection() as connection:
        version = current_version(connection)
        tables = {
            row["name"]
            for row in connection.execute(
                "SELECT name FROM sqlite_master WHERE type = 'table'"
            ).fetchall()
        }

    assert version == SCHEMA_VERSION
    assert {"players", "game_results", "player_results"} <= tables


def test_initialize_is_idempotent(tmp_path: Path) -> None:
    db = Database(tmp_path / "asciicade.db")

    db.initialize()
    db.initialize()

    with db.connection() as connection:
        assert current_version(connection) == SCHEMA_VERSION


def test_initialize_rejects_newer_schema(tmp_path: Path) -> None:
    path = tmp_path / "future.db"
    connection = sqlite3.connect(path)
    connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION + 1}")
    connection.commit()
    connection.close()

    with pytest.raises(RuntimeError, match="newer"):
        Database(path).initialize()


def test_data_dir_and_database_path_honour_override(tmp_path: Path) -> None:
    assert data_dir(tmp_path) == tmp_path
    assert database_path(tmp_path) == tmp_path / "asciicade.db"


def test_profile_survives_restart(tmp_path: Path) -> None:
    path = tmp_path / "asciicade.db"
    Database(path).initialize()
    first = PlayerRepository(Database(path))
    profile = first.create("Paul")

    Database(path).initialize()
    second = PlayerRepository(Database(path))
    loaded = second.get(profile.id)

    assert loaded is not None
    assert loaded.name == "Paul"
    assert loaded.created_at == profile.created_at


def test_repository_lists_profiles_sorted(database: Database) -> None:
    repository = PlayerRepository(database)

    ada = repository.create("Ada")
    paul = repository.create("Paul")

    assert repository.count() == 2
    assert [profile.name for profile in repository.list()] == ["Ada", "Paul"]
    assert repository.get(ada.id) is not None
    assert repository.get(paul.id) is not None


def test_repository_rejects_blank_name(database: Database) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        PlayerRepository(database).create("   ")


def test_repository_returns_none_for_missing_profile(database: Database) -> None:
    repository = PlayerRepository(database)

    assert repository.get(PlayerProfile.create("Ghost").id) is None


def test_two_player_selection_requires_distinct_players(database: Database) -> None:
    repository = PlayerRepository(database)
    first = repository.create("Paul")
    second = repository.create("Ada")

    PlayerSelection((first, second))

    with pytest.raises(ValueError, match="same player"):
        PlayerSelection((first, first))


def test_guest_results_are_stored_without_profile(database: Database) -> None:
    results = ResultRepository(database)
    result = make_game_result(
        "snake",
        GameMode.SINGLE_PLAYER,
        (make_player_result(GuestPlayer(1), 12, MatchOutcome.LOSS),),
    )

    result_id = results.record(result)

    entries = results.leaderboard("snake")
    assert result_id > 0
    assert len(entries) == 1
    assert entries[0].player_id is None
    assert entries[0].player_name == "Guest 1"
    assert entries[0].score == 12


def test_leaderboard_orders_by_score_then_time(database: Database) -> None:
    players = PlayerRepository(database)
    results = ResultRepository(database)
    paul = players.create("Paul")
    ada = players.create("Ada")

    results.record(
        make_game_result(
            "snake",
            GameMode.SINGLE_PLAYER,
            (make_player_result(paul, 5, MatchOutcome.LOSS),),
        )
    )
    results.record(
        make_game_result(
            "snake",
            GameMode.SINGLE_PLAYER,
            (make_player_result(ada, 10, MatchOutcome.LOSS),),
        )
    )
    results.record(
        make_game_result(
            "snake",
            GameMode.SINGLE_PLAYER,
            (make_player_result(paul, 7, MatchOutcome.LOSS),),
        )
    )

    entries = results.leaderboard("snake", limit=2)

    assert [entry.score for entry in entries] == [10, 7]
    assert entries[0].player_name == "Ada"


def test_match_history_records_both_players_and_winner(database: Database) -> None:
    players = PlayerRepository(database)
    results = ResultRepository(database)
    paul = players.create("Paul")
    ada = players.create("Ada")

    results.record(
        make_game_result(
            "snake",
            GameMode.MULTIPLAYER,
            (
                make_player_result(paul, 3, MatchOutcome.LOSS),
                make_player_result(ada, 8, MatchOutcome.WIN),
            ),
            winner_name="Ada",
        )
    )

    history = results.match_history("snake")

    assert len(history) == 1
    record = history[0]
    assert record.winner_name == "Ada"
    assert not record.is_draw
    assert [player.score for player in record.players] == [3, 8]


def test_match_history_detects_draw(database: Database) -> None:
    results = ResultRepository(database)

    results.record(
        make_game_result(
            "snake",
            GameMode.MULTIPLAYER,
            (
                make_player_result(GuestPlayer(1), 1, MatchOutcome.DRAW),
                make_player_result(GuestPlayer(2), 1, MatchOutcome.DRAW),
            ),
            is_draw=True,
        )
    )

    history = results.match_history("snake")

    assert history[0].is_draw
    assert history[0].winner_name is None


def test_match_history_keeps_guest_names_after_profile_deletion(
    database: Database,
) -> None:
    players = PlayerRepository(database)
    results = ResultRepository(database)
    paul = players.create("Paul")

    results.record(
        make_game_result(
            "snake",
            GameMode.MULTIPLAYER,
            (
                make_player_result(paul, 4, MatchOutcome.LOSS),
                make_player_result(GuestPlayer(2), 6, MatchOutcome.WIN),
            ),
            winner_name="Guest 2",
        )
    )
    with database.connection() as connection:
        connection.execute("DELETE FROM players WHERE id = ?", (str(paul.id),))

    history = results.match_history("snake")

    assert history[0].players[0].player_name == "Paul"
    assert history[0].players[0].player_id == paul.id


def test_match_history_returns_newest_first(database: Database) -> None:
    results = ResultRepository(database)

    for score in (1, 2, 3):
        results.record(
            make_game_result(
                "snake",
                GameMode.MULTIPLAYER,
                (
                    make_player_result(GuestPlayer(1), score, MatchOutcome.LOSS),
                    make_player_result(GuestPlayer(2), score, MatchOutcome.WIN),
                ),
                winner_name="Guest 2",
            )
        )

    history = results.match_history("snake")

    assert [record.players[0].score for record in history] == [3, 2, 1]


def test_leaderboard_excludes_multiplayer_scores(database: Database) -> None:
    results = ResultRepository(database)
    results.record(
        make_game_result(
            "snake",
            GameMode.SINGLE_PLAYER,
            (make_player_result(GuestPlayer(1), 5, MatchOutcome.LOSS),),
        )
    )
    results.record(
        make_game_result(
            "snake",
            GameMode.MULTIPLAYER,
            (
                make_player_result(GuestPlayer(1), 99, MatchOutcome.WIN),
                make_player_result(GuestPlayer(2), 1, MatchOutcome.LOSS),
            ),
            winner_name="Guest 1",
        )
    )

    entries = results.leaderboard("snake")
    all_entries = results.leaderboard("snake", mode=None)

    assert [entry.score for entry in entries] == [5]
    assert len(all_entries) == 3


def test_match_history_excludes_single_player_results(database: Database) -> None:
    results = ResultRepository(database)
    results.record(
        make_game_result(
            "snake",
            GameMode.SINGLE_PLAYER,
            (make_player_result(GuestPlayer(1), 5, MatchOutcome.LOSS),),
        )
    )

    assert results.match_history("snake") == []
    assert len(results.match_history("snake", mode=None)) == 1


def test_failed_transaction_rolls_back(database: Database) -> None:
    repository = PlayerRepository(database)

    with pytest.raises(RuntimeError, match="boom"):
        with database.connection() as connection:
            connection.execute(
                "INSERT INTO players (id, name, created_at) VALUES (?, ?, ?)",
                ("rollback-id", "Ghost", "2026-01-01T00:00:00+00:00"),
            )
            raise RuntimeError("boom")

    assert repository.count() == 0
    assert repository.get(UUID(int=0)) is None


def test_deleting_result_cascades_player_results(database: Database) -> None:
    results = ResultRepository(database)
    result_id = results.record(
        make_game_result(
            "snake",
            GameMode.SINGLE_PLAYER,
            (make_player_result(GuestPlayer(1), 5, MatchOutcome.LOSS),),
        )
    )

    with database.connection() as connection:
        connection.execute("DELETE FROM game_results WHERE id = ?", (result_id,))

    assert results.match_history("snake", mode=None) == []
