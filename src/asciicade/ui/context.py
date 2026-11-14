"""Shared dependencies passed to UI screens."""

from __future__ import annotations

from dataclasses import dataclass

from asciicade.core.registry import GameRegistry
from asciicade.persistence.players import PlayerRepository
from asciicade.persistence.results import ResultRepository
from asciicade.persistence.settings import SettingsRepository
from asciicade.ui.audio import AudioPlayer


@dataclass(frozen=True, slots=True)
class AppContext:
    """Application services available to screens."""

    registry: GameRegistry
    players: PlayerRepository
    results: ResultRepository
    settings: SettingsRepository
    audio: AudioPlayer
