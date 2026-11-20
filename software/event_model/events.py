"""Validated timestamped pulse-window data structures and CSV I/O."""

from __future__ import annotations

import csv
from dataclasses import dataclass
from numbers import Integral
from pathlib import Path
from typing import Iterable

import numpy as np


@dataclass(frozen=True)
class EventWindow:
    """One labeled or unlabeled interval of hardware-clock pulse timestamps.

    ``timestamps_ticks`` are offsets from the start of the window, not absolute
    FPGA counter values. Convert absolute hardware timestamps to offsets before
    constructing this object. Events must be strictly increasing and fall
    inside ``duration_ticks``.
    """

    sample_id: str
    tick_hz: int
    duration_ticks: int
    timestamps_ticks: tuple[int, ...]
    input_voltage_v: float | None = None
    source: str = "unknown"
    synthetic: bool = False

    def __post_init__(self) -> None:
        if not self.sample_id:
            raise ValueError("sample_id must not be empty")
        if isinstance(self.tick_hz, bool) or not isinstance(self.tick_hz, Integral) or self.tick_hz <= 0:
            raise ValueError("tick_hz must be a positive integer")
        if isinstance(self.duration_ticks, bool) or not isinstance(self.duration_ticks, Integral) or self.duration_ticks <= 0:
            raise ValueError("duration_ticks must be positive")
        ticks = tuple(self.timestamps_ticks)
        if any(isinstance(tick, bool) or not isinstance(tick, Integral) for tick in ticks):
            raise ValueError("event timestamps must be integer FPGA ticks")
        object.__setattr__(self, "tick_hz", int(self.tick_hz))
        object.__setattr__(self, "duration_ticks", int(self.duration_ticks))
        object.__setattr__(self, "timestamps_ticks", tuple(int(tick) for tick in ticks))
        if any(t < 0 or t >= self.duration_ticks for t in self.timestamps_ticks):
            raise ValueError("event timestamps must be within [0, duration_ticks)")
        if any(b <= a for a, b in zip(self.timestamps_ticks, self.timestamps_ticks[1:])):
            raise ValueError("event timestamps must be strictly increasing")
        if self.input_voltage_v is not None:
            if not np.isfinite(self.input_voltage_v) or not 0.0 <= self.input_voltage_v <= 1.0:
                raise ValueError("input_voltage_v must be in [0, 1]")

    @property
    def duration_s(self) -> float:
        return self.duration_ticks / self.tick_hz

    @property
    def event_rate_hz(self) -> float:
        return len(self.timestamps_ticks) / self.duration_s

    @property
    def timestamp_seconds(self) -> tuple[float, ...]:
        return tuple(t / self.tick_hz for t in self.timestamps_ticks)


def generate_periodic_window(
    sample_id: str,
    frequency_hz: float,
    duration_s: float,
    tick_hz: int,
    *,
    input_voltage_v: float | None = None,
    source: str = "synthetic-periodic",
    synthetic: bool = True,
) -> EventWindow:
    """Create a deterministic periodic event train for simulation/demo use.

    This is a pulse-stream generator, not an LM331 model. Its frequency is an
    explicit caller-provided value; it must not be treated as hardware
    calibration.
    """
    if frequency_hz <= 0:
        raise ValueError("frequency_hz must be positive")
    if duration_s <= 0:
        raise ValueError("duration_s must be positive")
    if tick_hz <= 0:
        raise ValueError("tick_hz must be positive")
    if frequency_hz >= tick_hz:
        raise ValueError("frequency_hz must be below tick_hz")

    duration_ticks = round(duration_s * tick_hz)
    period_ticks = tick_hz / frequency_hz
    times: list[int] = []
    n = 1
    while True:
        tick = round(n * period_ticks)
        if tick >= duration_ticks:
            break
        if times and tick <= times[-1]:
            raise ValueError("frequency exceeds timestamp tick resolution")
        times.append(tick)
        n += 1

    return EventWindow(
        sample_id=sample_id,
        tick_hz=tick_hz,
        duration_ticks=duration_ticks,
        timestamps_ticks=tuple(times),
        input_voltage_v=input_voltage_v,
        source=source,
        synthetic=synthetic,
    )


