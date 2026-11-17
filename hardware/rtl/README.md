# RTL

`pulse_counter.v` is the synthesizable pulse-window counter module. It synchronizes an asynchronous input, detects a rising edge, accumulates a configurable-width count, and publishes a stable snapshot at each configurable window boundary. Its logic is unchanged.

`pynq_z2_pulse_wrapper.v` is a thin, synthesizable integration wrapper. It maps `fclk_clk0`, synchronized active-high `reset`, and an intentionally unassigned `pulse_in_gpio_async` logical port onto the existing counter, and exposes the captured count and valid strobe. It does not instantiate the PS or Xilinx IP, assign physical pins, connect the LM331, or add AXI.

The window is specified in destination clock cycles with `WINDOW_CYCLES`; `COUNTER_WIDTH` controls the count and snapshot width. The counter has no board pin or clock-period assumption. For PYNQ-Z2 project integration, clock/reset configuration, and board-file setup, see [`../vivado/README.md`](../vivado/README.md). See [`../README.md`](../README.md) for counter semantics and the XSim test status.
