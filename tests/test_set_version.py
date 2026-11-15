"""Tests for the package version setter."""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "set_version.py"

_spec = importlib.util.spec_from_file_location("set_version", SCRIPT)
assert _spec is not None and _spec.loader is not None
set_version = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(set_version)


def test_replace_version_updates_single_line() -> None:
    text = '"""Doc."""\n\n__version__ = "0.1.0"\n'

    result = set_version.replace_version(text, "0.2.1")

    assert result == '"""Doc."""\n\n__version__ = "0.2.1"\n'


def test_replace_version_requires_exactly_one_match() -> None:
    text = '__version__ = "0.1.0"\n__version__ = "0.1.0"\n'

    with pytest.raises(ValueError, match="found 2"):
        set_version.replace_version(text, "0.2.1")


def test_replace_version_rejects_missing_line() -> None:
    with pytest.raises(ValueError, match="found 0"):
        set_version.replace_version('"""Doc."""\n', "0.2.1")
