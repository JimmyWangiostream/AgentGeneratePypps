# 11.37 READ (16) Command

The READ (16) command (see Table 11.12) requests that the Device Server read from the medium the specified number of logical block(s) and transfer them to the Application Client.

The Command CDB shall be sent in a single COMMAND UPIU

## Table 11.12 — READ (16) Command

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-------------|---|---|---|---|---|---|---|---|
| 0 | | | | OPERATION CODE (88h) | | | | |
| 1 | RDPROTECT<br>= 000b | | DPO | FUA | Reserved | FUA_NV<br>= 0b | Reserved |
| 2 | (MSB) | | | | | | | |
| …. | | | LOGICAL BLOCK ADDRESS | | | | |
| 9 | | | | | | | | (LSB) |
| 10 | (MSB) | | | | | | | |
| …. | | | TRANSFER LENGTH | | | | |
| 13 | | | | | | | | (LSB) |
| 14 | Reserved | Reserved | | GROUP NUMBER | | | |
| 15 | | | CONTROL = 00h | | | | |

• The RDPROTECT field is set to zero for UFS.

---

*JEDEC Standard No. 220G*  
*Page 196*

# JEDEC Standard No. 220G
Page 197

## 11.3.7.1 Read (16) Command Parameters

• **DPO = Disable Page Out**  
  "0" = specifies that the retention priority shall be determined by the RETENTION PRIORITY fields in the Caching mode page.  
  "1" = specifies that the device server shall assign the logical blocks accessed by this command the lowest retention priority for being fetched into or retained by the cache. A DPO bit set to one overrides any retention priority specified in the Caching mode page.

• **FUA: Force Unit Access**  
  '0' = The Device Server may read the logical blocks from the cache and/or the medium.  
  '1' = The Device Server shall read the logical blocks from the medium. If a cache contains a more recent version of a logical block, then the device server shall write the logical block to the medium before reading it.

• **FUA_NV** is defined per SBC. Since non-volatile cache support is not currently defined in this standard, the FUA_NV parameter value in the CDB is ignored by the UFS Device Server.

• **LOGICAL BLOCK ADDRESS:** Address of first block

• **TRANSFER LENGTH:** Number of contiguous logical blocks of data that shall be read and transferred. A transfer length of zero specifies that no logical blocks will be read. This condition shall not be considered an error.

• **GROUP NUMBER:** See Read (10) Command.

## 11.3.7.2 Read (16) Command Data Transfer

• The Device Server will read the specified logical block(s) from the medium and transfer them to the Application Client in a series of DATA IN UPIU's

• The data segment of each DATA IN UPIU shall contain an integer number of logical blocks

• Zero or an incomplete number of DATA IN UPIU's could be transferred if a read error occurs before the entire data transfer is complete

## 11.3.7.3 Read (16) Command Status Response

• Status response will be sent in a single RESPONSE UPIU

• If all requested data is successfully read and transferred, the READ command will terminate with a STATUS response of GOOD

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned

• Failure can occur for numerous reasons. When the READ command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as
  ○ ILLEGAL REQUEST (range or CDB errors)
  ○ MEDIUM ERROR (medium failure, ECC, etc.)
  ○ HARDWARE ERROR (hardware failure)
  ○ UNIT ATTENTION (reset, power-on, etc.)
  ○ etc.