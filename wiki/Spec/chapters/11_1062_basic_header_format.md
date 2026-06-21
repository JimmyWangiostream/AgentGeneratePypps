# JEDEC Standard No. 220G
Page 74

## 10.6.1 Overview

UPIU total size will vary depending upon the UPIU transaction type but all UPIU sizes will be an integer multiple of 32-bits, meaning they will be addressed on a 4-byte boundary. If the aggregation of data and header segments does not end on a 32-bit boundary then additional padding will be added to round up the UPIU to the next 32-bit, 4-byte address boundary.

The UPIU size can be fixed or variable depending upon the Transaction Type field and extension flags. Some Transaction Types will have different lengths for the same code others will always be a fixed size. In addition, any UPIU can be extended if necessary to include extra header and data segments. The general format allows for extension and has flags and size fields defined within the structure to indicate to the processing entity where the extension areas are located within the structure and their size (not including padding) and in some cases the type of extension data.

## 10.6.2 Basic Header Format

This is the format of the basic header contained within every UPIU structure. This data packet will be sent between Initiator devices and Target devices and will be part of a larger function specific UPIU. There is enough information in this header to allow the Initiator device or the Target device to track the destination and the source, the function request, if additional data and parameters are required and whether they are included in this UPIU or will follow in subsequent UPIU's.

The smallest sized UPIU is currently defined to have 32 bytes. The 32 bytes area will contain the basic header plus additional fields. This means that the smallest datum sent over the Service Delivery Subsystem will be 32 bytes.

### Table 10.4 — Basic Header Format

| Transaction Type | Flags | LUN | Task Tag |
|-----------------|-------|-----|----------|
| IID | Command Set Type | EXT_IID, Query Function, Task Manag. Function | Response | EXT_IID, Status |
| Total EHS Length | Device Information | Data Segment Length |

The basic header formats are defined as follows:

**a) Transaction Type**

The Transaction Type indicates the type of request or response contained within the data structure. The Transaction Type contains the HD bit, the DD bit and the Transaction Code, see Table 10.5.

### Table 10.5 — Transaction Type Format

| 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|---|---|---|---|---|---|---|---|
| HD | DD | | | Transaction Code | | | |

**Transaction Type Bits**

# JEDEC Standard No. 220G
Page 75

## 10.6.2 Basic Header Format (cont'd)

### b) HD

The HD bit when set to '1' specifies that an end-to-end CRC of all Header Segments is included within the UPIU. The CRC fields include all fields within the header area. The CRC is placed at the 32-bit word location following the header.

End-to-end CRC is not supported in this version of the standard, therefore HD shall be '0'.

### c) DD

The DD bit when set to '1' specifies that an end-to-end CRC of the Data Segment is included with the UPIU. The 32-bit CRC is calculated over all the fields within the Data Segment. The 32-bit CRC word is placed at the end of the Data Segment. This will be the last word location of the UPIU.
End-to-end CRC is not supported in this version of the standard, therefore DD shall be '0'.

### d) Transaction Code

The Transaction Code indicates the operation that is represented within the data fields of the UPIU and the number and location of the defined fields within the UPIU (see Table 10.1).

# JEDEC Standard No. 220G
Page 76

## 10.6.2 Basic Header Format (cont'd)

### e) Flags

The content of the Flags field vary with the Transaction Type opcode (1).

#### Table 10.6 — UPIU Flags

| UPIU Type | Operational Flags |  |  |  | Retransmit Indicator | CP(2) | Task Attribute |  |
|-----------|-------------------|--|--|--|---------------------|-------|----------------|--|
|           | Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
| NOP Out | - | - | - | - | - | - | - | - |
| NOP In | - | - | - | - | - | - | - | - |
| Command | - | R | W | - | - | CP(2) | | ATTR |
| Response | - | O | U | D | - | - | - | - |
| Data Out | - | - | - | - | T | - | - | - |
| Data In | - | - | - | - | T | - | - | - |
| Ready to Transfer | - | - | - | - | T | - | - | - |
| Reject | - | - | - | - | - | - | - | - |
| Query Request | - | - | - | - | - | - | - | - |
| Query Response | - | - | - | - | - | - | - | - |
| Task Management Request | - | - | - | - | - | - | - | - |
| Task Management Response | - | - | - | - | - | - | - | - |

NOTE 1 "-" denotes reserved values.  
NOTE 2 CP = Command Priority

#### Table 10.7 — Task Attribute Definition

