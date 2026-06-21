# 11.3.13 VERIFY (10) Command

The VERIFY command requests that the UFS device verify that the specified logical block(s) and range on the medium can be accessed.

• Logical units that contain cache shall write referenced cached logical blocks to the medium for the logical unit before verification

The Command CDB shall be sent in a single COMMAND UPIU.

## Table 11.27 — VERIFY (10) Command

| Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-----|---|---|---|---|---|---|---|---|
| Byte | | | | | | | | |
| 0 | | | OPERATION CODE (2Fh) | | | | | |
| 1 | VRPROTECT = 000b | | DPO = 0b | Reserved | BYTCHK = 0b | Obsolete = 0b |
| 2 | (MSB) | | | | | | | |
| 3 | | | | | | | | |
| 4 | | LOGICAL BLOCK ADDRESS | | | | | |
| 5 | | | | | | | | (LSB) |
| 6 | Reserved | | | GROUP NUMBER = 00000b | | | |
| 7 | (MSB) | | | | | | | |
| 8 | | VERIFICATION LENGTH | | | | | | (LSB) |
| 9 | | | CONTROL = 00h | | | | | |

UFS device is required to support only the value zero for the byte check (BYTCHK) bit. Therefore the BYTCHK bit should be set to zero, and the device shall perform a medium verification with no data comparison and not transfer any data from the data-out buffer for any mapped LBA specified by the command.

---
JEDEC Standard No. 220G  
Page 211

# JEDEC Standard No. 220G
Page 212

## 11.3.13.1 Verify Command Parameters

### Table 11.28 — Verify Command Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 2:5  | 7:0 | **LOGICAL BLOCK ADDRESS:** Address of first block |
| 7:8  | 7:0 | **VERIFICATION LENGTH:** Number of contiguous logical blocks of data that shall be verified, starting with the logical block specified by the LOGICAL BLOCK ADDRESS field. A transfer length of zero specifies that no logical blocks will be verified. This condition shall not be considered an error. |

## 11.3.13.2 Verify Command Data Transfer
The VERIFY command does not have a data response

• No DATA IN or DATA OUT UPIU's are transferred

## 11.3.13.3 Verify Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU

• If all requested data is successfully verified against the medium, the VERIFY command will terminate with a STATUS response of GOOD

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned

• Other failures can occur for numerous reasons. When the VERIFY command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as:

  ○ ILLEGAL REQUEST (range or CDB errors)
  
  ○ MEDIUM ERROR (medium failure, ECC, etc.)
  
  ○ HARDWARE ERROR (hardware failure)
  
  ○ UNIT ATTENTION (reset, power-on, etc.)
  
  ○ etc.