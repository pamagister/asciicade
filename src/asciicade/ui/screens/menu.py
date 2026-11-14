"""Shared keyboard behavior for menu screens."""

from __future__ import annotations

from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import OptionList


class MenuScreen(Screen[None]):
    """A screen whose highlighted option can be confirmed or left with the keyboard."""

    BINDINGS = [
        Binding("right", "confirm", "Select", show=False),
        Binding("d", "confirm", "Select", show=False),
        Binding("left", "back", "Back", show=False),
        Binding("a", "back", "Back", show=False),
        Binding("up", "cursor_up", "Move up", show=False),
        Binding("down", "cursor_down", "Move down", show=False),
        Binding("w", "cursor_up", "Move up", show=False),
        Binding("s", "cursor_down", "Move down", show=False),
        Binding("space", "confirm", "Select", show=False),
    ]

    def action_confirm(self) -> None:
        """Select the currently highlighted option."""
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
