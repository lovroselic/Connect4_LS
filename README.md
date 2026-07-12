# Connect4_LS

![Connect4_LS title artwork](assets/images/connect4_title.png)

A standalone desktop implementation of standard **6 × 7 Connect Four**, built with Python and Pygame.

Connect4_LS supports Human vs Human, Human vs AI, and AI vs AI matches — because seven columns are apparently enough room for strategy, machine learning, and public humiliation.

## The project

The project began as a fast bitboard Lookahead script for a Kaggle competition, then escaped into JavaScript as a web game. Reinforcement learning followed, because a functioning search engine clearly was not enough trouble.

- [Original Kaggle notebook](https://www.kaggle.com/code/lovroselic/connect-4-ls-fast-la-bitboard-op-book-par)
- [Play the web version](https://www.laughingskull.org/Games/Connect4/Connect4.php)
- [Connect4_LS on GitHub](https://github.com/lovroselic/Connect4_LS)

The DQN agent remained firmly at village-idiot level. AlphaZero showed promise, provided one was willing to wait roughly another three centuries. PPO eventually produced `PPO_2004`, which can hold its own against deeper Lookahead agents and occasionally behaves as though this was planned.

From first bitboard to this desktop version, the whole expedition took about a year — a perfectly reasonable amount of time to drop coloured discs into seven columns.

## Features

- Standard 6 × 7 Connect Four board
- Human vs Human
- Human vs AI
- AI vs AI
- Depth-selectable Lookahead agents
- PPO neural-network player
- LA13 move hints for human players
- Move evaluation and analysis display
- AI-vs-AI pause, resume, and single-step controls
- Falling-disc animation
- Session scoreboard
- Random and alternating starting-player modes
- Configurable window size, fullscreen mode, FPS, animation speed, AI delay, sound, and volume
- Optional development and benchmark test menu

## Players

### Human

A local player armed with a mouse, keyboard, intuition, and the traditional ability to blame the interface.

### Lookahead

A depth-limited search engine accelerated with [Numba](https://numba.pydata.org).

Higher depths search farther ahead, consume more time, and become increasingly smug about obvious moves.

### PPO

A neural-network player trained with Proximal Policy Optimization and executed with [PyTorch](https://pytorch.org).

It chooses moves from learned board patterns rather than explicitly searching every possible future.

## Human controls

| Control | Action |
|---|---|
| Mouse | Select and play a column |
| `1`–`7` | Play that column immediately |
| `A` / `D` | Move selection left or right |
| `Left` / `Right` | Move selection left or right |
| `Enter` / `Space` | Play the selected column |
| `R` | Restart the current match, optimism fully restored |
| `Esc` | Return to the previous screen |

## AI-vs-AI controls

| Control | Action |
|---|---|
| `P` | Pause or resume the match |
| `N` / `.` | Play one AI move while paused |

## LA13 hint

During a human turn, the **Hint (LA13)** button asks the depth-13 Lookahead engine for a recommendation.

The suggested column and evaluation score are displayed without automatically playing the move, preserving your right to ignore excellent advice.


## Running the project

From the project root:

```bash
python main.py
```

The project currently targets Python 3.11 and Pygame 2.6.1.

Additional dependencies may include:

- NumPy
- Numba
- PyTorch

## Credits

- Design, programming, PPO training, and most questionable decisions: **Lovro Selič**, a.k.a. [LaughingSkull](https://www.laughingskull.org)
- Game framework: [Pygame](https://www.pygame.org)
- Lookahead acceleration: [Numba](https://numba.pydata.org)
- Neural-network inference: [PyTorch](https://pytorch.org)

Yep, that is it. The discs still fall downward, which remains the project's most thoroughly tested physical law.
