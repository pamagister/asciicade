"""Quit confirmation dialog."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static


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
                Button("Quit", id="quit", variant="error"),
                Button("Cancel", id="cancel", variant="primary"),
                id="confirm-actions",
            ),
            classes="menu-screen modal-screen",
        )

    def on_mount(self) -> None:
        """Focus the safe option."""
        self.query_one("#cancel", Button).focus()

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
