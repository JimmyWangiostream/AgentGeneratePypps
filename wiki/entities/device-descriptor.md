---
type: entity
title: "Device Descriptor (IDN 00h)"
tags: [descriptor, device, query, ufs]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
aliases: [Device Descriptor, IDN 00h, bDescriptorIDN 00h]
---

# Device Descriptor (IDN 00h)

The Device Descriptor is the top-level descriptor of a UFS device. It identifies the manufacturer, product, spec version, LU count, and device capabilities. It is read-only and accessed via QUERY REQUEST with OPCODE=01h (READ DESCRIPTOR).

- **IDN**: 00h
- **bLength**: 59h (89 bytes for UFS 4.1)
- **Access**: Read only (OPCODE=01h); host queries INDEX=00h, SELECTOR=00h

## Field Table

| Offset | Field | Value / Notes |
|--------|-------|---------------|
| 00h | bLength | 59h |
| 01h | bDescriptorIDN | 00h |
| 02h | bDevice | Device class |
| 03h | bDeviceClass | |
| 04h | bDeviceSubClass | |
| 05h | bProtocol | |
| 06h | bNumberLU | Number of enabled LUs |
| 07h | bNumberWLU | Number of Well-Known LUs |
| 08h | bBootEnable | 00h=disabled, 01h=bootable, 02h=permanent-bootable |
| 09h | bDescrAccessEn | |
| 0Ah | bInitPowerMode | Power mode after init |
| 0Bh | bHighPriorityLUN | 7Fh=equal priority; or specific LUN index |
| 0Ch | bSecureRemovalType | 00h=erase, 01h=overwrite+erase, 02h=overwrite+complement+random+erase, 03h=vendor |
| 0Dh | bSecurityLU | 01h=RPMB supported |
| 0Eh | bBackgroundOpsTermLat | Background ops termination latency (10ms units) |
| 0Fh | bInitActiveICCLevel | Default ICC level |
| 10h–11h | wSpecVersion | 0410h for UFS 4.1 |
| 12h–13h | wManufactureDate | |
| 14h | iManufacturerName | Index into [[string-descriptor]] |
| 15h | iProductName | Index into [[string-descriptor]] |
| 16h | iSerialNumber | Index into [[string-descriptor]] |
| 17h | iOemID | Index into [[string-descriptor]] |
| 18h–19h | wManufacturerID | JEDEC JEP106 ID |
| 1Ah | bUD0BaseOffset | |
| 1Bh | bUDConfigPLength | |
| 1Ch | bDeviceRTTCap | Max simultaneous RTTs device supports |
| 1Dh–1Eh | wPeriodicRTCUpdate | |
| 1Fh | bUFSFeaturesSupport | bit[0]=FFU, bit[1]=PSA, bit[2]=Device Life Span, bit[3]=Refresh |
| 20h | bFFUTimeout | Max FFU WRITE BUFFER time |
| 21h | bQueueDepth | Shared queue depth (0=per-LU queue model) |
| 22h–23h | wDeviceVersion | |
| 24h | bNumSecureWPArea | Max secure write protect areas |
| 25h–28h | dPSAMaxDataSize | Max PSA data size (4KB units) |
| 29h | bPSAStateTimeout | |
| 2Ah | iProductRevisionLevel | Index into [[string-descriptor]] |
| 4Fh–52h | dExtendedUFSFeaturesSupport | 32-bit; bit[0]=WriteBooster, bit[2]=FFU ext, bit[3]=Refresh, bit[4]=Dynamic Capacity, bit[5]=WriteBooster type, bit[6]=Advanced RPMB, bit[13]=HID, bit[14]=FastRecovery |
| 53h | bWriteBoosterBufferPreserveUserSpaceEn | |
| 54h | bWriteBoosterBufferType | 00h=LU dedicated buffer, 01h=shared buffer |
| 55h–58h | dNumSharedWriteBoosterBufferAllocUnits | For shared buffer type only |

## Key Fields Explained

### wSpecVersion (10h–11h)
Identifies the UFS specification revision. UFS 4.1 = `0410h`. Used to determine supported features.

### bNumberLU (06h)
Count of currently enabled Normal LUs. Ranges from 0 to bMaxNumberLU (from [[geometry-descriptor]]).

### dExtendedUFSFeaturesSupport (4Fh–52h)
32-bit bitmap of optional features:
- **bit[0]**: WriteBooster supported
- **bit[5]**: WriteBooster buffer type (0=LU-dedicated, 1=shared)
- **bit[13]**: HID (Host Initiated Defragmentation)
- **bit[14]**: FastRecovery

### bWriteBoosterBufferType (54h)
- `00h` — Each LU has its own dedicated WB buffer
- `01h` — Single shared WB buffer across all LUs

## Usage Example

```python
# Read Device Descriptor via QUERY REQUEST
resp = query_read_descriptor(idn=0x00, index=0x00, selector=0x00)

spec_version = (resp[0x10] << 8) | resp[0x11]  # Should be 0x0410 for UFS 4.1
num_lu       = resp[0x06]
wb_type      = resp[0x54]  # 0=dedicated, 1=shared
ext_features = int.from_bytes(resp[0x4F:0x53], 'big')
wb_supported = bool(ext_features & 0x01)
```

## Related

[[configuration-descriptor]] | [[unit-descriptor]] | [[geometry-descriptor]] | [[device-health-descriptor]] | [[lun]] | [[write-booster]]

## Sources

- JEDEC UFS 4.1 (JESD220G) Table 14.4 — Device Descriptor
- Section 1.1 Descriptors, UFS41_Structured_Knowledge_Report
