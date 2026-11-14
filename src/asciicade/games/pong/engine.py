"""Deterministic Pong game engine."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence

from asciicade.core.game import GameMode
from asciicade.core.input import Direction, InputEvent, direction_for_action
from asciicade.core.options import GameOptions
from asciicade.core.player import Player
from asciicade.core.results import (
    GameResult,
    MatchOutcome,
    PlayerResult,
    make_game_result,
    make_player_result,
)
from asciicade.games.pong.models import (
    Ball,
    Paddle,
    Point,
    PongConfig,
    PongPlayerView,
    PongSnapshot,
    clamp,
)

_MAX_SUBSTEP = 0.4
_MIN_BOUNCE_RATIO = 0.08


class PongEngine:
    """A UI-independent, deterministic Pong engine."""

    def __init__(
        self,
        config: PongConfig | None = None,
        rng: random.Random | None = None,
    ) -> None:
        """Create an engine.

        Args:
            config: Field and physics configuration. Defaults to :class:`PongConfig`.
            rng: Injectable random generator. Defaults to a new generator.
        """
        self.config = config or PongConfig()
        self._rng = rng or random.Random()
        self._players: tuple[Player, ...] = ()
        self._mode = GameMode.SINGLE_PLAYER
        self._paddles: list[Paddle] = []
        self._ball = Ball(self.config.width / 2, self.config.field_height / 2, 0.0, 0.0, 0.0)
        self._scores: list[int] = [0, 0]
        self._finished = False
        self._winner_index: int | None = None
        self._serve_countdown = 0
        self._rally_hits = 0

    @property
    def tick_rate(self) -> float:
        """Return the number of simulation ticks per second."""
        return self.config.tick_rate

    @property
    def is_finished(self) -> bool:
        """Return whether the current session has ended."""
        return self._finished

    @property
    def snapshot(self) -> PongSnapshot:
        """Return an immutable snapshot suitable for rendering."""
        return PongSnapshot(
            width=self.config.width,
            height=self.config.height,
            players=tuple(
                PongPlayerView(
                    player_index=paddle.player_index,
                    score=self._scores[index],
                    y=paddle.y,
                    height=paddle.height,
                )
                for index, paddle in enumerate(self._paddles)
            ),
            ball=Point(self._ball.x, self._ball.y),
            score_limit=self.config.score_limit,
            serve_countdown=self._serve_countdown,
            finished=self._finished,
            winner_index=self._winner_index,
        )

    @property
    def result(self) -> GameResult | None:
        """Return the structured result once the session has ended."""
        if not self._finished or not self._players:
            return None

        player_results: tuple[PlayerResult, ...]
        if self._mode is GameMode.SINGLE_PLAYER:
            human = self._players[0]
            won = self._winner_index == 0
            player_results = (
                make_player_result(
                    human,
                    self._scores[0],
                    MatchOutcome.WIN if won else MatchOutcome.LOSS,
                ),
            )
            return make_game_result(
                "pong",
                self._mode,
                player_results,
                winner_name=human.name if won else None,
            )

        assert self._winner_index is not None
        player_results = tuple(
            make_player_result(
                player,
                self._scores[index],
                MatchOutcome.WIN if index == self._winner_index else MatchOutcome.LOSS,
            )
            for index, player in enumerate(self._players)
        )
        return make_game_result(
            "pong",
            self._mode,
            player_results,
            winner_name=self._players[self._winner_index].name,
        )

    def start(
        self,
        mode: GameMode,
        players: Sequence[Player],
        *,
        options: GameOptions | None = None,
    ) -> None:
        """Initialize a new session.

        Args:
            mode: The game mode.
            players: One player for single-player, two for multiplayer.
            options: Optional resolved game options. Defaults to the game's
                declared option defaults.

        Raises:
            ValueError: If the mode or player count is invalid.
        """
        expected_players = 1 if mode is GameMode.SINGLE_PLAYER else 2
        if mode not in (GameMode.SINGLE_PLAYER, GameMode.MULTIPLAYER):
            raise ValueError(f"Unsupported Pong mode: {mode}")
        if len(players) != expected_players:
            raise ValueError(f"{mode.value} Pong requires {expected_players} player(s).")

        self.config = PongConfig.for_options(options)
        self._mode = mode
        self._players = tuple(players)
        self._paddles = [
            Paddle(1, 1.0, self.config.field_height / 2, self.config.paddle_height),
            Paddle(
                2,
                float(self.config.width - 2),
                self.config.field_height / 2,
                self.config.paddle_height,
            ),
        ]
        self._scores = [0, 0]
        self._finished = False
        self._winner_index = None
        self._serve_countdown = 0
        self._rally_hits = 0
        self._reset_ball(self._rng.randrange(2))

    def handle_input(self, event: InputEvent) -> None:
        """Move a human paddle in response to a normalized input event."""
        if self._finished or event.player is None:
            return
        if self._mode is GameMode.SINGLE_PLAYER and event.player != 1:
            return
        direction = direction_for_action(event.action)
        if direction is None:
            return
        index = event.player - 1
        if not 0 <= index < len(self._paddles):
            return
        delta = -self.config.paddle_step if direction is Direction.UP else self.config.paddle_step
        paddle = self._paddles[index]
        paddle.y = clamp(
            paddle.y + delta,
            paddle.height / 2,
            self.config.field_height - paddle.height / 2,
        )

    def clear_pending(self) -> None:
        """No-op for API compatibility with buffered-input games."""
        return

    def tick(self) -> None:
        """Advance the game by one deterministic tick."""
        if self._finished or not self._paddles:
            return

        if self._mode is GameMode.SINGLE_PLAYER:
            self._update_computer()

        if self._serve_countdown > 0:
            self._serve_countdown -= 1
            return

        self._move_ball()

    def _update_computer(self) -> None:
        """Move the computer paddle toward the ball with a capped speed."""
        paddle = self._paddles[1]
        ball = self._ball
        target = ball.y if ball.vx > 0 else self.config.field_height / 2
        difference = target - paddle.y
        if abs(difference) <= self.config.cpu_deadzone:
            return
        step = math.copysign(min(abs(difference), self.config.cpu_speed), difference)
        paddle.y = clamp(
            paddle.y + step,
            paddle.height / 2,
            self.config.field_height - paddle.height / 2,
        )

    def _move_ball(self) -> None:
        """Move the ball with substeps and resolve collisions."""
        ball = self._ball
        distance = max(abs(ball.vx), abs(ball.vy))
        steps = max(1, math.ceil(distance / _MAX_SUBSTEP))

        for _ in range(steps):
            previous_x = ball.x
            ball.x += ball.vx / steps
            ball.y += ball.vy / steps

            if ball.y - self.config.ball_radius < 0:
                ball.y = self.config.ball_radius
                ball.vy = abs(ball.vy)
            elif ball.y + self.config.ball_radius > self.config.field_height:
                ball.y = self.config.field_height - self.config.ball_radius
                ball.vy = -abs(ball.vy)

            if ball.vx < 0:
                self._collide_with_left_paddle(previous_x)
            elif ball.vx > 0:
                self._collide_with_right_paddle(previous_x)

            if ball.x + self.config.ball_radius < 0:
                self._score_point(1)
                return
            if ball.x - self.config.ball_radius > self.config.width:
                self._score_point(0)
                return

    def _collide_with_left_paddle(self, previous_x: float) -> None:
        """Reflect the ball when it crosses the left paddle."""
        paddle = self._paddles[0]
        plane = paddle.x + 1.0 + self.config.ball_radius
        ball = self._ball
        if previous_x < plane or ball.x > plane:
            return
        if not self._paddle_contains(paddle, ball.y):
            return
        ball.x = plane
        self._reflect(paddle, 1.0)

    def _collide_with_right_paddle(self, previous_x: float) -> None:
        """Reflect the ball when it crosses the right paddle."""
        paddle = self._paddles[1]
        plane = paddle.x - self.config.ball_radius
        ball = self._ball
        if previous_x > plane or ball.x < plane:
            return
        if not self._paddle_contains(paddle, ball.y):
            return
        ball.x = plane
        self._reflect(paddle, -1.0)

    def _paddle_contains(self, paddle: Paddle, ball_y: float) -> bool:
        """Return whether the ball overlaps the paddle vertically."""
        top = paddle.top - self.config.ball_radius
        bottom = paddle.bottom + self.config.ball_radius
        return top <= ball_y <= bottom

    def _reflect(self, paddle: Paddle, horizontal_direction: float) -> None:
        """Reflect the ball based on the paddle impact position."""
        ball = self._ball
        reach = paddle.height / 2 + self.config.ball_radius
        offset = clamp((ball.y - paddle.y) / reach, -1.0, 1.0)
        angle = offset * self.config.max_bounce_angle
        minimum_angle = self.config.max_bounce_angle * _MIN_BOUNCE_RATIO
        if abs(angle) < minimum_angle:
            sign = -1.0 if offset < 0 else 1.0
            angle = sign * minimum_angle

        ball.speed = min(
            ball.speed * (1.0 + self.config.speed_increase_per_hit),
            self.config.max_ball_speed,
        )
        ball.vx = horizontal_direction * ball.speed * math.cos(angle)
        ball.vy = ball.speed * math.sin(angle)
        self._rally_hits += 1

    def _score_point(self, scorer_index: int) -> None:
        """Award a point and either finish or reset for the next serve."""
        self._scores[scorer_index] += 1
        if self._scores[scorer_index] >= self.config.score_limit:
            self._finish(scorer_index)
            return
        self._reset_ball(1 - scorer_index)

    def _reset_ball(self, toward_index: int) -> None:
        """Reset the ball to the center and prepare a serve."""
        ball = self._ball
        ball.x = self.config.width / 2
        ball.y = self.config.field_height / 2
        ball.speed = self.config.base_ball_speed
        angle = self._rng.uniform(-self.config.serve_angle, self.config.serve_angle)
        direction = -1.0 if toward_index == 0 else 1.0
        ball.vx = direction * ball.speed * math.cos(angle)
        ball.vy = ball.speed * math.sin(angle)
        self._serve_countdown = self.config.serve_delay_ticks
        self._rally_hits = 0

    def _finish(self, winner_index: int) -> None:
        """Mark the session as finished."""
        self._finished = True
        self._winner_index = winner_index
        self._ball.vx = 0.0
        self._ball.vy = 0.0
        self._ball.speed = 0.0
