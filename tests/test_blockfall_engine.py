"""Tests for the deterministic Blockfall engine."""

from __future__ import annotations

import os
import random
import subprocess
import sys

import pytest

from asciicade.core.game import GameMode
from asciicade.core.input import InputAction, InputEvent
from asciicade.core.options import GameOptions
from asciicade.core.player import GuestPlayer, PlayerProfile
from asciicade.core.results import MatchOutcome
from asciicade.games.blockfall import (
    ROTATIONS,
    ActivePiece,
    BlockfallConfig,
    BlockfallGame,
    Board,
    PieceKind,
    Position,
    line_clear_score,
    shuffled_bag,
)


def make_engine(
    mode: GameMode = GameMode.SINGLE_PLAYER,
    *,
    seed: int = 1234,
    config: BlockfallConfig | None = None,
    players: tuple[GuestPlayer, ...] | None = None,
    options: GameOptions | None = None,
) -> BlockfallGame:
    """Create a started engine for tests."""
    engine = BlockfallGame(config or BlockfallConfig(), random.Random(seed))
    selected = players or (GuestPlayer(1),)
    engine.start(mode, selected, options=options)
    return engine


def set_active(
    engine: BlockfallGame,
    kind: PieceKind,
    rotation: int,
    x: int,
    y: int,
    *,
    player_index: int = 0,
) -> None:
    """Replace a player's active piece for a deterministic scenario."""
    state = engine._states[player_index]
    state.active = ActivePiece(kind, rotation, x, y)
    state.gravity_counter = 0
    state.lock_delay = None


def fill_row(engine: BlockfallGame, y: int, *, skip: range = range(0)) -> None:
    """Fill one row with locked pieces except for the skipped columns."""
    board = engine._states[0].board
    for x in range(engine.config.width):
        if x not in skip:
            board.set_cell(x, y, PieceKind.J)


def test_single_player_initial_state() -> None:
    engine = make_engine()
    snapshot = engine.snapshot

    assert snapshot.width == 10
    assert snapshot.height == 20
    assert len(snapshot.players) == 1
    assert snapshot.players[0].player_index == 1
    assert snapshot.players[0].active is not None
    assert snapshot.players[0].next_kind is not None
    assert snapshot.players[0].score == 0
    assert snapshot.players[0].lines == 0
    assert snapshot.players[0].level == 1


def test_rotations_have_four_states() -> None:
    assert set(ROTATIONS[PieceKind.T][0]) == {
        Position(1, 0),
        Position(0, 1),
        Position(1, 1),
        Position(2, 1),
    }
    assert set(ROTATIONS[PieceKind.T][1]) == {
        Position(1, 0),
        Position(1, 1),
        Position(1, 2),
        Position(2, 1),
    }
    assert set(ROTATIONS[PieceKind.O][0]) == set(ROTATIONS[PieceKind.O][1])
    assert len(ROTATIONS[PieceKind.I]) == 4


def test_move_left_right_and_down() -> None:
    engine = make_engine()
    state = engine._states[0]
    set_active(engine, PieceKind.O, 0, 4, 0)

    engine.handle_input(InputEvent(InputAction.LEFT, player=1))
    assert state.active is not None
    assert state.active.x == 3

    engine.handle_input(InputEvent(InputAction.RIGHT, player=1))
    assert state.active is not None
    assert state.active.x == 4

    engine.handle_input(InputEvent(InputAction.DOWN, player=1))
    assert state.active is not None
    assert state.active.y == 1
    assert state.score == 1


def test_piece_cannot_move_through_a_wall() -> None:
    engine = make_engine()
    state = engine._states[0]
    set_active(engine, PieceKind.O, 0, 0, 0)

    engine.handle_input(InputEvent(InputAction.LEFT, player=1))

    assert state.active is not None
    assert state.active.x == 0


