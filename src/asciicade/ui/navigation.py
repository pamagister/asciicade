"""Screen navigation helpers."""

from __future__ import annotations

from textual.app import App

from asciicade.core.game import GameMode
from asciicade.core.options import GameOptions
from asciicade.core.player import GuestPlayer, PlayerProfile
from asciicade.core.registry import GameRegistration
from asciicade.ui.context import AppContext


def go_to_main_menu(app: App[None], context: AppContext) -> None:
    """Return to the main menu, discarding deeper screens."""
    from asciicade.ui.screens.main_menu import MainMenuScreen

    while len(app.screen_stack) > 2:
        app.pop_screen()
    if isinstance(app.screen, MainMenuScreen):
        return
    if len(app.screen_stack) == 1:
        app.push_screen(MainMenuScreen(context))
    else:
        app.switch_screen(MainMenuScreen(context))


def go_to_game_menu(
    app: App[None],
    context: AppContext,
    registration: GameRegistration,
    mode: GameMode,
    players: tuple[PlayerProfile | GuestPlayer, ...],
    options: GameOptions | None,
) -> None:
    """Return to the game menu, discarding gameplay screens."""
    from asciicade.ui.screens.game_menu import GameMenuScreen

    stack = app.screen_stack
    for index in range(len(stack) - 1, -1, -1):
        if isinstance(stack[index], GameMenuScreen):
            while len(app.screen_stack) - 1 > index:
                app.pop_screen()
            return

    go_to_main_menu(app, context)
    app.push_screen(GameMenuScreen(context, registration, mode, players, options=options))
