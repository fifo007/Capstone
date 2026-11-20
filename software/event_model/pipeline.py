"""Hardware-free pulse-to-neural-feature-to-6-bit demonstration pipeline."""

from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pandas as pd

from .connectome import load_connectome_model, load_flywire_connectome, save_connectome_model
from .decoder import FeatureDecoder, spike_feature_names
from .events import (
    EventWindow,
    generate_periodic_window,
    generate_poisson_window,
    load_event_windows,
    save_event_windows,
)
from .network import NetworkConfig, simulate_event_window


def validate_decoder_compatibility(
    decoder: FeatureDecoder,
    *,
    connectome,
    config: NetworkConfig,
    event_gain: float,
) -> None:
    """Reject inference with a mismatched calibrated network configuration."""
    metadata = decoder.training_metadata or {}
    if not metadata:
        return
    if not np.isclose(float(metadata.get("event_gain", np.nan)), event_gain, rtol=1e-10, atol=1e-12):
        raise ValueError("decoder event_gain does not match inference event_gain")
    canonical = lambda value: json.dumps(value, sort_keys=True, separators=(",", ":"))
    if canonical(metadata.get("network_config", {})) != canonical(asdict(config)):
        raise ValueError("decoder NetworkConfig does not match inference NetworkConfig")
    if list(metadata.get("connectome_type_names", [])) != list(connectome.type_names):
        raise ValueError("decoder connectome type ordering does not match the loaded connectome")
    if canonical(metadata.get("connectome_source_hashes", {})) != canonical(connectome.source_hashes):
        raise ValueError("decoder dataset hashes do not match the loaded connectome")


