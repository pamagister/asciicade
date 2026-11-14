"""Reusable UI widgets and keyboard helpers."""

from __future__ import annotations

from textual import events
from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import Button


class ActionButton(Button):
    """A button that can be activated with Enter or Space."""

    BINDINGS = [
        Binding("enter", "press", "Press", show=False),
        Binding("space", "press", "Press", show=False),
    ]


def move_button_focus(screen: Screen, step: int) -> None:
    """Move focus to the previous or next action button."""
    buttons = list(screen.query(ActionButton))
    if not buttons:
        return
    focused = screen.focused
    index = next((i for i, button in enumerate(buttons) if button is focused), None)
    if index is None:
        index = 0 if step > 0 else len(buttons) - 1
    else:
        index = (index + step) % len(buttons)
    buttons[index].focus()


def handle_button_row_key(screen: Screen, event: events.Key) -> bool:
    """Handle arrow navigation for a focused action button.

    Returns:
        ``True`` when the key was consumed by the button-row navigation.
    """
    if not isinstance(screen.focused, ActionButton):
        return False
    if event.key in ("left", "up"):
        event.stop()
        event.prevent_default()
        move_button_focus(screen, -1)
        return True
    if event.key in ("right", "down"):
        event.stop()
        event.prevent_default()
        move_button_focus(screen, 1)
        return True
    return False
