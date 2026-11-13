# Asciicade – Implementation Plan

## 1. Project Mission

Build **Asciicade**, a polished, extensible arcade game collection for Linux terminals.

The initial release (v0.1.0) focuses exclusively on Snake. The architecture must nevertheless support adding further games later without requiring changes to the application core, player management, persistence layer, or general user interface.

The application should provide:

- A unified terminal-based user interface.
- Single-player and local two-player gameplay.
- Persistent player profiles.
- Persistent high scores and match results.
- Consistent controls and interaction patterns.
- Short, accessible in-application instructions.
- Straightforward installation and execution through PyPI.
- Automated quality checks, testing, building, and publishing through GitHub Actions.

The implementation should prioritize simplicity, maintainability, testability, and a clearly separated architecture.

## 2. Scope

### 2.1 Initial Release

Version 0.1.0 includes:

- Main menu and navigation.
- Player profile management.
- Snake single-player mode.
- Snake competitive local multiplayer mode.
- High-score and match-result persistence.
- Game-specific instructions.
- Consistent keyboard controls.
- Terminal UI with a retro/neon-inspired visual style.
- PyPI-compatible package and CLI entry point.
- Automated CI/CD pipeline.

### 2.2 Explicitly Out of Scope

Do not implement:

- Additional games.
- Online multiplayer.
- Network functionality.
- Remote leaderboards.
- Artificial intelligence opponents.
- Game modding interfaces.
- External plugin loading.
- Complex animation or graphics beyond terminal capabilities.

The architecture should allow future expansion without implementing speculative abstractions prematurely.

## 3. Technical Decisions

### 3.1 Runtime and Packaging

- Python >=3.11.
- Do not impose an upper Python version limit.
- Use `uv` for dependency and environment management.
- Use `pyproject.toml` as the central project configuration.
- Maintain a committed `uv.lock`.
- Provide the `asciicade` command-line entry point.
- Ensure the package can be built and installed through standard Python packaging tools.
- Review the existing setuptools/setuptools_scm configuration before deciding whether a migration to another build backend is justified.

### 3.2 Technology Stack

| Component | Technology |
|---|---|
| Language | Python >=3.11 |
| Terminal UI | Textual |
| Terminal rendering | Rich (integrated through Textual) |
| Persistence | SQLite |
| Dependency management | uv |
| Testing | pytest |
| Linting and formatting | Ruff |
| Type checking | mypy |
| CI/CD | GitHub Actions |
| Packaging | Existing pyproject.toml build configuration, subject to review |

Avoid unnecessary dependencies.

### 3.3 Architectural Principles

1. Separate game logic from terminal UI.
2. Keep the application core independent of individual games.
3. Keep persistence independent of individual games.
4. Use explicit interfaces between components.
5. Prefer straightforward implementations over premature abstraction.
6. Make game logic deterministic and independently testable.
7. Keep the initial implementation small while preserving clear extension points.
8. Avoid global mutable state.
9. Use type hints consistently.
10. Document architectural decisions where they are not self-explanatory.

## 4. Application Architecture

Use a modular architecture with the following conceptual components:

### 4.1 Application Layer

Responsible for:

- Application startup and shutdown.
- Main menu and navigation.
- Player selection.
- Game selection.
- Starting and ending game sessions.
- Coordinating the UI, game engine, and persistence layer.

The application layer must not contain game-specific rules.

### 4.2 Terminal UI

Use Textual for the terminal interface.

Responsibilities:

- Main menu.
- Player management screens.
- Game selection.
- Game rendering.
- High-score views.
- Instructions and help screens.
- Pause and game-over screens.

The UI must communicate with the game engine through defined interfaces rather than manipulating game state directly.

### 4.3 Arcade Core

Provide shared functionality for all games:

- Game lifecycle.
- Game session management.
- Game mode definitions.
- Player and input abstractions.
- Game registration and discovery within the application.
- Shared game result structures.
- Common game configuration.

The core must not depend on Snake-specific implementation details.

### 4.4 Game Interface

Define a minimal interface that every game must implement.

A game should be able to:

- Declare its name and metadata.
- Declare supported game modes.
- Initialize a game session.
- Receive input events.
- Advance its state through game ticks.
- Report its current state.
- Determine whether the game has ended.
- Return a structured result.

The interface must support games with different mechanics without forcing unnecessary functionality on every game.