def run_synthetic_sweep(
    *,
    data_dir: str | Path,
    output_dir: str | Path,
    sample_count: int = 64,
    duration_s: float = 0.2,
    tick_hz: int = 100_000_000,
    frequency_min_hz: float = 50.0,
    frequency_max_hz: float = 400.0,
    event_gain: float = 1.0,
    w_scale: float = 0.5,
    event_source: str = "periodic",
    seed: int = 42,
    model_size: int = 100,
) -> dict[str, object]:
    """Run a labeled synthetic voltage sweep and held-out 6-bit evaluation.

    The linear voltage-to-frequency map here is an explicit simulation
    assumption, not an LM331 transfer function or physical calibration. Only
    neural spike features enter the fitted decoder; pulse rate and synthetic
    labels are excluded from its input features.
    """
    if sample_count < 8:
        raise ValueError("sample_count must be at least 8 for a train/test sweep")
    if duration_s <= 0 or tick_hz <= 0:
        raise ValueError("duration_s and tick_hz must be positive")
    if frequency_min_hz <= 0 or frequency_max_hz <= frequency_min_hz:
        raise ValueError("frequency range must be positive and increasing")
    if frequency_max_hz >= tick_hz:
        raise ValueError("frequency_max_hz must be below tick_hz")
    if frequency_max_hz >= 1.0 / (2.0 * NetworkConfig().dt_s):
        raise ValueError("frequency_max_hz must be below the 1/(2*dt) event-raster limit")
    if event_source not in {"periodic", "poisson"}:
        raise ValueError("event_source must be 'periodic' or 'poisson'")

    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    connectome = load_flywire_connectome(data_dir, model_size=model_size)
    readouts = tuple(name for name in ("L1", "Mi1") if name in connectome.type_to_index)
    if not readouts:
        raise ValueError("connectome must include the L1 input boundary node")
    config = NetworkConfig(w_scale=w_scale, seed=seed, readout_types=readouts)

    voltages = np.linspace(0.0, 1.0, sample_count)
    windows = []
    rows = []
    for index, voltage in enumerate(voltages):
        frequency = frequency_min_hz + float(voltage) * (frequency_max_hz - frequency_min_hz)
        sample_id = f"synthetic_{index:04d}"
        if event_source == "periodic":
            window = generate_periodic_window(
                sample_id, frequency, duration_s, tick_hz,
                input_voltage_v=float(voltage), synthetic=True,
            )
        else:
            window = generate_poisson_window(
                sample_id, frequency, duration_s, tick_hz, seed=seed + index,
                input_voltage_v=float(voltage),
            )
        windows.append(window)
        rows.append(simulate_event_window(connectome, window, event_gain=event_gain, config=config))

    indices = np.arange(sample_count)
    test_mask = indices % 4 == 2
    if not test_mask.any() or test_mask.all():
        raise ValueError("sweep split produced an empty training or test partition")
    train_indices = indices[~test_mask]
    test_indices = indices[test_mask]
    feature_names = spike_feature_names(readouts)
    decoder = FeatureDecoder.fit(
        [rows[i] for i in train_indices],
        [float(voltages[i]) for i in train_indices],
        feature_names=feature_names,
        ridge_alpha=1e-2,
        calibration_source=f"synthetic-{event_source}-sweep",
        training_metadata={
            "event_gain": event_gain,
            "network_config": asdict(config),
            "connectome_type_names": list(connectome.type_names),
            "connectome_source_hashes": connectome.source_hashes,
        },
    )
    predicted_voltage = decoder.predict_voltage(rows)
    predicted_codes = decoder.predict_code(rows)
    target_codes = np.rint(voltages * 63.0).astype(np.uint8)

    result_rows = []
    for i, row in enumerate(rows):
        result_rows.append({
            **row,
            "partition": "test" if test_mask[i] else "train",
            "target_voltage_v": float(voltages[i]),
            "target_code_6bit": int(target_codes[i]),
            "decoded_voltage_v": float(predicted_voltage[i]),
            "decoded_code_6bit": int(predicted_codes[i]),
            "absolute_code_error": int(abs(int(predicted_codes[i]) - int(target_codes[i]))),
        })

    heldout_error = np.abs(predicted_codes[test_indices].astype(int) - target_codes[test_indices].astype(int))
    heldout_voltage_error = np.abs(predicted_voltage[test_indices] - voltages[test_indices])
    metrics = {
        "test_samples": int(test_indices.size),
        "mae_voltage_v": float(heldout_voltage_error.mean()),
        "mae_code_lsb": float(heldout_error.mean()),
        "exact_code_fraction": float(np.mean(heldout_error == 0)),
        "monotonic_fraction_full_sweep": float(np.mean(np.diff(predicted_codes) >= 0)),
    }

    save_event_windows(
        windows,
        output / "synthetic_events.csv",
        output / "synthetic_windows.csv",
    )
    save_connectome_model(connectome, output / "connectome_model.npz")
    decoder.save(output / "feature_decoder.json")
    pd.DataFrame(result_rows).to_csv(output / "sweep_results.csv", index=False)
    manifest = {
        "pipeline": "synthetic timestamped pulses -> BioWire ME_L Brian2 network -> neural-feature ridge decoder -> 6-bit code",
        "synthetic_only": True,
        "hardware_input_used": False,
        "voltage_frequency_assumption": {
            "kind": "linear synthetic mapping",
            "frequency_min_hz": frequency_min_hz,
            "frequency_max_hz": frequency_max_hz,
            "duration_s": duration_s,
            "source": event_source,
            "seed": seed,
        },
        "network_config": asdict(config),
        "model": connectome.manifest(),
        "decoder_feature_names": list(feature_names),
        "training_sample_ids": [windows[i].sample_id for i in train_indices],
        "heldout_sample_ids": [windows[i].sample_id for i in test_indices],
        "heldout_metrics": metrics,
        "quantizer": "round(clip(decoded_voltage_v, 0, 1) * 63)",
        "warning": "Synthetic results validate software execution only; they are not LM331 calibration, biological validation, or hardware measurements.",
    }
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def calibrate_labeled_windows(
    *,
    events_csv: str | Path,
    windows_csv: str | Path,
    data_dir: str | Path,
    output_dir: str | Path,
    event_gain: float,
    w_scale: float = 0.2,
    seed: int = 42,
    model_size: int = 100,
    allow_synthetic: bool = False,
    connectome_file: str | Path | None = None,
) -> dict[str, object]:
    """Fit and hold out a voltage decoder from labeled event-window CSVs.

    Physical calibration callers should use windows whose voltage labels were
    measured with an instrument and whose ``synthetic`` flag is false. The
    default rejects synthetic windows so a simulated transfer function cannot
    be mistaken for a hardware calibration.
    """
    windows = load_event_windows(events_csv, windows_csv)
    if len(windows) < 8:
        raise ValueError("at least eight labeled windows are required for calibration and held-out evaluation")
    missing_labels = [window.sample_id for window in windows if window.input_voltage_v is None]
    if missing_labels:
        raise ValueError(f"calibration windows need measured voltage labels: {missing_labels[:5]}")
    synthetic_flags = {window.synthetic for window in windows}
    if len(synthetic_flags) != 1:
        raise ValueError("calibration windows must not mix synthetic and non-synthetic records")
    synthetic_only = synthetic_flags == {True}
    if not allow_synthetic and synthetic_only:
        raise ValueError("synthetic windows rejected; pass allow_synthetic=True only for an explicitly synthetic calibration")

    connectome = (
        load_connectome_model(connectome_file)
        if connectome_file is not None
        else load_flywire_connectome(data_dir, model_size=model_size)
    )
    readouts = tuple(name for name in ("L1", "Mi1") if name in connectome.type_to_index)
    config = NetworkConfig(w_scale=w_scale, seed=seed, readout_types=readouts)
    rows = [simulate_event_window(connectome, window, event_gain=event_gain, config=config) for window in windows]

    unique_voltages = sorted({round(float(w.input_voltage_v), 9) for w in windows})
    if len(unique_voltages) < 4:
        raise ValueError("at least four distinct labeled voltage levels are required for a meaningful held-out split")
    test_levels = {voltage for i, voltage in enumerate(unique_voltages) if i % 4 == 2}
    if not test_levels:
        test_levels = {unique_voltages[len(unique_voltages) // 2]}
    test_mask = np.array([round(float(w.input_voltage_v), 9) in test_levels for w in windows])
    train_indices = np.flatnonzero(~test_mask)
    test_indices = np.flatnonzero(test_mask)
    if train_indices.size < 2 or test_indices.size < 1:
        raise ValueError("calibration split needs at least two training samples and one held-out sample")

    feature_names = spike_feature_names(readouts)
    labels = np.asarray([float(w.input_voltage_v) for w in windows])
    decoder = FeatureDecoder.fit(
        [rows[i] for i in train_indices], labels[train_indices],
        feature_names=feature_names, ridge_alpha=1e-2,
        calibration_source=(
            "synthetic-event-windows" if synthetic_only else "non-synthetic-labeled-event-windows"
        ),
        training_metadata={
            "event_gain": event_gain,
            "network_config": asdict(config),
            "connectome_type_names": list(connectome.type_names),
            "connectome_source_hashes": connectome.source_hashes,
        },
    )
    predicted_voltage = decoder.predict_voltage(rows)
    predicted_codes = decoder.predict_code(rows)
    target_codes = np.rint(labels * 63.0).astype(np.uint8)
    code_error = np.abs(predicted_codes[test_indices].astype(int) - target_codes[test_indices].astype(int))
    manifest = {
        "pipeline": "labeled pulse windows -> BioWire ME_L Brian2 network -> neural-feature ridge decoder -> 6-bit code",
        "synthetic_only": synthetic_only,
        "hardware_input_used": any(w.source == "pynq-axi-lite-fifo" for w in windows),
        "window_sources": sorted({w.source for w in windows}),
        "voltage_label_note": "Labels are caller supplied; this code does not independently verify measurement provenance.",
        "network_config": asdict(config),
        "event_gain": event_gain,
        "model": connectome.manifest(),
        "decoder_feature_names": list(feature_names),
        "training_sample_ids": [windows[i].sample_id for i in train_indices],
        "heldout_sample_ids": [windows[i].sample_id for i in test_indices],
        "heldout_metrics": {
            "test_samples": int(test_indices.size),
            "mae_voltage_v": float(np.mean(np.abs(predicted_voltage[test_indices] - labels[test_indices]))),
            "mae_code_lsb": float(code_error.mean()),
            "exact_code_fraction": float(np.mean(code_error == 0)),
        },
        "warning": "Interpret results according to the labeled input data provenance; synthetic labels are not hardware calibration.",
    }
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    save_connectome_model(connectome, output / "connectome_model.npz")
    decoder.save(output / "feature_decoder.json")
    pd.DataFrame([
        {
            **rows[i],
            "partition": "test" if test_mask[i] else "train",
            "target_voltage_v": labels[i],
            "target_code_6bit": int(target_codes[i]),
            "decoded_voltage_v": float(predicted_voltage[i]),
            "decoded_code_6bit": int(predicted_codes[i]),
            "absolute_code_error": abs(int(predicted_codes[i]) - int(target_codes[i])),
        }
        for i in range(len(windows))
    ]).to_csv(output / "calibration_results.csv", index=False)
    (output / "run_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest


def infer_event_window(
    window: EventWindow,
    *,
    decoder: FeatureDecoder,
    data_dir: str | Path,
    event_gain: float,
    w_scale: float = 0.2,
    seed: int = 42,
    model_size: int = 100,
    connectome_file: str | Path | None = None,
) -> dict[str, object]:
    """Run one timestamped input window through the connectome and 6-bit readout."""
    connectome = (
        load_connectome_model(connectome_file)
        if connectome_file is not None
        else load_flywire_connectome(data_dir, model_size=model_size)
    )
    readouts = tuple(name for name in ("L1", "Mi1") if name in connectome.type_to_index)
    config = NetworkConfig(w_scale=w_scale, seed=seed, readout_types=readouts)
    validate_decoder_compatibility(decoder, connectome=connectome, config=config, event_gain=event_gain)
    features = simulate_event_window(connectome, window, event_gain=event_gain, config=config)
    predicted_voltage = float(decoder.predict_voltage([features])[0])
    predicted_code = int(decoder.predict_code([features])[0])
    return {
        **features,
        "input_voltage_v": window.input_voltage_v,
        "decoded_voltage_v": predicted_voltage,
        "decoded_code_6bit": predicted_code,
        "synthetic_events": window.synthetic,
        "input_source": window.source,
    }
