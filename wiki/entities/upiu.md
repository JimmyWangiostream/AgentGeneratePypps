---
type: entity
title: "UPIU Types"
tags: [upiu, protocol, query, scsi, transport, response-codes]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
---

# UPIU Types

UPIU (UFS Protocol Information Unit) is the fundamental transport unit of the UFS Transport Protocol (UTP) layer. All host-device communication uses UPIUs.

## General UPIU Format

- **Minimum size**: 32 bytes (12-byte basic header + 20 bytes transaction-specific fields)
- **Maximum size**: 65,600 bytes
- **Optional**: Extended Header Segments (EHS) + Data Segment

### Basic Header (Bytes 0–11)

| Byte | Field | Notes |
|------|-------|-------|
| 0 | Transaction Type | bit[7]=HD, bit[6]=DD, bits[5:0]=Transaction Code |
| 1 | Flags | Transaction-specific flags |
| 2 | LUN | Logical Unit Number (or Well-Known LUN) |
| 3 | Task Tag | Command identifier within initiator |
| 4 | IID [bits 7:4] | Initiator ID (upper 4 bits) |
| 5 | Command Set Type / EXT_IID / Query Function / TM Function | Role depends on transaction type |
| 6 | Response | Device→Host response code |
| 7 | EXT_IID (H→D) / Status (D→H) | SCSI status in Response UPIU |
| 8–9 | Total EHS Length / Device Information | EHS length in 32-byte units (0–3); Device Info in Response |
| 10–11 | Data Segment Length | Length of appended data segment |

## UPIU Types Table

| UPIU | Transaction Code | Direction | Key Fields |
|------|-----------------|-----------|------------|
| NOP OUT | 00h | H→D | Connection ping/keep-alive; no data |
| COMMAND | 01h | H→D | Flags: R=data-in, W=data-out, ATTR=task attribute, CP=priority; bytes 12–15=Expected Data Transfer Length; bytes 16–31=CDB[0:15] |
| DATA OUT | 02h | H→D | Flags.T=retransmit; Data Buffer Offset + Data Transfer Count; must be integer multiples of Logical Block Size |
| TM REQUEST | 04h | H→D | TM Function code; Input Parameters: LUN, Task Tag, Initiator ID |
| QUERY REQUEST | 16h | H→D | Query Function=01h(READ)/81h(WRITE); OPCODE; IDN; INDEX; SELECTOR |
| NOP IN | 20h | D→H | Response=00h; echoes Task Tag from NOP OUT |
| RESPONSE | 21h | D→H | Flags: O=overflow, U=underflow, D=DATA OUT mismatch; SCSI Status; Device Information; 18-byte Sense Data |
| DATA IN | 22h | D→H | Flags.T=retransmit; Hint fields for out-of-order DMA pre-positioning |
| TM RESPONSE | 24h | D→H | Service Response codes for Task Management |
| RTT | 31h | D→H | Ready To Transfer: Data Buffer Offset (4-byte multiple); Data Transfer Count max=bMaxDataOutSize |
| QUERY RESPONSE | 36h | D→H | Query Response codes; Flag Value at byte 23 |
| REJECT UPIU | 3Fh | D→H | Response=01h; sent only for invalid Transaction Type (unknown code or HD/DD bit set) |

## QUERY REQUEST UPIU Details

### Query Function Codes

| Value | Description |
|-------|-------------|
| 01h | STANDARD READ REQUEST |
| 81h | STANDARD WRITE REQUEST |

### QUERY OPCODE Values

| OPCODE | Value | Target |
|--------|-------|--------|
| NOP | 00h | — |
| READ DESCRIPTOR | 01h | Descriptor (IDN + INDEX + SELECTOR) |
| WRITE DESCRIPTOR | 02h | Descriptor |
| READ ATTRIBUTE | 03h | Attribute (IDN + INDEX + SELECTOR) |
| WRITE ATTRIBUTE | 04h | Attribute |
| READ FLAG | 05h | Flag (IDN) |
| SET FLAG | 06h | Flag |
| CLEAR FLAG | 07h | Flag |
| TOGGLE FLAG | 08h | Flag |
| Vendor Specific | F0h–FFh | Vendor defined |

**Constraint**: Device processes only one QUERY REQUEST or NOP OUT at a time.

### QUERY RESPONSE Codes

| Code | Description |
|------|-------------|
| 00h | Success |
| F6h | Parameter not readable |
| F7h | Parameter not writeable |
| F8h | Parameter already written (write-once violation) |
| F9h | Invalid LENGTH |
| FAh | Invalid value |
| FBh | Invalid SELECTOR |
| FCh | Invalid INDEX |
| FDh | Invalid IDN |
| FEh | Invalid OPCODE |
| FFh | General failure |

## RESPONSE UPIU — Sense Data

18-byte fixed format, Response Code = 70h:

| Byte | Field | Notes |
|------|-------|-------|
| 0 | Response Code | 70h = fixed format current errors |
| 2 bits[3:0] | Sense Key | Category of error — see below |
| 7 | Additional Sense Length | 0Ah (10 bytes follow) |
| 12 | ASC | Additional Sense Code |
| 13 | ASCQ | Additional Sense Code Qualifier |

### Sense Key Values

