# Architecture

Asciicade separates game logic, persistence and the terminal UI.

```text
src/asciicade/
├── assets/        Packaged sound effects
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
2. Add a `docs.py` module next to the game that exports a `GameDocs` instance
   with the summary, single-player and two-player descriptions, one-line
   controls hints and the long controls text.
3. Declare a `GameMetadata` instance with an identifier, name, supported modes,
   the `GameDocs` instance and optional game options.
4. Register the game in `asciicade.games.build_default_registry`.
5. Add a game-specific Textual screen for rendering and input.
6. Run `make syncdocs` to regenerate `docs/games/<id>.md` and the game list in
   `docs/index.md`. Do not write generated documentation by hand.

The registry drives the game menu and supported modes. Game-specific screens
still need to be added when a new game is registered. Third-party plugin
discovery is intentionally not implemented yet.
