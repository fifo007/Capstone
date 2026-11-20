from __future__ import annotations

import numpy as np
import pandas as pd
import pytest

from software.event_model.connectome import (
    build_top_type_connectome,
    load_connectome_model,
    save_connectome_model,
)
from software.event_model.decoder import FeatureDecoder, spike_feature_names
from software.event_model.events import (
    EventWindow,
    generate_poisson_window,
    generate_periodic_window,
    load_event_windows,
    save_event_windows,
)
from software.event_model.network import NetworkConfig, event_bins, simulate_event_window
from software.event_model.pynq_reader import (
    HardwareBufferOverrun,
    PynqPulseEventReader,
    Register,
)


def test_event_window_round_trip_preserves_empty_and_populated_samples(tmp_path):
    windows = [
        EventWindow("empty", 1_000_000, 100_000, (), source="test", synthetic=True),
        EventWindow("events", 1_000_000, 100_000, (1_000, 20_000, 99_999), 0.5, "test", True),
    ]
    events_csv = tmp_path / "events.csv"
    windows_csv = tmp_path / "windows.csv"

    save_event_windows(windows, events_csv, windows_csv)

    assert load_event_windows(events_csv, windows_csv) == windows


@pytest.mark.parametrize(
    "ticks,duration",
    [((-1,), 10), ((10,), 10), ((4, 4), 10), ((5, 3), 10)],
)
def test_event_window_rejects_invalid_timestamp_sequences(ticks, duration):
    with pytest.raises(ValueError):
        EventWindow("invalid", 1_000, duration, ticks)


def test_event_window_rejects_non_integer_clock_timestamps():
    with pytest.raises(ValueError, match="integer FPGA ticks"):
        EventWindow("fractional", 1_000, 10, (1.5,))


def test_periodic_generator_is_deterministic_and_explicitly_synthetic():
    window = generate_periodic_window("s0", 100, 0.05, 1_000_000)

    assert window.synthetic is True
    assert window.source == "synthetic-periodic"
    assert window.timestamps_ticks == tuple(range(10_000, 50_000, 10_000))
    assert window.event_rate_hz == pytest.approx(80.0)


def test_poisson_generator_is_seeded_and_produces_valid_synthetic_events():
    first = generate_poisson_window("p", 100.0, 0.5, 1_000_000, seed=9)
    second = generate_poisson_window("p", 100.0, 0.5, 1_000_000, seed=9)

    assert first == second
    assert first.synthetic is True
    assert first.source == "synthetic-poisson"
    assert 20 <= len(first.timestamps_ticks) <= 80


def test_connectome_builder_matches_notebook_quantization_and_row_signs():
    cells = pd.DataFrame(
        {
            "root_id": [1, 2, 3],
            "primary_type": ["L1", "Mi1", "Tm4"],
        }
    )
    connections = pd.DataFrame(
        {
            "pre_root_id": [1, 3, 2],
            "post_root_id": [2, 2, 1],
            "syn_count": [100, 50, 25],
            "neuropil": ["ME_L"] * 3,
        }
    )

    model = build_top_type_connectome(cells, connections, model_size=3, force_t4_t5=False)
    idx = model.type_to_index

    assert model.weights_unsigned[idx["L1"], idx["Mi1"]] == 15
    assert model.weights_unsigned[idx["Tm4"], idx["Mi1"]] == 8
    assert model.weights_signed[idx["Tm4"], idx["Mi1"]] == -8
    assert model.weights_signed[idx["L1"], idx["Mi1"]] == 15


