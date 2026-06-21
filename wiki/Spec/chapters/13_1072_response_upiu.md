# JEDEC Standard No. 220G
Page 85

## 10.7.1.1 Basic header (cont'd)

### e) CDB

The CDB fields contain the Command Descriptor Block. This area is an array of 16 bytes that will contain a standard Command Descriptor Block as defined by one of the supported UFS Command Set Types. For SCSI commands, specifications such as [SPC] can be referenced. Up to a 16 byte CDB can be utilized. The CDB size is implicitly indicated by the group bits of the operation code field in CDB[0] for SCSI, which is the SCSI command operation code. If the CDB size is lower than 16 bytes the unused COMMAND UPIU bytes are defined as reserved. For other commands, the CDB size is dependent upon the command opcode.

### f) IID

This field is the LSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2, for details.

### g) EXT_IID

This field is the MSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2, Basic Header Format, for details.

### h) Command Set Type

The Command Set Type field will specify an enumerated value that indicates which particular command set is used to define the command bytes in the CDB fields. See Command Set Type description for details.

## 10.7.2 RESPONSE UPIU

The RESPONSE UPIU contains the basic UPIU header plus additional information indicating the command and device level status resulting from the successful or failed execution of a command. The Target will generate this UPIU and send it to the Initiator device after it has completed the requested task.

Before terminating a command which requires Data-Out data transfer and before sending the RESPONSE UPIU, the Target device shall wait until it receives all DATA OUT UPIUs related to any outstanding READY TO TRANSFER UPIUs. Also, the Target device should stop sending READY TO TRANSFER UPIUs for the command which requires Data-Out data transfer and to be terminated.

# JEDEC Standard No. 220G
Page 86

## 10.7.2 RESPONSE UPIU (cont'd)

### Table 10.15 — RESPONSE UPIU

| RESPONSE UPIU |  |  |  |
|---|---|---|---|
| 0 | 1 | 2 | 3 |
| xx10 0001b | Flags | LUN | Task Tag |
| 4 | 5 | 6 | 7 |
| IID | Command Set Type | EXT_IID | Reserved | Response | Status |
| 8 | 9 | 10 | (MSB) | 11 | (LSB) |
| Total EHS Length | Device Information | Data Segment Length |  |
| 12 | (MSB) | 13 | 14 | 15 | (LSB) |
|  | Residual Transfer Count |  |  |
| 16 | 17 | 18 | 19 |
|  | Reserved |  |  |
| 20 | 21 | 22 | 23 |
|  | Reserved |  |  |
| 24 | 25 | 26 | 27 |
|  | Reserved |  |  |
| 28 | 29 | 30 | 31 |
|  | Reserved |  |  |
| i | i+1 | i+2 | i+3 |
|  | Extra Header Segment (EHS) 1 |  |  |
|  | ... |  |  |
| j | j+1 | j+2 | j+3 |
|  | Extra Header Segment (EHS) N |  |  |
|  | Header E2ECRC (omit if HD=0) |  |  |
| k | (MSB) | k+1 | (LSB) | k+2 | k+3 |
|  | Sense Data Length | Sense Data[0] | Sense Data[1] |
| ... | ... | ... | ... |
| k+16 | k+17 | k+18 | k+19 |
| Sense Data[14] | Sense Data[15] | Sense Data[16] | Sense Data[17] |
|  | Data E2ECRC (omit if DD=0) |  |  |

**NOTE 1** k = 32 + (32 x Total EHS Length) if HD = 0.

# 10.7.2.1 Basic Header

The first 12 bytes of the RESPONSE UPIU contain the Basic Header as described in 10.6.2, Basic Header Format. Specific details are as follows:

## a) Transaction Type

A type code value of xx10 0001b indicates a RESPONSE UPIU.

## b) Flags

Table 10.16 describes the flags used in RESPONSE UPIU.

### Table 10.16 — Flags Definition for RESPONSE UPIU