For example, a future turn-based game should not need to implement real-time movement merely to satisfy the interface.

### 4.5 Game Registry

Implement a simple internal registry.

Each game registers itself and provides its metadata and supported modes.

The application menu should derive available games and modes from this registry rather than maintaining a separate hard-coded list.

For the initial release, only Snake is registered.

Do not implement third-party plugin discovery or Python entry-point based game loading yet.

### 4.6 Player Management

Support persistent player profiles.

A profile should contain at least:

- Unique identifier.
- Display name.
- Creation timestamp.

Gameplay requirements:

- Single-player mode: select one player.
- Two-player mode: select two distinct players.
- Allow creation of new profiles.
- Provide a guest option without requiring permanent profile creation.
- Prevent the same profile from occupying both player slots in competitive multiplayer.

Player identity must be independent of the game implementation.

### 4.7 Input Management

Provide a centralized input abstraction.

Default keyboard mapping:

| Action | Player 1 | Player 2 |
|---|---|---|
| Up | Arrow Up | W |
| Down | Arrow Down | S |
| Left | Arrow Left | A |
| Right | Arrow Right | D |

Global controls:

- Escape: pause or return to the appropriate menu.
- Q: quit or leave the current game, subject to confirmation where appropriate.

Requirements:

- Game-specific controls must be configurable through the input abstraction.
- The UI must not hard-code game mechanics into keyboard handlers.
- The game engine receives normalized input events.
- Input handling must support independent player input.
- For Snake, buffer requested directions and apply them at the next game tick.
- Reject immediate 180-degree direction changes.
- Avoid relying on continuous physical key-state detection, since terminal input behavior varies between environments.

The architecture should remain suitable for future real-time games, while acknowledging that different terminal environments may have different input capabilities.

### 4.8 Persistence Layer

Use SQLite for persistent application data.

Responsibilities:

- Player profiles.
- Game results.
- High scores.
- Match history.

Keep database access behind repository or service interfaces.

Game implementations must not execute SQL directly.

Use database migrations or another explicit, versioned schema initialization strategy.

Store application data in an appropriate XDG data directory, typically:

`~/.local/share/asciicade/`

Keep configuration data separate under the XDG configuration directory.

## 5. Snake – Game Specification

### 5.1 Single-Player Mode

Implement classic Snake:

- One player controls one snake.
- The snake moves continuously on a grid.
- Food appears at valid positions.
- Eating food increases the score and snake length.
- The snake dies when colliding with a wall or itself.
- The game ends when the snake dies.
- Display the current score and final result.

The game speed should be configurable internally, with sensible defaults.

Do not introduce a complicated difficulty system in the initial release.

### 5.2 Competitive Two-Player Mode

Implement local competitive multiplayer on one shared keyboard and one shared terminal screen.

Rules:

- Both players start simultaneously.
- Each player controls an independent snake.
- Both snakes share the same arena.
- Both players compete for the same food.
- Eating food increases the respective player's score and snake length.
- Players can collide with walls, themselves, or the opposing snake.
- A collision eliminates the affected player.
- The surviving player wins.
- If both players are eliminated during the same game tick, the match ends in a draw.

Player identification should be visually clear:

- Player 1: green.
- Player 2: cyan.

Use additional visual indicators where necessary so that the distinction does not rely exclusively on color.

The game should display:

- Both player names.
- Individual scores.
- Current game state.
- Winner or draw result.

Define collision resolution deterministically, particularly for cases where both snakes move into the same cell during the same tick.

### 5.3 Snake Game Engine

Keep the Snake implementation independent of Textual.

Represent the game state using explicit data structures.

Separate:

- Snake state.
- Food position.
- Arena dimensions.
- Movement and direction.
- Collision detection.
- Scoring.
- Game lifecycle.
- Game mode rules.

The engine must be testable without starting a terminal UI.

Use deterministic update logic wherever possible. Random food placement should be injectable or otherwise controllable in tests.

## 6. User Experience

### 6.1 Visual Design

Create a coherent retro arcade appearance.

Design goals:

- Dark terminal background.
- Neon-inspired accent colors.
- Clear typography and visual hierarchy.
- Consistent menu and screen layouts.
- Minimal visual clutter.
- Readable game information.

Use Textual widgets and styling rather than implementing a custom terminal rendering framework.

### 6.2 Navigation

The application should provide a clear navigation flow:

