# Default Vendor Command Parameters

Used when TC specifies vendor commands but omits parameter details. These are UFS implementation-specific commands.

## Common Vendor Commands

### Firmware Value Read/Write

When accessing firmware internal state without specifics:

```python
# Default read pattern for debugging
read_fw_value(address='gInhibitMgr.lock')  # Inhibition manager state

# Standard reads
fw_state = read_fw_value('gFwState.value')
inhibition_status = read_fw_value('gInhibitMgr.lock')
background_ops_status = read_fw_value('gBkopsStatus')
temperature = read_fw_value('gThermalMgr.current_temp')
```

### Memory Access

When reading device memory without specifics:

```python
# Default SRAM read
sram_address = get_debug_info().VB_list_cycle_address.value
memory_data = read_Xmemory(sram_address=sram_address)

# Default DRAM read (if available)
dram_offset = 0x0000
dram_size = 256  # bytes (typical debug buffer)
```

---

## Debug Information Defaults

When retrieving debug info:

```python
# Always get full debug info structure first
resp, debug_info = api.ufs_api.vendor_cmd.get_debug_info()

# Key addresses provided by debug_info
VB_list_cycle_address = debug_info.VB_list_cycle_address.value
error_history_address = debug_info.error_history_address.value
bad_block_address = debug_info.bad_block_address.value
temperature_sensor_address = debug_info.temperature_sensor_address.value
```

---

## Flash Configuration

### Flash Setting Defaults

```python
# Get device flash characteristics
flash_setting = get_flash_setting()

# Use device's native configuration
page_size = flash_setting.page_size         # NAND page size (4KB typical)
erase_block_size = flash_setting.block_size # Block size (varies by device)
planes_per_lun = flash_setting.planes       # Parallelism factor
nand_type = flash_setting.nand_type         # SLC/TLC/QLC detection
```

### SLC Block Mode

When configuring SLC mode without details:

```python
# Default SLC mode behavior
enable_slc_mode = True
slc_block_ratio = auto  # Let device select optimal ratio

# SLC benefits
# - Better write performance
# - Lower error rates
# - Trade: reduced capacity
```

---

## VB (Virtual Block) Information

### Getting VB Metadata

```python
# Default VB information retrieval
vb_list_data = get_VB_group(show=False)  # Get all VB metadata

# Common VB queries
vpct_data = get_all_VPCT_VBINFO_values()  # Virtual Page Count Table
vbinfo = get_VPCT_VBINFO_value(vb_index)   # For specific VB
```

### VB State Defaults

```python
# When checking VB status
expected_vpct = api.VPCT_values(bytearray(4))
expected_vpct.VPC.value = expected_block_count

expected_vbinfo = api.VBINFO_values(bytearray(2))
expected_vbinfo.VBINFO_BIT_PSA.value = 0      # Not PSA block
expected_vbinfo.VBINFO_BIT_PMNTRAINEN.value = 0  # Not training block
```

---

## Background Operation Control

### Enabling/Disabling Background Ops

```python
# Default vendor command for background ops
enable_background_operation = True
bkops_timeout = 3600  # seconds (1 hour max)

# Query background ops status
bkops_status = read_fw_value('gBkopsStatus')
# Values: IDLE, TRIGGERED, URGENT, or RUNNING
```

---

## Temperature Management

### Temperature Reading

```python
# Default temperature monitoring
current_temp = read_fw_value('gThermalMgr.current_temp')

# Temperature sensor defaults
temp_threshold_warning = 80  # Celsius
temp_threshold_critical = 85  # Celsius

# Thermal throttling
throttle_on_warning = True
throttle_on_critical = True
```

### Thermal Protection

```python
# Default thermal protection mode (from ThermalProtection patterns)
thermal_mode = api.ThermalProtectionMode.HOT_COLD  # Both hot & cold

# Test temperature scenarios
test_cold = -5   # Celsius (cold test)
test_normal = 25  # Celsius (room temperature)
test_hot = 50    # Celsius (operating limit)
```

---

## RPMB Management

### RPMB Key Programming

```python
# Default RPMB key initialization
rpmb_region = RPMBRegion.REGION_0
key_size = 32  # bytes (256-bit)
clear_on_init = True

# Key programming sequence
vuc_clear_rpmb_key(RPMBRegion.REGION_0)  # Clear existing
rpmb_key_programming()  # Program new key
```

### RPMB Operations

```python
# Default RPMB operation defaults
write_counter_reset = True  # Reset on init
authenticated_write_enabled = True
replay_protection_enabled = True

# Operation result handling
operation_timeout = 5000  # milliseconds
max_retries = 3
```

---

## Device Identification

### Getting Device Info

```python
# Default identification queries
asic_id = get_asic_id()                    # ASIC version
fw_version = get_fw_version()              # Firmware version
fw_config = get_fw_configuration()         # Feature set
device_uid = read_uid()                    # Unique device ID

# Efuse data (one-time programmable)
efuse_data = get_efuse()  # Read OTP values
```

