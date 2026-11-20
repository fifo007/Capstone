"""Brian2 event-driven adapter for the repository's ME_L type network."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from brian2 import (
    Network,
    NetworkOperation,
    NeuronGroup,
    SpikeMonitor,
    Synapses,
    defaultclock,
    ms,
    prefs,
    second,
    start_scope,
    seed,
    volt,
)

from .connectome import ConnectomeModel, INHIBITORY_TYPES, OFF_TYPES
from .events import EventWindow


@dataclass(frozen=True)
class NetworkConfig:
    """Model parameters aligned with BioWire notebook Step 7 defaults."""

    dt_s: float = 0.0005
    tau_m_s: float = 0.015
    tau_syn_s: float = 0.005
    w_scale: float = 0.06
    seed: int = 42
    input_type: str = "L1"
    readout_types: tuple[str, ...] = ("L1", "Mi1")
    rest_v: float = -0.065
    excitatory_v: float = 0.0
    inhibitory_v: float = -0.075
    delta_v_on: float = 0.015
    delta_v_off: float = 0.008
    delta_v_inhibitory: float = 0.010

    def __post_init__(self) -> None:
        if self.dt_s <= 0 or self.tau_m_s <= 0 or self.tau_syn_s <= 0:
            raise ValueError("dt_s, tau_m_s and tau_syn_s must be positive")
        if self.w_scale <= 0:
            raise ValueError("w_scale must be positive")
        if not self.input_type:
            raise ValueError("input_type must be specified")
        if not self.readout_types:
            raise ValueError("at least one readout type is required")


def calibrated_thresholds(model: ConnectomeModel, config: NetworkConfig) -> np.ndarray:
    """Reproduce ``calibrated_thresholds_v1`` from the baseline notebook."""
    thresholds = np.zeros(model.model_size, dtype=np.float64)
    for post_idx, name in enumerate(model.type_names):
        exc_inputs = model.weights_signed[:, post_idx]
        exc_inputs = exc_inputs[exc_inputs > 0]
        if name in OFF_TYPES:
            delta_v = config.delta_v_off
        elif name in INHIBITORY_TYPES:
            delta_v = config.delta_v_inhibitory
        else:
            delta_v = config.delta_v_on
        base_threshold = config.rest_v + delta_v
        if exc_inputs.size:
            p25 = float(np.percentile(exc_inputs, 25))
            delta_mv = delta_v * 1000.0
            reduction = min(0.20 * delta_mv, p25 / 15.0 * delta_mv * 0.3) / 1000.0
            base_threshold -= reduction
        thresholds[post_idx] = base_threshold
    return thresholds


def event_bins(window: EventWindow, dt_s: float) -> np.ndarray:
    """Count external pulses in Brian2 time bins; preserve same-bin multiplicity."""
    n_steps = int(np.ceil(window.duration_s / dt_s - 1e-12))
    counts = np.zeros(n_steps, dtype=np.int64)
    if not window.timestamps_ticks:
        return counts
    seconds = np.asarray(window.timestamps_ticks, dtype=np.float64) / window.tick_hz
    bins = np.floor(seconds / dt_s + 1e-12).astype(np.int64)
    if np.any(bins < 0) or np.any(bins >= n_steps):
        raise ValueError("event falls outside the simulated window")
    np.add.at(counts, bins, 1)
    return counts


def simulate_event_window(
    model: ConnectomeModel,
    window: EventWindow,
    *,
    event_gain: float,
    config: NetworkConfig = NetworkConfig(),
) -> dict[str, float | str | int | bool]:
    """Inject timestamped input pulses at the selected ME_L boundary node.

    Events are rasterized at ``config.dt_s`` because the inherited BioWire LIF
    equations use a fixed integration step. Multiple hardware pulses in one
    simulation bin are summed as conductance increments; this quantization is
    reported in the model manifest and must be checked against measured rates.
    """
    if not np.isfinite(event_gain) or event_gain <= 0:
        raise ValueError("event_gain must be a finite positive conductance increment")
    index = model.type_to_index
    if config.input_type not in index:
        raise ValueError(f"input type {config.input_type!r} is absent from connectome")
    missing_readouts = [name for name in config.readout_types if name not in index]
    if missing_readouts:
        raise ValueError(f"readout types absent from connectome: {missing_readouts}")

    counts_by_step = event_bins(window, config.dt_s)
    n_steps = len(counts_by_step)
    duration_s = n_steps * config.dt_s
    dt = config.dt_s * second
    prefs.codegen.target = "numpy"
    start_scope()
    seed(config.seed)
    defaultclock.dt = dt

    equations = """
    dv/dt = (E_rest - v + g_exc*(E_exc-v) + g_inh*(E_inh-v) + g_drive*(E_exc-v)) / tau_m : volt
    dg_exc/dt = -g_exc/tau_syn : 1
    dg_inh/dt = -g_inh/tau_syn : 1
    g_drive : 1
    tau_m : second
    v_th : volt
    E_rest : volt
    E_exc : volt
    E_inh : volt
    tau_syn : second
    """
    neurons = NeuronGroup(
        model.model_size,
        model=equations,
        threshold="v > v_th",
        reset="v = E_rest",
        method="euler",
    )
    neurons.tau_m = config.tau_m_s * second
    neurons.tau_syn = config.tau_syn_s * second
    neurons.v = config.rest_v * volt
    neurons.v_th = calibrated_thresholds(model, config) * volt
    neurons.E_rest = config.rest_v * volt
    neurons.E_exc = config.excitatory_v * volt
    neurons.E_inh = config.inhibitory_v * volt
    neurons.g_exc = 0
    neurons.g_inh = 0
    neurons.g_drive = 0

    source, target = np.nonzero(model.weights_signed)
    objects: list[object] = [neurons]
    if source.size:
        signed_values = model.weights_signed[source, target]
        for is_inhibitory, conductance in ((False, "g_exc_post"), (True, "g_inh_post")):
            mask = signed_values < 0 if is_inhibitory else signed_values > 0
            if not mask.any():
                continue
            synapses = Synapses(
                neurons,
                neurons,
                model="w_g : 1",
                on_pre=f"{conductance} += w_g",
            )
            synapses.connect(i=source[mask], j=target[mask])
            synapses.w_g = np.abs(signed_values[mask]).astype(float) / 15.0 * config.w_scale
            objects.append(synapses)

    input_idx = index[config.input_type]

    def inject_binned_pulses(t) -> None:
        step = int(round(float(t / dt)))
        if 0 <= step < n_steps and counts_by_step[step]:
            neurons.g_exc[input_idx] += float(counts_by_step[step]) * event_gain

    pulse_injector = NetworkOperation(
        inject_binned_pulses,
        dt=dt,
        when="start",
        order=0,
        name="pulse_event_injector*",
    )
    spike_monitor = SpikeMonitor(neurons)
    objects.extend((pulse_injector, spike_monitor))
    network = Network(*objects)
    network.run(duration_s * second)

    spike_times_ms = np.asarray(spike_monitor.t / ms, dtype=float)
    spike_indices = np.asarray(spike_monitor.i, dtype=np.int64)
    duration_ms = duration_s * 1000.0
    row: dict[str, float | str | int | bool] = {
        "sample_id": window.sample_id,
        "input_voltage_v": float("nan") if window.input_voltage_v is None else window.input_voltage_v,
        "pulse_count": len(window.timestamps_ticks),
        "pulse_rate_hz": window.event_rate_hz,
        "duration_s": window.duration_s,
        "dt_s": config.dt_s,
        "event_gain": float(event_gain),
        "synthetic_events": bool(window.synthetic),
    }
    for name in config.readout_types:
        idx = index[name]
        times = spike_times_ms[spike_indices == idx]
        row[f"{name}_spike_count"] = int(times.size)
        row[f"{name}_first_latency_ms"] = float(times[0]) if times.size else duration_ms
        row[f"{name}_mean_isi_ms"] = float(np.diff(times).mean()) if times.size > 1 else duration_ms
    return row
