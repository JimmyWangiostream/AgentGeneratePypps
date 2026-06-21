---
type: entity
title: "UFS Attributes"
tags: [attributes, query, idn, power-mode, psa, writebooster]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
---

# UFS Attributes

Attributes are multi-byte device parameters, accessed via QUERY REQUEST UPIU (OPCODE 03h READ ATTRIBUTE / 04h WRITE ATTRIBUTE). The value field is 64-bit big-endian right-justified in the QUERY RESPONSE.

## Query OPCODEs

| OPCODE | Value | Description |
|--------|-------|-------------|
| READ ATTRIBUTE | 03h | Read current attribute value |
| WRITE ATTRIBUTE | 04h | Write new attribute value |

The IDN, INDEX, and SELECTOR fields address each attribute. Most attributes use INDEX=0 and SELECTOR=0; exceptions include wContextConf (INDEX=LUN, SELECTOR=ContextID).

## Attribute Table

| IDN | Name | Access | Size | MDV | Description / Enum |
|-----|------|--------|------|-----|-------------------|
| 00h | bBootLunEn | Persistent | 1B | 00h | 00h=Boot LU disabled, 01h=Boot LU A active, 02h=Boot LU B active |
| 01h | Reserved | — | — | — | Reserved (HPB extension) |
| 02h | bCurrentPowerMode | Read only | 1B | — | Current device power state — see enum below |
| 03h | bActiveICCLevel | Volatile | 1B | — | Active current level 00h–0Fh; default = bInitActiveICCLevel from Device Descriptor |
| 04h | bOutOfOrderDataEn | Write once | 1B | — | 00h=OOO disabled, 01h=both IN/OUT, 02h=DATA IN only, 03h=DATA OUT only |
| 05h | bBackgroundOpStatus | Read only | 1B | — | 00h=not required, 01h=non-critical, 02h=performance impact, 03h=critical |
| 06h | bPurgeStatus | Read only | 1B | — | 00h=idle, 01h=in progress, 02h=stopped, 03h=completed, 04h=failed queue not empty, 05h=general failure |
| 07h | bMaxDataInSize | Persistent | 1B | — | Max DATA IN UPIU size in 512-byte units; default = bMaxInBufferSize |
| 08h | bMaxDataOutSize | Persistent | 1B | — | Max DATA OUT UPIU size in 512-byte units; default = bMaxOutBufferSize |
| 09h | dDynCapNeeded | Read only | 4B | — | Dynamic Capacity: amount of physical memory to release per LU (array/LU index) |
| 0Ah | bRefClkFreq | Persistent | 1B | 03h | Reference clock frequency: 00h=19.2MHz, 01h=26MHz, 02h=38.4MHz, 03h=52MHz |
| 0Bh | bConfigDescrLock | Write once | 1B | — | 00h=unlocked, 01h=locked; locks all Configuration Descriptors permanently |
| 0Ch | bMaxNumOfRTT | Persistent | 1B | 02h | Max outstanding RTTs; shall not exceed bDeviceRTTCap in Device Descriptor |
| 0Dh | wExceptionEventControl | Volatile | 2B | — | Bits 0–11: enable/disable individual exception events |
| 0Eh | wExceptionEventStatus | Read only | 2B | — | Exception event status bits — see enum below |
| 0Fh | dSecondsPassed | Write-only volatile | 4B | — | Seconds since power-on; used for RTC update; check fBusyRTC=0 first |
| 10h | wContextConf | Volatile | 2B | — | Context configuration; INDEX=LUN, SELECTOR=ContextID (01h–0Fh) |
| 11h | dCorrPrgBlkNum | Obsolete | — | — | Deprecated in UFS 4.x |
| 14h | bDeviceFFUStatus | Read Only | 1B | — | FFU result: 00h=no info, 01h=successful, 02h=corruption, 03h=internal error, 04h=version mismatch, FFh=general error |
| 15h | bPSAState | Persistent | 1B | — | PSA state machine: 00h=Off, 01h=Pre-soldering, 02h=Loading Complete, 03h=Soldered — see [[psa-state]] |
| 16h | dPSADataSize | Persistent | 4B | — | PSA pre-load data size in 4KB units; must be ≤ dPSAMaxDataSize |
| 2Ah | bEXTIIDEn | Write once | 1B | 00h | 00h=EXT_IID field ignored, 01h=EXT_IID valid (enables 8-bit Initiator ID) |
| 2Ch | bRefreshStatus | Read only | 1B | — | Same states as bPurgeStatus (00h=idle … 05h=general failure) |
| 2Dh | bRefreshFreq | Persistent | 1B | — | Refresh frequency in months: 01h=1 month, FFh=255 months |
| 2Eh | bRefreshUnit | Persistent | 1B | — | 00h=minimum device capability, 01h=100% of device |
| 2Fh | bRefreshMethod | Persistent | 1B | 00h | 00h=not defined, 01h=Manual-Force, 02h=Manual-Selective |
| 30h | qTimestamp | Write only | 8B | — | Nanoseconds since Jan 1, 1970 UTC (for timestamp logging) |
| 35h | bDefragOperation | Volatile | 1B | — | HID: 00h=disabled, 01h=analysis only, 02h=analysis+defrag |
| 36h | dHIDAvailableSize | Read only | 4B | — | Total fragmented size in 4KB units; FFFFFFFFh=no valid info |
| 37h | dHIDSize | Persistent | 4B | FFFFFFFFh | Size limit per HID defrag operation in 4KB units |
| 38h | bHIDProgressRatio | Read only | 1B | — | HID progress: 00h=0% to 64h=100% |
| 39h | bHIDState | Read only | 1B | — | HID state: 00h=idle, 01h=analysis, 02h=defrag required, 03h=defrag in progress, 04h=completed, 05h=not required |
| 3Dh | bWriteBoosterBufferResizeEn | Write-only volatile | 1B | — | 00h=idle, 01h=decrease buffer, 02h=increase buffer |
| 3Fh | bWriteBoosterBufferPartialFlushMode | Persistent | 1B | — | 00h=no partial flush, 01h=FIFO, 02h=Pinned (retain GROUP NUMBER=11000b data) |
| 47h | wHostHintCacheSize | Persistent | 2B | — | Host hint cache size for out-of-order data transfer |
| 80h–FFh | Vendor specific | Vendor defined | — | — | Vendor-specific attributes |

