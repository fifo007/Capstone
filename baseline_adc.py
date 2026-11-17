import numpy as np
import matplotlib.pyplot as plt

# -------------------------------------------------
# 1. Generate synthetic analog input
# -------------------------------------------------
np.random.seed(42)

t = np.linspace(0, 1, 1000)

# Clean analog signal: 0 to 1 V sine wave
clean_signal = 0.5 + 0.45 * np.sin(2 * np.pi * 3 * t)

# Add Gaussian noise
noise_std = 0.05
noise = np.random.normal(0, noise_std, len(t))
noisy_signal = clean_signal + noise

# Clamp to valid 0-1 V range
noisy_signal = np.clip(noisy_signal, 0, 1)

# -------------------------------------------------
# 2. Population of "neurons"
# -------------------------------------------------
NUM_NEURONS = 16

# Each neuron is tuned to a different voltage level
preferred_voltage = np.linspace(0, 1, NUM_NEURONS)

# Width of each neuron's response
sigma = 0.08

# Activity matrix:
# rows = neurons
# columns = time
activity = np.zeros((NUM_NEURONS, len(t)))

for i in range(NUM_NEURONS):
    activity[i] = np.exp(
        -((noisy_signal - preferred_voltage[i]) ** 2)
        / (2 * sigma ** 2)
    )

# -------------------------------------------------
# 3. Convert neural activity to spikes
# -------------------------------------------------
threshold = 0.6

spikes = (activity > threshold).astype(int)

# -------------------------------------------------
# 4. Decode neural population activity
# -------------------------------------------------
# Weighted population decoding
numerator = np.sum(
    activity * preferred_voltage[:, None],
    axis=0
)

denominator = np.sum(activity, axis=0) + 1e-9

decoded_signal = numerator / denominator

# -------------------------------------------------
# 5. Quantize to 6-bit ADC
# -------------------------------------------------
BITS = 6
LEVELS = 2 ** BITS

digital_code = np.round(
    decoded_signal * (LEVELS - 1)
).astype(int)

quantized_voltage = digital_code / (LEVELS - 1)

# -------------------------------------------------
# 6. Calculate errors
# -------------------------------------------------
mae = np.mean(np.abs(clean_signal - quantized_voltage))
rmse = np.sqrt(
    np.mean((clean_signal - quantized_voltage) ** 2)
)

print("--------------------------------")
print("Neuromorphic ADC Proof-of-Concept")
print("--------------------------------")
print("Neurons:", NUM_NEURONS)
print("Resolution:", BITS, "bits")
print("Quantization levels:", LEVELS)
print("Noise STD:", noise_std)
print("Mean Absolute Error:", round(mae, 4))
print("RMSE:", round(rmse, 4))

# -------------------------------------------------
# 7. Plot clean vs noisy signal
# -------------------------------------------------
plt.figure(figsize=(10, 5))

plt.plot(t, clean_signal, label="Clean Analog Signal")
plt.plot(t, noisy_signal, alpha=0.5, label="Noisy Analog Signal")

plt.xlabel("Time")
plt.ylabel("Voltage")
plt.title("Analog Input with Noise")
plt.legend()
plt.grid()

plt.tight_layout()
plt.show()

# -------------------------------------------------
# 8. Plot neural activity
# -------------------------------------------------
plt.figure(figsize=(10, 6))

plt.imshow(
    activity,
    aspect="auto",
    origin="lower",
    extent=[t[0], t[-1], 0, NUM_NEURONS]
)

plt.colorbar(label="Neuron Activity")
plt.xlabel("Time")
plt.ylabel("Neuron Index")
plt.title("Population Neural Activity")

plt.tight_layout()
plt.show()

# -------------------------------------------------
# 9. Plot spike raster
# -------------------------------------------------
plt.figure(figsize=(10, 6))

for neuron in range(NUM_NEURONS):

    spike_times = t[spikes[neuron] == 1]

    plt.scatter(
        spike_times,
        np.ones_like(spike_times) * neuron,
        s=2
    )

plt.xlabel("Time")
plt.ylabel("Neuron Index")
plt.title("Neural Spike Raster")
plt.grid()

plt.tight_layout()
plt.show()

# -------------------------------------------------
# 10. Compare decoded result
# -------------------------------------------------
plt.figure(figsize=(10, 5))

plt.plot(
    t,
    clean_signal,
    label="Original Analog Signal"
)

plt.step(
    t,
    quantized_voltage,
    label="Neuromorphic ADC Output",
    where="mid"
)

plt.xlabel("Time")
plt.ylabel("Voltage")
plt.title("Original vs Neural ADC Reconstruction")
plt.legend()
plt.grid()

plt.tight_layout()
plt.show()

# -------------------------------------------------
# 11. Show digital ADC code
# -------------------------------------------------
plt.figure(figsize=(10, 5))

plt.step(
    t,
    digital_code,
    where="mid"
)

plt.xlabel("Time")
plt.ylabel("Digital Code")
plt.title("6-bit Digital Output")
plt.grid()

plt.tight_layout()
plt.show()