import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import os

# =================================================
# FIXED NEURAL ADC SETTINGS
# =================================================

BITS = 6
LEVELS = 2 ** BITS

NUM_NEURONS = 8
SIGMA = 0.08
THRESHOLD = 0.40

# Dense sweep
test_voltages = np.linspace(0, 1, 101)

excel_filename = "adc_results.xlsx"


# =================================================
# STORAGE
# =================================================

sweep_results = []


# =================================================
# NEURAL ADC
# =================================================

preferred_voltage = np.linspace(
    0, 1, NUM_NEURONS
)

digital_codes = []
quantized_voltages = []


for voltage in test_voltages:

    # -----------------------------------------
    # Neural activity
    # -----------------------------------------

    activity = np.exp(
        -((voltage - preferred_voltage) ** 2)
        / (2 * SIGMA ** 2)
    )

    # -----------------------------------------
    # Spike generation
    # -----------------------------------------

    spikes = (
        activity >= THRESHOLD
    ).astype(float)

    # -----------------------------------------
    # Spike-based decoding
    # -----------------------------------------

    numerator = np.sum(
        spikes * preferred_voltage
    )

    denominator = np.sum(spikes)

    if denominator > 0:
        decoded_voltage = (
            numerator / denominator
        )
    else:
        decoded_voltage = 0.0

    # -----------------------------------------
    # Quantization
    # -----------------------------------------

    digital_code = round(
        decoded_voltage * (LEVELS - 1)
    )

    quantized_voltage = (
        digital_code / (LEVELS - 1)
    )

    digital_codes.append(
        digital_code
    )

    quantized_voltages.append(
        quantized_voltage
    )


digital_codes = np.array(
    digital_codes
)

quantized_voltages = np.array(
    quantized_voltages
)


# =================================================
# MONOTONICITY ANALYSIS
# =================================================

code_differences = np.diff(
    digital_codes
)

# A negative difference means the output
# went backwards while the input increased.

violations = np.where(
    code_differences < 0
)[0]

num_violations = len(
    violations
)

is_monotonic = (
    num_violations == 0
)


# =================================================
# FIND WORST VIOLATION
# =================================================

if num_violations > 0:

    worst_index = violations[
        np.argmin(
            code_differences[violations]
        )
    ]

    worst_drop = (
        digital_codes[worst_index]
        - digital_codes[worst_index + 1]
    )

else:

    worst_index = None
    worst_drop = 0


# =================================================
# STORE DETAILED DATA
# =================================================

for i, voltage in enumerate(
    test_voltages
):

    if i == 0:
        previous_code = np.nan
        code_change = np.nan
        violation = False

    else:
        previous_code = (
            digital_codes[i - 1]
        )

        code_change = (
            digital_codes[i]
            - digital_codes[i - 1]
        )

        violation = (
            code_change < 0
        )

    sweep_results.append({

        "Input Voltage (V)": voltage,

        "Digital Code":
            digital_codes[i],

        "Quantized Voltage (V)":
            quantized_voltages[i],

        "Previous Code":
            previous_code,

        "Code Change":
            code_change,

        "Monotonicity Violation":
            violation
    })


# =================================================
# SUMMARY
# =================================================

summary = {

    "Resolution (bits)": BITS,

    "Neurons": NUM_NEURONS,

    "Sigma": SIGMA,

    "Threshold": THRESHOLD,

    "Input Points": len(
        test_voltages
    ),

    "Monotonic":
        is_monotonic,

    "Number of Violations":
        num_violations,

    "Worst Code Drop":
        worst_drop
}


summary_df = pd.DataFrame(
    [summary]
)

details_df = pd.DataFrame(
    sweep_results
)


# =================================================
# PRINT RESULTS
# =================================================

print()
print("======================================")
print("ADC MONOTONICITY ANALYSIS")
print("======================================")

print(
    f"Resolution: {BITS} bits"
)

print(
    f"Neurons: {NUM_NEURONS}"
)

