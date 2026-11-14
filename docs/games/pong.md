# Pong

Classic arcade Pong for one or two local players. Return the ball with your
paddle, use the paddle edges to aim, and be first to reach the score limit.

## Single player

- You control the left paddle with the arrow keys or WASD.
- The computer controls the right paddle.
- Move your paddle to return the ball. Hitting nearer the paddle edge produces a
  steeper return angle.
- The computer tracks the ball with a capped speed, so it is challenging but
  beatable.
- The first player to the score limit wins.

## Two players

- Player 1 uses the arrow keys.
- Player 2 uses W and S.
- Both players share the same keyboard and playfield.
- The same paddle and ball physics apply.
- The first player to the score limit wins.

## Options

- **Score limit:** 5, 7, 11 (default) or 15.
- **Difficulty:** Easy, Normal (default) or Hard. Difficulty changes the ball
  speed and, in single-player mode, the computer paddle speed.

## Controls

| Action | Key |
|---|---|
| Player 1 paddle up / down | Arrow Up / Arrow Down |
| Player 2 paddle up / down | W / S |
| Pause / resume | Escape or P |
| Leave game while paused | Enter |
| Quit application | Q, then confirm |
| Game-over back | Escape |

In single-player mode the human can use either the arrow keys or WASD. In
two-player mode the arrow keys belong to Player 1 and W/S to Player 2.

Tap a direction key to move the paddle one half-block. Hold it longer than 0.1
seconds to move continuously; releasing the key stops movement immediately.
Hold-to-move uses Kitty keyboard release events when the terminal supports them.
Terminals without release reporting use a short fallback timeout before the
paddle stops.

## Physics and rendering

- The ball reflects based on where it hits the paddle. A center hit produces a
  shallow return; an edge hit produces a steeper angle.
- The ball keeps a consistent speed and gains a small, capped speed increase
  during long rallies.
- The ball bounces off the top and bottom walls. A point is scored when it
  passes a paddle.
- After each point the ball resets to the center and a short serve delay gives
  both players time to reposition.
- Paddles are one terminal column wide and use half-block characters
  (`▀`, `▄`, `█`) for precise vertical movement.
- The center line, border, paddles and ball use the retro/neon terminal colors.
  Player profiles use their selected color; the computer uses red.
