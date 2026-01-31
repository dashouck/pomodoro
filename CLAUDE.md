# Project: Terminal Pomodoro Timer
A terminal-based Pomodoro timer built with Python and Textual.

## Environment & Setup
- **Virtual Env:** Uses a local venv located at `./venv`.
- **Activation:** Ensure venv is active (`source venv/bin/activate`) before running commands.
- **Ignored Paths:** Do not read, search, or index files inside `venv/` or `__pycache__/`.

## Build & Run Commands
- **Run App:** `python main.py`
- **Dev Mode:** `textual run main.py --dev` (Enables live CSS reloading)
- **Install Deps:** `pip install -r requirements.txt`
- **Type Check:** `mypy .`
- **Lint/Format:** `ruff check .` or `black .`
- **Test:** `pytest`

## Tech Stack
- **Language:** Python 3.10+
- **UI Framework:** Textual (TUI)
- **Audio:** `playsound` (or similar cross-platform lib) for ticking/alarm sounds.
- **Async:** Uses Python `asyncio`.

## Architecture & Coding Guidelines
1. **App Structure:** - Entry point: `App` class in `main.py`.
   - Complex widgets: Move to separate files (e.g., `timer_widget.py`) if they exceed ~100 lines.
   
2. **State Management:**
   - Use Textual's `reactive` attributes for any data that changes the UI (e.g., `time_left`, `is_running`).
   - Do not use global variables for state.

3. **Styling:**
   - strictly use external `.tcss` files. Avoid inline styles in Python code.
   - Use CSS variables for theme colors (e.g., `$primary`,
