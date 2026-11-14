"""Tests for the deterministic Pong engine."""

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
from asciicade.games.pong import Ball, PongConfig, PongGame


def make_engine(
    mode: GameMode = GameMode.SINGLE_PLAYER,
    *,
    seed: int = 1234,
    config: PongConfig | None = None,
    players: tuple[GuestPlayer, ...] | None = None,
    options: GameOptions | None = None,
) -> PongGame:
    """Create a started engine for tests."""
    engine = PongGame(config or PongConfig(), random.Random(seed))
    selected = players or (GuestPlayer(1),)
    engine.start(mode, selected, options=options)
    return engine


def place_ball(
    engine: PongGame,
    *,
    x: float,
    y: float,
    vx: float,
    vy: float,
    speed: float,
) -> None:
    """Replace the ball state and start play immediately."""
    engine._ball = Ball(x, y, vx, vy, speed)
    engine._serve_countdown = 0


def test_initial_state() -> None:
    engine = make_engine()
    snapshot = engine.snapshot

    assert snapshot.width == 56
    assert snapshot.height == 16
    assert [player.score for player in snapshot.players] == [0, 0]
    assert snapshot.players[0].y == 16
    assert snapshot.players[1].y == 16
    assert snapshot.ball.x == 28
    assert snapshot.ball.y == 16
    assert snapshot.serving
    assert snapshot.serve_countdown == 30


def test_serve_delay_holds_ball_before_play() -> None:
    engine = make_engine()

    for _ in range(30):
        engine.tick()

    assert engine.snapshot.ball.x == 28
    assert not engine.snapshot.serving

    engine.tick()
    assert engine.snapshot.ball.x != 28


def test_paddle_input_moves_only_the_requested_player() -> None:
    engine = make_engine(
        GameMode.MULTIPLAYER,
        players=(GuestPlayer(1), GuestPlayer(2)),
    )

    engine.handle_input(InputEvent(InputAction.UP, player=1))
    engine.handle_input(InputEvent(InputAction.UP, player=2))

    assert engine.snapshot.players[0].y == 15
    assert engine.snapshot.players[1].y == 15

    engine.handle_input(InputEvent(InputAction.DOWN, player=2))
    assert engine.snapshot.players[0].y == 15
    assert engine.snapshot.players[1].y == 16


def test_single_player_ignores_cpu_paddle_input() -> None:
    engine = make_engine()

    engine.handle_input(InputEvent(InputAction.UP, player=2))

    assert engine.snapshot.players[1].y == 16


def test_paddles_clamp_inside_the_field() -> None:
    engine = make_engine()

    for _ in range(30):
        engine.handle_input(InputEvent(InputAction.UP, player=1))
    for _ in range(60):
        engine.handle_input(InputEvent(InputAction.DOWN, player=1))

    paddle = engine.snapshot.players[0]
    assert paddle.y == engine.config.field_height - paddle.height / 2


def test_ball_bounces_off_the_top_wall() -> None:
    engine = make_engine()
    place_ball(engine, x=10, y=0.6, vx=0.1, vy=-0.2, speed=0.223606797749979)

    engine.tick()

    assert engine.snapshot.ball.y >= engine.config.ball_radius
    assert engine._ball.vy > 0


def test_ball_bounces_off_the_bottom_wall() -> None:
    engine = make_engine()
    place_ball(
        engine,
        x=10,
        y=engine.config.field_height - 0.6,
        vx=0.1,
        vy=0.2,
        speed=0.223606797749979,
    )

    engine.tick()

    assert engine.snapshot.ball.y <= engine.config.field_height - engine.config.ball_radius
    assert engine._ball.vy < 0


def test_paddle_reflection_depends_on_impact_position() -> None:
    center = make_engine()
    edge = make_engine()

    place_ball(center, x=2.6, y=16, vx=-0.5, vy=0, speed=0.5)
    place_ball(edge, x=2.6, y=18.5, vx=-0.5, vy=0, speed=0.5)

    center.tick()
    edge.tick()

    assert center._ball.vx > 0
    assert edge._ball.vx > 0
    assert abs(edge._ball.vy) > abs(center._ball.vy)


def test_paddle_reflection_reverses_horizontal_direction() -> None:
    engine = make_engine()

    place_ball(engine, x=2.6, y=16, vx=-0.5, vy=0, speed=0.5)
    engine.tick()

    assert engine._ball.vx > 0
    assert engine._ball.x >= 2.5


def test_ball_speed_is_capped() -> None:
    engine = make_engine()

    place_ball(
        engine,
        x=2.6,
        y=16,
        vx=-0.5,
        vy=0,
        speed=engine.config.max_ball_speed,
    )
    engine.tick()

    assert engine._ball.speed <= engine.config.max_ball_speed


def test_ball_scoring_resets_for_next_serve() -> None:
    engine = make_engine()

    place_ball(engine, x=-1, y=16, vx=-0.5, vy=0, speed=0.5)
    engine.tick()

    assert engine.snapshot.players[1].score == 1
    assert engine.snapshot.players[0].score == 0
    assert engine.snapshot.ball.x == 28
    assert engine.snapshot.serving
    assert engine._ball.vx < 0


