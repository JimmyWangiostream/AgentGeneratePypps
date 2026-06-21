# JEDEC Standard No. 220G
Page 242

## 11.3.27 READ BUFFER Command

The READ BUFFER command is used in conjunction with the WRITE BUFFER command for

• testing logical unit buffer memory

• testing the integrity of the service delivery subsystem

• Downloading microcode

• Retrieving error history and statistics

The READ BUFFER command transfers a specified number of data bytes from a specified offset within a specified buffer in the Device Server to a buffer in the Application Client.
The Command CDB shall be sent in a single COMMAND UPIU.

**Table 11.48 — READ BUFFER Command**

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | | | OPERATION CODE (3Ch) | | | | | |
| 1 | | Reserved | | | | MODE | | |
| 2 | | | BUFFER ID | | | | | |
| 3 | (MSB) | | | | | | | |
| 4 | | | BUFFER OFFSET | | | | | |
| 5 | | | | | | | | (LSB) |
| 6 | (MSB) | | | | | | | |
| 7 | | | ALLOCATION LENGTH | | | | | |
| 8 | | | | | | | | (LSB) |
| 9 | | | CONTROL = 00h | | | | | |

# 11.3.27.1 Read Buffer Command MODE Field Values

## Table 11.49 — Read Buffer Command Mode Field Values

| MODE | DESCRIPTION |
|------|-------------|
| 00h | Not used in UFS |
| 01h | Vendor Specific |
| 02h | Data |
| 03h-1Bh | Not used in UFS |
| 1Ch | Error history |
| 1Dh-1Fh | Reserved |

• The device shall support the MODE value of 02h, indicating Data Mode. The definition and structure of the data being transferred in Data Mode is device specific.

• The device shall support the MODE value of 1Ch, indicating Error History Mode. The format of the error history is device specific.

## 11.3.27.2 Data Mode (MODE = 02h)

• The BUFFER ID field specifies a buffer within the logical unit from which data shall be transferred. Buffer ID 0 shall be supported. If more than one buffer is supported, then additional buffer ID codes shall be assigned contiguously, beginning with one.

• The BUFFER OFFSET field contains the byte offset within the specified buffer from which data shall be transferred.

• The Device Server will read up to Allocation Length number of data bytes from the specified Buffer Offset within a buffer specified by the Buffer ID in the Device Server and transfer them to a buffer in the Application Client

  ○ Less than Allocation Length will be transferred if Device Server contains less bytes

• Data will be transferred from the Device Server to the Application Client via a series of DATA IN UPIU's

  ○ The data transferred from the Device Server will be contained within the Data Segment of the DATA IN UPIU

• Zero or an incomplete number of DATA IN UPIU's will be transferred if an error occurs before the entire data transfer is complete

---
*JEDEC Standard No. 220G*  
*Page 243*

# JEDEC Standard No. 220G
## Page 244

### 11.3.27.3 Error History Mode (MODE = 1Ch)

• The BUFFER ID field specifies the action that the device server shall perform, and the parameter data, if any, that the device server shall return.

#### Table 11.50 — Buffer ID Field for Error History Mode

| CODE | DESCRIPTION | BUFFER OFFSET |
|------|-------------|---------------|
| 00h | Return error history directory¹ | Zero² |
| 01h – 03h | Not used in UFS | |
| 04h – 0Fh | Reserved | |
| 10h – EFh | Return error history from corresponding error history data buffer ID | Zero² to Maximum³ |
| F0h – FDh | Reserved | |
| FEh | Clear Error History⁴ | |
| FFh | Not used in UFS | |

**NOTE 1** A error history snapshot is never created in this standard.
**NOTE 2** Zero is 000000h for the READ BUFFER (10) command.
**NOTE 3** Maximum is FFFFFFh for the READ BUFFER (10) command.
**NOTE 4** Clear the error history, if any. No data transfer. Buffer Offset is ignored by the device.
Supportability of error history clear operation is vendor specific and is indicated in
dExtendedUFSFeaturesSupport field of DEVICE DESCRIPTOR.

• In UFS standard, error history L_T nexus is always established and valid.

• In UFS standard, there is no error history snapshot exist. The returned error history may be real time contents or may be the contents captured at a vendor specific point in time.

• The BUFFER OFFSET field specifies the byte offset from the start of the buffer specified by the BUFFER ID field from which the device server shall return data.

• The Device Server will read up to Allocation Length number of data bytes from the specified Buffer Offset within a buffer specified by the Buffer ID in the Device Server and transfer them to a buffer in the Application Client
  ○ Less than Allocation Length will be transferred if Device Server contains less bytes

• Data will be transferred from the Device Server to the Application Client via a series of DATA IN UPIU's
  ○ The data transferred from the Device Server will be contained within the Data Segment of the DATA IN UPIU

• Zero or an incomplete number of DATA IN UPIU's will be transferred if an error occurs before the entire data transfer is complete

• See [SPC] for further details.

