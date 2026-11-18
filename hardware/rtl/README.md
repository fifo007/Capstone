# RTL modules

## `pulse_counter.v`

This synthesizable, board-independent pulse-window counter synchronizes an asynchronous input through two registers, detects rising edges, counts them, and publishes a stable snapshot at each measurement-window boundary. Reset is synchronous and active-high. The counter logic is unchanged by the PYNQ-Z2 wrapper work.

| Port | Direction | Meaning |
|---|---|---|
| `clk` | input | Destination logic clock. |
| `reset` | input | Synchronous, active-high reset. |
| `pulse_in_async` | input | Asynchronous pulse input; pulses must be long enough to be sampled reliably at `clk`. |
| `snapshot_count` | output | Stable count from the most recently completed window. |
| `snapshot_valid` | output | One-clock strobe when a new snapshot is published. |

Parameters: `WINDOW_CYCLES` (default 100,000 clock cycles) and `COUNTER_WIDTH` (default 32). At 100 MHz, the default window is 1 ms; that duration is valid only if the configured clock is actually 100 MHz. A boundary-detected pulse belongs to the window being closed. The counter wraps modulo its configured count width if that width is exceeded.

## `pynq_z2_pulse_wrapper.v`

This synthesizable thin wrapper maps `fclk_clk0`, synchronized active-high `reset`, and an intentionally unassigned `pulse_in_gpio_async` port to the existing counter, then exposes `snapshot_count` and `snapshot_valid`. It does not instantiate the PS or Xilinx IP, assign physical pins, connect the LM331, or add AXI.

For PYNQ-Z2 board/project setup and proposed clock/reset wiring, see [`../vivado/README.md`](../vivado/README.md). For simulation instructions/status, see [`../testbench/README.md`](../testbench/README.md) and [`../simulation/README.md`](../simulation/README.md).
