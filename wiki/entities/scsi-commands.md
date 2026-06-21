---
type: entity
title: "UFS SCSI Commands (UCS)"
tags: [scsi, commands, ucs, cdb, read, write, inquiry, unmap]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
---

# UFS SCSI Commands (UCS)

The UFS Command Set (UCS) is a subset of SCSI commands transported via COMMAND UPIU. All CDBs are fixed-length (maximum 16 bytes). The CONTROL byte in every CDB is always 00h.

## Support Levels

- **M** = Mandatory — all UFS devices must implement
- **O** = Optional

## Command Table

| Command | Opcode | Support | Notes |
|---------|--------|---------|-------|
| TEST UNIT READY | 00h | M | No data transfer; checks if device is ready to process commands |
| REQUEST SENSE | 03h | M | Returns 18-byte fixed-format sense data (Response Code=70h) |
| FORMAT UNIT | 04h | M | Formats medium; when sent to Device W-LUN (D0h), formats all LUs except RPMB |
| READ (6) | 08h | M | 6-byte CDB; LBA and transfer length limited to small ranges |
| WRITE (6) | 0Ah | M | 6-byte CDB write |
| INQUIRY | 12h | M | EVPD=0: Standard 36-byte response; EVPD=1: VPD pages |
| MODE SELECT (10) | 55h | M | Sets mode pages (e.g., caching policy, error recovery) |
| START STOP UNIT | 1Bh | M | POWER CONDITIONS field controls power mode transitions |
| SEND DIAGNOSTIC | 1Dh | M | Diagnostic operations |
| READ CAPACITY (10) | 25h | M | Returns 8 bytes: Last LBA (4B) + Block Length (4B) |
| READ (10) | 28h | M | See CDB detail below |
| WRITE (10) | 2Ah | M | See CDB detail below |
| PRE-FETCH (10) | 34h | M | Prefetch data into device cache |
| READ BUFFER | 3Ch | M | MODE 02h=Data, MODE 1Ch=Error History log |
| WRITE BUFFER | 3Bh | M | MODE 0Eh=FFU (download microcode with offsets, save, defer activation) |
| VERIFY (10) | 2Fh | M | Verify data integrity on medium |
| SYNCHRONIZE CACHE (10) | 35h | M | Flush volatile write cache to non-volatile medium |
| UNMAP | 42h | M | De-allocates LBA ranges; requires thin provisioning (bProvisioningType=02h or 03h) |
| MODE SENSE (10) | 5Ah | M | Returns current mode page settings |
| READ CAPACITY (16) | 9Eh | M | Returns 32 bytes; includes TPE and TPRZ bits for thin provisioning |
| REPORT LUNS | A0h | M | Returns list of all supported LUNs |
| SECURITY PROTOCOL IN | A2h | M | RPMB read via Protocol ID ECh; only supported by RPMB W-LUN (C4h) |
| PRE-FETCH (16) | 90h | O | 16-byte variant of PRE-FETCH |
| WRITE (16) | 8Ah | O | 16-byte CDB write with 8-byte LBA |
| READ (16) | 88h | O | 16-byte CDB read with 8-byte LBA |
| SYNCHRONIZE CACHE (16) | 91h | O | 16-byte variant of SYNCHRONIZE CACHE |
| SECURITY PROTOCOL OUT | B5h | M | RPMB write via Protocol ID ECh; only supported by RPMB W-LUN (C4h) |
| BARRIER | F0h | M | Flush ordering guarantee between command groups (UFS-specific) |

## CDB Details

### READ (10) — Opcode 28h

| Byte | Field | Notes |
|------|-------|-------|
| 0 | OPERATION CODE | 28h |
| 1 | RDPROTECT [7:5] \| DPO [4] \| FUA [3] \| FUA_NV [1] | RDPROTECT=000b; DPO=1: low cache priority; FUA=1: force medium access |
| 2–5 | LOGICAL BLOCK ADDRESS | 4-byte LBA |
| 6 | GROUP NUMBER [4:0] | 00h=default; 01h–0Fh=ContextID (wContextConf) |
| 7–8 | TRANSFER LENGTH | Number of logical blocks |
| 9 | CONTROL | 00h always |

### WRITE (10) — Opcode 2Ah

| Byte | Field | Notes |
|------|-------|-------|
| 0 | OPERATION CODE | 2Ah |
| 1 | WRPROTECT [7:5] \| DPO [4] \| FUA [3] \| FUA_NV [1] | WRPROTECT=000b |
| 2–5 | LOGICAL BLOCK ADDRESS | 4-byte LBA |
| 6 | GROUP NUMBER [4:0] | 10000b=System Data; 11000b=Pinned WriteBooster data |
| 7–8 | TRANSFER LENGTH | Number of logical blocks |
| 9 | CONTROL | 00h always |

