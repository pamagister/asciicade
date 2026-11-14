# Asciicade

Asciicade is a polished, extensible arcade game collection for Linux terminals.


## Features

- Unified retro/neon terminal interface built with [Textual](https://textual.textualize.io/).
- Persistent player profiles stored in SQLite.
- Player profiles with 16 selectable terminal colors.
- Snake single-player mode.
- Snake competitive local two-player mode on one keyboard.
- Pong single-player mode against a computer opponent.
- Pong competitive local two-player mode on one keyboard.
- Per-game options (for example Snake difficulty and wrap-around walls, or Pong
  score limit and difficulty).
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

## Quick start

```bash
asciicade [--data-dir PATH] [--version]
```

- `--data-dir PATH` overrides the directory used for persistent game data.
- `--version` prints the installed version.

Choose Single Player or Two Players, select a player, then choose a game. Use the
arrow keys, Enter or Space to navigate and confirm; Left or Escape goes back.
See [Using Asciicade](usage/index.md) for the full control reference, player
profiles and saved data.

## Games

- [Snake](games/snake.md) — classic arcade Snake for one or two local players;
  eat food, grow longer and avoid crashing, with adjustable difficulty and
  wrap-around walls.
- [Pong](games/pong.md) — classic arcade Pong for one or two local players;
  aim with the paddle edges, use half-block rendering and choose the score limit
  and difficulty.

## Documentation

- [Using Asciicade](usage/index.md) — controls, player profiles, high scores and
  the data directory.
- [Architecture](develop/architecture.md) — code layout and extension points.
- [Development](develop/development.md) — setup, tests, documentation and releases.
- [Funding](funding/funding.md) — ways to support the project.

```{toctree}
:hidden:
:caption: Documentation
:maxdepth: 2

games/snake
games/pong
usage/index
develop/architecture
develop/development
funding/funding
```

## License

Asciicade is released under the Unlicense (public domain). See [LICENSE](https://github.com/pamagister/asciicade/blob/main/LICENSE).