1. Main Menu.
2. Select Game.
3. Select Game Mode.
4. Select Player or Players.
5. Start Game.
6. Pause or Resume.
7. Game Over.
8. High Scores or Main Menu.

Avoid unnecessary navigation depth.

### 6.3 Instructions

Every game must provide short in-application instructions.

For Snake, explain:

- Objective.
- Movement controls.
- Scoring.
- Collision rules.
- Multiplayer rules where applicable.

Instructions should be available before starting a game and accessible during gameplay.

Do not require users to consult external documentation for basic gameplay.

## 7. High Scores and Match History

Implement persistent results for both game modes.

Store at least:

- Game identifier.
- Game mode.
- Player identifiers.
- Individual scores.
- Match outcome.
- Timestamp.

Single-player:

- Maintain a leaderboard based on score.
- Associate scores with player profiles where available.

Two-player:

- Store both participants.
- Store individual scores.
- Store the match outcome.
- Support a match history view.

Guest results may be stored without a permanent player profile.

Avoid designing an elaborate ranking or achievement system for the initial release.

## 8. Implementation Phases

Each phase must be implemented and validated before moving to the next phase.

The agent should update the project documentation and implementation progress as work proceeds.

### Phase 1 – Repository Assessment and Project Foundation [x]

Objectives:

- Inspect the existing repository and template structure.
- Understand the current packaging, CLI, configuration, and CI setup.
- Identify reusable components.
- Remove template-specific functionality that does not belong in Asciicade.
- Establish the project structure and technical baseline.

Tasks:

- [x] Review `pyproject.toml`, README, workflows, package structure, tests, and configuration files.
- [x] Identify obsolete template features and dependencies.
- [x] Set the supported Python version to >=3.11.
- [x] Configure `uv` and generate/update `uv.lock`.
- [x] Establish Textual as the terminal UI dependency.
- [x] Review and configure the build backend.
- [x] Establish Ruff, pytest, and mypy configuration.
- [x] Define the initial package structure.
- [x] Ensure the CLI entry point is valid.
- [x] Update basic project metadata.

Acceptance criteria:

- The project installs and runs in a clean environment.
- `uv sync` succeeds.
- The package builds successfully.
- The `asciicade` command is available.
- Static checks and an initial test suite run successfully.
- No obsolete template-specific behavior remains unintentionally exposed.

### Phase 2 – Core Architecture and Data Models [x]

Objectives:

Establish the minimal application architecture and shared interfaces.

Tasks:

- [x] Implement the application layer.
- [x] Define player and game session models.
- [x] Define game mode abstractions.
- [x] Define the game interface.
- [x] Implement the internal game registry.
- [x] Implement normalized input events and player input mappings.
- [x] Define structured game results.
- [x] Establish clear boundaries between application, UI, core, games, and persistence.
- [x] Add unit tests for the shared models and interfaces.

Acceptance criteria:

- The core can operate without starting Textual.
- A game can be registered without changing the application menu implementation.
- Game modes can be declared by individual games.
- Player input can be normalized independently of game logic.
- The architecture contains no unnecessary Snake-specific dependencies.

### Phase 3 – Persistence and Player Management [x]

Objectives:

Implement persistent player profiles and game result storage.

Tasks:

- [x] Initialize the SQLite database.
- [x] Define the database schema.
- [x] Implement schema versioning or migrations.
- [x] Implement player repositories.
- [x] Implement game result repositories.
- [x] Implement player creation and retrieval.
- [x] Implement guest-player handling.
- [x] Implement player selection for one- and two-player sessions.
- [x] Prevent selecting the same profile twice in multiplayer.
- [x] Add persistence tests.

Acceptance criteria:

- Profiles survive application restarts.
- Players can be created and selected.
- Guest sessions work without permanent profiles.
- Two-player sessions require distinct profiles or distinct guest identities.
- Game results can be stored and retrieved.
- Database operations are isolated from game implementations.

### Phase 4 – Terminal UI Foundation [x]

Objectives:

Build the common Textual interface.

Tasks:

- [x] Implement the application entry point.
- [x] Implement the main menu.
- [x] Implement navigation between screens.
- [x] Implement game and mode selection based on the registry.
- [x] Implement player selection screens.
- [x] Implement common dialogs and notifications.
- [x] Implement global keyboard controls.
- [x] Establish reusable screen and widget styling.
- [x] Implement the initial retro/neon visual theme.

Acceptance criteria:

