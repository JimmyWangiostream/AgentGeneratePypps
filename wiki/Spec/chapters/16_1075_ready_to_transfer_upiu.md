# JEDEC Standard No. 220G
Page 107

## 10.7.5 READY TO TRANSFER UPIU

The READY TO TRANSFER UPIU is issued by the Target device when it is ready to receive data blocks when processing a SCSI command that requires a data out transfer (e.g., a write command). The Target device may request the data in sequence or out of order by setting the appropriate fields within the UPIU.

The Initiator device responds to a READY TO TRANSFER UPIU packet with one DATA OUT UPIU packet. The Target device may send one or more READY TO TRANSFER UPIU to satisfy the Expected Data Transfer Length that was indicated within the associated COMMAND UPIU. The maximum number of bytes that can be requested with a single READY TO TRANSFER UPIU shall not be greater than the value indicated by bMaxDataOutSize attribute.

See 10.7.13, Data Out Transfer Rules, for further details about Initiator device to Target device data transfer.

### Table 10.25 — READY TO TRANSFER UPIU

| Byte | 0 | 1 | 2 | 3 |
|------|---|---|---|---|
| | xx11 0001b | Flags | LUN | Task Tag |
| 4-7 | IID | Reserved | EXT_IID | Reserved | Reserved | Reserved |
| 8-11 | Total EHS Length (00h) | Reserved | Data Segment Length (0000h) | |
| | (MSB) | | | (LSB) |
| 12-15 | Data Buffer Offset | | | |
| | (MSB) | | | (LSB) |
| 16-19 | Data Transfer Count | | | |
| | (MSB) | | | (LSB) |
| 20-23 | Reserved | HintControl | HintEXT_IID | HintIID | HintLUN | HintTaskTag |
| 24-27 | Hint Data Buffer Offset | | | |
| | (MSB) | | | (LSB) |
| 28-31 | Hint Data Count | | | |
| | | Header E2ECRC (omit if HD=0) | | |

# JEDEC Standard No. 220G
Page 108

## 10.7.5.1 Basic Header

The first 12 bytes of the READY TO TRANSFER UPIU contain the Basic Header as described in 10.6.2, Basic Header Format. Specific details are as follows:

### a) Transaction Type

A type code value of xx11 0001b indicates a READY TO TRANSFER UPIU.

### b) Flags

Table 10.26 describes the flags used in READY TO TRANSFER UPIU.

**Table 10.26 — Flags Definition for RTT UPIU**

| Flag | Description |
|------|-------------|
| Flags.T | A value of '1' in Flags.T indicates that all requested data shall be retransmitted data. See "f) Data Buffer Offset" for further explanation. |

**NOTE** The bit assignment of the Flags field is shown in Table 10.6.

### c) IID

This field is the LSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2 for details.

### d) EXT_IID

This field is the MSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2 for details.

### e) Data Segment Length

The Data Segment Length field shall contain zero as there is no Data Segment in this UPIU.

# JEDEC Standard No. 220G
## Page 109

### 10.7.5.1 Basic Header (cont'd)

#### f) Data Buffer Offset

The Data Buffer Offset field indicates to the Initiator device the location of the beginning of the segment of data to send. The Target device may request the Initiator device to transfer the data in a number of UPIUs, not necessarily in sequential order. The sum of the Data Buffer Offset and the Data Transfer Count should not exceed the Expected Data Transfer Length that was indicated in the COMMAND UPIU.

The Data Buffer Offset shall be an integer multiple of four and shall be less than Expected Data Transfer Length.

To request data retransmission for a task, the device shall set Data Buffer Offset appropriately and shall set Flags.T. All data in the resulting DATA OUT UPIU shall be retransmitted data.

**NOTE** UFS device may set the Data Buffer Offset to retransmit the all or some part of the data that was transferred already by previous READY TO TRANSFER UPIUs and their corresponding DATA OUT UPIUs for the command only if out of order sequencing for DATA OUT UPIUs is enabled (bDataOrdering = 01h or bDataOrdering = 03h).

When the RTT UPIU is a part of a SCSI WRITE transaction [i.e., a transaction which started with a WRITE (6), a WRITE (10), or a WRITE (16) command], the value of this field shall be equal to an integer multiple of the Logical Block Size (bLogicalBlockSize).

#### g) Data Transfer Count

This field indicates the number of bytes the Target device is requesting.

The Data Transfer Count field shall be always an integer multiple of four bytes except for the READY TO TRANSFER UPIU which requests the final portion of data in the transfer.

When the RTT UPIU is a part of a SCSI WRITE transaction [i.e., a transaction which started with a WRITE (6), a WRITE (10), or a WRITE (16) command], the value of this field shall be equal to an integer multiple of the Logical Block Size (bLogicalBlockSize).

The maximum number of bytes that can be requested in a single READY TO TRANSFER UPIU shall not be greater than the value indicated by bMaxDataOutSize attribute.

# JEDEC Standard No. 220G
Page 110

## 10.7.5.1 Basic Header (cont'd)

### h) HintControl

Bit0: This field indicates the validity of the Hint fields provided in the UPIU (HintIID, HintLUN, HintTaskTag, Hint Data Buffer Offset, Hint Data Count). When this field is set to 0b, the Hint fields are not valid and expected to be ignored by the host controller. When this field is set to 1b, the Hint fields are valid

