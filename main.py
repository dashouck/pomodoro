import io
import math
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Center, Vertical
from textual.reactive import reactive
from textual.timer import Timer
from textual.widgets import Button, Digits, Footer, Header, Label


WORK_SECONDS = 25 * 60
SHORT_BREAK_SECONDS = 5 * 60
LONG_BREAK_SECONDS = 15 * 60
SESSIONS_BEFORE_LONG_BREAK = 4


def _generate_tick_wav(path: Path) -> None:
    """Generate a mechanical clock tick sound and write it to a WAV file."""
    import random

    sample_rate = 44100
    duration = 0.035  # 35ms — short, sharp
    n_samples = int(sample_rate * duration)
    random.seed(42)  # deterministic

    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        # Sharp exponential decay — the "click" envelope
        envelope = math.exp(-t * 300)
        # Mix a low thud with a bright tap for that wooden clock feel
        low = math.sin(2 * math.pi * 120 * t)   # body
        mid = math.sin(2 * math.pi * 800 * t)   # resonance
        noise = random.uniform(-1, 1)             # transient texture
        # Weight toward noise at attack, tone sustains briefly
        attack = math.exp(-t * 600)
        sample = envelope * (
            0.35 * low + 0.30 * mid + 0.35 * noise * attack
        )
        value = int(12000 * max(-1.0, min(1.0, sample)))
        samples.append(struct.pack("<h", value))

    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(b"".join(samples))


def _play_tick(path: Path) -> None:
    """Play the tick WAV file asynchronously using a platform command."""
    if sys.platform == "darwin":
        subprocess.Popen(
            ["afplay", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    else:
        subprocess.Popen(
            ["aplay", "-q", str(path)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )


class PomodoroApp(App):
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("space", "toggle_timer", "Start/Pause"),
        ("r", "reset_timer", "Reset"),
        ("s", "skip", "Skip"),
        ("q", "quit", "Quit"),
    ]

    time_left: reactive[int] = reactive(WORK_SECONDS, init=False)
    is_running: reactive[bool] = reactive(False, init=False)
    session_count: reactive[int] = reactive(0, init=False)
    phase: reactive[str] = reactive("work", init=False)

    def __init__(self) -> None:
        super().__init__()
        self._tick_dir = tempfile.mkdtemp()
        self._tick_path = Path(self._tick_dir) / "tick.wav"
        _generate_tick_wav(self._tick_path)

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main"):
            yield Label("WORK", id="phase-label")
            with Center():
                yield Digits(self._format_time(self.time_left), id="timer")
            with Center(id="button-bar"):
                yield Button("Start", id="toggle-btn")
                yield Button("Reset", id="reset-btn")
                yield Button("Skip", id="skip-btn")
            yield Label(self._session_text(), id="session-label")
        yield Footer()

    def _format_time(self, seconds: int) -> str:
        m, s = divmod(seconds, 60)
        return f"{m:02d}:{s:02d}"

    def _session_text(self) -> str:
        return f"Session {self.session_count + 1} of {SESSIONS_BEFORE_LONG_BREAK}"

    # --- Reactive watchers ---------------------------------------------------

    def watch_time_left(self, value: int) -> None:
        self.query_one("#timer", Digits).update(self._format_time(value))
        if value <= 0:
            self._advance_phase()

    def watch_is_running(self, value: bool) -> None:
        btn = self.query_one("#toggle-btn", Button)
        btn.label = "Pause" if value else "Start"

    def watch_phase(self, value: str) -> None:
        label = self.query_one("#phase-label", Label)
        names = {"work": "WORK", "short_break": "SHORT BREAK", "long_break": "LONG BREAK"}
        label.update(names.get(value, value.upper()))

    def watch_session_count(self) -> None:
        self.query_one("#session-label", Label).update(self._session_text())

    # --- Timer mechanics ------------------------------------------------------

    _tick_timer: Timer | None = None

    def _start_tick(self) -> None:
        if self._tick_timer is None:
            self._tick_timer = self.set_interval(1, self._tick)

    def _stop_tick(self) -> None:
        if self._tick_timer is not None:
            self._tick_timer.stop()
            self._tick_timer = None

    def _tick(self) -> None:
        if self.time_left > 0:
            self.time_left -= 1
            _play_tick(self._tick_path)

    def _advance_phase(self) -> None:
        self.is_running = False
        self._stop_tick()
        self.bell()

        if self.phase == "work":
            self.session_count += 1
            if self.session_count % SESSIONS_BEFORE_LONG_BREAK == 0:
                self.phase = "long_break"
                self.time_left = LONG_BREAK_SECONDS
            else:
                self.phase = "short_break"
                self.time_left = SHORT_BREAK_SECONDS
        else:
            self.phase = "work"
            self.time_left = WORK_SECONDS

    # --- Actions / button handlers --------------------------------------------

    def action_toggle_timer(self) -> None:
        self.is_running = not self.is_running
        if self.is_running:
            self._start_tick()
        else:
            self._stop_tick()

    def action_reset_timer(self) -> None:
        self.is_running = False
        self._stop_tick()
        durations = {
            "work": WORK_SECONDS,
            "short_break": SHORT_BREAK_SECONDS,
            "long_break": LONG_BREAK_SECONDS,
        }
        self.time_left = durations[self.phase]

    def action_skip(self) -> None:
        self.is_running = False
        self._stop_tick()
        self._advance_phase()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        actions = {
            "toggle-btn": self.action_toggle_timer,
            "reset-btn": self.action_reset_timer,
            "skip-btn": self.action_skip,
        }
        action = actions.get(event.button.id or "")
        if action:
            action()


if __name__ == "__main__":
    PomodoroApp().run()
