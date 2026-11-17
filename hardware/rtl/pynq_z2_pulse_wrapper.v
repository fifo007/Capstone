`timescale 1ns/1ps

// Thin, board-independent PL wrapper for integration into a PYNQ-Z2 Vivado
// block design. Connect fclk_clk0 to the Zynq PS FCLK_CLK0 output and connect
// reset to a synchronized, active-high reset (for example, proc_sys_reset's
// peripheral_reset). pulse_in_gpio_async is intentionally left as an
// unconstrained logical port until its electrical interface and board pin are
// verified. In particular, do not connect the LM331 output yet.
module pynq_z2_pulse_wrapper #(
    parameter integer WINDOW_CYCLES = 100000,
    parameter integer COUNTER_WIDTH = 32
) (
    input  wire                     fclk_clk0,
    input  wire                     reset,
    input  wire                     pulse_in_gpio_async,
    output wire [COUNTER_WIDTH-1:0] snapshot_count,
    output wire                     snapshot_valid
);

    pulse_counter #(
        .WINDOW_CYCLES (WINDOW_CYCLES),
        .COUNTER_WIDTH (COUNTER_WIDTH)
    ) pulse_counter_i (
        .clk             (fclk_clk0),
        .reset           (reset),
        .pulse_in_async  (pulse_in_gpio_async),
        .snapshot_count  (snapshot_count),
        .snapshot_valid  (snapshot_valid)
    );

endmodule
