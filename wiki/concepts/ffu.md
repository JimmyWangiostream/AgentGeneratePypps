---
type: concept
title: "FFU — Field Firmware Update"
tags: [ffu, firmware, write-buffer, attributes, commands]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
---

# FFU — Field Firmware Update

Field Firmware Update (FFU) is the UFS mechanism for delivering new firmware to a device in the field without physical access to the flash. FFU is supported when `bUFSFeaturesSupport bit[0] = 1` in the Device Descriptor (offset 1Fh).

Extended FFU support is indicated by `dExtendedUFSFeaturesSupport bit[2] = 1` (offset 4Fh–52h).

## Mechanism

FFU uses the **WRITE BUFFER command** (opcode 3Bh) with a specific MODE value. UFS supports only one FFU mode:

| MODE field | Value | Description |
|-----------|-------|-------------|
| 0Eh | Download microcode with offsets, save, and defer active | The only valid FFU mode in UFS |

All other WRITE BUFFER modes (00h, 03h–0Dh, 0Fh, etc.) are not used for FFU.

## WRITE BUFFER Command for FFU

CDB format (opcode 3Bh):

| Byte | Field | FFU Requirement |
|------|-------|----------------|
| 1[4:0] | MODE | Must be 0Eh |
| 2 | BUFFER ID | Must be 00h |
| 3–5 | BUFFER OFFSET | Should be 4 KB-aligned; increasing order across sequence |
| 6–8 | PARAMETER LIST LENGTH | Number of bytes to transfer in this chunk |

## FFU Delivery Sequence (Spec 11.3.28.2.1)

1. **Deliver microcode**: host sends one or more WRITE BUFFER commands (MODE=0Eh, BUFFER ID=00h) through any LU that supports WRITE BUFFER. BUFFER OFFSET values must be in increasing order, starting from zero, and should be 4 KB-aligned.
2. **Task attribute**: all WRITE BUFFER commands in the sequence should use Simple or Ordered task attribute.
3. **Same LU**: all commands should be sent to the same logical unit.
4. **Timeout**: `bFFUTimeout` (Device Descriptor offset 20h) indicates the maximum time the device may handle each WRITE BUFFER command. During this window, device access may be limited or unavailable.
5. **Activate**: after successful delivery, host activates the new firmware via **hardware reset (RST_n)** or **power cycle** only.
   - START STOP UNIT command does NOT activate deferred microcode.
   - FORMAT UNIT command does NOT activate deferred microcode.
   - WRITE BUFFER MODE=0Fh does NOT activate microcode (not used in UFS).
6. **Verify**: after device re-initialization, host reads `bDeviceFFUStatus` attribute (IDN 14h) to confirm success.

## Key Attributes

### `bFFUTimeout` (Device Descriptor offset 20h)

Maximum time in which the device may handle a single WRITE BUFFER command during FFU. During this period, the host should not send other commands.

### `bDeviceFFUStatus` (Attribute IDN 14h)

Read-only attribute. Read after power-on/reset following FFU delivery to verify firmware update result.

| Value | Meaning |
|-------|---------|
| 00h | No info (initial state) |
| 01h | Successful |
| 02h | Corruption error |
| 03h | Internal error |
| 04h | Microcode version mismatch |
| FFh | General error |

## Activation Rules

The new firmware becomes active only on:
- Power-on (VCC power cycle)
- Hardware reset (RST_n assertion)

The first initialization after a successful FFU delivery may be longer than usual — the host should account for extended initialization time.

## Status Response

| Response | Condition |
|----------|-----------|
| GOOD | Data successfully transferred and written |
| BUSY | Device not ready to accept new command (still processing) |
| CHECK CONDITION (ILLEGAL REQUEST) | Range or CDB error (e.g., unsupported MODE, misaligned offset) |
| CHECK CONDITION (MEDIUM ERROR) | Medium failure or ECC error |
| CHECK CONDITION (HARDWARE ERROR) | Hardware failure |

## Key Claims (Spec)

- **[Ch 49]** FFU WRITE BUFFER MODE=0Eh only; firmware is activated on next power-on or hard reset, NOT on START STOP UNIT or FORMAT UNIT.
- **[Ch 49]** WRITE BUFFER BUFFER OFFSET for FFU should be 4 KB-aligned.
- **[Ch 68]** `bUFSFeaturesSupport bit[0] = 1` indicates FFU supported.
- `fPermanentlyDisableFwUpdate` (Flag IDN 0Bh): write-once flag; when set to 1, permanently disables firmware update capability.

## Related Entities

- [[flags]] — `fPermanentlyDisableFwUpdate` (IDN 0Bh) permanently blocks FFU
- [[write-buffer]] — WRITE BUFFER command (opcode 3Bh) is the transport mechanism
- [[device-descriptor]] — `bFFUTimeout` at offset 20h, `bUFSFeaturesSupport` at offset 1Fh
