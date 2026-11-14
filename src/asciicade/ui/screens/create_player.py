"""Modal screen for creating or editing a player profile."""

from __future__ import annotations

from dataclasses import replace

from rich.text import Text
from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, OptionList, Static
from textual.widgets.option_list import Option

from asciicade.core.player import PlayerColor, PlayerProfile
from asciicade.persistence.players import PlayerRepository
from asciicade.ui.widgets import ActionButton, handle_button_row_key


class CreatePlayerScreen(Screen[PlayerProfile | None]):
    """Collect a name and color, then create or update a profile."""

    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=False),
        Binding("space", "select_color", "Select color", show=False),
    ]

    def __init__(
        self,
        players: PlayerRepository,
        profile: PlayerProfile | None = None,
    ) -> None:
        """Store the repository and optional profile being edited."""
        super().__init__()
        self._players = players
        self._profile = profile
        self._color = profile.color if profile is not None else PlayerColor.GREEN

    def compose(self) -> ComposeResult:
        """Build the create/edit dialog."""
        editing = self._profile is not None
        yield Vertical(
            Static("EDIT PLAYER" if editing else "CREATE PLAYER", id="screen-title"),
            Input(placeholder="Player name", id="player-name"),
            Static("Color", id="color-label"),
            OptionList(
                *(
                    Option(
                        Text(f"██ {color.label}", style=color.value),
                        id=f"color:{color.value}",
                    )
                    for color in PlayerColor
                ),
                id="color-list",
            ),
            Static("", id="create-status"),
            Horizontal(
                ActionButton("Save" if editing else "Create", id="create", variant="primary"),
                ActionButton("Cancel", id="cancel"),
                id="create-actions",
            ),
            Static("Enter save · Space select · Tab next field · Esc cancel", id="menu-footer"),
            classes="menu-screen modal-screen",
        )

    def on_mount(self) -> None:
        """Focus the name input and preselect the current color."""
        name_input = self.query_one(Input)
        if self._profile is not None:
            name_input.value = self._profile.name
        name_input.focus()
        self._highlight_color()
        self._update_status()

    def on_key(self, event: events.Key) -> None:
        """Move focus between dialog buttons with the arrow keys."""
        handle_button_row_key(self, event)

    def action_select_color(self) -> None:
        """Select the highlighted color when the color list has focus."""
        option_list = self.query_one("#color-list", OptionList)
        if option_list.has_focus:
            option_list.action_select()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Create or save when Enter is pressed in the name field."""
        event.stop()
        self._submit()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the dialog buttons."""
        if event.button.id == "create":
            self._submit()
        else:
            self.dismiss(None)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Select a color without closing the dialog."""
        option_id = event.option.id
        if option_id is None or not option_id.startswith("color:"):
            return
        self._color = PlayerColor(option_id.removeprefix("color:"))
        self._highlight_color()
        self._update_status()

    def action_cancel(self) -> None:
        """Dismiss the dialog without saving."""
        self.dismiss(None)

    def _highlight_color(self) -> None:
        """Highlight the currently selected color."""
        option_list = self.query_one("#color-list", OptionList)
        for index, option in enumerate(option_list.options):
            if option.id == f"color:{self._color.value}":
                option_list.highlighted = index
                return

    def _update_status(self) -> None:
        """Show the selected color."""
        self.query_one("#create-status", Static).update(f"Selected color: {self._color.label}")

    def _submit(self) -> None:
        """Validate the name and persist the profile."""
        name = self.query_one(Input).value.strip()
        if not name:
            self.notify("Enter a player name.", severity="warning")
            return
        if self._profile is None:
            self.dismiss(self._players.create(name, color=self._color))
            return
        updated = replace(self._profile, name=name, color=self._color)
        try:
            self._players.update(updated)
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return
        self.dismiss(updated)
