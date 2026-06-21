# 11.3.8 READ CAPACITY (10) Command

The READ CAPACITY (10) command provides a means for the application client to discover the logical unit capacity. Refer to [SBC] for more details regarding the READ CAPACITY (10) command.

• The READ CAPACITY (10) command requests that the device server transfer 8 bytes of parameter data describing the capacity and medium format of the direct-access block device

The Command CDB shall be sent in a single COMMAND UPIU

## Table 11.13 — READ CAPACITY (10) Command

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | | | | OPERATION CODE (25h) | | | | |
| 1 | | | Reserved | | | | | Obsolete = 0b |
| 2 | (MSB) | | | | | | | |
| ... | | | LOGICAL BLOCK ADDRESS | | | | | |
| 5 | | | | | | | | (LSB) |
| 6 | | | | Reserved | | | | |
| 7 | | | | Reserved | | | | |
| 8 | | | Reserved | | | | | PMI = 0b |
| 9 | | | | CONTROL = 00h | | | | |

• PMI = 0 for UFS

• Logical Block Address = 0 for UFS

# JEDEC Standard No. 220G
Page 199

## 11.3.8.1 Read Capacity (10) Data Response

• Data returned from a READ CAPACITY (10) command will be transferred to the Application Client in a single DATA IN UPIU

• The Device Server will transfer 8 bytes of Capacity Data in the Data Segment area of a DATA IN UPIU

• Data will be returned in the indicated Read Capacity Parameter format described in the following.

• No DATA IN UPIU will be transferred if an error occurs

## 11.3.8.2 Read Capacity (10) Parameter Data

### Table 11.14 — Read Capacity (10) Parameter Data

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-------------|---|---|---|---|---|---|---|---|
| 0 | (MSB) |  |  |  |  |  |  |  |
| 1 |  |  |  |  |  |  |  |  |
| 2 |  | RETURNED LOGICAL BLOCK ADDRESS |  |  |  |  |  |  |
| 3 |  |  |  |  |  |  |  | (LSB) |
| 4 | (MSB) |  |  |  |  |  |  |  |
| 5 |  |  |  |  |  |  |  |  |
| 6 |  | LOGICAL BLOCK LENGTH IN BYTES |  |  |  |  |  |  |
| 7 |  |  |  |  |  |  |  | (LSB) |

• RETURNED LOGICAL BLOCK ADDRESS: last addressable block on medium under control of logical unit (LU)

  ○ If the number of logical blocks exceeds the maximum value that is able to be specified in the RETURNED LOGICAL BLOCK ADDRESS field, then the device server shall set the RETURNED LOGICAL BLOCK ADDRESS field to FFFF FFFFh. The application client should then issue a READ CAPACITY (16) command to request that the device server transfer the READ CAPACITY (16) parameter data to the data-in buffer.

• LOGICAL BLOCK LENGTH IN BYTES: size of block in bytes

  ○ For UFS minimum size shall be 4096 bytes

# JEDEC Standard No. 220G
Page 200

## 11.3.8.3 Read Capacity (10) Status Response

• STATUS response will be sent in a single RESPONSE UPIU
• If the requested data is successfully transferred, the READ CAPACITY command will terminate with a STATUS response of GOOD
• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned
• Failure can occur for a number of reasons. When the READ CAPACITY command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as
  ○ ILLEGAL REQUEST (range or CDB errors)
  ○ HARDWARE ERROR (hardware failure)
  ○ UNIT ATTENTION (reset, power-on, etc.)
  ○ etc.