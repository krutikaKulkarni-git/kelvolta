# core/intermediate_variables.py
"""
Intermediate variables calculated during waveform generation
These bridge inputs (parameters) to outputs (battery sizing)
"""

class IntermediateVariables:
    """Container for intermediate calculation results"""
    
    def __init__(self):
        # Time array
        self.time = None                # Time points [0, dt, 2*dt, ..., T]
        self.time_compliance = None     # Fine resolution [0, 0.005, 0.01, ...]
        
        # Power arrays
        self.power = None               # Raw instantaneous power (watts)
        self.power_compliance = None    # At 0.005s resolution for F1 check
        self.power_filtered = None      # Band-pass filtered (0.1-55 Hz)
        
        # Waveform metrics
        self.peak_power_w = None        # Max power (watts)
        self.min_power_w = None         # Min power (watts)
        self.avg_power_w = None         # Average power (watts)
        self.peak_to_avg_ratio = None   # Peak / Average
        
        # Load characteristics
        self.duty_cycle_actual = None   # Actual high-power fraction
        self.swing_depth_actual = None  # Actual swing (fraction of peak)
        self.ramp_rate_mw_per_sec = None  # Rising/falling ramp rate
        
        # Compliance analysis
        self.rolling_window_p2p = None  # Peak-to-peak per 5s window
        self.worst_case_p2p_mw = None   # Max p2p across all windows
        self.p2p_exceeding_limit = None # Which windows exceed F1 limit
        
        # Resampled versions (for sensitivity analysis)
        self.power_resampled = {}       # Dict: {resolution: power_array}
        self.time_resampled = {}        # Dict: {resolution: time_array}