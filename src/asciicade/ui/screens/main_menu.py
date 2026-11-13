"""Main menu screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from asciicade.ui.context import AppContext
from asciicade.ui.screens.confirm_quit import ConfirmQuitScreen
from asciicade.ui.screens.game_select import GameSelectScreen


class MainMenuScreen(Screen[None]):
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
                Option("Play", id="play"),
                Option("High Scores", id="high-scores"),
                Option("Match History", id="match-history"),
                Option("Instructions", id="instructions"),
                Option("Quit", id="quit"),
                id="main-menu",
            ),
            classes="menu-screen",
        )

    def on_mount(self) -> None:
        """Focus the menu."""
        self.query_one(OptionList).focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Open the selected menu entry."""
        option_id = event.option.id
        if option_id == "play":
            self.app.push_screen(GameSelectScreen(self._app_context, purpose="play"))
        elif option_id == "high-scores":
            self.app.push_screen(GameSelectScreen(self._app_context, purpose="high-scores"))
        elif option_id == "match-history":
            self.app.push_screen(GameSelectScreen(self._app_context, purpose="match-history"))
        elif option_id == "instructions":
            self.app.push_screen(GameSelectScreen(self._app_context, purpose="instructions"))
        elif option_id == "quit":
            self.app.push_screen(ConfirmQuitScreen())
