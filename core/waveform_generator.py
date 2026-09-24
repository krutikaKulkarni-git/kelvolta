"""
CHS Phase 0 - Waveform Generator
Generates synthetic GPU training load profile based on measured/empirical parameters
Supports dual resolution: 0.1s (load shape) + 0.005s (compliance checking)
"""

import numpy as np
from scipy.signal import butter, sosfilt
from config import parameters_C as pc
from config import parameters_E as pe


class WaveformGenerator:
    """
    Generate synthetic GPU training load profile
    
    Models the power consumption pattern of AI data center GPUs:
    - Compute phases (high power)
    - Synchronization/communication phases (low power)
    - Optional checkpoint dips (if C7 available)
    
    Parameters from Cluster C:
      C1: Iteration period (seconds)
      C2: Synchronization dip depth (fraction of peak)
      C6: Checkpoint duration (seconds)
      C7: Checkpoint depth (fraction of peak) - UNRESOLVED
      C13: High-power duty cycle (fraction of iteration)
      C14: Transition/ramp duration (seconds)
    """
    
    def __init__(self, gpu_count, peak_power_per_gpu_w=1200, idle_power_per_gpu_w=100):
        """
        Initialize waveform generator for GB200 cluster
        
        Args:
            gpu_count: Number of GPUs in cluster (int)
            peak_power_per_gpu_w: Peak power per GPU in watts (default: 1200W GB200)
            idle_power_per_gpu_w: Idle power per GPU in watts (default: 100W)
        """
        self.gpu_count = gpu_count
        self.P_peak_gpu = peak_power_per_gpu_w
        self.P_idle_gpu = idle_power_per_gpu_w
        
        # Cluster-level powers (watts)
        self.P_peak_cluster = gpu_count * peak_power_per_gpu_w
        self.P_idle_cluster = gpu_count * idle_power_per_gpu_w
        
        # ===== CLUSTER C PARAMETERS =====
        # Iteration cycle parameters
        self.C1_iter_period = pc.C1_ITER_PERIOD_TYPICAL  # 2.0 seconds (typical)
        self.C2_swing_depth = pc.C2_SWING_DEFAULT        # 0.50 (50% dip)
        self.C13_duty_cycle = pc.C13_DUTY_CYCLE_DEFAULT  # 0.80 (80% at peak)
        
        # Checkpoint parameters (C7 is UNRESOLVED)
        self.C7_checkpoint_depth = pc.C7_CHECKPOINT_DEPTH  # None
        self.C6_checkpoint_duration = pc.C6_CHECKPOINT_DURATION_TYPICAL  # 3.0 seconds
        self.checkpoint_frequency_iters = pc.CHECKPOINT_FREQUENCY_ITERS  # 100
        
        # Transition/ramp parameters
        self.C14_transition_duration = pc.C14_TRANSITION_DURATION  # 0.5 seconds
        
    def generate_dual_resolution(self):
        """
        Generate waveform at TWO resolutions for different analysis purposes:
        
        1. COARSE (0.1s resolution, 10 Hz):
           - For load shape visualization
           - Fast computation
           - 864,000 samples for 24 hours
           
        2. FINE (0.005s resolution, 200 Hz):
           - For ERCOT F1 compliance checking
           - Captures transient behavior
           - 17.28 million samples for 24 hours
        
        Why two resolutions?
        - 0.1s is sufficient to see load behavior (iteration cycles)
        - 0.005s is needed for Nyquist sampling of 55 Hz band-pass filter
        - Computing only 0.005s for 24 hours would be slow
        - Approach: Generate both in parallel, use each appropriately
        
        Returns:
            tuple: (time_coarse, power_coarse, time_fine, power_fine)
                   - time arrays in seconds
                   - power arrays in watts
        """
        # Set random seed for reproducibility
        np.random.seed(pe.E5_RANDOM_SEED)
        
        # ===== COARSE RESOLUTION (0.1s) =====
        dt_coarse = pe.E1_LOAD_SHAPE_RESOLUTION_SEC  # 0.1s
        total_seconds = pe.E3_SIMULATED_DURATION_HOURS * 3600  # 86,400s for 24h
        time_coarse = np.arange(0, total_seconds, dt_coarse)
        power_coarse = self._generate_waveform_at_resolution(time_coarse)
        
        # ===== FINE RESOLUTION (0.005s) =====
        dt_fine = pe.E1_COMPLIANCE_RESOLUTION_SEC  # 0.005s (200 Hz sampling)
        time_fine = np.arange(0, total_seconds, dt_fine)
        power_fine = self._generate_waveform_at_resolution(time_fine)
        
        return time_coarse, power_coarse, time_fine, power_fine
    
    def _generate_waveform_at_resolution(self, time):
        """
        ╔══════════════════════════════════════════════════════════════════════╗
        ║                                                                      ║
        ║  CORE WAVEFORM GENERATION LOGIC                                      ║
        ║                                                                      ║
        ║  This is where the power array is ACTUALLY FILLED                   ║
        ║  based on the load model parameters (C1, C2, C6, C7, C13, C14)       ║
        ║                                                                      ║
        ╚══════════════════════════════════════════════════════════════════════╝
        
        For each time point, decide which phase of the GPU cycle we're in:
        
        Phase 1: COMPUTE (80% of cycle)
          - All GPUs compute
          - Power = peak (35.9 MW)
          
        Phase 2: SYNC/COMMUNICATION (20% of cycle, minus checkpoint)
          - GPUs synchronize gradients, reduce all-reduce
          - Power = peak × (1 - C2) = 35.9 × 0.5 = 17.97 MW (50% dip)
          
        Phase 3: CHECKPOINT (occasional, every 100 iterations)
          - Save model weights to disk
          - Power = peak × (1 - C7) = undefined (C7 UNRESOLVED)
          - Currently SKIPPED because C7 = None
        
        Args:
            time: Time array at desired resolution (seconds)
        
        Returns:
            power: Power array (watts) at each time point
        """
        power = np.zeros_like(time, dtype=float)
        
        # Loop through every time point
        for i, t in enumerate(time):
            # ===== DETERMINE POSITION IN ITERATION CYCLE =====
            # The iteration cycle repeats every C1 seconds (typically 2.0s)
            iter_phase = (t % self.C1_iter_period) / self.C1_iter_period  # 0 to 1
            time_in_iter = t % self.C1_iter_period  # 0 to 2.0 seconds
            
            # ===== DETERMINE WHICH ITERATION NUMBER =====
            iteration_number = int(t / self.C1_iter_period)
            is_checkpoint_iter = (iteration_number > 0) and \
                                 (iteration_number % self.checkpoint_frequency_iters == 0)
            
            # ===== WAVEFORM LOGIC - DETERMINE POWER AT THIS TIME POINT =====
            
            # CHECKPOINT PHASE (only if C7 is available - currently UNRESOLVED)
            # Checkpoints: save model weights every 100 iterations, last 3 seconds of iteration
            if is_checkpoint_iter and self.C7_checkpoint_depth is not None and \
               time_in_iter >= (self.C1_iter_period - self.C6_checkpoint_duration):
                swing = self.C7_checkpoint_depth * self.P_peak_cluster
                power[i] = self.P_peak_cluster - swing
                
            # COMMUNICATION/SYNC PHASE (last 0.5s of iteration, C2 dip)
            # Gradient synchronization via all-reduce collective
            elif time_in_iter >= (self.C1_iter_period - self.C14_transition_duration):
                swing = self.C2_swing_depth * self.P_peak_cluster
                power[i] = self.P_peak_cluster - swing
                
            # HIGH POWER PHASE (first 80% of iteration, C13 duty cycle)
            # Compute: forward pass, backward pass, weight update
            elif iter_phase < self.C13_duty_cycle:
                power[i] = self.P_peak_cluster
                
            # LOW POWER PHASE (20-80% of iteration, between compute and sync)
            # Communication/memory access phases, some GPUs idle
            else:
                swing = self.C2_swing_depth * self.P_peak_cluster
                power[i] = self.P_peak_cluster - swing
        
        return power
    
    def get_parameters_summary(self):
        """
        Return summary of load parameters used in waveform generation
        
        Useful for logging, validation, and documentation
        
        Returns:
            dict: Parameters used in this simulation
        """
        return {
            'C1_iter_period_sec': self.C1_iter_period,
            'C2_swing_depth_frac': self.C2_swing_depth,
            'C7_checkpoint_depth_frac': self.C7_checkpoint_depth,  # May be None
            'C13_duty_cycle_frac': self.C13_duty_cycle,
            'C6_checkpoint_duration_sec': self.C6_checkpoint_duration,
            'checkpoint_frequency_iters': self.checkpoint_frequency_iters,
            'C14_transition_duration_sec': self.C14_transition_duration,
            'platform': 'GB200 NVL72',
            'gpu_count': self.gpu_count,
            'peak_power_per_gpu_w': self.P_peak_gpu,
            'peak_power_mw': self.P_peak_cluster / 1e6,
            'idle_power_per_gpu_w': self.P_idle_gpu,
            'idle_power_mw': self.P_idle_cluster / 1e6,
        }


