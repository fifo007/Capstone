# Fly Brain ADC project architecture

**Status:** architecture target, not a claim that the complete chain exists or has been measured. The analog range, converter behavior, board revision, pin-level interface, PS-to-PL software interface, event representation and final output method still need validation or design.

## Intended signal path

```text
Potentiometer (intended 0–1 V)
        │ analog voltage
        ▼
LM331 voltage-to-frequency circuit
        │ pulse train; electrical interface not yet approved
        ▼
PYNQ-Z2 programmable logic (PL): synchronise → count per window → snapshot
        │ count/window data; future PS interface not implemented
        ▼
Zynq ARM Processing System (PS): PYNQ Linux + Python application
        │ calibrated event/count features
        ▼
Future Fly-inspired event-driven model
        │ 6-bit code
        ▼
Future digital output interface (method and connector not selected)
```

The `0–1 V` potentiometer span is the intended experiment input range, not a claim about a verified circuit or a board-safe signal. No LM331 output is to be connected to the PYNQ-Z2 until its output stage, pull-up, voltage and timing have been measured and a suitable interface is reviewed.

## Subsystems and data movement

| Subsystem | Purpose and intended data | Current state |
|---|---|---|
| Potentiometer | Set the analog test voltage over the intended range. | Planned bench source; no new measurement is recorded here. |
| LM331 voltage-to-frequency converter | Encode the analog input as a pulse frequency. Calibration should relate measured voltage and pulse frequency. | Circuit and output topology have not been verified. |
| PYNQ-Z2 PL | Synchronize an asynchronous pulse input to a PL clock, count rising edges in a configurable window, and expose a stable count snapshot plus a valid strobe. | `pulse_counter.v` exists; its self-checking testbench passed in XSim. A thin wrapper exists and compiled with `xvlog`. No board integration or physical test has occurred. |
| Zynq ARM PS | Run Linux/PYNQ Python and, in the future, read measurement data from the PL. | Board boot and PYNQ image/version are not yet confirmed. No AXI/data interface connects the count to software yet. |
| Fly-inspired event model | Consume measured pulse-derived features and produce a 6-bit result. | Future isolated area only. No timestamped hardware-pulse processing exists. |
| 6-bit output | Present the model's output to a selected downstream system. | Output electrical/protocol interface is undecided and unimplemented. |

The current counter measures the number of synchronized rising edges per window; it does **not** timestamp each pulse, measure each period, or deliver data to software. For a future software model, a likely data unit is a count plus its window duration (which implies an average rate), but the interface and model input contract must be agreed before implementation. A future AXI memory-mapped or streaming link is a design decision, not an existing feature.

## PL, PS and development tools

- **Programmable Logic (PL):** FPGA fabric in the Zynq device. The counter and its synchronizer are intended to run here, clocked by PS-generated `FCLK_CLK0`. A proposed configuration is 100 MHz; confirm the actual frequency in the configured processing system before using that value in timing calculations. At 100 MHz, the existing default 100,000-cycle window is 1 ms.
- **Processing System (PS):** hard ARM Cortex-A9 subsystem that can run PYNQ Linux. It is distinct from the PL. A PL snapshot is not automatically visible to a Python process; an explicit PS/PL interface and software access path are still needed.
- **Vivado:** used to create the board project/block design, configure the Zynq PS, integrate RTL, synthesize and implement the PL, and produce a configuration image. The exact board preset and actual clock properties must be confirmed in the lab.
- **Vivado Simulator (XSim):** runs RTL testbenches before hardware work. It has passed the existing counter testbench; the new wrapper has only been parsed/compiled with `xvlog`, not simulated in a wrapper testbench.
- **PYNQ Python:** intended to run on the ARM/Linux side to configure or interact with a future PL design and execute the future event model. It cannot currently read the counter because no AXI or other PS-facing data path exists.

