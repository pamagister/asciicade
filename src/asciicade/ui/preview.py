"""Headless gameplay preview rendering for documentation."""

from __future__ import annotations

import random
from typing import Any, cast

from asciicade.core.game import GameMode
from asciicade.core.player import GuestPlayer
from asciicade.core.registry import GameRegistration
from asciicade.ui.context import AppContext
from asciicade.ui.screens.game_screen_factory import (
    GameScreenNotFoundError,
    create_game_screen,
)

PREVIEW_SEED = 0x5EED
PREVIEW_TICKS = 8


def render_game_preview(
    registration: GameRegistration,
    *,
    seed: int = PREVIEW_SEED,
    ticks: int = PREVIEW_TICKS,
) -> str | None:
    """Render a deterministic single-player gameplay preview as plain text.

    The preview uses the game's real screen renderer, but builds the game with a
    seeded random generator and advances it by a fixed number of ticks. It
    returns ``None`` when the game has no registered screen or cannot be built
    without a full application context.
    """
    metadata = registration.metadata
    mode = GameMode.SINGLE_PLAYER
    players = (GuestPlayer(1),)
    options = metadata.options.defaults() if metadata.options is not None else None

    game = _create_seeded_game(registration, seed)
    if not hasattr(game, "start") or not hasattr(game, "tick"):
        return None
    game.start(mode, players, options=options)
    for _ in range(ticks):
        game.tick()

    try:
        screen = create_game_screen(
            cast(AppContext, object()),
            registration,
            mode,
            players,
            options=options,
        )
    except GameScreenNotFoundError:
        return None

    render_arena = getattr(screen, "render_arena", None)
    if render_arena is None:
        return None

    # The screen normally builds its game in ``on_mount``. For a headless
    # preview we inject the already-advanced game instead of starting a timer.
    screen._game = game  # type: ignore[attr-defined]
    screen._paused = False  # type: ignore[attr-defined]
    screen._finished = False  # type: ignore[attr-defined]
    rendered = render_arena()
    plain = getattr(rendered, "plain", str(rendered))
    lines = [line.rstrip() for line in plain.splitlines()]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()
    return "\n".join(lines)


def _create_seeded_game(registration: GameRegistration, seed: int) -> Any:
    """Create a game instance with a seeded random generator when supported."""
    factory = cast(Any, registration.factory)
    try:
        return factory(rng=random.Random(seed))
    except TypeError:
        return factory()