| Task Attribute | Bit 1 | Bit 0 |
|----------------|-------|-------|
| Simple | 0 | 0 |
| Ordered | 0 | 1 |
| Head of Queue | 1 | 0 |
| ACA (Not Used) | 1 | 1 |

# JEDEC Standard No. 220G
Page 77

## 10.6.2 Basic Header Format (cont'd)

### f) Response

If a response is required from a Target device, this field indicates whether the requested function succeeded or failed. This field is reserved in UPIU transactions from Initiator device to Target device.

**Table 10.8 — UTP Response Values**

| Opcode | Response Description |
|--------|---------------------|
| 00h    | Target Success      |
| 01h    | Target Failure      |
| 02h-7Fh| Reserved           |
| 80h-FFh| Vendor Specific    |

### g) Status

This field contains the SCSI status (as defined in [SAM]) if the transaction is a RESPONSE UPIU for a COMMAND UPIU with Command Set Type = 00h (SCSI Command). Otherwise it contains an opcode specific status or it is reserved.

### h) Reserved

All fields marked as reserved shall contain a value of zero.

### i) LUN

This field contains the Logical Unit Number to which a request is targeted. Target devices will contain at a minimum one logical unit numbered unit 0. This field is generated by the Initiator device and maintained by the Target device and Initiator device for all UPIU transactions relating to a single request or task.

### j) Task Tag

The Task Tag is generated by the Initiator device when creating a task request. This field will be maintained by the Initiator device and Target device for all UPIU transactions relating to a single task. The Initiator device will contain a register or variable that represents the Task Tag value. The Initiator device will generate unique Task Tag by incrementing the internal variable when creating a new task request. When a task request is made up of or generates a series of UPIU transactions, all UPIU will contain the same value in the Task Tag field.

In particular, the same Task Tag value shall be maintained for the UPIU grouped in each row of Table 10.9.

**Table 10.9 — UPIU Associated to a Single Task**

| Initiator UPIU           | Target UPIU                    |
|-------------------------|--------------------------------|
| NOP Out                 | NOP In                         |
| Command, Data Out       | Ready to Transfer, Response    |
| Command                 | Data In, Response              |
| Task Management Request | Task Management Response       |
| Query Request           | Query Response                 |

# JEDEC Standard No. 220G
## Page 78

### 10.6.2 Basic Header Format (cont'd)

#### k) IID, EXT_IID (Nexus Initiator ID)

In UFS4.0, the Initiator ID field is 8 bits wide, comprised of the EXT_IID and IID fields as shown in Table 10.10.

**Table 10.10 — Initiator ID Composition**

| Initiator ID |
|---|
| 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
| EXT_IID | | | | IID | | | |
| [7:4] of byte 7 for host to device UPIUs | | | | [7:4] of byte 4 |
| [7:4] of byte 5 for device to host UPIUs | | | | |

• **IID**
  ○ The IID field is 4 bits wide, encoded in bits [7:4] of byte 4. This field indicates identity fo the Initiator device which created the task request.

• **EXT_IID**
  ○ The EXT_IID field is 4 bits wide, encoded in bits [7:4] of byte 7 for host to device UPIUs (COMMAND, DATA OUT, TASK MANAGEMENT REQUEST)
  ○ The EXT_IID field is 4 bits wide, encoded in bits [7:4] of byte 5 for device to host UPIUs (RESPONSE, DATA IN, READY TO TRANSFER, TASK MANAGEMENT RESPONSE, REJECT)

The Initiator ID shall be set to zero if there is only one Initiator device.

UFS devices shall support all 256 Initiator ID values (when bEXTIIDEn = 01h) or 16 Initiator ID values (when bEXTIIDEn = 00h). The Initiator ID shall be encoded in this field by the Host when creating a request. This field is maintained by the Initiator device and Target device for all UPIU transactions relating to the same task.

#### l) Command Set Type

Command set type field is 4 bits wide, encoded in bits [3:0] of byte 4. This field indicates the command set type the Command and RESPONSE UPIU is associated with. This field is defined for the COMMAND UPIU and the RESPONSE UPIU. This field is reserved in all other UPIU's. This field shall be used to indicate the type of command that is in the CDB field. The currently supported command types are listed in Table 10.11.

**Table 10.11 — Command Set Type**

| Value | Description |
|-------|-------------|
| 0h | SCSI Command Set (SPC, SBC) |
| 1h | UFS Specific Command Set |
| 2h … 7h | Reserved |
| 8h … Fh | Vendor Specific Set |

