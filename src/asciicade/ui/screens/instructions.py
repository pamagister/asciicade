"""In-application instructions screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import Static

from asciicade.core.registry import GameRegistration


class InstructionsScreen(Screen[None]):
    """Show the instructions for a game."""

    def __init__(self, registration: GameRegistration) -> None:
        """Store the selected game."""
        super().__init__()
        self._registration = registration

    def compose(self) -> ComposeResult:
        """Build the instructions view."""
        yield Vertical(
            Static(
                f"{self._registration.metadata.name.upper()} — HOW TO PLAY",
                id="screen-title",
            ),
            Static(self._registration.metadata.instructions, id="instructions-body"),
            classes="menu-screen",
        )

    def on_mount(self) -> None:
        """Focus the screen for scrolling."""
        self.focus()
