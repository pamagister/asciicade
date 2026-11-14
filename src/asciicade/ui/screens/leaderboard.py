"""Single-player leaderboard screen."""

from __future__ import annotations

from textual.app import ComposeResult
from textual.containers import Vertical
from textual.widgets import DataTable, OptionList, Static
from textual.widgets.option_list import Option

from asciicade.ui.context import AppContext
from asciicade.ui.screens.menu import MenuScreen


class LeaderboardScreen(MenuScreen):
    """Display stored high scores for a game."""

    def __init__(self, context: AppContext, game_id: str | None = None) -> None:
        """Store the context and optional preselected game."""
        super().__init__()
        self._app_context = context
        self._game_id = game_id

    def compose(self) -> ComposeResult:
        """Build the game selector and score table."""
        registrations = self._app_context.registry.all()
        yield Vertical(
            Static("HIGH SCORES", id="screen-title"),
            OptionList(
                *(
                    Option(registration.metadata.name, id=f"game:{registration.identifier}")
                    for registration in registrations
                ),
                id="leaderboard-games",
            ),
            DataTable(id="leaderboard-table"),
            Static("Enter/→ select · ←/Esc back", id="menu-footer"),
            classes="menu-screen",
        )

    def on_mount(self) -> None:
        """Configure the table and load the initial scores."""
        table = self.query_one(DataTable)
        table.add_columns("Rank", "Player", "Score", "Date")
        if self._game_id is None and self._app_context.registry.all():
            self._game_id = self._app_context.registry.all()[0].identifier
        option_list = self.query_one(OptionList)
        if option_list.option_count:
            option_list.highlighted = 0
            option_list.focus()
        self._load(self._game_id)

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Load scores for the selected game."""
        option_id = event.option.id
        if option_id is None or not option_id.startswith("game:"):
            return
        self._load(option_id.removeprefix("game:"))

    def _load(self, game_id: str | None) -> None:
        """Populate the table for a game."""
        table = self.query_one(DataTable)
        table.clear()
        if game_id is None:
            table.add_row("—", "No games registered", "", "")
            return
        entries = self._app_context.results.leaderboard(game_id)
        if not entries:
            table.add_row("—", "No scores yet", "", "")
            return
        for rank, entry in enumerate(entries, start=1):
            table.add_row(
                str(rank),
                entry.player_name,
                str(entry.score),
                entry.finished_at.strftime("%Y-%m-%d %H:%M"),
            )
