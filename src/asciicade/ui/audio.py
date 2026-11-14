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
    """Sound effects shipped with the application."""

    PADDLE_HIT = "click"
    FOOD_EATEN = "collect"
    LINE_CLEAR = "blob"
    MULTI_LINE_CLEAR = "bonus"
    POINT_SCORED = "coin"
    GAME_OVER = "game-over"


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
    try:
        resource = importlib.resources.files("asciicade").joinpath(
            *_SOUND_DIRECTORY,
            f"{effect.value}.mp3",
        )
    except (ModuleNotFoundError, TypeError):
        return None
    path = Path(str(resource))
    return path if path.is_file() else None


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
