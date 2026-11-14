# Asciicade

Asciicade is a polished, extensible arcade game collection for Linux terminals.

The initial release, **v0.1.0**, focuses on Snake and provides a unified terminal
interface, persistent player profiles, local two-player matches, high scores and
match history.

## Features

- Unified retro/neon terminal interface built with [Textual](https://textual.textualize.io/).
- Persistent player profiles stored in SQLite.
- Player profiles with 16 selectable terminal colors.
- Snake single-player mode.
- Snake competitive local two-player mode on one keyboard.
- Persistent high scores and match history.
- Short in-application instructions.
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

Snake arena:

```text
SNAKE — SINGLE-PLAYER
Guest 1: 3

+----------------------------------------------+
|                                              |
|        ██████████                            |
|        ██      ██                            |
|        ██      ██                            |
|        ██      ████████11  **               |
|                                              |
+----------------------------------------------+
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

Supported Python versions are 3.11 and newer. CI tests 3.11, 3.12, 3.13 and
3.14 on Linux.

## Usage

```bash
asciicade [--data-dir PATH] [--version]
```

- `--data-dir PATH` overrides the directory used for persistent game data.
- `--version` prints the installed version.

The application starts in the main menu. Choose Single Player or Two Players
first, then select a player. If only one game is registered, it starts directly;
otherwise the last played game is preselected. Use the arrow keys and Enter to
navigate, or select an entry directly.

## Controls

| Action | Key |
|---|---|
| Menu up / down | Arrow Up / Arrow Down |
| Menu confirm | Enter or Right |
| Menu back | Left or Escape |
| Pause / resume or go back in game | Escape |
| Quit or leave the current game | Q |

Player 1 uses the arrow keys by default. Player 2 uses W/A/S/D. In single-player
mode, WASD is accepted as an alternative to the arrow keys. Direction changes are
buffered and applied on the next game tick. Immediate 180-degree reversals are
rejected.

## Gameplay

### Snake single-player

- Eat food to increase your score and length.
- The snake moves continuously on the grid.
- Hitting a wall or your own body ends the game.
- Your score is stored in the single-player leaderboard.

### Snake two-player

- Both players start at the same time on a shared arena.
- Both snakes compete for the same food.
- Hitting a wall, yourself or the other snake eliminates you.
- The surviving snake wins.
- If both snakes are eliminated on the same tick, the match is a draw.

Player 1 is shown in green and player 2 in cyan by default. Player profiles can
choose from 16 terminal colors, including the eight normal and eight bright/neon
variants. Each logical arena cell is rendered as two horizontal characters, so the
playfield stays visually square in terminals where characters are about twice as
tall as they are wide. The head of each snake also uses a distinct two-character
marker (`11` or `22`), so the players remain distinguishable without relying on
color alone.

## Player profiles, colors and high scores

- Player profiles are persistent and can be created from the player-selection
  screen.
- A guest option is available for quick sessions without creating a profile.
- Guest player 1 uses green and guest player 2 uses cyan.
- Profiles can be edited with `E` on a highlighted profile or through the
  `Edit player` menu entry. The edit dialog changes the name and color.
- The color palette contains the eight normal terminal colors and their eight
  bright/neon variants.
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

## Architecture

Asciicade separates game logic, persistence and the terminal UI.

```text
src/asciicade/
├── cli/           Command-line entry point
├── core/          Player, game, input, session and result contracts
├── games/
│   └── snake/     UI-independent Snake engine and registration
├── persistence/   SQLite schema, migrations and repositories
└── ui/            Textual application, screens and theme
```

Key boundaries:

- The core has no Textual dependency and can be tested without a terminal.
- Games implement the `Game` protocol and do not execute SQL.
- Persistence is accessed through repositories.
- The application layer and UI do not contain game-specific rules.

### Extension points

To add a game:

1. Implement the `Game` protocol from `asciicade.core.game`.
2. Declare a `GameMetadata` instance with an identifier, name, description,
   supported modes and instructions.
3. Register the game in `asciicade.games.build_default_registry`.
4. Add a game-specific Textual screen for rendering and input.

The registry drives the game menu and supported modes. Game-specific screens
still need to be added when a new game is registered. Third-party plugin
discovery is intentionally not implemented yet.

## Development

Requirements: Python 3.11+ and [uv](https://docs.astral.sh/uv/).

```bash
uv sync --all-groups   # install all dependency groups
make test              # Ruff, mypy, pytest and coverage
make lint              # Ruff and mypy only
make fmt               # format and apply safe lint fixes
make build             # build sdist and wheel
make validate          # build and run twine check
make precommit         # format, lint and test
```

Run a single test file:

```bash
uv run pytest tests/test_snake_engine.py -v
```

`docs/index.md` is the source for `README.md`. After editing it, run:

```bash
make syncdocs
```

MkDocs documentation can be built with `make docs`.

## Release

The project version is `0.1.0`. Releases are created by tagging a commit:

```bash
make release
```

Pushing a tag triggers the release workflow, which:

1. Runs the full quality gate.
2. Builds and validates the source and wheel distributions.
3. Creates a GitHub release with the distributions.
4. Publishes to PyPI using Trusted Publishing (OIDC).

Trusted Publishing does not require a long-lived PyPI API token. Configure a
pending publisher for this repository and the `release.yml` workflow in the PyPI
project settings.

## License

Asciicade is released under the Unlicense (public domain). See [LICENSE](https://github.com/pamagister/asciicade/blob/main/LICENSE).