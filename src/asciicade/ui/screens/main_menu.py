"""Main menu screen."""

from __future__ import annotations

from typing import Literal

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from asciicade.core.game import GameMode
from asciicade.core.registry import GameRegistration
from asciicade.ui.context import AppContext
from asciicade.ui.screens.confirm_quit import ConfirmQuitScreen
from asciicade.ui.screens.game_select import GameSelectScreen
from asciicade.ui.screens.instructions import InstructionsScreen
from asciicade.ui.screens.leaderboard import LeaderboardScreen
from asciicade.ui.screens.match_history import MatchHistoryScreen
from asciicade.ui.screens.menu import MenuScreen
from asciicade.ui.screens.player_select import PlayerSelectScreen

MenuPurpose = Literal["high-scores", "match-history", "instructions"]


class MainMenuScreen(MenuScreen):
    """The application entry screen."""

    def __init__(self, context: AppContext) -> None:
        """Store the application context."""
        super().__init__()
        self._app_context = context

    def compose(self) -> ComposeResult:
        """Build the main menu."""
        yield Vertical(
            Static("ASCIICADE", id="app-title"),
            Static("A modular terminal arcade", id="app-subtitle"),
            OptionList(
                Option("Single Player", id="mode:single-player"),
                Option("Two Players", id="mode:multiplayer"),
                Option("High Scores", id="high-scores"),
                Option("Match History", id="match-history"),
                Option("Instructions", id="instructions"),
                Option("Quit", id="quit"),
                id="main-menu",
            ),
            Static("Enter/→ select · ←/Esc back", id="menu-footer"),
            classes="menu-screen",
        )

    def on_mount(self) -> None:
        """Focus the menu and preselect the last mode."""
        option_list = self.query_one(OptionList)
        option_list.focus()
        last_session = self._app_context.settings.get_last_session()
        if last_session is None:
            option_list.highlighted = 0
        else:
            option_list.highlighted = 0 if last_session.mode is GameMode.SINGLE_PLAYER else 1

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Open the selected menu entry."""
        option_id = event.option.id
        if option_id is None:
            return
        if option_id.startswith("mode:"):
            mode = GameMode(option_id.removeprefix("mode:"))
            self.app.push_screen(PlayerSelectScreen(self._app_context, mode))
        elif option_id == "high-scores":
            self._open_purpose("high-scores")
        elif option_id == "match-history":
            self._open_purpose("match-history")
        elif option_id == "instructions":
            self._open_purpose("instructions")
        elif option_id == "quit":
            self.app.push_screen(ConfirmQuitScreen())

    def _open_purpose(self, purpose: MenuPurpose) -> None:
        """Open a game-specific menu, skipping selection when only one game exists."""
        registrations = self._app_context.registry.all()
        if not registrations:
            self.notify("No games are registered.", severity="error")
            return
        if len(registrations) == 1:
            self._open_target(registrations[0], purpose)
            return
        self.app.push_screen(GameSelectScreen(self._app_context, purpose))

    def _open_target(self, registration: GameRegistration, purpose: MenuPurpose) -> None:
        """Open the target screen for a single registered game."""
        if purpose == "high-scores":
            self.app.push_screen(LeaderboardScreen(self._app_context, registration.identifier))
        elif purpose == "match-history":
            self.app.push_screen(MatchHistoryScreen(self._app_context, registration.identifier))
        else:
            self.app.push_screen(InstructionsScreen(registration))
