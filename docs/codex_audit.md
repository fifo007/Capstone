# Codex project audit

**Date:** 2026-11-16  
**Scope:** Read-only repository reconnaissance for Fly Brain ADC Task 0. No notebook was executed and no existing project file was changed.

## Repository contents

The project root contains `biowire/`, the top-level `biowire_v1_.ipynb`, `adc_results.xlsx`, `adc_test.py`, `baseline_adc.py`, `fly_adc.py`, `simulation.py`, `lut.py`, and `Fly_Brain_ADC_EXP53_EXP54_artifacts.zip`, plus `__pycache__/` and `.git/`.

`biowire/` contains a second `biowire_v1_.ipynb`, project README and dependency files, saved EXP-53/54/55/56 CSVs and plots, FlyWire connectome CSVs, and `fly_adc_lut.mem`. Its notebook has 176 cells; the root notebook has 157. Both record Python 3.11.5 metadata. The `biowire/README.md` describes a BioWire/Brian2 project and its simulation workflow. `requirements.txt` and `environment.yml` specify NumPy, pandas, matplotlib, networkx, SciPy, and Brian2 (Python 3.10 in the Conda file).

The available ambient interpreter is Python 3.11.5. NumPy, pandas, matplotlib, networkx, SciPy, Brian2, Jupyter, and scikit-learn are importable in it. No project-local `.venv` or `env` directory was found. No root README or project-level dependency manifest was found.

Git metadata exists, but `git ls-files` returned no tracked files and `git status --short` showed the project contents as untracked. Treat the current files as user data and preserve them.

## Saved experiment artifacts

The following relevant files exist under `biowire/`:

- `EXP56A_transfer_characterization.csv` — 101 data rows plus header.
- `EXP56B_EXP49_decoder.csv` — 101 data rows plus header.
- `EXP56B_code_transitions.csv` — 23 data rows plus header.
- `EXP56B_transfer_curve.csv` — 101 data rows plus header.

The saved corrected EXP-56B CSV was read without rerunning the experiment. Its values yield 101 valid rows, voltage MAE 2.83247 mV, RMSE 4.71257 mV, 55 unique 6-bit codes spanning 0–62, and nondecreasing decoded voltage and code columns. These are checks of the saved file only; they do not verify a new model run or hardware behavior. EXP-56A is a saved transfer-characterization artifact; its filename and row count do not establish that the data came from physical hardware.

The `biowire/` notebook includes source/output cells for EXP-49, EXP-51–56B; the corrected EXP-56B cell states that it reuses the EXP-49 200 ms decoder without fitting on EXP-56A. The notebook was inspected as JSON only and was not executed. The archive contains a research-log DOCX and EXP-53 artifacts.

## Hardware and integration state

No existing hardware, software, datasets, results, or docs implementation folders were found at the project root. No Verilog (`.v`), XDC, or Vivado project (`.xpr`) files were found. The board, its image, the LM331 circuit, signal levels, and pin assignment have not been verified in this inspection. The environment lookup did not find Icarus Verilog or Vivado on PATH.

## Inspection commands

- `Get-ChildItem -Force`
- `rg --files` with README, Python, notebook, CSV, workbook, and hardware-file filters
- `git status --short` and `git ls-files`
- Read `biowire/README.md`, `biowire/requirements.txt`, and `biowire/environment.yml`
- Python JSON/CSV inspection of notebook metadata/cell source and saved EXP-56 outputs
- `tar -tf Fly_Brain_ADC_EXP53_EXP54_artifacts.zip`
- Python interpreter/package availability inspection

No Python script, notebook, simulator, or hardware flow was run.

## Suggested next step

After project-owner review, create only the missing isolated hardware directories and documentation, then add a parameterized pulse counter and self-checking testbench as new files. First confirm an available Verilog simulator or document the Vivado xsim command. Keep any software replay/event-model work separate from the historical BioWire files and saved results.
