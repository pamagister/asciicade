"""Data structures for the Pong game engine."""

from __future__ import annotations

import math
from dataclasses import dataclass

from asciicade.core.options import GameOptions

_DEFAULT_SCORE_LIMIT = 11
_DEFAULT_DIFFICULTY = "Normal"

_DIFFICULTY_SETTINGS: dict[str, tuple[float, float, float, float]] = {
    # base ball speed, maximum ball speed, CPU paddle speed, CPU dead zone.
    "Easy": (0.40, 0.65, 0.12, 0.75),
    "Normal": (0.50, 0.85, 0.22, 0.50),
    "Hard": (0.60, 1.00, 0.34, 0.25),
}


def clamp(value: float, minimum: float, maximum: float) -> float:
    """Return ``value`` constrained to the inclusive range."""
    return max(minimum, min(maximum, value))


@dataclass(frozen=True, slots=True)
class Point:
    """A position in field units.

    ``x`` is measured in terminal columns and ``y`` in half-row units.
    """

    x: float
    y: float


@dataclass(frozen=True, slots=True)
class PongConfig:
    """Configuration for the Pong engine."""

    width: int = 56
    height: int = 16
    tick_rate: float = 60.0
    score_limit: int = _DEFAULT_SCORE_LIMIT
    difficulty: str = _DEFAULT_DIFFICULTY
    paddle_height: float = 6.0
    paddle_step: float = 1.0
    ball_radius: float = 0.5
    base_ball_speed: float = _DIFFICULTY_SETTINGS[_DEFAULT_DIFFICULTY][0]
    max_ball_speed: float = _DIFFICULTY_SETTINGS[_DEFAULT_DIFFICULTY][1]
    cpu_speed: float = _DIFFICULTY_SETTINGS[_DEFAULT_DIFFICULTY][2]
    cpu_deadzone: float = _DIFFICULTY_SETTINGS[_DEFAULT_DIFFICULTY][3]
    speed_increase_per_hit: float = 0.04
    max_bounce_angle: float = math.radians(60)
    serve_angle: float = math.radians(20)
    serve_delay_ticks: int = 30

    def __post_init__(self) -> None:
        """Validate the configuration."""
        if self.width < 20 or self.height < 8:
            raise ValueError("Pong field must be at least 20x8.")
        if self.tick_rate <= 0:
            raise ValueError("Tick rate must be positive.")
        if self.score_limit <= 0:
            raise ValueError("Score limit must be positive.")
        if self.paddle_height < 2 or self.paddle_height > self.height * 2:
            raise ValueError("Paddle height does not fit in the field.")
        if self.paddle_step <= 0:
            raise ValueError("Paddle step must be positive.")
        if self.ball_radius <= 0:
            raise ValueError("Ball radius must be positive.")
        if self.base_ball_speed <= 0:
            raise ValueError("Base ball speed must be positive.")
        if self.max_ball_speed < self.base_ball_speed:
            raise ValueError("Maximum ball speed must be at least the base speed.")
        if self.cpu_speed <= 0:
            raise ValueError("CPU speed must be positive.")
        if self.cpu_deadzone < 0:
            raise ValueError("CPU dead zone must not be negative.")
        if not 0 < self.max_bounce_angle < math.pi / 2:
            raise ValueError("Maximum bounce angle must be between 0 and 90 degrees.")
        if not 0 <= self.serve_angle < math.pi / 2:
            raise ValueError("Serve angle must be between 0 and 90 degrees.")
        if self.serve_delay_ticks < 0:
            raise ValueError("Serve delay must not be negative.")

    @classmethod
    def for_options(cls, options: GameOptions | None = None) -> PongConfig:
        """Return a configuration resolved from game options."""
        values = options or PongGameOptions.defaults()
        score_limit = _parse_score_limit(values.value_for(PongGameOptions.SCORE_LIMIT_KEY))
        difficulty = _parse_difficulty(values.value_for(PongGameOptions.DIFFICULTY_KEY))
        base_speed, max_speed, cpu_speed, cpu_deadzone = _DIFFICULTY_SETTINGS[difficulty]
        return cls(
            score_limit=score_limit,
            difficulty=difficulty,
            base_ball_speed=base_speed,
            max_ball_speed=max_speed,
            cpu_speed=cpu_speed,
            cpu_deadzone=cpu_deadzone,
        )

    @property
    def field_height(self) -> float:
        """Return the field height in half-row units."""
        return float(self.height * 2)


@dataclass(slots=True)
class Paddle:
    """A player-controlled paddle."""

    player_index: int
    x: float
    y: float
    height: float

    @property
    def top(self) -> float:
        """Return the upper edge of the paddle."""
        return self.y - self.height / 2

    @property
    def bottom(self) -> float:
        """Return the lower edge of the paddle."""
        return self.y + self.height / 2


@dataclass(slots=True)
class Ball:
    """The ball state."""

    x: float
    y: float
    vx: float
    vy: float
    speed: float


@dataclass(frozen=True, slots=True)
class PongPlayerView:
    """An immutable snapshot of one player's paddle and score."""

    player_index: int
    score: int
    y: float
    height: float


@dataclass(frozen=True, slots=True)
class PongSnapshot:
    """An immutable snapshot of the complete Pong state."""

    width: int
    height: int
    players: tuple[PongPlayerView, ...]
    ball: Point
    score_limit: int
    serve_countdown: int
    finished: bool
    winner_index: int | None

    @property
    def serving(self) -> bool:
        """Return whether the ball is waiting to be served."""
        return self.serve_countdown > 0


class PongGameOptions:
    """Resolved option values for Pong."""

    SCORE_LIMIT_KEY = "score_limit"
    DIFFICULTY_KEY = "difficulty"

    @staticmethod
    def defaults() -> GameOptions:
        """Return the default option values for Pong."""
        return GameOptions(
            (
                (PongGameOptions.SCORE_LIMIT_KEY, str(_DEFAULT_SCORE_LIMIT)),
                (PongGameOptions.DIFFICULTY_KEY, _DEFAULT_DIFFICULTY),
            )
        )


def _parse_score_limit(value: str) -> int:
    """Parse a score limit, falling back to the default."""
    try:
        score_limit = int(value)
    except ValueError:
        return _DEFAULT_SCORE_LIMIT
    return score_limit if score_limit > 0 else _DEFAULT_SCORE_LIMIT


def _parse_difficulty(value: str) -> str:
    """Return a supported difficulty, falling back to Normal."""
    return value if value in _DIFFICULTY_SETTINGS else _DEFAULT_DIFFICULTY