- The application starts in the terminal.
- Navigation works without errors.
- Registered games and supported modes are displayed automatically.
- Player selection is functional.
- Global controls behave consistently.
- The UI does not contain game-specific business logic.

### Phase 5 – Snake Game Engine [x]

Objectives:

Implement the complete Snake game logic independently of the UI.

Tasks:

- [x] Implement the arena model.
- [x] Implement snake state and movement.
- [x] Implement direction changes and input buffering.
- [x] Implement food placement.
- [x] Implement scoring and growth.
- [x] Implement wall and self-collision detection.
- [x] Implement competitive multiplayer state.
- [x] Implement collisions between both snakes.
- [x] Implement deterministic simultaneous collision resolution.
- [x] Implement win, loss, and draw conditions.
- [x] Add comprehensive unit tests.

Acceptance criteria:

- Single-player Snake works through the engine.
- Competitive two-player Snake works through the engine.
- Both game modes follow the specified rules.
- Direction reversal is prevented.
- Collision handling is deterministic.
- Food never spawns inside an occupied cell.
- The engine can be tested without Textual.
- Edge cases are covered by automated tests.

### Phase 6 – Snake UI Integration [x]

Objectives:

Connect the Snake engine to the common terminal interface.

Tasks:

- [x] Register Snake in the game registry.
- [x] Implement the Snake game screen.
- [x] Render the arena and both snakes.
- [x] Render food and game information.
- [x] Connect keyboard events to normalized player input.
- [x] Implement the game tick using Textual timers.
- [x] Implement pause and resume.
- [x] Implement game-over screens.
- [x] Display scores and match outcomes.
- [x] Provide in-application instructions.
- [x] Validate the visual experience in a real terminal (headless Textual pilot at 80x24 and 100x30; no interactive terminal available in this environment).

Acceptance criteria:

- Snake can be started from the main menu.
- Single-player gameplay is fully functional.
- Two-player gameplay is fully functional using the arrow keys and WASD.
- Both players can play simultaneously.
- Pause, resume, and game-over behavior work correctly.
- The UI remains responsive during gameplay.
- The game engine remains independent of Textual.

### Phase 7 – High Scores and Match History UI [x]

Objectives:

Make persistent results accessible through the application.

Tasks:

- [x] Save completed game results.
- [x] Implement the single-player leaderboard.
- [x] Implement multiplayer match history.
- [x] Display player names and individual scores.
- [x] Display winners and draws.
- [x] Implement sorting and basic filtering where useful.
- [x] Handle missing or deleted player profiles gracefully.

Acceptance criteria:

- Results are persisted after completed games.
- Single-player high scores are displayed correctly.
- Multiplayer results show both participants and the outcome.
- Results survive application restarts.
- The UI handles empty result sets and guest players correctly.

### Phase 8 – Quality Assurance and User Experience

Objectives:

Polish the initial release and validate the complete application.

Tasks:

- [ ] Review all navigation flows.
- [ ] Test gameplay in supported terminal environments.
- [ ] Check keyboard handling and responsiveness.
- [ ] Review visual consistency.
- [ ] Check terminal resizing behavior.
- [ ] Validate error handling and database recovery behavior.
- [ ] Review accessibility and readability.
- [ ] Remove dead code and unnecessary dependencies.
- [ ] Review type hints and documentation.
- [ ] Run the complete test and quality-check suite.

Acceptance criteria:

- No known critical gameplay or navigation defects remain.
- The application handles common error conditions gracefully.
- Terminal resizing does not break the application.
- The complete automated test suite passes.
- Static checks pass.
- The implementation remains appropriately simple.

### Phase 9 – CI/CD and PyPI Release Preparation

Objectives:

Establish reliable automated validation and publishing.

Tasks:

- [ ] Review and simplify the existing GitHub Actions workflows.
- [ ] Run CI on pushes and pull requests.
- [ ] Test supported Python versions starting at 3.11 and including current stable versions.
- [ ] Run Ruff checks.
- [ ] Run mypy.
- [ ] Run pytest.
- [ ] Build source and wheel distributions.
- [ ] Validate distribution contents.
- [ ] Test installation from the built wheel.
- [ ] Configure PyPI publishing through GitHub Actions using Trusted Publishing/OIDC where supported.
- [ ] Restrict publishing to intentional release events or version tags.

Acceptance criteria:

