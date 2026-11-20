from __future__ import annotations

import json

import numpy as np
import pytest

from software.event_model.connectome import ConnectomeModel
from software.event_model.events import EventWindow, save_event_windows
from software.event_model import pipeline


def _tiny_model():
    weights = np.array([[0, 15], [0, 0]], dtype=np.int8)
    return ConnectomeModel(
        type_names=("L1", "Mi1"),
        weights_signed=weights,
        weights_unsigned=weights.copy(),
        raw_global_max=1.0,
        model_size=2,
        source_mode="test",
        source_hashes={},
    )


def test_calibration_refuses_synthetic_windows_without_override(tmp_path):
    windows = [
        EventWindow(f"s{i}", 1_000_000, 100_000, (1_000 * i + 1,), i / 7, "synthetic-test", True)
        for i in range(8)
    ]
    events = tmp_path / "events.csv"
    metadata = tmp_path / "windows.csv"
    save_event_windows(windows, events, metadata)

    with pytest.raises(ValueError, match="synthetic windows rejected"):
        pipeline.calibrate_labeled_windows(
            events_csv=events,
            windows_csv=metadata,
            data_dir=tmp_path / "no-data-needed",
            output_dir=tmp_path / "out",
            event_gain=0.3,
        )


def test_calibration_rejects_mixed_synthetic_and_non_synthetic_records(tmp_path):
    windows = [
        EventWindow(
            f"s{i}", 1_000_000, 100_000, (1_000 * i + 1,), i / 7,
            "mixed-test", synthetic=(i == 0),
        )
        for i in range(8)
    ]
    events = tmp_path / "events.csv"
    metadata = tmp_path / "windows.csv"
    save_event_windows(windows, events, metadata)

    with pytest.raises(ValueError, match="must not mix synthetic"):
        pipeline.calibrate_labeled_windows(
            events_csv=events,
            windows_csv=metadata,
            data_dir=tmp_path / "no-data-needed",
            output_dir=tmp_path / "out",
            event_gain=0.3,
            allow_synthetic=True,
        )


def test_calibration_groups_voltage_levels_and_records_heldout_outputs(tmp_path, monkeypatch):
    voltages = np.linspace(0.0, 1.0, 8)
    windows = [
        EventWindow(
            f"measured_{i}", 1_000_000, 100_000,
            tuple(range(1_000, 1_000 + (i + 1) * 1_000, 1_000)),
            float(voltage), "bench-log", False,
        )
        for i, voltage in enumerate(voltages)
    ]
    events = tmp_path / "events.csv"
    metadata = tmp_path / "windows.csv"
    save_event_windows(windows, events, metadata)
    monkeypatch.setattr(pipeline, "load_flywire_connectome", lambda *a, **k: _tiny_model())

    def fake_simulate(model, window, *, event_gain, config):
        count = len(window.timestamps_ticks)
        return {
            "sample_id": window.sample_id,
            "L1_spike_count": count,
            "L1_first_latency_ms": 100.0 / count,
            "L1_mean_isi_ms": 100.0 / count,
            "Mi1_spike_count": count * 2,
            "Mi1_first_latency_ms": 50.0 / count,
            "Mi1_mean_isi_ms": 50.0 / count,
        }

    monkeypatch.setattr(pipeline, "simulate_event_window", fake_simulate)
    output = tmp_path / "calibration"
    result = pipeline.calibrate_labeled_windows(
        events_csv=events,
        windows_csv=metadata,
        data_dir=tmp_path,
        output_dir=output,
        event_gain=0.3,
    )

    assert result["training_sample_ids"] == ["measured_0", "measured_1", "measured_3", "measured_4", "measured_5", "measured_7"]
    assert result["heldout_sample_ids"] == ["measured_2", "measured_6"]
    assert result["synthetic_only"] is False
    assert result["heldout_metrics"]["test_samples"] == 2
    assert (output / "feature_decoder.json").exists()
    assert (output / "calibration_results.csv").exists()
    manifest = json.loads((output / "run_manifest.json").read_text(encoding="utf-8"))
    assert manifest["window_sources"] == ["bench-log"]
    from software.event_model.decoder import FeatureDecoder
    from software.event_model.network import NetworkConfig

    decoder = FeatureDecoder.load(output / "feature_decoder.json")
    pipeline.validate_decoder_compatibility(
        decoder,
        connectome=_tiny_model(),
        config=NetworkConfig(w_scale=0.2, readout_types=("L1", "Mi1")),
        event_gain=0.3,
    )
    with pytest.raises(ValueError, match="event_gain"):
        pipeline.validate_decoder_compatibility(
            decoder,
            connectome=_tiny_model(),
            config=NetworkConfig(w_scale=0.2, readout_types=("L1", "Mi1")),
            event_gain=0.4,
        )
    monkeypatch.setattr(pipeline, "load_flywire_connectome", lambda *a, **k: _tiny_model())
    monkeypatch.setattr(pipeline, "simulate_event_window", fake_simulate)
    inferred = pipeline.infer_event_window(
        EventWindow("unlabeled", 1_000_000, 100_000, (1_000, 2_000), None, "pynq-axi-lite-fifo", False),
        decoder=decoder,
        data_dir=tmp_path,
        event_gain=0.3,
        w_scale=0.2,
    )
    assert inferred["input_voltage_v"] is None
    assert 0 <= inferred["decoded_code_6bit"] <= 63
