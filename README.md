# Fly Brain ADC

This project explores a fly-inspired event-processing path for a 6-bit ADC prototype. The intended eventual signal chain is an external analog voltage-to-frequency circuit, programmable-logic pulse capture, event processing, and a 6-bit result. The board, circuit, clock, electrical interface, and pin assignment still require verification.

## Project areas

- `biowire/` contains the existing BioWire model, notebooks, dependencies, and experiment artifacts. These remain the historical baseline and are not modified by the hardware foundation work.
- `hardware/` contains the parameterized Verilog pulse counter, its self-checking testbench, and a thin PYNQ-Z2 integration wrapper. The saved Vivado 2024.1 XSim run passed the counter testbench. See `hardware/vivado/README.md` for board-file and PS clock/reset setup. No physical pin assignment, LM331 connection, AXI interface, deployment, or hardware validation is included.
- `software/event_model/` is reserved for a future event-driven model. It currently contains documentation only; no code here or in the existing BioWire project currently processes timestamped hardware pulses.
- `docs/codex_audit.md` records the repository reconnaissance and checks made on saved historical outputs.
- `docs/PROJECT_ARCHITECTURE.md` documents the intended end-to-end architecture, actual repository map, status, and open decisions.
- `docs/CAMPUS_HARDWARE_CHECKLIST.md` is the practical board/lab visit and electrical-safety checklist. `docs/HARDWARE_TEST_LOG.md` and `docs/ANALOG_CALIBRATION_LOG.md` are blank measurement templates.

## Results and status

**Saved historical results:** `biowire/EXP56B_EXP49_decoder.csv` is the current corrected EXP-56B reference. Its saved rows were inspected and its summary metrics reproduced from the CSV; this was not a new experiment or a hardware result.

**New implementation:** the pulse counter RTL and testbench were created and the testbench has passed in Vivado XSim. The PYNQ-Z2 wrapper and Vivado setup guide are new implementation/documentation. The existing BioWire model has not been rewritten and does not process timestamped hardware pulses.

**Planned hardware validation:** install/verify the official PYNQ-Z2 board files, create and validate the PS block design, then verify the pulse electrical levels/topology and select a suitable pin before adding constraints or connecting hardware. No hardware validation has occurred. No AXI interface, board constraints, or deployment flow is included yet.

## Pulse counter

See [`hardware/README.md`](hardware/README.md) for the interface, counter behavior, limitations, and exact test commands. Its measurement window is configured as a number of `clk` cycles; choose the value from a verified clock and desired interval when integrating the design.

## Event model

See [`software/event_model/README.md`](software/event_model/README.md). This is a planned isolated area, not an implemented model.
