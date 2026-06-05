# TETR.IO Autonomous Heuristic Bot

An ultra-fast, computer-vision-driven Tetris AI built specifically to survive and compete in modern Guideline Tetris games (TETR.IO). The system uses a Genetic Algorithm trained in a headless cloud environment, combined with a local high-speed screen-scraping bridge for real-time actuation.

## 🧠 System Architecture

This project is split into two distinct phases: **Cloud Training** and **Local Execution**.

### 1. The Brain (Heuristics)
Instead of relying on deep neural networks (which struggle with delayed rewards in Tetris), this bot evaluates board states using pure matrix mathematics. Before dropping a piece, it simulates every possible column and rotation, and scores the resulting board using four metrics:

* **Lines Cleared (Reward):** Maximizes completed rows.
* **Aggregate Height (Penalty):** Keeps the overall stack as low to the ground as possible.
* **Holes (Massive Penalty):** Heavily penalizes placing blocks over empty space.
* **Bumpiness (Penalty):** Prefers flat surfaces by measuring the absolute height difference between adjacent columns.

### 2. Cloud Training (Google Colab)
The bot's weights were optimized using a Genetic Algorithm running a custom, headless TETR.IO physics engine.
* **Population:** 100 bots per generation.
* **Evolution:** Bots play until they die (or hit a 5,000 line cap). The best performers are selected, crossed over, and mutated.
* **Convergence:** The bot achieved "immortality" (hitting the 5000 line cap) in just 4 generations after discovering a massive mathematical penalty for creating Holes (`-0.869`).

### 3. Local Execution (The Vision Bridge)
Because we do not have access to the TETR.IO source code, the bot relies on a 4-step execution loop running 30+ times a second:
1.  **High-Speed Screen Capture:** Uses `mss` to grab the specific bounding box of the game board.
2.  **Grid Parsing:** Uses OpenCV (`cv2`) to convert the visual pixels into a 20x10 binary NumPy array (0 for empty, 1 for block).
3.  **Simulation & Scoring:** Identifies the spawned piece, calculates all possible futures, and picks the highest-scoring state.
4.  **Hardware Actuation:** Uses `pydirectinput` to send low-level DirectX scan codes, bypassing browser anti-cheat mechanisms.

---

## 🛠️ Key Engineering Solutions

Migrating from a headless simulation to a live web browser introduced physics and timing desyncs. The following custom solutions are implemented in `run_bot.py`:

* **Rotational Drift Correction (The Offset Map):** In TETR.IO, pieces pivot around a center point when rotated (e.g., an 'I' piece shifts from column 3 to 5). The bot features a `NATURAL_SPAWN_COL` lookup table to perfectly calculate the geometric offset of every piece post-rotation, eliminating drift.
* **Keystroke Throttling:** Web browser engines drop inputs if they are received faster than the frame render rate. The bot uses a precise `0.03s` delay between hardware presses to guarantee every translation and rotation registers.
* **The 'O' Piece Offset:** Accounts for the Guideline rule where the square 'O' piece spawns exactly centered (column 4) rather than left-aligned (column 3).
* **Simulation Masking:** The engine automatically erases the top 4 rows during internal simulation so the falling piece doesn't mathematically collide with its own starting coordinates.

---

## 🚀 Setup & Installation

### Prerequisites
You will need Python installed along with the following libraries:
```bash
pip install mss numpy opencv-python pydirectinput


File Structure
calibrate.py (Optional): A utility script to find the precise screen coordinates of your browser window.

best_bot.npy (Optional): The optimized genetic weights saved from the Colab training loop.

run_bot.py: The main execution script.

🎮 Usage
Open TETR.IO in your web browser.

Ensure your BBOX_COORDINATES in run_bot.py are perfectly calibrated to your current screen layout.

Run the bot:

Bash
python run_bot.py
Click into the TETR.IO window within 3 seconds to give the browser focus.

Watch it play.