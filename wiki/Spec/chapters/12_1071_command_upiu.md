# JEDEC Standard No. 220G
Page 82

## 10.7 UFS Protocol Information Units

This sub-clause provides the details of each UFS Protocol Information Unit.

### 10.7.1 COMMAND UPIU

The COMMAND UPIU contains the basic UPIU header plus additional information needed to specify a command. The Initiator device will generate this UPIU and send it to a Target device to request a SCSI command service to be performed by the Target.

**Table 10.13 — COMMAND UPIU**

| | | | |
|---|---|---|---|
| **COMMAND UPIU** | | | |
| **0** | **1** | **2** | **3** |
| xx00 0001b | Flags | LUN | Task Tag |
| **4** | **5** | **6** | **7** |
| IID | Command Set Type | Reserved | Reserved | EXT_IID | Reserved |
| **8** | **9** | **10** | **11** |
| Total EHS Length | Reserved | (MSB) Data Segment Length (0000h) | (LSB) |
| **12** | **13** | **14** | **15** |
| (MSB) | | Expected Data Transfer Length | (LSB) |
| **16** | **17** | **18** | **19** |
| CDB[0] | CDB[1] | CDB[2] | CDB[3] |
| **20** | **21** | **22** | **23** |
| CDB[4] | CDB[5] | CDB[6] | CDB[7] |
| **24** | **25** | **26** | **27** |
| CDB[8] | CDB[9] | CDB[10] | CDB[11] |
| **28** | **29** | **30** | **31** |
| CDB[12] | CDB[13] | CDB[14] | CDB[15] |
| **i** | **i+1** | **i+2** | **i+3** |
| | | Extra Header Segment (EHS) 1 | |
| | | ... | |
| **j** | **j+1** | **j+2** | **j+3** |
| | | Extra Header Segment (EHS) N | |
| | | Header E2ECRC (omit if HD=0) | |

# JEDEC Standard No. 220G
## Page 83

### 10.7.1.1 Basic Header

The first 12 bytes of the COMMAND UPIU contain the Basic Header as described in 10.6.2, Basic Header Format. Specific details are as follows:

#### a) Transaction Type

A type code value of xx00 001b indicates a COMMAND UPIU.

#### b) Flags

Table 10.14 describes the flags used in COMMAND UPIU.

**Table 10.14 — Flags definition for COMMAND UPIU**

| Flag | Description |
|------|-------------|
| Flags.R | A value of '1' in the .R flag indicates that the command requires a data transfer (incoming data) from Target device to Initiator device. If .R is set to '1' then .W shall be set to '0'. If .R and .W are set to '0' then no data transfer is required for this command and the Expected Data Transfer Length field is ignored. |
| Flags.W | A value of '1' in the .W flag indicates that the command requires a data transfer (outgoing data) from Initiator device to Target device. If .W is set to '1' then .R shall be set to '0'. If .W and .R are set to '0' then no data transfer is required for this command and the Expected Data Transfer Length field is ignored. |
| Flags.ATTR | The .ATTR field contains the task attribute value as defined by [SAM].<br><br>**ATTR Definition**<br><br>\| Task Attribute \| Bit 1 \| Bit 0 \|<br>\|---------------\|------\|------\|<br>\| Simple \| 0 \| 0 \|<br>\| Ordered \| 0 \| 1 \|<br>\| Head of Queue \| 1 \| 0 \|<br>\| ACA (Not Used) \| 1 \| 1 \|<br><br>The relative order of execution between Head of Queue commands is left for implementation. |
| Flags.CP | The .CP field indicates the Command Priority; see [SAM] for details. In UFS, the .CP field supports only two values whereas [SAM] allows a larger range.<br><br>This 1-bit field specifies the relative scheduling importance of a command having a Simple task attribute in relation to other commands having Simple task attributes already in the task set. If the command has a task attribute other than Simple then this field has no meaning.<br><br>A task manager may use command priority to determine an ordering to process commands with the Simple task attribute within the task set.<br><br>A value of "1" indicates high priority. A value of "0" indicates no priority. |

**NOTE** The bit assignment of the Flags field is shown in Table 10.6.

# JEDEC Standard No. 220G
## Page 84

### 10.7.1.1 Basic header (cont'd)

**c) Data Segment Length**

The Data Segment Length field shall contain zero as there is no Data Segment in this UPIU.

**d) Expected Data Transfer Length**

The Expected Data Transfer Length field contains a value that represents the number of bytes to be transferred that are required to complete the SCSI command request as indicated in the CDB (e.g., TRANSFER LENGTH, ALLOCATION LENGTH, PARAMETER LIST LENGTH, etc.). Data may be transferred from the Initiator device to the Target device or from the Target device to the Initiator device. This field is valid only if one of the Flags.W or Flags.R bits are set to '1'.

For a data transfer from the Initiator device to the Target device, the .W flag shall be set to '1' and the .R flag shall be set to '0'. The value in the Expected Data Transfer Length field represents the size of the data in the number of bytes, excluding retransmits, that the Initiator device expects to send to the Target device. Upon completion of the transfer, the target device informs the initiator how many bytes have been processed (excluding retransmits) via the residual count.

For a data transfer from the Target device to the Initiator device, the .R flag shall be set to '1' and the .W flag shall be set to '0'. The value in the Expected Data Transfer Length field represents the size of the data in the number of bytes, excluding retransmits, that the Initiator device expects to receive from the Target device. Upon completion of the transfer, the target device informs the initiator how many bytes have been processed (excluding retransmits) via the residual count.

When the COMMAND UPIU encodes a SCSI WRITE or SCSI READ command (specifically WRITE (6), READ (6), WRITE (10), READ (10), WRITE (16), or READ (16)), the value of this field shall be the product of the Logical Block Size (bLogicalBlockSize) and the TRANSFER LENGTH field of the CDB.

This model requires that the Initiator device will allocate sufficient buffer space to receive the full size of the data requested by a command that requires a Data In operation. That size measured in bytes shall be the value in Expected Data Transfer Length field. This requirement is important in order to realize the full throughput of the Data In phase without the use of additional handshaking UPIU's.

The RESPONSE UPIU is used to complete the requested task initiated by the COMMAND UPIU.

**NOTE:** Before the RESPONSE UPIU is sent to the host, some portion or all data may be retransmitted to update the data sent by previous DATA IN UPIUs or DATA OUT UPIUs if the out of order feature for DATA IN UPIU or DATA OUT UPIU is enabled (bOutOf OrderDataEn = 01h, 02h or 03h). See READY TO TRANSFER UPIU, DATA OUT UPIU, and DATA IN UPIU for more details.

The Initiator device may request a Data Out size larger than the size of the receive buffer in the Target device. In this case, the Target device will pace the DATA OUT UPIU's by sending READY TO TRANSFER UPIUs as needed. The Initiator device will not send a DATA OUT UPIU before it receives a READY TO TRANSFER UPIU.