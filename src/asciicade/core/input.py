"""Normalized input events and keyboard mappings."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from asciicade.core.game import GameMode


class InputAction(StrEnum):
    """A normalized, game-independent input action."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"
    PAUSE = "pause"
    QUIT = "quit"


class Direction(StrEnum):
    """A cardinal movement direction."""

    UP = "up"
    DOWN = "down"
    LEFT = "left"
    RIGHT = "right"

    @property
    def delta(self) -> tuple[int, int]:
        """Return the ``(x, y)`` offset for one step in this direction."""
        return _DELTAS[self]

    @property
    def opposite(self) -> Direction:
        """Return the reverse direction."""
        return _OPPOSITES[self]


_DELTAS: dict[Direction, tuple[int, int]] = {
    Direction.UP: (0, -1),
    Direction.DOWN: (0, 1),
    Direction.LEFT: (-1, 0),
    Direction.RIGHT: (1, 0),
}

_OPPOSITES: dict[Direction, Direction] = {
    Direction.UP: Direction.DOWN,
    Direction.DOWN: Direction.UP,
    Direction.LEFT: Direction.RIGHT,
    Direction.RIGHT: Direction.LEFT,
}

_DIRECTION_ACTIONS: dict[InputAction, Direction] = {
    InputAction.UP: Direction.UP,
    InputAction.DOWN: Direction.DOWN,
    InputAction.LEFT: Direction.LEFT,
    InputAction.RIGHT: Direction.RIGHT,
}

_KEY_ALIASES: dict[str, str] = {
    "esc": "escape",
    "return": "enter",
    "spacebar": "space",
}


def normalize_key(key: str) -> str:
    """Normalize a terminal key name.

    Args:
        key: The raw key name reported by the terminal UI.

    Returns:
        A lower-case key name with common aliases resolved.
    """
    normalized = key.strip().lower()
    return _KEY_ALIASES.get(normalized, normalized)


def direction_for_action(action: InputAction) -> Direction | None:
    """Return the direction represented by an action, if any."""
    return _DIRECTION_ACTIONS.get(action)


@dataclass(frozen=True, slots=True)
class InputEvent:
    """A normalized input event.

    ``player`` is ``None`` for global actions such as pause or quit.
    """

    action: InputAction
    player: int | None = None


@dataclass(frozen=True, slots=True)
class InputBinding:
    """A mapping from one action to one or more normalized key names."""

    action: InputAction
    keys: frozenset[str]
    player: int | None = None


class InputMap:
    """Resolve normalized key names to input events."""

    def __init__(self, bindings: tuple[InputBinding, ...]) -> None:
        """Build a map from the supplied bindings."""
        self._by_key: dict[str, InputEvent] = {}
        for binding in bindings:
            for key in binding.keys:
                self._by_key[key] = InputEvent(binding.action, binding.player)

    def resolve(self, key: str) -> InputEvent | None:
        """Resolve a raw key name to an input event."""
        return self._by_key.get(normalize_key(key))

    def keys_for(self, action: InputAction, player: int | None = None) -> frozenset[str]:
        """Return all keys bound to an action and player."""
        keys: set[str] = set()
        for key, event in self._by_key.items():
            if event.action == action and event.player == player:
                keys.add(key)
        return frozenset(keys)

    def __len__(self) -> int:
        """Return the number of bound keys."""
        return len(self._by_key)


_GLOBAL_BINDINGS: tuple[InputBinding, ...] = (
    InputBinding(InputAction.PAUSE, frozenset({"escape"})),
    InputBinding(InputAction.QUIT, frozenset({"q"})),
)

_PLAYER_ONE_BINDINGS: tuple[InputBinding, ...] = (
    InputBinding(InputAction.UP, frozenset({"up"}), player=1),
    InputBinding(InputAction.DOWN, frozenset({"down"}), player=1),
    InputBinding(InputAction.LEFT, frozenset({"left"}), player=1),
    InputBinding(InputAction.RIGHT, frozenset({"right"}), player=1),
)

_PLAYER_TWO_BINDINGS: tuple[InputBinding, ...] = (
    InputBinding(InputAction.UP, frozenset({"w"}), player=2),
    InputBinding(InputAction.DOWN, frozenset({"s"}), player=2),
    InputBinding(InputAction.LEFT, frozenset({"a"}), player=2),
    InputBinding(InputAction.RIGHT, frozenset({"d"}), player=2),
)

# In single-player mode WASD is accepted as an alternative to the arrow keys.
_SINGLE_PLAYER_WASD_BINDINGS: tuple[InputBinding, ...] = (
    InputBinding(InputAction.UP, frozenset({"w"}), player=1),
    InputBinding(InputAction.DOWN, frozenset({"s"}), player=1),
    InputBinding(InputAction.LEFT, frozenset({"a"}), player=1),
    InputBinding(InputAction.RIGHT, frozenset({"d"}), player=1),
)


def bindings_for_mode(mode: GameMode) -> tuple[InputBinding, ...]:
    """Return the default bindings for a game mode."""
    if mode is GameMode.SINGLE_PLAYER:
        return _PLAYER_ONE_BINDINGS + _SINGLE_PLAYER_WASD_BINDINGS + _GLOBAL_BINDINGS
    return _PLAYER_ONE_BINDINGS + _PLAYER_TWO_BINDINGS + _GLOBAL_BINDINGS


def input_map_for_mode(mode: GameMode) -> InputMap:
    """Build the default input map for a game mode."""
    return InputMap(bindings_for_mode(mode))
