# Pulse counter testbench

`pulse_counter_tb.v` instantiates the RTL with a 32-cycle measurement window. It has no external dependencies beyond a Verilog simulator and the `pulse_counter` RTL source.

The self-checks cover synchronous reset, an empty window, multiple distinct input pulses, a pulse edge coincident with the snapshot boundary, a pulse edge immediately after a boundary, following-window behavior, and the one-cycle width of `snapshot_valid`. Any mismatch terminates simulation with `$fatal`; success prints `PASS: pulse_counter_tb`.

Run the Vivado XSim test from the project root with:

```sh
hardware\simulation\run_xsim.bat
```

The script uses Vivado's `xvlog`, `xelab`, and `xsim`, and saves generated files and logs under `hardware/simulation/`. The equivalent commands from an initialized Vivado command prompt are:

```sh
xvlog -sv hardware/rtl/pulse_counter.v hardware/testbench/pulse_counter_tb.v
xelab pulse_counter_tb -s pulse_counter_tb_sim
xsim pulse_counter_tb_sim -runall
```

The latest saved Vivado 2024.1 XSim run completed and reported `PASS: pulse_counter_tb`. This confirms the self-checks ran in simulation; it does not validate the wrapper, board timing, electrical levels, pin assignments, or physical hardware. See [`../simulation/README.md`](../simulation/README.md) for the saved logs and status.
