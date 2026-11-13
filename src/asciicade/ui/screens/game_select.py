"""Game selection screen."""

from __future__ import annotations

from typing import Literal

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from asciicade.core.registry import GameRegistration
from asciicade.ui.context import AppContext
from asciicade.ui.screens.instructions import InstructionsScreen
from asciicade.ui.screens.leaderboard import LeaderboardScreen
from asciicade.ui.screens.match_history import MatchHistoryScreen
from asciicade.ui.screens.mode_select import ModeSelectScreen

GameSelectPurpose = Literal["play", "high-scores", "match-history", "instructions"]

_PURPOSE_TITLES: dict[str, str] = {
    "play": "SELECT GAME",
    "high-scores": "HIGH SCORES",
    "match-history": "MATCH HISTORY",
    "instructions": "INSTRUCTIONS",
}


class GameSelectScreen(Screen[None]):
    """Choose a registered game."""

    def __init__(self, context: AppContext, purpose: GameSelectPurpose) -> None:
        """Store the context and navigation purpose."""
        super().__init__()
        self._app_context = context
        self._purpose = purpose

    def compose(self) -> ComposeResult:
        """Build the game list."""
        registrations = self._app_context.registry.all()
        yield Vertical(
            Static(_PURPOSE_TITLES[self._purpose], id="screen-title"),
            OptionList(
                *(
                    Option(registration.metadata.name, id=f"game:{registration.identifier}")
                    for registration in registrations
                ),
                id="game-list",
            ),
            classes="menu-screen",
        )

    def on_mount(self) -> None:
        """Focus the game list when it has entries."""
        option_list = self.query_one(OptionList)
        if option_list.option_count:
            option_list.highlighted = 0
            option_list.focus()

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
            self.app.push_screen(ModeSelectScreen(self._app_context, registration))
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
