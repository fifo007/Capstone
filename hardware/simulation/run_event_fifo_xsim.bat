@echo off
setlocal

rem Run the timestamp FIFO AXI-Lite testbench without changing the saved
rem pulse-counter simulation artifacts. Results are isolated in event_fifo_run.
if not defined VIVADO_SETTINGS set "VIVADO_SETTINGS=C:\Xilinx\Vivado\2024.1\settings64.bat"

set "SIM_DIR=%~dp0event_fifo_run"
if not exist "%SIM_DIR%" mkdir "%SIM_DIR%"

if not exist "%VIVADO_SETTINGS%" (
    echo ERROR: Vivado settings script not found: "%VIVADO_SETTINGS%"
    exit /b 2
)

pushd "%SIM_DIR%"
call "%VIVADO_SETTINGS%" > "vivado_setup.log" 2>&1
if errorlevel 1 (
    echo ERROR: Vivado environment setup failed. See "%SIM_DIR%\vivado_setup.log".
    popd
    exit /b 3
)

where gcc > "gcc_environment.log" 2>&1
if not errorlevel 1 gcc --version >> "gcc_environment.log" 2>&1

call xvlog -sv "..\..\rtl\pulse_event_fifo_axi.v" "..\..\testbench\pulse_event_fifo_axi_tb.v" > "xvlog_console.log" 2>&1
if errorlevel 1 (
    echo ERROR: xvlog compilation failed. See "%SIM_DIR%\xvlog_console.log".
    type "xvlog_console.log"
    if exist "xvlog.log" type "xvlog.log"
    popd
    exit /b 4
)

call xelab -v 2 pulse_event_fifo_axi_tb -s pulse_event_fifo_axi_tb_sim > "xelab_console.log" 2>&1
if errorlevel 1 (
    echo ERROR: xelab elaboration failed. See "%SIM_DIR%\xelab_console.log".
    findstr /C:"The system cannot execute" /C:"ERROR: [XSIM" "xelab_console.log"
    popd
    exit /b 5
)

call xsim pulse_event_fifo_axi_tb_sim -runall > "xsim_console.log" 2>&1
set "XSIM_EXIT=%ERRORLEVEL%"
type "xsim_console.log"
if not "%XSIM_EXIT%"=="0" (
    echo ERROR: xsim returned exit code %XSIM_EXIT%. See "%SIM_DIR%\xsim.log".
    if exist "xsim.log" type "xsim.log"
    popd
    exit /b %XSIM_EXIT%
)

findstr /C:"PASS: pulse_event_fifo_axi_tb" "xsim_console.log" >nul
if errorlevel 1 (
    echo ERROR: xsim exited successfully but the testbench PASS marker was not found.
    popd
    exit /b 6
)

echo PASS: Vivado XSim timestamp FIFO testbench completed successfully.
echo Logs and generated simulation files are in "%SIM_DIR%".
popd
exit /b 0
