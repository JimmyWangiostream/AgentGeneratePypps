---
type: concept
title: "Thin Provisioning and UNMAP"
tags: [thin-provisioning, unmap, provisioning-type, scsi-commands, lun]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
---

# Thin Provisioning and UNMAP

Thin Provisioning is a UFS LU-level configuration that allows the host to de-allocate logical blocks, notifying the device that certain LBA ranges are no longer in use. This enables the device to reclaim physical NAND resources associated with those addresses.

## `bProvisioningType` — LU Provisioning Mode

Configured per-LU in the Unit Descriptor (IDN 02h):

| Value | Mode | UNMAP Support | Unmapped LBA Read Behavior |
|-------|------|--------------|--------------------------|
| 00h | Full provisioning | Not supported | Returns data (implementation-defined) |
| 02h | Thin provisioning, TPRZ=0 | Supported | Returns any data (not guaranteed to be zeros) |
| 03h | Thin provisioning, TPRZ=1 | Supported | Returns zeros (secure erase semantics) |

`bProvisioningType` is set in the Configuration Descriptor (via Unit Descriptor fields). It is applied at LU configuration time (before `bConfigDescrLock = 1`).

### TPRZ Bit

TPRZ (Thin Provisioning Return Zeros) is reported in the READ CAPACITY (16) response data:
- TPRZ = 0 (from `bProvisioningType = 02h`): reading an unmapped LBA may return any data
- TPRZ = 1 (from `bProvisioningType = 03h`): reading an unmapped LBA returns all zeros

The TPE (Thin Provisioning Enabled) bit in READ CAPACITY (16) is set for both 02h and 03h.

## UNMAP Command (Opcode 42h)

The UNMAP command de-allocates one or more LBA extents on a thin-provisioned LU. The device then marks those LBAs as unmapped; subsequent reads return data per TPRZ policy.

### UNMAP Parameter List Structure

```
Byte 0–1: UNMAP DATA LENGTH (total length of following data, not including these 2 bytes)
Byte 2–3: UNMAP BLOCK DESCRIPTOR DATA LENGTH (total bytes of block descriptors)
Byte 4–7: Reserved
Byte 8+:  UNMAP Block Descriptors (16 bytes each)
```

### UNMAP Block Descriptor (16 bytes per entry)

| Bytes | Field | Size |
|-------|-------|------|
| 0–7 | UNMAP LOGICAL BLOCK ADDRESS | 8 bytes (LBA, big-endian) |
| 8–11 | NUMBER OF LOGICAL BLOCKS | 4 bytes (count) |
| 12–15 | Reserved | 4 bytes |

Multiple descriptors can be included in a single UNMAP command. If the `UNMAP BLOCK DESCRIPTOR DATA LENGTH` is not a multiple of 16, the last incomplete descriptor is ignored.

### UNMAP Constraints

- UNMAP is only supported on thin-provisioned LUs (`bProvisioningType = 02h` or `03h`)
- UNMAP is NOT supported on full-provisioned LUs (`bProvisioningType = 00h`); issuing UNMAP to a full-provisioned LU returns CHECK CONDITION with ILLEGAL REQUEST
- The `ANCHOR` field in the UNMAP CDB shall be set to 0

## PSA and UNMAP

UNMAP plays a key role in the PSA flow:

1. Before starting a PSA flow, host issues UNMAP for the entire LBA range of each LU with `bPSASensitive = 01h`
2. If PSA verification fails, host sets `bPSAState = Off` and issues UNMAP to erase all pre-loaded data, then restarts
3. After FORMAT UNIT on a thin-provisioned LU, all LBAs become unmapped; reads return zeros

See [[psa]] for full PSA flow.

## FORMAT UNIT Post-Condition

After a successful FORMAT UNIT command:
- Full-provisioned LU: all LBAs shall be mapped
- Thin-provisioned LU: all LBAs shall be unmapped; reads return zeros

## READ CAPACITY (16) — Thin Provisioning Bits

The READ CAPACITY (16) response (opcode 9Eh, returns 32 bytes) includes:

| Bit | Name | Meaning |
|-----|------|---------|
| TPE | Thin Provisioning Enabled | Set if `bProvisioningType = 02h` or `03h` |
| TPRZ | Thin Provisioning Return Zeros | Set if `bProvisioningType = 03h`; unmapped reads return zeros |

## Key Claims (Spec)

- **[Ch 47]** UNMAP command not supported on full-provisioned LUs (`bProvisioningType = 00h`).
- **[Ch 47]** If UNMAP BLOCK DESCRIPTOR DATA LENGTH is not a multiple of 16, the last incomplete descriptor is ignored.
- **[Ch 35]** TPRZ bit in READ CAPACITY (16): set by `bProvisioningType`. TPRZ=1 (03h) means unmapped LBA returns zeros; TPRZ=0 (02h) means unmapped LBA may return any data.
- **[Ch 42]** After successful FORMAT UNIT: thin-provisioned LU LBAs become unmapped; reads return zeros.
- **[Ch 54]** Discard/Erase security: `bProvisioningType=02h` (discard, TPRZ=0) vs `03h` (erase/secure, TPRZ=1).

## Interaction with Purge

The Purge operation (`fPurgeEnable`, Flag IDN 06h) is a related but distinct operation: it removes data from physical blocks not mapped to any logical block (i.e., previously UNMAP'd data). Purge provides a secure data removal guarantee beyond what UNMAP alone achieves.

- UNMAP: tells the device the LBA range is no longer needed; physical data may remain
- Purge: physically erases data that is no longer logically mapped

See [[background-operations]] for Purge status and interaction.

## Related Entities

- [[lun]] — `bProvisioningType` per-LU in Unit Descriptor
- [[psa]] — UNMAP is prerequisite for PSA flow on sensitive LUs
- [[background-operations]] — Purge physically removes UNMAP'd data
- [[scsi-commands]] — UNMAP (42h), READ CAPACITY (16) (9Eh), FORMAT UNIT (04h)
