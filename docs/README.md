# Project documents

This directory contains project-level references and lab records. These files explain architecture, status, planned checks, and observations; they are not executable programs.

## Start with these documents

1. [`PROJECT_ARCHITECTURE.md`](PROJECT_ARCHITECTURE.md) describes the intended signal path, current implementation boundaries, and open integration decisions.
2. [`CAMPUS_HARDWARE_CHECKLIST.md`](CAMPUS_HARDWARE_CHECKLIST.md) is a checklist for future bench work. Follow the hardware safety hold points before connecting external circuitry.
3. [`HARDWARE_TEST_LOG.md`](HARDWARE_TEST_LOG.md) records hardware work and outcomes. A planned test is not a completed test unless the log records its result.
4. [`ANALOG_CALIBRATION_LOG.md`](ANALOG_CALIBRATION_LOG.md) is the record for analog calibration observations and measurements.
5. [`codex_audit.md`](codex_audit.md) records a repository audit and is supplemental context, not a setup guide.

## What to run

There are no commands to execute from this directory. For Python programs, start at the repository [README](../README.md). For pulse-counter simulation, use the Vivado XSim runner documented in [`../hardware/simulation/README.md`](../hardware/simulation/README.md); it does not need the VFC circuit or board. For a future PYNQ-Z2 Vivado project, follow [`../hardware/vivado/README.md`](../hardware/vivado/README.md).

Keep saved measurements and historical experiment outputs intact. Record new lab observations in the appropriate log and distinguish measured results from simulation or plans.
