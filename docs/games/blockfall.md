# Blockfall

Classic falling-block puzzle for one or two local players. Arrange tetrominoes
into complete horizontal lines, clear them before the stack reaches the top and
survive as the pieces fall faster.

## Single player

- Move the active piece with the arrow keys or WASD.
- Rotate clockwise with Space (or Shift) and counterclockwise with AltGr (or
  Ctrl).
- Press Down or S to move down one row. Hold the key to soft drop continuously.
- Complete a horizontal line to clear it. Clearing several lines at once awards
  more points.
- The level rises every 10 cleared lines and gravity becomes faster.
- The game ends when a newly generated piece cannot enter the board.
- Your score is stored in the single-player leaderboard.

## Two players

- Player 1 uses the arrow keys, Space (clockwise) and AltGr (counterclockwise).
- Player 2 uses A and D to move, S to soft drop, Ctrl (clockwise) and Shift
  (counterclockwise). Player 2 plays on the left board.
- Both players play at the same time on separate 10x20 boards.
- The first player to top out loses and the other player wins. If both players
  top out on the same tick, the match is a draw.
- Each player has an independent score, line count, level and next-piece queue.

## Options

- **Start level:** 1, 3, 5, 8 or 10. A higher start level increases the initial
  fall speed and the score multiplier.
- **Next piece:** On (default) or Off. Shows the next tetromino in the information
  panel.
- **Ghost piece:** On (default) or Off. Shows a dim outline where the active
  piece will land.

## Rotation and wall kicks

Rotation uses wall kicks: if a rotation would collide with a wall or a locked
block, Blockfall tries a series of small horizontal and upward offsets and uses
the first one that fits. This keeps rotation predictable near walls, the floor
and uneven stacks.

A short lock delay follows a failed downward move. During the lock delay the
piece can still be moved or rotated; a successful adjustment restarts the delay.
Pressing Down while the piece is resting locks it immediately.

## Scoring and levels

| Lines cleared | Base score |
|---|---|
| 1 | 100 |
| 2 | 300 |
| 3 | 500 |
| 4 | 800 |

The base score is multiplied by the current level. Soft drop awards one point per
cell. The level rises every 10 cleared lines; the score for a clear uses the
level before the level-up.

Pieces are drawn from a seven-bag randomizer, so every group of seven pieces
contains each tetromino exactly once. The next-piece queue is deterministic for a
given random seed.

## Controls

Player 1 uses the arrow keys by default. Player 2 uses W/A/S/D. In single-player
mode, WASD is accepted as an alternative to the arrow keys.

Escape or P pauses or resumes during a game. The full, game-independent control
list is on the [controls page](../index.md#controls).

## Rendering

- Each logical cell is rendered as two horizontal block characters (`██`), so the
  playfield stays visually square in terminals where characters are about twice as
  tall as they are wide.
- Locked and active blocks use distinct colors for each tetromino: I is cyan,
  O is yellow, T is magenta, S is green, Z is red, J is blue and L is white.
- The active piece is bold, the ghost piece is a dim outline and completed rows
  flash white briefly before they disappear.
- The 10x20 board is surrounded by a visible one-character border. The information
  panel shows the player name, score, cleared lines, level and next piece.
- In two-player mode, Player 2's board and information panel are on the left and
  Player 1's are on the right.