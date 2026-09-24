# config/parameters_F.py
"""
Cluster F: Battery Characteristics and Constraints
Sizing parameters for behind-the-meter energy storage
"""

# F1: Target Power Variation Limit (ERCOT Proposed Standard)
F1_TARGET_PEAK_TO_PEAK_MW = 10.0     # MW (max swing per 5s window)
F1_FREQUENCY_BAND_LOW_HZ = 0.1       # Hz (lower cutoff)
F1_FREQUENCY_BAND_HIGH_HZ = 55.0     # Hz (upper cutoff)
F1_ROLLING_WINDOW_SEC = 5.0          # seconds

# F2: PCS Response Time
F2_PCS_RESPONSE_TIME_MS = 10.0       # milliseconds (voltage ride-through)

# F3: Round-Trip Efficiency
F3_EFFICIENCY = 0.88  # 88% system-level (battery + PCS + transformer)

# F4: Usable State-of-Charge Window
F4_USABLE_SOC = 0.80  # 80% (10% to 90% operating range)
F4_SOC_MIN = 0.10
F4_SOC_MAX = 0.90

# F5: C-Rate Ceiling
F5_CRATE_CEILING = None  # No ceiling - report what's needed

# F6: Recharge Window / Swing Recurrence
F6_RECHARGE_EVENTS_PER_HOUR = 1.0  # Battery returns to target SOC

# F7: Degradation and Service Life
F7_DEGRADATION_FACTOR = 1.25  # 25% oversizing for end-of-life