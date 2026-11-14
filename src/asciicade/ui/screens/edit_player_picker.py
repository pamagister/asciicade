"""Picker for choosing a profile to edit."""

from __future__ import annotations

from uuid import UUID

from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from asciicade.core.player import PlayerProfile
from asciicade.ui.context import AppContext
from asciicade.ui.screens.create_player import CreatePlayerScreen


class EditPlayerPickerScreen(Screen[PlayerProfile | None]):
    """Choose an existing profile and open the edit dialog."""

    BINDINGS = [
        Binding("right", "confirm", "Select", show=False),
        Binding("left", "back", "Back", show=False),
        Binding("space", "confirm", "Select", show=False),
    ]

    def __init__(self, context: AppContext) -> None:
        """Store the application context."""
        super().__init__()
        self._app_context = context

    def compose(self) -> ComposeResult:
        """Build the profile picker."""
        yield Vertical(
            Static("EDIT PLAYER", id="screen-title"),
            Static("Choose a profile to edit.", id="player-selection-status"),
            OptionList(id="edit-player-list"),
            Static("Enter/Space edit · ←/Esc back", id="menu-footer"),
            classes="menu-screen",
        )

    def on_mount(self) -> None:
        """Populate the picker."""
        self._refresh()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Open the selected profile for editing."""
        option_id = event.option.id
        if option_id is None or not option_id.startswith("profile:"):
            return
        profile = self._app_context.players.get(UUID(option_id.removeprefix("profile:")))
        if profile is None:
            self.notify("That profile no longer exists.", severity="error")
            self._refresh()
            return
        self.app.push_screen(
            CreatePlayerScreen(self._app_context.players, profile),
            self._on_profile_edited,
        )

    def action_confirm(self) -> None:
        """Select the highlighted profile."""
        self.query_one(OptionList).action_select()

    async def action_back(self) -> None:
        """Close the picker."""
        await self.app.action_back()

    def _on_profile_edited(self, profile: PlayerProfile | None) -> None:
        """Return the edited profile or refresh the picker on cancel."""
        if profile is not None:
            self.dismiss(profile)
        else:
            self._refresh()

    def _refresh(self) -> None:
        """Rebuild the profile list."""
        option_list = self.query_one(OptionList)
        option_list.clear_options()
        profiles = self._app_context.players.list()
        for profile in profiles:
            option_list.add_option(Option(profile.name, id=f"profile:{profile.id}"))
        if option_list.option_count:
            option_list.highlighted = 0
        option_list.focus()