- CI passes on all supported Python versions.
- Package distributions build successfully.
- A wheel can be installed and the CLI can be executed.
- Publishing is not triggered by ordinary pushes or pull requests.
- Release publishing does not require a long-lived PyPI API token when Trusted Publishing is available.

### Phase 10 – Documentation and Initial Release

Objectives:

Prepare Asciicade for public use.

Tasks:

- [ ] Replace the template README with project documentation.
- [ ] Document installation through PyPI.
- [ ] Document development setup using uv.
- [ ] Document supported Python versions.
- [ ] Document controls and gameplay.
- [ ] Document player profiles and high scores.
- [ ] Add screenshots or terminal demonstrations where useful.
- [ ] Document the architecture and extension points.
- [ ] Add license and release metadata.
- [ ] Prepare version 0.1.0.

Acceptance criteria:

- A new user can install and start Asciicade using the README.
- Basic gameplay does not require external instructions.
- Development setup is reproducible.
- Package metadata and documentation are consistent.
- Version 0.1.0 can be released through the configured workflow.

## 9. Testing Strategy

Testing must be implemented throughout development, not postponed until the end.

### Unit Tests

Cover:

- Game models.
- Player models.
- Input normalization.
- Snake movement.
- Direction changes.
- Food placement.
- Scoring.
- Collision detection.
- Multiplayer collision resolution.
- Win/loss/draw conditions.
- Persistence repositories.

### Integration Tests

Cover:

- Database initialization and persistence.
- Player creation and selection.
- Game registration and discovery.
- Game session lifecycle.
- Result persistence.
- CLI startup.

### UI Tests

Use Textual's testing facilities where practical.

Cover:

- Main menu navigation.
- Player selection.
- Game mode selection.
- Pause and resume.
- Game-over navigation.
- High-score display.

Avoid tests that depend on timing-sensitive real terminal input where deterministic alternatives are available.

## 10. Suggested Package Structure

The exact structure may be adjusted during Phase 1, but the separation of responsibilities must be preserved.

```text
src/
└── asciicade/
    ├── __init__.py
    ├── cli.py
    ├── app.py
    │
    ├── core/
    │   ├── __init__.py
    │   ├── game.py
    │   ├── registry.py
    │   ├── session.py
    │   ├── input.py
    │   ├── player.py
    │   └── results.py
    │
    ├── games/
    │   ├── __init__.py
    │   └── snake/
    │       ├── __init__.py
    │       ├── game.py
    │       ├── models.py
    │       ├── engine.py
    │       └── rules.py
    │
    ├── persistence/
    │   ├── __init__.py
    │   ├── database.py
    │   ├── migrations.py
    │   ├── players.py
    │   └── results.py
    │
    └── ui/
        ├── __init__.py
        ├── screens/
        ├── widgets/
        └── styles/
```

Keep the structure proportional to the actual implementation. Do not create empty modules or abstractions merely to match this proposal.

## 11. Agent Execution Rules

The implementation agent must follow these rules:

1. Work through the phases in order.
2. Inspect existing code before modifying it.
3. Preserve useful existing functionality.
4. Do not rewrite working infrastructure without a clear reason.
5. Keep each phase focused and independently verifiable.
6. Add or update tests alongside implementation.
7. Run relevant tests and quality checks before declaring a phase complete.
8. Do not silently skip failed checks.
9. Document deviations from the plan and explain their rationale.
10. Update implementation progress after each completed phase.
11. Ask for clarification only when a decision materially affects architecture, behavior, or scope.
12. Do not introduce additional games or features without explicit approval.
13. Do not commit or push changes unless explicitly requested.

At the end of each phase, provide:

- Summary of implemented functionality.
- Important architectural decisions.
- Files added, modified, or removed.
- Tests and checks executed.
- Results of those checks.
- Known limitations.
- Next phase and remaining work.

## 12. Definition of Done

The initial release is complete when:

- Asciicade installs and runs as a Python package.
- The terminal UI provides a coherent arcade experience.
- Player profiles can be created and selected.
- Single-player Snake works correctly.
- Competitive local two-player Snake works correctly.
- Both players can use the same keyboard with independent controls.
- High scores and match results persist.
- Instructions are available inside the application.
- Automated tests and quality checks pass.
- GitHub Actions builds the package successfully.
- PyPI publishing is configured.
- Documentation is sufficient for users and contributors.

The result should be a small, polished, reliable first release with a sound foundation for future games.

