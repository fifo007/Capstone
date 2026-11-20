# FPGA pulse-counter foundation

This directory contains the synthesizable pulse-window counter, its self-checking testbench, and a thin PYNQ-Z2 wrapper. Separate timestamp-FIFO/AXI-Lite RTL and a passing XSim testbench are also present as development work; they are not integrated with the wrapper or a Zynq PS block design, and have no physical validation. There are no board pin constraints. The pulse input is not electrically verified; keep the LM331 disconnected until the interface is reviewed.

## Architecture and status

`pulse_counter` synchronizes an asynchronous input, detects rising edges, counts them over `WINDOW_CYCLES` PL clock cycles, and publishes a stable snapshot with a one-cycle `snapshot_valid` strobe. `pynq_z2_pulse_wrapper` exposes that module's clock, reset, pulse, and outputs for later Block Design integration.

| Status item | Current state |
|---|---|
| Counter RTL | Implemented; see [`rtl/README.md`](rtl/README.md). |
| Counter testbench | Implemented; reset, empty/multiple pulses, boundary behavior and snapshot strobe checks. |
| Vivado 2024.1 XSim | Latest saved self-checking testbench run passed. See [`simulation/README.md`](simulation/README.md). |
| PYNQ-Z2 wrapper | `xvlog` compiled it successfully; no wrapper testbench or wrapper simulation has been run. |
| Timestamp FIFO and AXI-Lite | Separate RTL/testbench passes Vivado 2024.1 XSim; it is not integrated into the wrapper/project or tested on a board. |
| Board project / synthesis / bitstream / physical test | Not performed. No hardware validation claim. |
| Integrated PS/software data path | Not implemented or verified. The separate FIFO module is development source only; neither it nor current counter snapshots are available to PYNQ Python through a verified overlay. |

## Build and run the testbench

Prerequisite: AMD/Xilinx Vivado with XSim installed. The batch runner defaults to `C:\Xilinx\Vivado\2024.1\settings64.bat` and may be invoked from the repository root in PowerShell:

```powershell
& .\hardware\simulation\run_xsim.bat
```

From Command Prompt, use:

```bat
hardware\simulation\run_xsim.bat
```

If Vivado is installed elsewhere, set the runner override to that installation's actual settings script before invoking it in PowerShell (replace the example path):

```powershell
$env:VIVADO_SETTINGS = 'C:\path\to\Vivado\version\settings64.bat'
& .\hardware\simulation\run_xsim.bat
```

The script uses `xvlog -sv`, `xelab`, then `xsim`; it stores logs/generated files under `hardware/simulation/` and returns an error if a stage fails or the testbench PASS marker is absent. Success prints `PASS: pulse_counter_tb` and the runner's final PASS line. A passing simulation verifies the testbench assertions for the counter only, not the wrapper or board behavior.

For ports, parameters and edge/window behavior see [`rtl/README.md`](rtl/README.md); test coverage and direct simulator commands are in [`testbench/README.md`](testbench/README.md); board/clock/reset setup is in [`vivado/README.md`](vivado/README.md).

## Integration boundary

The Vivado guide proposes using PS-generated `FCLK_CLK0`, with the actual rate confirmed after applying the PYNQ-Z2 board preset. The guide describes reset synchronization and adding the wrapper as a Block Design module reference. It does not select a physical connector/pin or add an XDC file. `snapshot_count` and `snapshot_valid` need a later approved observation/software interface before ARM software can consume them.

The pulse input can lose pulses that do not remain high long enough to be sampled by the PL clock. Determine safe voltage levels, output topology, pull-up, pulse width/frequency and ground/reference before connecting any external circuit. Do not connect the LM331 output directly based only on its part number.
