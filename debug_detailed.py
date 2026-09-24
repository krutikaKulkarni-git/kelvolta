from core.waveform_generator import WaveformGenerator

gen = WaveformGenerator(gpu_count=71429)
time, power = gen.generate()
power_mw = power[:200] / 1e6  # First 20 seconds (200 samples)

print("First 20 seconds (detailed - every sample):")
for i in range(0, 200, 1):
    t = i * 0.1
    p = power_mw[i]
    
    # Print all samples to see the pattern
    if i % 10 == 0:
        print(f"\nTime {t:5.1f}s: {p:5.1f} MW", end="")
    else:
        print(f" | Time {t:5.1f}s: {p:5.1f} MW", end="")

print("\n\n" + "="*80)
print("Summary Statistics:")
print("="*80)
print(f"Min power: {power_mw.min():.1f} MW")
print(f"Max power: {power_mw.max():.1f} MW")
print(f"Avg power: {power_mw.mean():.1f} MW")

print(f"\nSamples at ~50 MW: {(power_mw > 48).sum()}")
print(f"Samples at ~25 MW: {((power_mw > 20) & (power_mw < 30)).sum()}")
print(f"Samples at ~12 MW: {(power_mw < 15).sum()}")

# Show pattern
print("\n" + "="*80)
print("Expected Pattern (C1=2s, C13=80%, C2_dip_duration=0.5s):")
print("="*80)
print("0-1.5s: HIGH (50 MW)")
print("1.5-2.0s: SYNC DIP (25 MW)")
print("2.0-3.5s: HIGH (50 MW)")
print("3.5-4.0s: SYNC DIP (25 MW)")
print("...")
print("\nCheckpoints start at iteration 100 (200s)")
