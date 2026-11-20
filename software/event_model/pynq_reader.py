"""PYNQ MMIO reader for the FPGA pulse-event FIFO AXI-Lite register map."""

from __future__ import annotations

import time
from dataclasses import dataclass
from enum import IntEnum
from math import isfinite
from numbers import Integral
from typing import Protocol

from .events import EventWindow


class Register(IntEnum):
    CONTROL = 0x00
    STATUS = 0x04
    EVENT_TIME_LO = 0x08
    EVENT_TIME_HI_POP = 0x0C
    OVERRUN_COUNT = 0x10
    CYCLE_COUNT_LO = 0x14
    CYCLE_COUNT_HI = 0x18
    VERSION = 0x1C


class MMIO(Protocol):
    def read(self, offset: int) -> int: ...
    def write(self, offset: int, value: int) -> None: ...


class HardwareBufferOverrun(RuntimeError):
    """Raised when FPGA FIFO loss makes a captured event window incomplete."""


@dataclass(frozen=True)
class ReaderStatus:
    event_count: int
    capture_enabled: bool
    overrun: bool
    overrun_count: int


class PynqPulseEventReader:
    """Read captured 64-bit PL cycle timestamps through PYNQ ``MMIO``.

    The clock rate is metadata supplied by the caller after verifying the
    configured PS FCLK0 frequency. This reader does not infer or configure the
    PL clock. If the FIFO overrun flag is set, captured data is rejected rather
    than silently treated as complete.
    """

    STATUS_OVERRUN = 1 << 31
    STATUS_ENABLED = 1 << 30
    STATUS_COUNT_MASK = 0xFFFF
    COUNTER_MASK = (1 << 64) - 1

    def __init__(self, mmio: MMIO, *, tick_hz: int):
        if isinstance(tick_hz, bool) or not isinstance(tick_hz, Integral) or tick_hz <= 0:
            raise ValueError("tick_hz must be the verified positive FCLK0 rate")
        self.mmio = mmio
        self.tick_hz = int(tick_hz)

    @classmethod
    def from_overlay(cls, overlay, ip_name: str, *, tick_hz: int) -> "PynqPulseEventReader":
        """Create an MMIO reader from a loaded PYNQ Overlay IP description."""
        ip = overlay.ip_dict[ip_name]
        base = int(ip["phys_addr"])
        length = int(ip["addr_range"])
        try:
            from pynq import MMIO as PynqMMIO
        except ImportError as exc:
            raise RuntimeError("pynq is available only in the target PYNQ environment") from exc
        return cls(PynqMMIO(base, length), tick_hz=tick_hz)

    def status(self) -> ReaderStatus:
        value = int(self.mmio.read(Register.STATUS))
        return ReaderStatus(
            event_count=value & self.STATUS_COUNT_MASK,
            capture_enabled=bool(value & self.STATUS_ENABLED),
            overrun=bool(value & self.STATUS_OVERRUN),
            overrun_count=int(self.mmio.read(Register.OVERRUN_COUNT)),
        )

    def _read_cycle_count(self) -> int:
        # Retry if the low word rolls over between reads so the high/low pair
        # always describes one coherent 64-bit counter value.
        for _ in range(3):
            hi_before = int(self.mmio.read(Register.CYCLE_COUNT_HI)) & 0xFFFFFFFF
            lo = int(self.mmio.read(Register.CYCLE_COUNT_LO)) & 0xFFFFFFFF
            hi_after = int(self.mmio.read(Register.CYCLE_COUNT_HI)) & 0xFFFFFFFF
            if hi_before == hi_after:
                return (hi_after << 32) | lo
        raise RuntimeError("could not read a coherent PL cycle counter value")

    def _pop_event(self) -> int:
        lo = int(self.mmio.read(Register.EVENT_TIME_LO)) & 0xFFFFFFFF
        hi = int(self.mmio.read(Register.EVENT_TIME_HI_POP)) & 0xFFFFFFFF
        return (hi << 32) | lo

    def read_available(self, *, max_events: int | None = None) -> list[int]:
        """Drain currently queued absolute cycle timestamps from the PL FIFO."""
        status = self.status()
        if status.overrun:
            raise HardwareBufferOverrun(
                f"PL event FIFO overflowed {status.overrun_count} time(s); discard this capture"
            )
        count = status.event_count
        if max_events is not None:
            if isinstance(max_events, bool) or not isinstance(max_events, Integral) or max_events < 0:
                raise ValueError("max_events must be a non-negative integer")
            count = min(count, max_events)
        events = [self._pop_event() for _ in range(count)]
        after = self.status()
        if after.overrun:
            raise HardwareBufferOverrun(
                f"PL event FIFO overflowed {after.overrun_count} time(s) while draining"
            )
        return events

    def capture_window(
        self,
        *,
        sample_id: str,
        duration_s: float,
        input_voltage_v: float | None = None,
        poll_interval_s: float = 0.0005,
    ) -> EventWindow:
        """Enable capture for a wall-clock interval and return relative events.

        `duration_s` is measured with the ARM monotonic clock. FPGA timestamps
        are referenced to a nearby free-running PL counter sample. This API is
        suitable for bench calibration at rates the AXI-Lite reader can service;
        validate FIFO overrun and actual timing on the target before relying on
        it for high-rate acquisition.
        """
        if (
            not isfinite(duration_s)
            or not isfinite(poll_interval_s)
            or duration_s <= 0
            or poll_interval_s <= 0
        ):
            raise ValueError("duration_s and poll_interval_s must be finite and positive")
        # Control bit 1 is write-one-to-clear overrun; bit 0 enables capture.
        self.mmio.write(Register.CONTROL, 0x2)
        # Discard records left by an earlier capture before establishing this
        # window's timestamp origin. Capture is disabled, so this queue stays
        # stable while it is drained.
        self.read_available()
        start_tick = self._read_cycle_count()
        start_wall = time.monotonic()
        collected: list[int] = []
        try:
            self.mmio.write(Register.CONTROL, 0x1)
            if not self.status().capture_enabled:
                raise RuntimeError("PL event capture did not enable")
            while time.monotonic() - start_wall < duration_s:
                collected.extend(self.read_available())
                remaining = duration_s - (time.monotonic() - start_wall)
                if remaining > 0:
                    time.sleep(min(poll_interval_s, remaining))
        finally:
            self.mmio.write(Register.CONTROL, 0x0)

        collected.extend(self.read_available())
        stop_tick = self._read_cycle_count()
        duration_ticks = (stop_tick - start_tick) & self.COUNTER_MASK
        if duration_ticks == 0:
            raise RuntimeError("PL timestamp counter did not advance; check clock/reset connection")
        relative = sorted(((event - start_tick) & self.COUNTER_MASK) for event in collected)
        relative = [tick for tick in relative if tick < duration_ticks]
        return EventWindow(
            sample_id=sample_id,
            tick_hz=self.tick_hz,
            duration_ticks=duration_ticks,
            timestamps_ticks=tuple(relative),
            input_voltage_v=input_voltage_v,
            source="pynq-axi-lite-fifo",
            synthetic=False,
        )