def test_compact_connectome_model_round_trip_preserves_hashes_and_weights(tmp_path):
    cells = pd.DataFrame({"root_id": [1, 2, 3], "primary_type": ["L1", "Mi1", "Tm4"]})
    connections = pd.DataFrame({
        "pre_root_id": [1, 3, 2],
        "post_root_id": [2, 2, 1],
        "syn_count": [100, 50, 25],
        "neuropil": ["ME_L"] * 3,
    })
    model = build_top_type_connectome(
        cells, connections, model_size=3, force_t4_t5=False,
        source_mode="test-fixture", source_hashes={"cells": "abc123"},
    )
    path = tmp_path / "connectome_model.npz"

    save_connectome_model(model, path)
    restored = load_connectome_model(path)

    assert restored.type_names == model.type_names
    assert restored.source_hashes == model.source_hashes
    np.testing.assert_array_equal(restored.weights_signed, model.weights_signed)
    np.testing.assert_array_equal(restored.weights_unsigned, model.weights_unsigned)


def test_event_bins_keep_count_and_place_boundary_events_in_next_bin():
    window = EventWindow("bins", 1_000_000, 2_000, (0, 499, 500, 999, 1_000, 1_999))

    bins = event_bins(window, dt_s=0.0005)

    np.testing.assert_array_equal(bins, [2, 2, 1, 1])


def test_brian2_network_runs_timestamped_input_and_returns_readout_features():
    from software.event_model.connectome import ConnectomeModel

    weights = np.array([[0, 15], [0, 0]], dtype=np.int8)
    model = ConnectomeModel(
        type_names=("L1", "Mi1"),
        weights_signed=weights,
        weights_unsigned=weights.copy(),
        raw_global_max=1,
        model_size=2,
        source_mode="test-fixture",
        source_hashes={},
    )
    window = EventWindow(
        "network", 1_000_000, 100_000, tuple(range(1_000, 100_000, 1_000)),
        source="synthetic-test", synthetic=True,
    )
    config = NetworkConfig(readout_types=("L1",), seed=7)

    result = simulate_event_window(model, window, event_gain=0.15, config=config)

    assert result["pulse_count"] == len(window.timestamps_ticks)
    assert result["synthetic_events"] is True
    assert result["L1_spike_count"] > 0
    assert result["L1_first_latency_ms"] < result["duration_s"] * 1000


class FakeMMIO:
    def __init__(self, events=(), *, overrun=False, overrun_count=0):
        self.events = list(events)
        self.overrun = overrun
        self.overrun_count = overrun_count
        self.read_offset = None

    def read(self, offset):
        if offset == Register.STATUS:
            return (int(self.overrun) << 31) | len(self.events)
        if offset == Register.OVERRUN_COUNT:
            return self.overrun_count
        if offset == Register.EVENT_TIME_LO:
            self.read_offset = offset
            return self.events[0] & 0xFFFFFFFF if self.events else 0
        if offset == Register.EVENT_TIME_HI_POP:
            value = self.events.pop(0) >> 32 if self.events else 0
            return value & 0xFFFFFFFF
        raise AssertionError(f"unexpected read register {offset}")

    def write(self, offset, value):
        raise AssertionError(f"unexpected write register {offset}={value}")


def test_mmio_reader_drains_timestamps_and_rejects_overrun():
    high = (1 << 40) + 99
    mmio = FakeMMIO([17, high])
    reader = PynqPulseEventReader(mmio, tick_hz=100_000_000)

    assert reader.read_available() == [17, high]
    with pytest.raises(HardwareBufferOverrun, match=r"overflowed 2 time\(s\)"):
        PynqPulseEventReader(FakeMMIO(overrun=True, overrun_count=2), tick_hz=100_000_000).read_available()


@pytest.mark.parametrize("tick_hz", [0, -1, 100_000_000.5, True])
def test_mmio_reader_requires_an_integer_verified_clock_rate(tick_hz):
    with pytest.raises(ValueError, match="verified positive FCLK0 rate"):
        PynqPulseEventReader(FakeMMIO(), tick_hz=tick_hz)


def test_mmio_reader_rejects_non_integer_drain_limit():
    with pytest.raises(ValueError, match="non-negative integer"):
        PynqPulseEventReader(FakeMMIO(), tick_hz=100_000_000).read_available(max_events=1.5)


