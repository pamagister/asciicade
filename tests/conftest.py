"""Shared test fixtures."""

from __future__ import annotations

import pytest


@pytest.fixture(autouse=True)
def _disable_sound_by_default(monkeypatch: pytest.MonkeyPatch) -> None:
    """Prevent gameplay tests from starting real audio players."""
    monkeypatch.setenv("ASCIICADE_SOUND", "off")
