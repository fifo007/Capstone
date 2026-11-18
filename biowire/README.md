# BioWire connectome model and saved experiments

BioWire is the repository's existing Brian2 spiking-network research track. Its notebook builds a Drosophila optic-lobe/left-medulla (ME_L) network from FlyWire cell-type and synaptic-connection tables, simulates circuit responses, and compares model outputs with selected biological/electrophysiological references. It is a research model and historical software work; it is not the future hardware event model and does not currently process timestamped FPGA pulses.

## Contents

- `biowire_v1_.ipynb` — primary notebook, with executed/saved outputs and the staged connectome/network workflow.
- `environment.yml` and `requirements.txt` — Conda and pip dependency specifications.
- `consolidated_cell_types.csv.gz` — FlyWire cell-type table; present in this checkout as a regular Git file.
- `connections_princeton_no_threshold.csv.gz` — large FlyWire synapse table tracked by Git LFS.
- `EXP53_*`, `EXP54_*`, `EXP55_*`, `EXP56*` — saved experiment inputs, results and figures. These are historical outputs; opening the notebook does not rerun them.
- `fly_adc_lut.mem` — saved 101-entry, two-digit hexadecimal code table produced from the corrected EXP-56B reference. The generator `../lut.py` is machine-path-specific and overwrites this file if run.
- `.ipynb_checkpoints/` and any extra notebook figures — editor/generated artifacts, not separate source workflows.

The repository root also has an older `biowire_v1_.ipynb` snapshot. Use this directory's notebook for the documented BioWire workflow.

## Data requirements and Git LFS

The notebook's initial data-loading cells look for both files in the notebook's current working directory and require columns including:

- Cell types: `root_id`, `primary_type`.
- Connections: `pre_root_id`, `post_root_id`, `syn_count`, `neuropil`.

The maintained notebook cell can generate a synthetic mock connectome when either table is absent. Mock mode is for an offline demonstration and must not be described as a real FlyWire result. Some later analysis/audit cells assume real data and may not work in mock mode.

### Clone and fetch the tracked large table (PowerShell)

Install Git LFS once, then clone/fetch:

```powershell
git lfs install
git clone https://github.com/fifo007/Capstone.git
Set-Location .\Capstone
git lfs pull
git lfs ls-files
Get-Item .\biowire\connections_princeton_no_threshold.csv.gz, .\biowire\consolidated_cell_types.csv.gz | Select-Object Name,Length
```

If the repository is already cloned, run `git lfs install` and `git lfs pull` from its root. The connections table is the LFS object. If LFS access is unavailable, download the correctly versioned tables from [FlyWire downloads](https://codex.flywire.ai/api/download) and put them beside this README/notebook as `biowire/consolidated_cell_types.csv.gz` and `biowire/connections_princeton_no_threshold.csv.gz`. Keep the compressed filenames unchanged and do not commit replacement datasets without reviewing provenance/licensing/size.

Linux equivalent:

```bash
git lfs install
git lfs pull
ls -lh biowire/connections_princeton_no_threshold.csv.gz biowire/consolidated_cell_types.csv.gz
```

## Environment setup

### Conda (recommended for this notebook)

From the repository root:

```powershell
conda env create -f .\biowire\environment.yml
conda activate biowire
python -m pip install jupyter
```

The checked-in environment file includes Python 3.10, NumPy, pandas, Matplotlib, NetworkX, SciPy and Brian2. It does not list Jupyter, so install it in the environment as shown above. If the environment already exists, use `conda env update -f .\biowire\environment.yml --prune` only if you intend to update that environment; otherwise activate it and install Jupyter.

### pip/venv alternative

From the repository root:

```powershell
py -3.10 -m venv .\biowire\.venv
.\biowire\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r .\biowire\requirements.txt
python -m pip install jupyter
```

The maintained requirements file lists NumPy, pandas, Matplotlib, NetworkX, SciPy and Brian2. Use Python 3.10 or a compatible later version; the Conda environment explicitly uses Python 3.10.

## Launch and run the notebook

In PowerShell, with the `biowire` environment activated:

```powershell
Set-Location .\biowire
jupyter lab .\biowire_v1_.ipynb
```

Or use `jupyter notebook .\biowire_v1_.ipynb`. Keep `biowire/` as the notebook working directory: the initial pipeline uses relative CSV names and saves figures/results relative to the current directory. In Jupyter, restart the kernel and execute cells in notebook order when intentionally reproducing the pipeline. The full-connectome simulation is computationally intensive and can require substantial memory/time.

**Portability and preservation notes:** later data-audit/experiment cells contain absolute paths into the original author's `C:\Users\sagni\OneDrive\Documents\capstone\biowire` location. A clone in a different folder may fail in those cells. Notebook cells also write result CSVs and figures with names matching saved artifacts, so running them can replace files. Review the cell paths and work on a disposable copy before executing the full notebook; do not use Run All as a way to inspect the saved results.

The initial notebook loader's mock fallback does not mean the entire notebook can reproduce every saved experiment without the real data. Confirm the notebook's printed mode and table shapes before interpreting any output.

## Notebook workflow and saved experiment outputs

The notebook's main documented sequence is: load connectome → extract ME_L → classify excitatory/inhibitory types and quantize weights → inspect topology/weight plots → configure conductance-based LIF dynamics → run core 8-type and larger 20/100-type circuit simulations → stimulus/directional tuning analysis → electrophysiology comparison → randomized-topology negative controls. Saved baseline figures include topology, signed weights, voltage traces, stimulus results, electrophysiology comparison and negative-control plots.

Later notebook work produced the following files in this directory. These are already-saved artifacts and should not be regenerated just to read them:

| Experiment | Purpose | Saved outputs currently present |
|---|---|---|
| EXP-53 | Fly-inspired ADC processing of a real-video-derived motion/voltage signal; includes a decoder correction using the frozen EXP-33 configuration. | `EXP53_real_video_motion_signal.csv`, `EXP53_real_video_fly_adc_results.csv`, `EXP53_real_video_fly_adc_reconstruction.png`, `EXP53_real_video_fly_adc_error.png`, `EXP53_real_video_fly_adc_transfer.png`, `EXP53_real_video_fly_adc_code_occupancy.png`. |
| EXP-54 | Saved real-video Fly-vs-SNN comparison. | `EXP54_real_video_fly_vs_snn.csv`, `EXP54_real_video_code_occupancy.png`, `EXP54_real_video_error_comparison.png`, `EXP54_real_video_transfer_comparison.png`, and `EXP54_real_video_fly_vs_snn.png`. |
| EXP-55 | Noise robustness/code agreement analysis. | `EXP55_noise_robustness_samples.csv`, `EXP55_noise_robustness_summary.csv`, and the `EXP55_noise_*.png` figures for agreement, coverage, MAE, RMSE and SNR. |
| EXP-56A | Saved transfer characterization. | `EXP56A_transfer_characterization.csv` and `EXP56A_transfer_characterization.png`. |
| EXP-56B | Code transitions and transfer-curve work; the corrected decoder CSV remains the historical reference. | `EXP56B_code_transitions.csv`, `EXP56B_transfer_curve.csv`, `EXP56B_EXP49_decoder.csv`, and `fly_adc_lut.mem`. |

The values in these files are saved research results, not proof of physical ADC measurements. Do not rerun experiments or overwrite the corrected `EXP56B_EXP49_decoder.csv` when only inspecting the repository. For the project-wide status and the relationship to future pulse-driven work, see [Project architecture](../docs/PROJECT_ARCHITECTURE.md) and the root [README](../README.md).
