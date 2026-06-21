# JEDEC Standard No. 220G
Page 238

## 11.3.26 UNMAP Command

The UNMAP command shall require the device server to cause one or more LBAs to be unmapped (de-allocated).

UFS defines that a logical unit shall be either Full Provisioning or Thin Provisioning as described in SCSI SBC. To use UNMAP command, SCSI SBC requires that a logical unit to be thin-provisioned and support logical block provisioning management. UNMAP command is not supported in a full-provisioned logical unit.

In UFS, a thin provisioned logical unit shall have sufficient physical memory resources to support the logical block address space when the device is configured by the user. Mapped State and De-Allocated State are mandatory in a UFS thin provisioned logical unit.

### Table 11.45 — UNMAP Command

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-------------|---|---|---|---|---|---|---|---|
| 0 | | | | OPERATION CODE (42h) | | | | |
| 1 | | | | Reserved | | | | ANCHOR<br>= 0b |
| 2 | (MSB) | | | | | | | |
| 3 | | | | | | | | |
| 4 | | | | Reserved | | | | |
| 5 | | | | | | | | (LSB) |
| 6 | | | Reserved | | | GROUP NUMBER = 00000b | | |
| 7 | (MSB) | | | | | | | |
| 8 | | | | PARAMETER LIST LENGTH | | | | (LSB) |
| 9 | | | | CONTROL = 00h | | | | |

• GROUP NUMBER = '0'
• ANCHOR = 0 for UFS. If ANCHOR = 1, the device server shall terminate the command with CHECK CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to INVALID FIELD IN CDB.
• The PARAMETER LIST LENGTH field specifies the length in bytes of the UNMAP parameter data that are sent from the application client to the device server.

# 11.3.26.1 UNMAP Parameter List

The UNMAP parameter list contains the data sent by an application client along with an UNMAP command. Included in the data are an UNMAP parameter list header and block descriptors for LBA extents to be processed by the device server for the UNMAP command. The LBAs specified in the block descriptors may contain overlapping extents, and may be in any order.

## Table 11.46 — UNMAP Parameter List

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | (MSB) | | | UNMAP DATA LENGTH (n-1) | | | | |
| 1 | | | | | | | | (LSB) |
| 2 | (MSB) | | | | | | | |
| 3 | | | UNMAP BLOCK DESCRIPTOR DATA LENGTH (n-7) | | | | (LSB) |
| 4 | (MSB) | | | | | | | |
| .... | | | Reserved | | | | | |
| 7 | | | | | | | | (LSB) |
| | | | **UNMAP block descriptors** | | | | | |
| 8 | (MSB) | | | | | | | |
| .... | | | UNMAP block descriptor (first) | | | | | |
| 23 | | | | | | | | (LSB) |
| | | | ... | | | | | |
| n-15 | (MSB) | | | | | | | |
| .... | | | UNMAP block descriptor (last) | | | | | |
| n | | | | | | | | (LSB) |

• The UNMAP DATA LENGTH field specifies the length in bytes of the following data that is available to be transferred from the data-out buffer. The unmap data length does not include the number of bytes in the UNMAP DATA LENGTH field.

• The UNMAP BLOCK DESCRIPTOR DATA LENGTH field specifies the length in bytes of the UNMAP block descriptors that are available to be transferred from the data-out buffer. The unmap block descriptor data length should be a multiple of 16. If the unmap block descriptor data length is not a multiple of 16, then the last unmap block descriptor is incomplete and shall be ignored. If the UNMAP BLOCK DESCRIPTOR DATA LENGTH is set to zero, then no unmap block descriptors are included in the UNMAP parameter data. This condition shall not be considered an error.

---
JEDEC Standard No. 220G  
Page 239

# JEDEC Standard No. 220G
Page 240

## 11.3.26.2 UNMAP Block Descriptor

### Table 11.47 — UNMAP Block Descriptor

| Bit  | 7    | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|------|---|---|---|---|---|---|---|
| Byte |      |   |   |   |   |   |   |   |
| 0    | (MSB)|   |   |   |   |   |   |   |
| .... |      | UNMAP LOGICAL BLOCK ADDRESS |   |   |   |   |   |   |
| 7    |      |   |   |   |   |   |   | (LSB) |
| 8    | (MSB)|   |   |   |   |   |   |   |
| ... |      | NUMBER OF LOGICAL BLOCKS |   |   |   |   |   |   |
| 11   |      |   |   |   |   |   |   | (LSB) |
| 12   |      |   |   |   |   |   |   |   |
| .... |      | Reserved |   |   |   |   |   |   |
| 15   |      |   |   |   |   |   |   |   |

• The UNMAP LOGICAL BLOCK ADDRESS field contains the first LBA of the UNMAP block descriptor to be unmapped.

• The NUMBER OF LOGICAL BLOCKS field contains the number of LBAs to be unmapped beginning with the LBA specified by the UNMAP LOGICAL BLOCK ADDRESS field.

• To minimize performance degradation, the entire LBA region to be unmapped should be aligned with the OptimalUnmapGranularitySize value in the Unit Descriptor where possible (but not required).

• If the NUMBER OF LOGICAL BLOCKS is set to zero, then no LBAs shall be unmapped for this UNMAP block descriptor. This condition shall not be considered an error.

• If the LBA specified by the UNMAP LOGICAL BLOCK ADDRESS field plus the number of logical blocks exceeds the capacity of the medium, then the device server shall terminate the command with CHECK CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to LOGICAL BLOCK ADDRESS OUT OF RANGE.

• If the UFS device does not support Block Limits VPD page then MAXIMUM UNMAP LBA COUNT value and MAXIMUM UNMAP BLOCK DESCRIPTOR COUNT value are defined as in the following:
  ○ MAXIMUM UNMAP LBA COUNT = LBA count reported in READ CAPACITY
  ○ MAXIMUM UNMAP BLOCK DESCRIPTOR COUNT = 1

• If Vital Product Data Page is supported by the device, the MAXIMUM UNMAP LBA COUNT and MAXIMUM UNMAP BLOCK DESCRIPTOR COUNT are set by the device manufacturer in the Block Limits VPD page. If the total number of logical blocks specified in the UNMAP block descriptor data exceeds the value indicated in the MAXIMUM UNMAP LBA COUNT field in the Block Limits VPD page or if the number of UNMAP block descriptors exceeds the value of the MAXIMUM UNMAP BLOCK DESCRIPTOR COUNT field in the Block Limits VPD page, then the device server shall terminate the command with CHECK CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to INVALID FIELD IN PARAMETER LIST.

# JEDEC Standard No. 220G
Page 241

## 11.3.26.3 UNMAP parameter list transfer

• The Device Server requests to transfer the UNMAP parameter list from the Application Client data-out buffer by issuing a series of READY TO TRANSFER UPIU's (RTT).

• The UNMAP parameter list is delivered in one or more segments sending DATA OUT UPIU packets, as indicated in the RTT requests.

• Zero or an incomplete number of segments may be requested, if an error occurs before the entire data transfer is complete.

## 11.3.26.4 UNMAP Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU
• If the command is performed successfully then it will terminate with a STATUS response of GOOD.
• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned.
• Failure can occur for numerous reasons. When the UNMAP command fails a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as

  ○ ILLEGAL REQUEST (range or CDB errors)
  
  ○ MEDIUM ERROR (medium failure, ECC, etc.)
  
  ○ HARDWARE ERROR (hardware failure)
  
  ○ UNIT ATTENTION (reset, power-on, etc.)
  
  ○ DATA PROTECT (permanent, power-on, secure write protect, etc.)
  
  ○ etc.