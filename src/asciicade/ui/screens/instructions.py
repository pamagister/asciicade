"""In-application instructions screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical, VerticalScroll
from textual.screen import Screen
from textual.widgets import Static

from asciicade.core.registry import GameRegistration


class InstructionsScreen(Screen[None]):
    """Show the instructions for a game."""

    BINDINGS = [
        Binding("escape", "back", "Back", show=False),
        Binding("left", "back", "Back", show=False),
        Binding("space", "page_down", "Page down", show=False),
    ]

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
            VerticalScroll(
                Static(self._registration.metadata.instructions, id="instructions-body"),
                id="instructions-scroll",
            ),
            Static("↑/↓ scroll · Space page · ←/Esc back", id="menu-footer"),
            classes="menu-screen",
        )

    def on_mount(self) -> None:
        """Focus the scrollable instructions."""
        self.query_one(VerticalScroll).focus()

    async def action_back(self) -> None:
        """Leave the instructions."""
        await self.app.action_back()

    def action_page_down(self) -> None:
        """Scroll the instructions down one page."""
        self.query_one(VerticalScroll).action_page_down()