## bCurrentPowerMode Enum (IDN 02h)

| Value | State | Description |
|-------|-------|-------------|
| 00h | Idle | Powered on, not active; VCC may be removed |
| 10h | Pre-Active | Transitioning to Active state |
| 11h | Active | Full operation; VCC + VCCQ + VCCQ2 all on |
| 20h | Pre-Sleep | Transitioning to UFS-Sleep |
| 22h | UFS-Sleep | Reduced power; VCC may be off; UniPro link in Hibernate |
| 30h | Pre-PowerDown | Transitioning to UFS-PowerDown |
| 33h | UFS-PowerDown | Minimal power; device retains data |
| 44h | UFS-DeepSleep | Deepest power saving (optional feature) |

## wExceptionEventStatus Bit Definitions (IDN 0Eh)

| Bit | Event | Description |
|-----|-------|-------------|
| 0 | TOO_HIGH_TEMP | Device temperature exceeds upper threshold |
| 1 | TOO_LOW_TEMP | Device temperature below lower threshold |
| 2 | URGENT_BKOPS | Background operations urgently needed |
| 3 | PERFORMANCE_THROTTLING | Device throttling due to thermal or other condition |
| 4 | WRITEBOOSTER_FLUSH_NEEDED | WriteBooster buffer needs flushing |
| 5 | DYNAMIC_CAPACITY_NEEDED | Physical memory release requested |
| 6 | CORRECTION_NEEDED | Data correction operation needed |
| 7 | DEVICE_HEALTH_EVENT | Device health status changed |
| 8 | DEVICE_LEVEL_EXCEPTION | Device-level exception occurred |

