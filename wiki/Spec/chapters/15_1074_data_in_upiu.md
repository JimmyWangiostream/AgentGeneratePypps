# JEDEC Standard No. 220G
Page 101

## 10.7.4 DATA IN UPIU

The DATA IN UPIU contains the basic UPIU header plus additional information needed to manage the data in transfer. Data in flows from Target device to Initiator device (READ). The DATA IN UPIU will usually contain a data segment. It is possible to have a null DATA IN UPIU; the Data Segment is empty and Data Segment Length is 0.

### Table 10.23 —DATA IN UPIU

| **DATA IN UPIU** | | | |
|---|---|---|---|
| **0** | **1** | **2** | **3** |
| xx10 0010b | Flags | LUN | Task Tag |
| **4** | **5** | **6** | **7** |
| IID | Reserved | EXT_IID | Reserved | Reserved | Reserved |
| **8** | **9** | **10** | **11** |
| Total EHS Length (00h) | Reserved | (MSB) | (LSB) |
| | | Data Segment Length | |
| **12** | **13** | **14** | **15** |
| (MSB) | | | (LSB) |
| | Data Buffer Offset | | |
| **16** | **17** | **18** | **19** |
| (MSB) | | | (LSB) |
| | Data Transfer Count | | |
| **20** | **21** | **22** | **23** |
| Reserved | HintControl | HintEXT_IID | HintIID | HintLUN | HintTaskTag |
| **24** | **25** | **26** | **27** |
| | | Hint Data Buffer Offset | |
| **28** | **29** | **30** | **31** |
| | | Hint Data Count | |
| | | Header E2ECRC (omit if HD=0) | |
| **k** | **k+1** | **k+2** | **k+3** |
| Data[0] | Data[1] | Data[2] | Data[3] |
| ... | ... | ... | ... |
| **k+ Length-4** | **k+ Length-3** | **k+ Length-2** | **k+ Length-1** |
| Data[Length -4] | Data[Length -3] | Data[Length -2] | Data[Length -1] |
| | | Data E2ECRC (omit if DD=0) | |

**NOTE 1** k = 32 if HD = 0.

# JEDEC Standard No. 220G
## Page 102

### 10.7.4.1 Basic Header

The first 12 bytes of the DATA IN UPIU contain the Basic Header as described in 10.6.2, Basic Header Format. Specific details are as follows:

**a) Transaction Type**

A type code value of xx10 0010b indicates a DATA IN UPIU.

**b) Flags**

Table 10.24 describes the flags used in DATA IN UPIU.

#### Table 10.24 — Flags Definition for DATA IN UPIU

| Flag | Description |
|------|-------------|
| Flags.T | A value of '1' in Flags.T indicates that all data in this UPIU shall be retransmitted data. See "f) Data Buffer Offset" for further explanation. |

**NOTE** The bit assignment of the Flags field is shown in Table 10.6.

**c) IID**

This field is the LSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2 for details.

**d) EXT_IID**

This field is the MSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2 for details.

**e) Data Segment Length**

The Data Segment Length shall indicate the number of valid bytes within the Data Segment area, and it shall not include the number of padding bytes (if present).

# JEDEC Standard No. 220G
## Page 103

### 10.7.4.1 Basic Header (cont'd)

**f) Data Buffer Offset**

The Data Buffer Offset field contains the offset of this UPIU data payload within the complete data transfer area. The sum of the Data Buffer Offset and the Data Segment Length shall not exceed the Expected Data Transfer Length that was indicated in the COMMAND UPIU.

This field permits out of order sequencing of the DATA IN UPIU packets. Therefore the order of the DATA IN UPIU packets do not have to be sequential.

To retransmit data for a task, the device shall set Data Buffer Offset appropriately and shall set Flags.T. All data in this UPIU shall be retransmitted data.

NOTE: A UFS device may set the Data Buffer Offset to retransmit only if out of order sequencing of DATA IN UPIU packets is enabled (bOutOfOrderDataEn = 01h or bOutOfOrderDataEn = 02h).

When the DATA IN UPIU is a part of a SCSI READ transaction [i.e., a transaction which started with a READ (6), a READ (10), or a READ (16) command], the value of this field shall be equal to an integer multiple of the Logical Block Size (bLogicalBlockSize).

**g) Data Transfer Count**

This field indicates the number of bytes that the Target device has placed in the UPIU Data Segment, for transfer back to the Initiator device. This value is the number of valid bytes that are contained within the Data Segment of this UPIU. The maximum number of bytes that can be transferred within a single DATA IN UPIU packet is 65535 bytes.

When the DATA IN UPIU is a part of a SCSI READ transaction [i.e., a transaction which started with a READ (6), a READ (10), or a READ (16) command], the value of this field shall be equal to an integer multiple of the Logical Block Size (bLogicalBlockSize).

This field and the Data Segment Length field of the UPIU shall contain the same value.

# JEDEC Standard No. 220G
## Page 104

### 10.7.4.1 Basic Header (cont'd)

#### h) Data Segment

This is the Data Segment area that contains the data payload.

The maximum data payload size that can be transferred within a single DATA IN UPIU packet is 65535 bytes.

The Data Segment area always starts on a 32-bit (DWORD) boundary. The Data Segment area shall be entirely filled with data payload to a 32-bit (DWORD) boundary unless the UPIU is the one that transmits the last data portion. In this case, if necessary, the Data Segment area shall be padded out to the next nearest 32-bit boundary.

