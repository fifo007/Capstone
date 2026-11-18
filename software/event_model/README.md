# Future event-driven model (not implemented)

This directory is reserved for the software model intended to consume data from the future FPGA pulse-capture path. It currently contains documentation only: there is no Python module, dependency file, executable command, trained decoder or inference workflow here. Do not try to run this directory as a program.

## Intended role

The planned flow is ARM/PYNQ Python reads a measurement from PL, converts pulse counts/rates with a measured voltage-to-frequency calibration, runs a Fly-inspired event-based decoder, and produces a 6-bit result. The current PL counter only emits a count snapshot and one-cycle valid strobe. It does not timestamp each pulse, and no AXI/other PS-visible data path is implemented, so the model cannot receive hardware data yet.

The existing BioWire notebook and corrected EXP-56B decoder are voltage-derived research and historical software results. They may inform future model design, but neither is an implemented timestamped-pulse model. Keep future source, tests, dependencies and outputs isolated here rather than rewriting the BioWire notebook or saved experiments.

## Decisions required before implementation

1. Specify the PS/PL interface and data contract (for example, count plus window duration, rate estimate, or timestamps); no choice is implemented.
2. Characterize the LM331 voltage/frequency relation and electrical interface using actual measurements. Do not treat a synthetic mapping as calibration.
3. Define whether the output should represent average window voltage or a time-resolved value, plus latency and update-rate requirements.
4. Select a runtime/dependency set compatible with the actual ARM/PYNQ image and decide how the 6-bit output is delivered.
5. Create synthetic unit tests first, clearly label their assumptions, then compare with measured calibration and hardware observations when available.

See the root [project architecture](../../docs/PROJECT_ARCHITECTURE.md), [hardware README](../../hardware/README.md) and [hardware visit checklist](../../docs/CAMPUS_HARDWARE_CHECKLIST.md) for current system boundaries. There is no setup or run command until implementation and dependencies exist.
