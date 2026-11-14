# Architecture

Asciicade separates game logic, persistence and the terminal UI.

```text
src/asciicade/
├── cli/           Command-line entry point
├── core/          Player, game, input, session and result contracts
├── games/
│   ├── blockfall/  UI-independent Blockfall engine and registration
│   ├── pong/      UI-independent Pong engine and registration
│   └── snake/     UI-independent Snake engine and registration
├── persistence/   SQLite schema, migrations and repositories
└── ui/            Textual application, screens and theme
```

Key boundaries:

- The core has no Textual dependency and can be tested without a terminal.
- Games implement the `Game` protocol and do not execute SQL.
- Persistence is accessed through repositories.
- The application layer and UI do not contain game-specific rules.

## Extension points

To add a game:

1. Implement the `Game` protocol from `asciicade.core.game`.
2. Declare a `GameMetadata` instance with an identifier, name, description,
   supported modes and instructions.
3. Register the game in `asciicade.games.build_default_registry`.
4. Add a game-specific Textual screen for rendering and input.
5. Add a documentation page under `docs/games/` and reference it from
   `docs/index.md`.

The registry drives the game menu and supported modes. Game-specific screens
still need to be added when a new game is registered. Third-party plugin
discovery is intentionally not implemented yet.
