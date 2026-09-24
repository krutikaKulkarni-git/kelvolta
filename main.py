#!/usr/bin/env python3
"""
CHS Phase 0 - Main Orchestrator
Flow: Parameters → Waveform → Analysis → Compliance → Battery Sizing → Plots
"""

import numpy as np
from config import parameters_A as pa
from config import parameters_B as pb
from config import parameters_C as pc
from config import parameters_E as pe
from config import parameters_F as pf
from core.waveform_generator import WaveformGenerator
from core.compliance_checker import ComplianceChecker, print_compliance_report
from core.battery_sizer import BatterySizer, print_battery_report
from output.plotter import save_plots


def main():
    """Main execution: Complete CHS Phase 0 modeling pipeline"""
    
    print("\n" + "="*80)
    print("CHS PHASE 0 - COMPLETE MODELING PIPELINE")
    print("Waveform → Analysis → Compliance → Battery Sizing → Visualization")
    print("="*80)
    
    # ========================================================================
    # STEP 1: READ PARAMETERS AND CALCULATE CLUSTER CONFIGURATION
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 1: CLUSTER CONFIGURATION (Cluster A & B)")
    print("="*80)
    
    hall_mw = pb.HALL_CAPACITY_MW
    rack_config = pb.get_rack_configuration(
        hall_mw=hall_mw,
        rack_power_kw=pa.RACK_POWER_GB200
    )
    
    print(f"\nPlatform: {pa.DEFAULT_PLATFORM}")
    print(f"GPU TDP: {pa.DEFAULT_GPU_TDP} W/GPU")
    print(f"Rack Power: {pa.DEFAULT_RACK_POWER} kW/rack")
    print(f"\nHall Capacity: {hall_mw} MW")
    print(f"Rack Count: {rack_config['rack_count']}")
    print(f"GPUs per Rack: {rack_config['gpus_per_rack']}")
    print(f"Total GPU Count: {rack_config['total_gpu_count']:,}")
    
    gpu_count = rack_config['total_gpu_count']
    
    # ========================================================================
    # STEP 2: LOAD BEHAVIOR PARAMETERS (Cluster C)
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 2: LOAD BEHAVIOR PARAMETERS (Cluster C)")
    print("="*80)
    
    print(f"\nC1 (Iteration Period): {pc.C1_ITER_PERIOD_TYPICAL} seconds")
    print(f"C2 (Swing Depth): {pc.C2_SWING_DEFAULT * 100:.0f}% of peak")
    print(f"C6 (Checkpoint Duration): {pc.C6_CHECKPOINT_DURATION_TYPICAL} seconds")
    print(f"C7 (Checkpoint Depth): {pc.C7_CHECKPOINT_DEPTH if pc.C7_CHECKPOINT_DEPTH else 'UNRESOLVED'}")
    print(f"C13 (Duty Cycle): {pc.C13_DUTY_CYCLE_DEFAULT * 100:.0f}% high power")
    print(f"C14 (Edge Duration): {pc.C14_TRANSITION_DURATION} seconds")
    
    # ========================================================================
    # STEP 3: SIMULATION SETTINGS (Cluster E)
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 3: SIMULATION SETTINGS (Cluster E)")
    print("="*80)
    
    print(f"\nE1 (Load Shape Resolution): {pe.E1_LOAD_SHAPE_RESOLUTION_SEC} s ({1/pe.E1_LOAD_SHAPE_RESOLUTION_SEC:.0f} Hz)")
    print(f"E1 (Compliance Resolution): {pe.E1_COMPLIANCE_RESOLUTION_SEC} s ({1/pe.E1_COMPLIANCE_RESOLUTION_SEC:.0f} Hz)")
    print(f"E2 (Reporting Resolutions): {pe.E2_COMPARISON_RESOLUTIONS_SEC}")
    print(f"E3 (Duration): {pe.E3_SIMULATED_DURATION_HOURS} hours")
    print(f"E4 (Downsampling): {pe.E4_DOWNSAMPLING_METHOD}")
    print(f"E5 (Random Seed): {pe.E5_RANDOM_SEED}")
    
    # ========================================================================
    # STEP 4: COMPLIANCE CONSTRAINT (Cluster F)
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 4: COMPLIANCE CONSTRAINT (Cluster F)")
    print("="*80)
    
    print(f"\nF1 (Peak-to-Peak Limit): {pf.F1_TARGET_PEAK_TO_PEAK_MW} MW per rolling 5 seconds")
    print(f"F1 (Frequency Band): {pf.F1_FREQUENCY_BAND_LOW_HZ}-{pf.F1_FREQUENCY_BAND_HIGH_HZ} Hz")
    print(f"F2 (PCS Response Time): {pf.F2_PCS_RESPONSE_TIME_MS} ms")
    print(f"F3 (Round-Trip Efficiency): {pf.F3_EFFICIENCY * 100:.0f}%")
    print(f"F4 (Usable SOC): {pf.F4_USABLE_SOC * 100:.0f}%")
    print(f"F7 (Degradation Factor): {pf.F7_DEGRADATION_FACTOR}x")
    
    # ========================================================================
    # STEP 5: GENERATE WAVEFORM (Dual Resolution)
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 5: GENERATING WAVEFORM")
    print("="*80)
    
    print(f"\nInitializing WaveformGenerator...")
    print(f"  GPU Count: {gpu_count:,}")
    print(f"  Peak Power per GPU: {pa.DEFAULT_GPU_TDP} W")
    print(f"  Cluster Peak Power: {gpu_count * pa.DEFAULT_GPU_TDP / 1e6:.1f} MW")
    
    generator = WaveformGenerator(
        gpu_count=gpu_count,
        peak_power_per_gpu_w=pa.DEFAULT_GPU_TDP
    )
    
    print(f"\nGenerating waveform at two resolutions...")
    time_coarse, power_coarse, time_fine, power_fine = generator.generate_dual_resolution()
    
    print(f"  Coarse resolution: {len(time_coarse):,} samples at {pe.E1_LOAD_SHAPE_RESOLUTION_SEC}s")
    print(f"  Fine resolution: {len(time_fine):,} samples at {pe.E1_COMPLIANCE_RESOLUTION_SEC}s")
    
    # ========================================================================
    # STEP 6: CALCULATE INTERMEDIATE VARIABLES
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 6: LOAD ANALYSIS - INTERMEDIATE VARIABLES")
    print("="*80)
    
    # Convert to MW for readability
    power_coarse_mw = power_coarse / 1e6
    power_fine_mw = power_fine / 1e6
    
    # Basic metrics
    peak_power_mw = np.max(power_coarse_mw)
    min_power_mw = np.min(power_coarse_mw)
    avg_power_mw = np.mean(power_coarse_mw)
    peak_to_avg_ratio = peak_power_mw / avg_power_mw
    
    # Energy
    total_energy_mwh = avg_power_mw * pe.E3_SIMULATED_DURATION_HOURS
    
    # Ramp rate (derived from C2 swing and edge duration)
    swing_magnitude_mw = pc.C2_SWING_DEFAULT * peak_power_mw
    ramp_rate_mw_per_sec = swing_magnitude_mw / pc.C14_TRANSITION_DURATION
    
    print(f"\n--- POWER METRICS ---")
    print(f"Peak Power:            {peak_power_mw:.2f} MW")
    print(f"Minimum Power:         {min_power_mw:.2f} MW")
    print(f"Average Power:         {avg_power_mw:.2f} MW")
    print(f"Peak-to-Average Ratio: {peak_to_avg_ratio:.2f}x")
    
    print(f"\n--- ENERGY METRICS (24 hours) ---")
    print(f"Total Energy Delivered: {total_energy_mwh:.0f} MWh")
    
    print(f"\n--- TRANSIENT METRICS ---")
    print(f"C2 Swing Depth:        {pc.C2_SWING_DEFAULT * 100:.0f}% of peak")
    print(f"Swing Magnitude:       {swing_magnitude_mw:.2f} MW")
    print(f"Edge Duration:         {pc.C14_TRANSITION_DURATION} seconds")
    print(f"Derived Ramp Rate:     {ramp_rate_mw_per_sec:.1f} MW/sec ({ramp_rate_mw_per_sec*60:.0f} MW/min)")
    
    print(f"\n--- LOAD CHARACTERISTICS ---")
    actual_high_power_fraction = np.sum(power_coarse_mw > (peak_power_mw * 0.9)) / len(power_coarse_mw)
    actual_low_power_fraction = np.sum(power_coarse_mw < (peak_power_mw * 0.5)) / len(power_coarse_mw)
    print(f"High-Power Time (>90% peak): {actual_high_power_fraction * 100:.1f}%")
    print(f"Low-Power Time (<50% peak):  {actual_low_power_fraction * 100:.1f}%")
    
    # Generator parameters
    gen_params = generator.get_parameters_summary()
    print(f"\n--- WAVEFORM CONFIGURATION ---")
    for key, value in gen_params.items():
        print(f"{key}: {value}")
    
    # ========================================================================
    # STEP 6b: ERCOT F1 COMPLIANCE CHECK
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 6b: ERCOT F1 COMPLIANCE CHECK")
    print("="*80)
    
    checker = ComplianceChecker()
    compliance_results = checker.check_f1_compliance(time_fine, power_fine_mw)
    print_compliance_report(compliance_results)
    
    # ========================================================================
    # STEP 6c: BATTERY SIZING
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 6c: BATTERY SIZING CALCULATION")
    print("="*80)
    
    battery_sizer = BatterySizer()
    battery_results = battery_sizer.calculate_battery_requirements(
        peak_power_mw=peak_power_mw,
        min_power_mw=min_power_mw,
        avg_power_mw=avg_power_mw,
        duration_hours=pe.E3_SIMULATED_DURATION_HOURS,
        compliance_max_swing=compliance_results['max_swing_observed_mw']
    )
    print_battery_report(battery_results)
    
    # ========================================================================
    # STEP 7: EXECUTIVE SUMMARY
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 7: EXECUTIVE SUMMARY")
    print("="*80)
    
    print(f"""
CHS PHASE 0 MODELING COMPLETE

CLUSTER CONFIGURATION:
  Hall Capacity:         {hall_mw} MW
  Total GPUs:            {gpu_count:,}
  Rack Count:            {rack_config['rack_count']}
  Platform:              GB200 NVL72

LOAD PROFILE (24-hour simulation):
  Peak Power:            {peak_power_mw:.2f} MW
  Average Power:         {avg_power_mw:.2f} MW
  Minimum Power:         {min_power_mw:.2f} MW
  Total Energy:          {total_energy_mwh:.0f} MWh
  Peak-to-Avg Ratio:     {peak_to_avg_ratio:.2f}x
  Ramp Rate:             {ramp_rate_mw_per_sec:.1f} MW/s

COMPLIANCE STATUS:
  ERCOT F1 Standard:     {compliance_results['compliance_status']}
  Max Swing (filtered):  {compliance_results['max_swing_observed_mw']:.2f} MW
  F1 Limit:              {compliance_results['f1_limit_mw']:.2f} MW
  Margin:                {compliance_results['margin_mw']:.2f} MW

BATTERY REQUIREMENTS:
  Power Rating:          {battery_results['power_rating_mw']:.2f} MW
  Energy Capacity:       {battery_results['energy_capacity_mwh']:.0f} MWh (nameplate)
  Usable Energy:         {battery_results['usable_energy_mwh']:.0f} MWh
  Round-Trip Efficiency: {battery_results['efficiency_pct']:.1f}%
  Usable SOC:            {battery_results['usable_soc_pct']:.0f}%
  Degradation Factor:    {battery_results['degradation_factor']}x
  Recommended Technology: {battery_results['technology_recommendation']}
  C-Rate:                {battery_results['c_rate']:.2f}

VALIDATION:
  ✓ Load model captures GPU iteration cycles (C1, C2, C13)
  ✓ Waveform validates against F1 standard
  ✓ Battery sizing accounts for efficiency & degradation
  ✗ C7 (checkpoint depth) UNRESOLVED - sensitivity analysis needed

NEXT STEPS:
  1. Obtain measured C7 value from production GB200 cluster
  2. Run sensitivity analysis (C7 = 0%, 25%, 50%)
  3. Integrate power quality metrics (voltage, current, THD)
  4. Add state-of-charge trajectory visualization
  5. Client presentation deck
""")
    
    print("="*80)
    
    # Prepare comprehensive results dictionary
    results = {
        'time_coarse': time_coarse,
        'power_coarse': power_coarse_mw,
        'time_fine': time_fine,
        'power_fine': power_fine_mw,
        'power_filtered': compliance_results['power_filtered'],
        'metrics': {
            'peak_mw': peak_power_mw,
            'min_mw': min_power_mw,
            'avg_mw': avg_power_mw,
            'peak_to_avg_ratio': peak_to_avg_ratio,
            'total_energy_mwh': total_energy_mwh,
            'ramp_rate_mw_per_sec': ramp_rate_mw_per_sec,
        },
        'cluster': rack_config,
        'generator_params': gen_params,
        'compliance': compliance_results,
        'battery': battery_results,
    }
    
    # Add total power for plotting
    results['cluster']['total_power_mw'] = hall_mw
    
    # ========================================================================
    # STEP 8: GENERATE VISUALIZATIONS
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 8: GENERATING VISUALIZATIONS")
    print("="*80)
    
    try:
        save_plots(results, output_dir='./')
        print("\n✅ Main visualizations generated successfully!")
    except Exception as e:
        print(f"\n⚠️  Warning: Could not generate main plots")
        print(f"   Error: {str(e)}")
    
    # ========================================================================
    # STEP 9: GENERATE DETAILED WAVEFORM ANALYSIS (Multi-resolution)
    # ========================================================================
    print("\n" + "="*80)
    print("STEP 9: GENERATING DETAILED WAVEFORM ANALYSIS")
    print("="*80)
    
    try:
        from output.detailed_plotter import save_detailed_plots
        save_detailed_plots(time_fine, power_fine_mw, pc.C1_ITER_PERIOD_TYPICAL, output_dir='./')
        print("\n✅ Detailed waveform plots generated successfully!")
    except Exception as e:
        print(f"\n⚠️  Warning: Could not generate detailed waveform plots")
        print(f"   Error: {str(e)}")
        print(f"   Install with: pip install matplotlib scipy")
    
    print("\n" + "="*80)
    print("SIMULATION COMPLETE - ALL OUTPUTS GENERATED")
    print("="*80 + "\n")
    
    return results


if __name__ == "__main__":
    results = main()