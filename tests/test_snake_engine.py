"""Tests for the deterministic Snake engine."""

from __future__ import annotations

import os
import random
import subprocess
import sys

import pytest

from asciicade.core.game import GameMode
from asciicade.core.input import Direction, InputAction, InputEvent
from asciicade.core.options import GameOptions
from asciicade.core.player import GuestPlayer, PlayerProfile
from asciicade.core.results import MatchOutcome
from asciicade.games.snake import (
    Position,
    SnakeConfig,
    SnakeGame,
    occupied_cells,
)


def make_engine(
    mode: GameMode = GameMode.SINGLE_PLAYER,
    *,
    seed: int = 1234,
    config: SnakeConfig | None = None,
    players: tuple[GuestPlayer, ...] | None = None,
    options: GameOptions | None = None,
) -> SnakeGame:
    """Create a started engine for tests."""
    engine = SnakeGame(config or SnakeConfig(), random.Random(seed))
    selected = players or (GuestPlayer(1),)
    engine.start(mode, selected, options=options)
    return engine


def place_body(
    engine: SnakeGame, index: int, body: tuple[Position, ...], direction: Direction
) -> None:
    """Replace a snake body and direction for a collision scenario."""
    snake = engine._snakes[index]
    snake.body = body
    snake.direction = direction
    snake.pending.clear()
    snake.alive = True


def test_single_player_initial_state() -> None:
    engine = make_engine()
    snapshot = engine.snapshot

    assert snapshot.width == 30
    assert snapshot.height == 15
    assert len(snapshot.snakes) == 1
    assert snapshot.snakes[0].body == (
        Position(7, 7),
        Position(6, 7),
        Position(5, 7),
    )
    assert snapshot.snakes[0].direction is Direction.RIGHT
    assert snapshot.food is not None
    assert snapshot.food not in occupied_cells(engine._snakes)


def test_tick_moves_and_drops_tail() -> None:
    engine = make_engine()
    engine._food = Position(0, 0)

    engine.tick()

    assert engine.snapshot.snakes[0].body == (
        Position(8, 7),
        Position(7, 7),
        Position(6, 7),
    )
    assert engine.snapshot.snakes[0].score == 0


def test_eating_grows_and_scores() -> None:
    engine = make_engine()
    engine._food = Position(8, 7)

    engine.tick()

    snake = engine.snapshot.snakes[0]
    assert snake.body == (
        Position(8, 7),
        Position(7, 7),
        Position(6, 7),
        Position(5, 7),
    )
    assert snake.score == 1
    assert engine.snapshot.food is not None
    assert engine.snapshot.food not in occupied_cells(engine._snakes)


def test_wall_collision_ends_single_player_game() -> None:
    engine = make_engine()
    engine._food = Position(0, 0)

    for _ in range(30):
        engine.tick()
        if engine.is_finished:
            break

    assert engine.is_finished
    result = engine.result
    assert result is not None
    assert result.winner_name is None
    assert result.player_results[0].outcome is MatchOutcome.LOSS


def test_self_collision_ends_game() -> None:
    engine = make_engine(config=SnakeConfig(initial_length=5))
    engine._food = Position(0, 0)

    engine.handle_input(InputEvent(InputAction.UP, player=1))
    engine.tick()
    engine.handle_input(InputEvent(InputAction.LEFT, player=1))
    engine.tick()
    engine.handle_input(InputEvent(InputAction.DOWN, player=1))
    engine.tick()

    assert engine.is_finished
    assert engine.result is not None
    assert engine.result.player_results[0].outcome is MatchOutcome.LOSS


def test_reverse_direction_is_rejected() -> None:
    engine = make_engine()
    engine._food = Position(0, 0)

    engine.handle_input(InputEvent(InputAction.LEFT, player=1))
    engine.tick()

    assert engine.snapshot.snakes[0].direction is Direction.RIGHT
    assert engine.snapshot.snakes[0].body[0] == Position(8, 7)


