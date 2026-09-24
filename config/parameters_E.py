# config/parameters_E.py
"""
Cluster E: Simulation Settings
Controls waveform generation, filtering, and resampling
"""

# E1: Generation and Evaluation Resolution
# TWO RESOLUTIONS REQUIRED:
E1_LOAD_SHAPE_RESOLUTION_SEC = 0.1      # 0.1s (10 Hz) for load-shape analysis
E1_COMPLIANCE_RESOLUTION_SEC = 0.005    # 0.005s (200 Hz) for F1 compliance
# Reason: F1 requires 0.1-55 Hz content, needs >110 Hz sampling (Nyquist)

# E2: Comparison Resolutions (for resampling/reporting ONLY)
E2_COMPARISON_RESOLUTIONS_SEC = [1, 5, 60, 300, 900]  # 1s, 5s, 1min, 5min, 15min

# E3: Simulated Duration
E3_SIMULATED_DURATION_HOURS = 24  # 24 hours

# E4: Downsampling Method
E4_DOWNSAMPLING_METHOD = "mean"  # How to aggregate fine resolution to coarse

# E5: Determinism (Reproducibility)
E5_RANDOM_SEED = 42  # Fixed seed for reproducible results
E5_DOCUMENT_SEED = True  # Always log it in outputs