`timescale 1ns/1ps

// Timestamped asynchronous-pulse capture with a memory-mapped AXI4-Lite FIFO.
// Timestamps are 64-bit FCLK cycles. The software reader must be configured
// with the verified FCLK0 rate; no physical package pin is assigned here.
module pulse_event_fifo_axi #(
    parameter integer FIFO_DEPTH = 1024,
    parameter integer C_S_AXI_ADDR_WIDTH = 6,
    parameter integer C_S_AXI_DATA_WIDTH = 32
) (
    input  wire                                  pulse_in_async,

    (* X_INTERFACE_INFO = "xilinx.com:signal:clock:1.0 S_AXI_ACLK CLK" *)
    (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME S_AXI_ACLK, ASSOCIATED_BUSIF S_AXI, ASSOCIATED_RESET s_axi_aresetn" *)
    input  wire                                  s_axi_aclk,
    (* X_INTERFACE_INFO = "xilinx.com:signal:reset:1.0 S_AXI_ARESETN RST" *)
    (* X_INTERFACE_PARAMETER = "XIL_INTERFACENAME S_AXI_ARESETN, POLARITY ACTIVE_LOW" *)
    input  wire                                  s_axi_aresetn,

    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWADDR" *)
    input  wire [C_S_AXI_ADDR_WIDTH-1:0]         s_axi_awaddr,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWPROT" *)
    input  wire [2:0]                            s_axi_awprot,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWVALID" *)
    input  wire                                  s_axi_awvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI AWREADY" *)
    output wire                                  s_axi_awready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WDATA" *)
    input  wire [C_S_AXI_DATA_WIDTH-1:0]         s_axi_wdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WSTRB" *)
    input  wire [(C_S_AXI_DATA_WIDTH/8)-1:0]     s_axi_wstrb,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WVALID" *)
    input  wire                                  s_axi_wvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI WREADY" *)
    output wire                                  s_axi_wready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI BRESP" *)
    output wire [1:0]                            s_axi_bresp,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI BVALID" *)
    output reg                                   s_axi_bvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI BREADY" *)
    input  wire                                  s_axi_bready,

    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARADDR" *)
    input  wire [C_S_AXI_ADDR_WIDTH-1:0]         s_axi_araddr,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARPROT" *)
    input  wire [2:0]                            s_axi_arprot,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARVALID" *)
    input  wire                                  s_axi_arvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI ARREADY" *)
    output wire                                  s_axi_arready,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RDATA" *)
    output reg  [C_S_AXI_DATA_WIDTH-1:0]         s_axi_rdata,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RRESP" *)
    output wire [1:0]                            s_axi_rresp,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RVALID" *)
    output reg                                   s_axi_rvalid,
    (* X_INTERFACE_INFO = "xilinx.com:interface:aximm:1.0 S_AXI RREADY" *)
    input  wire                                  s_axi_rready
);

    localparam [C_S_AXI_ADDR_WIDTH-1:0] ADDR_CONTROL      = 6'h00;
    localparam [C_S_AXI_ADDR_WIDTH-1:0] ADDR_STATUS       = 6'h04;
    localparam [C_S_AXI_ADDR_WIDTH-1:0] ADDR_EVENT_LO     = 6'h08;
    localparam [C_S_AXI_ADDR_WIDTH-1:0] ADDR_EVENT_HI_POP = 6'h0C;
    localparam [C_S_AXI_ADDR_WIDTH-1:0] ADDR_OVERRUNS     = 6'h10;
    localparam [C_S_AXI_ADDR_WIDTH-1:0] ADDR_CYCLE_LO    = 6'h14;
    localparam [C_S_AXI_ADDR_WIDTH-1:0] ADDR_CYCLE_HI    = 6'h18;
    localparam [C_S_AXI_ADDR_WIDTH-1:0] ADDR_VERSION     = 6'h1C;

    localparam integer PTR_WIDTH = $clog2(FIFO_DEPTH);
    localparam [C_S_AXI_DATA_WIDTH-1:0] VERSION_VALUE = 32'h0001_0000;

    (* ASYNC_REG = "TRUE" *) reg pulse_sync_meta;
    (* ASYNC_REG = "TRUE" *) reg pulse_sync;
    reg pulse_sync_d;
    reg capture_enable;
    reg [63:0] cycle_counter;
    reg [63:0] event_memory [0:FIFO_DEPTH-1];
    reg [PTR_WIDTH-1:0] write_ptr;
    reg [PTR_WIDTH-1:0] read_ptr;
    reg [PTR_WIDTH:0] event_count;
    reg overrun_sticky;
    reg [31:0] overrun_count;

    wire pulse_rise = pulse_sync & ~pulse_sync_d;
    wire event_arrival = capture_enable & pulse_rise;

    // AXI-Lite write channel state. AW and W can arrive in either order.
    reg aw_pending;
    reg w_pending;
    reg [C_S_AXI_ADDR_WIDTH-1:0] awaddr_saved;
    reg [C_S_AXI_DATA_WIDTH-1:0] wdata_saved;
    reg [(C_S_AXI_DATA_WIDTH/8)-1:0] wstrb_saved;
    wire aw_take = s_axi_awvalid & s_axi_awready;
    wire w_take = s_axi_wvalid & s_axi_wready;
    wire write_fire = (aw_pending | aw_take) & (w_pending | w_take) & ~s_axi_bvalid;
    wire [C_S_AXI_ADDR_WIDTH-1:0] write_addr = aw_pending ? awaddr_saved : s_axi_awaddr;
    wire [C_S_AXI_DATA_WIDTH-1:0] write_data = w_pending ? wdata_saved : s_axi_wdata;
    wire [(C_S_AXI_DATA_WIDTH/8)-1:0] write_strb = w_pending ? wstrb_saved : s_axi_wstrb;
    wire clear_overrun = write_fire & (write_addr == ADDR_CONTROL) & write_strb[0] & write_data[1];

    // A read of EVENT_TIME_HI_POP consumes the event after its AXI response is
    // accepted. EVENT_TIME_LO is non-destructive, so software reads LO then HI.
    reg [C_S_AXI_ADDR_WIDTH-1:0] read_addr_saved;
    wire read_fire = s_axi_rvalid & s_axi_rready;
    wire event_pop = read_fire & (read_addr_saved == ADDR_EVENT_HI_POP) & (event_count != 0);
    wire event_push = event_arrival & ((event_count < FIFO_DEPTH) | event_pop);
    wire event_overflow = event_arrival & ~event_push;

    assign s_axi_awready = ~aw_pending & ~s_axi_bvalid;
    assign s_axi_wready  = ~w_pending & ~s_axi_bvalid;
    assign s_axi_arready = ~s_axi_rvalid;
    assign s_axi_bresp = 2'b00;
    assign s_axi_rresp = 2'b00;

    wire [15:0] event_count_status = event_count;
    wire [63:0] head_event = event_memory[read_ptr];
    reg [C_S_AXI_DATA_WIDTH-1:0] read_mux;

    always @* begin
        read_mux = {C_S_AXI_DATA_WIDTH{1'b0}};
        case (s_axi_araddr)
            ADDR_CONTROL:      read_mux = {{(C_S_AXI_DATA_WIDTH-1){1'b0}}, capture_enable};
            ADDR_STATUS:       read_mux = {overrun_sticky, capture_enable, 14'b0, event_count_status};
            ADDR_EVENT_LO:     read_mux = event_count != 0 ? head_event[31:0] : 32'b0;
            ADDR_EVENT_HI_POP: read_mux = event_count != 0 ? head_event[63:32] : 32'b0;
            ADDR_OVERRUNS:     read_mux = overrun_count;
            ADDR_CYCLE_LO:     read_mux = cycle_counter[31:0];
            ADDR_CYCLE_HI:     read_mux = cycle_counter[63:32];
            ADDR_VERSION:      read_mux = VERSION_VALUE;
            default:           read_mux = {C_S_AXI_DATA_WIDTH{1'b0}};
        endcase
    end

    // Pulse synchronizer, free-running timestamp counter, and event FIFO.
    always @(posedge s_axi_aclk) begin
        if (!s_axi_aresetn) begin
            pulse_sync_meta <= 1'b0;
            pulse_sync <= 1'b0;
            pulse_sync_d <= 1'b0;
            cycle_counter <= 64'd0;
            write_ptr <= {PTR_WIDTH{1'b0}};
            read_ptr <= {PTR_WIDTH{1'b0}};
            event_count <= {(PTR_WIDTH+1){1'b0}};
            overrun_sticky <= 1'b0;
            overrun_count <= 32'd0;
        end else begin
            pulse_sync_meta <= pulse_in_async;
            pulse_sync <= pulse_sync_meta;
            pulse_sync_d <= pulse_sync;
            cycle_counter <= cycle_counter + 1'b1;

            if (event_push) begin
                event_memory[write_ptr] <= cycle_counter;
                write_ptr <= write_ptr + 1'b1;
            end
            if (event_pop)
                read_ptr <= read_ptr + 1'b1;

            case ({event_push, event_pop})
                2'b10: event_count <= event_count + 1'b1;
                2'b01: event_count <= event_count - 1'b1;
                default: event_count <= event_count;
            endcase

            if (event_overflow) begin
                overrun_sticky <= 1'b1;
                if (overrun_count != 32'hFFFF_FFFF)
                    overrun_count <= overrun_count + 1'b1;
            end else if (clear_overrun) begin
                overrun_sticky <= 1'b0;
            end
        end
    end

    // AXI-Lite write response and capture control.
    always @(posedge s_axi_aclk) begin
        if (!s_axi_aresetn) begin
            aw_pending <= 1'b0;
            w_pending <= 1'b0;
            awaddr_saved <= {C_S_AXI_ADDR_WIDTH{1'b0}};
            wdata_saved <= {C_S_AXI_DATA_WIDTH{1'b0}};
            wstrb_saved <= {(C_S_AXI_DATA_WIDTH/8){1'b0}};
            s_axi_bvalid <= 1'b0;
            capture_enable <= 1'b0;
        end else begin
            if (aw_take) begin
                aw_pending <= 1'b1;
                awaddr_saved <= s_axi_awaddr;
            end
            if (w_take) begin
                w_pending <= 1'b1;
                wdata_saved <= s_axi_wdata;
                wstrb_saved <= s_axi_wstrb;
            end
            if (write_fire) begin
                aw_pending <= 1'b0;
                w_pending <= 1'b0;
                s_axi_bvalid <= 1'b1;
                if ((write_addr == ADDR_CONTROL) && write_strb[0])
                    capture_enable <= write_data[0];
            end
            if (s_axi_bvalid && s_axi_bready)
                s_axi_bvalid <= 1'b0;
        end
    end

    // AXI-Lite read response. RDATA is held stable while RVALID is stalled.
    always @(posedge s_axi_aclk) begin
        if (!s_axi_aresetn) begin
            s_axi_rvalid <= 1'b0;
            s_axi_rdata <= {C_S_AXI_DATA_WIDTH{1'b0}};
            read_addr_saved <= {C_S_AXI_ADDR_WIDTH{1'b0}};
        end else begin
            if (s_axi_arvalid && s_axi_arready) begin
                s_axi_rvalid <= 1'b1;
                s_axi_rdata <= read_mux;
                read_addr_saved <= s_axi_araddr;
            end
            if (s_axi_rvalid && s_axi_rready)
                s_axi_rvalid <= 1'b0;
        end
    end

endmodule
