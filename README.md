# CHS Model — Compute Hall Signature Load & Storage Model

Phase 0/1 modelling for the Kelvolta **CHS (Compute Hall Signature)** initiative.

The model synthesises the electrical load signature of an AI training hall (NVIDIA
GB200 NVL72), tests it against the proposed **ERCOT F1** load-change limit, and sizes
a behind-the-meter battery to absorb the resulting swings.

Pipeline:

```
Parameters (A,B,C,E,F) → Waveform → Load analysis → ERCOT F1 check → Battery sizing → Plots
```

---

## Status

Phase 1 complete: dual-resolution load profile plus the F1 compliance filter.
The pipeline runs end to end and produces all plots.

The current baseline **fails** F1 by a wide margin — that is the expected physical
result (a 17.97 MW load swing against a 10 MW limit) and is the motivation for the
battery. Note, however, that the reported swing figure is inflated by a filter
artefact and that the F1 result does not currently drive the battery sizing. See
[Known issues](#known-issues-and-open-items) before quoting any number from a run.

---

## Quick start

Requires Python 3.12 with `numpy`, `scipy` and `matplotlib`.

> The system `/usr/bin/python3` (3.9) does not have these installed. On the
> current workstation the working interpreter is `/opt/anaconda3/bin/python3`
> (Python 3.12.7, numpy 1.26.4, scipy 1.13.1, matplotlib 3.9.2).

```bash
# Run from the repository root — modules import as `from config import ...`
python main.py
```

Measured on the workstation above: **~90 s runtime, 2.2 GB peak RSS**. The memory goes
on the fine-resolution pass, which holds several 17,280,000-sample float64 arrays
(~138 MB each) live at once, plus matplotlib rendering 17.28 M points per panel.

Plots are written into the **current working directory**, overwriting any existing
copies. To keep a run separate, copy the tree elsewhere and run there.

The standalone monitoring-preview script takes an output directory:

```bash
python output/monitoringMetrics.py --output ./plots/ --prefix phase1
```

---

## Repository layout

### Entry points

| File | Purpose |
|---|---|
| [main.py](main.py) | Main orchestrator. Runs all 9 steps, prints the full report, returns a `results` dict. |
| [output/monitoringMetrics.py](output/monitoringMetrics.py) | Standalone Phase 1 script for the 5 monitoring-preview graphs. Independent of the `config/` package — see [Known issues](#known-issues-and-open-items). |
| [debug.py](debug.py) | Prints the first 100 coarse samples. **Currently broken.** |
| [debug_detailed.py](debug_detailed.py) | Prints the first 200 samples with the expected pattern. **Currently broken.** |

### `config/` — parameter clusters

Each cluster is a flat module of constants, named to match the CHS decision register.

| File | Cluster | Contents |
|---|---|---|
| [config/parameters_A.py](config/parameters_A.py) | A — Hardware | GPU TDP (GB200 1200 W, GB300 1400 W, H100 700 W ref), 72 GPUs/rack, rack power (120/135 kW), idle floor, non-GPU overhead. |
| [config/parameters_B.py](config/parameters_B.py) | B — Hall config | `HALL_CAPACITY_MW = 50` and `get_rack_configuration()`, which derives rack and GPU counts. |
| [config/parameters_C.py](config/parameters_C.py) | C — Temporal behaviour | Iteration period, swing depth, checkpoint duration/depth, duty cycle, edge duration. Derived from H100/A100 measurements — **no measured GB200/GB300 temporal data exists**. |
| [config/parameters_E.py](config/parameters_E.py) | E — Simulation | Both resolutions, reporting resolutions, 24 h duration, downsampling method, random seed 42. |
| [config/parameters_F.py](config/parameters_F.py) | F — Storage & grid | F1 limit and band, PCS response, round-trip efficiency, usable SOC, C-rate ceiling, recharge window, degradation factor. |

### `core/` — computation

| File | Purpose |
|---|---|
| [core/waveform_generator.py](core/waveform_generator.py) | `WaveformGenerator`. `generate_dual_resolution()` returns coarse and fine time/power arrays. Also defines `validate_waveform()` (unused). |
| [core/compliance_checker.py](core/compliance_checker.py) | `ComplianceChecker`. 2nd-order Butterworth band-pass (`sosfilt`) then a brute-force scan of every rolling 5 s window. |
| [core/battery_sizer.py](core/battery_sizer.py) | `BatterySizer`. Power rating, energy capacity, C-rate, and a C-rate-based technology recommendation. |
| [core/intermidiate_variables.py](core/intermidiate_variables.py) | `IntermediateVariables` container. Declared but never instantiated; filename is misspelled. |

### `output/` — plotting

| File | Purpose |
|---|---|
| [output/plotter.py](output/plotter.py) | `LoadProfilePlotter` + `save_plots()`. The four main Phase 0 charts. |
| [output/detailed_plotter.py](output/detailed_plotter.py) | `DetailedWaveformPlotter` + `save_detailed_plots()`. Multi-zoom waveform and FFT. |
| [output/monitoringMetrics.py](output/monitoringMetrics.py) | Standalone Phase 1 previews. Does not import `config/` — see [Known issues](#known-issues-and-open-items). |

---

## Which file generates what

Every PNG in this repo, and the exact function that writes it.

### Produced by `python main.py`

`main.py` step 8 calls `save_plots()` in [output/plotter.py:209](output/plotter.py#L209),
which writes four files at **dpi=300** into the current working directory:

| Output file | Written at | Plotting function | Contents |
|---|---|---|---|
| `chs_load_profile_analysis.png` | [plotter.py:240](output/plotter.py#L240) | `plot_full_analysis()` [:17](output/plotter.py#L17) | 4-panel: 24 h series, first-hour zoom, power histogram, metrics table |
| `chs_iteration_detail.png` | [plotter.py:245](output/plotter.py#L245) | `plot_iteration_detail()` [:85](output/plotter.py#L85) | First 5 iterations with iteration boundaries marked |
| `chs_ercot_f1_compliance.png` | [plotter.py:251](output/plotter.py#L251) | `plot_compliance_analysis()` [:106](output/plotter.py#L106) | Raw vs band-pass filtered power, plus the F1 limit line. Skipped if no compliance results. |
| `chs_battery_sizing.png` | [plotter.py:257](output/plotter.py#L257) | `plot_battery_summary()` [:140](output/plotter.py#L140) | Load profile with battery operating window, spec table, technology rationale. Skipped if no battery results. |

`main.py` step 9 then calls `save_detailed_plots()` in
[detailed_plotter.py:248](output/detailed_plotter.py#L248), which writes three more at **dpi=300**:

| Output file | Written at | Plotting function | Contents |
|---|---|---|---|
| `01_multi_resolution_waveform.png` | [detailed_plotter.py:266](output/detailed_plotter.py#L266) | `plot_multi_resolution_waveform()` [:16](output/detailed_plotter.py#L16) | 5 panels, each zooming 10× deeper: 24 h → 2 h → 12 min → 60 s → 10 s |
| `02_single_iteration_detail.png` | [detailed_plotter.py:272](output/detailed_plotter.py#L272) | `plot_single_iteration_detail()` [:122](output/detailed_plotter.py#L122) | One 2 s iteration at 5 ms sampling, compute/comms/sync phases annotated |
| `03_power_spectrum.png` | [detailed_plotter.py:278](output/detailed_plotter.py#L278) | `plot_power_spectrum()` [:187](output/detailed_plotter.py#L187) | FFT of the first hour; marks 0.5 Hz iteration frequency and the 0.1–55 Hz ERCOT band |

Both steps are wrapped in `try/except` in `main.py`, so a plotting failure prints a
warning and the run still completes.

### Produced by `python output/monitoringMetrics.py`

A **separate entry point** — these are not generated by `main.py`. Written at **dpi=150**
into `--output` (default `./`), optionally prefixed with `--prefix`:

| Output file | Written at | Plotting function | Contents |
|---|---|---|---|
| `power_quality_metrics.png` | [monitoringMetrics.py:309](output/monitoringMetrics.py#L309) | `plot_power_quality_metrics()` [:234](output/monitoringMetrics.py#L234) | Voltage, current, power factor, THD, frequency against ERCOT limits |
| `load_duration_curve.png` | [monitoringMetrics.py:355](output/monitoringMetrics.py#L355) | `plot_load_duration_curve()` [:314](output/monitoringMetrics.py#L314) | Load duration curve, used to validate the duty cycle |
| `soc_projection.png` | [monitoringMetrics.py:400](output/monitoringMetrics.py#L400) | `plot_soc_projection()` [:360](output/monitoringMetrics.py#L360) | 24 h state-of-charge against a Texas sunny-day solar profile |
| `soh_projection.png` | [monitoringMetrics.py:437](output/monitoringMetrics.py#L437) | `plot_soh_projection()` [:405](output/monitoringMetrics.py#L405) | 15-year state-of-health fade to the 80% warranty and 70% end-of-life marks |
| `monitoring_system_diagram.png` | [monitoringMetrics.py:530](output/monitoringMetrics.py#L530) | `plot_monitoring_diagram()` [:442](output/monitoringMetrics.py#L442) | Sensor placement across the monitoring system |

> The power quality, THD and frequency traces in `power_quality_metrics.png` are
> **synthesised from `np.random.normal`**, not measured or derived from the waveform
> model. They are presentation previews of the metric shape, not results.

### Not image outputs

- `main()` in [main.py](main.py) returns a `results` dict (time/power arrays, `metrics`,
  `cluster`, `generator_params`, `compliance`, `battery`) and prints the full 9-step
  report to stdout. Nothing is written to disk except the PNGs.
- No CSV, JSON or log file is written by any module.

All PNGs and CSVs are **gitignored** — they are regenerated artefacts, kept locally only.
The plot files currently in your working copy were committed once and then untracked in
`c0b459f`; they still exist in git history.

---

## The load model

Per 2.0 s iteration, at 29,952 GPUs × 1200 W = 35.94 MW peak:

| Window | Phase | Power |
|---|---|---|
| 0.000 – 1.500 s | Compute — forward/backward pass, weight update | 35.94 MW (peak) |
| 1.500 – 2.000 s | Sync — gradient all-reduce | 17.97 MW (peak × (1 − C2)) |

A checkpoint phase every 100 iterations is implemented but **never fires**, because
`C7_CHECKPOINT_DEPTH = None`. C7 is the model's one unresolved parameter: no usable
source was found to convert the available single-GPU measurement into a production
rack power fraction.

### Resolutions

Two resolutions are generated because one would not serve both purposes:

- **Coarse, 0.1 s (10 Hz), 864,000 samples** — load-shape analysis and visualisation.
- **Fine, 0.005 s (200 Hz), 17,280,000 samples** — F1 compliance. The 55 Hz upper
  band edge needs >110 Hz sampling to satisfy Nyquist.

---

## Baseline results

Verified from a full run on 2026-09-23 with the default parameters
(50 MW hall, GB200, C1 = 2.0 s, C2 = 0.50, C13 = 0.80, seed 42):

**Cluster** — 416 racks, 29,952 GPUs, 50 MW hall capacity.

| Load metric | Value |
|---|---|
| Peak power | 35.94 MW |
| Minimum power | 17.97 MW |
| Average power | 31.45 MW |
| Peak-to-average ratio | 1.14× |
| Energy over 24 h | 755 MWh |
| Derived ramp rate | 35.9 MW/s |
| Time above 90% of peak | 75.0% |

| ERCOT F1 | Value |
|---|---|
| Status | **FAIL** |
| Limit | 10.00 MW peak-to-peak per rolling 5 s |
| Max swing reported | 65.09 MW |
| Violating windows | 17,279,000 of 17,279,000 |

| Battery sizing | Value |
|---|---|
| Power rating | 4.50 MW |
| Nameplate capacity | 1340 MWh |
| Usable energy | 755 MWh |
| C-rate | 0.003C |
| Recommendation | LFP — cost-optimised |

Every window violates, which is the expected consequence of a 17.97 MW swing
recurring every 2 s against a 10 MW limit. The **65.09 MW** figure, however, is not
physical — it exceeds the raw signal's own 17.97 MW range. See issue 2 below.

---

## Known issues and open items

Recorded from reading and running the current code. None are fixed in this branch.

**Modelling**

1. **Effective duty cycle is 75%, not the configured 80%.** In
   `_generate_waveform_at_resolution`, the C14 sync branch is tested before the C13
   duty-cycle branch, so `t ∈ [1.5, 2.0)` always takes the dip and only 0–1.5 s stays
   at peak. The run confirms it: "High-Power Time (>90% peak): 75.0%". `C13_DUTY_CYCLE_DEFAULT`
   has no effect on the output while `C14 = 0.5` and `C1 = 2.0`.
2. **Filtered swing exceeds the raw swing.** The checker reports 65.09 MW against a
   raw range of 17.97 MW, which a band-pass of a bounded signal cannot produce. It is
   the `sosfilt` startup transient: the filter begins at zero initial condition against
   a ~31 MW DC offset, and every top-ranked violation is at t = 0. Candidate fixes:
   seed the state with `sosfilt_zi * x[0]`, use `sosfiltfilt`, or discard the settling
   window before scanning. The 0.1 Hz lower edge is also only 0.001× Nyquist at 200 Hz,
   which is numerically demanding for the filter design.
3. **The F1 result does not size the battery.** `compliance_max_swing` is passed into
   `calculate_battery_requirements()` and only echoed back in the results dict. The
   power rating comes from `peak − avg` = 4.49 MW. Holding a 17.97 MW swing under the
   10 MW limit needs roughly 8 MW of absorption, so the battery is undersized against
   the very constraint it exists to satisfy.
4. **Energy capacity is sized for the wrong duty.** `calculate_energy_capacity()` uses
   `avg_power × 24 h`, i.e. a full day of total site load (755 MWh → 1340 MWh nameplate),
   rather than the energy needed to buffer sub-minute swings. This is what produces the
   0.003C rate and the nonsensical "discharge time: 17,869 minutes".
5. **Dead branch in `calculate_power_rating()`.** `supply_rate = avg_power_mw - avg_power_mw`
   is always 0; it appears to have been intended as `avg − min`. `min_power_mw` is
   accepted by the sizer but never used in a calculation.
6. **The executive summary hardcodes a pass.** `main.py` always prints
   "✓ Waveform validates against F1 standard", including on the current FAIL run.

**Code health**

7. Both debug scripts call `gen.generate()`, which was removed when the generator moved
   to `generate_dual_resolution()`. Both raise `AttributeError` immediately.
8. `core/intermidiate_variables.py` is misspelled (its own docstring says
   `intermediate_variables.py`), and `IntermediateVariables` is never instantiated.
9. `validate_waveform()` is defined but never called.
10. The trailing comment in `parameters_B.py` claims "417 racks, ~30,000 GPUs"; `int()`
    truncation actually yields 416 racks and 29,952 GPUs.
11. `output/monitoringMetrics.py` carries its own hardcoded `CHS_Config` instead of
    importing `config/`, and has already drifted — it holds `POWER_RATING = 4.49` and
    `BATTERY_CAPACITY_MWH = 1343` against the model's current 4.50 MW and 1340 MWh.
    It also never seeds the RNG, unlike the main pipeline, so its five plots differ on
    every run and cannot be reproduced from a prior deck.
12. Declared but unused: `F5_CRATE_CEILING`, `F6_RECHARGE_EVENTS_PER_HOUR`,
    `F1_ROLLING_WINDOW_SEC` (the checker hardcodes `5.0`), `RACK_IDLE_POWER`, and the
    non-GPU overhead constants. `E2`, `E4` and `F2` are printed in the banner but feed
    no calculation. `idle_power_per_gpu_w` is set to 100 W but the waveform never
    reaches idle.
13. No `requirements.txt` or pinned environment.
14. `plotter.py` emits a `tight_layout` warning from the table panel on every run.

**Open parameter**

15. **C7 (checkpoint power drop depth) is unresolved.** Until it is measured, the
    checkpoint phase is inert and the model omits checkpoint transients entirely.

---

## Next steps

Carried from the executive summary in `main.py`:

1. Obtain a measured C7 value from a production GB200 cluster.
2. Run a sensitivity analysis over C7 = 0%, 25%, 50%.
3. Integrate power quality metrics (voltage, current, THD) into the main pipeline.
4. Add the state-of-charge trajectory to the main visualisation set.
5. Client presentation deck.

---

## Provenance

Cluster A is sourced from NVIDIA datasheets and official documentation. Cluster C is
derived from published H100/A100 measurements (RoBERTa, GPT-NeoX, Flan-T5 scenarios;
NVIDIA NeMo and PyTorch checkpoint timings) — there is no measured GB200/GB300 temporal
data. Cluster F reflects the proposed ERCOT load-change limits. Cluster B hall capacity
is a design choice, not a measurement.

Runs are deterministic: `E5_RANDOM_SEED = 42`. The current waveform generator is fully
deterministic regardless, as no stochastic term is applied.
