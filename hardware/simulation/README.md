# Vivado XSim simulation

## Pulse counter: run this first

The counter simulation is self-contained. **No VFC circuit, LM331, PYNQ-Z2 board, wiring, or pin configuration is needed.** The testbench drives the counter with simulated clock, reset and pulse signals. The `.v` counter is hardware description source, so use this runner rather than trying to run the RTL file directly or creating a hardware project first.

1. Install/locate Vivado 2024.1 with XSim. The provided script defaults to `C:\Xilinx\Vivado\2024.1\settings64.bat`.
2. Open PowerShell in the repository root, the directory containing `hardware\`.
3. Invoke the runner:

   ```powershell
   & .\hardware\simulation\run_xsim.bat
   ```

4. Wait for `PASS: pulse_counter_tb` and `PASS: Vivado XSim pulse-counter testbench completed successfully.` The script exits with an error and points to logs if compilation, elaboration, simulation, or the PASS-marker check fails.

The runner calls `xvlog -sv`, `xelab`, and `xsim` in sequence. It writes simulator output under `hardware\simulation\`, including console logs and generated `xsim.dir` files. This run exercises only the `pulse_counter` and its testbench, not the PYNQ-Z2 wrapper or physical hardware.

If the installed Vivado is in another location, set the override for this PowerShell session and rerun:

```powershell
$env:VIVADO_SETTINGS = 'D:\Xilinx\Vivado\2024.1\settings64.bat' # replace with the actual settings64.bat path
& .\hardware\simulation\run_xsim.bat
```

The first script call is also possible from Command Prompt as `hardware\simulation\run_xsim.bat` after `cd` to the repository root. It can also be double-clicked in Explorer; PowerShell keeps the output visible more conveniently.

The script uses Vivado 2024.1 at `C:\Xilinx\Vivado\2024.1` by default and executes `xvlog -sv`, `xelab`, then `xsim`. From Command Prompt, use `hardware\simulation\run_xsim.bat` after changing to the repository root.

The script changes its working directory to `hardware/simulation/`, keeping generated simulator files and logs here. It captures console output in `vivado_setup.log`, `xvlog_console.log`, `xelab_console.log`, and `xsim_console.log`; Vivado also writes its own `xvlog.log`, `xelab.log`, and `xsim.log` files. Vivado's generated `xsim.dir/` simulation files are kept in this directory. The script returns a nonzero status when environment setup, compilation, elaboration, simulation, or the expected PASS marker fails.

The design is compiled in SystemVerilog mode because the self-checking testbench uses `$fatal`. Its files remain named `.v` and use constructs supported by the project RTL.

Expected successful output contains `PASS: pulse_counter_tb`, followed by `PASS: Vivado XSim pulse-counter testbench completed successfully.` A pass means the self-checks in the testbench passed in simulation; it does not validate board timing, electrical levels, pin assignments, or hardware behavior.

## Latest recorded result

Vivado 2024.1 is installed at `C:\Xilinx\Vivado\2024.1`. The latest saved run completed `xvlog`, `xelab`, and `xsim`; `xsim_console.log` ends with `PASS: pulse_counter_tb` and `$finish`. The self-checking counter testbench passed in simulation. Earlier failed xelab diagnostic logs remain in this directory as historical diagnostics; they do not describe the latest run. Simulation does not establish board timing, electrical safety, pin assignments, or hardware behavior.

The PYNQ-Z2 wrapper is not included in this self-checking testbench. It was separately parsed by `xvlog`; that is not wrapper simulation or synthesis. Its Vivado block-design integration is described in `../vivado/README.md`.

## Timestamp FIFO testbench

The separate AXI-Lite timestamp FIFO source and testbench are run with:

```powershell
& .\hardware\simulation\run_event_fifo_xsim.bat
```

This runner stores its own Vivado environment record, compiler path, compile/elaborate/simulate logs, and generated files under `hardware/simulation/event_fifo_run/`, preserving the pulse-counter run above. It invokes `xelab -v 2` to record the C compiler command. The latest Vivado 2024.1 run completed `xvlog`, `xelab`, and `xsim` and ended with `PASS: pulse_event_fifo_axi_tb` and `$finish`. A prior attempt from the Codex workspace sandbox could not launch GCC (Windows error 623, `ERROR_ILLEGAL_DLL_RELOCATION`); the bundled GCC started normally outside that sandbox, and the batch simulation passed there. No Vivado installation or persistent environment changes were required. Simulation does not establish synthesis, PS integration, electrical safety, pin assignments, or board behavior.
