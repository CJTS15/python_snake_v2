# 🐍 Python Snake V2

A modern, cartoonish twist on the classic Snake game built with Python and Pygame. This isn't your Nokia 3310 snake—it features smooth interpolated movement, wavy body animations, progressive difficulty, and a chaotic bomb mechanic!

## 🎮 Features

*   **Smooth Movement:** Uses Linear Interpolation (Lerp) for buttery smooth 60 FPS visuals, independent of the grid-based logic.
*   **Wavy Animation:** The snake's body moves in a procedural sine-wave pattern.
*   **Progressive Difficulty:**
    *   The snake gets faster with every apple eaten.
    *   **Bomb Stacking:** Every 10 apples, 2 permanent bombs are added to the arena. By 50 apples, the screen is a minefield!
*   **Risk & Reward:**
    *   **Cookies:** Rare bonus items appear periodically for high points.
    *   **Bombs:** Hitting a bomb doesn't kill you instantly—it blows off your tail (shrink mechanic), reducing your length but keeping you alive.
*   **Full UI:** Start Menu, Pause Menu (Press ESC), Instructions, and Game Over screens.

## 🛠️ Prerequisites

You need Python installed on your machine. This game relies on the **Pygame** library.

```bash
pip install pygame
```

# 📂 Project Structure & Assets

For the game to look its best, you need image assets in the same folder as the script. The game will automatically look for these files. If they are missing, it will fallback to drawing colored circles.

## Required Files:

*    snake_game.py (The main game script)
*    head.png (The snake's face)
*    body.png (A round green/cyan circle)
*    apple.png (A red apple)
*    cookie.png (A cookie sprite)
*    bomb.png (A bomb/mine sprite)

# 🚀 How to Run

1. Open your terminal or command prompt.
2.    Navigate to the project folder.
3.    Run the script:

```bash
python snake_game.py
```

# 📝 Configuration

You can tweak the game settings at the top of the snake_game.py file:

```
SCREEN_WIDTH = 810       # Must be divisible by GRID_SIZE (30)
START_MOVE_DELAY = 150   # Higher = Slower start speed
APPLES_FOR_EVENT = 10    # How often bombs/cookies spawn
```