# Snake

Classic arcade Snake for one or two local players. Eat food, grow longer and avoid crashing into walls or your own body.

## Single player

- The snake moves continuously on the grid.
- Each food item increases your score and length.
- Hitting a wall or your own body ends the game.
- Your score is stored in the single-player leaderboard.

## Two players

- Both players start at the same time on a shared arena.
- By default each player has their own food in their own color. A snake can only
  eat its own food.
- Turning off "Food per player" restores the classic shared food that either
  snake can eat. The shared ball is white.
- Hitting a wall, yourself or the other snake eliminates you.
- The surviving snake wins.
- If both snakes are eliminated on the same tick, the match is a draw.

## Options

- Difficulty: Easy, Medium (default), Hard. Changes the game speed.
- Wrap walls: Off (default), On. When on, the snake reappears on the opposite
  side of the arena when it leaves the play area. Hitting a wall no longer
  crashes the snake, but hitting your own or the other snake's body still ends
  the game.
- Food per player: On (default), Off. On gives each player in two-player mode
  their own food in their player color. Off uses one neutral shared food, as in
  the original game. This option has no effect in single-player mode.

Player 1 uses the arrow keys by default. Player 2 uses W/A/S/D. In single-player
mode, WASD is accepted as an alternative to the arrow keys. Direction changes are
buffered and applied on the next game tick. Immediate 180-degree reversals are
rejected.

Escape or P pauses or resumes during a game. The full, game-independent control
list is on the [controls page](../index.md#controls).

Snake rendering uses solid block characters: the wall, every snake segment and
side walls that are one arena cell wide. Food is drawn as a ball made of the
left and right halves of a filled circle (`◖◗`). Player-owned food uses the
player color, while shared food is white. The head is emphasized in bold rather
than with a number marker. Player 1 is shown in green and player 2 in cyan by
default; player profiles can choose from the eight normal terminal colors. Each logical arena cell is rendered as two horizontal
characters, so the playfield stays visually square in terminals where characters
are about twice as tall as they are wide.