# 11.3.27.3.1 Error History Directory

The error history directory is defined in Table 11.51, and the error history directory entry is defined in Table 11.53.

## Table 11.51 — Error history directory

| Bit Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | (MSB) | | | | | | | |
| ... | | T10 VENDOR IDENTIFICATION | | | | | | |
| 7 | | | | | | | | (LSB) |
| 8 | | VERSION | | | | | | |
| 9 | Reserved | | EHS_RETRIEVED = 00b | EHS_SOURCE = 00b | CLR_SUP = 0b |
| 10 | (MSB) | | | | | | | |
| ... | | Reserved | | | | | | |
| 29 | | | | | | | | (LSB) |
| 30 | (MSB) | | | | | | | |
| 31 | | DIRECTORY LENGTH (n-31) | | | | | | (LSB) |
| | | Error history directory list | | | | | | |
| 32 | | | | | | | | |
| ... | | Error history directory entry [first] | | | | | | |
| 39 | | | | | | | | |
| ... | | ... | | | | | | |
| n-7 | | | | | | | | |
| ... | | Error history directory entry [last] | | | | | | |
| n | | | | | | | | |

• The T10 VENDOR IDENTIFICATION field contains eight bytes of left-aligned ASCII data as defined in [SPC].

• The VERSION field indicates the version and format of the vendor specific error history. The VERSION field is assigned by the vendor indicated in the T10 VENDOR IDENTIFICATION field.

• The DIRECTORY LENGTH field indicates the number of error history directory list bytes available to be transferred. This value shall not be altered even if the allocation length is not sufficient to transfer the entire error history directory list.

• The error history source (EHS_SOURCE) field indicates the source of the error history snapshot.

# JEDEC Standard No. 220G
Page 246

## 11.3.27.3.1 Error History Directory (cont'd)

### Table 11.52 — EHS_SOURCE Field

| Code | Description |
|------|-------------|
| 00b | The error history snapshot was created by the device server and was not created due to processing a READ BUFFER command. |
| 01b | Not used in UFS |
| 10b | Not used in UFS |
| 11b | Reserved |

• The error history directory list contains an error history directory entry for each supported buffer ID in the range of 10h to FFh. The first entry shall be for buffer ID 10h and the entries shall be in order of ascending buffer IDs. The supported buffer IDs are not required to be contiguous. There shall not be any entries for buffer IDs greater than or equal to F0h.

### Table 11.53 — Error History Directory Entry

| Byte | Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|-----|---|---|---|---|---|---|---|---|
| 0 |     |   |   | SUPPORTED BUFFER ID |   |   |   |   |   |
| 1 |     |   |   |   |   |   |   |   |   |
| 2 |     |   |   | Reserved |   |   |   |   |   |
| 3 |     |   |   |   |   |   |   |   |   |
| 4 | (MSB) |   |   |   |   |   |   |   |   |
| ... |     |   | MAXIMUM AVAILABLE LENGTH |   |   |   |   |   |
| 7 |     |   |   |   |   |   |   |   | (LSB) |

• The SUPPORTED BUFFER ID field indicates the error history buffer ID associated with this entry.

• The MAXIMUM AVAILABLE LENGTH field indicates the maximum number of data bytes contained in the buffer indicated by the SUPPORTED BUFFER ID field. The actual number of bytes available for transfer may be smaller.

# JEDEC Standard No. 220G
## Page 247

### 11.3.27.3.2 Retrieving error history with the READ BUFFER command

In UFS standard, Error History Snapshot is not supported. The returned error history may be real-time contents or may be the contents captured at a vendor specific point in time.

Error history retrieve operation uses the following mechanism.

1) Device failure is detected. Host may need to reset UFS device and re-establish the link before retrieving the error history if the device is not responding after the failure.

2) Host retrieves the error history directory by sending a READ BUFFER command by specifying: MODE = 1Ch, BUFFER ID = 00h, BUFFER OFFSET = zero, and ALLOCATION LENGTH set to at least 2088 (i.e., large enough to transfer the complete error history directory).

3) Host retrieves the error history. For each buffer ID indicated in the error history directory in the range of 10h to EFh, the host sends one or more READ BUFFER commands with BUFFER ID set to the error history data buffer ID. During the error history retrieval, it is recommended that host does not send any normal request other than READ BUFFER command because the other normal request could change the error history information which is being retrieved.

### 11.3.27.4 Read Buffer Command Status Response

• Status response will be sent in a single RESPONSE UPIU

• If all requested data is successfully read and transferred, the READ BUFFER command will terminate with a STATUS response of GOOD

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned

• Failure can occur for numerous reasons. When the READ BUFFER command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, see [SPC] for further details.

    ○ ILLEGAL REQUEST (range or CDB errors)
    
    ○ MEDIUM ERROR (medium failure, ECC, etc.)
    
    ○ HARDWARE ERROR (hardware failure)
    
    ○ UNIT ATTENTION (reset, power-on, etc.)
    
    ○ etc.