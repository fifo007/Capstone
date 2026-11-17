`timescale 1ns/1ps

module pulse_counter #(
    parameter integer WINDOW_CYCLES = 100000,
    parameter integer COUNTER_WIDTH = 32
) (
    input  wire                      clk,
    input  wire                      reset,
    input  wire                      pulse_in_async,
    output reg  [COUNTER_WIDTH-1:0]  snapshot_count,
    output reg                       snapshot_valid
);

    (* ASYNC_REG = "TRUE" *) reg pulse_sync_meta;
    (* ASYNC_REG = "TRUE" *) reg pulse_sync;
    reg pulse_sync_d;

    reg [COUNTER_WIDTH-1:0] pulse_count;
    reg [31:0] window_cycle_count;

    wire pulse_rise = pulse_sync & ~pulse_sync_d;

    always @(posedge clk) begin
        if (reset) begin
            pulse_sync_meta  <= 1'b0;
            pulse_sync       <= 1'b0;
            pulse_sync_d     <= 1'b0;
            pulse_count      <= {COUNTER_WIDTH{1'b0}};
            window_cycle_count <= 32'd0;
            snapshot_count   <= {COUNTER_WIDTH{1'b0}};
            snapshot_valid   <= 1'b0;
        end else begin
            pulse_sync_meta <= pulse_in_async;
            pulse_sync      <= pulse_sync_meta;
            pulse_sync_d    <= pulse_sync;
            snapshot_valid  <= 1'b0;

            if (window_cycle_count == WINDOW_CYCLES - 1) begin
                // Include an edge detected on this boundary clock in the
                // window that is completing.
                snapshot_count <= pulse_count + pulse_rise;
                pulse_count    <= {COUNTER_WIDTH{1'b0}};
                window_cycle_count <= 32'd0;
                snapshot_valid <= 1'b1;
            end else begin
                if (pulse_rise)
                    pulse_count <= pulse_count + 1'b1;
                window_cycle_count <= window_cycle_count + 1'b1;
            end
        end
    end

endmodule