def test_first_to_score_limit_finishes_single_player_match() -> None:
    engine = make_engine(options=GameOptions((("score_limit", "1"), ("difficulty", "Normal"))))

    place_ball(engine, x=57, y=16, vx=0.5, vy=0, speed=0.5)
    engine.tick()

    assert engine.is_finished
    result = engine.result
    assert result is not None
    assert result.winner_name == "Guest 1"
    assert result.player_results[0].outcome is MatchOutcome.WIN
    assert result.player_results[0].score == 1


def test_cpu_win_is_a_loss_for_the_human_result() -> None:
    engine = make_engine(options=GameOptions((("score_limit", "1"), ("difficulty", "Normal"))))

    place_ball(engine, x=-1, y=16, vx=-0.5, vy=0, speed=0.5)
    engine.tick()

    result = engine.result
    assert result is not None
    assert result.winner_name is None
    assert result.player_results[0].outcome is MatchOutcome.LOSS


def test_multiplayer_result_records_winner() -> None:
    engine = make_engine(
        GameMode.MULTIPLAYER,
        players=(GuestPlayer(1), GuestPlayer(2)),
        options=GameOptions((("score_limit", "1"), ("difficulty", "Normal"))),
    )

    place_ball(engine, x=-1, y=16, vx=-0.5, vy=0, speed=0.5)
    engine.tick()

    result = engine.result
    assert result is not None
    assert result.winner_name == "Guest 2"
    assert result.player_results[0].outcome is MatchOutcome.LOSS
    assert result.player_results[1].outcome is MatchOutcome.WIN
    assert result.player_results[1].score == 1


def test_computer_paddle_tracks_the_ball_and_recenters() -> None:
    engine = make_engine()
    place_ball(engine, x=20, y=24, vx=0.1, vy=0, speed=0.1)

    engine.tick()
    assert engine.snapshot.players[1].y > 16

    place_ball(engine, x=20, y=24, vx=-0.1, vy=0, speed=0.1)
    engine.tick()
    assert engine.snapshot.players[1].y < 24


def test_computer_paddle_stays_inside_the_field() -> None:
    engine = make_engine()
    place_ball(engine, x=20, y=100, vx=0.1, vy=0, speed=0.1)

    for _ in range(100):
        engine.tick()

    paddle = engine.snapshot.players[1]
    assert paddle.y <= engine.config.field_height - paddle.height / 2


def test_same_seed_produces_the_same_sequence() -> None:
    first = make_engine(seed=99)
    second = make_engine(seed=99)

    for _ in range(100):
        first.tick()
        second.tick()

    assert first.snapshot == second.snapshot


def test_profile_players_are_reflected_in_result() -> None:
    engine = PongGame(PongConfig(), random.Random(7))
    paul = PlayerProfile.create("Paul")
    engine.start(
        GameMode.SINGLE_PLAYER,
        (paul,),
        options=GameOptions((("score_limit", "1"), ("difficulty", "Normal"))),
    )

    place_ball(engine, x=57, y=16, vx=0.5, vy=0, speed=0.5)
    engine.tick()

    result = engine.result
    assert result is not None
    assert result.player_results[0].player_id == paul.id
    assert result.player_results[0].player_name == "Paul"


def test_start_rejects_wrong_player_count() -> None:
    engine = PongGame()

    with pytest.raises(ValueError, match="requires"):
        engine.start(GameMode.MULTIPLAYER, (GuestPlayer(1),))


def test_config_validates_dimensions_and_speeds() -> None:
    with pytest.raises(ValueError, match="at least 20x8"):
        PongConfig(width=10, height=8)
    with pytest.raises(ValueError, match="positive"):
        PongConfig(tick_rate=0)
    with pytest.raises(ValueError, match="Score limit"):
        PongConfig(score_limit=0)
    with pytest.raises(ValueError, match="Maximum ball speed"):
        PongConfig(base_ball_speed=2.0, max_ball_speed=1.0)


def test_options_resolve_score_limit_and_difficulty() -> None:
    config = PongConfig.for_options(GameOptions((("score_limit", "5"), ("difficulty", "Hard"))))

    assert config.score_limit == 5
    assert config.difficulty == "Hard"
    assert config.cpu_speed > PongConfig.for_options().cpu_speed


def test_invalid_options_fall_back_to_defaults() -> None:
    config = PongConfig.for_options(
        GameOptions((("score_limit", "invalid"), ("difficulty", "Impossible")))
    )

    assert config.score_limit == 11
    assert config.difficulty == "Normal"


def test_engine_does_not_import_textual() -> None:
    code = "import sys; import asciicade.games.pong; assert 'textual' not in sys.modules"
    environment = {**os.environ, "PYTHONPATH": "src"}

    subprocess.run(
        [sys.executable, "-c", code],
        check=True,
        env=environment,
        cwd=os.getcwd(),
    )
