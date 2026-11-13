"""Game mode selection screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.screen import Screen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from asciicade.core.game import GameMode
from asciicade.core.registry import GameRegistration
from asciicade.ui.context import AppContext
from asciicade.ui.screens.instructions import InstructionsScreen
from asciicade.ui.screens.player_select import PlayerSelectScreen

_MODE_LABELS: dict[GameMode, str] = {
    GameMode.SINGLE_PLAYER: "Single player",
    GameMode.MULTIPLAYER: "Two players",
}


class ModeSelectScreen(Screen[None]):
    """Choose a supported game mode."""

    def __init__(self, context: AppContext, registration: GameRegistration) -> None:
        """Store the context and selected game."""
        super().__init__()
        self._app_context = context
        self._registration = registration

    def compose(self) -> ComposeResult:
        """Build the mode list."""
        yield Vertical(
            Static(
                f"{self._registration.metadata.name.upper()} — SELECT MODE",
                id="screen-title",
            ),
            OptionList(
                *(
                    Option(_MODE_LABELS[mode], id=f"mode:{mode.value}")
                    for mode in self._registration.modes
                ),
                Option("Instructions", id="instructions"),
                id="mode-list",
            ),
            classes="menu-screen",
        )

    def on_mount(self) -> None:
        """Focus the mode list."""
        option_list = self.query_one(OptionList)
        if option_list.option_count:
            option_list.highlighted = 0
            option_list.focus()

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Open the selected mode or instructions."""
        option_id = event.option.id
        if option_id == "instructions":
            self.app.push_screen(InstructionsScreen(self._registration))
        elif option_id is not None and option_id.startswith("mode:"):
            mode = GameMode(option_id.removeprefix("mode:"))
            self.app.push_screen(PlayerSelectScreen(self._app_context, self._registration, mode))