@pytest.mark.parametrize("duration_s,poll_interval_s", [(float("nan"), 0.001), (1.0, float("inf"))])
def test_capture_window_rejects_non_finite_timing(duration_s, poll_interval_s):
    reader = PynqPulseEventReader(FakeMMIO(), tick_hz=100_000_000)

    with pytest.raises(ValueError, match="finite and positive"):
        reader.capture_window(
            sample_id="bad-timing",
            duration_s=duration_s,
            poll_interval_s=poll_interval_s,
        )


def test_mmio_cycle_counter_read_retries_across_low_word_rollover():
    class RolloverMMIO:
        def __init__(self):
            self.high = iter([5, 6, 6, 6])
            self.low = iter([0xFFFFFFF0, 0x12])

        def read(self, offset):
            if offset == Register.CYCLE_COUNT_HI:
                return next(self.high)
            if offset == Register.CYCLE_COUNT_LO:
                return next(self.low)
            raise AssertionError(f"unexpected register {offset}")

        def write(self, offset, value):
            raise AssertionError("unexpected MMIO write")

    reader = PynqPulseEventReader(RolloverMMIO(), tick_hz=100_000_000)

    assert reader._read_cycle_count() == (6 << 32) | 0x12


def test_capture_window_discards_stale_fifo_events_and_returns_relative_ticks(monkeypatch):
    from software.event_model import pynq_reader

    class CaptureMMIO:
        def __init__(self):
            self.events = [5, 7]  # left over from an earlier capture
            self.tick = 100
            self.enabled = False
            self.overrun = False

        def read(self, offset):
            if offset == Register.STATUS:
                return (int(self.overrun) << 31) | (int(self.enabled) << 30) | len(self.events)
            if offset == Register.OVERRUN_COUNT:
                return 0
            if offset == Register.CYCLE_COUNT_LO:
                return self.tick & 0xFFFFFFFF
            if offset == Register.CYCLE_COUNT_HI:
                return self.tick >> 32
            if offset == Register.EVENT_TIME_LO:
                return self.events[0] & 0xFFFFFFFF if self.events else 0
            if offset == Register.EVENT_TIME_HI_POP:
                return (self.events.pop(0) >> 32) & 0xFFFFFFFF if self.events else 0
            raise AssertionError(f"unexpected read register {offset}")

        def write(self, offset, value):
            assert offset == Register.CONTROL
            self.enabled = bool(value & 1)
            if value & 2:
                self.overrun = False

    class FakeClock:
        now = 0.0

        def monotonic(self):
            return self.now

        def sleep(self, _seconds):
            mmio.events.extend([120, 130])
            mmio.tick = 140
            self.now = 0.002

    mmio = CaptureMMIO()
    fake_clock = FakeClock()
    monkeypatch.setattr(pynq_reader.time, "monotonic", fake_clock.monotonic)
    monkeypatch.setattr(pynq_reader.time, "sleep", fake_clock.sleep)
    reader = PynqPulseEventReader(mmio, tick_hz=100_000_000)

    window = reader.capture_window(sample_id="capture", duration_s=0.001)

    assert window.timestamps_ticks == (20, 30)
    assert window.duration_ticks == 40
    assert window.synthetic is False
    assert mmio.events == []
    assert mmio.enabled is False


def test_feature_decoder_fits_saves_loads_and_quantizes(tmp_path):
    names = spike_feature_names(("L1",))
    rows = [
        {"L1_spike_count": float(i), "L1_first_latency_ms": 50.0 - i, "L1_mean_isi_ms": 1.0}
        for i in range(8)
    ]
    targets = np.linspace(0.0, 1.0, len(rows))
    decoder = FeatureDecoder.fit(
        rows, targets, feature_names=names, calibration_source="synthetic-test"
    )

    predicted = decoder.predict_voltage(rows)
    assert np.mean(np.abs(predicted - targets)) < 0.01
    assert decoder.predict_code(rows)[0] == 0
    assert decoder.predict_code(rows)[-1] == 63

    path = tmp_path / "decoder.json"
    decoder.save(path)
    restored = FeatureDecoder.load(path)
    np.testing.assert_allclose(restored.predict_voltage(rows), predicted)
