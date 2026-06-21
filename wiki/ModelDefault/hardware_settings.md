# Default Hardware Settings & Configuration

Used when TC specifies hardware configuration but omits specific setting values.

## HwSetting Field Defaults

When modifying hardware settings without explicit values:

```python
# Most commonly configured settings (from Script patterns)

# Inhibition Time (idle timeout)
HwSettingField.INHIBITION_TIME = 180  # seconds

# PSA (Production State Awareness) Configuration
PSA_STATE = api.PSAState.PRE_SOLDERING  # Default after manufacturing
PSA_DATA_SIZE = device_descriptor.l37_psa_max_data_size  # Use device max

# Write Booster
WRITEBOOSTER_ENABLED = True
WRITEBOOSTER_BUFFER_SIZE = auto  # Use device default

# Background Operations
BKOPS_ENABLED = True
BKOPS_FLUSH_ENABLE = True

# Temperature Monitoring
TEMPERATURE_THRESHOLD_HIGH = 85  # Celsius
TEMPERATURE_THRESHOLD_LOW = 0    # Celsius

# Cache Settings
CACHE_MODE = WRITE_BACK  # Default cache policy
CACHE_FLUSH_TIMEOUT = 30  # seconds
```

---

## Device Descriptor Access

When TC needs device info but doesn't specify what to read:

```python
# Default descriptor retrieval (safe to always do)
device_desc = api.get_device_descriptor()
geometry_desc = api.get_geometry_descriptor()
fw_geometry = api.get_fw_geometry()

# Common device info accessed:
device_desc.l37_psa_max_data_size      # PSA capacity
device_desc.bNumberLU                   # Number of logical units
device_desc.bSecureRemovalType          # Secure erase support
```

**Spec Reference:** Section 14 (Descriptors, Flags and Attributes)

---

## Virtual Block (VB) Sizing

When determining VB sizes for test operations:

```python
# Calculate from firmware geometry
flash_setting = get_flash_setting()
slc_vb_size = fw_geometry.l84_vb_size_u0 * 512 // 4096
tlc_vb_size = fw_geometry.l88_vb_size_u1 * 512 // 4096

# Safety margins
exceed_size = 50  # Extra blocks beyond main VB capacity

# Total test allocation
total_test_size = slc_vb_size + exceed_size
```

---

## LUN Configuration Defaults

When configuring logical units for a test:

```python
# Standard LUN allocation (from VPCT test patterns)
TestNormalLun = 0      # Primary data partition
TestEM1Lun = 1         # Enhanced Memory 1 (extra reliable)
TestWBLun = 2          # WriteBooster dedicated LUN
TestGCLun = 3          # Garbage Collection area
TestTemperatureLun = 4 # Temperature monitoring

# LUN type defaults
normal_lu_type = "General Purpose"
em1_lu_type = "Enhanced Reliability"
wb_lu_type = "WriteBooster Cache"

# Common LU counts
min_lun_required = 2   # At least data + EM1
typical_lun_count = 5  # Data + EM1 + WB + GC + Temp
max_lun_count = device_descriptor.bNumberLU  # Device maximum
```

---

## RPMB Configuration

When accessing RPMB (Replay Protected Memory Block) without details:

```python
# Default RPMB region and mode
rpmb_region = RPMBRegion.REGION_0  # Always use region 0 by default

# Key management
rpmb_key = auto_generate_key()  # Generate random key for test
rpmb_key_size = 32  # bytes (256-bit key)

# Write counter reset
clear_rpmb_key = True  # Clear and reset on init (safe default)

# Operation mode
rpmb_mode = "NORMAL"  # Use normal RPMB mode by default
```

**Spec Reference:** Section 12.4 (RPMB — Replay Protected Memory Block)

---

## Erase/Defect Management

When configuring NAND management without specifics:

```python
# Flash defect handling
bad_block_info = api.get_bad_block_information()  # Retrieve existing defects
defragmentation_enabled = True  # Enable auto-defrag
defrag_source_vp = auto  # Let firmware select VPs to defrag

# Format operation defaults
format_type = "QUICK_FORMAT"  # Fast format (no full erase)
keep_user_data = False         # Erase all data unless specified

# Rebuild operation
auto_rebuild_on_error = True   # Auto-repair on detection
```

