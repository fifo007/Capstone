# Fly Brain ADC

Fly Brain ADC is a research and prototyping repository for a fly-inspired 6-bit ADC. The repository contains early software prototypes and saved BioWire experiments, plus a separate Verilog pulse-counter foundation. The complete analog-to-digital hardware/software chain is **not implemented or hardware-validated**.

## Intended architecture and current status

The long-term concept is: potentiometer voltage → LM331 voltage-to-frequency conversion → PYNQ-Z2 programmable-logic (PL) pulse capture → ARM Processing System (PS) software → future event-driven model → 6-bit code. See [Project architecture](docs/PROJECT_ARCHITECTURE.md) for the data flow, repository map and open decisions.

Current implementation status:

- The root Python scripts are independent software demonstrations/helpers; they do not consume physical board data.
- `biowire/` contains a Brian2/FlyWire connectome notebook and saved voltage-derived research outputs. It is not the future timestamped-pulse model.
- The hardware counter testbench passed in the saved Vivado 2024.1 XSim run. The PYNQ-Z2 wrapper compiled with `xvlog` but has not had its own simulation testbench run.
- No Vivado synthesis, board programming, physical pulse capture, LM331 connection, AXI-to-ARM data path, or hardware validation has been completed.

## Repository structure

```text
README.md                         This guide
adc_test.py                       6-bit sweep, monotonicity and ENOB analysis
baseline_adc.py                   Synthetic noisy-signal 6-bit prototype
simulation.py                     Synthetic noisy-signal 4-bit prototype
fly_adc.py                        Voltage/drive/quantizer calibration helpers
lut.py                            EXP-56B CSV-to-memory-file generator (fixed path)
adc_results.xlsx                  Existing workbook used by adc_test.py
biowire_v1_.ipynb                 Existing top-level notebook snapshot
Fly_Brain_ADC_EXP53_EXP54_artifacts.zip  Existing archive
biowire/                          BioWire notebook, dependencies, data and saved results
hardware/                         Counter RTL, XSim testbench and Vivado setup guide
software/event_model/             Documentation-only future-model placeholder
docs/                             Architecture, audit and hardware visit/log documents
```

Directory guides: [BioWire](biowire/README.md) · [hardware](hardware/README.md) · [RTL](hardware/rtl/README.md) · [testbench](hardware/testbench/README.md) · [XSim](hardware/simulation/README.md) · [Vivado/PYNQ-Z2 setup](hardware/vivado/README.md) · [future event model](software/event_model/README.md).

Project documents: [campus hardware checklist](docs/CAMPUS_HARDWARE_CHECKLIST.md) · [hardware test log](docs/HARDWARE_TEST_LOG.md) · [analog calibration log](docs/ANALOG_CALIBRATION_LOG.md) · [project architecture](docs/PROJECT_ARCHITECTURE.md) · [repository audit](docs/codex_audit.md).

## Prerequisites

