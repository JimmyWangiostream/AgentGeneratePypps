---
type: entity
title: "RPMB — Replay Protected Memory Block"
tags: [rpmb, security, authentication, mac, write-counter, region]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
aliases: [RPMB, Replay Protected Memory Block, rpmb_region]
---

# RPMB — Replay Protected Memory Block

RPMB is a secure storage partition in UFS devices that uses HMAC-SHA-256 authentication to prevent unauthorized writes. It supports up to 4 regions, each with its own dedicated key, write counter, and result register. Supported if `bSecurityLU (Device Descriptor 0Dh) = 01h`.

## Regions

Each RPMB region is independently keyed and addressed.

| Region | Protocol Specific | Descriptor Field | Notes |
|--------|------------------|-----------------|-------|
| Region 0 | 00h 01h | bRPMBRegion0Size | Always enabled; only region that supports Secure WP Config Block |
| Region 1 | 01h 01h | bRPMBRegion1Size | Optional |
| Region 2 | 02h 01h | bRPMBRegion2Size | Optional |
| Region 3 | 03h 01h | bRPMBRegion3Size | Optional |

- `bRPMBRegionEnable`: bits[0–3] = region 0–3 enabled; bit[4] = Advanced RPMB mode
- Region size unit: **128 KB** (0 = disabled); range: 128 KB – 16 MB
- `bRPMBLifeTimeEst`: 00h = no info; 01h–0Ah = 0–100% used; 0Bh = exceeded

**Default (ModelDefault):** `rpmb_region = RPMBRegion.REGION_0`

## Resources per Region

| Resource | Size | Access | Notes |
|----------|------|--------|-------|
| Authentication Key | 32 bytes | Write-once, not readable/erasable | Used as HMAC-SHA-256 key |
| Write Counter | 4 bytes | Read-only | Starts at 00000000h; max FFFFFFFFh; no wrap-around |
| Result Register | 2 bytes | Read-only | Last operation result |
| RPMB Data Area | 128 KB – 16 MB | Auth read/write only | Cannot be erased |
| Secure WP Config Block (Normal) | 256 bytes | Auth read/write | Region 0 only |
| Secure WP Config Block (Advanced) | 4 KB | Auth read/write | Region 0 only |

**Default (ModelDefault):** `rpmb_key_size = 32 bytes`

## RPMB Modes

| Mode | Block Size | Message Frame | Detection |
|------|-----------|--------------|-----------|
| Normal RPMB | 256 bytes data | 512 bytes | Default |
| Advanced RPMB | 4 KB data | Uses EHS (Extended Header Segment) | `bRPMBRegionEnable bit[4] = 1`; `dExtendedUFSFeaturesSupport bit[6] = 1` |

**SECURITY PROTOCOL IN/OUT requirements:**
- Normal RPMB: ALLOCATION/TRANSFER LENGTH must be a multiple of **512 bytes**
- Advanced RPMB: ALLOCATION/TRANSFER LENGTH must be a multiple of **4096 bytes**
- SECURITY PROTOCOL = **ECh** (JEDEC UFS)

## Normal RPMB Message Data Frame (512 bytes)

```
Byte   0 – 195  : Stuff Bytes (196 bytes) — padding, ignored
Byte 196 – 227  : Key / MAC (32 bytes) — HMAC-SHA-256 result
Byte 228 – 483  : Data (256 bytes) — user data [255:0]
Byte 484 – 499  : Nonce (16 bytes) — random, from host; echoed in response
Byte 500 – 503  : Write Counter (4 bytes, MSB first)
Byte 504 – 505  : Address (2 bytes) — LBA in RPMB region
Byte 506 – 507  : Block Count (2 bytes)
Byte 508 – 509  : Result (2 bytes)
Byte 510 – 511  : Request / Response Message Type (2 bytes)
```

MAC is computed over bytes **228–511** of each data frame using HMAC-SHA-256.

## Request Message Types (Table 12.8)

| Code | Request Message Type |
|------|---------------------|
| 0001h | Authentication Key programming request |
| 0002h | Write Counter read request |
| 0003h | Authenticated data write request |
| 0004h | Authenticated data read request |
| 0005h | Result read request **(Normal RPMB Mode only)** |
| 0006h | Secure Write Protect Configuration Block write request |
| 0007h | Secure Write Protect Configuration Block read request |
| 0008h | RPMB Purge Enable request |
| 0009h | RPMB Purge Status Read request |
| 0010h | Authenticated Vendor Specific Command request |
| 0011h | Authenticated Vendor Specific Command Status Read request |