def test_player_one_rotation_actions() -> None:
    engine = make_engine()
    state = engine._states[0]

    set_active(engine, PieceKind.T, 0, 3, 0)
    engine.handle_input(InputEvent(InputAction.ACTION_A, player=1))
    assert state.active is not None
    assert state.active.rotation == 1

    set_active(engine, PieceKind.T, 0, 3, 0)
    engine.handle_input(InputEvent(InputAction.ACTION_B, player=1))
    assert state.active is not None
    assert state.active.rotation == 3


def test_player_two_rotation_actions() -> None:
    engine = make_engine(
        GameMode.MULTIPLAYER,
        players=(GuestPlayer(1), GuestPlayer(2)),
    )
    state = engine._states[1]

    set_active(engine, PieceKind.T, 0, 3, 0, player_index=1)
    engine.handle_input(InputEvent(InputAction.ACTION_B, player=2))
    assert state.active is not None
    assert state.active.rotation == 1

    set_active(engine, PieceKind.T, 0, 3, 0, player_index=1)
    engine.handle_input(InputEvent(InputAction.ACTION_A, player=2))
    assert state.active is not None
    assert state.active.rotation == 3


def test_players_move_independently() -> None:
    engine = make_engine(
        GameMode.MULTIPLAYER,
        players=(GuestPlayer(1), GuestPlayer(2)),
    )
    set_active(engine, PieceKind.O, 0, 4, 0, player_index=0)
    set_active(engine, PieceKind.O, 0, 4, 0, player_index=1)

    engine.handle_input(InputEvent(InputAction.RIGHT, player=1))
    engine.handle_input(InputEvent(InputAction.LEFT, player=2))

    assert engine._states[0].active is not None
    assert engine._states[0].active.x == 5
    assert engine._states[1].active is not None
    assert engine._states[1].active.x == 3


def test_rotation_kicks_away_from_right_wall() -> None:
    engine = make_engine()
    state = engine._states[0]
    set_active(engine, PieceKind.I, 1, 7, 0)

    engine.handle_input(InputEvent(InputAction.ACTION_A, player=1))

    assert state.active is not None
    assert state.active.rotation == 2
    assert state.active.x == 6


def test_rotation_kicks_away_from_left_wall() -> None:
    engine = make_engine()
    state = engine._states[0]
    set_active(engine, PieceKind.I, 1, -2, 0)

    engine.handle_input(InputEvent(InputAction.ACTION_A, player=1))

    assert state.active is not None
    assert state.active.rotation == 2
    assert state.active.x == 0


def test_rotation_kicks_up_from_floor() -> None:
    engine = make_engine()
    state = engine._states[0]
    set_active(engine, PieceKind.T, 0, 3, 18)

    engine.handle_input(InputEvent(InputAction.ACTION_A, player=1))

    assert state.active is not None
    assert state.active.rotation == 1
    assert state.active.y == 17


def test_single_line_clear_scores_and_spawns_next_piece() -> None:
    engine = make_engine()
    state = engine._states[0]
    fill_row(engine, 19, skip=range(6, 10))
    set_active(engine, PieceKind.I, 0, 6, 18)

    engine._lock_piece(state)

    assert state.lines == 1
    assert state.score == 100
    assert state.board.full_rows() == ()
    assert state.active is not None
    assert engine.snapshot.players[0].flash_rows == (19,)


def test_four_line_clear_scores() -> None:
    engine = make_engine()
    state = engine._states[0]
    for y in range(16, 20):
        for x in range(1, engine.config.width):
            state.board.set_cell(x, y, PieceKind.J)
    set_active(engine, PieceKind.I, 1, -2, 16)

    engine._lock_piece(state)

    assert state.lines == 4
    assert state.score == 800
    assert state.board.full_rows() == ()


def test_level_increases_every_ten_lines() -> None:
    engine = make_engine()
    state = engine._states[0]
    state.lines = 9
    state.level = 1
    fill_row(engine, 19, skip=range(6, 10))
    set_active(engine, PieceKind.I, 0, 6, 18)

    engine._lock_piece(state)

    assert state.lines == 10
    assert state.level == 2
    assert state.score == 100


