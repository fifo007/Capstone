# Pulse-driven event model

This directory implements the software side of the pulse-driven architecture in isolation from the existing BioWire notebook and saved experiments. It builds a ME_L type-level connectome from the repository's FlyWire data, injects timestamped events at the selected `L1` boundary node, extracts spike features, and decodes them to a 6-bit value.

The ME_L extract contains no `R1-6` node, so `L1` is an explicit network boundary assumption. The simulation preserves the BioWire notebook's type aggregation, signed 4-bit weights, LIF equations, and default integration step. External timestamps are rasterized to the Brian2 `dt` (default 0.5 ms); pulse events in one bin are summed. The synthetic demo limits average input frequency below `1/(2*dt)` to keep its default pulse train within that event-raster limit.

## Modules

| File | Role |
|---|---|
| `events.py` | Validated `EventWindow`, paired CSV read/write, and periodic/seeded-Poisson synthetic event generation. These are mathematical event sources, not an LM331 model. |
| `connectome.py` | Builds the notebook's ME_L top-type matrix, applies inhibitory presynaptic row signs, records SHA-256 hashes, and saves/loads a compact provenance-bearing NPZ model. |
| `network.py` | Injects time-binned pulses at L1 into the Brian2 network and returns readout spike count, first latency, and mean inter-spike interval features. `w_scale` and `event_gain` are explicit model parameters. |
| `decoder.py` | Fits/scales a ridge-linear readout using neural spike features only, serializes the model, clips voltage to 0–1 V, and rounds to codes 0–63. |
| `pipeline.py` | Runs synthetic sweeps, fits/tests held-out decoders, trains from labeled event windows, and performs single-window inference. |
| `pynq_reader.py` | Reads timestamp FIFO events from PYNQ MMIO and rejects captures that report FIFO overrun. |
| `__main__.py` | CLI for synthetic demonstration, labeled-window calibration, and stored-window inference. |
| `tests/` | Tests for event data, connectome quantization/signs, event binning, Brian2 execution, decoder persistence, and MMIO FIFO reads. |

## Setup and data

Use Python 3.10 or 3.11. From the repository root, install the pinned host dependencies and test runner:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r software\event_model\requirements.txt
git lfs install
git lfs pull
```

The two required inputs are `biowire/consolidated_cell_types.csv.gz` and the Git LFS file `biowire/connections_princeton_no_threshold.csv.gz`. The connectome loader checks that both exist and rejects tiny unresolved LFS pointer files. On Linux/macOS, activate with `source .venv/bin/activate` and use forward slashes in paths.

## Hardware-free synthetic demonstration

From the repository root:

```powershell
python -m software.event_model demo --data-dir biowire --output-dir runs/event_model_demo
```

The default 64-point sweep assumes a **synthetic linear** voltage-to-frequency map from 50 to 400 Hz over 0.2 s. It creates periodic pulse timestamps, simulates the 100-type ME_L network, trains a decoder on three quarters of the voltage levels, and evaluates it on held-out levels. `--event-source poisson` selects reproducible seeded Poisson events. The event-model demo parameters are `event_gain=1.0` and `w_scale=0.5`; the original BioWire network's baseline scale remains 0.06 in its own code/configuration. These demo settings make downstream activity visible in this synthetic sweep and are not calibrated to LM331 data. Adjust `--samples`, `--duration-s`, `--frequency-min-hz`, `--frequency-max-hz`, `--event-gain`, `--w-scale`, `--seed`, or `--model-size` to explore assumptions; rerun output goes only to the chosen output directory.

Outputs are `synthetic_events.csv`, `synthetic_windows.csv`, `connectome_model.npz`, `feature_decoder.json`, `sweep_results.csv`, and `run_manifest.json`. The compact NPZ contains the type-level weights and source hashes, so later inference does not need to reload the 275 MB compressed FlyWire connections table. The manifest records data hashes, type ordering, neural parameters, train/test IDs, assumptions, and held-out metrics. `sweep_results.csv` includes neural features and decoded code. The decoder uses L1/Mi1 spike features and does not receive synthetic input frequency or target voltage as a feature.

One recorded 64-sample run using the checked-in FlyWire tables, 100 types, 0.2 s windows, 50–400 Hz, `event_gain=1.0`, and `w_scale=0.5` reported 16 held-out samples, 0.00633 V MAE, 0.125 code-LSB MAE, 87.5% exact-code fraction, and a monotonic full-sweep prediction. L1 spiked in all 64 samples and Mi1 in 42. These are results on a synthetic linear mapping and synthetic periodic pulses; they do not validate the LM331 transfer function, analog accuracy, physical pulse timing, or hardware.

## Fit from labeled event windows

The paired CSV format is written by `save_event_windows()` in `events.py`. Each metadata row needs a measured `input_voltage_v` label. For hardware calibration, use windows whose voltage labels were measured with an instrument and whose `synthetic` flag is false; preserve source/run details in `source` and in the hardware logs. The calibrator rejects windows marked synthetic by default and holds out entire voltage levels rather than randomly splitting repeated rows at the same voltage.

```powershell
python -m software.event_model calibrate `
  --events-csv runs/measured/events.csv `
  --windows-csv runs/measured/windows.csv `
  --connectome-file runs/event_model_demo/connectome_model.npz `
  --output-dir runs/measured/calibration `
  --event-gain 1.0 `
  --w-scale 0.5
