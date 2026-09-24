"""
Detailed Multi-Resolution Waveform Plotter
Shows load profile at different zoom levels to reveal wave structure
"""

import matplotlib.pyplot as plt
import numpy as np


class DetailedWaveformPlotter:
    """Create detailed waveform plots at multiple resolutions/zoom levels"""
    
    def __init__(self, figsize=(16, 14)):
        self.figsize = figsize
    
    def plot_multi_resolution_waveform(self, time_fine, power_fine_mw, c1_period):
        """
        Create 5-panel plot showing waveform at different zoom levels
        
        Args:
            time_fine: Time array at fine resolution (0.005s, seconds)
            power_fine_mw: Power array at fine resolution (MW)
            c1_period: Iteration period for reference (seconds)
        
        Returns:
            fig: matplotlib figure object
        """
        fig, axes = plt.subplots(5, 1, figsize=self.figsize)
        fig.suptitle('CHS Load Profile - Multi-Resolution Waveform Analysis\n(Each panel zooms in 10x deeper)', 
                     fontsize=16, fontweight='bold', y=0.995)
        
        # ===== PANEL 1: FULL 24 HOURS =====
        ax = axes[0]
        ax.plot(time_fine / 3600, power_fine_mw, linewidth=0.3, color='#003366', alpha=0.8)
        ax.fill_between(time_fine / 3600, power_fine_mw, alpha=0.15, color='#0066cc')
        ax.set_ylabel('Power (MW)', fontsize=11, fontweight='bold')
        ax.set_title('LEVEL 1: Full 24-Hour Load Profile', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_xlim(0, max(time_fine) / 3600)
        ax.set_ylim(10, 40)
        
        # ===== PANEL 2: 2-HOUR ZOOM =====
        ax = axes[1]
        time_window_2h = 2 * 3600  # 2 hours
        mask = time_fine <= time_window_2h
        ax.plot(time_fine[mask] / 60, power_fine_mw[mask], linewidth=0.5, color='#003366', alpha=0.8)
        ax.fill_between(time_fine[mask] / 60, power_fine_mw[mask], alpha=0.15, color='#0066cc')
        ax.set_ylabel('Power (MW)', fontsize=11, fontweight='bold')
        ax.set_title('LEVEL 2: 2-Hour Window (120 iterations)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(10, 40)
        
        # ===== PANEL 3: 12-MINUTE ZOOM =====
        ax = axes[2]
        time_window_12m = 12 * 60  # 12 minutes
        mask = time_fine <= time_window_12m
        ax.plot(time_fine[mask], power_fine_mw[mask], linewidth=1.0, color='#003366', alpha=0.8)
        ax.fill_between(time_fine[mask], power_fine_mw[mask], alpha=0.15, color='#0066cc')
        
        # Add iteration boundaries
        for i in range(int(time_window_12m / c1_period) + 1):
            t_boundary = i * c1_period
            ax.axvline(t_boundary, color='red', linestyle='--', alpha=0.4, linewidth=0.8)
        
        ax.set_ylabel('Power (MW)', fontsize=11, fontweight='bold')
        ax.set_title(f'LEVEL 3: 12-Minute Window (~6 iterations, C1={c1_period}s)', fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.set_ylim(10, 40)
        
        # ===== PANEL 4: 60-SECOND ZOOM (DETAILED WAVES) =====
        ax = axes[3]
        time_window_60s = 60  # 60 seconds = 30 iterations
        mask = time_fine <= time_window_60s
        ax.plot(time_fine[mask], power_fine_mw[mask], linewidth=1.5, color='#003366', marker='o', 
                markersize=2, alpha=0.8, label='Fine resolution (0.005s)')
        ax.fill_between(time_fine[mask], power_fine_mw[mask], alpha=0.2, color='#0066cc')
        
        # Add iteration boundaries
        for i in range(int(time_window_60s / c1_period) + 1):
            t_boundary = i * c1_period
            ax.axvline(t_boundary, color='red', linestyle='--', alpha=0.5, linewidth=1)
            ax.text(t_boundary + 0.05, 38, f'I{i}', fontsize=8, color='red')
        
        ax.set_ylabel('Power (MW)', fontsize=11, fontweight='bold')
        ax.set_title(f'LEVEL 4: 60-Second Window (30 iterations) - ITERATION STRUCTURE VISIBLE', 
                     fontsize=12, fontweight='bold', color='#cc0000')
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(10, 40)
        
        # ===== PANEL 5: 10-SECOND ZOOM (SINGLE ITERATION CYCLE) =====
        ax = axes[4]
        time_window_10s = 10  # 10 seconds = 5 iterations
        mask = time_fine <= time_window_10s
        ax.plot(time_fine[mask], power_fine_mw[mask], linewidth=2.0, color='#003366', marker='o', 
                markersize=3, alpha=0.9, label='Fine resolution (5ms sampling)')
        ax.fill_between(time_fine[mask], power_fine_mw[mask], alpha=0.25, color='#0066cc')
        
        # Add iteration boundaries and labels
        for i in range(int(time_window_10s / c1_period) + 1):
            t_boundary = i * c1_period
            ax.axvline(t_boundary, color='red', linestyle='--', alpha=0.6, linewidth=1.5)
            ax.text(t_boundary + 0.1, 38, f'Iteration {i}', fontsize=9, color='red', fontweight='bold')
        
        # Annotate phases for first iteration
        ax.text(0.4, 36, 'COMPUTE\n(80% at peak)', fontsize=9, ha='center', 
                bbox=dict(boxstyle='round', facecolor='#00cc00', alpha=0.3))
        ax.text(1.75, 20, 'SYNC\n(50% dip)', fontsize=9, ha='center',
                bbox=dict(boxstyle='round', facecolor='#ffaa00', alpha=0.3))
        
        ax.set_xlabel('Time (seconds)', fontsize=11, fontweight='bold')
        ax.set_ylabel('Power (MW)', fontsize=11, fontweight='bold')
        ax.set_title(f'LEVEL 5: 10-Second Window (5 complete iterations) - SEE INDIVIDUAL WAVES', 
                     fontsize=12, fontweight='bold', color='#cc0000')
        ax.legend(loc='upper right', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.set_ylim(10, 40)
        
        plt.tight_layout()
        return fig
    
    def plot_single_iteration_detail(self, time_fine, power_fine_mw, c1_period):
        """
        Deep dive into a single 2-second iteration cycle
        
        Args:
            time_fine: Time array (seconds)
            power_fine_mw: Power array (MW)
            c1_period: Iteration period (seconds)
        
        Returns:
            fig: matplotlib figure object
        """
        fig, ax = plt.subplots(figsize=(14, 6))
        
        # Extract first iteration only
        mask = time_fine <= c1_period
        time_iter = time_fine[mask]
        power_iter = power_fine_mw[mask]
        
        # Plot with markers to show 5ms sampling
        ax.plot(time_iter * 1000, power_iter, linewidth=2.5, color='#003366', marker='o', 
                markersize=4, alpha=0.85, label=f'Power at 5ms resolution ({len(time_iter)} samples)')
        ax.fill_between(time_iter * 1000, power_iter, alpha=0.2, color='#0066cc')
        
        # Add phase annotations
        compute_end = c1_period * 0.8 * 1000
        sync_start = (c1_period - 0.5) * 1000
        
        # Compute phase
        ax.axvspan(0, compute_end, alpha=0.1, color='#00cc00', label='COMPUTE phase (80%)')
        ax.text(compute_end/2, 37, 'COMPUTE PHASE\n(Forward pass, backward pass,\nweight update)', 
                ha='center', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='#00cc00', alpha=0.2))
        
        # Middle communication phase
        ax.axvspan(compute_end, sync_start, alpha=0.1, color='#ffaa00')
        ax.text((compute_end + sync_start)/2, 20, 'COMMUNICATION\n(All-reduce, \nI/O)', 
                ha='center', fontsize=9, style='italic',
                bbox=dict(boxstyle='round', facecolor='#ffaa00', alpha=0.2))
        
        # Sync phase
        ax.axvspan(sync_start, c1_period * 1000, alpha=0.1, color='#ff6600', label='SYNC phase (20%)')
        ax.text((sync_start + c1_period * 1000)/2, 37, 'SYNC/GRADIENT\nREDUCTION', 
                ha='center', fontsize=10, fontweight='bold',
                bbox=dict(boxstyle='round', facecolor='#ff6600', alpha=0.2))
        
        # Add phase transition lines
        ax.axvline(compute_end, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Phase boundary')
        ax.axvline(sync_start, color='red', linestyle='--', linewidth=2, alpha=0.7)
        
        # Add grid at 5ms intervals
        ax.set_xticks(np.arange(0, c1_period * 1000 + 100, 100))
        ax.grid(True, alpha=0.2, which='major', linewidth=0.8)
        ax.grid(True, alpha=0.1, which='minor', linewidth=0.3)
        
        ax.set_xlabel('Time within Iteration (milliseconds)', fontsize=12, fontweight='bold')
        ax.set_ylabel('Power (MW)', fontsize=12, fontweight='bold')
        ax.set_title(f'Single Iteration Deep Dive: {c1_period}s Cycle with 5ms Sampling Resolution', 
                     fontsize=13, fontweight='bold')
        ax.legend(loc='upper right', fontsize=11, framealpha=0.95)
        ax.set_ylim(15, 40)
        
        plt.tight_layout()
        return fig
    
    def plot_power_spectrum(self, time_fine, power_fine_mw):
        """
        FFT analysis to show frequency content of the load
        
        Args:
            time_fine: Time array (seconds)
            power_fine_mw: Power array (MW)
        
        Returns:
            fig: matplotlib figure object
        """
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 8))
        fig.suptitle('Load Power Spectrum Analysis (FFT)', fontsize=14, fontweight='bold')
        
        # Use only first hour to avoid excessive computation
        time_window = 3600  # 1 hour
        mask = time_fine <= time_window
        power_segment = power_fine_mw[mask]
        
        # Compute FFT
        dt = time_fine[1] - time_fine[0]  # 0.005s
        fft_result = np.fft.fft(power_segment - np.mean(power_segment))
        frequencies = np.fft.fftfreq(len(power_segment), dt)
        magnitude = np.abs(fft_result)
        
        # Only plot positive frequencies
        idx = frequencies > 0
        frequencies_pos = frequencies[idx]
        magnitude_pos = magnitude[idx]
        
        # Panel 1: Full spectrum
        ax1.semilogy(frequencies_pos, magnitude_pos, linewidth=0.8, color='#003366')
        ax1.axvline(0.5, color='red', linestyle='--', linewidth=2, alpha=0.7, label='0.5 Hz (2s iteration period)')
        ax1.axvline(1.0, color='orange', linestyle='--', linewidth=1.5, alpha=0.7, label='1 Hz')
        ax1.axvline(55, color='green', linestyle='--', linewidth=1.5, alpha=0.7, label='55 Hz (ERCOT band upper limit)')
        ax1.set_xlabel('Frequency (Hz)', fontsize=11, fontweight='bold')
        ax1.set_ylabel('Magnitude (log scale)', fontsize=11, fontweight='bold')
        ax1.set_title('Full Power Spectrum (0 - 100 Hz)', fontsize=12, fontweight='bold')
        ax1.legend(loc='upper right', fontsize=10)
        ax1.grid(True, alpha=0.3, which='both')
        ax1.set_xlim(0, 100)
        
        # Panel 2: Zoomed to ERCOT band
        ax2.plot(frequencies_pos, magnitude_pos, linewidth=1.5, color='#003366')
        ax2.axvline(0.5, color='red', linestyle='--', linewidth=2, alpha=0.7, label='Iteration frequency (0.5 Hz)')
        ax2.axvline(0.1, color='blue', linestyle='--', linewidth=1.5, alpha=0.7, label='ERCOT band: 0.1-55 Hz')
        ax2.axvline(55, color='blue', linestyle='--', linewidth=1.5, alpha=0.7)
        ax2.fill_between(frequencies_pos, 0, magnitude_pos, 
                        where=((frequencies_pos >= 0.1) & (frequencies_pos <= 55)), 
                        alpha=0.15, color='#0066cc', label='ERCOT compliance band')
        ax2.set_xlabel('Frequency (Hz)', fontsize=11, fontweight='bold')
        ax2.set_ylabel('Magnitude', fontsize=11, fontweight='bold')
        ax2.set_title('Zoomed: ERCOT F1 Compliance Band (0.1 - 55 Hz)', fontsize=12, fontweight='bold')
        ax2.legend(loc='upper right', fontsize=10)
        ax2.grid(True, alpha=0.3)
        ax2.set_xlim(0, 60)
        
        plt.tight_layout()
        return fig


def save_detailed_plots(time_fine, power_fine_mw, c1_period, output_dir='./'):
    """
    Generate and save all detailed waveform plots
    
    Args:
        time_fine: Time array at fine resolution
        power_fine_mw: Power array at fine resolution
        c1_period: Iteration period
        output_dir: Output directory for plots
    """
    import os
    
    os.makedirs(output_dir, exist_ok=True)
    plotter = DetailedWaveformPlotter()
    
    # Plot 1: Multi-resolution waveform
    print("\n📊 Creating multi-resolution waveform plot...")
    fig1 = plotter.plot_multi_resolution_waveform(time_fine, power_fine_mw, c1_period)
    fig1.savefig(f'{output_dir}/01_multi_resolution_waveform.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: 01_multi_resolution_waveform.png")
    
    # Plot 2: Single iteration detail
    print("📊 Creating single iteration detail plot...")
    fig2 = plotter.plot_single_iteration_detail(time_fine, power_fine_mw, c1_period)
    fig2.savefig(f'{output_dir}/02_single_iteration_detail.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: 02_single_iteration_detail.png")
    
    # Plot 3: Power spectrum
    print("📊 Creating power spectrum analysis plot...")
    fig3 = plotter.plot_power_spectrum(time_fine, power_fine_mw)
    fig3.savefig(f'{output_dir}/03_power_spectrum.png', dpi=300, bbox_inches='tight')
    print("✓ Saved: 03_power_spectrum.png")
    
    print("\n✅ All detailed waveform plots generated!")
    print(f"📁 Location: {os.path.abspath(output_dir)}/")