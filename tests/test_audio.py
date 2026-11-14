"""Tests for sound effects and their gameplay event wiring."""

from __future__ import annotations

import asyncio
import subprocess
from pathlib import Path

from asciicade.core.game import GameMode
from asciicade.core.player import GuestPlayer
from asciicade.core.registry import GameRegistration, GameRegistry
from asciicade.core.results import MatchOutcome, make_game_result, make_player_result
from asciicade.games.blockfall import BlockfallGame
from asciicade.games.pong import PongGame
from asciicade.games.snake import SnakeGame
from asciicade.persistence import (
    Database,
    PlayerRepository,
    ResultRepository,
    SettingsRepository,
)
from asciicade.ui.app import AsciicadeApp
from asciicade.ui.audio import AudioPlayer, SoundEffect, sound_path
from asciicade.ui.context import AppContext
from asciicade.ui.screens.blockfall_game import BlockfallGameScreen
from asciicade.ui.screens.game_over import GameOverScreen
from asciicade.ui.screens.pong_game import PongGameScreen
from asciicade.ui.screens.snake_game import SnakeGameScreen


class FakeProcess:
    """A process stand-in that can be either running or finished."""

    def __init__(self, *, running: bool = True) -> None:
        self._running = running

    def poll(self) -> int | None:
        """Return the simulated exit status."""
        return None if self._running else 0


class RecordingAudio(AudioPlayer):
    """An audio player that records requested effects instead of playing them."""

    def __init__(self) -> None:
        super().__init__(enabled=False)
        self.played: list[SoundEffect] = []

    def play(self, effect: SoundEffect) -> None:
        """Record the requested effect."""
        self.played.append(effect)


def make_runner(
    calls: list[tuple[list[str], dict[str, object]]], process: FakeProcess | None = None
):
    """Return a process launcher that records its arguments."""
    launched = process or FakeProcess()

    def runner(command: list[str], **kwargs: object) -> FakeProcess:
        calls.append((command, kwargs))
        return launched

    return runner


def make_context(tmp_path: Path, audio: AudioPlayer) -> AppContext:
    """Create an application context with a temporary database."""
    database = Database(tmp_path / "audio.db")
    database.initialize()
    return AppContext(
        registry=GameRegistry(),
        players=PlayerRepository(database),
        results=ResultRepository(database),
        settings=SettingsRepository(database),
        audio=audio,
    )


def make_registration(game_type: type) -> GameRegistration:
    """Return a registration for a game class."""
    return GameRegistration(game_type.metadata, game_type)


def test_all_sound_effects_have_packaged_files() -> None:
    """Every declared effect has a non-empty packaged MP3 file."""
    for effect in SoundEffect:
        path = sound_path(effect)
        assert path is not None
        assert path.is_file()
        assert path.stat().st_size > 0


def test_audio_player_launches_configured_command() -> None:
    """The player launches the configured command with the packaged file."""
    calls: list[tuple[list[str], dict[str, object]]] = []
    player = AudioPlayer(
        enabled=True,
        command=("fake-player",),
        runner=make_runner(calls),
    )

    player.play(SoundEffect.PADDLE_HIT)

    assert len(calls) == 1
    command, kwargs = calls[0]
    assert command[0] == "fake-player"
    assert command[-1].endswith("click.mp3")
    assert kwargs["stdout"] is subprocess.DEVNULL
    assert kwargs["stderr"] is subprocess.DEVNULL


def test_audio_player_skips_repeated_playback_while_running() -> None:
    """A sound is not restarted while the previous playback is still running."""
    calls: list[tuple[list[str], dict[str, object]]] = []
    player = AudioPlayer(
        enabled=True,
        command=("fake-player",),
        runner=make_runner(calls, FakeProcess(running=True)),
    )

    player.play(SoundEffect.PADDLE_HIT)
    player.play(SoundEffect.PADDLE_HIT)

    assert len(calls) == 1


def test_audio_player_is_disabled_by_environment(monkeypatch) -> None:
    """The environment can disable playback without breaking the caller."""
    monkeypatch.setenv("ASCIICADE_SOUND", "off")
    calls: list[tuple[list[str], dict[str, object]]] = []
    player = AudioPlayer(command=("fake-player",), runner=make_runner(calls))

    assert player.enabled is False
    player.play(SoundEffect.PADDLE_HIT)
    assert calls == []


def test_audio_player_without_command_is_silent() -> None:
    """No supported system player means calls are ignored."""
    calls: list[tuple[list[str], dict[str, object]]] = []
    player = AudioPlayer(enabled=True, command=(), runner=make_runner(calls))

    player.play(SoundEffect.PADDLE_HIT)

    assert calls == []


