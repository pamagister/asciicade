"""Leave-game confirmation dialog."""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from asciicade.core.game import GameMode
from asciicade.ui.widgets import ActionButton, handle_button_row_key


class LeaveGameScreen(Screen[str]):
    """Ask whether to leave the current game."""

    BINDINGS = [Binding("escape", "stay", "Stay", show=False)]

    def __init__(self, game_name: str, mode: GameMode) -> None:
        """Store the session description."""
        super().__init__()
        self._game_name = game_name
        self._mode = mode

    def compose(self) -> ComposeResult:
        """Build the leave-game dialog."""
        mode_label = self._mode.value.replace("-", " ").title()
        yield Vertical(
            Static("PAUSED", id="confirm-title"),
            Static(
                f"Leave {self._game_name} ({mode_label})?",
                id="leave-question",
            ),
            Horizontal(
                ActionButton("Game menu", id="game-menu"),
                ActionButton("Main menu", id="main-menu"),
                ActionButton("Stay", id="stay", variant="primary"),
                id="confirm-actions",
            ),
            Static("←/→ move · Enter/Space select · Esc stay", id="menu-footer"),
            classes="menu-screen modal-screen",
        )

    def on_mount(self) -> None:
        """Focus the safe option."""
        self.query_one("#stay", ActionButton).focus()

    def on_key(self, event: events.Key) -> None:
        """Move focus between dialog buttons with the arrow keys."""
        handle_button_row_key(self, event)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Return the selected action."""
        self.dismiss(event.button.id or "stay")

    def action_stay(self) -> None:
        """Close the dialog and stay in the game."""
        self.dismiss("stay")