def test_line_clear_scores_use_guideline_values() -> None:
    assert line_clear_score(1, 1) == 100
    assert line_clear_score(2, 1) == 300
    assert line_clear_score(3, 1) == 500
    assert line_clear_score(4, 1) == 800
    assert line_clear_score(1, 5) == 500


def test_ghost_piece_is_lowest_valid_position() -> None:
    engine = make_engine()
    set_active(engine, PieceKind.O, 0, 4, 0)

    ghost = engine.snapshot.players[0].ghost

    assert min(cell.y for cell in ghost) == 18
    assert max(cell.y for cell in ghost) == 19


def test_ghost_piece_can_be_disabled() -> None:
    engine = make_engine(
        options=GameOptions(
            (
                ("start_level", "1"),
                ("next_preview", "on"),
                ("ghost_piece", "off"),
            )
        )
    )
    set_active(engine, PieceKind.O, 0, 4, 0)

    assert engine.snapshot.players[0].ghost == ()


def test_options_set_start_level_and_toggles() -> None:
    engine = make_engine(
        options=GameOptions(
            (
                ("start_level", "5"),
                ("next_preview", "off"),
                ("ghost_piece", "off"),
            )
        )
    )

    assert engine.config.start_level == 5
    assert engine.snapshot.players[0].level == 5
    assert engine.config.next_preview is False
    assert engine.config.ghost_piece is False


def test_queue_and_bag_start_with_all_seven_pieces() -> None:
    engine = make_engine()
    state = engine._states[0]

    kinds = set(state.queue) | set(state.bag)
    if state.active is not None:
        kinds.add(state.active.kind)

    assert kinds == set(PieceKind)
    assert len(state.queue) + len(state.bag) + (1 if state.active else 0) == 7


def test_shuffled_bag_contains_each_piece_once() -> None:
    bag = shuffled_bag(random.Random(7))

    assert len(bag) == 7
    assert set(bag) == set(PieceKind)


def test_same_seed_produces_same_pieces() -> None:
    first = make_engine(seed=99)
    second = make_engine(seed=99)

    assert first.snapshot.players[0].active == second.snapshot.players[0].active
    assert first.snapshot.players[0].next_kind == second.snapshot.players[0].next_kind


def test_soft_drop_into_floor_locks_piece() -> None:
    engine = make_engine()
    state = engine._states[0]
    set_active(engine, PieceKind.O, 0, 4, 18)

    engine.handle_input(InputEvent(InputAction.DOWN, player=1))

    assert state.board.get(4, 18) is PieceKind.O
    assert state.board.get(5, 19) is PieceKind.O
    assert state.active is not None


def test_gravity_moves_piece_down() -> None:
    engine = make_engine(
        config=BlockfallConfig(
            base_gravity_ticks=2,
            gravity_ticks_per_level=0,
            min_gravity_ticks=1,
        )
    )
    state = engine._states[0]
    set_active(engine, PieceKind.O, 0, 4, 0)

    engine.tick()
    assert state.active is not None
    assert state.active.y == 0

    engine.tick()
    assert state.active is not None
    assert state.active.y == 1


def test_lock_delay_allows_adjustment_before_locking() -> None:
    engine = make_engine(config=BlockfallConfig(base_gravity_ticks=1000, min_gravity_ticks=1000))
    state = engine._states[0]
    set_active(engine, PieceKind.O, 0, 4, 18)
    state.lock_delay = 2

    engine.tick()
    assert state.board.get(4, 18) is None
    assert state.lock_delay == 1

    engine.tick()
    assert state.board.get(4, 18) is PieceKind.O
    assert state.board.get(5, 19) is PieceKind.O


def test_line_clear_flash_ages_out() -> None:
    engine = make_engine()
    state = engine._states[0]
    fill_row(engine, 19, skip=range(6, 10))
    set_active(engine, PieceKind.I, 0, 6, 18)
    engine._lock_piece(state)

    assert engine.snapshot.players[0].flash_rows == (19,)
    for _ in range(engine.config.flash_ticks):
        engine.tick()

    assert engine.snapshot.players[0].flash_rows == ()


