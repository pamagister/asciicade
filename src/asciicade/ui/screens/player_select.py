"""Player selection screen."""

from __future__ import annotations

from uuid import UUID

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Vertical
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from asciicade.core.game import GameMode
from asciicade.core.player import (
    GuestPlayer,
    PlayerProfile,
    PlayerSelection,
    player_identity,
)
from asciicade.ui.context import AppContext
from asciicade.ui.screens.create_player import CreatePlayerScreen
from asciicade.ui.screens.edit_player_picker import EditPlayerPickerScreen
from asciicade.ui.screens.game_select import GameSelectScreen
from asciicade.ui.screens.menu import MenuScreen


class PlayerSelectScreen(MenuScreen):
    """Select one or two players for a session."""

    BINDINGS = [
        *MenuScreen.BINDINGS,
        Binding("e", "edit_profile", "Edit profile", show=False),
        Binding("backspace", "undo_selection", "Undo", show=False),
    ]

    def __init__(self, context: AppContext, mode: GameMode) -> None:
        """Store the context and game mode."""
        super().__init__()
        self._app_context = context
        self._mode = mode
        self._selected: list[PlayerProfile | GuestPlayer] = []

    @property
    def _required(self) -> int:
        """Return the number of players required by the mode."""
        return 1 if self._mode is GameMode.SINGLE_PLAYER else 2

    def compose(self) -> ComposeResult:
        """Build the selection screen."""
        yield Vertical(
            Static("", id="screen-title"),
            Static("", id="player-selection-status"),
            OptionList(id="player-list"),
            Static("", id="menu-footer"),
            classes="menu-screen",
        )

    def on_mount(self) -> None:
        """Populate the initial selection list."""
        self._refresh()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle a selection entry."""
        option_id = event.option.id
        if option_id is None:
            return
        if option_id == "create":
            self.app.push_screen(
                CreatePlayerScreen(self._app_context.players),
                self._on_profile_created,
            )
        elif option_id == "edit-player":
            self.app.push_screen(
                EditPlayerPickerScreen(self._app_context),
                self._on_profile_edited,
            )
        elif option_id == "guest":
            self._add_player(GuestPlayer(slot=len(self._selected) + 1))
        elif option_id.startswith("profile:"):
            player_id = UUID(option_id.removeprefix("profile:"))
            profile = self._app_context.players.get(player_id)
            if profile is not None:
                self._add_player(profile)

    def on_option_list_option_highlighted(
        self,
        event: OptionList.OptionHighlighted,
    ) -> None:
        """Update the footer for the highlighted entry."""
        self._update_footer(event.option)

    def action_edit_profile(self) -> None:
        """Edit the highlighted profile."""
        option = self.query_one(OptionList).highlighted_option
        if option is None or option.id is None or not option.id.startswith("profile:"):
            self.notify("Select an existing profile to edit.", severity="warning")
            return
        player_id = UUID(option.id.removeprefix("profile:"))
        profile = self._app_context.players.get(player_id)
        if profile is None:
            return
        self.app.push_screen(
            CreatePlayerScreen(self._app_context.players, profile),
            self._on_profile_edited,
        )

    def _add_player(self, player: PlayerProfile | GuestPlayer) -> None:
        """Add a player when the slot is free and the identity is unique."""
        if len(self._selected) >= self._required:
            return
        identities = {player_identity(item) for item in self._selected}
        if player_identity(player) in identities:
            self.notify("That player is already selected.", severity="warning")
            return
        self._selected.append(player)
        self._refresh()
        if len(self._selected) == self._required:
            self._start_game()

    def action_undo_selection(self) -> None:
        """Remove the most recently selected player."""
        if not self._selected:
            return
        removed = self._selected.pop()
        preferred_id = removed.id if isinstance(removed, PlayerProfile) else None
        self._refresh(preferred_id)

    def _on_profile_created(self, profile: PlayerProfile | None) -> None:
        """Add a newly created profile to the selection."""
        if profile is not None:
            self._add_player(profile)

    def _on_profile_edited(self, profile: PlayerProfile | None) -> None:
        """Refresh after an edit dialog closes."""
        self._refresh(profile.id if profile is not None else None)

    def _available_profiles(self) -> list[PlayerProfile]:
        """Return profiles that are not already selected."""
        identities = {player_identity(item) for item in self._selected}
        return [
            profile
            for profile in self._app_context.players.list()
            if player_identity(profile) not in identities
        ]

    def _refresh(self, preferred_id: UUID | None = None) -> None:
        """Rebuild the option list and status text."""
        option_list = self.query_one(OptionList)
        option_list.clear_options()
        option_list.add_option(Option("Play as guest", id="guest"))
        option_list.add_option(Option("New player", id="create"))

        profiles = self._available_profiles()
        if profiles:
            option_list.add_option(Option("Edit player", id="edit-player"))
        for profile in profiles:
            option_list.add_option(
                Option(
                    Text(profile.name, style=profile.color.value),
                    id=f"profile:{profile.id}",
                )
            )

        option_list.highlighted = self._default_index(option_list, preferred_id)
        option_list.focus()
        self._update_texts()
        self._update_footer()

    def _default_index(self, option_list: OptionList, preferred_id: UUID | None = None) -> int:
        """Prefer a specific profile, then the first profile, otherwise guest."""
        if preferred_id is not None:
            for index, option in enumerate(option_list.options):
                if option.id == f"profile:{preferred_id}":
                    return index
        for index, option in enumerate(option_list.options):
            if option.id is not None and option.id.startswith("profile:"):
                return index
        return 0

    def _update_texts(self) -> None:
        """Update the title and status line."""
        title = self.query_one("#screen-title", Static)
        status = self.query_one("#player-selection-status", Static)
        if len(self._selected) == self._required:
            names = " vs ".join(player.name for player in self._selected)
            title.update("READY TO PLAY")
            status.update(f"Players: {names}.")
        else:
            title.update(f"SELECT PLAYER {len(self._selected) + 1} OF {self._required}")
            if self._selected:
                names = ", ".join(player.name for player in self._selected)
                status.update(
                    f"Selected: {names}. "
                    f"Choose player {len(self._selected) + 1} of {self._required}."
                )
            else:
                status.update("Choose a profile, create a player, or play as a guest.")

    def _update_footer(self, option: Option | None = None) -> None:
        """Show the actions available for the current highlight."""
        if option is None:
            option = self.query_one(OptionList).highlighted_option
        footer = self.query_one("#menu-footer", Static)
        if option is not None and option.id is not None and option.id.startswith("profile:"):
            footer.update("Enter/Space/D select · E edit · Backspace undo · A/←/Esc back")
        elif self._selected:
            footer.update("Enter/Space/D select · Backspace undo · A/←/Esc back")
        else:
            footer.update("Enter/Space/D select · A/←/Esc back")

    def _start_game(self) -> None:
        """Validate the selection and start the game."""
        try:
            selection = PlayerSelection(tuple(self._selected))
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return

        registrations = [
            registration
            for registration in self._app_context.registry.all()
            if self._mode in registration.modes
        ]
        if not registrations:
            self.notify("No game supports the selected mode.", severity="error")
            return

        last_session = self._app_context.settings.get_last_session()
        default_game_id = registrations[0].identifier
        if (
            last_session is not None
            and last_session.mode is self._mode
            and any(item.identifier == last_session.game_id for item in registrations)
        ):
            default_game_id = last_session.game_id
        self.app.push_screen(
            GameSelectScreen(
                self._app_context,
                "play",
                mode=self._mode,
                players=selection.players,
                default_game_id=default_game_id,
            )
        )
