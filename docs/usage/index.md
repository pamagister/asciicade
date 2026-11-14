# Using Asciicade

This page covers the shared interface, keyboard controls, player profiles and saved data.
Game-specific rules and options are on the [Snake](../games/snake.md) and [Pong](../games/pong.md) pages.

## Controls

| Action | Key |
|---|---|
| Menu up / down | Arrow Up / Arrow Down |
| Menu confirm | Enter, Space or Right |
| Menu back | Left or Escape |
| Main-menu exit | Three quick Escape presses within 1.5 s |
| Pause / resume | Escape or P |
| Leave game while paused | Enter |
| Quit application | Q, then confirm |
| Toggle / cycle game option | Space or Enter |
| Change game option value | Left or Right |

The application starts in the main menu. Choose Single Player or Two Players first, then select
a player. The game selection screen is always shown next, even when only one game is registered,
and shows a description of the highlighted game. Choose a game, then open its menu to adjust
game-specific options, read the instructions or press Play to start.

In the game menu, highlight an option and use Space or Enter to cycle it, or Left/Right to change
its value. The disabled `--- Options ---` separator is skipped while navigating; Left on Play or
Instructions goes back.

Player 1 uses the arrow keys by default. Player 2 uses W/A/S/D. In single-player mode, WASD is
accepted as an alternative to the arrow keys. Pong uses the same mapping: Player 1 controls the
left paddle with the arrow keys and Player 2 controls the right paddle with W/S. Direction changes
are buffered and applied on the next game tick for Snake. Immediate 180-degree reversals are
rejected.

During a game, Escape or P pauses and resumes. While paused, Enter opens a dialog to open the game
menu, return to the main menu or stay in the game. Q always opens a quit confirmation; confirming
exits the application. On the game-over screen, the arrow keys move between actions, Enter or Space
selects one, and Escape returns to the game menu. The instructions screen scrolls with Up/Down,
PageUp/PageDown or Space; Left or Escape goes back.

## Player profiles, colors and high scores

- Player profiles are persistent and can be created from the player-selection screen.
- A guest option is available for quick sessions without creating a profile.
- Guest player 1 uses green and guest player 2 uses cyan.
- Profiles can be edited with `E` on a highlighted profile or through the `Edit player` menu entry.
  The edit dialog changes the name and color.
- The color palette contains the eight normal terminal colors and their eight bright/neon variants.
- A profile cannot occupy both player slots in a two-player match.
- Single-player scores appear in the leaderboard.
- Multiplayer results appear in the match history with both participants, scores and the winner or
  draw.
- Guest results are stored without a permanent profile.

Application data is stored in the XDG data directory, normally:

```text
~/.local/share/asciicade/asciicade.db
```

Set `XDG_DATA_HOME` to change the base directory.

## Game controls

- **Snake:** Player 1 uses the arrow keys, Player 2 uses W/A/S/D. In single-player mode, WASD is
  accepted as an alternative to the arrow keys.
- **Pong:** Player 1 uses the arrow keys, Player 2 uses W and S. In single-player mode, the human
  can use either the arrow keys or WASD.

See the [Snake](../games/snake.md) and [Pong](../games/pong.md) pages for rules, options and terminal
previews.