- Git. Install [Git LFS](https://git-lfs.com/) to retrieve the tracked large FlyWire connections table.
- Python 3.10 or later for the Python demonstrations. The BioWire Conda environment specifies Python 3.10.
- Conda (Miniforge or Anaconda) for the BioWire notebook, or pip/venv as described in its README.
- Vivado 2024.1 with XSim for the hardware simulation. `hardware/simulation/run_xsim.bat` defaults to `C:\Xilinx\Vivado\2024.1\settings64.bat`; another installation can be selected with `VIVADO_SETTINGS`.
- For PYNQ-Z2 implementation work: the correct PYNQ-Z2 board definition, board, and lab-verified electrical setup. Details are in the [Vivado setup guide](hardware/vivado/README.md).

## Clone and retrieve repository data

In Windows PowerShell, install Git LFS once, then clone and pull LFS data:

```powershell
git lfs install
git clone https://github.com/fifo007/Capstone.git
Set-Location .\Capstone
git lfs pull
git lfs ls-files
```

The current repository tracks `biowire/connections_princeton_no_threshold.csv.gz` with Git LFS. `biowire/consolidated_cell_types.csv.gz` is also present in the repository. If the large connections file is absent or is a small text pointer, run `git lfs pull` from the repository root. The BioWire notebook expects both dataset filenames in its working directory (`biowire/`); see its README for the manual-download fallback and the notebook's path limitations.

## Python environment

From the repository root, create a virtual environment for the root scripts:

```powershell
py -3.10 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install numpy matplotlib pandas openpyxl
```

If PowerShell blocks environment activation, invoke the environment interpreter directly as `./.venv/Scripts/python.exe` (relative to the repository root), or use the current session's approved execution policy; do not change system policy globally for this project. `openpyxl` is needed by `adc_test.py` for Excel output. BioWire has a separate environment and additional dependencies; do not assume this small root environment is sufficient for the notebook.

Linux/macOS equivalent for the root scripts:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install numpy matplotlib pandas openpyxl
```

## Run the root Python programs

These scripts have no command-line argument parser. Run them from the repository root except where noted. Matplotlib figures open interactively and may keep the process running until the plot windows are closed.

### `baseline_adc.py` — synthetic 6-bit prototype

```powershell
python .\baseline_adc.py
```

Generates a deterministic synthetic noisy 0–1 V sine-wave sample, evaluates a 16-neuron population decoder, quantizes to 6 bits, prints MAE/RMSE, and displays signal/activity/spike/reconstruction/code plots. It reads no dataset and creates no output file. The displayed metrics are simulation results, not hardware measurements.

### `simulation.py` — synthetic 4-bit prototype

```powershell
python .\simulation.py
```

Runs a similar deterministic synthetic signal demonstration, but quantizes to **4 bits**. It prints MAE/RMSE and displays figures; it does not save plots or use hardware. Do not confuse it with `baseline_adc.py` or with the 6-bit final target.

### `adc_test.py` — 6-bit monotonicity and ENOB analysis

The script uses a fixed 8-neuron configuration, sweeps 101 points from 0 to 1 V, reports monotonicity/code-drop information, then analyzes an 8192-sample synthetic sine for SINAD/ENOB. It displays plots and writes/replaces four workbook sheets: `Monotonicity_Summary`, `Monotonicity_Details`, `ENOB_Summary`, and `ENOB_Spectrum`. The workbook path is the current working directory's `adc_results.xlsx`; running in the repository root can modify the existing workbook.

Run it in a separate output folder to preserve the checked-in workbook:

```powershell
New-Item -ItemType Directory -Force .\runs\adc_test | Out-Null
Push-Location .\runs\adc_test
python ..\..\adc_test.py
Pop-Location
```

Linux/macOS, from the repository root:

```bash
mkdir -p runs/adc_test
cd runs/adc_test
python ../../adc_test.py
```

### `fly_adc.py` — utility functions

This file defines NumPy-based conversion helpers (`voltage_to_drive`, `quantize_6bit`, spike-count decoding and calibration interpolation) and has no standalone `main` routine. Running `python .\fly_adc.py` simply imports definitions and exits without producing a result. To call the helpers:

```powershell
python -c "from fly_adc import voltage_to_drive, quantize_6bit, calibrated_spikes_to_drive; print(voltage_to_drive(0.5)); print(quantize_6bit(0.5)); print(calibrated_spikes_to_drive(100))"
```

These functions use calibration constants embedded in the source; they do not read hardware or the EXP-56B file at runtime.

### `lut.py` — generate the memory-format LUT

```powershell
python .\lut.py
```

This standard-library script reads `biowire/EXP56B_EXP49_decoder.csv`, checks row count, required columns, 6-bit code range and monotonicity, then writes 101 hexadecimal entries to `biowire/fly_adc_lut.mem`. **The input path is hard-coded to the original `C:\Users\sagni\OneDrive\Documents\capstone\biowire` checkout, and it overwrites the existing LUT file.** It will not work from a differently located clone without a code change; do not run it in this checkout unless intentionally regenerating that file. Its result is a software-derived LUT, not a hardware result.

## Run the BioWire notebook

Follow the [BioWire README](biowire/README.md) for LFS data, Conda/pip setup, notebook launch and output warnings. In brief: create the `biowire` environment from `biowire/environment.yml`, install Jupyter, change into `biowire/`, then open `biowire_v1_.ipynb`. The notebook has saved historical outputs; executing it may take substantial time and overwrite generated experiment files. Later cells also contain machine-specific absolute paths, so full execution from an arbitrary clone is not guaranteed.

The top-level `biowire_v1_.ipynb` is an existing older snapshot. Use the maintained copy in `biowire/` for the documented workflow.

## Run the hardware simulation

From repository-root PowerShell:

```powershell
& .\hardware\simulation\run_xsim.bat
```

The script initializes Vivado and runs `xvlog`, `xelab`, and `xsim`. It writes logs and generated simulator files into `hardware/simulation/`; success includes `PASS: pulse_counter_tb`. The latest saved XSim log has that pass marker. See [hardware simulation instructions](hardware/simulation/README.md) for direct commands, logs and troubleshooting. Icarus Verilog is not the supported project flow.

## Troubleshooting

- **Missing/placeholder FlyWire connections file:** install Git LFS and run `git lfs pull` from the repository root. Confirm the file has a plausible large size rather than the short LFS pointer text.
- **BioWire cannot locate data:** launch Jupyter with `biowire/` as the working directory and confirm the exact `.csv.gz` filenames. Some later notebook audit cells also use the original author's absolute Windows path; those cells are not portable without editing the notebook.
- **`adc_test.py` cannot write Excel:** install `openpyxl`; ensure the current directory is writable. Run from `runs/adc_test/` to avoid changing the root workbook.
- **Matplotlib figures do not appear:** use an interactive Python session/GUI backend; on a headless system choose a supported noninteractive backend, noting that these scripts do not save the figures.
- **`lut.py` says the CSV is missing:** its source path is hard-coded for the original checkout. Do not edit files to work around this without deliberately reviewing the implementation change; the script also overwrites the existing LUT.
- **XSim `xelab` fails:** inspect `xelab_console.log` and `xelab.log` in `hardware/simulation/`, confirm the script's `VIVADO_SETTINGS` path and run from the `.bat`. Old GCC-launch diagnostics are historical; the latest saved counter run passed, but a new run must be judged by its own PASS marker.
- **Expecting Python access to the count or hardware measurements:** neither AXI access nor a physical pulse input/constraint exists yet. The simulations do not validate electrical safety or board behavior.

## No hardware validation claim

The LM331 output remains disconnected from the PYNQ-Z2 until output topology, pull-up, levels, timing, grounding and a suitable board input are verified. No pin assignment, board deployment, or hardware validation is documented as complete.