def test_direction_buffer_applies_one_per_tick() -> None:
    engine = make_engine()
    engine._food = Position(0, 0)

    engine.handle_input(InputEvent(InputAction.UP, player=1))
    engine.handle_input(InputEvent(InputAction.LEFT, player=1))

    engine.tick()
    assert engine.snapshot.snakes[0].direction is Direction.UP
    assert engine.snapshot.snakes[0].body[0] == Position(7, 6)

    engine.tick()
    assert engine.snapshot.snakes[0].direction is Direction.LEFT
    assert engine.snapshot.snakes[0].body[0] == Position(6, 6)


def test_tail_chase_is_allowed() -> None:
    engine = make_engine()
    engine._food = Position(0, 0)
    place_body(
        engine,
        0,
        (Position(5, 5), Position(4, 5), Position(4, 6), Position(5, 6)),
        Direction.DOWN,
    )

    engine.tick()

    snake = engine.snapshot.snakes[0]
    assert snake.alive
    assert snake.body == (
        Position(5, 6),
        Position(5, 5),
        Position(4, 5),
        Position(4, 6),
    )


def test_food_never_spawns_on_a_snake() -> None:
    engine = make_engine()
    engine._food = Position(8, 7)

    engine.tick()

    assert engine.snapshot.food is not None
    assert engine.snapshot.food not in occupied_cells(engine._snakes)


def test_same_seed_produces_same_food() -> None:
    first = make_engine(seed=99)
    second = make_engine(seed=99)

    assert first.snapshot.food == second.snapshot.food


def test_multiplayer_initial_state_has_two_snakes() -> None:
    engine = make_engine(
        GameMode.MULTIPLAYER,
        players=(GuestPlayer(1), GuestPlayer(2)),
    )
    snapshot = engine.snapshot

    assert len(snapshot.snakes) == 2
    assert snapshot.snakes[0].player_index == 1
    assert snapshot.snakes[1].player_index == 2
    assert snapshot.snakes[0].direction is Direction.RIGHT
    assert snapshot.snakes[1].direction is Direction.LEFT
    assert snapshot.snakes[0].body[0] != snapshot.snakes[1].body[0]


def test_multiplayer_last_survivor_wins() -> None:
    engine = make_engine(
        GameMode.MULTIPLAYER,
        players=(GuestPlayer(1), GuestPlayer(2)),
    )
    engine._food = Position(0, 0)
    place_body(engine, 1, (Position(0, 9),), Direction.LEFT)

    engine.tick()

    assert engine.is_finished
    result = engine.result
    assert result is not None
    assert result.winner_name == "Guest 1"
    assert result.player_results[0].outcome is MatchOutcome.WIN
    assert result.player_results[1].outcome is MatchOutcome.LOSS


def test_multiplayer_head_on_collision_is_a_draw() -> None:
    engine = make_engine(
        GameMode.MULTIPLAYER,
        players=(GuestPlayer(1), GuestPlayer(2)),
    )
    engine._food = Position(0, 0)
    place_body(engine, 0, (Position(5, 5),), Direction.RIGHT)
    place_body(engine, 1, (Position(7, 5),), Direction.LEFT)

    engine.tick()

    assert engine.is_finished
    result = engine.result
    assert result is not None
    assert result.is_draw
    assert result.winner_name is None
    assert all(player.outcome is MatchOutcome.DRAW for player in result.player_results)


def test_multiplayer_collision_with_other_snake_body_eliminates_player() -> None:
    engine = make_engine(
        GameMode.MULTIPLAYER,
        players=(GuestPlayer(1), GuestPlayer(2)),
    )
    engine._food = Position(0, 0)
    place_body(engine, 0, (Position(5, 5),), Direction.RIGHT)
    place_body(
        engine,
        1,
        (
            Position(9, 5),
            Position(8, 5),
            Position(7, 5),
            Position(6, 5),
            Position(4, 5),
        ),
        Direction.RIGHT,
    )

    engine.tick()

    assert engine.is_finished
    result = engine.result
    assert result is not None
    assert result.winner_name == "Guest 2"
    assert result.player_results[0].outcome is MatchOutcome.LOSS


