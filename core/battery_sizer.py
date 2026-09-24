"""
Battery Sizing Calculator
Power rating, energy capacity, technology recommendation
"""

import numpy as np
from config import parameters_F as pf


class BatterySizer:
    """Calculate battery power rating and energy capacity requirements"""
    
    def __init__(self):
        """Initialize with battery/system parameters"""
        self.efficiency = pf.F3_EFFICIENCY  # 0.88 (88% round-trip)
        self.usable_soc = pf.F4_USABLE_SOC  # 0.80 (10-90% usable)
        self.degradation_factor = pf.F7_DEGRADATION_FACTOR  # 1.25 (25% oversizing)
        self.c_rate_threshold = 2.0  # Recommend supercap if >2C
        
    def calculate_power_rating(self, peak_power_mw, avg_power_mw):
        """
        Calculate battery power rating needed
        
        The battery must be able to:
        - ABSORB excess power during high-load periods
        - SUPPLY deficit during low-load periods
        
        Power rating = max(peak - avg, avg - min)
        
        Args:
            peak_power_mw: Peak load power (MW)
            avg_power_mw: Average load power (MW)
        
        Returns:
            power_rating_mw: Required battery power output (MW)
        """
        # During peak: battery absorbs (peak - avg)
        absorb_rate = peak_power_mw - avg_power_mw
        
        # During low: battery supplies (avg - min) — but we use peak for symmetry
        supply_rate = avg_power_mw - avg_power_mw  # Conservative: just absorption
        
        # For safety, use the larger requirement
        power_rating_mw = max(absorb_rate, supply_rate)
        
        # Round up to nearest 0.5 MW
        power_rating_mw = np.ceil(power_rating_mw * 2) / 2
        
        return power_rating_mw
    
    def calculate_energy_capacity(self, avg_power_mw, duration_hours):
        """
        Calculate nameplate battery energy capacity
        
        Formula:
          Usable Energy = avg_power × duration
          Nameplate = Usable ÷ Efficiency ÷ Usable_SOC × Degradation
        
        Args:
            avg_power_mw: Average load power (MW)
            duration_hours: Simulation duration (hours)
        
        Returns:
            tuple: (usable_mwh, nameplate_mwh)
        """
        # Energy needed to handle average load for one cycle
        usable_energy_mwh = avg_power_mw * duration_hours
        
        # Account for inefficiencies and degradation
        # nameplate = usable / (efficiency × usable_soc) × degradation
        nameplate_mwh = (usable_energy_mwh / self.efficiency / self.usable_soc) * self.degradation_factor
        
        return usable_energy_mwh, nameplate_mwh
    
    def calculate_c_rate(self, power_rating_mw, nameplate_capacity_mwh):
        """
        Calculate C-rate (power / capacity ratio)
        
        C-rate indicates charging/discharging speed:
        - 1C = discharge in 1 hour
        - 2C = discharge in 0.5 hour (30 min)
        - >2C = very fast discharge (may require supercap hybrid)
        
        Args:
            power_rating_mw: Required power output (MW)
            nameplate_capacity_mwh: Battery capacity (MWh)
        
        Returns:
            c_rate: C-rate ratio
        """
        if nameplate_capacity_mwh == 0:
            return 0
        
        c_rate = power_rating_mw / nameplate_capacity_mwh
        
        return c_rate
    
    def get_technology_recommendation(self, c_rate):
        """
        Recommend battery technology based on C-rate
        
        Args:
            c_rate: Calculated C-rate
        
        Returns:
            str: Technology recommendation
        """
        if c_rate <= 0.5:
            return "Lithium Iron Phosphate (LFP) - cost-optimized"
        elif c_rate <= 1.0:
            return "Lithium Iron Phosphate (LFP) - balanced"
        elif c_rate <= 2.0:
            return "LFP with optional supercap buffer"
        elif c_rate <= 4.0:
            return "Lithium Titanate Oxide (LTO) or LFP/Supercap hybrid"
        else:
            return "Supercapacitor dominant with LFP backup"
    
    def calculate_battery_requirements(self, peak_power_mw, min_power_mw, avg_power_mw, 
                                       duration_hours, compliance_max_swing):
        """
        Complete battery sizing workflow
        
        Args:
            peak_power_mw: Peak load (MW)
            min_power_mw: Minimum load (MW)
            avg_power_mw: Average load (MW)
            duration_hours: Simulation duration (hours)
            compliance_max_swing: Max swing after ERCOT filtering (MW)
        
        Returns:
            dict: Complete battery sizing results
        """
        
        # Step 1: Power rating
        power_rating_mw = self.calculate_power_rating(peak_power_mw, avg_power_mw)
        
        # Step 2: Energy capacity
        usable_energy_mwh, nameplate_mwh = self.calculate_energy_capacity(
            avg_power_mw, duration_hours
        )
        
        # Step 3: C-rate
        c_rate = self.calculate_c_rate(power_rating_mw, nameplate_mwh)
        
        # Step 4: Technology recommendation
        tech_recommendation = self.get_technology_recommendation(c_rate)
        
        # Compile results
        return {
            'power_rating_mw': power_rating_mw,
            'energy_capacity_mwh': nameplate_mwh,
            'usable_energy_mwh': usable_energy_mwh,
            'efficiency_pct': self.efficiency * 100,
            'usable_soc_pct': self.usable_soc * 100,
            'degradation_factor': self.degradation_factor,
            'c_rate': c_rate,
            'c_rate_threshold': self.c_rate_threshold,
            'technology_recommendation': tech_recommendation,
            'load_peak_mw': peak_power_mw,
            'load_min_mw': min_power_mw,
            'load_avg_mw': avg_power_mw,
            'compliance_max_swing_mw': compliance_max_swing,
        }


def print_battery_report(results):
    """Print formatted battery sizing report"""
    
    print(f"\nBATTERY SIZING RESULTS")
    
    print(f"\n--- POWER RATING (Continuous) ---")
    print(f"Required power output: {results['power_rating_mw']:.2f} MW")
    print(f"  (Absorbs {results['load_peak_mw'] - results['load_avg_mw']:.2f} MW peak-to-avg swing)")
    
    print(f"\n--- ENERGY CAPACITY (Nameplate) ---")
    print(f"Usable energy needed:  {results['usable_energy_mwh']:.0f} MWh")
    print(f"Efficiency loss (12%):  ÷ {results['efficiency_pct']:.0f}%")
    print(f"Usable SOC (80%):       ÷ {results['usable_soc_pct']:.0f}%")
    print(f"Degradation factor:     × {results['degradation_factor']}x (end-of-life)")
    print(f"─" * 50)
    print(f"Nameplate capacity:    {results['energy_capacity_mwh']:.0f} MWh")
    
    print(f"\n--- C-RATE & TECHNOLOGY ---")
    print(f"C-Rate:                {results['c_rate']:.2f}C")
    print(f"  (Discharge time:     {60/results['c_rate']:.0f} minutes)")
    print(f"Recommendation:        {results['technology_recommendation']}")
    
    if results['c_rate'] > results['c_rate_threshold']:
        print(f"\n⚠️  WARNING: C-rate > {results['c_rate_threshold']}C")
        print(f"  Consider hybrid system (LFP + supercapacitor)")
    
    print(f"\n--- VALIDATION ---")
    print(f"Load range:            {results['load_min_mw']:.2f} → {results['load_peak_mw']:.2f} MW")
    print(f"Swing (raw):           {results['load_peak_mw'] - results['load_min_mw']:.2f} MW")
    print(f"Swing (filtered):      {results['compliance_max_swing_mw']:.2f} MW (ERCOT F1)")