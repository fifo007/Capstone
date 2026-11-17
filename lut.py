import csv
from pathlib import Path

# Corrected EXP-56B results
csv_path = Path(
    r"C:\Users\sagni\OneDrive\Documents\capstone\biowire"
    r"\EXP56B_EXP49_decoder.csv"
)

output_path = csv_path.parent / "fly_adc_lut.mem"

if not csv_path.exists():
    raise FileNotFoundError(
        f"Cannot find corrected EXP-56B CSV:\n{csv_path}"
    )

with csv_path.open("r", newline="", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    rows = list(reader)

required = {"input_voltage_V", "exp49_adc_code_6bit"}

if not rows or not required.issubset(reader.fieldnames or []):
    raise ValueError(
        "CSV does not contain the expected EXP-56B columns. "
        f"Found: {reader.fieldnames}"
    )

# Sort by input voltage to preserve the transfer curve.
rows.sort(key=lambda row: float(row["input_voltage_V"]))

if len(rows) != 101:
    raise ValueError(f"Expected 101 rows, found {len(rows)}")

codes = [int(row["exp49_adc_code_6bit"]) for row in rows]

if any(code < 0 or code > 63 for code in codes):
    raise ValueError("An ADC code is outside the 6-bit range.")

if any(codes[i] < codes[i - 1] for i in range(1, len(codes))):
    raise ValueError("Codes are not monotonic. LUT not generated.")

# One 6-bit code per line, written as two-digit hexadecimal.
with output_path.open("w", encoding="ascii", newline="\n") as f:
    for code in codes:
        f.write(f"{code:02X}\n")

print("LUT generated successfully!")
print("File:", output_path)
print("Entries:", len(codes))
print("Code range:", min(codes), "to", max(codes))
print("Unique codes:", len(set(codes)), "/ 64")
print("First 10 codes:", codes[:10])
print("Last 10 codes:", codes[-10:])