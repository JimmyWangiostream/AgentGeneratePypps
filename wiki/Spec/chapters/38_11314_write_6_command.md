# 11.3.14 WRITE (6) Command

The WRITE (6) UFS command requests that the Device Server transfer the specified number of logical blocks(s) from the Application Client and write them to the medium.
The Command CDB shall be sent in a single COMMAND UPIU.

## Table 11.29 — WRITE (6) Command

| Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-----|---|---|---|---|---|---|---|---|
| Byte |   |   |   |   |   |   |   |   |
| 0 |   |   | OPERATION CODE (0Ah) |   |   |   |   |   |
| 1 | Reserved |   |   | (MSB) |   |   |   |   |
| 2 |   |   |   |   |   |   |   |   |
| 3 |   |   | LOGICAL BLOCK ADDRESS |   |   |   |   | (LSB) |
| 4 |   |   | TRANSFER LENGTH |   |   |   |   |   |
| 5 |   |   | CONTROL = 00h |   |   |   |   |   |

## 11.3.14.1 Write (6) Command Parameters

• LOGICAL BLOCK ADDRESS: Address of first block

• TRANSFER LENGTH: Number of contiguous logical blocks of data that shall be transferred and written. A transfer length of zero specifies that 256 logical blocks shall be written. Any other value specifies the number of logical blocks that shall be written.

## 11.3.14.2 Write (6) Command Data Transfer

The Device Server requests to transfer the specified logical block(s) from the Application Client data-out buffer by issuing one or more READY TO TRANSFER UPIU's (RTT).

The data is delivered in one or more segments sending DATA OUT UPIU packets, as indicated in the RTT requests. The data contained in DATA OUT UPIU is written.

The number of bytes requested and the Data Buffer Offset field in each RTT shall both be integer multiples of the Logical Block Size (bLogicalBlockSize).

The data segment of each DATA OUT UPIU shall contain an integer number of logical blocks.

Zero or an incomplete number of segments may be requested, if an error occurs before the entire data transfer is complete.

---

JEDEC Standard No. 220G  
Page 213

# JEDEC Standard No. 220G
Page 214

## 11.3.14.3 Write (6) Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU

• If all requested data is successfully transferred and written, the WRITE command will terminate with a STATUS response of GOOD

• If the logical blocks are transferred directly to a cache then the Device Server may complete the command with a GOOD status prior to writing the logical blocks to the medium

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned

• Failure can occur for numerous reasons. When the WRITE command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as

  ○ ILLEGAL REQUEST (range or CDB errors)

  ○ MEDIUM ERROR (medium failure, ECC, etc.)

  ○ HARDWARE ERROR (hardware failure)

  ○ UNIT ATTENTION (reset, power-on, etc.)

  ○ DATA PROTECT (permanent, power-on, secure write protect, etc.)

  ○ etc.