When the feature is not supported or is disabled (bDataOrdering = 00h or bOutOfOrderDataEn = 00h), or the Hint fields (HintTaskTag, etc...) do not refer to a WRITE(6) / WRITE (10) / WRITE (16) command - HintControl shall be set to 0x0 and hint information is not provided.

The hint only provide RTT information, which is independent with max no. of RTT.

Other bits: reserved.

### i) HintIID [3:0]

This field indicates the IID of RTT UPIUs that the device will transfer. This field is valid only when HintControl is set to 1b. HintIID field may be different than IID field.

### j) HintEXT_IID [7:4]

This field indicates the EXT_IID of RTT UPIUs that the device will transfer. This field is valid only when HintControl is set to 1b. HintEXT_IID field may be different than EXT_IID field.

### k) HintLUN

This field indicates the LUN of RTT UPIUs that the device will transfer. This field is valid only when HintControl is set to 1b. HintLUN field may be different than LUN field.

### l) HintTaskTag

This field indicates the Task Tag of RTT UPIUs that the device will transfer. This field is valid only when HintControl is set to 1b. HintTaskTag field may be different than TaskTag field.

### m) Hint Data Buffer Offset

This field indicates the Data Buffer Offset in RTT UPIUs that the device will transfer. This field is valid only when HintControl is set to 1b.

### n) Hint Data Count

This field indicates the number of 4KB that the Initiator device is expected to transfer to the Target starting from Hint Data Buffer Offset field. The value 0 indicates 4KB data, the value 1 indicates 8KB data, and so on.

The device may interleave RTT UPIUs pertaining to all hints provided by the device.

This field is valid only when HintControl is set to 1b.

# JEDEC Standard No. 220G
Page 111

## 10.7.5.1 Basic Header (cont'd)

### o) READY TO TRANSFER UPIU Sequence Examples

Figure 10.5 shows an example of READY TO TRANSFER UPIU sequence. In particular, during the command processing the Target device requests the Initiator device to send a total amount of 577-byte data. The data transfer is done out of order (reverse): at the beginning the last portion, then the middle portion and finally the first portion.

**NOTE** The first READY TO TRANSFER UPIU requests to send the last portion of the data.

[**Figure 10.5 — READY TO TRANSFER UPIU Sequence Example**

This is a sequence diagram showing communication between Host and Device with the following key elements:

- **577-byte Data** buffer on the left divided into three portions:
  - **first portion** (000h-0FFh)
  - **middle portion** (100h-1FFh) 
  - **last portion** (200h-240h, with individual bytes at 00h, 00h, 00h, 00h)

- **Command flow** from Host to Device:
  - COMMAND UPIU (Expected Data Transfer Length = 241h, 577 byte)

- **Three RTT UPIU sequences** from Device to Host requesting data out of order:
  1. **Last portion of the data** - Data Buffer Offset = 200h, Data Transfer Count = 41h
  2. **Middle portion of the data** - Data Buffer Offset = 100h, Data Transfer Count = 100h  
  3. **First portion of the data** - Data Buffer Offset = 0h, Data Transfer Count = 100h

- **DATA OUT UPIU** responses from Host to Device for each portion
- **RESPONSE UPIU** final response from Device to Host

The diagram shows the out-of-order data transfer where last portion is requested first, then middle, then first portion.]

# JEDEC Standard No. 220G
**Page 112**

## 10.7.5.1 Basic Header (cont'd)

Figure 10.6 shows and example of a READY TO TRANSFER UPIU sequence for a WRITE Command when some data sent using a previous DATA OUT UPIU needs to be updated. In this example the device sends an RTT UPIU with an appropriate Data Buffer Offset and Data Transfer Count for the data to be updated.

[**Figure 10.6 — READY TO TRANSFER UPIU with Retransmission Sequence Example**

This is a sequence diagram showing communication between Host and Device with the following elements:

- **Host** and **Device** columns at the top
- **Expected Data Transfer Length = 02_5000h (148KB)** shown in yellow box
- **WRITE COMMAND UPIU** arrow from Host to Device

The diagram shows a data buffer on the left side with memory addresses:
- 00 0000h at top
- First Portion (56KB)
- 00 DFFh, 00 E000h 
- 00 F000h with Middle Portion (60KB) in green
- 01 CFFh, 01 D000h
- Last Portion (32KB) in purple  
- 02 4FFh at bottom

The sequence shows multiple data transfers:
1. **Middle portion of the data**: Data Buffer Offset = 00_E000h, Data Transfer Count = F000h (60KB) - RTT UPIU and DATA OUT UPIU to Middle Portion (60KB)
2. **Last portion of the data**: Data Buffer Offset = 01_D000h, Data Transfer Count = 8000h (32KB) - RTT UPIU and DATA OUT UPIU to Last Portion (32KB) 
3. **Retransmit portion of the data**: Data Buffer Offset = 00_F000h, Data Transfer Count = 1000h (4KB) - RTT UPIU and DATA OUT UPIU to Retransmit portion 4KB (shown in red)
4. **First portion of the data**: Data Buffer Offset = 0h, Data Transfer Count = E000h (56KB) - RTT UPIU and DATA OUT UPIU to First Portion (56KB)

Finally, a **RESPONSE UPIU** arrow from Device back to Host.]