def test_top_out_when_new_piece_cannot_enter() -> None:
    engine = make_engine()
    state = engine._states[0]
    for x in range(3, 6):
        state.board.set_cell(x, 0, PieceKind.J)
        state.board.set_cell(x, 1, PieceKind.J)
    state.active = None
    state.alive = True

    engine._spawn(state)

    assert not state.alive
    engine._resolve_end_condition()
    assert engine.is_finished
    result = engine.result
    assert result is not None
    assert result.player_results[0].outcome is MatchOutcome.LOSS
    assert result.winner_name is None


def test_multiplayer_last_player_wins() -> None:
    engine = make_engine(
        GameMode.MULTIPLAYER,
        players=(GuestPlayer(1), GuestPlayer(2)),
    )
    engine._states[1].alive = False

    engine._resolve_end_condition()

    assert engine.is_finished
    result = engine.result
    assert result is not None
    assert result.winner_name == "Guest 1"
    assert result.player_results[0].outcome is MatchOutcome.WIN
    assert result.player_results[1].outcome is MatchOutcome.LOSS


def test_multiplayer_double_top_out_is_a_draw() -> None:
    engine = make_engine(
        GameMode.MULTIPLAYER,
        players=(GuestPlayer(1), GuestPlayer(2)),
    )
    engine._states[0].alive = False
    engine._states[1].alive = False

    engine._resolve_end_condition()

    result = engine.result
    assert result is not None
    assert result.is_draw
    assert result.winner_name is None
    assert all(player.outcome is MatchOutcome.DRAW for player in result.player_results)


def test_result_is_none_before_finish() -> None:
    engine = make_engine()

    assert engine.result is None


def test_profile_players_are_reflected_in_result() -> None:
    engine = BlockfallGame(BlockfallConfig(), random.Random(7))
    paul = PlayerProfile.create("Paul")
    engine.start(GameMode.SINGLE_PLAYER, (paul,))
    state = engine._states[0]
    for x in range(3, 6):
        state.board.set_cell(x, 0, PieceKind.J)
        state.board.set_cell(x, 1, PieceKind.J)
    state.active = None
    state.alive = True
    engine._spawn(state)
    engine._resolve_end_condition()

    result = engine.result
    assert result is not None
    assert result.player_results[0].player_id == paul.id
    assert result.player_results[0].player_name == "Paul"


def test_start_rejects_wrong_player_count() -> None:
    engine = BlockfallGame()

    with pytest.raises(ValueError, match="requires"):
        engine.start(GameMode.MULTIPLAYER, (GuestPlayer(1),))


def test_config_validates_values() -> None:
    with pytest.raises(ValueError, match="at least 4x8"):
        BlockfallConfig(width=3, height=20)
    with pytest.raises(ValueError, match="Tick rate"):
        BlockfallConfig(tick_rate=0)
    with pytest.raises(ValueError, match="Start level"):
        BlockfallConfig(start_level=0)
    with pytest.raises(ValueError, match="Minimum gravity"):
        BlockfallConfig(base_gravity_ticks=2, min_gravity_ticks=3)


def test_board_clear_rows_drops_remaining_rows() -> None:
    board = Board(4, 4)
    board.set_cell(0, 3, PieceKind.I)
    board.set_cell(1, 2, PieceKind.O)

    board.clear_rows((3,))

    assert board.get(1, 3) is PieceKind.O
    assert board.get(0, 3) is None


def test_board_validation() -> None:
    with pytest.raises(ValueError, match="positive"):
        Board(0, 4)
    with pytest.raises(ValueError, match="cell count"):
        Board(2, 2, [None])


def test_engine_does_not_import_textual() -> None:
    code = "import sys; import asciicade.games.blockfall; assert 'textual' not in sys.modules"
    environment = {**os.environ, "PYTHONPATH": "src"}

    subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        env=environment,
        cwd=os.getcwd(),
    )
