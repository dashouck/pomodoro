import math
import random
import struct
import subprocess
import sys
import tempfile
import wave
from pathlib import Path

from textual.app import App, ComposeResult
from textual.containers import Center, Vertical
from textual.reactive import reactive
from textual.screen import ModalScreen
from textual.timer import Timer
from textual.widgets import Button, Footer, Header, Label, OptionList
from textual.widgets.option_list import Option


WORK_SECONDS = 25 * 60
SHORT_BREAK_SECONDS = 5 * 60
LONG_BREAK_SECONDS = 15 * 60
SESSIONS_BEFORE_LONG_BREAK = 4

TICK_SOUNDS = [
    "Mechanical Clock",
    "Soft Click",
    "Woodblock",
    "Metronome",
    "Drip",
    "Typewriter",
    "Pulse",
    "Chirp",
    "Snap",
    "Sonar",
]


def _generate_sound(name: str, path: Path) -> None:
    """Generate a tick sound WAV file based on the preset name."""
    sample_rate = 44100
    random.seed(42)

    if name == "Mechanical Clock":
        duration = 0.035
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            envelope = math.exp(-t * 300)
            low = math.sin(2 * math.pi * 120 * t)
            mid = math.sin(2 * math.pi * 800 * t)
            noise = random.uniform(-1, 1)
            attack = math.exp(-t * 600)
            sample = envelope * (0.35 * low + 0.30 * mid + 0.35 * noise * attack)
            samples.append(int(12000 * max(-1.0, min(1.0, sample))))

    elif name == "Soft Click":
        duration = 0.015
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            envelope = math.exp(-t * 800)
            tone = math.sin(2 * math.pi * 3000 * t)
            sample = envelope * tone
            samples.append(int(8000 * max(-1.0, min(1.0, sample))))

    elif name == "Woodblock":
        duration = 0.04
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            envelope = math.exp(-t * 200)
            tone = math.sin(2 * math.pi * 600 * t) + 0.5 * math.sin(2 * math.pi * 1200 * t)
            sample = envelope * tone
            samples.append(int(10000 * max(-1.0, min(1.0, sample))))

    elif name == "Metronome":
        duration = 0.025
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            envelope = math.exp(-t * 400)
            tone = math.sin(2 * math.pi * 1000 * t)
            sample = envelope * tone
            samples.append(int(14000 * max(-1.0, min(1.0, sample))))

    elif name == "Drip":
        duration = 0.06
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            envelope = math.exp(-t * 150)
            freq = 1200 - 800 * (t / duration)
            tone = math.sin(2 * math.pi * freq * t)
            sample = envelope * tone
            samples.append(int(10000 * max(-1.0, min(1.0, sample))))

    elif name == "Typewriter":
        duration = 0.012
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            envelope = math.exp(-t * 1000)
            noise = random.uniform(-1, 1)
            tone = math.sin(2 * math.pi * 4000 * t)
            sample = envelope * (0.6 * noise + 0.4 * tone)
            samples.append(int(14000 * max(-1.0, min(1.0, sample))))

    elif name == "Pulse":
        duration = 0.05
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            envelope = math.exp(-t * 180)
            tone = math.sin(2 * math.pi * 60 * t) + 0.5 * math.sin(2 * math.pi * 120 * t)
            sample = envelope * tone
            samples.append(int(16000 * max(-1.0, min(1.0, sample))))

    elif name == "Chirp":
        duration = 0.04
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            envelope = math.exp(-t * 250)
            freq = 800 + 2000 * (t / duration)
            tone = math.sin(2 * math.pi * freq * t)
            sample = envelope * tone
            samples.append(int(10000 * max(-1.0, min(1.0, sample))))

    elif name == "Snap":
        duration = 0.008
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            envelope = math.exp(-t * 1500)
            noise = random.uniform(-1, 1)
            sample = envelope * noise
            samples.append(int(16000 * max(-1.0, min(1.0, sample))))

    elif name == "Sonar":
        duration = 0.15
        n_samples = int(sample_rate * duration)
        samples = []
        for i in range(n_samples):
            t = i / sample_rate
            envelope = math.exp(-t * 30)
            tone = math.sin(2 * math.pi * 1500 * t)
            sample = envelope * tone
            samples.append(int(8000 * max(-1.0, min(1.0, sample))))

    else:
        return

    raw = b"".join(struct.pack("<h", s) for s in samples)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw)


def _generate_bell_sound(path: Path) -> None:
    """Generate a bell/chime WAV file to play when a phase ends."""
    sample_rate = 44100
    duration = 1.0
    n_samples = int(sample_rate * duration)
    samples = []
    for i in range(n_samples):
        t = i / sample_rate
        envelope = math.exp(-t * 3)
        tone = (
            0.5 * math.sin(2 * math.pi * 880 * t)
            + 0.3 * math.sin(2 * math.pi * 1760 * t)
            + 0.2 * math.sin(2 * math.pi * 2640 * t)
        )
        sample = envelope * tone
        samples.append(int(16000 * max(-1.0, min(1.0, sample))))
    raw = b"".join(struct.pack("<h", s) for s in samples)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(raw)


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


class SoundPickerScreen(ModalScreen[str]):
    BINDINGS = [("escape", "dismiss_picker", "Close")]

    def compose(self) -> ComposeResult:
        yield OptionList(
            *[Option(name, id=name) for name in TICK_SOUNDS],
            id="sound-list",
        )

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        self.dismiss(event.option.prompt)

    def action_dismiss_picker(self) -> None:
        self.dismiss("")


class PomodoroApp(App):
    TITLE = "PomodorO"
    CSS_PATH = "styles.tcss"
    BINDINGS = [
        ("space", "toggle_timer", "Start/Pause"),
        ("r", "reset_timer", "Reset"),
        ("s", "skip", "Skip"),
        ("t", "pick_sound", "Tick Sound"),
        ("q", "quit", "Quit"),
    ]

    time_left: reactive[int] = reactive(WORK_SECONDS, init=False)
    is_running: reactive[bool] = reactive(False, init=False)
    session_count: reactive[int] = reactive(0, init=False)
    phase: reactive[str] = reactive("work", init=False)
    tick_sound: reactive[str] = reactive("Metronome", init=False)

    def __init__(self) -> None:
        super().__init__()
        self._tick_dir = Path(tempfile.mkdtemp())
        self._sound_paths: dict[str, Path] = {}
        for name in TICK_SOUNDS:
            p = self._tick_dir / f"{name}.wav"
            _generate_sound(name, p)
            self._sound_paths[name] = p
        self._tick_path = self._sound_paths["Metronome"]
        self._bell_path = self._tick_dir / "bell.wav"
        _generate_bell_sound(self._bell_path)

    def compose(self) -> ComposeResult:
        yield Header()
        with Vertical(id="main"):
            yield Label("WORK", id="phase-label")
            with Center():
                yield Label(self._format_time(self.time_left), id="timer")
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
        self.query_one("#timer", Label).update(self._format_time(value))
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

    def watch_tick_sound(self, value: str) -> None:
        if value in self._sound_paths:
            self._tick_path = self._sound_paths[value]

    def _on_sound_picked(self, name: str) -> None:
        if name:
            self.tick_sound = name

    def action_pick_sound(self) -> None:
        self.push_screen(SoundPickerScreen(), callback=self._on_sound_picked)

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
        _play_tick(self._bell_path)

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