```

Use `--allow-synthetic` only for an explicitly synthetic calibration. Synthetic and non-synthetic records cannot be mixed in one calibration run. A `synthetic=false` flag and a supplied voltage label do not independently prove that a measurement was taken: verify the electrical interface, label source, repeatability, FIFO overrun status, and model parameters. The decoder records a neutral `non-synthetic-labeled-event-windows` source label rather than claiming measurements were independently verified. Output includes `feature_decoder.json`, `calibration_results.csv`, and `run_manifest.json` with held-out metrics and provenance notes.

## Decode a stored event window

Choose one `sample_id` present in the paired event/window CSVs and a decoder trained with compatible network settings:

```powershell
python -m software.event_model infer `
  --events-csv runs/event_model_demo/synthetic_events.csv `
  --windows-csv runs/event_model_demo/synthetic_windows.csv `
  --sample-id synthetic_0000 `
  --decoder runs/event_model_demo/feature_decoder.json `
  --connectome-file runs/event_model_demo/connectome_model.npz `
  --event-gain 1.0 `
  --w-scale 0.5 `
  --output runs/event_model_demo/inference.json
```

Inference outputs the neural features, decoded voltage estimate, 6-bit code, event source and synthetic flag. For live PYNQ use, call `PynqPulseEventReader.from_overlay()` on the board with the verified FCLK0 rate, capture an event window, and pass the resulting `EventWindow` through `simulate_event_window()` and the loaded `FeatureDecoder`. Capture disables the source, clears the sticky overrun flag, drains events left in the FIFO, and verifies capture is enabled before collecting a new window. This route is not yet validated on an overlay or physical board.

## Tests

From the repository root:

```powershell
python -m pytest software\event_model\tests -q
```

The suite checks software behavior using small in-memory connectome fixtures, including stale-FIFO draining, relative timestamps for a captured window, rejection of mixed synthetic/non-synthetic calibration records, and validation of clock-rate and timing arguments. The latest run passed all 26 tests. Tests do not characterize real LM331 behavior or validate PYNQ MMIO on hardware. The full 100-type dataset demo is a separate end-to-end command documented above.

## Limits and hardware boundary

`pynq_reader.py` expects the register map in `hardware/rtl/pulse_event_fifo_axi.v`. The FIFO RTL/testbench are separate development files and are not integrated with `pynq_z2_pulse_wrapper` or a Vivado PS block design. The most recent XSim run completed `xvlog`, then failed at `xelab`: the bundled `C:\Xilinx\Vivado\2024.1\tps\mingw\6.2.0\win64.o\nt\bin\gcc.exe` printed “The system cannot execute the specified program.” No FIFO testbench pass is claimed. The runner and logs are isolated under `hardware/simulation/event_fifo_run/`.

For PYNQ-side inference, copy the compact `connectome_model.npz` and calibrated `feature_decoder.json` to the board; this avoids loading the large raw connectome CSVs on the 512 MB ARM system. The `pynq` Python package is supplied by the target PYNQ image and is not part of the host requirements. No pin assignment, LM331 connection, board deployment, or hardware validation is included. See the [project architecture](../../docs/PROJECT_ARCHITECTURE.md) and [campus checklist](../../docs/CAMPUS_HARDWARE_CHECKLIST.md).
