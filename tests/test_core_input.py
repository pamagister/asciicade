"""Tests for normalized input handling."""

from __future__ import annotations

from asciicade.core.game import GameMode
from asciicade.core.input import (
    Direction,
    InputAction,
    InputMap,
    bindings_for_mode,
    direction_for_action,
    input_map_for_mode,
    normalize_key,
)


def test_normalize_key_lowercases_and_resolves_aliases() -> None:
    assert normalize_key("Up") == "up"
    assert normalize_key("ESC") == "escape"
    assert normalize_key(" return ") == "enter"


def test_direction_delta_and_opposite() -> None:
    assert Direction.UP.delta == (0, -1)
    assert Direction.DOWN.delta == (0, 1)
    assert Direction.LEFT.delta == (-1, 0)
    assert Direction.RIGHT.delta == (1, 0)
    assert Direction.UP.opposite is Direction.DOWN
    assert Direction.LEFT.opposite is Direction.RIGHT


def test_direction_for_action() -> None:
    assert direction_for_action(InputAction.UP) is Direction.UP
    assert direction_for_action(InputAction.PAUSE) is None


def test_single_player_bindings_accept_arrows_and_wasd() -> None:
    input_map = input_map_for_mode(GameMode.SINGLE_PLAYER)

    arrow = input_map.resolve("up")
    wasd = input_map.resolve("w")

    assert arrow is not None
    assert arrow.action is InputAction.UP
    assert arrow.player == 1
    assert wasd is not None
    assert wasd.action is InputAction.UP
    assert wasd.player == 1


def test_multiplayer_bindings_keep_players_separate() -> None:
    input_map = input_map_for_mode(GameMode.MULTIPLAYER)

    first = input_map.resolve("up")
    second = input_map.resolve("w")

    assert first is not None
    assert first.player == 1
    assert second is not None
    assert second.player == 2
    assert second.action is InputAction.UP


def test_global_controls_are_player_independent() -> None:
    input_map = input_map_for_mode(GameMode.MULTIPLAYER)

    pause = input_map.resolve("escape")
    quit_event = input_map.resolve("q")

    assert pause is not None
    assert pause.action is InputAction.PAUSE
    assert pause.player is None
    assert quit_event is not None
    assert quit_event.action is InputAction.QUIT
    assert quit_event.player is None


def test_unknown_key_resolves_to_none() -> None:
    input_map = input_map_for_mode(GameMode.SINGLE_PLAYER)

    assert input_map.resolve("f1") is None


def test_keys_for_action_and_player() -> None:
    input_map = input_map_for_mode(GameMode.SINGLE_PLAYER)

    assert input_map.keys_for(InputAction.LEFT, player=1) == frozenset({"left", "a"})
    assert input_map.keys_for(InputAction.LEFT, player=2) == frozenset()


def test_bindings_for_mode_are_distinct() -> None:
    single = bindings_for_mode(GameMode.SINGLE_PLAYER)
    multi = bindings_for_mode(GameMode.MULTIPLAYER)

    single_map = InputMap(single)
    multi_map = InputMap(multi)

    assert all(isinstance(binding.keys, frozenset) for binding in single + multi)
    assert single_map.resolve("w").player == 1
    assert multi_map.resolve("w").player == 2


def test_input_map_len_counts_keys() -> None:
    input_map = InputMap(bindings_for_mode(GameMode.MULTIPLAYER))

    assert len(input_map) == 14


def test_player_one_action_buttons() -> None:
    input_map = input_map_for_mode(GameMode.MULTIPLAYER)

    action_a = input_map.resolve("space")
    action_b = input_map.resolve("altgr")
    action_b_alias = input_map.resolve("right_alt")

    assert action_a is not None
    assert action_a.action is InputAction.ACTION_A
    assert action_a.player == 1
    assert action_b is not None
    assert action_b.action is InputAction.ACTION_B
    assert action_b.player == 1
    assert action_b_alias is not None
    assert action_b_alias.action is InputAction.ACTION_B
    assert action_b_alias.player == 1


def test_player_two_action_buttons() -> None:
    input_map = input_map_for_mode(GameMode.MULTIPLAYER)

    action_a = input_map.resolve("shift")
    action_b = input_map.resolve("control")

    assert action_a is not None
    assert action_a.action is InputAction.ACTION_A
    assert action_a.player == 2
    assert action_b is not None
    assert action_b.action is InputAction.ACTION_B
    assert action_b.player == 2


def test_single_player_action_buttons_use_wasd_modifiers() -> None:
    input_map = input_map_for_mode(GameMode.SINGLE_PLAYER)

    action_a = input_map.resolve("shift")
    action_b = input_map.resolve("control")

    assert action_a is not None
    assert action_a.action is InputAction.ACTION_A
    assert action_a.player == 1
    assert action_b is not None
    assert action_b.action is InputAction.ACTION_B
    assert action_b.player == 1


def test_direction_for_action_returns_none_for_action_buttons() -> None:
    assert direction_for_action(InputAction.ACTION_A) is None
    assert direction_for_action(InputAction.ACTION_B) is None


def test_normalize_key_resolves_action_button_aliases() -> None:
    assert normalize_key("AltGr") == "iso_level3_shift"
    assert normalize_key("right_ctrl") == "control"
    assert normalize_key("shift") == "shift"
