# Vivado 2024.1 setup: PYNQ-Z2 pulse counter

This guide describes setup of the pulse-counter wrapper only. The wrapper and counter have not been validated on a board. This path has no AXI interface or XDC pin assignments. A separate timestamp-FIFO/AXI-Lite module has a passing XSim testbench but remains unintegrated development RTL and is not covered by this guide. There are no LM331 connections or deployment steps.

## Board support and target

The PYNQ-Z2 uses a Zynq-7000 `XC7Z020-1CLG400C` device. The TUL/PYNQ-Z2 board definition (board files) supplies the board preset used to configure PS settings; it is distinct from the board's Master XDC pin-constraint file. Use the **PYNQ-Z2** board definition only. Do not select a different board preset as a substitute. The PYNQ documentation links the PYNQ-Z2 board-file download and explains that it configures the Zynq PS settings. [PYNQ board-settings guide](https://pynq.readthedocs.io/en/v2.5/overlay_design_methodology/board_settings.html) · [PYNQ-Z2 Reference Manual](https://dpoauwgwqsy2x.cloudfront.net/Download/PYNQ_Z2_User_Manual_v1.1.pdf)

For Vivado 2024.1, install the official PYNQ-Z2 board-file package from the PYNQ board-settings page. PYNQ documents the modern Vivado `xhub` board-store directory for manually installed board files. Put its board definition under:

```text
C:\Xilinx\Vivado\2024.1\data\xhub\boards\XilinxBoardStore\boards\Xilinx\
```

Preserve the directory hierarchy from the archive; do not flatten it. Verify that the resulting PYNQ-Z2 board directory contains its `board.xml`. Close and restart Vivado after installing board files, then confirm **PYNQ-Z2** appears under the Boards selector and that the selected device is `xc7z020clg400-1` (displayed by the reference manual as `XC7Z020-1CLG400C`). Do not install or add a different preset if PYNQ-Z2 is missing; recheck the package structure and Vivado's board repository path.

The project environment checked for this work had no PYNQ/Z2-named directories in either the legacy `data\boards` path or the 2024.1 XHub board-store path. Board-file installation is therefore a remaining local setup step; this guide does not install files into Vivado.

## Clock and reset configuration

Use the Zynq Processing System's `FCLK_CLK0` output as the wrapper clock. The PYNQ-Z2 has a 50 MHz reference into the PS (`PS_CLK`); that is not the PL clock port. Enable `FCLK_CLK0` and configure its output to **100 MHz** as the proposed PL clock. The PYNQ board's PS configuration uses a 100 MHz FCLK0 setting. Check the final value in the PS Clock Configuration after applying board automation. [PYNQ-Z2 Reference Manual, clock sources](https://dpoauwgwqsy2x.cloudfront.net/Download/PYNQ_Z2_User_Manual_v1.1.pdf) · [PYNQ board-settings guide and board-file path](https://pynq.readthedocs.io/en/latest/overlay_design_methodology/board_settings.html) · [PYNQ-Z2 PS Tcl configuration](https://github.com/Xilinx/PYNQ/blob/master/boards/Pynq-Z2/petalinux_bsp/hardware_project/pynqz2.tcl)

At 100 MHz, the existing default `WINDOW_CYCLES=100000` makes each measurement window 1 ms. The count and `snapshot_valid` update at the end of every window. If a different rate or window duration is selected, recalculate `WINDOW_CYCLES` and override the wrapper parameter; the RTL itself does not assume a frequency.

Use a **Processor System Reset** IP in the block design:

- Set `slowest_sync_clk` to `FCLK_CLK0`.
- Connect the PS `FCLK_RESET0_N` to `ext_reset_in`, configured as active-low.
- Tie `dcm_locked` high when no clock manager is used.
- Connect the IP's active-high `peripheral_reset` output to the wrapper's `reset` input.

This gives the counter's synchronous, active-high reset a clock-synchronized source. Do not connect `FCLK_RESET0_N` directly to `reset`. See [AMD Processor System Reset PG164](https://docs.amd.com/api/khub/documents/5VcEWg~hYG0gT~7WNDt64g/content) for reset input and output polarity/details.

## Create and configure the project

1. In Vivado 2024.1, create a new RTL project and select **PYNQ-Z2** from the Boards list. Confirm the target part is `xc7z020clg400-1`.
2. Add these design sources:

   ```text
   hardware/rtl/pulse_counter.v
   hardware/rtl/pynq_z2_pulse_wrapper.v
   ```

   Keep `pulse_counter` unchanged. The wrapper instantiates it and exposes a simple clock, reset, asynchronous pulse input, captured count, and snapshot strobe.
3. Create a Block Design and add **Zynq7 Processing System**. Run Block Automation and apply the **PYNQ-Z2** board preset. Check that the expected DDR and fixed-IO PS interfaces are enabled by the preset. Enable `FCLK_CLK0`, then confirm it is 100 MHz after automation.
4. Add the Processor System Reset IP and configure/connect it as described above.
5. Add `pynq_z2_pulse_wrapper` to the block design as a **Module Reference**. Connect `FCLK_CLK0` to `fclk_clk0`, the synchronized active-high reset to `reset`, and make `pulse_in_gpio_async` an external block-design port. Do not assign it to a package pin.
6. Keep `snapshot_count` and `snapshot_valid` as visible wrapper outputs. They are not software-readable through the PS in this design because AXI is intentionally not included.
7. Validate the Block Design and run RTL elaboration/synthesis as needed. This is an implementation setup guide, not a report of synthesis, bitstream generation, programming, or hardware validation.

## Electrical and pin-assignment hold point

The pulse input is a logical placeholder only. Do not connect the LM331 output or another external source until its voltage range, output topology, pull-up requirements, pulse width, and common-ground/reference arrangement have been checked against the actual interface circuit and PYNQ-Z2 I/O limits. The board manual warns that signals above the board's supported logic level can damage it. After that review, select a suitable connector signal from the official PYNQ-Z2 schematic/Master XDC and add only the verified constraints. No pin name or package assignment is proposed here.

## Simulation status

The existing `pulse_counter_tb` XSim run is recorded as passing in `hardware/simulation/`. That proves the simulated counter checks only. The wrapper has not been connected to a PS block design, synthesized, constrained, deployed, or tested on PYNQ-Z2 hardware.