### GROUP NUMBER Field Encoding

| Value (binary) | Meaning |
|---------------|---------|
| 00000b | Default (no context) |
| 00001b–01111b | ContextID 1–15 (wContextConf) |
| 10000b | System Data (hint to device) |
| 11000b | Pinned WriteBooster data (retained during partial flush) |

### READ (16) — Opcode 88h

- Bytes 2–9: 8-byte LOGICAL BLOCK ADDRESS
- Bytes 10–13: 4-byte TRANSFER LENGTH
- Otherwise same flags as READ (10)

### WRITE (16) — Opcode 8Ah

- Same structure as READ (16) with write-specific flags

### INQUIRY — Opcode 12h

**Standard response (36 bytes, EVPD=0):**

| Offset | Field | Notes |
|--------|-------|-------|
| 0 bits[4:0] | PERIPHERAL DEVICE TYPE | 00h=direct access block device, 1Eh=well-known LU |
| 2 | VERSION | 06h (SPC conformance) |
| 3 bits[3:0] | RESPONSE DATA FORMAT | 0010b |
| 8–15 | VENDOR IDENTIFICATION | ASCII, 8 characters |
| 16–31 | PRODUCT IDENTIFICATION | ASCII, 16 characters |
| 32–35 | PRODUCT REVISION LEVEL | ASCII, 4 characters (firmware version) |

### READ CAPACITY (10) — Opcode 25h

Returns 8 bytes:
- Bytes 0–3: Last Logical Block Address (4B)
- Bytes 4–7: Logical Block Length in bytes (4B)

### READ CAPACITY (16) — Opcode 9Eh

Returns 32 bytes, additional fields:
- bit[1]: TPE (Thin Provisioning Enabled)
- bit[2]: TPRZ (Thin Provisioning Read Zeros — unmapped LBA returns all zeros)

### UNMAP — Opcode 42h

**Parameter List Structure:**

| Offset | Field | Size |
|--------|-------|------|
| 0–1 | UNMAP DATA LENGTH | 2B |
| 2–3 | UNMAP BLOCK DESCRIPTOR DATA LENGTH | 2B |
| 4–7 | Reserved | 4B |
| 8+ | UNMAP Block Descriptors | 16B each |

**Each UNMAP Block Descriptor (16 bytes):**

| Offset | Field | Size |
|--------|-------|------|
| 0–7 | UNMAP LOGICAL BLOCK ADDRESS | 8B |
| 8–11 | NUMBER OF LOGICAL BLOCKS | 4B |
| 12–15 | Reserved | 4B |

Requires bProvisioningType = 02h (TPRZ=0, discard) or 03h (TPRZ=1, erase to zeros).

### START STOP UNIT — Opcode 1Bh

**POWER CONDITIONS Field Values:**

| Value | Power State |
|-------|-------------|
| 0h | Start valid (LOEJ=0, START=1 → Active; START=0 → Idle) |
| 1h | Active |
| 2h | Idle |
| 3h | Standby |
| 5h | Sleep (UFS-Sleep or UFS-DeepSleep) |
| 7h | LU Control |
| Bh | Force Idle |
| Ch | Force Standby |

### WRITE BUFFER — Opcode 3Bh

| MODE | Value | Usage |
|------|-------|-------|
| Data | 02h | Write data to buffer |
| Download Microcode with Offsets, Save, Defer Activate | 0Eh | FFU: firmware update; BUFFER OFFSET must be 4KB-aligned; BUFFER ID=00h |
| Error History | 1Ch | — |

FFU firmware is activated on next hardware reset or power cycle. Use Simple or Ordered task attribute.

### READ BUFFER — Opcode 3Ch

| MODE | Value | Usage |
|------|-------|-------|
| Data | 02h | Read buffered data |
| Error History | 1Ch | Read device error log / event log |

### BARRIER — Opcode F0h

- 16-byte CDB; no data transfer
- Guarantees flush ordering between command groups
- **Only affects** Simple task attribute, normal priority commands
- Does NOT affect Head of Queue or Ordered task attribute commands
- Scoped per LU (LUN field in COMMAND UPIU)
- Device may flush lazily; use SYNCHRONIZE CACHE for immediate guarantee

## Well-Known LUN Command Support

