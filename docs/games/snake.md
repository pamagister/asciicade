# Snake

Classic arcade Snake for one or two local players. Eat food, grow longer and avoid crashing into walls or your own body.

## Single player

- The snake moves continuously on the grid.
- Each food item increases your score and length.
- Hitting a wall or your own body ends the game.
- Your score is stored in the single-player leaderboard.

## Two players

- Both players start at the same time on a shared arena.
- Both snakes compete for the same food.
- Hitting a wall, yourself or the other snake eliminates you.
- The surviving snake wins.
- If both snakes are eliminated on the same tick, the match is a draw.

Player 1 uses the arrow keys by default. Player 2 uses W/A/S/D. In single-player
mode, WASD is accepted as an alternative to the arrow keys. Direction changes are
buffered and applied on the next game tick. Immediate 180-degree reversals are
rejected.

Escape pauses or resumes during a game; Q leaves the current game or quits the
application. The full, game-independent control list is on the [landing page](../index.md#controls).

Snake rendering uses solid block characters: the wall, every snake segment and
side walls that are one arena cell wide. The head is emphasized in bold rather
than with a number marker. Player 1 is shown in green and player 2 in cyan by
default; player profiles can choose from 16 terminal colors (eight normal and
eight bright/neon variants). Each logical arena cell is rendered as two horizontal
characters, so the playfield stays visually square in terminals where characters
are about twice as tall as they are wide.

## Terminal preview

```text
SNAKE — SINGLE-PLAYER
Guest 1: 3

███████████████████████████████████████████████████
██                                              ██
██        ██████████                            ██
██        ██      ██                            ██
██        ██      ██                            ██
██        ██      ████████████  **              ██
██                                              ██
███████████████████████████████████████████████████
```
