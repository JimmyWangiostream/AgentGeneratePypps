# 11.3.15 WRITE (10) Command

The WRITE (10) UFS command requests that the Device Server transfer the specified number of logical block(s) from the Application Client and write them to the medium.
The Command CDB shall be sent in a single COMMAND UPIU.

## Table 11.30 — WRITE (10) Command

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-------------|---|---|---|---|---|---|---|---|
| 0 | | | | OPERATION CODE (2Ah) | | | | |
| 1 | WRPROTECT<br>= 000b | | DPO | FUA | Reserved | FUA_NV<br>= 0b | Obsolete |
| 2 | (MSB) | | | | | | | |
| 3 | | | LOGICAL BLOCK ADDRESS | | | | |
| 4 | | | | | | | | |
| 5 | | | | | | | | (LSB) |
| 6 | Reserved | | | GROUP NUMBER | | | |
| 7 | (MSB) | | | | | | | |
| 8 | | | TRANSFER LENGTH | | | | | (LSB) |
| 9 | | | | CONTROL = 00h | | | | |

• The WRPROTECT field is set to zero for UFS.

---
JEDEC Standard No. 220G  
Page 215

# JEDEC Standard No. 220G
Page 216

## 11.3.15.1 Write (10) Command Parameters

• **DPO: Disable Page Out**
  "0" = specifies that the retention priority shall be determined by the RETENTION PRIORITY fields in the Caching mode page
  "1" = specifies that the device server shall assign the logical blocks accessed by this command the lowest retention priority for being fetched into or retained by the cache. A DPO bit set to one overrides any retention priority specified in the Caching mode page.

• **FUA: Force Unit Access**
  "0" = The Device Server shall write the logical blocks to the cache and/or the medium.
  "1" = The Device Server shall write the logical blocks to the medium, and shall not complete the command with GOOD status until all the logical blocks have been written on the medium without error.

• FUA_NV is defined per SBC. Since non-volatile cache support is not currently defined in this standard, the FUA_NV parameter value in the CDB is ignored by the UFS Device Server.

• **LOGICAL BLOCK ADDRESS:** Address of first block

• **TRANSFER LENGTH:** Number of contiguous logical blocks of data that shall be transferred and written. A transfer length of zero specifies that no logical blocks will be written. This condition shall not be considered an error.

• **GROUP NUMBER:** Notifies the Target device that the data has System Data characteristics or linked to a ContextID:

| GROUP NUMBER Value | Function |
|-------------------|----------|
| 00000b | Default, no Context ID or System Data characteristics is associated with the write operation. |
| 00001b to 01111b (0XXXXb) | Context ID. (XXXX from 0001b to 1111b - Context ID value) |
| 10000b | Data has System Data characteristics |
| 10001b to 10111b | Reserved |
| 11000b | Pinned data in Pinned Partial Flush Mode of WriteBooster Buffer |
| 11001b to 11111b | Reserved |

In case the GROUP NUMBER is set to a reserved value, then the operation shall fail and a status response of CHECK CONDITION will be returned along the sense key set to ILLEGAL REQUEST.

# JEDEC Standard No. 220G
## Page 217

### 11.3.15.2 Write(10) Command Data Transfer

The Device Server requests to transfer the specified logical block(s) from the Application Client data-out buffer by issuing a series of READY TO TRANSFER UPIU's (RTT).

The data is delivered in one or more segments sending DATA OUT UPIU packets, as indicated in the RTT requests. The data contained in DATA OUT UPIU is written.

The number of bytes requested and the Data Buffer Offset field in each RTT shall both be integer multiples of the Logical Block Size (bLogicalBlockSize).

The data segment of each DATA OUT UPIU shall contain an integer number of logical blocks.

Zero or an incomplete number of segments may be requested, if an error occurs before the entire data transfer is complete.

### 11.3.15.3 Write (10) Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU.

• If all requested data is successfully transferred and written, the WRITE command will terminate with a STATUS response of GOOD.

• If the logical blocks are transferred directly to a cache then the Device Server may complete the command with a GOOD status prior to writing the logical blocks to the medium.

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned.

• Failure can occur for numerous reasons. When the WRITE command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as
  ○ ILLEGAL REQUEST (range or CDB errors)
  ○ MEDIUM ERROR (medium failure, ECC, etc.)
  ○ HARDWARE ERROR (hardware failure)
  ○ UNIT ATTENTION (reset, power-on, etc.)
  ○ DATA PROTECT (permanent, power-on, secure write protect, etc.)
  ○ etc.