| W-LUN | LUN Field | Supported Commands |
|-------|-----------|-------------------|
| REPORT LUNS (01h) | 81h | INQUIRY, REQUEST SENSE, TEST UNIT READY, REPORT LUNS |
| UFS Device (50h) | D0h | INQUIRY, REQUEST SENSE, TEST UNIT READY, START STOP UNIT, FORMAT UNIT |
| Boot (30h) | B0h | INQUIRY, REQUEST SENSE, TEST UNIT READY, READ (6), READ (10), READ (16), READ BUFFER |
| RPMB (44h) | C4h | INQUIRY, REQUEST SENSE, TEST UNIT READY, SECURITY PROTOCOL IN, SECURITY PROTOCOL OUT |

## Mode Pages (MODE SENSE/SELECT)

| Page Code | Subpage | Name | Key Fields |
|-----------|---------|------|------------|
| 01h | 00h | Read-Write Error Recovery | AWRE=1b default; READ/WRITE RETRY COUNT; RECOVERY TIME LIMIT |
| 08h | 00h | Caching | WCE=1b default (write-back); RCD=0b default; changeable: WCE, RCD |
| 0Ah | 00h | Control | QUEUE ALGORITHM MODIFIER=0001b; SWP=changeable; BUSY TIMEOUT PERIOD; TST=000b |
| 3Fh | 00h | ALL PAGES | Return all supported mode pages |
| 3Fh | FFh | ALL SUBPAGES | Return all pages and subpages |

## Usage Examples (Python API)

### Read (10)
```python
from Script.api import cmd_seq as ExecuteCMD
import api

write10 = ExecuteCMD.Read10()
write10.assign(lun=0, lba=0, length=1)  # length in 4KB blocks
write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX)
ExecuteCMD.enqueue(write10)
ExecuteCMD.send()
```

### Write (10) with ContextID
```python
write10 = ExecuteCMD.Write10()
write10.assign(lun=0, lba=0x1000, length=256, group_number=1)  # ContextID=1
write10.set_option(pattern_mode=api.CmdParamPatternMode.HW_FIX, timeout=30_000_000)
ExecuteCMD.enqueue(write10)
ExecuteCMD.send()
```

### Write Pinned WriteBooster data
```python
# GROUP NUMBER=11000b=0x18 for Pinned WriteBooster data
write10 = ExecuteCMD.Write10()
write10.assign(lun=0, lba=0, length=64, group_number=0x18)
ExecuteCMD.enqueue(write10)
ExecuteCMD.send()
```

### UNMAP (discard LBA range)
```python
unmap = ExecuteCMD.Unmap()
unmap.assign(lun=0)
unmap.add_block_descriptor(lba=0x0, block_count=0x10000)
ExecuteCMD.enqueue(unmap)
ExecuteCMD.send()
```

### SYNCHRONIZE CACHE
```python
sync = ExecuteCMD.SynchronizeCache10()
sync.assign(lun=0)
ExecuteCMD.enqueue(sync)
ExecuteCMD.send()
```

### FFU — Firmware Update
```python
# Download firmware image via WRITE BUFFER MODE=0Eh
with open("firmware.bin", "rb") as f:
    firmware_data = f.read()

CHUNK_SIZE = 4096  # 4KB-aligned
for offset in range(0, len(firmware_data), CHUNK_SIZE):
    chunk = firmware_data[offset:offset + CHUNK_SIZE]
    wb = ExecuteCMD.WriteBuffer()
    wb.assign(lun=target_lun, mode=0x0E, buffer_id=0x00,
              buffer_offset=offset, data=chunk)
    ExecuteCMD.enqueue(wb)
    ExecuteCMD.send()

# Power cycle to activate, then check bDeviceFFUStatus
api.power_cycle()
status = api.read_attribute(idn=api.AttributeIDN.DEVICE_FFU_STATUS)
assert status == 0x01, f"FFU failed: 0x{status:02X}"
```

## Key Notes

- **LUN field in COMMAND UPIU**: bit[7]=1 for Well-Known LUN (WLUN_ID); bits[6:0]=LUN value or W-LUN value.
- **Normal LU range**: LUN 00h–1Fh (0–31); bLUEnable=01h must be set in Unit Descriptor.
- **INQUIRY to W-LUN**: PERIPHERAL DEVICE TYPE = 1Eh (well-known LU) for well-known LUs; 00h for normal LUs.
- **Thin provisioning check**: Before issuing UNMAP, verify bProvisioningType != 00h via Unit Descriptor.
- **BARRIER**: Does not guarantee data is persisted to medium — use SYNCHRONIZE CACHE for durability.

## Related

[[upiu]] | [[attributes]] | [[flags]] | [[lun]] | [[write-booster]] | [[spec]]
