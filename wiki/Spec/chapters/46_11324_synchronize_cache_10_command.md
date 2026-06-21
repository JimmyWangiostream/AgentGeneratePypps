# 11.3.24 SYNCHRONIZE CACHE (10) Command

The SYNCHRONIZE CACHE (10) command requests that the device server ensure that the specified logical blocks have their most recent data values recorded on the medium.

## Table 11.42 — SYNCHRONIZE CACHE (10) Command

| Bit<br/>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|---|---|---|---|---|---|---|---|---|
| 0 | | | OPERATION CODE (35h) | | | | |
| 1 | | Reserved | | SYNC_NV | IMMED | Obsolete<br/>=0b |
| 2 | (MSB) | | | | | | | |
| 3 | | | | | | | | |
| 4 | | LOGICAL BLOCK ADDRESS | | | | | |
| 5 | | | | | | | | (LSB) |
| 6 | | Reserved | | | GROUP NUMBER = 00000b | | |
| 7 | (MSB) | | | | | | | |
| 8 | | NUMBER OF LOGICAL BLOCKS | | | | | (LSB) |
| 9 | | | CONTROL = 00h | | | | |

---

*JEDEC Standard No. 220G*  
*Page 234*

# 11.3.24.1 Synchronize Cache Command Parameters

## Table 11.43 — Synchronize Cache Command Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 1 | 2 | **SYNC_NV:** SYNC_NV is defined per SBC. Since non-volatile cache support is not currently defined in this standard, the SYNC_NV parameter value in the CDB is ignored by the UFS Device Server. |
| 1 | 1 | **IMMED:** An immediate (IMMED) bit set to zero specifies that the device server shall not return status until the operation has been completed. An IMMED bit set to one specifies that the device server shall return status as soon as the CDB has been validated. If the IMMED bit is set to one, and the device server does not support the IMMED bit, then the device server shall terminate the command with CHECK CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to INVALID FIELD IN CDB. |
| 2:5 | 7:0 | **LOGICAL BLOCK ADDRESS:** The LOGICAL BLOCK ADDRESS field specifies the LBA of the first logical block accessed by this command. If the specified LBA exceeds the capacity of the medium, then the device server shall terminate the command with CHECK CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to LOGICAL BLOCK ADDRESS OUT OF RANGE. |
| 6 | 4:0 | **GROUP NUMBER:** The use of GROUP NUMBER field for SYNCHRONIZE CACHE command is not defined in this standard therefore this field should be set to zero. |
| 7:8 | 7:0 | **NUMBER OF LOGICAL BLOCKS:** The NUMBER OF LOGICAL BLOCKS field specifies the number of logical blocks that shall be synchronized, starting with the logical block specified by the LOGICAL BLOCK ADDRESS field. A NUMBER OF LOGICAL BLOCKS field set to zero specifies that all logical blocks starting with the one specified in the LOGICAL BLOCK ADDRESS field to the last logical block on the medium shall be synchronized. If the LBA plus the number of logical blocks exceeds the capacity of the medium, then the device server shall terminate the command with CHECK CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to LOGICAL BLOCK ADDRESS OUT OF RANGE. A logical block within the range that is not in cache is not considered an error. |
| 9 | 7:0 | **CONTROL:** The CONTROL byte is not used in this standard; the CONTROL byte should be set to zero and it shall be ignored by UFS device. |

---

*JEDEC Standard No. 220G*  
*Page 235*

# JEDEC Standard No. 220G
## Page 236

### 11.3.24.2 Synchronize Cache Command Data Transfer

The SYNCHRONIZE CACHE command does not have a data transfer phase.

• No DATA IN or DATA OUT UPIU's are transferred.

### 11.3.24.3 Synchronize Cache Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU.

• If the command is performed successfully then it will terminate with a STATUS response of GOOD.

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned.

• Other failures can occur for numerous reasons. When the SYNCHRONIZE CACHE command fails, a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as

    ○ ILLEGAL REQUEST (range or CDB errors)
    
    ○ MEDIUM ERROR (medium failure, ECC, etc.)
    
    ○ HARDWARE ERROR (hardware failure)
    
    ○ UNIT ATTENTION (reset, power-on, etc.)
    
    ○ etc.

# 11.3.25 SYNCHRONIZE CACHE (16) Command

See SYNCHRONIZE CACHE (10) command for details.

## Table 11.44 — SYNCHRONIZE CACHE (16) Command Descriptor Block

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-------------|---|---|---|---|---|---|---|---|
| 0 | | | OPERATION CODE (91h) | | | | | |
| 1 | | Reserved | | SYNC_NV | IMMED | Reserved |
| 2 | (MSB) | | | | | | | |
| ... | | | LOGICAL BLOCK ADDRESS | | | | | |
| 9 | | | | | | | | (LSB) |
| 10 | (MSB) | | | | | | | |
| ... | | | NUMBER OF LOGICAL BLOCKS | | | | | |
| 13 | | | | | | | | (LSB) |
| 14 | | Reserved | | GROUP NUMBER = 00000b | | | | |
| 15 | | | CONTROL = 00h | | | | | |

---
*JEDEC Standard No. 220G  
Page 237*