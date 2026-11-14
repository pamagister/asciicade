"""Game menu screen with play, instructions and game-specific options."""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import OptionList, Static
from textual.widgets.option_list import Option

from asciicade.core.game import GameMode
from asciicade.core.options import (
    BooleanOptionDefinition,
    ChoiceOptionDefinition,
    GameOptions,
)
from asciicade.core.player import GuestPlayer, PlayerProfile
from asciicade.core.registry import GameRegistration
from asciicade.ui.context import AppContext
from asciicade.ui.screens.instructions import InstructionsScreen

_OPTION_SEPARATOR_ID = "options-separator"


class GameMenuScreen(Screen[None]):
    """Show play, instructions and options for a single game.

    Layout:

    - ``Play`` starts the game with the currently selected options.
    - ``Instructions`` opens the game-specific help screen.
    - ``--- Options ---`` is a disabled separator that is skipped while
      navigating with the arrow keys.
    - Each option below the separator can be toggled with Space and changed
      with the left and right arrow keys. Enter also cycles the value of a
      choice or boolean option.
    """

    BINDINGS = [
        Binding("right", "confirm", "Select", show=False),
        Binding("d", "confirm", "Select", show=False),
        Binding("escape", "back", "Back", show=False),
        Binding("a", "back", "Back", show=False),
        Binding("up", "cursor_up", "Move up", show=False),
        Binding("down", "cursor_down", "Move down", show=False),
        Binding("w", "cursor_up", "Move up", show=False),
        Binding("s", "cursor_down", "Move down", show=False),
        Binding("space", "toggle_option", "Toggle option", show=False),
    ]

    def __init__(
        self,
        context: AppContext,
        registration: GameRegistration,
        mode: GameMode,
        players: tuple[PlayerProfile | GuestPlayer, ...],
        *,
        options: GameOptions | None = None,
    ) -> None:
        """Store the session configuration and the resolved options."""
        super().__init__()
        self._app_context = context
        self._registration = registration
        self._mode = mode
        self._players = players
        self._options = options or self._default_options()
        self._option_keys: list[str] = []

    def _default_options(self) -> GameOptions:
        """Return the default options declared by the game metadata."""
        if self._registration.metadata.options is not None:
            return self._registration.metadata.options.defaults()
        return GameOptions(())

    def compose(self) -> ComposeResult:
        """Build the game menu."""
        metadata = self._registration.metadata
        yield Horizontal(
            Vertical(
                Static(metadata.name.upper(), id="screen-title"),
                Static(metadata.description, id="game-description"),
                OptionList(
                    Option("Play", id="play"),
                    Option("Instructions", id="instructions"),
                    Option("--- Options ---", id=_OPTION_SEPARATOR_ID, disabled=True),
                    *self._option_entries(),
                    id="menu-list",
                ),
                Static("", id="menu-footer"),
                classes="menu-pane",
            ),
            Static("", id="game-info-panel"),
            id="game-menu-root",
        )

    def _option_entries(self) -> list[Option]:
        """Build the option entries below the separator."""
        self._option_keys = []
        entries: list[Option] = []
        if self._registration.metadata.options is None:
            return entries
        for definition in self._registration.metadata.options.definitions:
            current = self._options.value_for(definition.key)
            entries.append(
                Option(self._format_option(definition, current), id=f"option:{definition.key}")
            )
            self._option_keys.append(definition.key)
        return entries

    def _format_option(
        self,
        definition: BooleanOptionDefinition | ChoiceOptionDefinition,
        current: str,
    ) -> str:
        """Return the display text for an option and its current value."""
        if isinstance(definition, ChoiceOptionDefinition):
            return f"{definition.label}: {current}"
        if isinstance(definition, BooleanOptionDefinition):
            return f"{definition.label}: {current}"
        return f"{definition.label}: {current}"

    def on_mount(self) -> None:
        """Focus the menu list and preselect Play."""
        option_list = self.query_one(OptionList)
        if option_list.option_count:
            option_list.highlighted = 0
            option_list.focus()
        self._update_footer()

    def on_option_list_option_highlighted(
        self,
        event: OptionList.OptionHighlighted,
    ) -> None:
        """Update the footer and info panel for the highlighted entry."""
        self._update_footer()
        self._update_info_panel(event.option)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Handle Play, Instructions, options toggling or confirmation."""
        option_id = event.option.id
        if option_id is None:
            return
        if option_id == "play":
            self._start_game()
        elif option_id == "instructions":
            self.app.push_screen(InstructionsScreen(self._registration))
        elif option_id == _OPTION_SEPARATOR_ID:
            # Disabled separator: never selectable.
            return
        elif option_id.startswith("option:"):
            self._toggle_option(option_id.removeprefix("option:"))
        self._update_footer()

    async def on_key(self, event: events.Key) -> None:
        """Handle option values and left-to-back navigation."""
        option_list = self.query_one(OptionList)
        option = option_list.highlighted_option
        if option is None or option.id is None:
            return
        if option.id.startswith("option:"):
            key = option.id.removeprefix("option:")
            if event.key in ("left", "h", "a"):
                self._change_option(key, -1)
                event.stop()
                event.prevent_default()
            elif event.key in ("right", "l", "d"):
                self._change_option(key, 1)
                event.stop()
                event.prevent_default()
            return
        if event.key in ("left", "a"):
            event.stop()
            event.prevent_default()
            await self.action_back()

    def action_toggle_option(self) -> None:
        """Toggle an option or activate a menu entry with Space."""
        option_list = self.query_one(OptionList)
        option = option_list.highlighted_option
        if option is None or option.id is None:
            return
        if not option.id.startswith("option:"):
            self.action_confirm()
            return
        self._toggle_option(option.id.removeprefix("option:"))
        self._update_footer()

    def _change_option(self, key: str, direction: int) -> None:
        """Move the selection of the given option by ``direction`` steps."""
        if self._registration.metadata.options is None:
            return
        for definition in self._registration.metadata.options.definitions:
            if definition.key != key:
                continue
            current = self._options.value_for(key)
            if isinstance(definition, ChoiceOptionDefinition):
                index = definition.index_of(current)
                next_value = definition.values[(index + direction) % len(definition.values)]
            else:
                next_value = "on" if current == "off" else "off"
            self._options = self._options.with_value(key, next_value)
            self._refresh_option_list()
            self._update_footer()
            self._update_info_panel(self.query_one(OptionList).highlighted_option)
            return

    def action_confirm(self) -> None:
        """Select the currently highlighted menu entry."""
        self.query_one(OptionList).action_select()

    def action_cursor_up(self) -> None:
        """Move the focused OptionList cursor up."""
        option_list = self.query_one(OptionList)
        if option_list.has_focus:
            option_list.action_cursor_up()

    def action_cursor_down(self) -> None:
        """Move the focused OptionList cursor down."""
        option_list = self.query_one(OptionList)
        if option_list.has_focus:
            option_list.action_cursor_down()

    async def action_back(self) -> None:
        """Leave this screen when possible."""
        await self.app.action_back()

    def _update_footer(self) -> None:
        """Show the actions available for the current highlight."""
        option_list = self.query_one(OptionList)
        option = option_list.highlighted_option
        footer = self.query_one("#menu-footer", Static)
        if option is None or option.id is None:
            footer.update("Esc back")
            return
        if option.id == "play":
            footer.update("Enter/Space/D start · A/Esc back")
        elif option.id == "instructions":
            footer.update("Enter/Space/D show · A/Esc back")
        elif option.id == _OPTION_SEPARATOR_ID:
            footer.update("W/S navigate · A/Esc back")
        elif option.id.startswith("option:"):
            footer.update("Space/Enter/D cycle · A/D/←/→ change · Esc")
        else:
            footer.update("A/Esc back")

    def _update_info_panel(self, option: Option | None) -> None:
        """Show a description for the highlighted option, if any."""
        panel = self.query_one("#game-info-panel", Static)
        if option is None or option.id is None or not option.id.startswith("option:"):
            panel.update("")
            return
        key = option.id.removeprefix("option:")
        if self._registration.metadata.options is None:
            panel.update("")
            return
        for definition in self._registration.metadata.options.definitions:
            if definition.key != key:
                continue
            current = self._options.value_for(definition.key)
            if isinstance(definition, ChoiceOptionDefinition):
                panel.update(
                    f"{definition.label}\n"
                    f"Values: {', '.join(definition.values)}\n"
                    f"Current: {current}"
                )
            elif isinstance(definition, BooleanOptionDefinition):
                state = "on" if current == "on" else "off"
                panel.update(f"{definition.label}\nToggle on/off. Current: {state}.")
            else:
                panel.update(f"{getattr(definition, 'label', 'Option')}: {current}")
            return
        panel.update("")

    def _toggle_option(self, key: str) -> None:
        """Cycle the value of the option with the given key."""
        if self._registration.metadata.options is None:
            return
        for definition in self._registration.metadata.options.definitions:
            if definition.key != key:
                continue
            current = self._options.value_for(key)
            if isinstance(definition, ChoiceOptionDefinition):
                index = definition.index_of(current)
                next_value = definition.values[(index + 1) % len(definition.values)]
            else:
                next_value = "on" if current == "off" else "off"
            self._options = self._options.with_value(key, next_value)
            self._refresh_option_list()
            self._update_footer()
            self._update_info_panel(self.query_one(OptionList).highlighted_option)
            return

    def _refresh_option_list(self) -> None:
        """Update the option entries in place with their current values."""
        if self._registration.metadata.options is None:
            return
        option_list = self.query_one(OptionList)
        for index, key in enumerate(self._option_keys):
            definition = self._find_definition(key)
            if definition is None:
                continue
            current = self._options.value_for(key)
            option_list.replace_option_prompt_at_index(
                3 + index, self._format_option(definition, current)
            )
        option_list.focus()

    def _find_definition(self, key: str) -> BooleanOptionDefinition | ChoiceOptionDefinition | None:
        """Return the option definition for a key, if declared."""
        if self._registration.metadata.options is None:
            return None
        for definition in self._registration.metadata.options.definitions:
            if definition.key == key:
                return definition
        return None

    def _start_game(self) -> None:
        """Push the gameplay screen with the selected options."""
        from asciicade.ui.screens.game_screen_factory import create_game_screen

        self.app.push_screen(
            create_game_screen(
                self._app_context,
                self._registration,
                self._mode,
                self._players,
                options=self._options,
            )
        )
