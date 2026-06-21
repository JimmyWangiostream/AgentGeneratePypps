---
type: entity
title: "UFS Flags"
tags: [flags, query, attribute, idn]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
---

# UFS Flags

Flags are single-bit boolean values on the UFS device, accessed via QUERY REQUEST UPIU. Each flag has an IDN (Index Number) and supports specific OPCODE operations.

## Access OPCODEs

| OPCODE | Value | Description |
|--------|-------|-------------|
| READ FLAG | 05h | Read current flag value (0 or 1) |
| SET FLAG | 06h | Set flag to 1 |
| CLEAR FLAG | 07h | Clear flag to 0 |
| TOGGLE FLAG | 08h | Toggle current flag value |

The flag value is returned in **byte 23** of the QUERY RESPONSE UPIU (Flag Value field).

Not all flags support all OPCODEs — see the Access column below.

## Flag Table

| IDN | Name | Access | Default | Description |
|-----|------|--------|---------|-------------|
| 01h | fDeviceInit | Set only | 0 | Device sets this to 1 during initialization; host polls until cleared to 0 before sending normal commands |
| 02h | fPermanentWPEn | Write once | 0 | Enables permanent write protection on LUs with bLUWriteProtect=02h; irreversible |
| 03h | fPowerOnWPEn | Power-on-reset | 0 | Enables power-on write protection on LUs with bLUWriteProtect=01h; cleared on power cycle or HW reset |
| 04h | fBackgroundOpsEn | Volatile | 1 | Enables background operations (e.g., garbage collection); default ON |
| 05h | fDeviceLifeSpanModeEn | Volatile | 0 | Enables device life span monitoring mode |
| 06h | fPurgeEnable | Write-only volatile | 0 | Starts purge operation; auto-cleared by device when done; requires empty command queue |
| 07h | fRefreshEnable | Write-only volatile | 0 | Starts refresh (data relocation) operation |
| 08h | fPhyResourceRemoval | Persistent | 0 | Triggers physical resource removal (Dynamic Capacity feature); set by host to reduce physical memory |
| 09h | fBusyRTC | Read Only | 0 | 1 = RTC update is in progress; host should not write dSecondsPassed while set |
| 0Bh | fPermanentlyDisableFwUpdate | Write once | 0 | Permanently disables firmware update (FFU); irreversible when set |
| 0Eh | fWriteBoosterEn | Volatile | 0 | Enables WriteBooster SLC buffer for write acceleration |
| 0Fh | fWriteBoosterBufferFlushEn | Volatile | 0 | Enables automatic flush of WriteBooster buffer to MLC |
| 10h | fWriteBoosterBufferFlushDuringHibernate | Volatile | 0 | Enables WriteBooster buffer flush during UniPro Hibernate state |
| 13h | fUnpinEn | Volatile | 0 | Enables unpinning of Pinned data in WriteBooster partial flush mode |
| 80h–FFh | Vendor specific flags | Vendor defined | — | Vendor-defined flags; behavior is device-specific |

## Access Type Semantics

| Access Type | Meaning |
|-------------|---------|
| **Set only** | Only SET FLAG (06h) is valid; CLEAR and TOGGLE not allowed |
| **Write once** | Can be set once; cannot be cleared afterwards |
| **Power-on-reset** | Cleared on power cycle or hardware reset (RST_n) |
| **Volatile** | Can be freely set/cleared; reset to default on power cycle |
| **Write-only volatile** | Only write allowed; auto-cleared by device |
| **Persistent** | Survives power cycles; stored in non-volatile memory |
| **Read Only** | Only READ FLAG (05h) is valid |

## Usage Examples (Python API)

### Read a flag
```python
import api
from Script.api import cmd_seq as ExecuteCMD

# Read fBackgroundOpsEn (04h)
value = api.read_flag(idn=api.FlagIDN.BACKGROUND_OPS_EN)
print(f"Background Ops Enabled: {value}")
```

### Set a flag
```python
# Enable WriteBooster
api.set_flag(idn=api.FlagIDN.WRITE_BOOSTER_EN)
```

### Clear a flag
```python
# Disable WriteBooster
api.clear_flag(idn=api.FlagIDN.WRITE_BOOSTER_EN)
```

### Poll fDeviceInit during initialization
```python
import time

# Wait for device to complete initialization
timeout_sec = 30
start = time.time()
while True:
    val = api.read_flag(idn=api.FlagIDN.DEVICE_INIT)
    if val == 0:
        break
    if time.time() - start > timeout_sec:
        raise TimeoutError("Device init timed out")
    time.sleep(0.1)
```

### Purge flow
```python
# 1. Ensure command queue is empty, then set purge flag
api.set_flag(idn=api.FlagIDN.PURGE_ENABLE)

# 2. Monitor bPurgeStatus until completed
while True:
    status = api.read_attribute(idn=api.AttributeIDN.PURGE_STATUS)
    if status == api.PurgeStatus.COMPLETED:
        break
    time.sleep(1)
```

## Key Notes

- **fDeviceInit flow**: Device sets this flag to 1 at startup; host must poll until 0 before sending any UCS commands. Valid UPIU types during initialization phase are defined in Table 13.2 of the spec.
- **Purge restriction**: During purge (fPurgeEnable=1), only descriptor/attribute/flag reads are allowed, plus writing fPurgeEnable=0 to interrupt.
- **WriteBooster flags**: fWriteBoosterEn must be set before fWriteBoosterBufferFlushEn has effect. The WriteBooster buffer type (LU-dedicated vs shared) is set in the Device Descriptor (offset 54h).

## Related

[[attributes]] | [[upiu]] | [[write-booster]] | [[psa-state]] | [[spec]]