print(
    f"Sigma: {SIGMA}"
)

print(
    f"Threshold: {THRESHOLD}"
)

print()

print(
    f"Monotonic: {is_monotonic}"
)

print(
    f"Number of violations: "
    f"{num_violations}"
)

print(
    f"Worst code drop: "
    f"{worst_drop}"
)


# =================================================
# UPDATE EXCEL
# =================================================

if os.path.exists(
    excel_filename
):

    with pd.ExcelWriter(
        excel_filename,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace"
    ) as writer:

        summary_df.to_excel(
            writer,
            sheet_name="Monotonicity_Summary",
            index=False
        )

        details_df.to_excel(
            writer,
            sheet_name="Monotonicity_Details",
            index=False
        )

else:

    with pd.ExcelWriter(
        excel_filename,
        engine="openpyxl"
    ) as writer:

        summary_df.to_excel(
            writer,
            sheet_name="Monotonicity_Summary",
            index=False
        )

        details_df.to_excel(
            writer,
            sheet_name="Monotonicity_Details",
            index=False
        )


print()
print("======================================")
print("EXCEL UPDATED")
print("======================================")

print(
    f"Saved to: {excel_filename}"
)


# =================================================
# PLOT
# =================================================

plt.figure(
    figsize=(8, 5)
)

plt.step(
    test_voltages,
    digital_codes,
    where="post"
)

plt.xlabel(
    "Input Voltage (V)"
)

plt.ylabel(
    "Digital Code"
)

plt.title(
    "Neural ADC Monotonicity"
)

plt.grid()

plt.show()

# =================================================
# ENOB ANALYSIS
# =================================================

print()
print("======================================")
print("ADC ENOB ANALYSIS")
print("======================================")

# -------------------------------------------------
# ENOB TEST SETTINGS
# -------------------------------------------------

N = 8192

# Number of complete sine-wave cycles in the sample window.
# Using an integer number avoids spectral leakage.
NUM_CYCLES = 37

# Sine-wave amplitude and DC offset
AMPLITUDE = 0.45
OFFSET = 0.50

# Sampling index
n = np.arange(N)

# Input sine wave
input_signal = (
    OFFSET
    + AMPLITUDE
    * np.sin(
        2 * np.pi * NUM_CYCLES * n / N
    )
)

# -------------------------------------------------
# RUN NEURAL ADC
# -------------------------------------------------

enob_codes = []

for voltage in input_signal:

    # Neural activity
    activity = np.exp(
        -((voltage - preferred_voltage) ** 2)
        / (2 * SIGMA ** 2)
    )

    # Spike generation
    spikes = (
        activity >= THRESHOLD
    ).astype(float)

    # Spike-based decoding
    numerator = np.sum(
        spikes * preferred_voltage
    )

    denominator = np.sum(spikes)

    if denominator > 0:
        decoded_voltage = (
            numerator / denominator
        )
    else:
        decoded_voltage = 0.0

    # 6-bit quantization
    digital_code = round(
        decoded_voltage * (LEVELS - 1)
    )

    # Keep code inside valid ADC range
    digital_code = np.clip(
        digital_code,
        0,
        LEVELS - 1
    )

    enob_codes.append(
        digital_code
    )

enob_codes = np.array(
    enob_codes,
    dtype=float
)

# -------------------------------------------------
# REMOVE DC COMPONENT
# -------------------------------------------------

codes_ac = (
    enob_codes
    - np.mean(enob_codes)
)

# -------------------------------------------------
# FFT
# -------------------------------------------------

fft_result = np.fft.rfft(
    codes_ac
)

frequencies = np.fft.rfftfreq(
    N,
    d=1.0
)

power_spectrum = (
    np.abs(fft_result) ** 2
)

# -------------------------------------------------
# FUNDAMENTAL BIN
# -------------------------------------------------

fundamental_bin = NUM_CYCLES

fundamental_power = (
    power_spectrum[fundamental_bin]
)

