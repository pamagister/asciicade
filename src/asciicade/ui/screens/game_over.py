"""Game-over summary screen."""

from __future__ import annotations

from textual import events
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Static

from asciicade.core.game import GameMode
from asciicade.core.options import GameOptions
from asciicade.core.player import GuestPlayer, PlayerProfile
from asciicade.core.registry import GameRegistration
from asciicade.core.results import GameResult
from asciicade.ui.context import AppContext
from asciicade.ui.navigation import go_to_game_menu, go_to_main_menu
from asciicade.ui.screens.leaderboard import LeaderboardScreen
from asciicade.ui.widgets import ActionButton, handle_button_row_key


class GameOverScreen(Screen[None]):
    """Show the final result and next actions."""

    BINDINGS = [Binding("escape", "back", "Back", show=False)]

    def __init__(
        self,
        context: AppContext,
        registration: GameRegistration,
        mode: GameMode,
        players: tuple[PlayerProfile | GuestPlayer, ...],
        result: GameResult,
        *,
        options: GameOptions | None = None,
        winner_label: str | None = None,
    ) -> None:
        """Store the completed session."""
        super().__init__()
        self._app_context = context
        self._registration = registration
        self._mode = mode
        self._players = players
        self._result = result
        self._options = options
        self._winner_label = winner_label

    def compose(self) -> ComposeResult:
        """Build the result summary."""
        yield Vertical(
            Static("GAME OVER", id="game-over-title"),
            Static(self._summary(), id="game-over-summary"),
            Horizontal(
                ActionButton("Play again", id="play-again", variant="primary"),
                ActionButton("Main menu", id="main-menu"),
                ActionButton("High scores", id="high-scores"),
                id="game-over-actions",
            ),
            Static("W/S/A/D move · Enter/Space select · A/Esc game menu", id="menu-footer"),
            classes="menu-screen",
        )

    def on_mount(self) -> None:
        """Focus the first action."""
        self.query_one("#play-again", ActionButton).focus()

    def on_key(self, event: events.Key) -> None:
        """Move focus between result actions with the arrow keys."""
        handle_button_row_key(self, event)

    def action_back(self) -> None:
        """Return to the game menu."""
        go_to_game_menu(
            self.app,
            self._app_context,
            self._registration,
            self._mode,
            self._players,
            self._options,
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle the selected action."""
        button_id = event.button.id
        if button_id == "play-again":
            from asciicade.ui.screens.game_screen_factory import create_game_screen

            self.app.pop_screen()
            self.app.switch_screen(
                create_game_screen(
                    self._app_context,
                    self._registration,
                    self._mode,
                    self._players,
                    options=self._options,
                )
            )
        elif button_id == "main-menu":
            go_to_main_menu(self.app, self._app_context)
        elif button_id == "high-scores":
            self.app.push_screen(
                LeaderboardScreen(
                    self._app_context,
                    self._registration.metadata.identifier,
                )
            )

    def _summary(self) -> str:
        """Build the human-readable result summary."""
        lines: list[str] = []
        if self._result.is_draw:
            lines.append("Result: Draw")
        elif self._winner_label is not None:
            lines.append(f"Winner: {self._winner_label}")
        elif self._result.winner_name is not None:
            lines.append(f"Winner: {self._result.winner_name}")
        else:
            lines.append("Result: Game over")

        for player_result in self._result.player_results:
            lines.append(
                f"{player_result.player_name}: {player_result.score} "
                f"({player_result.outcome.value})"
            )
        return "\n".join(lines)