| Flag | Description |
|------|-------------|
| Flags.O | The Flags.O flag will be set to '1' to indicate that a data overflow occurred during the task execution: the Target device has more data bytes to transfer than the Initiator device requested.<br><br>The Residual Transfer Count field will indicate the number of available bytes not transferred from the Target device to the Initiator device or vice versa.<br><br>The Residual Transfer Count will be set to the value difference of the total number of bytes available to be transferred and the Expected Data Transfer Length value received in the COMMAND UPIU. See "j) Residual Transfer Count" for further explanation. |
| Flags.U | The Flags.U flag will be set to '1' to indicate that a data underflow occurred during the task execution: the Target device has less data bytes to transfer than the Initiator device requested.<br><br>The Residual Transfer Count field will indicate the number of bytes that were not transferred from the Target device to the Initiator device or vice versa.<br><br>The Residual Transfer Count will be set to the value difference of the Expected Data Transfer Length value received in the COMMAND UPIU and the actual number of bytes transferred. See "j) Residual Transfer Count" for further explanation. |
| Flags.D | The .D flag will be set to '1' to indicate that a UTP Data Out Mismatch error occurred during the task execution: the data buffer offset and/or the data transfer count parameter in the Data Out UPIU doesn't match the corresponding parameters in the RTT request. See 10.7.13 for further explanation. |
| NOTE | The bit assignment of the Flags field is shown in Table 10.6. |

## c) IID

This field is the LSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2 for details.

## d) EXT_IID

This field is the MSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2, Basic Header Format, for details.

## e) Command Set Type

The Command Set Type field will specify an enumerated value that indicates which particular command set is used to define the command bytes in the CDB fields. See 10.6.2.

---
JEDEC Standard No. 220G  
Page 87

# JEDEC Standard No. 220G
Page 88

## 10.7.2.1 Basic Header (cont'd)

### f) Response

The Response field will contain the UFS response that indicates the UFS defined overall success or failure of the series of Command, Data and RESPONSE UPIU's that make up the execution of a task. See 10.6.2, Basic Header Format, for details.

### g) Status

The Status field contains the command set specific status for a specific command issued by the Initiator device. The Status field is command set specific. The Command Set Type field will indicate with which command set the status is associated. Specific command sets may or may not define detailed extended status indicated as Sense Data. If the command requires extended status, that information will be stored in the Sense Data field.

#### 1) SCSI Command Set Status

When the Command Set Type field indicates SCSI Command Set the Status field will contain the standard SPC defined SCSI status value. Possible values are listed in the Table 10.17. See the [SPC] or [SAM] for detailed definition of the status conditions.

A GOOD status indicates successful SCSI completion and therefore no Sense Data will be returned. A status of CHECK CONDITION requires that the Data Segment contain Sense Data for the failed command.

Other status values may or may not return Sense Data. In this case a non-zero value in the Data Segment Length field indicates that this UPIU contains Sense Data in the Data Segment area.

'M' indicates mandatory implementation of this field and the value specified if fixed. 'O' indicates that the support of this field is optional; if it is not supported then a value of zero should be inserted in the field otherwise the value will be indicated as described. n/a indicates "not applicable" to UFS.

# JEDEC Standard No. 220G
## Page 89

### 10.7.2.1 Basic Header (cont'd)

#### Table 10.17 — SCSI Status Values

| Opcode | Response Description | Use |
|--------|---------------------|-----|
| 00h | GOOD | M |
| 02h | CHECK CONDITION | M |
| 04h | CONDITION MET | n/a |
| 08h | BUSY | M |
| 18h | RESERVATION CONFLICT | O |
| 28h | TASK SET FULL | M |
| 30h | ACA ACTIVE | n/a |
| 40h | TASK ABORTED | n/a |

**GOOD** - This status indicates that the device has completed the command without error.

**CHECK CONDITION** - This status indicates that the device has completed the command with error or other actions are required to process the result. Valid Sense Data for the last command processed will be returned within the response UPIU when this status occurs.

**CONDITION MET** - Not used for UFS.

**BUSY** - This status indicates that the logical unit is busy. When the logical unit is unable to accept a command this status will be returned. Issuing the command at a later time is the standard recovery action.

**RESERVATION CONFLICT** - This status is returned when execution of the command will result in a conflict of an existing reservation. UFS may support reserving areas of the device depending upon the device type and capabilities.

**TASK SET FULL** - This status is returned when the logical unit cannot process the command due to a lack of resources such as task queue being full or memory needed for command execution is temporarily unavailable.

**ACA ACTIVE** - This status is returned when an ACA condition exists. See [SAM] for further definition.

