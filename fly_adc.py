import numpy as np


# ============================================================
# Fly-Brain ADC
# Stage 1: Voltage -> normalized BioWire input drive
# ============================================================

def voltage_to_drive(voltage, v_min=0.0, v_max=1.0,
                     drive_min=0.30, drive_max=1.00):
    """
    Convert an analog input voltage into the BioWire ON-drive range.

    Voltage range:
        0 V -> drive_min
        1 V -> drive_max

    The current BioWire characterization showed that the network
    was silent below approximately 0.30 drive, so the useful
    neural operating range is currently taken as 0.30 to 1.00.
    """

    voltage = np.clip(voltage, v_min, v_max)

    drive = drive_min + (
        (voltage - v_min) / (v_max - v_min)
    ) * (drive_max - drive_min)

    return float(drive)


# ============================================================
# 6-bit ADC quantizer
# ============================================================

def quantize_6bit(value, v_min=0.0, v_max=1.0):
    """
    Convert a voltage-domain value into a 6-bit ADC code.
    """

    value = np.clip(value, v_min, v_max)

    code = round(
        (value - v_min) /
        (v_max - v_min) * 63
    )

    return int(code)

# ============================================================
# Fly-Brain spike-count decoder
# ============================================================

def spikes_to_drive(spike_count,
                    spike_min=22,
                    spike_max=222,
                    drive_min=0.30,
                    drive_max=1.00):
    """
    Convert total spike count back into the estimated
    BioWire input drive.

    Current calibration:
        ~22 spikes  -> 0.30 drive
        ~222 spikes -> 1.00 drive
    """

    spike_count = np.clip(spike_count, spike_min, spike_max)

    drive = drive_min + (
        (spike_count - spike_min) /
        (spike_max - spike_min)
    ) * (drive_max - drive_min)

    return float(drive)


def drive_to_voltage(drive,
                     drive_min=0.30,
                     drive_max=1.00,
                     v_min=0.0,
                     v_max=1.0):
    """
    Convert decoded BioWire drive back into voltage.
    """

    drive = np.clip(drive, drive_min, drive_max)

    voltage = v_min + (
        (drive - drive_min) /
        (drive_max - drive_min)
    ) * (v_max - v_min)

    return float(voltage)

# ============================================================
# Measured Fly-Brain calibration
# ============================================================

FLY_DRIVE_CAL = np.array([
    0.30, 0.32, 0.34, 0.36, 0.38, 0.40,
    0.42, 0.44, 0.46, 0.48, 0.50, 0.52,
    0.54, 0.56, 0.58, 0.60, 0.62, 0.64,
    0.66, 0.68, 0.70, 0.72, 0.74, 0.76,
    0.78, 0.80, 0.82, 0.84, 0.86, 0.88,
    0.90, 0.92, 0.94, 0.96, 0.98, 1.00
])

FLY_SPIKE_CAL = np.array([
     22,  33,  41,  49,  55,  61,
     67,  72,  78,  84,  90,  96,
    102, 107, 113, 116, 124, 128,
    132, 137, 143, 147, 152, 159,
    166, 173, 173, 180, 181, 189,
    200, 200, 210, 211, 222, 222
])


def calibrated_spikes_to_drive(spike_count):
    """
    Convert Fly-Brain spike count to drive using
    the experimentally measured BioWire transfer curve.
    """

    spike_count = np.clip(
        spike_count,
        FLY_SPIKE_CAL[0],
        FLY_SPIKE_CAL[-1]
    )

    return float(
        np.interp(
            spike_count,
            FLY_SPIKE_CAL,
            FLY_DRIVE_CAL
        )
    )