**NOTE** This standard does not define any UFS specific command, therefore the value 1h is reserved for future use.

# JEDEC Standard No. 220G
## Page 79

### 10.6.2 Basic Header Format (cont'd)

**m) Query Function, Task Manag. Function**

This field is used in QUERY_REQUEST and QUERY_RESPONSE UPIU's to define the Query function, and in TASK MANAGEMENT REQUEST UPIU to define the task management function.

**n) Device Information**

This field provides device level information required by specific UFS functionality in all RESPONSE UPIU.

**o) Total Extra Header Segment Length**

This field represents the size in 32-byte units of all Extra Header Segments contained within the UPIU. This field is used if additional header segments are needed. The length of each Extra Header Segment shall be a multiple of 32 bytes. The value in this field is the number of total number of bytes in all EHS divided by 32.

*Total EHS Length value = INTEGER((Total Extra Header Segment Bytes + 31)/32)*

The maximum size of all EHS fields combined is 96 bytes. A value of zero in this field indicates that there are no EHS contained within the UPIU. Therefore the valid value of this field shall be one of the following: 0, 1, 2 or 3.

**p) Data Segment Length**

The Data Segment Length field contains the number of valid bytes within the Data Segment of the UPIU. When the number of bytes within the Data Segment is not a multiple of four then the last 32-bit field will be padded with zeros to terminate on the next nearest 32-bit boundary. The number of 32-bit units (DWORDS) that make up the Data Segment is calculated as follows:

*Data Segment DWORDS = INTEGER((Data Segment Length + 3)/4)*

Since the Data Segment Length field size is two bytes, the data segment can contain a maximum of 65535 valid bytes. A value of zero in this field indicates that there is no Data Segment within the UPIU.

**q) Transaction Specific Fields**

Additional fields as required by certain Transaction Codes are located within this area. For UTP, this area starts at byte address 12 within the UPIU and terminates on a 32 byte boundary at byte address 31. Since all UPIU contain a 12 byte Basic Header this leaves 20 bytes remaining for this area.

# JEDEC Standard No. 220G
Page 80

## 10.6.2 Basic Header Format (cont'd)

### r) Extra Header Segments

The Extra Header Segments exist if the Total EHS Length field contains a non-zero value. For UTP, this area will start at byte address 32 within the UPIU. The UPIU may contain zero or more EHS. The length of each Extra Header Segment shall be a multiple of 32 bytes.The Extra Header Segments contain zero or more EHS Entry of the following format. In this version of the standard, up to one EHS entry shall be allowed.

[**Figure 10.1 - EHS Entry Format**: A diagram showing the structure of an EHS Entry with the following components:
- Byte 0: bLength field
- Byte 1: bEHSType field  
- Bytes 2-3: wEHSSubType field
- Bytes 4 to (32*bLength)-1: EHS data field (depending on bEHSType & wEHSSubType)
The diagram shows these fields arranged in a rectangular format with labels indicating "EHS Header", "EHS Entry", and "EHS Data" sections. There's an arrow pointing to byte 0 with text "Indicating the size of the EHS Entry in 32-byte units".]

Table 10.12 describes the EHS Entry data format that gives detailed field information.

**Table 10.12 — EHS Entry Format**

| Byte | Name | Description |
|------|------|-------------|
| 0 | bLength | Size of the EHS Entry in 32 byte units |
| 1 | bEHSType | EHS Type<br>00h : Reserved<br>01h: Advanced RPMB<br>02h-7Fh : Reserved<br>80h-FFh : Vendor specific |
| 2:3 | wEHSSubType | EHS Sub Type |
| 4:(32*bLength)-1 | EHS data | EHS Data<br>Data in this field depends on the EHS Type and EHS Sub Type |

# JEDEC Standard No. 220G
Page 81

## 10.6.2 Basic Header Format (cont'd)

### s) Data Segment

The Data Segment field starts on the next 32-bit (DWORD) boundary after the EHS area within the UPIU. For UTP, there are no EHS areas used meaning that the Data Segment will begin at byte address 32 (byte address 36 if F2FECRC is enabled) within the UPIU. The Data Segment will be a multiple of 32-bits, thereby making the UPIU packet size a multiple of 4 bytes. The Data Segment Length field can contain a value that is not a multiple of 4 bytes but the Data Segment area will be padded with zeros to fill to the next nearest 32-bit (DWORD) boundary. The Data Segment Length field indicates the number of valid bytes within the Data Segment.