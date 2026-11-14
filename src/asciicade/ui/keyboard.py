"""Keyboard helpers for games that need key-release events.

Textual does not expose key-release events. The Kitty keyboard protocol can
report them, so this module enables that protocol and translates release
sequences into ``<key>_release`` key events for games that need hold-to-move
controls.
"""

from __future__ import annotations

from functools import lru_cache

from textual import events
from textual._keyboard_protocol import FUNCTIONAL_KEYS
from textual._xterm_parser import XTermParser, _re_extended_key
from textual.drivers.linux_driver import LinuxDriver
from textual.keys import _character_to_key

_KITTY_REPORT_EVENT_TYPES = 0b00000010
_KITTY_PROTOCOL_FLAGS = 0b00000001 | _KITTY_REPORT_EVENT_TYPES | 0b00001000 | 0b00010000


def _kitty_sequence_parts(sequence: str) -> tuple[list[str], str, str | None] | None:
    """Split a Kitty key sequence into parts, suffix and event type."""
    match = _re_extended_key.fullmatch(sequence)
    if match is None:
        return None
    codes, end = match.groups(default="")
    parts = codes.split(";")
    event_type = None
    if len(parts) >= 2 and ":" in parts[1]:
        event_type = parts[1].split(":", 1)[1]
    return parts, end, event_type


def _release_key_name(parts: list[str], end: str) -> str | None:
    """Return the base key name for a Kitty key-release sequence."""
    codepoint = int(parts[0] or "1")
    key = FUNCTIONAL_KEYS.get(f"{codepoint}{end}", "")
    if not key:
        key = _character_to_key(chr(codepoint))
    return key


class ReleaseXTermParser(XTermParser):
    """XTerm parser that emits ``<key>_release`` events."""

    @lru_cache(maxsize=1024)  # noqa: B019 - parser lifetime matches the app.
    def _parse_extended_key(self, sequence: str) -> list[events.Key] | None:
        """Parse a Kitty key sequence, including release events."""
        parsed = _kitty_sequence_parts(sequence)
        if parsed is not None:
            parts, end, event_type = parsed
            if event_type == "3":
                release_key = _release_key_name(parts, end)
                if release_key is not None:
                    return [events.Key(f"{release_key}_release", None)]
            elif event_type in ("1", "2"):
                # Textual's parser expects the legacy modifier field without
                # the Kitty event-type suffix.
                parts[1] = parts[1].split(":", 1)[0]
                sequence = f"\x1b[{';'.join(parts)}{end}"
        return super()._parse_extended_key(sequence)


class AsciicadeLinuxDriver(LinuxDriver):
    """Linux driver with Kitty key-release reporting enabled."""

    def start_application_mode(self) -> None:
        """Start the driver and request key-release events."""
        import textual.drivers.linux_driver as linux_driver

        linux_driver.XTermParser = ReleaseXTermParser  # type: ignore[misc]
        super().start_application_mode()
        self.write(f"\x1b[>{_KITTY_PROTOCOL_FLAGS}u")
        self.flush()
