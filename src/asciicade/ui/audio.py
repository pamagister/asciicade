"""Optional sound effects for the terminal user interface."""

from __future__ import annotations

import importlib.resources
import os
import shutil
import subprocess
from collections.abc import Callable, Sequence
from enum import StrEnum
from pathlib import Path
from typing import Protocol

_SOUND_DIRECTORY = ("assets", "sounds")
_DISABLED_ENV_VALUES = {"0", "false", "no", "off"}
_FFPLAY_COMMAND = ("ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet")
_FALLBACK_PLAYERS = ("paplay", "pw-play")


class SoundEffect(StrEnum):
    """Semantic sound events used by the user interface."""

    PADDLE_HIT = "paddle-hit"
    FOOD_EATEN = "food-eaten"
    LINE_CLEAR = "line-clear"
    MULTI_LINE_CLEAR = "multi-line-clear"
    POINT_SCORED = "point-scored"
    GAME_OVER = "game-over"
    UI_MOVE = "ui-move"
    UI_SELECT = "ui-select"
    UI_TOGGLE = "ui-toggle"


_SOUND_FILES: dict[SoundEffect, str] = {
    # Pong paddle hits and single-line Blockfall clears share one effect.
    SoundEffect.PADDLE_HIT: "arcade-blob.mp3",
    SoundEffect.FOOD_EATEN: "arcade-collect.mp3",
    SoundEffect.LINE_CLEAR: "arcade-blob.mp3",
    SoundEffect.MULTI_LINE_CLEAR: "arcade-bonus.mp3",
    SoundEffect.POINT_SCORED: "arcade-coin.mp3",
    SoundEffect.GAME_OVER: "arcade-game-over.mp3",
    SoundEffect.UI_MOVE: "ui-click.mp3",
    SoundEffect.UI_SELECT: "ui-menu-select.mp3",
    SoundEffect.UI_TOGGLE: "ui-toggle-switch.mp3",
}


class AudioProcess(Protocol):
    """Minimal process interface used to avoid overlapping playback."""

    def poll(self) -> int | None:
        """Return the exit status, or ``None`` while the process is running."""


class AudioPlayer:
    """Play short sound effects through a supported system audio player.

    Audio is optional. When playback is disabled or no supported player is
    available, calls are ignored so the game can continue silently.
    """

    def __init__(
        self,
        *,
        enabled: bool | None = None,
        command: Sequence[str] | None = None,
        runner: Callable[..., AudioProcess] = subprocess.Popen,
    ) -> None:
        """Create a player.

        Args:
            enabled: Force playback on or off. Defaults to the
                ``ASCIICADE_SOUND`` environment variable.
            command: Audio player command override, mainly for tests.
            runner: Process launcher override, mainly for tests.
        """
        self._enabled = _sound_enabled_by_environment() if enabled is None else enabled
        self._command = tuple(command) if command is not None else _find_player()
        self._runner = runner
        self._processes: dict[SoundEffect, AudioProcess] = {}

    @property
    def enabled(self) -> bool:
        """Return whether playback is enabled."""
        return self._enabled

    def play(self, effect: SoundEffect) -> None:
        """Start playback for a sound effect.

        Repeated calls for the same effect are ignored while its previous
        playback is still running.
        """
        if not self._enabled or not self._command:
            return

        path = sound_path(effect)
        if path is None:
            return

        process = self._processes.get(effect)
        if process is not None and process.poll() is None:
            return

        try:
            self._processes[effect] = self._runner(
                [*self._command, str(path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
            )
        except OSError:
            self._command = ()


def sound_path(effect: SoundEffect) -> Path | None:
    """Return the packaged file for a sound effect, if it exists."""
    filename = _SOUND_FILES[effect]
    try:
        resource = importlib.resources.files("asciicade").joinpath(
            *_SOUND_DIRECTORY,
            filename,
        )
    except (ModuleNotFoundError, TypeError):
        return None
    path = Path(str(resource))
    return path if path.is_file() else None


def play_ui_sound(app: object, effect: SoundEffect) -> None:
    """Play a UI sound on an application that exposes ``play_ui_sound``."""
    player = getattr(app, "play_ui_sound", None)
    if callable(player):
        player(effect)


def _sound_enabled_by_environment() -> bool:
    """Return whether the environment enables sound playback."""
    value = os.environ.get("ASCIICADE_SOUND", "on").strip().lower()
    return value not in _DISABLED_ENV_VALUES


def _find_player() -> tuple[str, ...] | None:
    """Return a supported system audio player, if one is installed."""
    if shutil.which("ffplay"):
        return _FFPLAY_COMMAND
    for command in _FALLBACK_PLAYERS:
        if shutil.which(command):
            return (command,)
    return None