When the DATA IN UPIU is a part of a SCSI READ transaction [i.e., a transaction which started with a READ (6), a READ (10), or a READ (16) command], the Data Segment area shall contain an integer number of logical blocks.

**NOTE** For out of order DATA IN UPIUs, the final data portion may not be transmitted by the last UPIU.

#### i) HintControl

Bit0: This field indicates the validity of the Hint fields provided in the DATA IN UPIU (HintIID, HintLUN, HintTaskTag, Hint Data Buffer Offset, Hint Data Count). When this field is set to 0b, the Hint fields are not valid and expected to be ignored by the host controller. When this field is set to 1b, the Hint fields are valid.

When the feature is not supported or is disabled (bDataOrdering = 00h or bOutOfOrderDataEn = 00h), or the Hint fields (HintTaskTag, etc…) do not refer to a READ(6) / READ (10) / READ (16) / HPB Read command - HintControl shall be set to 0x0 and hint information is not provided.

Other bits: reserved.

#### j) HintIID [3:0]

This field indicates the IID of DATA IN UPIUs that the device will transfer. This field is valid only when HintControl is set to 1b. HintIID field may be different than IID field.

#### k) HintEXT_IID [7:4]

This field indicates the EXT_IID of DATA IN UPIUs that the device will transfer. This field is valid only when HintControl is set to 1b. HintEXT_IID field may be different than EXT_IID field.

#### l) HintLUN

This field indicates the LUN of DATA IN UPIUs that the device will transfer. This field is valid only when HintControl is set to 1b. HintLUN field may be different than LUN field.

#### m) HintTaskTag

This field indicates the Task Tag of DATA IN UPIUs that the device will transfer. This field is valid only when HintControl is set to 1b. HintTaskTag field may be different than TaskTag field.

#### n) Hint Data Buffer Offset

This field indicates the Data Buffer Offset in a DATA IN UPIUs that the device will transfer. This field is valid only when HintControl is set to 1b.

# JEDEC Standard No. 220G
Page 105

## 10.7.4.1 Basic Header (cont'd)

### o) Hint Data Count

This field indicates the number of 4KB that the Target device is expected to transfer to the Initiator starting from Hint Data Buffer Offset field. The value 0 indicates 4KB data. The value 1 indicates 8KB data, and so on.

The device may interleave DATA IN UPIUs pertaining to all hints provided by the device. This field is valid only when HintControl is set to 1b.

### p) Data In Transfer Examples

Figure 10.3 shows an example of data transfer from the Target device to the Initiator device. In particular, during the command processing 577-byte data is sent to the Initiator device. The data transfer is done in sequence: at the beginning the first portion, then the middle portion and finally the last portion.

NOTE The last DATA IN UPIU delivers the last portion of the data. The Data Segment in this UPIU has 65 bytes of valid data and three pad bytes. The Data Segment in the other UPIUs is fully filled (no pad bytes).

[**Figure 10.3 — Data In Transfer Example**

This is a sequence diagram showing data transfer between Host and Device:

- Host sends COMMAND UPIU to Device with "Expected Data Transfer Length = 241h (577 byte)"

- The 577-byte data is divided into three portions:
  - **First portion** (000h): DATA IN UPIU with Data Segment Length = 100h, Data Buffer Offset = 0h, Data Transfer Count = 100h
  - **Middle portion** (100h-1FFh): DATA IN UPIU with Data Segment Length = 100h, Data Buffer Offset = 100h, Data Transfer Count = 100h  
  - **Last portion** (200h-241h): DATA IN UPIU with Data Segment Length = 41h, Data Buffer Offset = 200h, Data Transfer Count = 41h (includes 65 bytes valid data + 3 pad bytes)

- Device sends RESPONSE UPIU back to Host

The diagram shows the sequential transfer of data portions from Device to Host, with each portion labeled as "first portion", "middle portion", and "last portion" respectively.]

# JEDEC Standard No. 220G
## Page 106

### 10.7.4.1 Basic Header (cont'd)

Figure 10.4 shows and example of data transfer for a READ Command when some portion of the data sent using a previous DATA IN UPIU needs to be updated before sending the RESPONSE UPIU. In this example, the device sends a DATA IN UPIU with an appropriate Data Buffer Offset to update that data.

[**Figure 10.4 — DATA IN UPIU with Retransmission Sequence Example**

This is a sequence diagram showing communication between Host and Device with the following elements:

**Left side - Memory layout (148 KB total):**
- Address 00 0000h: First Portion (56KB)
- Address 00 DFFFh, 00 E000h: Boundary markers
- Address 00 F000h: Middle Portion (60KB) - shown in green with "60 KB" label
- Address 01 CFFh, 01 D000h: Boundary markers  
- Last Portion (32KB)
- Address 02 4FFFh: End marker

**Right side - Communication sequence:**
1. Host sends "READ COMMAND UPIU" to Device
2. Expected Data Transfer Length = 02_5000h (148 KB)
3. Device sends multiple "DATA IN UPIU" messages:
   - First portion: Data Buffer Offset = 0h, Data Transfer Count = E000h (56KB) - "First Portion (56KB)"
   - Middle portion: Data Buffer Offset = 00_E000h, Data Transfer Count = F000h (60KB) - "Middle Portion (60KB)" 
   - Last portion: Data Buffer Offset = 01_D000h, Data Transfer Count = 8000h (32 KB) - "Last Portion (32KB)"
   - Retransmit portion: Data Buffer Offset = 00_F000h, Data Transfer Count = 1000h (4KB) - "Retransmit Portion 4KB"
4. Device sends "RESPONSE UPIU" to Host]