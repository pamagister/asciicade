"""Modal screen for creating a player profile."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Static

from asciicade.core.player import PlayerProfile
from asciicade.persistence.players import PlayerRepository


class CreatePlayerScreen(Screen[PlayerProfile | None]):
    """Collect a name and create a persistent profile."""

    def __init__(self, players: PlayerRepository) -> None:
        """Store the player repository."""
        super().__init__()
        self._players = players

    def compose(self) -> ComposeResult:
        """Build the create-player dialog."""
        yield Vertical(
            Static("CREATE PLAYER", id="screen-title"),
            Input(placeholder="Player name", id="player-name"),
            Horizontal(
                Button("Create", id="create", variant="primary"),
                Button("Cancel", id="cancel"),
                id="create-actions",
            ),
            classes="menu-screen modal-screen",
        )

    def on_mount(self) -> None:
        """Focus the name input."""
        self.query_one(Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Create the profile when Enter is pressed."""
        event.stop()
        self._create()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the dialog buttons."""
        if event.button.id == "create":
            self._create()
        else:
            self.dismiss(None)

    def _create(self) -> None:
        """Validate the name and create the profile."""
        name = self.query_one(Input).value.strip()
        if not name:
            self.notify("Enter a player name.", severity="warning")
            return
        try:
            profile = self._players.create(name)
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return
        self.dismiss(profile)
