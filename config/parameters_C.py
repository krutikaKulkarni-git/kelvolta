# config/parameters_C.py
"""
Cluster C: Temporal Behavior at Chip Level
Load-shape parameters derived from H100/A100 measurements
Note: No measured GB200/GB300 temporal data available
"""

# C1: Iteration Period
C1_ITER_PERIOD_MIN = 1.0      # seconds (measured minimum)
C1_ITER_PERIOD_MAX = 10.0     # seconds (measured maximum)
C1_ITER_PERIOD_RANGE = (C1_ITER_PERIOD_MIN, C1_ITER_PERIOD_MAX)
C1_ITER_PERIOD_TYPICAL = 2.0  # seconds (scenario value for Phase 0)

# C2: Intra-Iteration Swing Depth (fraction of peak)
C2_SWING_LOW = 0.25   # RoBERTa scenario (A100)
C2_SWING_MID = 0.50   # GPT-NeoX scenario (A100)
C2_SWING_HIGH = 0.80  # Flan-T5 scenario (A100)
C2_SWING_SCENARIOS = [C2_SWING_LOW, C2_SWING_MID, C2_SWING_HIGH]
C2_SWING_DEFAULT = C2_SWING_MID  # Phase 0 baseline

# C6: Checkpoint Duration
C6_CHECKPOINT_DURATION_MIN = 1.0   # seconds (NVIDIA NeMo fast)
C6_CHECKPOINT_DURATION_MAX = 14.0  # seconds (PyTorch worst case)
C6_CHECKPOINT_DURATION_TYPICAL = 3.0  # seconds (Phase 0 scenario)

# C7: Checkpoint Power Drop Depth
C7_CHECKPOINT_DEPTH = None  # UNRESOLVED - no usable source found
# See: Li & Li measured 25-30A on single RTX 4090 with GPT-2 124M
# Cannot convert to production rack power fraction

# C13: High-Power Duty Cycle
C13_DUTY_CYCLE_TYPICAL = 0.80   # dense workload (Chaudhary)
C13_DUTY_CYCLE_MEASURED = 0.88  # H100 Llama-8B fine-tuning trace
C13_DUTY_CYCLE_DEFAULT = C13_DUTY_CYCLE_TYPICAL

# Checkpoint Frequency
CHECKPOINT_FREQUENCY_ITERS = 100  # Every 100 iterations

# Transition/Edge Duration (for waveform generation)
C14_TRANSITION_DURATION = 0.5  # seconds (rising/falling edge)