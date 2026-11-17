`timescale 1ns/1ps

module pulse_counter_tb;

    localparam integer WINDOW_CYCLES = 32;
    localparam integer COUNTER_WIDTH = 8;

    reg clk = 1'b0;
    reg reset = 1'b0;
    reg pulse_in_async = 1'b0;
    wire [COUNTER_WIDTH-1:0] snapshot_count;
    wire snapshot_valid;

    pulse_counter #(
        .WINDOW_CYCLES(WINDOW_CYCLES),
        .COUNTER_WIDTH(COUNTER_WIDTH)
    ) dut (
        .clk(clk),
        .reset(reset),
        .pulse_in_async(pulse_in_async),
        .snapshot_count(snapshot_count),
        .snapshot_valid(snapshot_valid)
    );

    always #5 clk = ~clk;

    task apply_reset;
        begin
            @(negedge clk);
            pulse_in_async = 1'b0;
            reset = 1'b1;
            @(posedge clk);
            #1;
            if (snapshot_count !== {COUNTER_WIDTH{1'b0}})
                $fatal(1, "snapshot_count did not clear during reset");
            if (snapshot_valid !== 1'b0)
                $fatal(1, "snapshot_valid was high during reset");
            repeat (2) @(negedge clk);
            reset = 1'b0;
        end
    endtask

    task wait_for_snapshot;
        input integer expected_count;
        integer cycles;
        begin
            cycles = 0;
            while ((snapshot_valid !== 1'b1) && (cycles < WINDOW_CYCLES + 8)) begin
                @(posedge clk);
                #1;
                cycles = cycles + 1;
            end
            if (snapshot_valid !== 1'b1)
                $fatal(1, "timed out waiting for snapshot_valid");
            if (snapshot_count !== expected_count)
                $fatal(1, "expected count %0d, got %0d", expected_count, snapshot_count);

            @(posedge clk);
            #1;
            if (snapshot_valid !== 1'b0)
                $fatal(1, "snapshot_valid was not a one-cycle pulse");
        end
    endtask

    task send_pulse;
        input integer high_cycles;
        begin
            @(negedge clk);
            pulse_in_async = 1'b1;
            repeat (high_cycles) @(negedge clk);
            pulse_in_async = 1'b0;
            // Leave enough low time for the synchronized edge detector to
            // re-arm before the next pulse.
            repeat (2) @(negedge clk);
        end
    endtask

    task send_edge_on_first_boundary;
        begin
            // With the two-flop synchronizer and registered edge history,
            // this input timing makes pulse_rise true on the first boundary
            // clock of the 32-cycle window.
            repeat (WINDOW_CYCLES - 3) @(negedge clk);
            pulse_in_async = 1'b1;
            repeat (3) @(negedge clk);
            pulse_in_async = 1'b0;
        end
    endtask

    task send_edge_just_after_first_boundary;
        begin
            // The synchronized rising edge is detected one clock after the
            // first window closes, so it must be counted in the next window.
            repeat (WINDOW_CYCLES - 2) @(negedge clk);
            pulse_in_async = 1'b1;
            repeat (2) @(negedge clk);
            pulse_in_async = 1'b0;
        end
    endtask

    initial begin
        apply_reset();
        wait_for_snapshot(0); // zero pulses

        apply_reset();
        send_pulse(3);
        send_pulse(3);
        send_pulse(3);
        send_pulse(3);
        wait_for_snapshot(4); // multiple pulses in one window

        apply_reset();
        send_edge_on_first_boundary();
        wait_for_snapshot(1); // boundary edge belongs to the closing window
        wait_for_snapshot(0); // next window starts with a cleared count

        apply_reset();
        send_edge_just_after_first_boundary();
        wait_for_snapshot(0); // edge is detected after boundary one
        wait_for_snapshot(1); // and appears in window two

        apply_reset();
        send_pulse(3);
        // Reset mid-window must discard the partial count and restart timing.
        apply_reset();
        wait_for_snapshot(0);

        $display("PASS: pulse_counter_tb");
        $finish;
    end

endmodule