## Response Message Types (Table 12.9)

| Code | Response Message Type |
|------|-----------------------|
| 0100h | Authentication Key programming response |
| 0200h | Write Counter read response |
| 0300h | Authenticated data write response |
| 0400h | Authenticated data read response |
| 0500h | Reserved |
| 0600h | Secure Write Protect Configuration Block write response |
| 0700h | Secure Write Protect Configuration Block read response |
| 0800h | RPMB Purge Enable response |
| 0900h | RPMB Purge Status Read response |
| 1000h | Authenticated Vendor Specific Command response **(Advanced RPMB only)** |
| 1100h | Authenticated Vendor Specific Command Status response |

## Operation Result Codes (Table 12.11)

Result field: bits[15:8] = Reserved, bit[7] = Write Counter expired, bits[6:0] = operation status.

| Code | Description |
|------|-------------|
| 0000h | Operation OK |
| 0001h | General failure |
| 0002h | Authentication failure — MAC comparison not matching |
| 0003h | Counter failure — counters not matching or increment failure |
| 0004h | Address failure — out of range or wrong alignment |
| 0005h | Write failure — data/counter/result write failure |
| 0006h | Read failure — data/counter/result read failure |
| 0007h | Authentication Key not yet programmed — **only valid until key is programmed; never occurs after** |
| 0008h | Secure Write Protect Config Block access failure |
| 0009h | Invalid Secure Write Protect Block Configuration parameter |
| 000Ah | Secure Write Protection not applicable — LU already has other WP mode |
| 000Bh | Unrecognized/Unsupported Request Type |
| 000Ch | Rejected — RPMB Purge operation in progress |

Note: When Write Counter has expired, codes appear as 0080h–008Ch (bit[7]=1).

## MAC Calculation

- Algorithm: **HMAC-SHA-256** (256-bit = 32 bytes)
- Key: the 256-bit Authentication Key stored in the target RPMB region
- Input: concatenation of fields in the RPMB packet (bytes 228–511)

**Advanced RPMB MAC:** concatenation of DATA IN/OUT segment data (in order sent) + Advanced RPMB Meta Information (bytes 0–27) + four 00h bytes.

## RPMB Purge

Purge removes data from physical blocks in RPMB. Mandatory since UFS 4.0.

| Status | Meaning |
|--------|---------|
| 00h | Purge not initiated (reset value) |
| 01h | Purge in progress |
| 02h | Purge completed (resets to 00h on next status read) |
| 03h | Purge general failure (resets to 00h on next status read) |

While purge is in progress: authenticated Read or Write returns result code **000Ch**.

## Secure Write Protect Entry (16 bytes)

| Field | Bits | Description |
|-------|------|-------------|
| WPF | bit[0] | Write Protect Flag: 1 = enabled |
| WPT | bits[2:1] | Type: 00b=NV (persistent), 01b=P (cleared on reset), 10b=NV-AWP (auto-set on reset) |
| Reserved | bits[7:3], bytes[1:3] | Must be 0 |
| LOGICAL BLOCK ADDRESS | bytes[4:11] | First LBA of protected area |
| NUMBER OF LOGICAL BLOCKS | bytes[12:15] | Count; 0 = entire LU |

WPF shall be **0 after device manufacturing**.

## Advanced RPMB EHS Structure

- `bEHSType = 01h` for Advanced RPMB
- `bLength = 02h` (60 bytes total including basic header)
- Content: Advanced RPMB Meta Information (28 bytes) + MAC/Key (32 bytes)

## SCSI Commands

| Command | Opcode | Notes |
|---------|--------|-------|
| SECURITY PROTOCOL IN | A2h | Read from RPMB; PROTOCOL = ECh |
| SECURITY PROTOCOL OUT | B5h | Write to RPMB; PROTOCOL = ECh |

## Key Claims (Spec §12)

- Each RPMB region has its own dedicated Authentication Key, Write Counter, and Result Register.
- Write Counter starts at 00000000h; max FFFFFFFFh; **no wrap-around**.
- Key-not-programmed state (0007h) is the only valid result until key is programmed; never occurs after programming.
- RPMB Purge is **mandatory since UFS 4.0**.
- RPMB W-LUN is not formatted by FORMAT UNIT to Device W-LUN.
- Cache is not used for RPMB W-LUN.

## Related

[[power-modes]] | [[device-descriptor]] | [[flags]] | [[lun]] | [[shipping-mode]]