# ============================================================================
# WAVEFORM VALIDATION & DIAGNOSTICS (Optional)
# ============================================================================

def validate_waveform(time, power_mw, expected_peak_mw, expected_avg_mw):
    """
    Quick validation that waveform looks reasonable
    
    Args:
        time: Time array (seconds)
        power_mw: Power array (MW)
        expected_peak_mw: Expected peak power (MW) - for comparison
        expected_avg_mw: Expected average power (MW) - for comparison
    
    Returns:
        dict: Validation results
    """
    peak = np.max(power_mw)
    min_val = np.min(power_mw)
    avg = np.mean(power_mw)
    std = np.std(power_mw)
    
    peak_error_pct = abs(peak - expected_peak_mw) / expected_peak_mw * 100
    avg_error_pct = abs(avg - expected_avg_mw) / expected_avg_mw * 100
    
    return {
        'peak_mw': peak,
        'min_mw': min_val,
        'avg_mw': avg,
        'std_mw': std,
        'expected_peak_mw': expected_peak_mw,
        'expected_avg_mw': expected_avg_mw,
        'peak_error_pct': peak_error_pct,
        'avg_error_pct': avg_error_pct,
        'peak_valid': peak_error_pct < 5,  # Within 5%
        'avg_valid': avg_error_pct < 5,
    }