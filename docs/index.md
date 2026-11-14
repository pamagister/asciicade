# Asciicade

Asciicade is a polished, extensible arcade game collection for Linux terminals.


## Features

- Unified terminal interface built with [Textual](https://textual.textualize.io/).
- Persistent player profiles stored in SQLite.
- Player profiles with eight selectable terminal colors.
- Snake single-player mode.
- Snake competitive local two-player mode on one keyboard.
- Pong single-player mode against a computer opponent.
- Pong competitive local two-player mode on one keyboard.
- Blockfall single-player mode with guideline scoring, levels, wall kicks and a
  ghost piece.
- Blockfall competitive local two-player mode on separate boards.
- Per-game options (for example Snake difficulty and wrap-around walls, Pong
  score limit and difficulty, or Blockfall start level, next preview and ghost
  piece).
- Persistent high scores and match history.
- Short in-application instructions.
- Optional sound effects for Snake food collection, Pong paddle hits and points,
  Blockfall single and multi-line clears, and game over. Playback uses a system
  audio player and is skipped silently when none is available.
- Consistent keyboard controls with normalized player input.
- PyPI-compatible package with the `asciicade` command.

## Terminal preview

Main menu:

```text
+--------------------------------------------------+
|                    ASCIICADE                     |
|             A modular terminal arcade            |
|                                                  |
|  +------------------------------+                |
|  | > Single Player              |                |
|  |   Two Players                |                |
|  |   High Scores                |                |
|  |   Match History              |                |
|  |   Instructions               |                |
|  |   Quit                       |                |
|  +------------------------------+                |
+--------------------------------------------------+
```

## Installation

### From PyPI

```bash
pip install asciicade
asciicade
```

`pipx` and `uv` work as well:

```bash
pipx install asciicade
# or
uv tool install asciicade
```

### From source

Requirements: Python 3.11 or newer and [uv](https://docs.astral.sh/uv/).

```bash
git clone https://github.com/pamagister/asciicade.git
cd asciicade
uv sync --all-groups
uv run asciicade
```

Supported Python versions are 3.11 and newer. CI tests 3.11 and 3.14 on Linux.

Sound effects are optional and use a system audio player. Install one of the
supported players, for example `ffmpeg` (for `ffplay`) or `pulseaudio-utils`
(for `paplay`). Set `ASCIICADE_SOUND=off` to disable playback.

## Quick start

```bash
asciicade [--data-dir PATH] [--version]
```

- `--data-dir PATH` overrides the directory used for persistent game data.
- `--version` prints the installed version.

Choose Single Player or Two Players, select a player, then choose a game. Use the
arrow keys, Enter or Space to navigate and confirm; Left or Escape goes back.
See [Controls](#controls) below for the full keyboard reference, including player
profiles and saved data.

## Controls

Asciicade uses one consistent keyboard mapping for menus, dialogs and gameplay.
The same keys work for both players; movement keys differ per player.

### Menus and dialogs

| Action | Key(s) |
|---|---|
| Move up / down | Arrow Up / Arrow Down, W / S |
| Confirm / select | Enter, Space, Right or D |
| Back / previous | Escape, Left or A |
| Move between dialog buttons | Arrow Up / Down / Left / Right, W / S / A / D |
| Cycle a game option | Space or Enter |
| Change a game option value | Left / Right or A / D |
| Edit the highlighted player profile | E |
| Undo the last player selection | Backspace |
| Scroll the instructions screen | Arrow Up / Down, W / S, PageUp / PageDown or Space |
| Quit the application | Q, then confirm |
| Exit from the main menu | Three quick Escape presses within 1.5 s |

W/A/S/D mirror the arrow keys everywhere. In two-player games they belong to
Player 2, so Player 1 uses the arrow keys and Player 2 uses W/A/S/D.

### Gameplay

| Action | Player 1 | Player 2 | Single player |
|---|---|---|---|
| Move | Arrow keys | W / A / S / D | Arrow keys or W / A / S / D |
| Action A (primary) | Space | Left Shift | Space |
| Action B (secondary) | AltGr (Right Alt / ISO Level 3 Shift) | Left Ctrl | AltGr |
| Pause / resume | Escape or P | Escape or P | Escape or P |
| Leave game while paused | Enter | Enter | Enter |
| Quit the application | Q, then confirm | Q, then confirm | Q, then confirm |

Action A and Action B are game-defined. For example, they can be used to rotate
a block left or right in a block-dropping game, or to jump and crouch in a jump
and run. Snake and Pong currently use movement only; Action A/B are the
standard for games that use action buttons.

Blockfall uses Action A and Action B for rotation. Player 1 rotates clockwise
with Space (Action A) and counterclockwise with AltGr (Action B). Player 2
rotates clockwise with Ctrl (Action B) and counterclockwise with Shift
(Action A). In single-player mode, Space or Shift rotates clockwise and AltGr or
Ctrl rotates counterclockwise.

Standalone AltGr, Shift and Ctrl key presses are only reported reliably by
terminals with Kitty keyboard protocol support. On other terminals, use Space
for Action A as the portable alternative.

### Player profiles, colors and saved data

- Player profiles are persistent and can be created from the player-selection
  screen.
- A guest option is available for quick sessions without creating a profile.
- Guest player 1 uses green and guest player 2 uses cyan.
- Profiles can be edited with `E` on a highlighted profile or through the
  `Edit player` menu entry. The edit dialog changes the name and color.
- The color palette contains the eight normal terminal colors.
- A profile cannot occupy both player slots in a two-player match.
- Single-player scores appear in the leaderboard.
- Multiplayer results appear in the match history with both participants,
  scores and the winner or draw.
- Guest results are stored without a permanent profile.

Application data is stored in the XDG data directory, normally:

```text
~/.local/share/asciicade/asciicade.db
```

Set `XDG_DATA_HOME` to change the base directory.

## Games

- [Snake](games/snake.md) — classic arcade Snake for one or two local players;
  eat food, grow longer and avoid crashing, with adjustable difficulty and
  wrap-around walls.
- [Pong](games/pong.md) — classic arcade Pong for one or two local players;
  aim with the paddle edges, use half-block rendering and choose the score limit
  and difficulty.
- [Blockfall](games/blockfall.md) — classic falling-block puzzle for one or two
  local players; arrange tetrominoes into lines, use wall kicks and a ghost
  piece, and choose the start level.

## Documentation

- [Architecture](develop/architecture.md) — code layout and extension points.
- [Development](develop/development.md) — setup, tests, documentation and releases.
- [Funding](funding/funding.md) — ways to support the project.

```{toctree}
:hidden:
:caption: Documentation
:maxdepth: 2

games/blockfall
games/snake
games/pong
develop/architecture
develop/development
funding/funding
```

## License

Asciicade is released under the Unlicense (public domain). See [LICENSE](https://github.com/pamagister/asciicade/blob/main/LICENSE).