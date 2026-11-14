"""Tests for the game option model."""

from __future__ import annotations

import pytest

from asciicade.core.game import GameMetadata, GameMode
from asciicade.core.options import (
    BooleanOptionDefinition,
    ChoiceOptionDefinition,
    GameOptionRegistry,
    GameOptions,
)


def test_choice_option_definition_defaults() -> None:
    option = ChoiceOptionDefinition(
        key="difficulty",
        label="Difficulty",
        values=("Easy", "Medium", "Hard"),
        default="Medium",
    )
    assert option.key == "difficulty"
    assert option.label == "Difficulty"
    assert option.values == ("Easy", "Medium", "Hard")
    assert option.default == "Medium"
    assert option.is_choice
    assert not option.is_boolean


def test_choice_option_definition_validates() -> None:
    with pytest.raises(ValueError, match="Option key must not be empty"):
        ChoiceOptionDefinition(
            key="", label="Difficulty", values=("Easy", "Medium"), default="Easy"
        )
    with pytest.raises(ValueError, match="Option label must not be empty"):
        ChoiceOptionDefinition(
            key="difficulty", label="", values=("Easy", "Medium"), default="Easy"
        )
    with pytest.raises(ValueError, match="at least one value"):
        ChoiceOptionDefinition(key="difficulty", label="Difficulty", values=(), default="Easy")
    with pytest.raises(ValueError, match="values must be unique"):
        ChoiceOptionDefinition(
            key="difficulty",
            label="Difficulty",
            values=("Easy", "Easy"),
            default="Easy",
        )
    with pytest.raises(ValueError, match="not in allowed values"):
        ChoiceOptionDefinition(
            key="difficulty",
            label="Difficulty",
            values=("Easy", "Medium"),
            default="Hard",
        )


def test_boolean_option_definition_defaults() -> None:
    option = BooleanOptionDefinition(key="wrap_walls", label="Wrap walls", default=False)
    assert option.key == "wrap_walls"
    assert option.label == "Wrap walls"
    assert option.default is False
    assert not option.is_choice
    assert option.is_boolean


def test_boolean_option_definition_validates() -> None:
    with pytest.raises(ValueError, match="Option key must not be empty"):
        BooleanOptionDefinition(key="", label="Wrap walls", default=False)
    with pytest.raises(ValueError, match="Option label must not be empty"):
        BooleanOptionDefinition(key="wrap_walls", label="", default=False)


def test_game_options_value_for() -> None:
    options = GameOptions((("difficulty", "Medium"), ("wrap_walls", "off")))
    assert options.value_for("difficulty") == "Medium"
    assert options.value_for("wrap_walls") == "off"

    with pytest.raises(KeyError, match="Unknown game option key"):
        options.value_for("unknown")


def test_game_options_with_value() -> None:
    options = GameOptions((("difficulty", "Medium"), ("wrap_walls", "off")))

    updated = options.with_value("difficulty", "Hard")
    assert updated is not options
    assert updated.value_for("difficulty") == "Hard"
    assert updated.value_for("wrap_walls") == "off"
    assert options.value_for("difficulty") == "Medium"  # original unchanged

    added = options.with_value("speed", "fast")
    assert added.value_for("speed") == "fast"
    assert added.value_for("difficulty") == "Medium"


def test_game_option_registry_defaults() -> None:
    registry = GameOptionRegistry(
        definitions=(
            ChoiceOptionDefinition(
                key="difficulty",
                label="Difficulty",
                values=("Easy", "Medium", "Hard"),
                default="Medium",
            ),
            BooleanOptionDefinition(
                key="wrap_walls",
                label="Wrap walls",
                default=False,
            ),
        )
    )
    defaults = registry.defaults()
    assert defaults.value_for("difficulty") == "Medium"
    assert defaults.value_for("wrap_walls") == "off"


def test_game_metadata_rejects_duplicate_option_keys() -> None:
    with pytest.raises(ValueError, match="Option keys must be unique"):
        GameMetadata(
            identifier="snake",
            name="Snake",
            description="desc",
            modes=(GameMode.SINGLE_PLAYER,),
            instructions="instructions",
            options=GameOptionRegistry(
                definitions=(
                    ChoiceOptionDefinition(
                        key="difficulty",
                        label="Difficulty",
                        values=("Easy", "Medium"),
                        default="Easy",
                    ),
                    ChoiceOptionDefinition(
                        key="difficulty",
                        label="Difficulty again",
                        values=("Easy", "Medium"),
                        default="Easy",
                    ),
                )
            ),
        )