**TASK ABORTED** - This status shall be returned when a command is aborted by a command or task management function on another I_T nexus and the Control mode page TAS bit is set to one. Since in UFS TAS bit is zero TASK ABORTED status codes will never occur.

# JEDEC Standard No. 220G
## Page 90

### 10.7.2.1 Basic Header (cont'd)

#### h) Device Information

The Device Information field provides information at device level not necessarily related with the logical unit executing the command.

In general, the information is about events that have an evolution much slower than the regular commands, and for which the host response latency is not critical. The use of this field avoids the execution of a continuous polling on some UFS attributes.

Bit[0] and bit[5:2] of the Device Information field are defined, and bit[1] is reserved for HPB (Host Performance Booster) Extension Standard. All the others are reserved and shall be set to zero.

| Bit | Name | Description |
|-----|------|-------------|
| bit[0] | EVENT_ALERT | Exception Event Alert<br/>0b: All exception sources not active<br/>1b: At least one exception source is active |
| bit[1] | Reserved | Reserved for HPB (Host Performance Booster) Extension Standard |
| bit[5:2] | FAST_RECOVERY_NEEDED | Fast recovery request<br/>Device requests host action after listed delay:<br/>0h: No reset requested.<br/>1h: HW reset with no delay.<br/>2h: HW reset after a 1 second delay.<br/>3h: HW reset after a 2 second delay.<br/>4h: HW reset after a 3 second delay.<br/>5h: HW reset after a 4 second delay.<br/>6h: HW reset after a 5 second delay.<br/>7h: HW reset after a 6 second delay.<br/>8h: HW reset after a 7 second delay.<br/>9h: HW reset after a 8 second delay.<br/>Ah: HW reset after a 9 second delay.<br/>Bh: HW reset after a 10 second delay.<br/>Ch: HW reset after a 11 second delay.<br/>Dh: HW reset after a 12 second delay.<br/>Eh: HW reset after a 13 second delay.<br/>Fh: HW reset after a 14 second delay. |
| Others | Reserved | |

The exception sources include: background operations, dynamic capacity, system data pool, etc. See 13.4.12, Exception Events Mechanism, for details.

# JEDEC Standard No. 220G
Page 91

## 10.7.2.1 Basic Header (cont'd)

### i) Data Segment Length

The Data Segment Length field will contain the number of valid bytes in the Data Segment.

In the RESPONSE UPIU the Data Segment will contain the Sense Data bytes and the Sense Data Length field.

When this field contains zero it indicates that there is no Data Segment area in the UPIU and therefore no Sense Data is returned.

This version of the standard, when the Command Set Type field indicates SCSI Command Set, the number of Sense Data bytes is 18, therefore this field will contain a value of 20 (18 bytes of Sense Data + 2 bytes for Sense Data Length = 20 bytes).

As stated previously, the Data Segment field size is located on a 32-bit (DWORD) boundary. The Data Segment Length field indicates the number of "valid" bytes in the Data Segment area and therefore its value may not be an integer multiple of four.

### j) Residual Transfer Count

This field is valid only if one of the Flags.U or Flags.O fields are set to '1', otherwise this field will contain zero.

When the Flags.O field is set to '1' then this field indicates the number of bytes that were not transferred from/to the Initiator device because the Expected Data Transfer Length field contained a value that was lower than the Target device expected to transfer. In other words, the Target device has more bytes to receive/send to complete the request but the Initiator device is not expecting more than the amount indicated in the Expected Data Transfer Length. For example, the Initiator device may intentionally request less bytes than it knows the Target device has available to transfer, because it only needs the first N bytes.

When the Flags.U field is set to '1' then this field indicates the number of bytes that were not transferred from/to the Initiator because the Expected Data Transfer Length field contained a value that was higher than the available data bytes. In other words, the Target device has less bytes to receive/send than the Initiator is requesting to transfer. For example, the Initiator device may intentionally request more bytes than the Target device has to transfer when it does not know how many bytes the Target device actually has and it asks for the max or more than possible.

**Table 10.18 — Flags and Residual Count Relationship**

| Flags.O | Flags.U | Residual Transfer Count | Description |
|---------|---------|------------------------|-------------|
| 0 | 0 | 0 | Expected Data Length bytes transferred |
| 1 | 0 | N | Target device expected to send N more bytes to Initiator device |
| 0 | 1 | N | Initiator device expected to receive N more bytes from Target device |
| 1 | 1 | X | Illegal condition |

