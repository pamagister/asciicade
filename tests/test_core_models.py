"""Tests for core player, session and result models."""

from __future__ import annotations

import os
import subprocess
import sys
from datetime import UTC
from uuid import uuid4

import pytest

from asciicade.core.game import GameMode
from asciicade.core.player import (
    GuestPlayer,
    PlayerColor,
    PlayerProfile,
    PlayerSelection,
    player_color,
    player_identity,
)
from asciicade.core.results import (
    MatchOutcome,
    make_game_result,
    make_player_result,
)
from asciicade.core.session import GameSession


def test_profile_create_normalizes_name_and_sets_timestamp() -> None:
    profile = PlayerProfile.create("  Paul  ")

    assert profile.name == "Paul"
    assert profile.created_at.tzinfo is not None
    assert profile.id == profile.id


def test_profile_create_rejects_empty_name() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        PlayerProfile.create("   ")


def test_guest_player_gets_default_name() -> None:
    assert GuestPlayer(slot=1).name == "Guest 1"
    assert GuestPlayer(slot=2, name=" Ada ").name == "Ada"


def test_guest_player_rejects_invalid_slot() -> None:
    with pytest.raises(ValueError, match="slot must be 1 or 2"):
        GuestPlayer(slot=3)


def test_guest_player_rejects_blank_name() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        GuestPlayer(slot=1, name="   ")


def test_profile_create_stores_color() -> None:
    profile = PlayerProfile.create("Paul", color=PlayerColor.BRIGHT_CYAN)

    assert profile.color is PlayerColor.BRIGHT_CYAN
    assert profile.color.label == "Bright Cyan"


def test_guest_players_get_slot_colors() -> None:
    assert GuestPlayer(slot=1).color is PlayerColor.GREEN
    assert GuestPlayer(slot=2).color is PlayerColor.CYAN


def test_guest_players_can_override_color() -> None:
    assert GuestPlayer(slot=1, color=PlayerColor.YELLOW).color is PlayerColor.YELLOW


def test_player_color_helper_handles_profiles_and_guests() -> None:
    profile = PlayerProfile.create("Paul", color=PlayerColor.BLUE)
    guest = GuestPlayer(slot=2)

    assert player_color(profile) is PlayerColor.BLUE
    assert player_color(guest) is PlayerColor.CYAN


def test_player_color_has_sixteen_terminal_colors() -> None:
    assert len(tuple(PlayerColor)) == 16
    assert PlayerColor("bright_red") is PlayerColor.BRIGHT_RED


def test_selection_accepts_one_and_two_players() -> None:
    first = PlayerProfile.create("Paul")
    second = PlayerProfile.create("Ada")

    assert not PlayerSelection((first,)).is_multiplayer
    assert PlayerSelection((first, second)).is_multiplayer


def test_selection_rejects_same_profile_twice() -> None:
    first = PlayerProfile.create("Paul")

    with pytest.raises(ValueError, match="same player"):
        PlayerSelection((first, first))


def test_selection_rejects_two_guests_with_same_slot() -> None:
    with pytest.raises(ValueError, match="same player"):
        PlayerSelection((GuestPlayer(1), GuestPlayer(1)))


def test_selection_allows_profile_and_guest() -> None:
    profile = PlayerProfile.create("Paul")
    selection = PlayerSelection((profile, GuestPlayer(2)))

    assert selection.is_multiplayer
    assert player_identity(profile) != player_identity(selection.players[1])


def test_selection_rejects_three_players() -> None:
    players = tuple(PlayerProfile.create(f"P{index}") for index in range(3))

    with pytest.raises(ValueError, match="one or two"):
        PlayerSelection(players)


def test_game_session_defaults_to_now() -> None:
    session = GameSession.create(
        "snake",
        GameMode.SINGLE_PLAYER,
        (GuestPlayer(1),),
    )

    assert session.started_at.tzinfo is not None
    assert not session.is_multiplayer


def test_player_result_marks_guests() -> None:
    guest_result = make_player_result(GuestPlayer(1), 10, MatchOutcome.LOSS)
    profile = PlayerProfile.create("Paul")
    profile_result = make_player_result(profile, 5, MatchOutcome.WIN)

    assert guest_result.is_guest
    assert guest_result.player_id is None
    assert not profile_result.is_guest
    assert profile_result.player_id == profile.id


def test_single_player_result_requires_one_player() -> None:
    result = make_player_result(GuestPlayer(1), 10, MatchOutcome.LOSS)

    game_result = make_game_result("snake", GameMode.SINGLE_PLAYER, (result,))

    assert game_result.scores == {"Guest 1": 10}
    assert game_result.winner_name is None


def test_multiplayer_result_records_winner() -> None:
    first = make_player_result(PlayerProfile.create("Paul"), 3, MatchOutcome.LOSS)
    second = make_player_result(PlayerProfile.create("Ada"), 8, MatchOutcome.WIN)

    game_result = make_game_result(
        "snake",
        GameMode.MULTIPLAYER,
        (first, second),
        winner_name="Ada",
    )

    assert game_result.winner_name == "Ada"
    assert game_result.scores == {"Paul": 3, "Ada": 8}


def test_draw_must_not_have_winner() -> None:
    first = make_player_result(GuestPlayer(1), 1, MatchOutcome.DRAW)
    second = make_player_result(GuestPlayer(2), 1, MatchOutcome.DRAW)

    with pytest.raises(ValueError, match="must not declare a winner"):
        make_game_result(
            "snake",
            GameMode.MULTIPLAYER,
            (first, second),
            winner_name="Guest 1",
            is_draw=True,
        )


def test_winner_must_be_a_participant() -> None:
    first = make_player_result(GuestPlayer(1), 1, MatchOutcome.LOSS)
    second = make_player_result(GuestPlayer(2), 2, MatchOutcome.WIN)

    with pytest.raises(ValueError, match="winner must be"):
        make_game_result(
            "snake",
            GameMode.MULTIPLAYER,
            (first, second),
            winner_name="Nobody",
        )


def test_result_rejects_negative_score() -> None:
    result = make_player_result(GuestPlayer(1), -1, MatchOutcome.LOSS)

    with pytest.raises(ValueError, match="negative"):
        make_game_result("snake", GameMode.SINGLE_PLAYER, (result,))


def test_result_finished_at_defaults_to_utc() -> None:
    result = make_player_result(GuestPlayer(1), 1, MatchOutcome.LOSS)

    game_result = make_game_result("snake", GameMode.SINGLE_PLAYER, (result,))

    assert game_result.finished_at.tzinfo == UTC


def test_profile_ids_are_unique() -> None:
    first = PlayerProfile.create("Paul")
    second = PlayerProfile.create("Paul")

    assert first.id != second.id
    assert first.id != uuid4()


def test_core_does_not_import_textual() -> None:
    code = "import sys; import asciicade.core; assert 'textual' not in sys.modules"
    environment = {**os.environ, "PYTHONPATH": "src"}

    subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        env=environment,
        cwd=os.getcwd(),
    )
