"""Game selection screen."""

from __future__ import annotations

from typing import Literal

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from asciicade.core.game import GameMode
from asciicade.core.player import GuestPlayer, PlayerProfile
from asciicade.core.registry import GameRegistration
from asciicade.ui.context import AppContext
from asciicade.ui.screens.instructions import InstructionsScreen
from asciicade.ui.screens.leaderboard import LeaderboardScreen
from asciicade.ui.screens.match_history import MatchHistoryScreen
from asciicade.ui.screens.menu import MenuScreen

GameSelectPurpose = Literal["play", "high-scores", "match-history", "instructions"]

_PURPOSE_TITLES: dict[str, str] = {
    "play": "SELECT GAME",
    "high-scores": "HIGH SCORES",
    "match-history": "MATCH HISTORY",
    "instructions": "INSTRUCTIONS",
}


class GameSelectScreen(MenuScreen):
    """Choose a registered game.

    A short description of the highlighted game is shown on the right side
    and updates automatically while scrolling through the list.
    """

    def __init__(
        self,
        context: AppContext,
        purpose: GameSelectPurpose,
        *,
        mode: GameMode | None = None,
        players: tuple[PlayerProfile | GuestPlayer, ...] = (),
        default_game_id: str | None = None,
    ) -> None:
        """Store the context and navigation purpose."""
        super().__init__()
        self._app_context = context
        self._purpose = purpose
        self._mode = mode
        self._players = players
        self._default_game_id = default_game_id

    def _registrations(self) -> tuple[GameRegistration, ...]:
        """Return the games available for the current purpose."""
        registrations = self._app_context.registry.all()
        if self._purpose == "play" and self._mode is not None:
            return tuple(item for item in registrations if self._mode in item.modes)
        return registrations

    def compose(self) -> ComposeResult:
        """Build the game list with a description panel."""
        yield Horizontal(
            Vertical(
                Static(_PURPOSE_TITLES[self._purpose], id="game-select-title"),
                OptionList(
                    *(
                        Option(registration.metadata.name, id=f"game:{registration.identifier}")
                        for registration in self._registrations()
                    ),
                    id="game-list",
                ),
                Static("Enter/→ select · ←/Esc back", id="menu-footer"),
                classes="menu-screen",
            ),
            Static("", id="game-description"),
            id="game-select-root",
        )

    def on_mount(self) -> None:
        """Focus the game list and preselect the default game."""
        option_list = self.query_one(OptionList)
        if option_list.option_count:
            option_list.highlighted = self._default_index(option_list)
            option_list.focus()
        self._update_description()

    def _default_index(self, option_list: OptionList) -> int:
        """Return the highlighted index for the requested default game."""
        if self._default_game_id is not None:
            for index, option in enumerate(option_list.options):
                if option.id == f"game:{self._default_game_id}":
                    return index
        return 0

    def on_option_list_option_highlighted(
        self,
        event: OptionList.OptionHighlighted,
    ) -> None:
        """Update the description panel for the highlighted game."""
        self._update_description()

    def _update_description(self) -> None:
        """Show the description of the highlighted game."""
        option_list = self.query_one(OptionList)
        description = self.query_one("#game-description", Static)
        option = option_list.highlighted_option
        if option is not None and option.id is not None and option.id.startswith("game:"):
            registration = self._app_context.registry.get(option.id.removeprefix("game:"))
            description.update(registration.metadata.description)
        else:
            description.update("")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Open the selected game in the requested context."""
        option_id = event.option.id
        if option_id is None or not option_id.startswith("game:"):
            return
        registration = self._app_context.registry.get(option_id.removeprefix("game:"))
        self._open(registration)

    def _open(self, registration: GameRegistration) -> None:
        """Push the next screen for the selected game."""
        if self._purpose == "play":
            if self._mode is None or not self._players:
                self.notify("No game mode or players were selected.", severity="error")
                return
            from asciicade.ui.screens.game_menu import GameMenuScreen

            self.app.push_screen(
                GameMenuScreen(
                    self._app_context,
                    registration,
                    self._mode,
                    self._players,
                )
            )
            return
        elif self._purpose == "high-scores":
            self.app.push_screen(
                LeaderboardScreen(self._app_context, registration.metadata.identifier)
            )
        elif self._purpose == "match-history":
            self.app.push_screen(
                MatchHistoryScreen(self._app_context, registration.metadata.identifier)
            )
        else:
            self.app.push_screen(InstructionsScreen(registration))
