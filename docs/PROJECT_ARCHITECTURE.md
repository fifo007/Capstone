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
PYNQ-Z2 programmable logic (PL): synchronise → timestamp/FIFO (development path)
        │ AXI-Lite register stream (RTL present, not integrated or validated)
        ▼
Zynq ARM Processing System (PS): PYNQ Linux + Python application
        │ timestamped event windows (software pipeline implemented; hardware interface pending)
        ▼
Fly-inspired event-driven model (hardware-free simulation runs; board input pending)
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
| PYNQ-Z2 PL | Synchronize/count pulses per window in the original counter; a separate module captures pulse timestamps into an AXI-Lite FIFO. | Counter and FIFO testbenches pass in Vivado 2024.1 XSim. The wrapper compiled with `xvlog`, but has no wrapper simulation testbench. The FIFO and wrapper are not integrated into a Vivado block design, synthesized, or physically tested. |
| Zynq ARM PS | Run Linux/PYNQ Python and read PL event records through a defined memory-mapped interface. | A Python MMIO reader is present, but no integrated overlay/bitstream or board boot/version check is available. It has not been validated against physical PL hardware. |
| Fly-inspired event model | Consume timestamped pulse windows through a ME_L network adapter and produce a 6-bit result. | A hardware-free synthetic pipeline is implemented and runs against the saved FlyWire tables. Its 26 software tests pass. A fresh 64-sample synthetic sweep reported 0.125 LSB held-out MAE. The input boundary is L1 because the ME_L source network has no R1-6 node. No measured LM331 calibration or hardware-driven result exists. |
| 6-bit output | Present the model's output to a selected downstream system. | Output electrical/protocol interface is undecided and unimplemented. |

The original `pulse_counter` measures synchronized rising edges per window; it does **not** timestamp each pulse. The separate `pulse_event_fifo_axi` module implements a timestamp FIFO and AXI-Lite register interface, and its self-checking XSim testbench passes. It is not connected to `pynq_z2_pulse_wrapper` or a PS block design, and the Python reader has not been validated on a board. Treat it as simulation-verified development RTL, not a usable physical hardware interface.

## PL, PS and development tools

- **Programmable Logic (PL):** FPGA fabric in the Zynq device. The counter and its synchronizer are intended to run here, clocked by PS-generated `FCLK_CLK0`. A proposed configuration is 100 MHz; confirm the actual frequency in the configured processing system before using that value in timing calculations. At 100 MHz, the existing default 100,000-cycle window is 1 ms.
- **Processing System (PS):** hard ARM Cortex-A9 subsystem that can run PYNQ Linux. It is distinct from the PL. A PL snapshot is not automatically visible to a Python process; an explicit PS/PL interface and software access path are still needed.
- **Vivado:** used to create the board project/block design, configure the Zynq PS, integrate RTL, synthesize and implement the PL, and produce a configuration image. The exact board preset and actual clock properties must be confirmed in the lab.
- **Vivado Simulator (XSim):** runs RTL testbenches before hardware work. It has passed the existing counter testbench; the new wrapper has only been parsed/compiled with `xvlog`, not simulated in a wrapper testbench.
- **PYNQ Python:** intended to run on the ARM/Linux side. An isolated MMIO reader exists for the unintegrated timestamp FIFO, but the current counter wrapper is not software-readable and there is no verified overlay/bitstream.

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
| `software/event_model/` | Implemented hardware-free event-window CSV types, ME_L connectome builder, Brian2 network adapter, neural-feature decoder, calibration/inference CLI, and PYNQ MMIO reader. Hardware-to-model integration and a final physical 6-bit output interface remain unvalidated. |
| `hardware/rtl/pulse_event_fifo_axi.v` | Separate timestamp FIFO/AXI-Lite development module; not integrated with the pulse-counter wrapper and not simulation-verified. |
| `hardware/testbench/pulse_event_fifo_axi_tb.v` | Self-checking testbench for FIFO register access, channel ordering, timestamp order, overflow, draining and reset; passes Vivado 2024.1 XSim. |
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
| Timestamp FIFO / AXI-Lite module | RTL/testbench simulation passes in XSim; not integrated in a PS block design, synthesized, or physically verified. |
| Software event model / MMIO reader | Hardware-free synthetic demo, labeled-window calibration path, stored-window inference path, compact connectome bundle, and MMIO reader are implemented. All 26 software tests pass, and the full synthetic demo and synthetic-only calibration CLI passed again during this work. The MMIO reader has not been tested against a real overlay. |
| Six-bit output | Not implemented; electrical/protocol interface undecided. |

