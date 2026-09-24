# debug.py
from core.waveform_generator import WaveformGenerator

# Create generator
gen = WaveformGenerator(gpu_count=71429)

# Generate waveform
time, power = gen.generate()

# Look at first 100 samples (first 10 seconds)
power_mw = power[:100] / 1e6

print("First 100 samples (10 seconds):")
for i in range(0, 100, 10):
    print(f"Time {i*0.1:.1f}s: {power_mw[i]:.1f} MW")

# Also check specific ranges
print(f"\nMin power: {power_mw.min():.1f} MW")
print(f"Max power: {power_mw.max():.1f} MW")
print(f"Avg power: {power_mw.mean():.1f} MW")

# Count how many samples at each level
print(f"\nSamples at ~50 MW: {(power_mw > 48).sum()}")
print(f"Samples at ~25 MW: {((power_mw > 20) & (power_mw < 30)).sum()}")
print(f"Samples at ~12 MW: {(power_mw < 15).sum()}")