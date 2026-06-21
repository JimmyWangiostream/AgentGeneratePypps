# 11.3.16 WRITE (16) Command

The WRITE (16) UFS command requests that the Device Server transfer the specified number of logical block(s) from the Application Client and write them to the medium.

The Command CDB shall be sent in a single COMMAND UPIU.

## Table 11.31 — WRITE (16) Command

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | | | OPERATION CODE (8Ah) | | | | | |
| 1 | WRPROTECT = 0000 | | DPO | FUA | Reserved | FUA_NV = 0b | Reserved |
| 2 | (MSB) | | | | | | | |
| .... | | | LOGICAL BLOCK ADDRESS | | | | | |
| 9 | | | | | | | | (LSB) |
| 10 | (MSB) | | | | | | | |
| .... | | | TRANSFER LENGTH | | | | | |
| 13 | | | | | | | | (LSB) |
| 14 | Reserved⁽¹⁾ | Reserved | | GROUP NUMBER | | | | |
| 15 | | | CONTROL = 00h | | | | | |

**NOTE 1** Bit 7 of byte 14 shall be ignored.

• The WDPROTECT field is set to zero for UFS.

---

*JEDEC Standard No. 220G  
Page 218*

# JEDEC Standard No. 220G
Page 219

## 11.3.16.1 Write (16) Command Parameters

• **DPO**: Disable Page Out  
"0" = specifies that the retention priority shall be determined by the RETENTION PRIORITY fields in the Caching mode page  
"1" = specifies that the device server shall assign the logical blocks accessed by this command the lowest retention priority for being fetched into or retained by the cache. A DPO bit set to one overrides any retention priority specified in the Caching mode page.

• **FUA**: Force Unit Access  
"0" = The Device Server shall write the logical blocks to the cache and/or the medium.  
"1" = The Device Server shall write the logical blocks to the medium, and shall not complete the command with GOOD status until all the logical blocks have been written on the medium without error.

• **FUA_NV** is defined per SBC. Since non-volatile cache support is not currently defined in this standard, the FUA_NV parameter value in the CDB is ignored by the UFS Device Server.

• **LOGICAL BLOCK ADDRESS**: Address of first block

• **TRANSFER LENGTH**: Number of contiguous logical blocks of data that shall be transferred and written. A transfer length of zero specifies that no logical blocks will be written. This condition shall not be considered an error.

• **GROUP NUMBER**: See Write (10) Command.

## 11.3.16.2 Write (16) Command Data Transfer

The Device Server requests to transfer the specified logical block(s) from the Application Client data-out buffer by issuing a series of READY TO TRANSFER UPIU's (RTT).

The data is delivered in one or more segments sending DATA OUT UPIU packets, as indicated in the RTT requests. The data contained in DATA OUT UPIU is written.

The number of bytes requested and the Data Buffer Offset field in each RTT shall both be integer multiples of the Logical Block Size (bLogicalBlockSize).

The data segment of each DATA OUT UPIU shall contain an integer number of logical blocks.

Zero or an incomplete number of segments may be requested, if an error occurs before the entire data transfer is complete.

# JEDEC Standard No. 220G
Page 220

## 11.3.16.3 Write (16) Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU

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