## Open decisions and blockers

1. What exact PYNQ-Z2 model, board revision and physical connector configuration are on the lab bench?
2. Are the official matching PYNQ-Z2 board files installed in the Vivado version used in the lab, and does the PYNQ-Z2 preset configure the expected PS interfaces?
3. What `FCLK_CLK0` rate is actually configured after board automation? Is the proposed 100 MHz accepted for the test?
4. What are the LM331 circuit's output stage, pull-up rail/value, high/low voltages, pulse width/duty range, frequency range and shared-ground arrangement under load?
5. Which board connector/bank can safely receive the verified signal, and what constraints and interface conditioning does it require? No pin is selected here.
6. How will the PL snapshot reach ARM software (AXI-Lite register, stream/FIFO, or another reviewed route)?
7. Does the model's 0.5 ms integration step resolve the measured LM331 event rates, and what latency/time resolution does the application require?
8. How will the final 6-bit value be presented, and what hardware/electrical protocol does that downstream device require?
9. What calibration method, voltage sweep, repeat count and validation split should be used before comparing hardware-driven results with the saved BioWire work?

No board-specific pin assignment, integrated AXI block design, analog interface design, or hardware validation is provided in this document. The separate AXI-Lite FIFO RTL and testbench pass simulation, but the design is not integrated with a PS block design or approved for deployment.

## Ordered next steps

1. **Identify and boot the lab board.** Record the exact PYNQ-Z2 model/revision, inspect the SD card without modifying it, power with the identified supply, and record boot/PYNQ version. This depends on the physical board and image being available.
2. **Confirm Vivado board support and start the project.** Install/select only the official matching PYNQ-Z2 board files and confirm `xc7z020clg400-1`. This depends on access to the Vivado installation used in the lab and the board's identity.
3. **Configure PS clock and reset.** Apply the PYNQ-Z2 PS preset, enable FCLK_CLK0, record its actual configured frequency, and wire the synchronized reset. The proposed 100 MHz must be confirmed in Vivado.
4. **Integrate the pulse-counter wrapper.** Add the existing counter and wrapper without changing counter logic. At this stage the wrapper outputs are not readable by PYNQ software; keep pins unconstrained until a safe interface and observation method are selected.
5. **Integrate the PS access path.** The timestamp FIFO RTL and its XSim testbench now pass simulation. Add the module to a PYNQ-Z2 PS block design, assign its AXI-Lite address, generate the overlay, and verify the Python reader against that overlay. This depends on selecting the official PYNQ-Z2 board support and confirming the PS preset and FCLK0 configuration in the target Vivado installation.
6. **Verify pulse capture with a known safe source.** First inspect the exact connector/bank and measure pulse levels, width, frequency, grounding and overshoot while disconnected from the board. This depends on scope/multimeter observations and reviewed constraints; no pins are selected in this repository.
7. **Characterize and integrate the LM331.** Measure output topology and voltage/frequency behavior over the potentiometer range, review an interface circuit, and only then plan a board connection. This depends on the actual LM331 schematic and bench measurements.
8. **Connect the event model.** Feed measured timestamped windows into the existing model, calibrate with labeled measurements, validate on held-out data, and decide how to expose the six-bit code. This depends on a verified PS/PL interface and measured/calibrated events.

The directory `software/event_model/` is already present. A board-specific constraints directory, integrated Vivado block-design project, and physical deployment artifacts have not been created; their contents depend on the board and interface checks above.
