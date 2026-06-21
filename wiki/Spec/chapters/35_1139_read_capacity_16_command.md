# 11.39 READ CAPACITY (16) Command

The READ CAPACITY (16) command provides a means for the application client to discover the logical unit capacity. Refer to [SBC] for more details regarding the READ CAPACITY (16) command.

• The READ CAPACITY (16) command requests that the device server transfer 32 bytes of parameter data describing the capacity and medium format of the direct-access block device

The Command CDB shall be sent in a single COMMAND UPIU.

## Table 11.15 — READ CAPACITY (16) Command

| Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-----|---|---|---|---|---|---|---|---|
| Byte | | | | | | | | |
| 0 | | | OPERATION CODE (9Eh) | | | | | |
| 1 | Reserved | | | SERVICE ACTION (10h) | | | | |
| 2 | (MSB) | | | | | | | |
| .... | | | LOGICAL BLOCK ADDRESS | | | | | |
| 9 | | | | | | | | (LSB) |
| 10 | (MSB) | | | | | | | |
| .... | | | ALLOCATION LENGTH | | | | | |
| 13 | | | | | | | | (LSB) |
| 14 | Reserved | | | | | | | PMI = 0b |
| 15 | CONTROL = 00h | | | | | | | |

• PMI = 0 for UFS
• Logical Block Address = 0 for UFS
• Allocation Length = the maximum number of bytes that the application client has allocated for the returned parameter data.

### 11.39.1 Read Capacity (16) Data Response

• Data returned from a READ CAPACITY (16) command will be transferred to the Application Client in a single DATA IN UPIU

• The Device Server will transfer 32 bytes of Capacity Data in the Data Segment area of a DATA IN UPIU

• Data will be returned in the indicated Read Capacity Parameter format described in the following.

• No DATA IN UPIU will be transferred if an error occurs

---
*JEDEC Standard No. 220G*  
*Page 201*

# JEDEC Standard No. 220G
## Page 202

### 11.3.9.2 Read Capacity (16) Parameter Data

#### Table 11.16 — Read Capacity (16) Parameter Data

| Bit Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | (MSB) | | | | | | | |
| …. | | RETURNED LOGICAL BLOCK ADDRESS | | | | | | |
| 7 | | | | | | | | (LSB) |
| 8 | (MSB) | | | | | | | |
| …. | | LOGICAL BLOCK LENGTH IN BYTES | | | | | | |
| 11 | | | | | | | | (LSB) |
| 12 | | Reserved | | P_TYPE | | PROT_EN |
| 13 | P_I_EXPONENT | | LOGICAL BLOCKS PER PHYSICAL BLOCK EXPONENT | | |
| 14 | TPE | TPRZ | (MSB) | LOWEST ALIGNED LOGICAL BLOCK ADDRESS | | |
| 15 | | | | | | | | (LSB) |
| 16 | | | | | | | | |
| …. | | Reserved | | | | | | |
| 31 | | | | | | | | |

• **RETURNED LOGICAL BLOCK ADDRESS**: last addressable block on medium under control of logical unit (LU)

• **LOGICAL BLOCK LENGTH IN BYTES**: size of block in bytes
  ○ For UFS minimum size shall be 4096 bytes

• **P_TYPE, PROT_EN** are set to '0' for UFS

• The **P_I_EXPONENT** field can be ignored for PROT_EN = '0'

• **Logical Blocks per Physical Block Exponent** (vendor-specific information)
  ○ 0: one or more physical blocks per logical block
  ○ n > 0: 2ⁿ logical blocks per physical block

• **TPE** is set to '0' if bProvisioningType parameter in UFS Configuration Descriptor is set to 00h. TPE is set to '1' if bProvisioningType is set to 02h or 03h.

• **TPRZ** value is set by bProvisioningType parameter in UFS Configuration Descriptor. If the thin provisioning read zeros (TPRZ) bit is set to one, then, for an unmapped LBA specified by a read operation, the device server shall send user data with all bits set to zero to the data in buffer. If the TPRZ bit is set to zero, then, for an unmapped LBA specified by a read operation, the device server shall send user data with all bits set to any value to the data in buffer. **Lowest Aligned Logical Block Address** indicates the LBA of the first logical block that is located at the beginning of a physical block (vendor-specific information)

# JEDEC Standard No. 220G
## Page 203

### 11.3.9.3 Read Capacity (16) Status Response

