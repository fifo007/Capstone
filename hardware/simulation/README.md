# Vivado XSim simulation

From repository-root PowerShell, run `& .\hardware\simulation\run_xsim.bat` or double-click the script. It uses Vivado 2024.1 at `C:\Xilinx\Vivado\2024.1` by default and executes `xvlog -sv`, `xelab`, then `xsim`. If Vivado is elsewhere, set `VIVADO_SETTINGS` to that installation's full `settings64.bat` path before invoking the script. From Command Prompt, use `hardware\simulation\run_xsim.bat`.

The script changes its working directory to `hardware/simulation/`, keeping generated simulator files and logs here. It captures console output in `vivado_setup.log`, `xvlog_console.log`, `xelab_console.log`, and `xsim_console.log`; Vivado also writes its own `xvlog.log`, `xelab.log`, and `xsim.log` files. Vivado's generated `xsim.dir/` simulation files are kept in this directory. The script returns a nonzero status when environment setup, compilation, elaboration, simulation, or the expected PASS marker fails.

The design is compiled in SystemVerilog mode because the self-checking testbench uses `$fatal`. Its files remain named `.v` and use constructs supported by the project RTL.

Expected successful output contains `PASS: pulse_counter_tb`, followed by `PASS: Vivado XSim pulse-counter testbench completed successfully.` A pass means the self-checks in the testbench passed in simulation; it does not validate board timing, electrical levels, pin assignments, or hardware behavior.

## Latest recorded result

Vivado 2024.1 is installed at `C:\Xilinx\Vivado\2024.1`. The latest saved run completed `xvlog`, `xelab`, and `xsim`; `xsim_console.log` ends with `PASS: pulse_counter_tb` and `$finish`. The self-checking counter testbench passed in simulation. Earlier failed xelab diagnostic logs remain in this directory as historical diagnostics; they do not describe the latest run. Simulation does not establish board timing, electrical safety, pin assignments, or hardware behavior.

The PYNQ-Z2 wrapper is not included in this self-checking testbench. It was separately parsed by `xvlog`; that is not wrapper simulation or synthesis. Its Vivado block-design integration is described in `../vivado/README.md`.
