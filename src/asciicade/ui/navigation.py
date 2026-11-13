"""Screen navigation helpers."""

from __future__ import annotations

from textual.app import App

from asciicade.ui.context import AppContext


def go_to_main_menu(app: App[None], context: AppContext) -> None:
    """Return to the main menu, discarding deeper screens."""
    from asciicade.ui.screens.main_menu import MainMenuScreen

    while len(app.screen_stack) > 2:
        app.pop_screen()
    if not isinstance(app.screen, MainMenuScreen):
        app.push_screen(MainMenuScreen(context))
