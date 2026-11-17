# Hardware foundation

This directory contains the isolated pulse-counter RTL, its XSim testbench and an unconnected PYNQ-Z2 integration wrapper. It does not include board-specific constraints, an AXI interface, a checked-in Vivado project, or deployment scripts.

## RTL module

`rtl/pulse_counter.v` defines `pulse_counter`.

Inputs:

- `clk`: destination logic clock.
- `reset`: synchronous, active-high reset.
- `pulse_in_async`: external asynchronous pulse signal. It passes through a two-flop synchronizer before edge detection. Pulses must remain high long enough to be sampled reliably by `clk`; the required pulse width depends on the eventual clock and input circuit.

Parameters:

- `WINDOW_CYCLES`: number of rising edges of `clk` in one measurement window (default 100,000). This is a cycle count, not a promised time interval. Set it from a verified clock period and selected measurement duration.
- `COUNTER_WIDTH`: width of the pulse counter and snapshot (default 32 bits).

Use `WINDOW_CYCLES >= 1` and a value representable by the 32-bit window-cycle counter; use `COUNTER_WIDTH >= 1`.

Outputs:

- `snapshot_count`: count for the most recently completed window. A pulse edge detected on the window's final clock edge is included in that window.
- `snapshot_valid`: one-clock-cycle strobe when `snapshot_count` is updated.

The design synchronizes and counts rising edges. It does not capture timestamps, measure individual pulse periods, perform analog conversion, or implement the neural model. The counter wraps modulo its configured width if the count exceeds that width.

`rtl/pynq_z2_pulse_wrapper.v` is a thin wrapper around this module. It exposes `fclk_clk0`, synchronous active-high `reset`, an unassigned asynchronous pulse input, and the captured count/strobe outputs. The wrapper does not alter the counter logic or instantiate the PS. See [`vivado/README.md`](vivado/README.md) for the PYNQ-Z2 project setup guide, board-file path, proposed 100 MHz FCLK0 configuration and reset wiring.

## Testbench

`testbench/pulse_counter_tb.v` uses a short 32-cycle window and checks reset behavior, a zero-pulse window, multiple pulses, an edge detected on a window boundary, an edge detected just after a boundary, consecutive windows, and the one-cycle `snapshot_valid` pulse. A failed check calls `$fatal`.

The testbench and RTL use Verilog/SystemVerilog constructs supported by Vivado XSim. No third-party HDL libraries are required.

### Vivado XSim

Run these commands from the project root in a Vivado command environment:

```sh
xvlog hardware/rtl/pulse_counter.v hardware/testbench/pulse_counter_tb.v
xelab pulse_counter_tb -s pulse_counter_tb_sim
xsim pulse_counter_tb_sim -runall
```

Vivado 2024.1 is installed at `C:\Xilinx\Vivado\2024.1`. The saved XSim logs show successful `xvlog`, `xelab`, and `xsim` execution; the testbench reported `PASS: pulse_counter_tb`. See `simulation/README.md` for the runner and logs. The new wrapper has not been added to the existing self-checking testbench.

## Hardware integration status

The proposed PS `FCLK_CLK0` frequency is 100 MHz; the guide requires confirming it after applying the official PYNQ-Z2 preset. No package pin or LM331 connection is defined. Verify electrical levels, output topology, pulse timing, and an approved board signal before adding constraints or connecting hardware. AXI and board programming remain out of scope. This is not hardware validation.
