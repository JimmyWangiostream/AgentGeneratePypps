---
type: entity
title: "Configuration Descriptor (IDN 01h)"
tags: [descriptor, configuration, query, ufs, lun]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
aliases: [Configuration Descriptor, IDN 01h, Config Descriptor, bDescriptorIDN 01h]
---

# Configuration Descriptor (IDN 01h)

The Configuration Descriptor defines how the UFS device is partitioned into Logical Units. It is writable before `bConfigDescrLock` is set, and contains per-LU provisioning parameters for up to 8 LUs per configuration block.

- **IDN**: 01h
- **INDEX**: 00h–03h (each index covers 8 LUs; total up to 32 LUs)
- **Access**: Read (OPCODE=01h) / Write (OPCODE=02h) — write allowed only when `bConfigDescrLock = 0`

## Configuration Descriptor Structure

A Configuration Descriptor (one INDEX) consists of:
1. **Header section** — device-level configuration fields
2. **Unit Descriptor Parameter blocks** — one block per LU (up to 8 LUs per index)

### Header Fields

| Offset | Field | Value / Notes |
|--------|-------|---------------|
| 00h | bLength | Total length of this configuration descriptor |
| 01h | bDescriptorIDN | 01h |
| 02h | bConfDescContinue | 00h=this is the last config descriptor, 01h=more follow (next INDEX) |
| 03h | bBootEnable | 00h=disabled, 01h=enabled, 02h=permanent |
| 04h | bDescrAccessEn | |
| 05h | bInitPowerMode | Power mode after init |
| 06h | bHighPriorityLUN | 7Fh=equal priority; or specific LUN |
| 07h | bSecureRemovalType | 00h=erase, 01h=overwrite+erase, 02h=overwrite+complement+random+erase, 03h=vendor |
| 08h | bInitActiveICCLevel | Default ICC level |
| 09h–0Ah | wPeriodicRTCUpdate | |
| 0Bh | bRPMBRegionEnable | bits[0–3]=region 0–3 enabled; bit[4]=Advanced RPMB mode |
| 0Ch | bRPMBRegion0Size | Size in 128KB units (0=disabled) |
| 0Dh | bRPMBRegion1Size | Size in 128KB units |
| 0Eh | bRPMBRegion2Size | Size in 128KB units |
| 0Fh | bRPMBRegion3Size | Size in 128KB units |
| 10h | bWriteBoosterBufferPreserveUserSpaceEn | |
| 11h | bWriteBoosterBufferType | 00h=LU dedicated, 01h=shared buffer |
| 12h–15h | dNumSharedWriteBoosterBufferAllocUnits | For shared WB buffer type |

### Per-LU Unit Descriptor Parameter Block

Starting from offset `bUD0BaseOffset` (from [[device-descriptor]]), each LU has a block of `bUDConfigPLength` bytes:

| Relative Offset | Field | Value / Notes |
|----------------|-------|---------------|
| 00h | bLUEnable | 00h=disabled, 01h=enabled |
| 01h | bBootLunID | 00h=not a boot LU, 01h=Boot LU A, 02h=Boot LU B |
| 02h | bLUWriteProtect | 00h=not protected, 01h=power-on WP, 02h=permanent WP |
| 03h | bMemoryType | 00h=Normal, 03h=SLC, etc. |
| 04h–07h | dNumAllocUnits | Allocation units for this LU (see formula below) |
| 08h | bDataReliability | 00h=not reliable, 01h=reliable write |
| 09h | bLogicalBlockSize | 0Ch=4096 bytes (minimum for UFS) |
| 0Ah | bProvisioningType | 00h=full provisioned, 02h=thin (TPRZ=0), 03h=thin (TPRZ=1) |
| 0Bh–0Ch | wContextCapabilities | |

## Capacity Allocation Formula

```
dNumAllocUnits = CEILING(
    (LUCapacity × CapAdjFactor) /
    (bAllocationUnitSize × dSegmentSize × 512)
)
```
Where `bAllocationUnitSize` and `dSegmentSize` come from [[geometry-descriptor]].

## Locking the Configuration

Once the device is configured, the configuration can be permanently locked:

```python
# Lock all Configuration Descriptors permanently (write-once)
write_attribute(idn=0x0B, value=0x01)  # bConfigDescrLock = 1
```

After locking, any WRITE DESCRIPTOR to IDN=01h returns QUERY RESPONSE `F7h` (not writable).

## Pagination: Multiple Indexes

For devices with more than 8 LUs, multiple INDEX values are used:
- INDEX=00h: LU 0–7
- INDEX=01h: LU 8–15
- INDEX=02h: LU 16–23
- INDEX=03h: LU 24–31

`bConfDescContinue = 01h` in a header signals the host to read the next INDEX before considering configuration complete.

## Usage Example

```python
# Read Configuration Descriptor for LU 0-7
resp = query_read_descriptor(idn=0x01, index=0x00, selector=0x00)

boot_enable       = resp[0x03]
conf_continue     = resp[0x02]   # 00h = last, 01h = more indexes
wb_buffer_type    = resp[0x11]   # 00=dedicated, 01=shared

# Write Configuration Descriptor (only if bConfigDescrLock == 0)
payload = build_config_descriptor(lus=[...])
query_write_descriptor(idn=0x01, index=0x00, selector=0x00, data=payload)
```

## Related

[[device-descriptor]] | [[unit-descriptor]] | [[geometry-descriptor]] | [[lun]] | [[write-booster]]

## Sources

- JEDEC UFS 4.1 (JESD220G) — Configuration Descriptor section
- Section 1.1 Descriptors, UFS41_Structured_Knowledge_Report