The host detects events via the EVENT_ALERT bit[0] in RESPONSE UPIU Device Information field, then reads wExceptionEventStatus. Device clears the bit when status is read.

Control individual events via wExceptionEventControl (IDN 0Dh) — same bit positions.

## bRefClkFreq Enum (IDN 0Ah)

| Value | Frequency | Max RMS Jitter | Notes |
|-------|-----------|----------------|-------|
| 00h | 19.2 MHz | 5.9 ps | Not suitable for HS-GEAR5 |
| 01h | 26.0 MHz | 4.6 ps | Not suitable for HS-GEAR5 |
| 02h | 38.4 MHz | 3.5 ps | |
| 03h | 52.0 MHz | 2.8 ps | Default (MDV=03h); recommended for HS-GEAR5 |

## Usage Examples (Python API)

### Read an attribute
```python
import api

# Read current power mode
power_mode = api.read_attribute(idn=api.AttributeIDN.CURRENT_POWER_MODE)
print(f"Power mode: 0x{power_mode:02X}")

# Read PSA state
psa_state = api.read_attribute(idn=api.AttributeIDN.PSA_STATE)
print(f"PSA State: 0x{psa_state:02X}")
```

### Write an attribute
```python
# Set PSA data size to 16 GB (in 4KB units)
BLOCK4K_SIZE_16G = 16 * 1024 * 1024 * 1024 // 4096
api.write_attribute(idn=api.AttributeIDN.PSA_DATA_SIZE, val=BLOCK4K_SIZE_16G)

# Set max RTT to 4
api.write_attribute(idn=api.AttributeIDN.MAX_NUM_OF_RTT, val=4)

# Enable refresh (Manual-Force, 100% of device)
api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=1)  # Manual-Force
api.write_attribute(idn=api.AttributeIDN.REFRESH_UNIT, val=1)    # 100%
```

### Check exception events
```python
# Enable all exception events
api.write_attribute(idn=api.AttributeIDN.EXCEPTION_EVENT_CONTROL, val=0x01FF)

# Read event status after EVENT_ALERT detected
status = api.read_attribute(idn=api.AttributeIDN.EXCEPTION_EVENT_STATUS)
if status & (1 << 2):
    print("URGENT_BKOPS: Background operations urgently needed")
if status & (1 << 4):
    print("WRITEBOOSTER_FLUSH_NEEDED")
```

### Context configuration (wContextConf)
```python
from Script.api import cmd_seq as ExecuteCMD

# Set ContextID 1 for LUN 0
write_attr = ExecuteCMD.WriteAttribute()
write_attr.assign(idn=api.AttributeIDN.CONTEXT_CONF, index=0, selector=1)  # LUN=0, ContextID=1
write_attr.set_attr(value)
ExecuteCMD.enqueue(write_attr)
ExecuteCMD.send()
```

## Key Notes

- **bConfigDescrLock**: Once written to 01h, all Configuration Descriptors are permanently locked. Cannot be reversed. Only valid while not already locked.
- **dPSADataSize vs dPSAMaxDataSize**: dPSADataSize (IDN 16h, writable) must not exceed dPSAMaxDataSize (Device Descriptor offset 25h–28h, read-only hardware limit). Writing a larger value returns GENERAL_FAILURE (FFh).
- **bDeviceFFUStatus**: Valid only after firmware update and re-initialization sequence. Read after power cycle following FFU.
- **HID (bHIDState IDN 39h)**: After reading state 04h (Completed), device resets all HID attributes. HID is aborted if any medium-modifying command arrives during operation.

## Related

[[flags]] | [[upiu]] | [[psa-state]] | [[write-booster]] | [[lun]] | [[spec]]
