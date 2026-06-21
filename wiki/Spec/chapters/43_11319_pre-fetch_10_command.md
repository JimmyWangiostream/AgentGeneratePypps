# 11.3.19 PRE-FETCH (10) Command

The PRE-FETCH (10) command shall require the device server to transfer the logical blocks for the mapped LBAs specified by the command from the medium to the volatile cache (if such cache exists) and for any unmapped LBAs specified by the command to update the volatile cache to prevent retrieval of stale data as defined in [SBC].

The Command CDB shall be sent in a single COMMAND UPIU.

**Table 11.35 — PRE_FETCH Command**

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|---|---|---|---|---|---|---|---|---|
| 0 | | | OPERATION CODE (34h) | | | | | |
| 1 | | | Reserved | | | IMMED | Obsolete<br>= 0b |
| 2 | (MSB) | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | LOGICAL BLOCK ADDRESS | | | | | |
| 5 | | | | | | | | (LSB) |
| 6 | | Reserved | | | GROUP NUMBER = 00000b | | | |
| 7 | (MSB) | | | | | | | |
| 8 | | | PREFETCH LENGTH | | | | | (LSB) |
| 9 | | | CONTROL= 00h | | | | | |

---
*JEDEC Standard No. 220G*  
*Page 225*

# JEDEC Standard No. 220G
Page 226

## 11.3.19.1 PRE-FETCH (10) Command Parameters

### Table 11.36 — PRE-FETCH Command Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 1 | 1 | **IMMED:** An immediate (IMMED) bit set to zero specifies that the device server shall not return status until the operation has been completed. An IMMED bit set to one specifies that the device server shall return status as soon as the CDB has been validated. If the IMMED bit is set to one, and the device server does not support the IMMED bit, then the device server shall terminate the command with CHECK CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to INVALID FIELD IN CDB. |
| 2:5 | 7:0 | **LOGICAL BLOCK ADDRESS:** The LOGICAL BLOCK ADDRESS field specifies the LBA of the first logical block accessed by this command. If the specified LBA exceeds the capacity of the medium, then the device server shall terminate the command with CHECK CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to LOGICAL BLOCK ADDRESS OUT OF RANGE. |
| 6 | 4:0 | **GROUP NUMBER:** The GROUP NUMBER field specifies the group into which attributes associated with the command should be collected. A GROUP NUMBER field set to zero specifies that any attributes associated with the command shall not be collected into any group. The use of GROUP NUMBER field for PRE-FETCH command is not defined in this standard therefore this field should be set to zero. |
| 7:8 | 7:0 | **PREFETCH LENGTH:** The PREFETCH LENGTH field specifies the number of contiguous logical blocks that shall be pre-fetched, starting with the logical block specified by the LOGICAL BLOCK ADDRESS field. A NUMBER OF LOGICAL BLOCKS field set to zero specifies that all logical blocks starting with the one specified in the LOGICAL BLOCK ADDRESS field up to the last logical block on the medium shall be pre-fetched. If the LBA plus the prefetch length exceeds the capacity of the medium, then the device server shall terminate the command with CHECK CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to LOGICAL BLOCK ADDRESS OUT OF RANGE. The device server is not required to transfer logical blocks that already are contained in the cache. |
| 9 | 7:0 | **CONTROL:** The CONTROL byte is not used in this standard: the CONTROL byte should be set to zero and it shall be ignored by UFS device. |

# JEDEC Standard No. 220G
Page 227

## 11.3.19.2 PRE-FETCH Command Data Transfer

The PRE-FETCH command does not have a data transfer phase

• No DATA IN or DATA OUT UPIU's are transferred

## 11.3.19.3 PRE-FETCH Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU

• If the command is performed successfully then it will terminate with a STATUS response of GOOD

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned

• Other failures can occur for numerous reasons. When the PRE-FETCH command fails, a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as:

    ○ ILLEGAL REQUEST (range or CDB errors)
    
    ○ MEDIUM ERROR (medium failure, ECC, etc.)
    
    ○ HARDWARE ERROR (hardware failure)
    
    ○ UNIT ATTENTION (reset, power-on, etc.)
    
    ○ etc.

# 11.3.20 PRE-FETCH (16) Command

See PRE-FETCH (10) command for details.

## Table 11.37 — PRE-FETCH (16) Command

| Byte | Bit 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|-------|---|---|---|---|---|---|---|
| 0 | | | OPERATION CODE (90h) | | | | | |
| 1 | | Reserved | | | | IMMED | Reserved |
| 2 | (MSB) | | | | | | | |
| .... | | | LOGICAL BLOCK ADDRESS | | | | | |
| 9 | | | | | | | | (LSB) |
| 10 | (MSB) | | | | | | | |
| .... | | | PREFETCH LENGTH | | | | | |
| 13 | | | | | | | | (LSB) |
| 14 | | Reserved | | GROUP NUMBER = 00000b | | | | |
| 15 | | | CONTROL= 00h | | | | | |

# JEDEC Standard No. 220G
## Page 229

### 11.3.21 SECURITY PROTOCOL IN Command

The SECURITY PROTOCOL IN command is used to retrieve security protocol information or the results of one or more SECURITY PROTOCOL OUT commands. See [SPC] for details.

#### Table 11.38 — SECURITY PROTOCOL IN Command

| Bit  | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|---|---|---|---|---|---|---|---|
| Byte |   |   |   |   |   |   |   |   |
| 0    | OPERATION CODE (A2h) ||||||| |
| 1    | SECURITY PROTOCOL ||||||| |
| 2    |           |   |   | SECURITY PROTOCOL SPECIFIC |   |           |
| 3    |||||||||
| 4    | INC_512 |   |   | Reserved |   |   |   |   |
| 5    | Reserved ||||||| |
| 6    | (MSB) |   |   |   |   |   |   |   |
| ...  | ALLOCATION LENGTH ||||||| |
| 9    ||||||| (LSB) |
| 10   | Reserved ||||||| |
| 11   | CONTROL = 00h ||||||| |

#### 11.3.21.1 SECURITY PROTOCOL IN Command Parameter
• The SECURITY PROTOCOL field specifies which security protocol is being used. UFS devices shall support the following value:
  ○ ECh: JEDEC UFS application

Support of other SECURITY PROTOCOL values is device specific.
• A INC_512 bit set to one specifies that the ALLOCATION LENGTH is expressed in increments of 512 bytes.

#### 11.3.21.2 SECURITY PROTOCOL IN Command Data Transfer
• The Device Server transfers security protocol data to the Application Client using one or more DATA IN UPIU's.

#### 11.3.21.3 SECURITY PROTOCOL IN Command Status Response
• Status response shall be sent in a single RESPONSE UPIU
• If the command is successfully executed, it shall terminate with a STATUS response of GOOD
• Failure can occur for numerous reasons. When the command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as
  ○ ILLEGAL REQUEST (range or CDB errors)
  ○ HARDWARE ERROR (hardware failure)
  ○ UNIT ATTENTION (reset, power-on, etc.)
  ○ etc.