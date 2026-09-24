#!/usr/bin/env python3
"""
Kelvolta CHS Phase 1: Generate Monitoring Metric Previews

This standalone script generates 5 publication-quality graphs:
  1. Power Quality Metrics (voltage, current, PF, THD, frequency)
  2. Load Duration Curve (duty cycle validation)
  3. Battery SOC Projection (daily solar cycle)
  4. Battery SOH Degradation (15-year fade)
  5. System Monitoring Diagram (sensor placement)

Usage:
  python monitoring_metrics_generator.py --output ./plots/

Generated files:
  - power_quality_metrics.png
  - load_duration_curve.png
  - soc_projection.png
  - soh_projection.png
  - monitoring_system_diagram.png

Author: Krutika Kulkarni (Kelvolta CHS)
Date: September 2026
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
import argparse
import os
from pathlib import Path


# ============================================================================
# CONFIGURATION: Adjust these to match your actual parameters
# ============================================================================

class CHS_Config:
    """Central configuration for all CHS parameters"""
    
    # Power profile parameters (from your waveform model)
    POWER_PEAK = 35.94  # MW (36 MW all GPUs computing)
    POWER_MIN = 17.97   # MW (18 MW all GPUs syncing)
    POWER_AVG = 31.45   # MW (average over 24h)
    DUTY_CYCLE_HIGH = 0.80  # 80% time at peak
    ITERATION_PERIOD = 2.0  # seconds
    RAMP_TIME = 0.5  # seconds
    
    # Battery parameters (from sizing calculation)
    BATTERY_CAPACITY_MWH = 1343  # MWh nameplate
    BATTERY_USABLE_SOC = 0.80    # 80% usable window (10-90%)
    ROUNDTRIP_EFFICIENCY = 0.88  # 88% round-trip
    POWER_RATING = 4.49  # MW continuous
    
    # Grid parameters (ERCOT)
    GRID_VOLTAGE_NOMINAL = 220.0  # kV
    GRID_FREQUENCY_NOMINAL = 60.0  # Hz
    ERCOT_THD_LIMIT = 0.05  # 5% max
    ERCOT_FREQ_MIN = 59.95  # Hz
    ERCOT_FREQ_MAX = 60.05  # Hz
    
    # Degradation parameters (LFP battery)
    CYCLES_PER_YEAR = 365
    DEGRADATION_PER_CYCLE = 0.05  # 0.05% per cycle
    SOH_WARRANTY_END = 0.80  # 80% SOH at year 10
    SOH_END_OF_LIFE = 0.70  # 70% SOH end-of-life
    
    # Simulation resolution
    RESOLUTION_SEC = 0.1  # seconds (10 Hz)
    DURATION_HOURS = 24  # 24-hour cycle


# ============================================================================
# WAVEFORM GENERATION
# ============================================================================

def generate_waveform_24h(config=CHS_Config(), resolution_sec=None):
    """
    Generate 24-hour synthetic power profile
    
    Returns:
        time_array: Time in seconds
        power_array: Power in MW
    """
    if resolution_sec is None:
        resolution_sec = config.RESOLUTION_SEC
    
    duration_sec = config.DURATION_HOURS * 3600
    num_samples = int(duration_sec / resolution_sec)
    time_array = np.arange(num_samples) * resolution_sec
    power_array = np.zeros(num_samples)
    
    cycle_period = config.ITERATION_PERIOD
    for i, t in enumerate(time_array):
        cycle_pos = (t % cycle_period) / cycle_period
        
        # High power phase
        if cycle_pos < config.DUTY_CYCLE_HIGH:
            ramp_prog = min(cycle_pos / 0.1, 1.0)
            power_array[i] = config.POWER_MIN + (config.POWER_PEAK - config.POWER_MIN) * ramp_prog
        else:
            # Transition to low power
            transition_start = config.DUTY_CYCLE_HIGH
            transition_end = config.DUTY_CYCLE_HIGH + (config.RAMP_TIME / cycle_period)
            
            if cycle_pos < transition_end:
                ramp_prog = (cycle_pos - transition_start) / (transition_end - transition_start)
                power_array[i] = config.POWER_PEAK - (config.POWER_PEAK - config.POWER_MIN) * ramp_prog
            else:
                power_array[i] = config.POWER_MIN
    
    return time_array, power_array


# ============================================================================
# POWER QUALITY DATA GENERATION
# ============================================================================

def generate_power_quality_data(power_array, config=CHS_Config(), resolution_sec=None):
    """Generate realistic power quality metrics"""
    if resolution_sec is None:
        resolution_sec = config.RESOLUTION_SEC
    
    time_array = np.arange(len(power_array)) * resolution_sec
    
    # Voltage (220V nominal, ±2% variation based on power)
    v_nominal = config.GRID_VOLTAGE_NOMINAL
    v_sag = (power_array / config.POWER_PEAK) * 2.0
    vrms = v_nominal - v_sag + np.random.normal(0, 0.5, len(power_array))
    
    # Current (P = V × I)
    arms = (power_array * 1e6) / (vrms * np.sqrt(3))
    
    # Power Factor (varies with load)
    pf_base = 0.98 - (power_array / config.POWER_PEAK) * 0.08
    pf = np.clip(pf_base + np.random.normal(0, 0.01, len(power_array)), 0.85, 1.0)
    
    # THD (higher during transitions)
    transitions = np.abs(np.diff(power_array)) > 0.5
    transitions = np.concatenate([[False], transitions])
    thd = np.where(transitions,
                   3.5 + np.random.normal(0, 0.3, len(power_array)),
                   2.2 + np.random.normal(0, 0.2, len(power_array)))
    thd = np.clip(thd, 1.5, 5.0)
    
    # Frequency (60 Hz nominal)
    frequency = config.GRID_FREQUENCY_NOMINAL + np.random.normal(0, 0.02, len(power_array))
    frequency = np.clip(frequency, config.ERCOT_FREQ_MIN, config.ERCOT_FREQ_MAX)
    
    return time_array, vrms, arms, pf, thd, frequency


# ============================================================================
# LOAD DURATION CURVE
# ============================================================================

def generate_load_duration_data(power_array):
    """Generate load duration curve from power profile"""
    
    bin_width = 0.5  # MW
    bins = np.arange(0, 37, bin_width)
    
    hist, bin_edges = np.histogram(power_array, bins=bins)
    total = np.sum(hist)
    pct = (hist / total) * 100
    
    cumulative_pct = np.cumsum(pct[::-1])[::-1]
    
    return bin_edges[:-1], pct, cumulative_pct


# ============================================================================
# SOC PROJECTION
# ============================================================================

def generate_soc_projection(config=CHS_Config()):
    """Project SOC over 24 hours with solar forecast"""
    
    # Typical sunny day solar forecast (Texas)
    solar_profile = np.array([
        0, 0, 0, 0, 0, 0,           # Night
        2, 8, 18, 35, 50, 58,       # Morning rise
        60, 58, 55, 50, 42, 30,     # Afternoon
        15, 5, 0, 0, 0, 0           # Evening/night
    ])
    
    dc_demand = np.full(24, config.POWER_AVG)
    
    soc = config.BATTERY_USABLE_SOC / 2  # Start at 50% for demo
    soc_trajectory = [soc]
    
    for hour in range(24):
        net_power = solar_profile[hour] - dc_demand[hour]
        energy_change = net_power * 1.0  # MWh per hour
        
        if energy_change > 0:
            actual_change = energy_change * config.ROUNDTRIP_EFFICIENCY
        else:
            actual_change = energy_change / config.ROUNDTRIP_EFFICIENCY
        
        soc_change = actual_change / config.BATTERY_CAPACITY_MWH
        soc = np.clip(soc + soc_change, 0.10, 0.90)
        soc_trajectory.append(soc)
    
    return solar_profile, dc_demand, np.array(soc_trajectory)


# ============================================================================
# SOH PROJECTION
# ============================================================================

def generate_soh_projection(years=15, config=CHS_Config()):
    """Project SOH over multiple years"""
    
    year_array = []
    soh_array = []
    
    for year in range(years + 1):
        cumulative_cycles = year * config.CYCLES_PER_YEAR
        soh = 100 - (cumulative_cycles * config.DEGRADATION_PER_CYCLE)
        soh = max(70, soh)
        
        year_array.append(year)
        soh_array.append(soh)
    
    return np.array(year_array), np.array(soh_array)


# ============================================================================
# PLOTTING FUNCTIONS
# ============================================================================

def plot_power_quality_metrics(config=CHS_Config(), output_path='power_quality_metrics.png'):
    """Generate 5-panel power quality plot"""
    
    # Generate 1 hour of data at 1 Hz
    time_1h, power_1h = generate_waveform_24h(config, resolution_sec=1.0)
    time_1h = time_1h[:3600]
    power_1h = power_1h[:3600]
    time_1h_min = time_1h / 60
    
    _, vrms, arms, pf, thd, frequency = generate_power_quality_data(power_1h, config, resolution_sec=1.0)
    
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(3, 2, figure=fig, hspace=0.35, wspace=0.25)
    
    # Power reference
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(time_1h_min, power_1h, 'b-', linewidth=2, label='Power')
    ax1.axhline(y=config.POWER_PEAK, color='r', linestyle='--', alpha=0.5, label=f'Peak ({config.POWER_PEAK:.2f} MW)')
    ax1.axhline(y=config.POWER_MIN, color='g', linestyle='--', alpha=0.5, label=f'Min ({config.POWER_MIN:.2f} MW)')
    ax1.set_ylabel('Power (MW)', fontsize=11, fontweight='bold')
    ax1.set_title('POWER QUALITY METRICS - 1 Hour Window', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3)
    ax1.legend(loc='upper right')
    ax1.set_xlim([0, 60])
    
    # Voltage
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.plot(time_1h_min, vrms, 'purple', linewidth=1.5, alpha=0.7)
    ax2.axhline(y=220, color='k', linestyle='-', alpha=0.3)
    ax2.axhspan(198, 242, alpha=0.1, color='green')
    ax2.set_ylabel('Voltage (V RMS)', fontsize=10, fontweight='bold')
    ax2.set_title('RMS Voltage (Vrms)', fontsize=11, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim([190, 260])
    ax2.set_xlim([0, 60])
    
    # Current
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.plot(time_1h_min, arms / 1000, 'darkblue', linewidth=1.5, alpha=0.7)
    ax3.set_ylabel('Current (kA)', fontsize=10, fontweight='bold')
    ax3.set_title('RMS Current (Arms)', fontsize=11, fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.set_xlim([0, 60])
    
    # Power Factor
    ax4 = fig.add_subplot(gs[2, 0])
    ax4.plot(time_1h_min, pf, 'darkorange', linewidth=1.5, alpha=0.7)
    ax4.axhline(y=1.0, color='k', linestyle='-', alpha=0.3)
    ax4.axhline(y=0.95, color='g', linestyle='--', alpha=0.5, label='Good (>0.95)')
    ax4.axhline(y=0.90, color='orange', linestyle='--', alpha=0.5)
    ax4.axhline(y=0.80, color='r', linestyle='--', alpha=0.5)
    ax4.axhspan(0.95, 1.0, alpha=0.1, color='green')
    ax4.set_ylabel('Power Factor', fontsize=10, fontweight='bold')
    ax4.set_title('Power Factor (PF)', fontsize=11, fontweight='bold')
    ax4.grid(True, alpha=0.3)
    ax4.set_ylim([0.75, 1.05])
    ax4.set_xlim([0, 60])
    ax4.legend(fontsize=8)
    
    # THD
    ax5 = fig.add_subplot(gs[2, 1])
    ax5.plot(time_1h_min, thd, 'darkred', linewidth=1.5, alpha=0.7)
    ax5.axhline(y=3.0, color='g', linestyle='--', alpha=0.5, label='Good (<3%)')
    ax5.axhline(y=5.0, color='r', linestyle='--', alpha=0.5, label='ERCOT limit (<5%)')
    ax5.axhspan(0, 3, alpha=0.1, color='green')
    ax5.axhspan(3, 5, alpha=0.1, color='yellow')
    ax5.axhspan(5, 8, alpha=0.1, color='red')
    ax5.set_ylabel('THD (%)', fontsize=10, fontweight='bold')
    ax5.set_xlabel('Time (minutes)', fontsize=10, fontweight='bold')
    ax5.set_title('Total Harmonic Distortion (THD)', fontsize=11, fontweight='bold')
    ax5.grid(True, alpha=0.3)
    ax5.set_ylim([0, 8])
    ax5.set_xlim([0, 60])
    ax5.legend(fontsize=8)
    
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()


def plot_load_duration_curve(config=CHS_Config(), output_path='load_duration_curve.png'):
    """Generate load duration curve"""
    
    time_24h, power_24h = generate_waveform_24h(config, resolution_sec=10.0)
    bin_centers, pct, cumulative_pct = generate_load_duration_data(power_24h)
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    
    # Histogram
    bars = ax1.bar(bin_centers, pct, width=0.4, alpha=0.7, color='steelblue', edgecolor='black', linewidth=1.5)
    
    for i, bar in enumerate(bars):
        if 35 <= bin_centers[i] <= 36:
            bar.set_color('darkgreen')
        elif 17 <= bin_centers[i] <= 18:
            bar.set_color('darkorange')
    
    ax1.axvline(x=config.POWER_PEAK, color='r', linestyle='--', linewidth=2, alpha=0.6, label=f'Peak ({config.POWER_PEAK:.2f} MW)')
    ax1.axvline(x=config.POWER_MIN, color='g', linestyle='--', linewidth=2, alpha=0.6, label=f'Min ({config.POWER_MIN:.2f} MW)')
    ax1.set_xlabel('Power (MW)', fontsize=11, fontweight='bold')
    ax1.set_ylabel('% of Time', fontsize=11, fontweight='bold')
    ax1.set_title('Power Distribution (Histogram)', fontsize=12, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.legend(fontsize=10)
    ax1.set_xlim([0, 36])
    
    # Cumulative
    ax2.plot(bin_centers, cumulative_pct, 'b-', linewidth=2.5, marker='o', markersize=4, label='Load duration')
    ax2.axhline(y=80, color='r', linestyle='--', linewidth=2, alpha=0.6, label='80% duty cycle')
    ax2.axvline(x=35, color='purple', linestyle=':', linewidth=2, alpha=0.5)
    ax2.fill_between(bin_centers, 0, cumulative_pct, alpha=0.2, color='steelblue')
    ax2.set_xlabel('Power (MW)', fontsize=11, fontweight='bold')
    ax2.set_ylabel('% Time at or Above', fontsize=11, fontweight='bold')
    ax2.set_title('Load Duration Curve (Cumulative)', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.legend(fontsize=10)
    ax2.set_xlim([0, 36])
    ax2.set_ylim([0, 105])
    
    plt.suptitle('LOAD DURATION CURVE - 24 Hour Period', fontsize=13, fontweight='bold', y=1.02)
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()


def plot_soc_projection(config=CHS_Config(), output_path='soc_projection.png'):
    """Generate SOC trajectory plot"""
    
    solar_profile, dc_demand, soc_trajectory = generate_soc_projection(config)
    
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 9))
    
    hours = np.arange(25)
    
    # Solar and demand
    ax1.bar(hours[:-1], solar_profile, width=0.9, alpha=0.6, color='gold', edgecolor='darkorange', linewidth=1.5, label='Solar')
    ax1.plot(hours[:-1], dc_demand, 'b-', linewidth=3, marker='s', markersize=6, label='DC Demand', zorder=5)
    ax1.axvspan(-0.5, 6, alpha=0.15, color='blue')
    ax1.axvspan(18, 24.5, alpha=0.15, color='blue')
    ax1.set_ylabel('Power (MW)', fontsize=11, fontweight='bold')
    ax1.set_xlabel('Hour of Day', fontsize=11, fontweight='bold')
    ax1.set_title('BATTERY SOC PROJECTION - Sunny Day', fontsize=13, fontweight='bold')
    ax1.grid(True, alpha=0.3, axis='y')
    ax1.set_xlim([-0.5, 24.5])
    ax1.set_ylim([0, 70])
    ax1.legend(fontsize=10, loc='upper left')
    
    # SOC trajectory
    ax2.plot(hours, soc_trajectory * 100, 'g-', linewidth=3, marker='o', markersize=5, label='SOC', zorder=5)
    ax2.axhline(y=90, color='r', linestyle='--', linewidth=2, alpha=0.6, label='Max usable (90%)')
    ax2.axhline(y=10, color='b', linestyle='--', linewidth=2, alpha=0.6, label='Min usable (10%)')
    ax2.axhspan(10, 90, alpha=0.1, color='green', label='Safe window')
    ax2.axhspan(0, 10, alpha=0.1, color='red')
    ax2.axhspan(90, 100, alpha=0.1, color='red')
    ax2.axvspan(-0.5, 6, alpha=0.15, color='blue')
    ax2.axvspan(18, 24.5, alpha=0.15, color='blue')
    ax2.set_ylabel('State of Charge (%)', fontsize=11, fontweight='bold')
    ax2.set_xlabel('Hour of Day', fontsize=11, fontweight='bold')
    ax2.set_title('Battery SOC Trajectory', fontsize=12, fontweight='bold')
    ax2.grid(True, alpha=0.3)
    ax2.set_xlim([-0.5, 24.5])
    ax2.set_ylim([0, 105])
    ax2.legend(fontsize=10, loc='upper right')
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()


def plot_soh_projection(config=CHS_Config(), output_path='soh_projection.png'):
    """Generate SOH degradation plot"""
    
    years, soh = generate_soh_projection(15, config)
    
    fig, ax = plt.subplots(figsize=(12, 7))
    
    ax.plot(years, soh, 'b-o', linewidth=3, markersize=8, label='SOH projection', zorder=5)
    ax.axhline(y=80, color='r', linestyle='--', linewidth=2, alpha=0.6, label='Warranty end (80%)')
    ax.axhline(y=70, color='orange', linestyle='--', linewidth=2, alpha=0.6, label='End-of-life (70%)')
    ax.axhspan(70, 80, alpha=0.1, color='orange', label='Replacement window')
    ax.axhspan(80, 100, alpha=0.1, color='green', label='Normal operation')
    ax.axhspan(0, 70, alpha=0.1, color='red')
    
    ax.set_xlabel('Years', fontsize=12, fontweight='bold')
    ax.set_ylabel('State of Health (%)', fontsize=12, fontweight='bold')
    ax.set_title('BATTERY SOH DEGRADATION PROJECTION\nLFP Chemistry: 20,000 cycle lifespan', 
                fontsize=13, fontweight='bold')
    ax.grid(True, alpha=0.3)
    ax.set_xlim([-0.5, 15.5])
    ax.set_ylim([65, 105])
    ax.legend(fontsize=10, loc='upper right')
    
    # Annotations
    for year in [0, 5, 10, 15]:
        if year <= 15:
            ax.plot(year, soh[year], 'o', markersize=10, color='darkblue', zorder=6)
            ax.text(year, soh[year]-6, f'{soh[year]:.1f}%\nYear {year}', 
                   ha='center', fontsize=9, fontweight='bold',
                   bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()


def plot_monitoring_diagram(config=CHS_Config(), output_path='monitoring_system_diagram.png'):
    """Generate system monitoring diagram"""
    
    fig, ax = plt.subplots(figsize=(14, 9))
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)
    ax.axis('off')
    
    # Title
    ax.text(5, 9.5, 'Battery Energy Storage System - Monitoring Points', 
           ha='center', fontsize=14, fontweight='bold')
    
    # Grid
    grid_box = mpatches.FancyBboxPatch((0.2, 6.5), 1.5, 1.2, 
                                       boxstyle="round,pad=0.1", 
                                       edgecolor='black', facecolor='lightyellow', linewidth=2)
    ax.add_patch(grid_box)
    ax.text(0.95, 7.1, 'ERCOT Grid\n220 kV', ha='center', va='center', fontsize=10, fontweight='bold')
    
    # Battery
    battery_box = mpatches.FancyBboxPatch((3.0, 2.0), 2.0, 1.8, 
                                          boxstyle="round,pad=0.1", 
                                          edgecolor='darkgreen', facecolor='lightgreen', linewidth=3)
    ax.add_patch(battery_box)
    ax.text(4.0, 3.2, 'BATTERY\n1,343 MWh LFP', ha='center', va='center', 
           fontsize=11, fontweight='bold', color='darkgreen')
    
    # GPU
    gpu_box = mpatches.FancyBboxPatch((6.5, 2.0), 2.0, 1.8, 
                                       boxstyle="round,pad=0.1", 
                                       edgecolor='purple', facecolor='plum', linewidth=3)
    ax.add_patch(gpu_box)
    ax.text(7.5, 3.2, '50 MW Data Center\nGPU Cluster', ha='center', va='center', 
           fontsize=11, fontweight='bold', color='darkviolet')
    
    # Converters
    converter_box = mpatches.FancyBboxPatch((0.1, 2.4), 1.8, 1.0, 
                                            boxstyle="round,pad=0.05", 
                                            edgecolor='darkred', facecolor='lightyellow', linewidth=2)
    ax.add_patch(converter_box)
    ax.text(1.0, 2.9, 'Converter\nAC↔DC', ha='center', va='center', fontsize=10, fontweight='bold', color='darkred')
    
    # PQ Meters (as text boxes)
    pq1 = mpatches.FancyBboxPatch((0.05, 5.2), 1.9, 0.9, 
                                  boxstyle="round,pad=0.05", 
                                  edgecolor='darkblue', facecolor='lightblue', linewidth=2, linestyle='--')
    ax.add_patch(pq1)
    ax.text(1.0, 5.65, '⊙ PQ METER #1\nVrms, Arms, PF, THD, f', 
           ha='center', va='center', fontsize=9, fontweight='bold', color='darkblue')
    
    pq2 = mpatches.FancyBboxPatch((0.05, 1.3), 1.9, 0.7, 
                                  boxstyle="round,pad=0.05", 
                                  edgecolor='darkblue', facecolor='lightblue', linewidth=2, linestyle='--')
    ax.add_patch(pq2)
    ax.text(1.0, 1.67, '⊙ PQ METER #2\nConverter output', 
           ha='center', va='center', fontsize=8, fontweight='bold', color='darkblue')
    
    # BMS
    bms_box = mpatches.FancyBboxPatch((3.2, 0.8), 1.6, 0.8, 
                                      boxstyle="round,pad=0.05", 
                                      edgecolor='darkgreen', facecolor='lightgreen', linewidth=2, linestyle='--')
    ax.add_patch(bms_box)
    ax.text(4.0, 1.2, '⊙ BMS Logger\nSOC, SOH, Temp', 
           ha='center', va='center', fontsize=8, fontweight='bold', color='darkgreen')
    
    # GPU Logger
    gpu_log = mpatches.FancyBboxPatch((6.5, 0.8), 2.0, 0.8, 
                                      boxstyle="round,pad=0.05", 
                                      edgecolor='purple', facecolor='plum', linewidth=2, linestyle='--')
    ax.add_patch(gpu_log)
    ax.text(7.5, 1.2, '⊙ Power Logger\nAI workload power', 
           ha='center', va='center', fontsize=8, fontweight='bold', color='darkviolet')
    
    # Info box
    info_text = f"""MONITORING ARCHITECTURE
    