def test_snake_food_play_sound(tmp_path: Path) -> None:
    """Snake plays the collect effect when its score increases."""
    audio = RecordingAudio()
    screen = SnakeGameScreen(
        make_context(tmp_path, audio),
        make_registration(SnakeGame),
        GameMode.SINGLE_PLAYER,
        (GuestPlayer(1),),
    )
    screen._game = SnakeGame()
    screen._game.start(GameMode.SINGLE_PLAYER, (GuestPlayer(1),))
    screen._game._snakes[0].score = 1
    screen._last_score = 0

    screen._play_food_sound()

    assert audio.played == [SoundEffect.FOOD_EATEN]


def test_blockfall_line_clear_play_sound(tmp_path: Path) -> None:
    """Blockfall plays the line-clear effect when one row is completed."""
    audio = RecordingAudio()
    screen = BlockfallGameScreen(
        make_context(tmp_path, audio),
        make_registration(BlockfallGame),
        GameMode.SINGLE_PLAYER,
        (GuestPlayer(1),),
    )
    screen._game = BlockfallGame()
    screen._game.start(GameMode.SINGLE_PLAYER, (GuestPlayer(1),))
    screen._game._states[0].lines = 2
    screen._last_lines = 1

    screen._play_line_clear_sound()

    assert audio.played == [SoundEffect.LINE_CLEAR]


def test_blockfall_multi_line_clear_play_bonus(tmp_path: Path) -> None:
    """Blockfall plays the bonus effect when multiple rows are completed."""
    audio = RecordingAudio()
    screen = BlockfallGameScreen(
        make_context(tmp_path, audio),
        make_registration(BlockfallGame),
        GameMode.SINGLE_PLAYER,
        (GuestPlayer(1),),
    )
    screen._game = BlockfallGame()
    screen._game.start(GameMode.SINGLE_PLAYER, (GuestPlayer(1),))
    screen._game._states[0].lines = 4
    screen._last_lines = 1

    screen._play_line_clear_sound()

    assert audio.played == [SoundEffect.MULTI_LINE_CLEAR]


def test_pong_paddle_hit_play_sound(tmp_path: Path) -> None:
    """Pong plays the paddle effect when the ball reverses near a paddle."""
    audio = RecordingAudio()
    screen = PongGameScreen(
        make_context(tmp_path, audio),
        make_registration(PongGame),
        GameMode.SINGLE_PLAYER,
        (GuestPlayer(1),),
    )
    screen._game = PongGame()
    screen._game.start(GameMode.SINGLE_PLAYER, (GuestPlayer(1),))
    screen._game._serve_countdown = 0
    screen._game._ball.x = 3.0
    screen._last_ball_x = 5.0
    screen._ball_moving_right = True

    screen._play_paddle_hit_sound()

    assert audio.played == [SoundEffect.PADDLE_HIT]


def test_pong_point_play_sound(tmp_path: Path) -> None:
    """Pong plays the point effect when a player scores."""
    audio = RecordingAudio()
    screen = PongGameScreen(
        make_context(tmp_path, audio),
        make_registration(PongGame),
        GameMode.SINGLE_PLAYER,
        (GuestPlayer(1),),
    )
    screen._game = PongGame()
    screen._game.start(GameMode.SINGLE_PLAYER, (GuestPlayer(1),))
    screen._game._scores[0] = 1
    screen._last_scores = (0, 0)

    screen._play_score_sound()

    assert audio.played == [SoundEffect.POINT_SCORED]


def test_game_over_screen_plays_sound(tmp_path: Path) -> None:
    """The game-over screen plays the game-over effect when mounted."""

    async def scenario() -> None:
        audio = RecordingAudio()
        database = Database(tmp_path / "game-over.db")
        database.initialize()
        app = AsciicadeApp(
            database=database,
            players=PlayerRepository(database),
            results=ResultRepository(database),
            settings=SettingsRepository(database),
            audio=audio,
        )
        result = make_game_result(
            "snake",
            GameMode.SINGLE_PLAYER,
            (make_player_result(GuestPlayer(1), 1, MatchOutcome.LOSS),),
        )
        async with app.run_test(size=(100, 30)) as pilot:
            app.push_screen(
                GameOverScreen(
                    app.context,
                    make_registration(SnakeGame),
                    GameMode.SINGLE_PLAYER,
                    (GuestPlayer(1),),
                    result,
                )
            )
            await pilot.pause()
            assert audio.played == [SoundEffect.GAME_OVER]

    asyncio.run(scenario())