def generate_poisson_window(
    sample_id: str,
    frequency_hz: float,
    duration_s: float,
    tick_hz: int,
    *,
    seed: int,
    input_voltage_v: float | None = None,
) -> EventWindow:
    """Generate a seeded Poisson pulse train for simulation and stress tests.

    This is a mathematical synthetic source only; it does not model LM331
    transfer behavior, pulse shape, jitter, or electrical output levels.
    """
    if not np.isfinite(frequency_hz) or frequency_hz <= 0:
        raise ValueError("frequency_hz must be finite and positive")
    if not np.isfinite(duration_s) or duration_s <= 0:
        raise ValueError("duration_s must be finite and positive")
    if tick_hz <= 0 or frequency_hz >= tick_hz:
        raise ValueError("tick_hz must be positive and exceed frequency_hz")
    n_ticks = round(duration_s * tick_hz)
    if n_ticks <= 0:
        raise ValueError("duration_s is shorter than one timestamp tick")

    rng = np.random.default_rng(seed)
    interarrival = rng.exponential(tick_hz / frequency_hz, size=max(16, int(frequency_hz * duration_s * 2 + 16)))
    event_ticks: list[int] = []
    elapsed = 0.0
    for gap in interarrival:
        elapsed += float(gap)
        tick = int(round(elapsed))
        if tick >= n_ticks:
            break
        if event_ticks and tick <= event_ticks[-1]:
            tick = event_ticks[-1] + 1
        event_ticks.append(tick)
    return EventWindow(
        sample_id=sample_id,
        tick_hz=tick_hz,
        duration_ticks=n_ticks,
        timestamps_ticks=tuple(event_ticks),
        input_voltage_v=input_voltage_v,
        source="synthetic-poisson",
        synthetic=True,
    )


def save_event_windows(
    windows: Iterable[EventWindow], events_csv: str | Path, windows_csv: str | Path
) -> None:
    """Save event timestamps and per-window metadata as two CSV files."""
    windows = list(windows)
    if len({w.sample_id for w in windows}) != len(windows):
        raise ValueError("sample_id values must be unique")
    events_path = Path(events_csv)
    metadata_path = Path(windows_csv)
    events_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_path.parent.mkdir(parents=True, exist_ok=True)

    with events_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["sample_id", "timestamp_ticks"])
        writer.writeheader()
        for window in windows:
            for tick in window.timestamps_ticks:
                writer.writerow({"sample_id": window.sample_id, "timestamp_ticks": tick})

    with metadata_path.open("w", newline="", encoding="utf-8") as f:
        fields = [
            "sample_id", "tick_hz", "duration_ticks", "input_voltage_v", "source", "synthetic"
        ]
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for window in windows:
            writer.writerow({
                "sample_id": window.sample_id,
                "tick_hz": window.tick_hz,
                "duration_ticks": window.duration_ticks,
                "input_voltage_v": "" if window.input_voltage_v is None else window.input_voltage_v,
                "source": window.source,
                "synthetic": int(window.synthetic),
            })


def load_event_windows(events_csv: str | Path, windows_csv: str | Path) -> list[EventWindow]:
    """Read the paired event/metadata CSV format written by ``save_event_windows``."""
    event_rows: dict[str, list[int]] = {}
    with Path(events_csv).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None or not {"sample_id", "timestamp_ticks"}.issubset(reader.fieldnames):
            raise ValueError("events CSV requires sample_id,timestamp_ticks columns")
        for row in reader:
            event_rows.setdefault(row["sample_id"], []).append(int(row["timestamp_ticks"]))

    windows: list[EventWindow] = []
    with Path(windows_csv).open(newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        required = {"sample_id", "tick_hz", "duration_ticks", "input_voltage_v", "source", "synthetic"}
        if reader.fieldnames is None or not required.issubset(reader.fieldnames):
            raise ValueError("window metadata CSV is missing required columns")
        for row in reader:
            sample_id = row["sample_id"]
            voltage = row["input_voltage_v"].strip()
            windows.append(EventWindow(
                sample_id=sample_id,
                tick_hz=int(row["tick_hz"]),
                duration_ticks=int(row["duration_ticks"]),
                timestamps_ticks=tuple(event_rows.pop(sample_id, [])),
                input_voltage_v=None if not voltage else float(voltage),
                source=row["source"],
                synthetic=bool(int(row["synthetic"])),
            ))
    if event_rows:
        raise ValueError(f"event CSV contains unknown sample_id values: {sorted(event_rows)}")
    if len({w.sample_id for w in windows}) != len(windows):
        raise ValueError("window metadata has duplicate sample_id values")
    return windows