# JEDEC Standard No. 220G
Page 92

## 10.7.2.1 Basic Header (cont'd)

### k) Sense Data Fields

The Sense Data fields will contain additional information on error condition.

For SCSI command they will provide a copy of first 18 sense data bytes as defined for the fixed format sense data, which corresponds to Response Code value of 70h. See the following subsection for further details.

A successfully executed command will not normally need to return Sense Data, therefore in this case the Data Segment may be empty and the Data Segment Length may have a zero value.

The Sense Data Fields will be padded with zeros to place the data on the next nearest 32-bit boundary if the length of valid Sense Data fields plus two is not a multiple of 32-bit.

### l) SCSI Sense Data Fields

The Sense Data Fields will contain standard 18 byte SPC defined sense data when using format for a Response Code value of 70h. See [SPC] for further information.

Sense Data consists of three levels of error codes, each in increasing detail. The purpose is to provide the application client a means to determine the cause of an error or exceptional condition at various levels of detail. The Sense Key provides a general category of what error or exceptional condition occurred and has caused the current command from successfully completing. Further and finer error detail is provided in the Additional Sense Code field (ASC). The Additional Sense Code Qualifier (ASCQ) field refines the error information even further. It is required to implement the Sense Key value when indicating an error or exceptional condition. It is not required to implement the ASC or ASCQ values not described in this document; a value of zero can be placed in these fields if the implementation does not require more refined error detail.

All SCSI commands that terminate in error or exceptional condition will automatically return Sense Data in the RESPONSE UPIU, relieving the host from issuing a subsequent REQUEST SENSE command to retrieve the additional sense error information.

# JEDEC Standard No. 220G
Page 93

## 10.7.2.1 Basic Header (cont'd)

### m) Sense Data Length

The Sense Data Length field indicates the number of valid Sense Data bytes that follow. The Sense Data Length plus two may be less than the number of bytes contained in the Data Segment area, if padding bytes have been added to reach 32-bit boundary.

A successfully executed command will not normally need to return Sense Data, therefore in this case the Data Segment area may be empty and the Data Segment Length may have a zero value.

A command that terminated in error or an exception may or may not return Sense Data. If the Sense Data Length indicates a value of zero, then that error condition did not return Sense Data. A zero value in the Data Segment Length also indicates that no Sense Data was returned. Otherwise, the Sense Data Length will contain a value that indicates the number of additional bytes of Sense Data information.

### n) SCSI Sense Data Length

The Sense Data Length field shall indicate a value of 18 when using the SCSI Command Set.

### o) Sense Data Format

Table 10.19 describes the sense data structure that gives detailed error information about the previously executed SCSI command. Eighteen bytes are returned and the Additional Sense Length field is set to a value of ten.

'M' indicates mandatory implementation of this field and the value specified if fixed. 'O' indicates that the support of this field is optional; if it is not supported then a value of zero should be inserted in the field otherwise the value will be indicated as described.

# JEDEC Standard No. 220G
Page 94

## 10.7.2.1 Basic Header (cont'd)

### Table 10.19 — SCSI Fixed Format Sense Data

