# Pulse counter testbench

`pulse_counter_tb.v` instantiates the RTL with a 32-cycle measurement window. It has no external dependencies beyond a Verilog simulator and the `pulse_counter` RTL source.

## First run in Windows PowerShell

No VFC circuit, LM331, PYNQ-Z2, or physical signal connection is required. The testbench generates its own clock, reset, and test pulses in simulation. You need Vivado 2024.1 with XSim installed.

1. Open PowerShell in the cloned repository root (the folder containing `hardware\`).
2. Run the batch script:

   ```powershell
   & .\hardware\simulation\run_xsim.bat
   ```

3. Confirm the console contains both `PASS: pulse_counter_tb` and `PASS: Vivado XSim pulse-counter testbench completed successfully.` A failure is reported with a nonzero exit status and a log filename. Logs and build files are in `hardware\simulation\`.

Do not launch `pulse_counter.v` by itself and do not connect the VFC circuit for this procedure. The testbench generates synthetic digital pulses; it validates RTL assertions in simulation only. For a Vivado GUI block design, which is a different workflow, see [`../vivado/README.md`](../vivado/README.md).

The self-checks cover synchronous reset, an empty window, multiple distinct input pulses, a pulse edge coincident with the snapshot boundary, a pulse edge immediately after a boundary, following-window behavior, and the one-cycle width of `snapshot_valid`. Any mismatch terminates simulation with `$fatal`; success prints `PASS: pulse_counter_tb`.

The batch script is the recommended one-command route. To run the simulator tools manually, open **Vivado 2024.1 Command Prompt** from the Start menu, change into the simulation folder, and enter:

```bat
cd /d C:\Users\sagni\OneDrive\Documents\capstone\hardware\simulation
xvlog -sv ..\rtl\pulse_counter.v ..\testbench\pulse_counter_tb.v
xelab pulse_counter_tb -s pulse_counter_tb_sim
xsim pulse_counter_tb_sim -runall
```

For another clone location, replace the `cd /d` path with that clone's `hardware\simulation` folder. The batch runner is preferred because it selects the working directory and captures logs automatically.

The latest saved Vivado 2024.1 XSim run completed and reported `PASS: pulse_counter_tb`. This confirms the self-checks ran in simulation; it does not validate the wrapper, board timing, electrical levels, pin assignments, or physical hardware. See [`../simulation/README.md`](../simulation/README.md) for the saved logs and status.

## Timestamp FIFO testbench

`pulse_event_fifo_axi_tb.v` checks the FIFO's version register, both AW-before-W and W-before-AW AXI-Lite writes, reads, timestamp ordering, full-FIFO overflow indication, write-one-to-clear behavior, FIFO draining, and reset clearing. Run it with `& .\hardware\simulation\run_event_fifo_xsim.bat` from the repository root. The latest Vivado 2024.1 XSim run completed and printed `PASS: pulse_event_fifo_axi_tb`. This validates the covered RTL behavior in simulation only; it does not validate the Vivado block design or physical hardware. See [`../simulation/README.md`](../simulation/README.md).
