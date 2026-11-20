# Campus hardware visit checklist

**Visit date:** ____________________. This checklist is for inspection and staged verification. Do not connect an unknown signal to the PYNQ-Z2, do not flash or format the SD card, and do not connect the LM331 output directly.

Use the blank [Hardware Test Log](HARDWARE_TEST_LOG.md) and [Analog Calibration Log](ANALOG_CALIBRATION_LOG.md). Record observed facts, instrument IDs/settings and failures; leave unknowns marked unknown rather than guessing.

## A. Hardware inventory

For every item, record whether it is present, its label/model/revision where applicable, condition, and any relevant settings. Photograph labels and wiring before changing anything.

| Item | Inspect and record |
|---|---|
| PYNQ-Z2 board | Exact product/model, board revision printed on PCB/label, serial/asset label if present, visible condition and connector state. Photograph both sides and labels. |
| SD card | Capacity, label, insertion state, and whether an image/version is known. Do not format, repartition, overwrite, or run repair tools. |
| Board power supply | Manufacturer/model, output voltage/current, connector/polarity marking, condition and whether it is the known board-specified supply. Do not use an unidentified adapter. |
| USB cable(s) | Connector types, data-capable vs charge-only if known, condition, and which board connector each cable fits. Record whether it is for JTAG/UART, power, or another purpose only after checking the manual/labels. |
| Laptop | OS, free disk space, administrator/access restrictions, Vivado version/install path, board-file availability, USB drivers/cable access, and ability to run PYNQ Python tools. |
| Network access | Available wired/Wi-Fi network, restrictions, whether the board image requires network access, and whether internet access is allowed. Do not expose credentials in the log. |
| Oscilloscope and probes | Make/model, probe type/attenuation, compensation state, bandwidth/sample rate, calibration status, ground lead type, and channel settings. |
| Multimeter | Make/model, calibration/status, lead condition, measurement mode/range and battery status. |
| Potentiometer and source | Pot value/taper/rating if marked, supply/source range, wiring, wiper voltage range and current-limiting arrangement. Record the circuit source; do not assume it is 0–1 V without measuring it. |
| LM331 circuit | Schematic/board revision if available; IC marking; component values; supply rails; output-stage topology; pull-up presence/value/rail; output connector; and known calibration. Do not connect to the FPGA yet. |
| Passive/interface parts | Resistors, capacitors, pull-ups, level-shifting/buffering parts, breadboard and jumper wires. Record markings/tolerances and verify the proposed part values against a reviewed schematic before use. |
| Logic-level pulse sources | Generator/model, output type (push-pull/open-drain/etc.), allowed amplitude/offset/load, frequency/duty/pulse-width controls and output impedance. Do not infer output levels from the knob setting; measure them. |

## B. Board inspection and boot

- [ ] Photograph the board front/back and close-ups of the product label, PCB revision, connectors and any damage. Record model/revision exactly as printed; do not infer revision from appearance.
- [ ] Inspect for bent pins, debris, corrosion, loose connectors, cracked components, unusual smell, or prior rework. If anything appears damaged, stop before powering and ask the lab supervisor.
- [ ] Record SD card identity and insertion state. Inspect it without formatting or modifying it. Ask before removing it; if removed, use anti-static handling and return it in the same state.
- [ ] Record the power input that will be used and the supply label/polarity. Check the board manual and supply label before connecting power. Do not power from an unknown adapter.
- [ ] Record USB connection(s), connector labels, jumper/switch positions and cables before changing them. Use the board manual to identify each connector; do not guess from connector shape.
- [ ] With no external circuit connected, power the board using the confirmed supply. Record LEDs, boot behavior, serial-console output if available and any errors. Stop if there is abnormal heating, smell or unexpected behavior.
- [ ] Determine whether PYNQ Linux boots and whether the board is reachable locally (console/network as allowed). Record method and result; do not change network or boot settings without permission.
- [ ] If accessible, record `pynq` package/image version and OS/kernel version from the running system. If it is not accessible, record “not verified” and continue only with non-invasive inspection.

## C. Vivado preparation

