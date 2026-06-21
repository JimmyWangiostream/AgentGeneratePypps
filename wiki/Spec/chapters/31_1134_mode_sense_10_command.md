# JEDEC Standard No. 220G
Page 190

## 11.3.3.3 Mode Select Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU

• If the requested data is successfully transferred and written, the MODE SELECT command will terminate with a STATUS response of GOOD

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned

• Failure can occur for numerous reasons. When the MODE SELECT command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as

  ○ ILLEGAL REQUEST (CDB or parameter errors)
  
  ○ MEDIUM ERROR (medium failure, ECC, etc.)
  
  ○ HARDWARE ERROR (hardware failure)
  
  ○ UNIT ATTENTION (reset, power-on, etc.)

## 11.3.4 MODE SENSE (10) Command

The MODE SENSE command provides a means for a Device Server to report parameters to an Application Client

• Parameters are managed by means of parameter pages called Mode Pages

  ○ UFS devices shall support the following mode pages
  
    ▪ CONTROL, READ-WRITE ERROR RECOVERY, CACHING
  
  ○ UFS devices may support vendor specific mode pages
  
  ○ See 11.4 for further details

• Reads parameter pages in a list

  ○ The Application Client may request any one or all of the supported pages from the Device Server
  
  ○ If all pages requested, they will be returned in ascending page order

• Mode Sense returns DEVICE-SPECIFIC PARAMETER in header

  ○ See paragraph 0,
  
  ○ Mode Parameter Header for details.

• Complementary command to the MODE SELECT command

The Command CDB shall be sent in a single COMMAND UPIU

# 11.3.4 MODE SENSE (10) Command (cont'd)

## Table 11.7 — MODE SENSE (10) Command

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | | | OPERATION CODE (5Ah) | | | | | |
| 1 | Reserved =000b | | LLBAA =0b | DBD = 1b | Reserved = 000b | |
| 2 | PC | | | PAGE CODE | | | |
| 3 | | | SUBPAGE CODE | | | | |
| 4 | | | | | | | | |
| 5 | | | Reserved | | | | | |
| 6 | | | | | | | | |
| 7 | (MSB) | | | | | | | |
| 8 | | ALLOCATION LENGTH | | | | | (LSB) |
| 9 | | | CONTROL = 00h | | | | | |

## 11.3.4.1 Mode Sense Command Parameters

### Table 11.8 — Mode Sense Command Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 2 | 7:6 | **PC:** The page control (PC) field specifies the type of mode parameter values to be returned in the mode pages. See Table 11.9 for its definition. |
| 2 | 5:0 | **PAGE CODE:** Specifies which mode page to return. The Page and Subpage code specify the page to return. |
| 3 | 7:0 | **SUBPAGE CODE:** Specifies which subpage mode page to return |
| 7:8 | 7:0 | **ALLOCATION LENGTH:** Specifies the maximum number of bytes the Device Server will transfer to the Application Client |

---

JEDEC Standard No. 220G  
Page 191

# JEDEC Standard No. 220G
Page 192

## 11.3.4.2 Page Control Function

### Table 11.9 — Page Control Function

| Page Control (PC) | Description | Use |
|-------------------|-------------|-----|
| 00b | Current Values | Return the current operational mode page parameter values. |
| 01b | Changeable Values | Return a bit mask denoting values that are changeable. Changeable bits in the mode parameters will have a value of '1', non-changeable will have a value of '0'. |
| 10b | Default Values | Return the default values of the mode parameters. |
| 11b | Saved Values | Return the saved values of the mode parameters. |

## 11.3.4.3 Mode Sense Command Data Transfer

The Device Server will transfer up to Allocation Length number of data bytes of Mode Parameter Data to the Application Client.

• Less than Allocation Length will be transferred if Device Server contains less bytes

The Device Server will transfer the data as indicated by the Mode Parameter Layout

• Header (8 bytes)

• Block Descriptor (0 bytes for UFS)

• Page Data (N bytes, dependent up page requested)

Data will be transferred from the Device Server to the Application Client via a series of DATA IN UPIU's

• The data transferred from the Device Server will be contained within the Data Segment of the DATA IN UPIU

Zero or an incomplete number of DATA IN UPIU's will be transferred if an error occurs before the entire data transfer is complete.

## 11.3.4.4 Mode Sense Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU

• If the requested data is successfully transferred and written, the MODE SENSE command will terminate with a STATUS response of GOOD

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned

• Failure occurs when a requesting a page or subpage that is not supported. A STATUS response of CHECK CONDITION will be returned with a SENSE KEY indicating ILLEGAL REQUEST

• Failure can occur for numerous reasons. When the MODE SENSE command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as
  ○ ILLEGAL REQUEST (CDB errors)
  ○ HARDWARE ERROR (hardware failure)
  ○ UNIT ATTENTION (reset, power-on, etc.)

# 11.3.5 READ (6) Command

The READ (6) command (see Table 11.10) requests that the Device Server read from the medium the specified number of logical block(s) and transfer them to the Application Client.

The Command CDB shall be sent in a single COMMAND UPIU.

## Table 11.10 — READ (6) Command

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | | | OPERATION CODE (08h) | | |
| 1 | Reserved | (MSB) | | | |
| 2 | | | | | |
| 3 | | LOGICAL BLOCK ADDRESS | | (LSB) |
| 4 | | TRANSFER LENGTH | | |
| 5 | | CONTROL = 00h | | |

### 11.3.5.1 Read (6) Command Parameters

• **LOGICAL BLOCK ADDRESS:** Address of first block

• **TRANSFER LENGTH:** Number of contiguous logical blocks of data that shall be read and transferred. A transfer length of zero specifies that 256 logical blocks shall be read. Any other value specifies the number of logical blocks that shall be read.

### 11.3.5.2 Read (6) Command Data Transfer

• The Device Server will read the specified logical block(s) from the medium and transfer them to the Application Client in a series of DATA IN UPIU's

• The data segment of each DATA IN UPIU shall contain an integer number of logical blocks

• Zero or an incomplete number of DATA IN UPIU's could be transferred if a read error occurs before the entire data transfer is complete

### 11.3.5.3 Read (6) Command Status Response

• Status response will be sent in a single RESPONSE UPIU

• If all requested data is successfully read and transferred, the READ command will terminate with a STATUS response of GOOD

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned

• Failure can occur for numerous reasons. When the READ command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as
  ○ ILLEGAL REQUEST (range or CDB errors)
  ○ MEDIUM ERROR (medium failure, ECC, etc.)
  ○ HARDWARE ERROR (hardware failure)
  ○ UNIT ATTENTION (reset, power-on, etc.)
  ○ etc.

---
*JEDEC Standard No. 220G*  
*Page 193*