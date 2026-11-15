# Repository Instructions

These rules apply to this Python project. Keep changes focused and follow the existing architecture.

## Python conventions

- Target Python 3.11 as declared in `pyproject.toml`.
- Follow PEP 8 and the repository's Ruff configuration: 4-space indentation, double quotes, 100-character line length.
- Use `snake_case` for packages, modules, functions and variables; `PascalCase` for classes; and `UPPER_SNAKE_CASE` for constants.
- Use `snake_case` for importable Python names. Use `kebab-case` for distribution/repository names, CLI commands and documentation paths.
- Prefer descriptive names, type hints on public function signatures, explicit imports, context managers and focused functions.
- Add or update deterministic pytest tests for behavior changes, bug fixes and important edge cases.

## Project tooling

- Use `uv` for dependency and environment management. Declare dependencies in `pyproject.toml`.
- Use Ruff for linting and formatting, and pytest for tests. Follow the existing configuration rather than introducing alternative tools.
- Inspect the Makefile before using a target. Relevant targets:
  - `make lint`: Ruff lint and format checks.
  - `make test`: lint plus the test suite and coverage reports.
  - `make fmt`: mutating formatting/fix operations and documentation synchronization.
  - `make precommit`: runs formatting, tests and dependency checks; it is mutating and may install a tool.
- Do not run mutating convenience targets merely as a substitute for understanding what they do.

## GitHub CLI

GitHub CLI (`gh`) is available for repository management and GitHub operations.

Useful commands:

```bash
gh --help
gh issue list
gh issue create --label bug
```

Prefer `gh` for GitHub issues, pull requests, and repository operations when appropriate. Check command help before using unfamiliar options. For workflow conventions around issues, commits, pushes and CI, load `git-workflow`.

## Generated documentation

- `docs/index.md` is the source for `README.md`. Never edit `README.md` directly.
- After changing `docs/index.md`, run `make syncdocs` when appropriate.
- Check existing generation scripts before editing generated files.
- Keyboard controls are documented centrally in `docs/index.md` under "Controls"
  (menus, dialogs and gameplay for Player 1 and Player 2, incl. Action A/B).
  Game docs only list controls when they deviate from this default; keep in-game
  instructions to a single control hint per screen.

## Agent workflow routing

Choose the workflow from the user's requested scope, not from whether they know or use the internal mode name.

- **Task mode:** A bounded change such as a review, typo fix, small refactor or small documentation adjustment. Load `workflow-task`.
- **Feature mode:** One self-contained feature or bug fix that needs a short design step, issue tracking, a commit, a push and CI verification. Load `workflow-feature`.
- **Autopilot:** Whenever the user asks to implement, execute or continue a plan, or names one or more phases/work packages from a plan. This includes a single selected phase. Phrases such as "implement the first phase", "execute phase 2", "continue plan.md" or "implement autonomously" are sufficient; the user does not need to say "Autopilot". Load `workflow-autopilot`. By default it executes the full plan; if the user names phases or work packages, it executes only those.

A plan or phase request always takes precedence over the single-feature workflow, even when the selected phase is the only requested scope.

Load the shared and supporting skills as needed:
- `workflow-core`: shared task loop, safety, verification, reporting and authorization rules.
- `workflow-task`: bounded implementation without commit, push or issue tracking.
- `workflow-feature`: standalone feature implementation with issue, commit, push and CI.
- `workflow-autopilot`: full-plan or selected-phase execution.
- `git-workflow`: Git, GitHub issues, `gh` CLI, commits, pushes and CI.
- `mission-planning`: turn a mission or external specification into one executable plan.

## New Game: Game protocol

- When implementing a new game, consider docs/develop/architecture.md
- also consider the gameplay controls in docs/index.md

## Game UI conventions

These conventions apply to every game screen and are easy to regress. Apply them
to new games and preserve them when changing existing ones.

- **Render each grid cell two characters wide.** Terminal cells are roughly
  twice as tall as they are wide, so a logical cell must be rendered as two
  horizontal block characters (`_CELL_WIDTH = 2`, e.g. `██`, `░░` or two
  spaces) to keep a board visually square. Every width-dependent layout must
  derive from that constant: board borders span `2 * board.width` characters,
  empty cells in previews are two characters wide, and column widths are
  measured in rendered characters. Using a single space for an empty cell
  shifts rows that begin with an empty cell and misaligns the top/bottom
  border. Reference: `src/asciicade/ui/screens/blockfall_game.py` and the fixes
  in commits `60c5751` (border width) and `7244e53` (next-piece preview).
- **Player 1 always plays on the right.** Player 1 uses the arrow keys and sits
  on the right side of a shared keyboard, so in two-player mode Player 1 owns
  the right field/board and Player 2 (W/A/S/D) owns the left. Keep the engine,
  the renderer and the game documentation consistent with this. Reference:
  Pong commit `be68f50`; Blockfall `_render_middle` places Player 2's board on
  the left and Player 1's on the right.
