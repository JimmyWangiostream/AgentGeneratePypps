---
type: entity
title: "Unit Descriptor (IDN 02h)"
tags: [descriptor, lun, unit, query, ufs, provisioning]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
aliases: [Unit Descriptor, IDN 02h, LU Descriptor, bDescriptorIDN 02h]
---

# Unit Descriptor (IDN 02h)

The Unit Descriptor describes the runtime parameters of a single Logical Unit. One Unit Descriptor exists per LU (Normal LU 0–31, RPMB, Boot). It is accessed via QUERY REQUEST using OPCODE=01h (READ DESCRIPTOR), with INDEX=LUN number.

- **IDN**: 02h
- **INDEX**: LUN number (00h–1Fh for Normal LUs; additional values for Well-Known LUs)
- **Access**: Read only (OPCODE=01h); parameters are configured via [[configuration-descriptor]]

## Field Table

| Offset | Field | Value / Notes |
|--------|-------|---------------|
| 00h | bLength | Length of this descriptor |
| 01h | bDescriptorIDN | 02h |
| 02h | bUnitIndex | LUN index of this unit |
| 03h | bLUEnable | 00h=disabled, 01h=enabled |
| 04h | bBootLunID | 00h=not a boot LU, 01h=Boot LU A, 02h=Boot LU B |
| 05h | bLUWriteProtect | 00h=not protected, 01h=power-on WP, 02h=permanent WP |
| 06h | bLUQueueDepth | Per-LU queue depth (0=uses device shared queue) |
| 07h | bPSASensitive | 01h=PSA sensitive (filled/unmapped during PSA flow) |
| 08h | bMemoryType | 00h=Normal, 03h=SLC, other values vendor-specific |
| 09h | bDataReliability | 00h=not reliable, 01h=reliable write (power-loss safe) |
| 0Ah | bLogicalBlockSize | 0Ch=4096 bytes (minimum for UFS 4.1) |
| 0Bh–0Eh | qLogicalBlockCount | 64-bit (split across 0Bh-12h); total LBA count |
| 0Fh–12h | (continued qLogicalBlockCount) | |
| 13h–16h | dEraseBlockSize | Erase block size in bytes |
| 17h | bProvisioningType | 00h=full provisioned, 02h=thin (TPRZ=0), 03h=thin (TPRZ=1) |
| 18h–1Fh | qPhyMemResourceCount | Physical memory resource count (64-bit) |
| 20h–21h | wContextCapabilities | Bit per context ID; 1=supported |
| 22h | bLargeUnitGranularity_M1 | Large unit granularity minus 1 |

## RPMB Unit Descriptor Additional Fields

When INDEX targets the RPMB Well-Known LU (C4h), additional fields are present:

| Offset | Field | Value / Notes |
|--------|-------|---------------|
| — | bRPMBRegionEnable | bits[0–3]=region 0–3 enabled; bit[4]=Advanced RPMB mode |
| — | bRPMBRegion0Size | Size of RPMB region 0 in 128KB units (0=disabled) |
| — | bRPMBRegion1Size | Size of RPMB region 1 in 128KB units |
| — | bRPMBRegion2Size | Size of RPMB region 2 in 128KB units |
| — | bRPMBRegion3Size | Size of RPMB region 3 in 128KB units |
| — | bRPMBLifeTimeEst | 00h=no info, 01h–0Ah=0–100% used (10% steps), 0Bh=exceeded |

## Field Details

### bLUEnable (03h)
- `00h` — LU is disabled; not accessible
- `01h` — LU is enabled; all UCS commands supported

### bBootLunID (04h)
- `00h` — Not a boot LU
- `01h` — This is Boot LU A (selected when `bBootLunEn` attribute = 01h)
- `02h` — This is Boot LU B (selected when `bBootLunEn` attribute = 02h)

### bLUWriteProtect (05h)
- `00h` — Not write protected
- `01h` — Power-on write protection (active when flag `fPowerOnWPEn` is set)
- `02h` — Permanent write protection (active when flag `fPermanentWPEn` is set)

### bLogicalBlockSize (0Ah)
Encoded as power of 2: `LBS = 2^bLogicalBlockSize` bytes.
- `0Ch` (12) = 4096 bytes — minimum required for UFS

### bProvisioningType (17h)
- `00h` — Fully provisioned (all physical blocks pre-allocated)
- `02h` — Thin provisioned, TPRZ=0 (unmapped LBAs read as undefined data)
- `03h` — Thin provisioned, TPRZ=1 (unmapped LBAs read as zeros)

### bPSASensitive (07h)
- `01h` — LU is PSA-sensitive; during PSA flow (see [[psa-state]]), host fills and unmaps this LU
- Normal memory LUs are typically PSA-sensitive; Enhanced Memory LUs are not

## Usage Example

```python
# Read Unit Descriptor for LUN 0
resp = query_read_descriptor(idn=0x02, index=0x00, selector=0x00)

lun_enable       = resp[0x03]   # 00=disabled, 01=enabled
boot_lun_id      = resp[0x04]   # 00=none, 01=Boot A, 02=Boot B
write_protect    = resp[0x05]
memory_type      = resp[0x08]
block_size_exp   = resp[0x0A]   # Logical block size = 2^block_size_exp
provisioning     = resp[0x17]   # 00=full, 02=thin TPRZ=0, 03=thin TPRZ=1

logical_block_count = int.from_bytes(resp[0x0B:0x13], 'big')
capacity_bytes   = logical_block_count * (2 ** block_size_exp)

# Read RPMB Unit Descriptor
rpmb_resp = query_read_descriptor(idn=0x02, index=0xC4, selector=0x00)
```

## Related

[[configuration-descriptor]] | [[device-descriptor]] | [[lun]] | [[psa-state]] | [[write-booster]] | [[geometry-descriptor]]

## Sources

- JEDEC UFS 4.1 (JESD220G) — Unit Descriptor section
- Section 1.1 Descriptors and 1.5 Logical Units, UFS41_Structured_Knowledge_Report
