@echo off
setlocal

rem Run this file from any working directory. Vivado 2024.1 was found at
rem C:\Xilinx\Vivado\2024.1 on the inspected machine. Override this variable
rem if the installation is moved or a different Vivado release is preferred.
if not defined VIVADO_SETTINGS set "VIVADO_SETTINGS=C:\Xilinx\Vivado\2024.1\settings64.bat"

set "SIM_DIR=%~dp0"
for %%I in ("%SIM_DIR%..\..") do set "PROJECT_ROOT=%%~fI"

if not exist "%VIVADO_SETTINGS%" (
    echo ERROR: Vivado settings script not found: "%VIVADO_SETTINGS%"
    echo Set VIVADO_SETTINGS to the full path of your Vivado settings64.bat.
    exit /b 2
)

pushd "%SIM_DIR%"
call "%VIVADO_SETTINGS%" > "vivado_setup.log" 2>&1
if errorlevel 1 (
    echo ERROR: Vivado environment setup failed. See "%SIM_DIR%vivado_setup.log".
    popd
    exit /b 3
)

call xvlog -sv "..\rtl\pulse_counter.v" "..\testbench\pulse_counter_tb.v" > "xvlog_console.log" 2>&1
if errorlevel 1 (
    echo ERROR: xvlog compilation failed. See "%SIM_DIR%xvlog.log".
    type "xvlog_console.log"
    if exist "xvlog.log" type "xvlog.log"
    popd
    exit /b 4
)

call xelab pulse_counter_tb -s pulse_counter_tb_sim > "xelab_console.log" 2>&1
if errorlevel 1 (
    echo ERROR: xelab elaboration failed. See "%SIM_DIR%xelab.log".
    type "xelab_console.log"
    if exist "xelab.log" type "xelab.log"
    popd
    exit /b 5
)

call xsim pulse_counter_tb_sim -runall > "xsim_console.log" 2>&1
set "XSIM_EXIT=%ERRORLEVEL%"
type "xsim_console.log"
if not "%XSIM_EXIT%"=="0" (
    echo ERROR: xsim returned exit code %XSIM_EXIT%. See "%SIM_DIR%xsim.log".
    if exist "xsim.log" type "xsim.log"
    popd
    exit /b %XSIM_EXIT%
)

findstr /C:"PASS: pulse_counter_tb" "xsim_console.log" >nul
if errorlevel 1 (
    echo ERROR: xsim exited successfully but the testbench PASS marker was not found.
    popd
    exit /b 6
)

echo PASS: Vivado XSim pulse-counter testbench completed successfully.
echo Logs and generated simulation files are in "%SIM_DIR%".
popd
exit /b 0
