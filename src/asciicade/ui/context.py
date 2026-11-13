"""Shared dependencies passed to UI screens."""

from __future__ import annotations

from dataclasses import dataclass

from asciicade.core.registry import GameRegistry
from asciicade.persistence.players import PlayerRepository
from asciicade.persistence.results import ResultRepository


@dataclass(frozen=True, slots=True)
class AppContext:
    """Application services available to screens."""

    registry: GameRegistry
    players: PlayerRepository
    results: ResultRepository
