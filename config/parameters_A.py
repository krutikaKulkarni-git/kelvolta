# config/parameters_A.py
"""
Cluster A: GPU and Hardware Specifications (Blackwell)
Sourced from NVIDIA datasheets and official documentation
"""

# A2: GPU Thermal Design Power
GPU_TDP_GB200 = 1200  # watts per GPU (GB200 NVL72)
GPU_TDP_GB300 = 1400  # watts per GPU (GB300 NVL72)
GPU_TDP_H100_REFERENCE = 700  # watts (H100 reference only)

# A5: GPUs per Rack
GPUS_PER_RACK = 72  # NVL72 platform definition

# A6: Rack Nominal Power
RACK_POWER_GB200 = 120  # kW per rack (NVIDIA official)
RACK_POWER_GB300 = 135  # kW per rack
RACK_POWER_HPE_GB200 = 132  # kW per rack (HPE implementation, secondary)

# A8: Rack Idle Floor Power
RACK_IDLE_POWER = 10.8  # kW per rack

# A9: Non-GPU Rack Overhead
NON_GPU_OVERHEAD_GB200 = 33.6  # kW per rack
NON_GPU_OVERHEAD_GB300 = 34.2  # kW per rack

# Platform selection for Phase 0
DEFAULT_PLATFORM = "GB200"
DEFAULT_GPU_TDP = GPU_TDP_GB200
DEFAULT_RACK_POWER = RACK_POWER_GB200