Measurement Points: 5 locations (Grid, Converter ×2, Battery, GPUs)
Logging Frequency: 10 Hz (PQ) | 5 Hz (Converter) | 1 Hz (BMS/GPU)
Data Storage: InfluxDB time-series (cloud or local)
Dashboard: Grafana real-time visualization
Retention: 1 year detailed, 5 years summary
Battery Capacity: {config.BATTERY_CAPACITY_MWH} MWh LFP
Power Rating: {config.POWER_RATING} MW continuous"""
    
    ax.text(5, 0.05, info_text, ha='center', va='bottom', fontsize=8.5, family='monospace',
           bbox=dict(boxstyle='round', facecolor='lightyellow', alpha=0.9, pad=0.8))
    
    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches='tight')
    print(f"✓ Saved: {output_path}")
    plt.close()


# ============================================================================
# MAIN
# ============================================================================

def main():
    parser = argparse.ArgumentParser(description='Generate CHS Phase 1 monitoring metrics')
    parser.add_argument('--output', type=str, default='./', help='Output directory')
    parser.add_argument('--prefix', type=str, default='', help='Filename prefix')
    args = parser.parse_args()
    
    # Create output directory
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    config = CHS_Config()
    
    print("=" * 80)
    print("KELVOLTA CHS PHASE 1: GENERATING MONITORING METRIC PREVIEWS")
    print("=" * 80)
    print()
    
    print(f"Configuration:")
    print(f"  Power Peak: {config.POWER_PEAK} MW")
    print(f"  Power Min: {config.POWER_MIN} MW")
    print(f"  Power Avg: {config.POWER_AVG} MW")
    print(f"  Duty Cycle: {config.DUTY_CYCLE_HIGH*100:.0f}% high / {(1-config.DUTY_CYCLE_HIGH)*100:.0f}% low")
    print(f"  Battery Capacity: {config.BATTERY_CAPACITY_MWH} MWh")
    print(f"  Output Directory: {output_dir}")
    print()
    
    prefix = f"{args.prefix}_" if args.prefix else ""
    
    print("1. Generating Power Quality Metrics...")
    plot_power_quality_metrics(config, str(output_dir / f"{prefix}power_quality_metrics.png"))
    print()
    
    print("2. Generating Load Duration Curve...")
    plot_load_duration_curve(config, str(output_dir / f"{prefix}load_duration_curve.png"))
    print()
    
    print("3. Generating SOC Projection...")
    plot_soc_projection(config, str(output_dir / f"{prefix}soc_projection.png"))
    print()
    
    print("4. Generating SOH Degradation...")
    plot_soh_projection(config, str(output_dir / f"{prefix}soh_projection.png"))
    print()
    
    print("5. Generating System Monitoring Diagram...")
    plot_monitoring_diagram(config, str(output_dir / f"{prefix}monitoring_system_diagram.png"))
    print()
    
    print("=" * 80)
    print("✓ ALL PLOTS GENERATED SUCCESSFULLY")
    print("=" * 80)
    print()
    print(f"Output files in: {output_dir}")
    print(f"  - {prefix}power_quality_metrics.png")
    print(f"  - {prefix}load_duration_curve.png")
    print(f"  - {prefix}soc_projection.png")
    print(f"  - {prefix}soh_projection.png")
    print(f"  - {prefix}monitoring_system_diagram.png")
    print()


if __name__ == '__main__':
    main()