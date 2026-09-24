"""
Engineering-style plotting for CHS load profiles
Creates publication-ready charts for load analysis, compliance, and battery sizing
"""

import matplotlib.pyplot as plt
import numpy as np


class LoadProfilePlotter:
    """Create professional engineering charts for CHS load profiles"""
    
    def __init__(self, figsize=(16, 12)):
        """Initialize plotter with figure size"""
        self.figsize = figsize
        
    def plot_full_analysis(self, time_coarse, power_coarse_mw, cluster_name, metrics):
        """Create 4-panel load profile analysis chart"""
        fig, axes = plt.subplots(2, 2, figsize=self.figsize)
        fig.suptitle(f'CHS Load Profile Analysis - {cluster_name}', 
                     fontsize=16, fontweight='bold', y=0.995)
        
        # PANEL 1: Full 24-hour time series
        ax = axes[0, 0]
        ax.plot(time_coarse / 3600, power_coarse_mw, linewidth=0.7, color='#003366')
        ax.set_xlabel('Time (hours)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Power (MW)', fontsize=11, fontweight='bold')
        ax.set_title('24-Hour Load Profile (0.1s resolution)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(time_coarse) / 3600)
        
        # PANEL 2: Zoomed first hour
        ax = axes[0, 1]
        mask = time_coarse <= 3600
        ax.plot(time_coarse[mask], power_coarse_mw[mask], linewidth=0.9, color='#003366')
        ax.set_xlabel('Time (seconds)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Power (MW)', fontsize=11, fontweight='bold')
        ax.set_title('First Hour Detail - Iteration Behavior', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        
        # PANEL 3: Power distribution histogram
        ax = axes[1, 0]
        ax.hist(power_coarse_mw, bins=150, color='#0066cc', alpha=0.7, edgecolor='#003366', linewidth=0.5)
        ax.axvline(metrics['peak_mw'], color='#cc0000', linestyle='--', linewidth=2.5, 
                   label=f"Peak: {metrics['peak_mw']:.1f} MW")
        ax.axvline(metrics['avg_mw'], color='#ff6600', linestyle='--', linewidth=2.5, 
                   label=f"Avg: {metrics['avg_mw']:.1f} MW")
        ax.axvline(metrics['min_mw'], color='#00aa00', linestyle='--', linewidth=2.5, 
                   label=f"Min: {metrics['min_mw']:.1f} MW")
        ax.set_xlabel('Power (MW)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Frequency (count)', fontsize=11, fontweight='bold')
        ax.set_title('Power Level Distribution', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        
        # PANEL 4: Metrics table
        ax = axes[1, 1]
        ax.axis('off')
        table_data = [
            ['Metric', 'Value'],
            ['Peak Power', f"{metrics['peak_mw']:.2f} MW"],
            ['Average Power', f"{metrics['avg_mw']:.2f} MW"],
            ['Minimum Power', f"{metrics['min_mw']:.2f} MW"],
            ['Peak-to-Average Ratio', f"{metrics['peak_to_avg_ratio']:.2f}x"],
            ['Total Energy (24h)', f"{metrics['total_energy_mwh']:.0f} MWh"],
            ['', ''],
            ['Load Parameters', ''],
            ['C1: Iteration Period', f"{metrics['C1_iter_period_sec']:.2f} s"],
            ['C2: Swing Depth', f"{metrics['C2_swing_depth_frac']*100:.0f}%"],
            ['C13: Duty Cycle', f"{metrics['C13_duty_cycle_frac']*100:.0f}%"],
            ['Ramp Rate (Computed)', f"{metrics['ramp_rate_mw_per_sec']:.1f} MW/s"],
        ]
        table = ax.table(cellText=table_data, loc='center', cellLoc='left',
                        colWidths=[0.55, 0.45], bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2.2)
        for i in range(2):
            table[(0, i)].set_facecolor('#003366')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        plt.tight_layout()
        return fig
    
    def plot_iteration_detail(self, time_coarse, power_coarse_mw, c1_period):
        """Close-up of iterations to show structure"""
        fig, ax = plt.subplots(figsize=(14, 6))
        time_window = c1_period * 5
        mask = time_coarse <= time_window
        ax.plot(time_coarse[mask], power_coarse_mw[mask], linewidth=2.0, 
                color='#003366', marker='o', markersize=3, alpha=0.8)
        ax.fill_between(time_coarse[mask], power_coarse_mw[mask], alpha=0.2, color='#0066cc')
        
        for iter_num in range(int(time_window / c1_period) + 1):
            t_boundary = iter_num * c1_period
            ax.axvline(t_boundary, color='red', linestyle='--', alpha=0.5, linewidth=1)
            ax.text(t_boundary + 0.1, ax.get_ylim()[1] * 0.95, f'Iter {iter_num}', fontsize=9, color='red')
        
        ax.set_xlabel('Time (seconds)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Power (MW)', fontsize=12, fontweight='bold')
        ax.set_title(f'First 5 Iterations (C1={c1_period}s) - Waveform Structure', fontsize=13, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        return fig
    
    def plot_compliance_analysis(self, time_fine, power_fine_mw, power_filtered_mw, compliance_results):
        """ERCOT F1 compliance visualization"""
        fig, axes = plt.subplots(2, 1, figsize=(14, 8))
        fig.suptitle('ERCOT F1 Compliance Analysis', fontsize=14, fontweight='bold')
        
        time_window = 2 * 3600
        mask = time_fine <= time_window
        
        ax = axes[0]
        ax.plot(time_fine[mask] / 60, power_fine_mw[mask], linewidth=0.5, color='#cc0000', alpha=0.6, label='Raw power')
        ax.plot(time_fine[mask] / 60, power_filtered_mw[mask], linewidth=1.5, color='#003366', label='Band-pass filtered (0.1-55 Hz)')
        ax.set_ylabel('Power (MW)', fontsize=11, fontweight='bold')
        ax.set_title('Raw Power vs ERCOT Band-Pass Filtered', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        ax = axes[1]
        ax.plot(time_fine[mask] / 60, power_filtered_mw[mask], linewidth=1, color='#003366', label='Filtered power')
        ax.axhline(compliance_results['max_swing_observed_mw'] / 2, color='#ff6600', linestyle='--', linewidth=2, alpha=0.7,
                   label=f"Max swing: {compliance_results['max_swing_observed_mw']:.2f} MW")
        ax.axhline(compliance_results['f1_limit_mw'] / 2, color='#cc0000', linestyle='--', linewidth=2, alpha=0.7,
                   label=f"F1 Limit: {compliance_results['f1_limit_mw']:.2f} MW")
        status_color = '#00cc00' if compliance_results['compliance_status'].startswith('PASS') else '#cc0000'
        ax.text(0.02, 0.95, f"Status: {compliance_results['compliance_status']}", transform=ax.transAxes, fontsize=12, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor=status_color, alpha=0.3))
        ax.set_xlabel('Time (minutes)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Power (MW)', fontsize=11, fontweight='bold')
        ax.set_title('Compliance Check (5-Second Rolling Window)', fontsize=12, fontweight='bold')
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        return fig
    
    def plot_battery_summary(self, power_coarse_mw, metrics, battery_results):
        """Battery sizing summary"""
        fig = plt.figure(figsize=(14, 8))
        gs = fig.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        fig.suptitle('Battery System Sizing Summary', fontsize=14, fontweight='bold')
        
        ax1 = fig.add_subplot(gs[0, :])
        time_hours = np.arange(len(power_coarse_mw)) * 0.1 / 3600
        ax1.plot(time_hours, power_coarse_mw, linewidth=0.5, color='#003366', label='Load power')
        avg = metrics['avg_mw']
        ax1.axhline(avg, color='#ff6600', linestyle='--', linewidth=2, label=f"Average: {avg:.1f} MW")
        ax1.axhline(metrics['peak_mw'], color='#cc0000', linestyle='--', linewidth=1, alpha=0.5, label=f"Peak: {metrics['peak_mw']:.1f} MW")
        ax1.fill_between(time_hours, avg, metrics['peak_mw'], alpha=0.1, color='#cc0000',
                        label=f"Battery absorbs: {metrics['peak_mw'] - avg:.1f} MW")
        ax1.set_ylabel('Power (MW)', fontsize=11, fontweight='bold')
        ax1.set_title('24-Hour Load Profile & Battery Operating Window', fontsize=12, fontweight='bold')
        ax1.legend(loc='upper right', fontsize=9)
        ax1.grid(True, alpha=0.3)
        ax1.set_xlim(0, 24)
        
        ax2 = fig.add_subplot(gs[1, 0])
        ax2.axis('off')
        table_data = [
            ['Battery Specification', 'Value'],
            ['Power Rating', f"{battery_results['power_rating_mw']:.2f} MW"],
            ['Energy Capacity', f"{battery_results['energy_capacity_mwh']:.0f} MWh (nameplate)"],
            ['Usable Energy', f"{battery_results['usable_energy_mwh']:.0f} MWh"],
            ['Round-Trip Efficiency', f"{battery_results['efficiency_pct']:.0f}%"],
            ['Usable SOC Window', f"{battery_results['usable_soc_pct']:.0f}%"],
            ['Degradation Factor', f"{battery_results['degradation_factor']}x"],
            ['C-Rate', f"{battery_results['c_rate']:.2f}C"],
        ]
        table = ax2.table(cellText=table_data, loc='center', cellLoc='left',
                         colWidths=[0.55, 0.45], bbox=[0, 0, 1, 1])
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2.0)
        for i in range(2):
            table[(0, i)].set_facecolor('#003366')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        ax3 = fig.add_subplot(gs[1, 1])
        ax3.axis('off')
        tech = battery_results['technology_recommendation']
        c_rate = battery_results['c_rate']
        threshold = battery_results['c_rate_threshold']
        color = '#00cc00' if c_rate <= threshold else '#ffaa00'
        recommendation_text = f"""
TECHNOLOGY RECOMMENDATION

{tech}

C-Rate Analysis:
  • Calculated C-Rate: {c_rate:.2f}C
  • Threshold: {threshold}C
  • Status: {'✓ Acceptable' if c_rate <= threshold else '⚠ Consider hybrid'}

Rationale:
  • Power needed: {battery_results['power_rating_mw']:.2f} MW
  • Energy capacity: {battery_results['energy_capacity_mwh']:.0f} MWh
  • Discharge time: {60/c_rate:.0f} minutes at full power
"""
        ax3.text(0.05, 0.95, recommendation_text, transform=ax3.transAxes, fontsize=9, verticalalignment='top', family='monospace',
                bbox=dict(boxstyle='round', facecolor=color, alpha=0.15))
        
        plt.tight_layout()
        return fig


def save_plots(results, output_dir='./'):
    """Generate and save all plots"""
    import os
    os.makedirs(output_dir, exist_ok=True)
    
    time_coarse = results['time_coarse']
    power_coarse_mw = results['power_coarse']
    time_fine = results['time_fine']
    power_fine_mw = results['power_fine']
    power_filtered = results.get('power_filtered', None)
    metrics = results['metrics']
    gen_params = results['generator_params']
    compliance = results.get('compliance', {})
    battery = results.get('battery', {})
    
    metrics.update(gen_params)
    if compliance:
        metrics['f1_status'] = compliance['compliance_status']
        metrics['f1_max_swing'] = compliance['max_swing_observed_mw']
    if battery:
        metrics['battery_power_mw'] = battery['power_rating_mw']
        metrics['battery_energy_mwh'] = battery['energy_capacity_mwh']
    
    plotter = LoadProfilePlotter()
    
    print("\n📊 Creating full analysis plot...")
    fig1 = plotter.plot_full_analysis(
        time_coarse, power_coarse_mw, 
        f"{results['cluster']['total_gpu_count']:,} GPUs, {results['cluster']['total_power_mw']} MW",
        metrics
    )
    fig1.savefig(f'{output_dir}/chs_load_profile_analysis.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: chs_load_profile_analysis.png")
    
    print("📊 Creating iteration detail plot...")
    fig2 = plotter.plot_iteration_detail(time_coarse, power_coarse_mw, gen_params['C1_iter_period_sec'])
    fig2.savefig(f'{output_dir}/chs_iteration_detail.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: chs_iteration_detail.png")
    
    if power_filtered is not None and compliance:
        print("📊 Creating ERCOT F1 compliance plot...")
        fig3 = plotter.plot_compliance_analysis(time_fine, power_fine_mw, power_filtered, compliance)
        fig3.savefig(f'{output_dir}/chs_ercot_f1_compliance.png', dpi=300, bbox_inches='tight')
        print("✓ Saved: chs_ercot_f1_compliance.png")
    
    if battery:
        print("📊 Creating battery sizing summary plot...")
        fig4 = plotter.plot_battery_summary(power_coarse_mw, metrics, battery)
        fig4.savefig(f'{output_dir}/chs_battery_sizing.png', dpi=300, bbox_inches='tight')
        print("✓ Saved: chs_battery_sizing.png")
    
    print("\n✅ All plots generated successfully!")
    print(f"📁 Location: {os.path.abspath(output_dir)}/")