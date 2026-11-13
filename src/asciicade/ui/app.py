"""Textual application shell for Asciicade."""

from __future__ import annotations

from pathlib import Path

from textual.app import App
from textual.binding import Binding

from asciicade.games import build_default_registry
from asciicade.persistence import (
    Database,
    PlayerRepository,
    ResultRepository,
    database_path,
)
from asciicade.ui.context import AppContext
from asciicade.ui.screens.confirm_quit import ConfirmQuitScreen
from asciicade.ui.screens.main_menu import MainMenuScreen


class AsciicadeApp(App[None]):
    """The top-level Textual application."""

    CSS_PATH = Path(__file__).parent / "styles" / "theme.tcss"
    BINDINGS = [
        Binding("escape", "back", "Back", show=False),
        Binding("q", "quit_confirm", "Quit", show=False),
    ]

    def __init__(
        self,
        *,
        data_dir: Path | None = None,
        database: Database | None = None,
        players: PlayerRepository | None = None,
        results: ResultRepository | None = None,
    ) -> None:
        """Create the application.

        Args:
            data_dir: Optional data directory override.
            database: Optional pre-initialized database (used by tests).
            players: Optional player repository (used by tests).
            results: Optional result repository (used by tests).
        """
        super().__init__()
        self._data_dir = data_dir
        self._database = database
        self._players = players
        self._results = results
        self._app_context: AppContext | None = None

    @property
    def context(self) -> AppContext:
        """Return the initialized application context."""
        if self._app_context is None:
            raise RuntimeError("Application context is not initialized.")
        return self._app_context

    def on_mount(self) -> None:
        """Initialize persistence and show the main menu."""
        try:
            database = self._database
            if database is None:
                database = Database(database_path(self._data_dir))
                database.initialize()
            players = self._players or PlayerRepository(database)
            results = self._results or ResultRepository(database)
            self._app_context = AppContext(
                registry=build_default_registry(),
                players=players,
                results=results,
            )
        except Exception as exc:  # pragma: no cover - defensive startup guard
            self.notify(f"Could not initialize storage: {exc}", severity="error")
            self.exit(return_code=1)
            return

        self.push_screen(MainMenuScreen(self.context))

    async def action_back(self) -> None:
        """Leave the current screen when possible."""
        if self._app_context is None:
            return
        if isinstance(self.screen, MainMenuScreen):
            return
        if len(self.screen_stack) > 2:
            self.pop_screen()

    def action_quit_confirm(self) -> None:
        """Ask for confirmation before quitting."""
        if self._app_context is None:
            return
        if isinstance(self.screen, ConfirmQuitScreen):
            return
        self.push_screen(ConfirmQuitScreen())


def run_app(data_dir: Path | None = None) -> int:
    """Run the Textual application and return its exit code."""
    app = AsciicadeApp(data_dir=data_dir)
    app.run()
    return app.return_code or 0


if __name__ == "__main__":
    raise SystemExit(run_app())
