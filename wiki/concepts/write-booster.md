---
type: concept
title: "WriteBooster"
tags: [write-booster, performance, slc-cache, flags, attributes]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
---

# WriteBooster

WriteBooster is an SLC-based write acceleration buffer defined in the UFS specification. It is supported when `dExtendedUFSFeaturesSupport bit[0] = 1` (Device Descriptor offset 4Fh–52h).

## Overview

The WriteBooster feature allows the device to use an SLC buffer for incoming write data, converting writes to high-throughput SLC writes initially, then migrating data to TLC in the background. This provides burst write performance significantly above the device's sustained TLC write rate.

## Flags

| IDN | Name | Access | Default | Description |
|-----|------|--------|---------|-------------|
| 0Eh | `fWriteBoosterEn` | Volatile | 0 | Enable/disable WriteBooster; when cleared, WB buffer is not used |
| 0Fh | `fWriteBoosterBufferFlushEn` | Volatile | 0 | Enables background flush of WB buffer to TLC |
| 10h | `fWriteBoosterBufferFlushDuringHibernate` | Volatile | 0 | Allows WB buffer flush to continue during UniPro Hibernate state |
| 13h | `fUnpinEn` | Volatile | 0 | Enables unpinning of Pinned data in WriteBooster partial flush |

All WriteBooster flags are **volatile** — they reset to 0 on power cycle or hardware reset.

## Buffer Types

`bWriteBoosterBufferType` (Device Descriptor offset 54h) defines the allocation model:

| Value | Mode | Description |
|-------|------|-------------|
| 00h | LU Dedicated | Each enabled LU has its own WB buffer allocation; capacity set per-LU |
| 01h | Shared | A single shared buffer is allocated across all LUs using `dNumSharedWriteBoosterBufferAllocUnits` |

### LU Dedicated Mode (00h)

In dedicated mode, each LU's WB buffer size is configured in the Unit Descriptor (per LU). The total capacity is split across LUs.

### Shared Mode (01h)

`dNumSharedWriteBoosterBufferAllocUnits` (Device Descriptor offset 55h–58h, 4-byte field) defines the total number of allocation units for the shared buffer. All LUs draw from this shared pool.

## Key Attributes

| IDN | Name | Access | Description |
|-----|------|--------|-------------|
| 3Dh | `bWriteBoosterBufferResizeEn` | Write-only volatile | 00h=idle, 01h=decrease buffer size, 02h=increase buffer size |
| 3Fh | `bWriteBoosterBufferPartialFlushMode` | Persistent | 00h=no partial flush, 01h=FIFO, 02h=Pinned |

### Buffer Resize (`bWriteBoosterBufferResizeEn` IDN 3Dh)

- Write 01h: request decrease in WB buffer allocation
- Write 02h: request increase in WB buffer allocation
- The result is reported via the `WRITEBOOSTER_FLUSH_NEEDED` exception event (bit 4 of `wExceptionEventStatus`)

## Partial Flush Modes (`bWriteBoosterBufferPartialFlushMode`)

| Value | Mode | Behavior |
|-------|------|----------|
| 00h | No partial flush | Full flush only; device determines when to flush |
| 01h | FIFO | Flush oldest data first; preserves write ordering |
| 02h | Pinned | Retain data marked with `GROUP NUMBER = 11000b`; flush non-Pinned data first |

Pinned data is marked using the GROUP NUMBER field in the WRITE (10)/(16) CDB: `GROUP NUMBER = 11000b = 0x18`.

## User Space Modes

Two modes control how WB buffer storage is allocated relative to user data:

1. **User Space Reduction Mode**: The WriteBooster buffer consumes from the logical LU capacity. The LU's effective user capacity is reduced by the WB buffer size.
2. **Preserve User Space Mode**: The WriteBooster buffer is allocated from reserved physical area. LU logical capacity is unaffected. Controlled by `bWriteBoosterBufferPreserveUserSpaceEn` (Device Descriptor offset 53h).

## Exception Events

WriteBooster-related exception events (see [[exception-events]]):

- `bit4` of `wExceptionEventStatus`: `WRITEBOOSTER_FLUSH_NEEDED` — device signals that flush is required

## CustomerReq Override

> **Note (CustomerReq):** In this project's implementation, WriteBooster is restricted to **Normal LUNs, non-Boot LUNs, LUN numbers 0–7** only. This is a CustomerReq constraint that overrides the Spec's general allowance for any enabled LU. When configuring WB buffer, only LUNs 0–7 that are Normal (not Boot or system) are valid targets.

## Related Entities

- [[flags]] — `fWriteBoosterEn`, `fWriteBoosterBufferFlushEn`, `fWriteBoosterBufferFlushDuringHibernate`, `fUnpinEn`
- [[exception-events]] — `WRITEBOOSTER_FLUSH_NEEDED` event (bit 4)
- [[lun]] — per-LU WB buffer configuration in Unit Descriptor
- [[background-operations]] — WB flush is a background operation
