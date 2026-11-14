"""Quit confirmation dialog."""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from asciicade.ui.widgets import ActionButton, handle_button_row_key


class ConfirmQuitScreen(Screen[None]):
    """Ask the user to confirm quitting the application."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("q", "quit", "Quit", show=False),
    ]

    def compose(self) -> ComposeResult:
        """Build the confirmation dialog."""
        yield Vertical(
            Static("Quit Asciicade?", id="confirm-title"),
            Horizontal(
                ActionButton("Quit", id="quit", variant="error"),
                ActionButton("Cancel", id="cancel", variant="primary"),
                id="confirm-actions",
            ),
            Static("W/S/A/D move · Enter/Space select · A/Esc cancel", id="menu-footer"),
            classes="menu-screen modal-screen",
        )

    def on_mount(self) -> None:
        """Focus the safe option."""
        self.query_one("#cancel", ActionButton).focus()

    def on_key(self, event: events.Key) -> None:
        """Move focus between dialog buttons with the arrow keys."""
        handle_button_row_key(self, event)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the dialog buttons."""
        if event.button.id == "quit":
            self.app.exit()
        else:
            self.app.pop_screen()

    def action_cancel(self) -> None:
        """Dismiss the dialog."""
        self.app.pop_screen()

    def action_quit(self) -> None:
        """Quit the application."""
        self.app.exit()
