"""Player selection screen."""

from __future__ import annotations

from uuid import UUID

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from asciicade.core.game import GameMode
from asciicade.core.player import (
    GuestPlayer,
    PlayerProfile,
    PlayerSelection,
    player_identity,
)
from asciicade.core.registry import GameRegistration
from asciicade.ui.context import AppContext
from asciicade.ui.screens.create_player import CreatePlayerScreen
from asciicade.ui.screens.snake_game import SnakeGameScreen


class PlayerSelectScreen(Screen[None]):
    """Select one or two players for a session."""

    def __init__(
        self,
        context: AppContext,
        registration: GameRegistration,
        mode: GameMode,
    ) -> None:
        """Store the context, game and mode."""
        super().__init__()
        self._app_context = context
        self._registration = registration
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
        elif option_id == "guest":
            self._add_player(GuestPlayer(slot=len(self._selected) + 1))
        elif option_id == "start":
            self._start_game()
        elif option_id.startswith("profile:"):
            player_id = UUID(option_id.removeprefix("profile:"))
            profile = self._app_context.players.get(player_id)
            if profile is not None:
                self._add_player(profile)

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

    def _on_profile_created(self, profile: PlayerProfile | None) -> None:
        """Add a newly created profile to the selection."""
        if profile is not None:
            self._add_player(profile)

    def _refresh(self) -> None:
        """Rebuild the option list and status text."""
        option_list = self.query_one(OptionList)
        option_list.clear_options()
        identities = {player_identity(item) for item in self._selected}

        for profile in self._app_context.players.list():
            if player_identity(profile) in identities:
                continue
            option_list.add_option(Option(profile.name, id=f"profile:{profile.id}"))

        option_list.add_option(Option("Create new player", id="create"))
        option_list.add_option(Option("Play as guest", id="guest"))
        if len(self._selected) == self._required:
            option_list.add_option(Option("Start game", id="start"))
        if option_list.option_count:
            option_list.highlighted = 0
        option_list.focus()

        title = self.query_one("#screen-title", Static)
        status = self.query_one("#player-selection-status", Static)
        if len(self._selected) == self._required:
            names = " vs ".join(player.name for player in self._selected)
            title.update(f"{self._registration.metadata.name.upper()} — READY")
            status.update(f"Players: {names}. Choose Start game.")
        else:
            title.update(
                f"{self._registration.metadata.name.upper()} — "
                f"SELECT PLAYER {len(self._selected) + 1} OF {self._required}"
            )
            status.update("Choose a profile, create a player, or play as a guest.")

    def _start_game(self) -> None:
        """Validate the selection and start the game."""
        try:
            selection = PlayerSelection(tuple(self._selected))
        except ValueError as exc:
            self.notify(str(exc), severity="error")
            return
        self.app.push_screen(
            SnakeGameScreen(
                self._app_context,
                self._registration,
                self._mode,
                selection.players,
            )
        )
