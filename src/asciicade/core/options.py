"""Game option definitions and resolved option values."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class ChoiceOptionDefinition:
    """A single-choice option with a finite set of allowed values.

    Attributes:
        key: Stable identifier used to store and resolve the value.
        label: Human-readable label shown in the options menu.
        values: Allowed values in selection order.
        default: Default value; must be contained in ``values``.
    """

    key: str
    label: str
    values: tuple[str, ...]
    default: str

    def __post_init__(self) -> None:
        """Validate the option definition."""
        if not self.key.strip():
            raise ValueError("Option key must not be empty.")
        if not self.label.strip():
            raise ValueError("Option label must not be empty.")
        if not self.values:
            raise ValueError("Choice option must declare at least one value.")
        if len(set(self.values)) != len(self.values):
            raise ValueError("Choice option values must be unique.")
        if self.default not in self.values:
            raise ValueError(f"Default value {self.default!r} is not in allowed values.")

    def index_of(self, value: str) -> int:
        """Return the selection index for a value.

        Raises:
            ValueError: If the value is not allowed.
        """
        try:
            return self.values.index(value)
        except ValueError as exc:
            raise ValueError(f"Value {value!r} is not allowed for option {self.key!r}.") from exc

    @property
    def is_choice(self) -> bool:
        """Return whether this definition describes a choice option."""
        return True

    @property
    def is_boolean(self) -> bool:
        """Return whether this definition describes a boolean option."""
        return False


@dataclass(frozen=True, slots=True)
class BooleanOptionDefinition:
    """A yes/no option.

    Attributes:
        key: Stable identifier used to store and resolve the value.
        label: Human-readable label shown in the options menu.
        default: Default value, either ``True`` (on) or ``False`` (off).
    """

    key: str
    label: str
    default: bool

    def __post_init__(self) -> None:
        """Validate the option definition."""
        if not self.key.strip():
            raise ValueError("Option key must not be empty.")
        if not self.label.strip():
            raise ValueError("Option label must not be empty.")

    @property
    def is_choice(self) -> bool:
        """Return whether this definition describes a choice option."""
        return False

    @property
    def is_boolean(self) -> bool:
        """Return whether this definition describes a boolean option."""
        return True


@dataclass(frozen=True, slots=True)
class GameOptions:
    """Resolved values for the options of one game."""

    values: tuple[tuple[str, str], ...]

    def value_for(self, key: str) -> str:
        """Return the resolved value for an option key.

        Raises:
            KeyError: If no option with the given key exists.
        """
        for stored_key, value in self.values:
            if stored_key == key:
                return value
        raise KeyError(f"Unknown game option key: {key!r}")

    def with_value(self, key: str, value: str) -> GameOptions:
        """Return a copy with the value for ``key`` replaced or added."""
        updated = list(self.values)
        for index, (stored_key, _) in enumerate(updated):
            if stored_key == key:
                updated[index] = (key, value)
                return GameOptions(tuple(updated))
        updated.append((key, value))
        return GameOptions(tuple(updated))


@dataclass(frozen=True, slots=True)
class GameOptionRegistry:
    """All option definitions for one game."""

    definitions: tuple[ChoiceOptionDefinition | BooleanOptionDefinition, ...]

    def defaults(self) -> GameOptions:
        """Return the default values for all options."""
        values: list[tuple[str, str]] = []
        for definition in self.definitions:
            if isinstance(definition, ChoiceOptionDefinition):
                values.append((definition.key, definition.default))
            else:
                values.append((definition.key, "on" if definition.default else "off"))
        return GameOptions(tuple(values))

    def key_for_label(self, label: str) -> str | None:
        """Return the option key for a human-readable label, if any."""
        for definition in self.definitions:
            if definition.label == label:
                return definition.key
        return None