# -------------------------------------------------
# TOTAL NON-FUNDAMENTAL POWER
# -------------------------------------------------

# Start with all AC spectral power
total_ac_power = np.sum(
    power_spectrum[1:]
)

# Remove fundamental
noise_distortion_power = (
    total_ac_power
    - fundamental_power
)

# Prevent numerical problems
noise_distortion_power = max(
    noise_distortion_power,
    1e-20
)

# -------------------------------------------------
# SINAD
# -------------------------------------------------

SINAD = 10 * np.log10(
    fundamental_power
    / noise_distortion_power
)

# -------------------------------------------------
# ENOB
# -------------------------------------------------

ENOB = (
    SINAD - 1.76
) / 6.02

# -------------------------------------------------
# SNR
# -------------------------------------------------

# For this experiment, everything except the
# fundamental is treated as noise + distortion.
SNR = SINAD

# -------------------------------------------------
# PRINT RESULTS
# -------------------------------------------------

print()
print(
    f"Resolution: {BITS} bits"
)

print(
    f"Neurons: {NUM_NEURONS}"
)

print(
    f"Sigma: {SIGMA}"
)

print(
    f"Threshold: {THRESHOLD}"
)

print(
    f"FFT samples: {N}"
)

print(
    f"Sine cycles: {NUM_CYCLES}"
)

print()

print(
    f"SINAD: {SINAD:.4f} dB"
)

print(
    f"ENOB: {ENOB:.4f} bits"
)

# -------------------------------------------------
# SAVE ENOB RESULTS TO EXCEL
# -------------------------------------------------

enob_summary = {

    "Resolution (bits)": BITS,

    "Neurons": NUM_NEURONS,

    "Sigma": SIGMA,

    "Threshold": THRESHOLD,

    "FFT Samples": N,

    "Sine Cycles": NUM_CYCLES,

    "Amplitude (V)": AMPLITUDE,

    "DC Offset (V)": OFFSET,

    "Fundamental Bin": fundamental_bin,

    "SINAD (dB)": SINAD,

    "ENOB (bits)": ENOB
}

enob_summary_df = pd.DataFrame(
    [enob_summary]
)

# -------------------------------------------------
# FFT DATA
# -------------------------------------------------

spectrum_df = pd.DataFrame({

    "Frequency Bin":
        np.arange(len(frequencies)),

    "Normalized Frequency":
        frequencies,

    "FFT Magnitude":
        np.abs(fft_result),

    "Power":
        power_spectrum
})

# -------------------------------------------------
# UPDATE EXCEL
# -------------------------------------------------

if os.path.exists(
    excel_filename
):

    with pd.ExcelWriter(
        excel_filename,
        engine="openpyxl",
        mode="a",
        if_sheet_exists="replace"
    ) as writer:

        enob_summary_df.to_excel(
            writer,
            sheet_name="ENOB_Summary",
            index=False
        )

        spectrum_df.to_excel(
            writer,
            sheet_name="ENOB_Spectrum",
            index=False
        )

else:

    with pd.ExcelWriter(
        excel_filename,
        engine="openpyxl"
    ) as writer:

        enob_summary_df.to_excel(
            writer,
            sheet_name="ENOB_Summary",
            index=False
        )

        spectrum_df.to_excel(
            writer,
            sheet_name="ENOB_Spectrum",
            index=False
        )

print()
print("======================================")
print("ENOB RESULTS SAVED")
print("======================================")

print(
    f"Saved to: {excel_filename}"
)

# -------------------------------------------------
# PLOT FFT
# -------------------------------------------------

plt.figure(
    figsize=(9, 5)
)

plt.plot(
    frequencies,
    10 * np.log10(
        power_spectrum + 1e-20
    )
)

plt.xlabel(
    "Frequency Bin / Normalized Frequency"
)

plt.ylabel(
    "Power (dB)"
)

plt.title(
    "Neural ADC FFT Spectrum"
)

plt.grid()

plt.show()