- [ ] Record Vivado version and exact install path on the laptop that will be used.
- [ ] Check the official PYNQ-Z2 board definition. For the inspected Vivado 2024.1 installation, the expected manual board-file location is `C:\Xilinx\Vivado\2024.1\data\xhub\boards\XilinxBoardStore\boards\Xilinx\`; board support must be installed from the PYNQ board-settings source and Vivado restarted. The earlier local check did not find a PYNQ/Z2 entry, so verify on the actual lab laptop. Do not install a different board preset as a substitute. See the [PYNQ board-settings guide](https://pynq.readthedocs.io/en/latest/overlay_design_methodology/board_settings.html) and [AMD board-file installation guidance](https://docs.amd.com/r/en-US/ug1289-u200-u250-reconfig-accel/Vivado-Board-Support-and-XDC-Files-Installation).
- [ ] In Vivado's Boards selector, choose **PYNQ-Z2** only. Confirm the device is `XC7Z020-1CLG400C` / `xc7z020clg400-1`. If the board is missing or the device differs, stop and resolve board support/identity; do not choose another preset.
- [ ] In the Zynq7 Processing System configuration, apply the PYNQ-Z2 board preset and inspect PS DDR/fixed-IO settings rather than entering speculative values. Record any warning and the preset name.
- [ ] Enable PS `FCLK_CLK0` and inspect its actual configured frequency after applying board automation. The project proposes 100 MHz and the existing default counter window is 100,000 cycles (1 ms only if the clock is exactly 100 MHz). Record the displayed value; do not assume it survived automation. The PYNQ-Z2 board reference specifies a 50 MHz `PS_CLK` input to the PS; this is distinct from `FCLK_CLK0`.
- [ ] Configure reset using Processor System Reset: `slowest_sync_clk` = `FCLK_CLK0`; `FCLK_RESET0_N` into active-low `ext_reset_in`; `dcm_locked` high when no clock manager is used; active-high `peripheral_reset` to the wrapper reset. Do not wire the active-low PS reset directly to the counter's active-high synchronous reset.
- [ ] Before making a final block design, determine/record: exact board/revision, board-file status, actual FCLK0 frequency, reset wiring/polarity, pulse input source/interface, required pulse high/low widths and rates, a verified safe connector/bank and its I/O standard, output observation method, intended count window, and how software will read the snapshot. Pin and electrical decisions require actual inspection/measurements; none are specified here.

## D. First hardware test (staged; stop at any unsafe/unknown condition)

### 1. Verify board power and boot

- [ ] With the pulse circuit disconnected, use only the confirmed board power arrangement. Record supply label, LED behavior, boot indicators, console/network access and PYNQ version if available.
- [ ] Expected observation: board powers without abnormal heating and, if the installed image is bootable, reaches its normal PYNQ/Linux state. If it does not boot, record the observed LED/console behavior; do not flash or alter the SD card.

### 2. Verify the FPGA configuration workflow

- [ ] Verify Vivado sees the board/cable using the appropriate Hardware Manager flow and the lab's approved known-good design/bitstream, if one is provided. Record cable and Vivado messages.
- [ ] Do not program an unreviewed bitstream or use another board's preset. The pulse-counter wrapper is not yet a complete project/bitstream. If no approved known-good image is available, record configuration workflow as unverified.
- [ ] Expected observation: the hardware target is detected and the approved image/programming action completes without error. This does not prove this pulse counter works on hardware.

### 3. Establish PL clock and reset

- [ ] In the PYNQ-Z2 PS block design, apply the correct preset, enable `FCLK_CLK0`, and record the actual frequency after automation. Proposed 100 MHz is a setup target to confirm, not a measured board result.
- [ ] Connect the clock/reset according to Section C. Record reset polarity and the processor-system-reset outputs. Verify the block design and inspect generated clock/reset reports or use a reviewed observation method.
- [ ] Expected observation: the design reports the intended PL clock and reset connections without validation errors. Do not infer clock frequency from the board's 50 MHz `PS_CLK` oscillator label.

### 4. Test pulse capture using a verified safe logic-level source

- [ ] First identify a candidate board input using the official schematic/Master XDC for the exact board revision. Check the bank supply and allowed I/O standard. Do not guess a pin.
- [ ] With the source disconnected from the board, measure the source output's low/high levels, offset, overshoot, pulse width, duty cycle and frequency using the scope. Confirm its topology, current limit and behavior at the intended load. Record instrument and settings.
- [ ] Verify common-ground plan with power off. Ensure the scope ground clip will not short a live/isolated node; use the lab's approved probing method. Do not connect a probe ground to an unknown reference.
- [ ] Only after source, pin, I/O bank, voltage and grounding are reviewed as compatible, and after a reviewed constraint exists, connect the known safe logic-level source with the board powered off unless the lab procedure explicitly requires otherwise.
- [ ] The pulse-counter wrapper exposes count/strobe as RTL outputs but has no AXI path. A separate timestamp-FIFO/AXI-Lite module and Python reader are present as development files; they are not integrated into a Vivado block design, and the latest FIFO testbench attempt did not complete. Do not use them as a verified observation path. For the counter, use a reviewed method (for example, an ILA probe) or leave observation as a later step. Do not assume PYNQ Python can read the counter yet.
- [ ] Apply a known frequency/window test plan. Record source frequency and level, configured FCLK0 and `WINDOW_CYCLES`, expected count per window, observed snapshot count/valid event and any discrepancy. A count expectation is only meaningful after clock, pulse width and measurement-window timing are known.

### 5. Observe and record pulse and count

- [ ] Capture a scope screenshot of the pulse at the source and, if safely accessible, at the FPGA-side signal. Record volts/div, time/div, probe attenuation, trigger and channel reference.
- [ ] Record counter observations from the approved ILA/software method, including window duration, repeated readings and valid-strobe timing. Compare only against a calculated expectation based on measured input frequency and configured window; report missed/extra edges rather than hiding them.
- [ ] If the signal is noisy, exceeds the agreed range, clips/overshoots, has unknown grounding, or the count is inconsistent, stop and disconnect safely. Do not proceed to LM331 hookup.

### 6. Plan LM331 integration only after electrical verification

- [ ] With LM331 unconnected from the PYNQ-Z2, document its schematic and identify open-collector/open-drain or push-pull topology, pull-up rail/value, output low/high voltage, pulse width/duty and frequency versus input voltage.
- [ ] Measure the converter output under its own circuit load across the planned potentiometer range; record values in the calibration log. Use a multimeter for DC levels and an oscilloscope/frequency counter for pulse behavior.
- [ ] Obtain review of the interface (including any pull-up, divider, buffer/level translation and common-ground requirements) before selecting a board connector/pin or connecting it. Do not connect the LM331 output directly based only on its IC name or a nominal supply voltage.

## E. Electrical safety hold point

PYNQ-Z2 GPIO must **not** receive 5 V. PYNQ-Z2 Pmod headers provide 3.3 V VCC and logic signals; 3.3 V on a connector does not mean every attached circuit is automatically safe. Confirm the exact connector, FPGA bank, board revision and applicable I/O limits from the official [PYNQ-Z2 reference manual](https://www.mouser.com/pdfDocs/pynqz2_user_manual_v1_0.pdf) and device documentation before any connection.

Before connecting any external pulse source:

- [ ] Identify the source output topology from its schematic/datasheet; confirm whether it is open collector/drain and whether a pull-up exists.
- [ ] Identify pull-up voltage and resistance; do not add or move a pull-up until reviewed.
- [ ] Measure unloaded and intended-load logic-low/high levels, DC offset, ringing and overshoot with the board disconnected.
- [ ] Measure pulse high/low widths, duty cycle, frequency range, rise/fall time and startup/transient behavior.
- [ ] Confirm board bank VCCO / selected I/O standard supports the measured levels and that input current/series protection are appropriate.
- [ ] Confirm ground/reference and scope-ground safety; never join grounds or attach scope ground blindly.
- [ ] Check wiring against the exact board revision's schematic/Master XDC. Record the approved connector and pin in the log only after review.
- [ ] If any value or topology is unknown, **do not connect the signal**. Ask the supervisor or circuit designer and keep the board input disconnected.

## Bring to campus

- [ ] PYNQ-Z2 board and its SD card (do not format or alter).
- [ ] Confirmed board power supply and the required known-good USB data cable(s), identified from the manual.
- [ ] Laptop with Vivado 2024.1 or access to the lab Vivado workstation; project files copied/synced; charger and approved network access.
- [ ] LM331 circuit schematic/BOM and potentiometer, but keep the circuit disconnected from the board.
- [ ] Multimeter, oscilloscope probes and a known safe logic-level pulse source if available.
- [ ] Resistors/capacitors/interfaces only when values and circuit use have been reviewed; breadboard/jumper wires.
- [ ] This checklist, [hardware test log](HARDWARE_TEST_LOG.md), [calibration log](ANALOG_CALIBRATION_LOG.md), notebook/pen, and a way to save scope screenshots.
