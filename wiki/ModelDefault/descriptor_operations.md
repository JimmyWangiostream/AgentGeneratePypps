# Default Descriptor, Attribute & Flag Operations

Used when TC specifies attribute/flag changes but omits specific values.

## Attribute Operations

### Common Attributes When Not Specified

```python
# When reading attributes without specifying which ones
api.read_attribute(idn=api.AttributeIDN.PSA_STATE)  # Most commonly checked

# PSA State defaults
PSA_STATE = api.PSAState.PRE_SOLDERING  # After manufacturing
PSA_DATA_SIZE = device_descriptor.l37_psa_max_data_size

# Data Sector Size
DATA_SECTOR_SIZE = 4096  # bytes (standard UFS)

# Boot LU attributes
BOOT_LU_A_ENABLED = True
BOOT_LU_B_ENABLED = True
```

---

## Flag Operations

### Default Flag Settings

```python
# When setting/clearing flags without specific target

# WriteBooster
set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)    # Default: enabled

# Background Operations  
set_flag(idn=api.FlagIDN.BKOPS_RECOMMENDED)  # Default: enabled
set_flag(idn=api.FlagIDN.BKOPS_URGENT)       # Default: NOT urgent unless critical

# Device Init
set_flag(idn=api.FlagIDN.DEVICE_INIT)        # Only set if needed (rare)

# Purge (Secure Erase)
clear_flag(idn=api.FlagIDN.PURGE_ENABLE)     # Default: disabled (risky operation)
```

---

## Query Operation Defaults

When using Query Request/Response without specifics:

```python
# Default query operations
QueryType = Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_ATTRIBUTE  # Most common

# Typical query workflow when TC doesn't specify
def standard_query_flow():
    # 1. Read descriptor first (safe, doesn't modify)
    device_desc = query_descriptor(DescriptorType.DEVICE)
    
    # 2. Then read attributes
    psa_state = query_attribute(AttributeIDN.PSA_STATE)
    
    # 3. Finally modify if needed (rare, requires explicit TC instruction)
```

---

## Descriptor Read Defaults

### Device Descriptor
```python
# Always safe to read, provides baseline info
device_descriptor = api.get_device_descriptor()

# Key fields typically accessed
bNumberLU = device_descriptor.bNumberLU                    # LU count
bBootLunEn = device_descriptor.bBootLunEn                  # Boot support  
l37_psa_max_data_size = device_descriptor.l37_psa_max_data_size
bSecureRemovalType = device_descriptor.bSecureRemovalType  # Erase type
```

### Geometry Descriptor
```python
# Always needed for capacity calculations
geometry_desc = api.get_geometry_descriptor()

# Key fields
bAllocationUnitSize = geometry_desc.bAllocationUnitSize
wManufacturerID = geometry_desc.wManufacturerID
```

### LU Descriptor
```python
# Read for each LU that will be used in test
for lun in [0, 1, 2, 3, 4]:
    lu_desc = api.get_lu_descriptor(lun)
    # Verify LU type and capacity match expectations
```

---

## Mode Page Defaults

### Mode Sense Defaults

When reading mode pages without specifying which:

```python
# Default to reading all supported pages
all_mode_pages = api.read_mode_sense(lun=<target_lun>, pc=0)  # Current values

# Most commonly checked pages
CONTROL_MODE_PAGE = 0x0A       # Device behavior control
ERROR_RECOVERY_PAGE = 0x01     # Retry/error handling
CACHE_MODE_PAGE = 0x08         # Caching policy
```

### Mode Select Defaults

When modifying mode pages:

```python
# Default behavior when updating mode pages
PF_BIT = 1  # Permanent (save to non-volatile)
SP_BIT = 1  # Save parameters (non-volatile storage)

# Default parameter values for common pages
error_recovery = {
    "awre": 1,        # Auto-write reallocate enabled
    "arre": 1,        # Auto-read reallocate enabled
    "tb": 0,          # Transfer block on error disabled
    "rc": 0,          # Read continuous disabled
    "eec": 0,         # Enable error recovery control
    "tur": 0,         # Test unit ready on recovery
}

cache_policy = {
    "cce": 1,         # Cache control enabled
    "dra": 1,         # Disable read-ahead (let firmware optimize)
    "wce": 1,         # Write cache enabled (safe: host responsible for flush)
    "rcd": 0,         # No read cache disable
    "mf": 0,          # Modular
    "rsc": 0,         # Restart/save control
    "fua": 0,         # FUA disabled (allow caching)
    "fuanv": 0,       # FUA non-volatile disable
}
```

**Spec Reference:** Section 11.4 (Mode Pages)

---

## VPD (Vital Product Data) Pages

Default VPD pages when device info needed:

```python
# Always available and safe to read
vpd_supported_pages = api.read_vpd_pages(lun=0)
vpd_device_id = api.read_vpd_pages(page=0x83)  # Device identification
vpd_serial_number = api.read_vpd_pages(page=0x80)

# Query via INQUIRY command (better compatibility)
inquiry_response = api.inquiry(lun=0)
```

**Spec Reference:** Section 11.5 (VPD Pages)

