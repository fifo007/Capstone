# Hardware test log

Blank record for bench observations. Use one copy per session/build. Do not fill unknowns from memory or assumptions. No measurements are pre-populated.

## Session and board identification

| Field | Record |
|---|---|
| Date / time / timezone | |
| Operator / lab | |
| Project/build ID or Git revision | |
| Board product/model as printed | |
| Board revision / serial or asset ID | |
| Board condition / photographs location | |
| Connector/cable configuration | |
| Power supply model and label output | |
| Power input used | |
| Vivado version and install path | |
| Official PYNQ-Z2 board definition present/version/path | |
| Selected board preset and selected device | |
| SD card label/capacity/image identity (no modification) | |
| Boot result / observation | |

## PYNQ software and configuration

| Field | Record |
|---|---|
| PYNQ image / release | |
| PYNQ package version | |
| Linux distribution / kernel | |
| Network/console access method | |
| Bitstream/project name and source | |
| FPGA programming result / log path | |
| PS preset / block design name | |
| `FCLK_CLK0` configured frequency | |
| Frequency verification method/report | |
| Reset IP / polarity / wiring notes | |
| `WINDOW_CYCLES` / `COUNTER_WIDTH` | |
| Snapshot observation method (ILA/software/other) | |

## Pulse source and input electrical observations

| Field | Record |
|---|---|
| Source make/model / output channel | |
| Source topology (push-pull/open-drain/etc.) | |
| Source schematic/datasheet reference | |
| Output load / impedance / current limit | |
| Pull-up value and voltage (if present) | |
| Ground/reference plan and review | |
| Selected board connector/pin (only after verification) | |
| FPGA bank / I/O standard / constraint reference | |
| Measured low level | |
| Measured high level | |
| Measured offset / overshoot / ringing | |
| Measured pulse high width / low width | |
| Measured duty cycle | |
| Input frequency / range tested | |
| Probe type, attenuation, scope and settings | |
| Scope screenshot path(s) | |

## Pulse-counter readings

| Trial | Input frequency | FCLK0 frequency | Window cycles | Expected count/window | Observed count | `snapshot_valid` observation | Pass/fail and notes |
|---|---:|---:|---:|---:|---:|---|---|
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |
| | | | | | | | |

## Test outcomes and failures

| Test/step | Expected observation | Actual observation | Result | Log/screenshot reference | Follow-up / failure detail |
|---|---|---|---|---|---|
| | | | | | |
| | | | | | |
| | | | | | |
| | | | | | |

## Sign-off / next actions

| Field | Record |
|---|---|
| Electrical review by / date | |
| Board/config review by / date | |
| Open blockers | |
| Approved next action | |
