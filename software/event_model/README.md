# Event-driven model development area

This package is an isolated implementation area for turning pulse events into Fly-inspired model features. It does not replace the BioWire notebook or alter saved experiments. The code is currently a development foundation: no end-to-end hardware-to-model run, calibrated LM331 mapping, or verified 6-bit output exists.

## Files and role

| File | Purpose |
|---|---|
| `events.py` | `EventWindow` representation, event CSV serialization, and deterministic periodic event generator for explicitly synthetic inputs. Timestamps are offsets in FPGA clock ticks. |
| `connectome.py` | Rebuilds the ME_L type-level network from the repository's FlyWire cell-type and connection tables, using the BioWire notebook's type selection, quantization, and inhibitory row signs. |
| `network.py` | Brian2 adapter for injecting event trains into the selected network input and collecting readout features. It uses an explicit event-gain/configuration; those parameters are not physical calibration values. |
| `pynq_reader.py` | MMIO reader for the register map defined by `hardware/rtl/pulse_event_fifo_axi.v`. PYNQ is imported only when creating an MMIO object from a loaded overlay. |

The ME_L source network has no `R1-6` node. The current adapter therefore uses `L1` as its input boundary. This is a modeling choice and does not claim that L1 represents the complete photoreceptor pathway.

## Dependencies and data

The modules require Python 3.10+, NumPy, pandas, Brian2; `connectome.py` also reads the two BioWire CSV.GZ files, and `pynq_reader.py` needs the `pynq` package only on the target PYNQ system. There is not yet a dedicated requirements file, CLI, or supported end-to-end run command. Install/reuse the BioWire environment for host-side development, and confirm package compatibility against the actual PYNQ image before deployment.

From the repository root, first ensure Git LFS data is populated:

```powershell
git lfs pull
Get-Item .\biowire\connections_princeton_no_threshold.csv.gz, .\biowire\consolidated_cell_types.csv.gz
```

The event-window generator can create synthetic periodic event data, but it is not an LM331 model. Do not treat a chosen frequency, voltage label, or event-gain value as measured calibration.

## Hardware reader boundary

`PynqPulseEventReader` expects a loaded PYNQ overlay with an IP instance whose MMIO register map matches the in-progress FIFO RTL. Pass the verified FCLK0 tick rate explicitly. The reader rejects capture data when the FIFO overrun flag is set. The RTL and Python reader have not been validated together on a bitstream or board; the FIFO testbench's latest recorded XSim attempt failed during generated-C compilation. There are no pin assignments, safe LM331 interface, overlay, or deployment instructions at this stage.

See the [project architecture](../../docs/PROJECT_ARCHITECTURE.md), [hardware guide](../../hardware/README.md), and [campus hardware checklist](../../docs/CAMPUS_HARDWARE_CHECKLIST.md) for system status and safety boundaries.