| Value | Name | Description |
|-------|------|-------------|
| 00h | NO SENSE | No error; information may still be present |
| 01h | RECOVERED ERROR | Command completed with error recovery |
| 02h | NOT READY | Device not ready to service command |
| 03h | MEDIUM ERROR | Non-recoverable medium error |
| 04h | HARDWARE ERROR | Non-recoverable hardware error |
| 05h | ILLEGAL REQUEST | Invalid CDB or parameter |
| 06h | UNIT ATTENTION | State change (power on, reset, media change) |
| 07h | DATA PROTECT | Write-protected medium |
| 08h | BLANK CHECK | Blank or unformatted medium |
| 09h | VENDOR SPECIFIC | Vendor-specific condition |
| 0Bh | ABORTED COMMAND | Command aborted by device |
| 0Eh | MISCOMPARE | VERIFY command data mismatch |

### SCSI Status Values (in RESPONSE UPIU byte 7)

| Value | Status |
|-------|--------|
| 00h | GOOD |
| 02h | CHECK CONDITION |
| 08h | BUSY |
| 18h | RESERVATION CONFLICT |
| 28h | TASK SET FULL |

## RESPONSE UPIU — Device Information Field (Bytes 8–9)

| Bit | Field | Description |
|-----|-------|-------------|
| bit[0] | EVENT_ALERT | 1 = exception event pending; host should read wExceptionEventStatus |
| bits[5:2] | FAST_RECOVERY_NEEDED | 0h–Fh = seconds hint before host should issue HW Reset (Fast Recovery mode, UFS 4.1) |

## Task Management Functions (TM REQUEST)

| Value | Function |
|-------|----------|
| 01h | Abort Task |
| 02h | Abort Task Set |
| 04h | Clear Task Set |
| 08h | Logical Unit Reset |
| 80h | Query Task |
| 81h | Query Task Set |

### TM Service Response Codes

| Code | Description |
|------|-------------|
| 00h | Complete |
| 04h | Not Supported |
| 05h | Failed |
| 08h | Succeeded |
| 09h | Incorrect LU Number |

## Extended Header Segments (EHS)

- Combined max: **96 bytes** (3 × 32-byte segments)
- Total EHS Length field = 0, 1, 2, or 3 (units of 32 bytes)
- **Only supported** in COMMAND UPIU and RESPONSE UPIU; Total EHS Length shall be 0 in all other UPIU types
- bEHSType = 01h for Advanced RPMB; bLength = 02h (60 bytes total including header)

## DATA IN UPIU — Out-of-Order Hint Fields

When bOutOfOrderDataEn != 00h and bDataOrdering=01h/02h/03h:

| Field | Description |
|-------|-------------|
| HintControl | Enables hint for this transfer |
| HintIID | Initiator ID hint |
| HintEXT_IID | Extended IID hint |
| HintLUN | Target LUN for hint |
| Hint Data Buffer Offset | Pre-position DMA target offset |
| Hint Data Count | Amount of data in 4KB units |

Host uses wHostHintCacheSize (attribute 47h) to limit hint cache size.

## REJECT UPIU Usage

Sent ONLY when:
- Invalid Transaction Type received (unknown Transaction Code)
- HD or DD bit set to invalid combination

NOT sent for:
- Wrong LUN in COMMAND UPIU
- Wrong LUN in TM REQUEST
- Wrong Query Function in QUERY REQUEST

Response=01h, Basic Header Status=01h in REJECT UPIU.

## Usage Examples (Python API)

### Issue a QUERY REQUEST (read attribute)
```python
from Script.api import cmd_seq as ExecuteCMD
import api

# Read attribute via QUERY REQUEST UPIU
read_attr = ExecuteCMD.ReadAttribute()
read_attr.assign(idn=api.AttributeIDN.CURRENT_POWER_MODE, index=0, selector=0)
idx = ExecuteCMD.enqueue(read_attr)
ExecuteCMD.send(clear_on_success=False)
response = ExecuteCMD.read_response(idx)
print(f"Query Response Code: 0x{response.upiu.b6_query_response:02X}")
ExecuteCMD.clear()
```

### Send NOP OUT and check NOP IN
```python
# NOP OUT / NOP IN exchange
nop_out = ExecuteCMD.NopOut()
idx = ExecuteCMD.enqueue(nop_out)
ExecuteCMD.send(clear_on_success=False)
response = ExecuteCMD.read_response(idx)
# Response UPIU b6_query_response should be 00h on NOP IN
ExecuteCMD.clear()
```

### Handle RESPONSE UPIU sense data
```python
from Script.api import cmd_seq as ExecuteCMD
import api

write10 = ExecuteCMD.Write10()
write10.assign(lun=0, lba=0, length=1)
idx = ExecuteCMD.enqueue(write10)
try:
    ExecuteCMD.send(clear_on_success=False)
    response = ExecuteCMD.read_response(idx)
except Exception:
    response = ExecuteCMD.read_response(idx)
    scsi_status = response.upiu.b7_status  # SCSI Status byte
    sense_key = response.sense_data[2] & 0x0F
    asc = response.sense_data[12]
    ascq = response.sense_data[13]
    print(f"SCSI Status: 0x{scsi_status:02X}, Sense Key: 0x{sense_key:02X}, ASC/ASCQ: 0x{asc:02X}/0x{ascq:02X}")
ExecuteCMD.clear()
```

## Related

[[flags]] | [[attributes]] | [[scsi-commands]] | [[lun]] | [[spec]]
