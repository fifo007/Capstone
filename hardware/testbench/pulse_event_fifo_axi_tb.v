`timescale 1ns/1ps

module pulse_event_fifo_axi_tb;
    reg clk = 1'b0;
    reg aresetn = 1'b0;
    reg pulse_in_async = 1'b0;

    reg [5:0] awaddr = 0;
    reg [2:0] awprot = 0;
    reg awvalid = 0;
    wire awready;
    reg [31:0] wdata = 0;
    reg [3:0] wstrb = 4'hF;
    reg wvalid = 0;
    wire wready;
    wire [1:0] bresp;
    wire bvalid;
    reg bready = 1;
    reg [5:0] araddr = 0;
    reg [2:0] arprot = 0;
    reg arvalid = 0;
    wire arready;
    wire [31:0] rdata;
    wire [1:0] rresp;
    wire rvalid;
    reg rready = 1;

    reg [31:0] axi_status;
    reg [31:0] value;
    reg [63:0] timestamp_a;
    reg [63:0] timestamp_b;
    integer k;

    always #5 clk = ~clk;

    pulse_event_fifo_axi #(
        .FIFO_DEPTH(4),
        .C_S_AXI_ADDR_WIDTH(6),
        .C_S_AXI_DATA_WIDTH(32)
    ) dut (
        .pulse_in_async(pulse_in_async),
        .s_axi_aclk(clk),
        .s_axi_aresetn(aresetn),
        .s_axi_awaddr(awaddr), .s_axi_awprot(awprot), .s_axi_awvalid(awvalid), .s_axi_awready(awready),
        .s_axi_wdata(wdata), .s_axi_wstrb(wstrb), .s_axi_wvalid(wvalid), .s_axi_wready(wready),
        .s_axi_bresp(bresp), .s_axi_bvalid(bvalid), .s_axi_bready(bready),
        .s_axi_araddr(araddr), .s_axi_arprot(arprot), .s_axi_arvalid(arvalid), .s_axi_arready(arready),
        .s_axi_rdata(rdata), .s_axi_rresp(rresp), .s_axi_rvalid(rvalid), .s_axi_rready(rready)
    );

    task axi_write;
        input [5:0] address;
        input [31:0] data;
        integer cycles;
        begin
            @(negedge clk);
            awaddr = address;
            wdata = data;
            awvalid = 1'b1;
            wvalid = 1'b1;
            cycles = 0;
            while (!(awready && wready) && cycles < 20) begin
                @(negedge clk);
                cycles = cycles + 1;
            end
            if (!(awready && wready)) $fatal(1, "AXI write address/data channels timed out");
            @(negedge clk);
            awvalid = 1'b0;
            wvalid = 1'b0;
            cycles = 0;
            while (!bvalid && cycles < 20) begin
                @(negedge clk);
                cycles = cycles + 1;
            end
            if (!bvalid) $fatal(1, "AXI write response timed out");
            if (bresp !== 2'b00) $fatal(1, "unexpected AXI write response");
            @(negedge clk);
        end
    endtask

    task axi_write_aw_first;
        input [5:0] address;
        input [31:0] data;
        integer cycles;
        begin
            @(negedge clk);
            awaddr = address;
            awvalid = 1'b1;
            cycles = 0;
            while (!awready && cycles < 20) begin
                @(negedge clk);
                cycles = cycles + 1;
            end
            if (!awready) $fatal(1, "AXI AW-first address handshake timed out");
            @(negedge clk);
            awvalid = 1'b0;
            repeat (2) @(negedge clk);
            wdata = data;
            wvalid = 1'b1;
            cycles = 0;
            while (!wready && cycles < 20) begin
                @(negedge clk);
                cycles = cycles + 1;
            end
            if (!wready) $fatal(1, "AXI AW-first data handshake timed out");
            @(negedge clk);
            wvalid = 1'b0;
            cycles = 0;
            while (!bvalid && cycles < 20) begin
                @(negedge clk);
                cycles = cycles + 1;
            end
            if (!bvalid) $fatal(1, "AXI AW-first response timed out");
            if (bresp !== 2'b00) $fatal(1, "unexpected AXI AW-first response");
            @(negedge clk);
        end
    endtask

    task axi_write_w_first;
        input [5:0] address;
        input [31:0] data;
        integer cycles;
        begin
            @(negedge clk);
            wdata = data;
            wvalid = 1'b1;
            cycles = 0;
            while (!wready && cycles < 20) begin
                @(negedge clk);
                cycles = cycles + 1;
            end
            if (!wready) $fatal(1, "AXI W-first data handshake timed out");
            @(negedge clk);
            wvalid = 1'b0;
            repeat (2) @(negedge clk);
            awaddr = address;
            awvalid = 1'b1;
            cycles = 0;
            while (!awready && cycles < 20) begin
                @(negedge clk);
                cycles = cycles + 1;
            end
            if (!awready) $fatal(1, "AXI W-first address handshake timed out");
            @(negedge clk);
            awvalid = 1'b0;
            cycles = 0;
            while (!bvalid && cycles < 20) begin
                @(negedge clk);
                cycles = cycles + 1;
            end
            if (!bvalid) $fatal(1, "AXI W-first response timed out");
            if (bresp !== 2'b00) $fatal(1, "unexpected AXI W-first response");
            @(negedge clk);
        end
    endtask

    task axi_read;
        input [5:0] address;
        output [31:0] data;
        integer cycles;
        begin
            @(negedge clk);
            araddr = address;
            arvalid = 1'b1;
            cycles = 0;
            while (!arready && cycles < 20) begin
                @(negedge clk);
                cycles = cycles + 1;
            end
            if (!arready) $fatal(1, "AXI read address handshake timed out");
            @(negedge clk);
            arvalid = 1'b0;
            cycles = 0;
            while (!rvalid && cycles < 20) begin
                @(negedge clk);
                cycles = cycles + 1;
            end
            if (!rvalid) $fatal(1, "AXI read response timed out");
            if (rresp !== 2'b00) $fatal(1, "unexpected AXI read response");
            data = rdata;
            @(negedge clk);
        end
    endtask

    task send_pulse;
        begin
            @(negedge clk);
            pulse_in_async = 1'b1;
            repeat (3) @(negedge clk);
            pulse_in_async = 1'b0;
            repeat (5) @(negedge clk);
        end
    endtask

    initial begin
        repeat (4) @(negedge clk);
        aresetn = 1'b1;
        repeat (3) @(negedge clk);

        axi_read(6'h1C, value);
        if (value !== 32'h0001_0000) $fatal(1, "version register mismatch: %h", value);
        axi_write_w_first(6'h00, 32'h0000_0001); // AXI W channel precedes AW
        axi_read(6'h04, axi_status);
        if (axi_status[30] !== 1'b1) $fatal(1, "capture did not enable");

        send_pulse();
        send_pulse();
        repeat (4) @(negedge clk);
        axi_read(6'h04, axi_status);
        if (axi_status[15:0] !== 16'd2) $fatal(1, "expected 2 events, status=%h", axi_status);
        if (axi_status[31] !== 1'b0) $fatal(1, "unexpected FIFO overflow before full test");

        axi_read(6'h08, value);
        timestamp_a[31:0] = value;
        axi_read(6'h0C, value); // high word read pops first event
        timestamp_a[63:32] = value;
        axi_read(6'h08, value);
        timestamp_b[31:0] = value;
        axi_read(6'h0C, value);
        timestamp_b[63:32] = value;
        if (timestamp_b <= timestamp_a)
            $fatal(1, "timestamps not strictly increasing: %0d then %0d", timestamp_a, timestamp_b);
        axi_read(6'h04, axi_status);
        if (axi_status[15:0] !== 16'd0) $fatal(1, "FIFO did not pop both events");

        // Fill a four-entry FIFO and create one more event: the newest event
        // must be dropped, while sticky overrun and its counter report loss.
        for (k = 0; k < 5; k = k + 1) send_pulse();
        repeat (4) @(negedge clk);
        axi_read(6'h04, axi_status);
        if (axi_status[15:0] !== 16'd4) $fatal(1, "FIFO should be full, status=%h", axi_status);
        if (axi_status[31] !== 1'b1) $fatal(1, "overflow sticky flag was not set");
        axi_read(6'h10, value);
        if (value !== 32'd1) $fatal(1, "expected one overrun, got %0d", value);

        axi_write_aw_first(6'h00, 32'h0000_0002); // AXI AW channel precedes W; disable and clear overrun
        axi_read(6'h04, axi_status);
        if (axi_status[31] !== 1'b0) $fatal(1, "W1C did not clear overflow");
        if (axi_status[15:0] !== 16'd4) $fatal(1, "clearing overrun must preserve queued events");

        repeat (4) begin
            axi_read(6'h08, value);
            axi_read(6'h0C, value);
        end
        axi_read(6'h04, axi_status);
        if (axi_status[15:0] !== 16'd0) $fatal(1, "FIFO not empty after draining");

        axi_write(6'h00, 32'h0000_0001);
        send_pulse();
        axi_read(6'h04, axi_status);
        if (axi_status[15:0] !== 16'd1) $fatal(1, "reset setup did not queue one event");
        aresetn = 1'b0;
        repeat (4) @(negedge clk);
        aresetn = 1'b1;
        repeat (3) @(negedge clk);
        axi_read(6'h04, axi_status);
        if (axi_status[15:0] !== 16'd0) $fatal(1, "reset did not clear queued events");
        if (axi_status[30] !== 1'b0) $fatal(1, "reset did not disable capture");
        axi_read(6'h10, value);
        if (value !== 32'd0) $fatal(1, "reset did not clear overrun count");

        $display("PASS: pulse_event_fifo_axi_tb");
        $finish;
    end
endmodule