The board reference manual identifies the PYNQ-Z2 Zynq device as `XC7Z020-1CLG400C` and describes a 50 MHz `PS_CLK` reference. `PS_CLK` is not the PL clock connection in this design; use the PS `FCLK_CLK0` output for the counter. The proposed 100 MHz configuration is documented in the PYNQ-Z2 PS design configuration; verify it after applying the official preset/automation. See the [PYNQ-Z2 Reference Manual](https://www.mouser.com/pdfDocs/pynqz2_user_manual_v1_0.pdf) and [PYNQ board-settings guide](https://pynq.readthedocs.io/en/latest/overlay_design_methodology/board_settings.html).

## Relationship to existing BioWire research

The existing BioWire notebook, saved decoder and EXP-56B data are voltage-derived software research and historical results. They can inform hypotheses, representations and later comparison of a Fly-inspired model. They do not demonstrate a model that consumes timestamped FPGA pulses, and they are not rewritten by this project stage. Before reusing a decoder, define how hardware counts/frequency map to voltage and collect/approve the calibration data; label any synthetic data and assumptions explicitly.

## Repository map

| Path | What is actually present |
|---|---|
| `README.md` | Project overview and current status. |
| `adc_test.py`, `baseline_adc.py`, `fly_adc.py`, `simulation.py`, `lut.py` | Existing root-level Python scripts; preserved and not reviewed as part of the new RTL. |
| `adc_results.xlsx`, `biowire_v1_.ipynb`, `Fly_Brain_ADC_EXP53_EXP54_artifacts.zip` | Existing workbook, notebook and archive; preserved. |
| `biowire/` | Existing BioWire notebooks, model/dependency documentation, saved experiment CSVs, plots, FlyWire CSV data and LUT memory file. `EXP56B_EXP49_decoder.csv` remains the corrected historical EXP-56B reference. |
| `hardware/rtl/pulse_counter.v` | Existing new-stage pulse-window counter RTL; logic was not changed for the wrapper. |
| `hardware/rtl/pynq_z2_pulse_wrapper.v` | Thin wrapper around the counter; no PS IP, AXI, package pin, or LM331 electrical connection. |
| `hardware/testbench/pulse_counter_tb.v` | Self-checking counter testbench for reset, zero/multiple pulses, boundary cases and valid-strobe behavior. |
| `hardware/simulation/` | Vivado XSim batch runner, saved pass logs, generated XSim files and older diagnostic logs. |
| `hardware/vivado/README.md` | Vivado setup guidance for the PYNQ-Z2 board, PS clock/reset and wrapper integration. |
| `software/event_model/README.md` | Documentation-only placeholder for a future event model; no implementation exists there. |
| `docs/codex_audit.md` | Earlier repository reconnaissance record. It is historical and predates the hardware implementation. |
| `docs/PROJECT_ARCHITECTURE.md` | This architecture and status document. |
| `docs/CAMPUS_HARDWARE_CHECKLIST.md` | Lab visit checklist. |
| `docs/HARDWARE_TEST_LOG.md` | Blank hardware test record. |
| `docs/ANALOG_CALIBRATION_LOG.md` | Blank potentiometer/LM331 calibration record. |

The repository also contains Python cache material and Git metadata; neither is part of the proposed hardware path.

## Status snapshot

| Area | Status |
|---|---|
| Saved historical experiments | Existing BioWire files preserved; corrected EXP-56B CSV is the reference. No experiment rerun for this documentation. |
| Counter RTL simulation | Existing `pulse_counter_tb` passed on Vivado 2024.1 XSim according to saved `xsim_console.log`. |
| Wrapper | `xvlog` compilation passed; wrapper testbench/simulation not performed. |
| PYNQ-Z2 board files | Earlier inspection found no PYNQ/Z2-named definition in the checked Vivado 2024.1 board directories; confirm/install official files in the lab environment. |
| Board boot / PYNQ image | Not verified. |
| Synthesis / implementation / bitstream | Not performed. |
| Physical pulse capture / LM331 | Not performed; no signal connection authorized by this design note. |
| AXI / software event model / six-bit output | Planned, not implemented. |

## Open decisions and blockers

1. What exact PYNQ-Z2 model, board revision and physical connector configuration are on the lab bench?
2. Are the official matching PYNQ-Z2 board files installed in the Vivado version used in the lab, and does the PYNQ-Z2 preset configure the expected PS interfaces?
3. What `FCLK_CLK0` rate is actually configured after board automation? Is the proposed 100 MHz accepted for the test?
4. What are the LM331 circuit's output stage, pull-up rail/value, high/low voltages, pulse width/duty range, frequency range and shared-ground arrangement under load?
5. Which board connector/bank can safely receive the verified signal, and what constraints and interface conditioning does it require? No pin is selected here.
6. How will the PL snapshot reach ARM software (AXI-Lite register, stream/FIFO, or another reviewed route)?
7. Should the model consume counts per fixed window, estimated frequency, or timestamped pulse events? What latency and time resolution are required?
8. How will the final 6-bit value be presented, and what hardware/electrical protocol does that downstream device require?
9. What calibration method, voltage sweep, repeat count and validation split should be used before comparing hardware-driven results with the saved BioWire work?

No board-specific pin assignment, AXI implementation, analog interface design, or hardware validation is provided in this document.
