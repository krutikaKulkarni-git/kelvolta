# config/parameters_B.py
"""
Cluster B: Rack/Hall Configuration
Uses GB200 NVL72 as primary platform (Phase 0)
"""

# B1: Hall IT Capacity
HALL_CAPACITY_MW = 50  # MW (design choice)

# Derived from HALL_CAPACITY_MW and rack power
def get_rack_configuration(hall_mw=HALL_CAPACITY_MW, rack_power_kw=120):
    """
    B2: Calculate rack count from hall capacity
    """
    total_kw = hall_mw * 1000
    rack_count = int(total_kw / rack_power_kw)
    total_gpu_count = rack_count * 72  # 72 GPUs per NVL72
    return {
        'hall_capacity_mw': hall_mw,
        'rack_count': rack_count,
        'gpus_per_rack': 72,
        'total_gpu_count': total_gpu_count,
        'total_power_kw': total_kw,
        'total_power_mw': hall_mw,
    }

# Phase 0 configuration
RACK_CONFIG = get_rack_configuration()
# Result: 417 racks, ~30,000 GPUs, 50 MW total