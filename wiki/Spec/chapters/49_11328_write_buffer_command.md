# JEDEC Standard No. 220G
Page 248

## 11.3.28 WRITE BUFFER Command

The WRITE BUFFER command is used in conjunction with the READ BUFFER command for

• testing logical unit buffer memory

• testing the integrity of the service delivery subsystem

• Field Firmware Update

• Retrieving error history and statistics

The WRITE BUFFER command transfers a specified number of data bytes from a buffer in the Application Client to a specified buffer in the Device Server at a specified buffer offset.

The Command CDB shall be sent in a single COMMAND UPIU

### Table 11.54 — WRITE BUFFER Command

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | | | OPERATION CODE (3Bh) | | | | | |
| 1 | | Reserved | | | | MODE | | |
| 2 | | | BUFFER ID | | | | | |
| 3 | (MSB) | | | | | | | |
| 4 | | | BUFFER OFFSET | | | | | |
| 5 | | | | | | | | (LSB) |
| 6 | (MSB) | | | | | | | |
| 7 | | | PARAMETER LIST LENGTH | | | | | |
| 8 | | | | | | | | (LSB) |
| 9 | | | CONTROL = 00h | | | | | |

# JEDEC Standard No. 220G
## Page 249

### 11.3.28.1 Write Buffer Command Parameters

#### Table 11.55 — Write Buffer Command Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 1 | 4:0 | MODE: Specifies the function of this command. See Table 11.56 for more detail. |
| 2 | 7:0 | BUFFER ID: Specifies a buffer within the logical unit. Buffer 0 shall be supported. If more than one buffer is supported, then additional BUFFER ID codes shall be assigned contiguously, beginning with one. |
| 3:5 | 7:0 | BUFFER OFFSET: Specifies the byte offset within the specified buffer from which data shall be transferred. |
| 6:8 | 7:0 | PARAMETER LIST LENGTH: Specifies the maximum number of bytes the Application Client buffer will transfer to the Device Server. |

### 11.3.28.2 Write Buffer Command Mode Field Values

#### Table 11.56 — Write Buffer Command Mode Field Values

| MODE | DESCRIPTION |
|------|-------------|
| 00h | Not used in UFS |
| 01h | Vendor Specific |
| 02h | Data |
| 03h | Not used in UFS |
| 04h | Not used in UFS |
| 05h | Not used in UFS |
| 06h | Not used in UFS |
| 07h | Not used in UFS |
| 08h-0Dh | Not used in UFS |
| 0Eh | Download microcode with offsets, save and defer active |
| 0Fh | Not used in UFS |
| 10h-1Ch | Not used in UFS |
| 1Dh-1Fh | Reserved |

• The device shall support the MODE value of 02h, indicating Data Mode. The BUFFER ID field specifies a buffer to which data shall be transferred. The BUFFER OFFSET field specifies the location to which the data is written.

• The definition and structure of the data being transferred in Data Mode is device specific.

• UFS device shall support a MODE value of 0Eh for microcode download as defined in the Field Firmware Update clause.

# JEDEC Standard No. 220G
## Page 250

### 11.3.28.2.1 Field Firmware Update

UFS Field Firmware Update (FFU) is based on microcode download definition in [SPC].

[SPC] describes multiple operation modes for microcode download which are selected using the MODE field in the WRITE BUFFER command. UFS supports only the MODE field value 0Eh: "Download microcode with offsets, save, and defer active".

The deferred microcode shall be activated and no longer considered deferred when a power on or a hard reset occurs. Note that in UFS, START STOP UNIT command, FORMAT UNIT command or WRITE BUFFER command (MODE=0Fh) will not activate the microcode.

UFS FFU uses the following mechanism:

1) Host delivers the microcode using one or more WRITE BUFFER commands through any logical unit which supports the WRITE BUFFER command. The host specifies: MODE = 0Eh, BUFFER OFFSET, which should be aligned to 4 Kbyte, BUFFER ID = 00h, and the PARAMETER LIST LENGTH field indicating the number of bytes to be transferred. All WRITE BUFFER commands should be sent to the same logical unit with task attribute set to simple or ordered. In the sequence of WRITE BUFFER commands used to deliver the microcode, the BUFFER OFFSET values should be in increasing order and it should start from zero.

2) bBFUTimeout indicates the maximum time in which the device may handle the WRITE BUFFER command. Within this time access to the device is limited or not possible.

3) Following a successful delivery of the microcode, the host activates the new firmware using a hardware reset or a power cycle. The UFS device shall use new firmware upon hard reset or power up. Host should be aware that the first initialization flow after a successful delivery of the microcode may be longer than usual.

4) After device initialization, the host should read bDeviceFFUStatus attribute and verify that the new firmware was updated successfully.

Other modes of WRITE BUFFER command are not supported by the UFS device for FFU process.

### 11.3.28.3 Write Buffer Command Data Transfer

The Device Server requests to transfer the buffer data from the Application Client data-out buffer by issuing a series of READY TO TRANSFER UPIU's (RTT).

The buffer data is delivered in one or more segments sending DATA OUT UPIU packets, as indicated in the RTT requests.

Zero or an incomplete number of segments may be requested, if an error occurs before the entire data transfer is complete.

The received data is written to the location specified by the BUFFER OFFSET field within the buffer specified by the BUFFER ID field.

# 11.3.28.4 Write Buffer Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU
• If the requested data is successfully transferred and written, the WRITE BUFFER command will terminate with a STATUS response of GOOD
• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned
• Failure can occur for numerous reasons. When the WRITE BUFFER command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as:
  ○ ILLEGAL REQUEST (range or CDB errors)
  ○ MEDIUM ERROR (medium failure, ECC, etc.)
  ○ HARDWARE ERROR (hardware failure)
  ○ UNIT ATTENTION (reset, power-on, etc.)
  ○ etc.

---

*JEDEC Standard No. 220G  
Page 251*

# JEDEC Standard No. 220G
Page 252

## 11.3.29 BARRIER Command

The BARRIER command requests that the device server guarantee that the data for the commands issued before the BARRIER command are flushed to the non-volatile memory before flushing the data for the commands issued after the BARRIER command. The BARRIER commands shall affect only the normal priority commands having the simple task attribute.

### Table 11.57 — BARRIER Command

| Bit Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | | | | OPERATION CODE (F0h) | | | | |
| 1 | | | | Reserved | | | | |
| 2 | | | | | | | | |
| 5 | | | | Reserved | | | | |
| 6 | | | | | | | | |
| 9 | | | | Reserved | | | | |
| 10 | | | | | | | | |
| 13 | | | | Reserved | | | | |
| 14 | | | | Reserved | | | | |
| 15 | | | | CONTROL = 00h | | | | |

### 11.3.29.1 BARRIER Command Data Transfer

The BARRIER command does not have a data transfer phase.

• No DATA IN or DATA OUT UPIU's are transferred.

### 11.3.29.2 BARRIER Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU.
• If the command is performed successfully then it will terminate with a STATUS response of GOOD.
• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned.
• Other failures can occur for numerous reasons. When the BARRIER command fails, a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as:
    ○ ILLEGAL REQUEST (range or CDB errors)
    ○ HARDWARE ERROR (hardware failure)
    ○ UNIT ATTENTION (reset, power-on, etc.)
    ○ etc.