"""Shared keyboard behavior for menu screens."""

from __future__ import annotations

from textual.binding import Binding
from textual.screen import Screen
from textual.widgets import OptionList


class MenuScreen(Screen[None]):
    """A screen whose highlighted option can be confirmed or left with the keyboard."""

    BINDINGS = [
        Binding("right", "confirm", "Select", show=False),
        Binding("left", "back", "Back", show=False),
    ]

    def action_confirm(self) -> None:
        """Select the currently highlighted option."""
        self.query_one(OptionList).action_select()

    async def action_back(self) -> None:
        """Leave this screen when possible."""
        await self.app.action_back()