def test_multiplayer_may_follow_other_snakes_vacating_tail() -> None:
    engine = make_engine(
        GameMode.MULTIPLAYER,
        players=(GuestPlayer(1), GuestPlayer(2)),
    )
    engine._food = Position(0, 0)
    place_body(engine, 0, (Position(5, 5),), Direction.RIGHT)
    place_body(
        engine,
        1,
        (Position(9, 5), Position(8, 5), Position(7, 5), Position(6, 5)),
        Direction.RIGHT,
    )

    # Player 2 moves first in the same tick; its tail at (6, 5) vacates.
    engine.tick()

    assert not engine.is_finished
    assert engine.snapshot.snakes[0].alive
    assert engine.snapshot.snakes[1].alive


def test_result_is_none_before_finish() -> None:
    engine = make_engine()

    assert engine.result is None


def test_profile_players_are_reflected_in_result() -> None:
    engine = SnakeGame(SnakeConfig(), random.Random(7))
    paul = PlayerProfile.create("Paul")
    engine.start(GameMode.SINGLE_PLAYER, (paul,))
    engine._food = Position(0, 0)

    for _ in range(30):
        engine.tick()
        if engine.is_finished:
            break

    result = engine.result
    assert result is not None
    assert result.player_results[0].player_id == paul.id
    assert result.player_results[0].player_name == "Paul"


def test_start_rejects_wrong_player_count() -> None:
    engine = SnakeGame()

    with pytest.raises(ValueError, match="requires"):
        engine.start(GameMode.MULTIPLAYER, (GuestPlayer(1),))


def test_config_validates_dimensions_and_length() -> None:
    with pytest.raises(ValueError, match="at least 10x8"):
        SnakeConfig(width=5, height=8)
    with pytest.raises(ValueError, match="at least 2"):
        SnakeConfig(initial_length=1)
    with pytest.raises(ValueError, match="does not fit"):
        SnakeConfig(width=10, height=10, initial_length=10)
    with pytest.raises(ValueError, match="positive"):
        SnakeConfig(tick_rate=0)


def test_difficulty_sets_tick_rate() -> None:
    """Difficulty options change the engine tick rate."""
    easy = make_engine(options=GameOptions((("difficulty", "Easy"), ("wrap_walls", "off"))))
    medium = make_engine(options=GameOptions((("difficulty", "Medium"), ("wrap_walls", "off"))))
    hard = make_engine(options=GameOptions((("difficulty", "Hard"), ("wrap_walls", "off"))))

    assert easy.config.tick_rate == 5.0
    assert medium.config.tick_rate == 8.0
    assert hard.config.tick_rate == 12.0


def test_difficulty_defaults_to_medium() -> None:
    """Without options, the engine uses the Medium tick rate."""
    engine = make_engine()
    assert engine.config.tick_rate == 8.0


def test_wrap_walls_snake_reappears_on_opposite_side() -> None:
    """With wrap walls enabled, the snake leaves one side and re-enters on the other."""
    engine = make_engine(options=GameOptions((("difficulty", "Medium"), ("wrap_walls", "on"))))
    assert engine.config.wrap_walls is True

    # Move the head to the left wall and head leftwards.
    snake = engine._snakes[0]
    snake.body = (Position(0, 7), Position(1, 7), Position(2, 7))
    snake.direction = Direction.LEFT
    snake.pending.clear()

    engine.tick()

    head = engine.snapshot.snakes[0].body[0]
    assert head == Position(engine.arena.width - 1, 7)
    assert engine.snapshot.snakes[0].alive


def test_wrap_walls_off_snake_crashes_into_wall() -> None:
    """With wrap walls disabled, leaving the arena ends the game."""
    engine = make_engine(options=GameOptions((("difficulty", "Medium"), ("wrap_walls", "off"))))
    assert engine.config.wrap_walls is False

    snake = engine._snakes[0]
    snake.body = (Position(0, 7), Position(1, 7), Position(2, 7))
    snake.direction = Direction.LEFT
    snake.pending.clear()

    engine.tick()

    assert engine.is_finished
    assert not engine.snapshot.snakes[0].alive


def test_engine_does_not_import_textual() -> None:
    code = "import sys; import asciicade.games.snake; assert 'textual' not in sys.modules"
    environment = {**os.environ, "PYTHONPATH": "src"}

    subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        env=environment,
        cwd=os.getcwd(),
    )