| Byte | Bits | Name | Description | Use |
|------|------|------|-------------|-----|
| 0 | 7:7 | VALID | A VALID bit set to one indicates that the INFORMATION field contains valid data. Default value = 0b | O |
| | 6:0 | RESPONSE CODE | Value of 70h for fixed format sense data response | M |
| 1 | 7:0 | Obsolete | Not used Default value = 00h | M |
| | 7:7 | FILEMARK | File mark found This bit is reserved for UFS. Default value = 0b | M |
| | 6:6 | EOM | End of media detected This bit is reserved for UFS. Default value = 0b | M |
| 2 | 5:5 | ILI | Incorrect length detected This bit is reserved for UFS. Default value = 0b | M |
| | 4:4 | Reserved | Default value = 0b | M |
| | 3:0 | SENSE KEY | SENSE KEY code is the general SCSI error code for previous command (see Table 10.20) | M |
| 3:6 | 7:0 | INFORMATION | Sense Information | O |
| 7 | 7:0 | ADDITIONAL SENSE LENGTH | Length in bytes of additional sense information Value = 10 (0Ah) indicating 10 additional bytes (bytes 8 through 17) | M |
| 8:11 | 7:0 | COMMAND-SPECIFIC INFORMATION | Command Specific Information This field is reserved for UFS. Default value = 00h | M |
| 12 | 7:0 | ASC | ADDITIONAL SENSE CODE is an additional, more specific error code (see SCSI specs) | M |
| 13 | 7:0 | ASCQ | ADDITIONAL SENSE CODE QUALIFIER qualifies the Additional Sense Code (see SCSI specs) | M |
| 14 | 7:0 | FRUC | FIELD REPLACEABLE UNIT CODE Default value = 00h | M |
| | 7:7 | SKSV | SKSV bit indicates if the SENSE KEY SPECIFIC field contains valid information. This bit is reserved for UFS. Default value = 0b | M |
| 15 | 6:0 | SENSE KEY SPECIFIC | Sense key specific information This field is reserved for UFS. Default value = 00 00 00h | M |
| 16:17 | 7:0 | SENSE KEY SPECIFIC | | M |

# JEDEC Standard No. 220G
Page 95

## 10.7.2.1 Basic Header (cont'd)

The SENSE KEY is used for normal error handling during operation.

The ADDITIONAL SENSE CODE (ASC) and the ADDITIONAL SENSE CODE QUALIFIER (ASCQ) are mainly used for detailed diagnostic and logging (post-mortem) information. If the device server does not have further information related to the error or exception condition, these fields shall be set to zero. Generally, except for a certain few, they're not mandatory and they may be set to zero, which means no additional information provided. See [SPC] for a list of additional sense codes and additional sense code qualifiers.

### p) Sense Key

The Sense Key value provides a means to categorize errors and exceptional conditions. The Sense Key indicates a particular type of error. The Additional Sense Code and Additional Sense Code Qualifier can be used to further detail and describe the condition that the Sense Key indicates. Sense Keys are specific to the action performed by a particular command.

# JEDEC Standard No. 220G
Page 96

## 10.7.2.1 Basic Header (cont'd)

### Table 10.20 — Sense Key

| Value | Description |
|-------|-------------|
| 00h | **NO SENSE** – Indicates that there is no specific sense key information to be reported. This would be the result of a successfully executed command. |
| 01h | **RECOVERED ERROR** – Indicates that the last command completed successfully after error recovery actions were performed by the device server. Further details may be determined by examining the additional sense bytes (ASC and ASCQ fields). |
| 02h | **NOT READY** – Indicates that the logical unit addressed cannot be accessed at this time. |
| 03h | **MEDIUM ERROR** – Indicates that the last command was unsuccessful due to a non-recoverable error condition due to a flaw in the media or failed error recovery. |
| 04h | **HARDWARE ERROR** – Indicates that the the device server detected a non-recoverable hardware error. |
| 05h | **ILLEGAL REQUEST** – Indicates that there was an illegal parameter value in a command descriptor block or within additional parameter data supplied with some commands. If the device server detects an invalid parameter in the command descriptor block then it shall terminate the command without altering the media. |
| 06h | **UNIT ATTENTION** – Indicates that the unit has been reset or unexpectedly powered-on or that removable media has changed. |
| 07h | **DATA PROTECT** – Indicates that a command that reads or writes the medium was attempted on a block that is protected from this operation. The read or write operation shall not be performed. |
| 08h | **BLANK CHECK** - Indicates that blank or unformatted media was encountered while reading or writing. |
| 09h | **VENDOR SPECIFIC** – This Sense Key is available for reporting vendor specific error or exceptional conditions. |
| 0Ah | **COPY ABORTED** – Not applicable for UFS device. Reserved |
| 0Bh | **ABORTED COMMAND** – Indicates that the device server aborted the execution of the command. The application client may be able to recover by retrying the command. |
| 0Ch | Reserved |
| 0Dh | **VOLUME OVERFLOW** - Indicates that a buffered peripheral device has reached the end-of-partition and data may remain in the buffer that has not been written to the medium. |
| 0Eh | **MISCOMPARE** – Indicates that the source data did not match the data read from the media. |
| 0Fh | **RESERVED** |

**NOTE 1** See [SAM] for further details.