• STATUS response will be sent in a single RESPONSE UPIU

• If the requested data is successfully transferred, the READ CAPACITY command will terminate with a STATUS response of GOOD

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned

• Failure can occur for a number of reasons. When the READ CAPACITY command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as

    ○ ILLEGAL REQUEST (range or CDB errors)
    
    ○ HARDWARE ERROR (hardware failure)
    
    ○ UNIT ATTENTION (reset, power-on, etc.)
    
    ○ etc.

# 11.3.10 START STOP UNIT Command

The START STOP UNIT command requests that the device server change the power condition of the logical unit or load or eject the medium.

• Enable or disable the direct-access block device for medium access operations by controlling power

The Command CDB shall be sent in a single COMMAND UPIU.

## Table 11.17 — START STOP UNIT Command

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-------------|---|---|---|---|---|---|---|---|
| 0 | | | | OPERATION CODE (1Bh) | | | | |
| 1 | | | | Reserved | | | | IMMED |
| 2 | | | | | Reserved | | | |
| 3 | | Reserved | | | POWER CONDITION MODIFIER = 0h | | | |
| 4 | | POWER CONDITIONS | | Reserved | NO_FLUSH | LOEJ<br>= 0b | START | |
| 5 | | | | CONTROL = 00h | | | | |

IMMED = 0 : Return STATUS (RESPONSE UPIU) after operation is completed  
IMMED = 1 : Return STATUS after CDB is decoded

## 11.3.10.1 START STOP UNIT Parameters

Power Condition Modifier shall be set to '0' (reserved) in UFS spec.  
Use of the other parameters is defined in the Power Mode sub-clause.

## 11.3.10.2 START STOP UNIT Data Response

• The START STOP UNIT command does not have a data phase
• No DATA IN or DATA OUT UPIU's are transferred

## 11.3.10.3 Start STOP UNIT STATUS Response

• STATUS response will be sent in a single RESPONSE UPIU
• If IMMED = 1 in the CDB, the STATUS response will be sent to the Application Client before the device operations have been completed
  ○ Usually used for shutting down
• If the requested operation is successful, the START STOP UNIT command will terminate with a STATUS response of GOOD
• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned
• Failure can occur for a few reasons. When the START STOP UNIT command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as
  ○ ILLEGAL REQUEST (range or CDB errors)
  ○ HARDWARE ERROR (hardware failure)
  ○ UNIT ATTENTION

---

JEDEC Standard No. 220G  
Page 204

# JEDEC Standard No. 220G
**Page 205**

## 11.3.11 TEST UNIT READY Command

The TEST UNIT READY command provides a means to check if the logical unit is ready. This is not a request for a self-test.

• If the logical unit is able to accept an appropriate medium-access command without returning CHECK CONDITION status, this command shall return a GOOD status.

• If the logical unit is unable to become operational or is in a state such that an Application Client action (e.g., START UNIT command) is required to make the logical unit ready, the command shall be terminated with CHECK CONDITION status, with the sense key set to NOT READY (02h).

The Command CDB shall be sent in a single COMMAND UPIU

### Table 11.18 — TEST UNIT READY Command

| Bit  | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|---|---|---|---|---|---|---|---|
| Byte |   |   |   |   |   |   |   |   |
| 0    |   |   | OPERATION CODE (00h) |   |   |   |   |   |
| 1    |   |   |   |   | Reserved |   |   |   |
| 2    |   |   |   |   | Reserved |   |   |   |
| 3    |   |   |   |   | Reserved |   |   |   |
| 4    |   |   |   |   | Reserved |   |   |   |
| 5    |   |   |   | CONTROL = 00h |   |   |   |

### 11.3.11.1 TEST UNIT READY Data Response

• The TEST UNIT READY command does not have a data response

• No DATA IN or DATA OUT UPIU's are transferred

### 11.3.11.2 TEST UNIT READY STATUS Response

• STATUS response will be sent in a single RESPONSE UPIU.

• If the command succeeds without error, the TEST UNIT READY command will terminate with a STATUS response of GOOD

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned

• Failure can occur for numerous reasons. When the TEST UNIT READY command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as
  ○ ILLEGAL REQUEST (CDB errors)
  ○ HARDWARE ERROR (hardware failure)
  ○ UNIT ATTENTION (reset, power-on, etc.)
  ○ etc.