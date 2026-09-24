"""
ERCOT F1 Compliance Checker
Band-pass filtering + rolling window analysis
"""

import numpy as np
from scipy.signal import butter, sosfilt
from config import parameters_F as pf
from config import parameters_E as pe



class ComplianceChecker:
    """Check ERCOT F1 compliance (10 MW peak-to-peak per 5s rolling window)"""
    
    def __init__(self):
        """Initialize with F1 parameters"""
        self.f1_limit_mw = pf.F1_TARGET_PEAK_TO_PEAK_MW  # 10 MW
        self.f1_freq_low = pf.F1_FREQUENCY_BAND_LOW_HZ   # 0.1 Hz
        self.f1_freq_high = pf.F1_FREQUENCY_BAND_HIGH_HZ # 55 Hz
        self.resolution_sec = pe.E1_COMPLIANCE_RESOLUTION_SEC  # 0.005s
        self.window_duration_sec = 5.0  # ERCOT standard
        
    def apply_bandpass_filter(self, power_fine_mw):
        """
        Apply Butterworth band-pass filter (0.1-55 Hz)
        
        Purpose: Remove DC drift and high-frequency noise while preserving
                 the load transients (0.1-55 Hz band contains grid transients)
        
        Args:
            power_fine_mw: Power array at fine resolution (0.005s, 200 Hz sampling)
        
        Returns:
            power_filtered: Band-pass filtered power (MW)
        """
        # Sampling frequency
        fs = 1.0 / self.resolution_sec  # 200 Hz
        
        # Design 4th-order Butterworth band-pass filter
        sos = butter(
            N=2,
            Wn=[self.f1_freq_low, self.f1_freq_high],
            btype='band',
            fs=fs,
            output='sos'
        )
        
        # Apply filter
        power_filtered = sosfilt(sos, power_fine_mw)
        
        return power_filtered
    
    def check_rolling_window(self, time_fine, power_filtered_mw):
        """
        Check peak-to-peak swing in each rolling 5-second window
        
        ERCOT F1: "Max power variation in any instantaneous 5-second 
                   rolling window shall not exceed 10 MW"
        
        Args:
            time_fine: Time array (seconds)
            power_filtered_mw: Band-pass filtered power (MW)
        
        Returns:
            tuple: (pass_fail, max_swing, violations list)
        """
        window_samples = int(self.window_duration_sec / self.resolution_sec)
        
        max_swing = 0.0
        violations = []
        
        # Check EVERY POSSIBLE rolling 5-second window
        for i in range(len(time_fine) - window_samples):
            window_power = power_filtered_mw[i:i+window_samples]
            swing = np.max(window_power) - np.min(window_power)
            
            if swing > max_swing:
                max_swing = swing
            
            # Flag violation if swing exceeds limit
            if swing > self.f1_limit_mw:
                violations.append({
                    'window_start_sec': time_fine[i],
                    'window_end_sec': time_fine[i+window_samples-1],
                    'swing_mw': swing,
                    'excess_mw': swing - self.f1_limit_mw
                })
        
        # PASS if no violations found
        pass_fail = len(violations) == 0
        
        return pass_fail, max_swing, violations
    
    def check_f1_compliance(self, time_fine, power_fine_mw):
        """
        Complete F1 compliance workflow: filter → check rolling windows
        
        Args:
            time_fine: Time array (seconds)
            power_fine_mw: Power array at fine resolution (0.005s, MW)
        
        Returns:
            dict: Compliance results with status, metrics, and violations
        """

        print("\n" + "="*70)
        print("STEP 0: CHECK RAW (UNFILTERED) WAVEFORM")
        print("="*70)
        
        # Raw signal stats
        raw_min = np.min(power_fine_mw)
        raw_max = np.max(power_fine_mw)
        raw_swing = raw_max - raw_min
        
        print(f"Raw waveform (BEFORE any filtering):")
        print(f"  Min: {raw_min:.2f} MW")
        print(f"  Max: {raw_max:.2f} MW")
        print(f"  Swing: {raw_swing:.2f} MW")
        
        # Check raw signal 5-second window
        window_samples = int(self.window_duration_sec / self.resolution_sec)
        raw_window = power_fine_mw[0:window_samples]
        raw_window_swing = np.max(raw_window) - np.min(raw_window)
        
        print(f"\nFirst 5-second window (raw):")
        print(f"  Swing in window: {raw_window_swing:.2f} MW")
        print("="*70 + "\n")
        # Step 1: Apply band-pass filter
        power_filtered = self.apply_bandpass_filter(power_fine_mw)
        
        # Step 2: Check rolling windows
        pass_fail, max_swing, violations = self.check_rolling_window(
            time_fine, power_filtered
        )
        
        # Compile results
        return {
            'compliance_status': 'PASS ✓' if pass_fail else 'FAIL ✗',
            'f1_limit_mw': self.f1_limit_mw,
            'f1_frequency_band_hz': (self.f1_freq_low, self.f1_freq_high),
            'max_swing_observed_mw': max_swing,
            'margin_mw': self.f1_limit_mw - max_swing,
            'window_duration_sec': self.window_duration_sec,
            'violation_count': len(violations),
            'violations': violations,
            'power_filtered': power_filtered,
        }


def print_compliance_report(results):
    """Print formatted ERCOT F1 compliance report"""
    
    print(f"\nERCOT F1 Standard (LCL - Load Change Limits):")
    print(f"  Metric:    Peak-to-peak variation in instantaneous power")
    print(f"  Limit:     ≤ {results['f1_limit_mw']} MW")
    print(f"  Window:    Every rolling 5-second interval")
    print(f"  Band:      {results['f1_frequency_band_hz'][0]}-{results['f1_frequency_band_hz'][1]} Hz (band-pass filtered)")
    
    print(f"\n✓ COMPLIANCE RESULT: {results['compliance_status']}")
    print(f"  Max swing observed:  {results['max_swing_observed_mw']:.2f} MW")
    print(f"  Limit:               {results['f1_limit_mw']:.2f} MW")
    print(f"  Safety margin:       {results['margin_mw']:.2f} MW")
    
    if results['violation_count'] == 0:
        print(f"\n✓ No violations found in any 5-second window")
    else:
        print(f"\n✗ Violations: {results['violation_count']} windows exceed F1 limit")
        print(f"\n  First 5 violations:")
        for i, v in enumerate(results['violations'][:5]):
            print(f"    {i+1}. Time {v['window_start_sec']:.1f}–{v['window_end_sec']:.1f}s: "
                  f"{v['swing_mw']:.2f} MW swing (excess: {v['excess_mw']:.2f} MW)")
        
        if len(results['violations']) > 5:
            print(f"    ... and {len(results['violations']) - 5} more violations")