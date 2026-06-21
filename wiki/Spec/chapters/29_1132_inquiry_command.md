# 11.3.1 General information about SCSI commands in UFS

The remaining part of this sub-clause describes the SCSI commands used in UFS devices. A dedicated paragraph for each command provides: CDB table, brief command description, relevant command fields, details about mandatory and optional features, and some other fundamental information.

Fields that are not supported by UFS should be set to zero, and are documented using the notation "= 00h" (e.g., RDPROTECT = 00h). The device may ignore values in fields that are not supported by UFS.

**NOTE** The values enclosed in parenthesis are defined in SCSI standards and are not UFS specific (e.g., OPERATION CODE (12h)).

The following information applies to all SCSI commands used in UFS.

**CONTROL** - The CONTROL byte is present in several CDB and it is defined in [SAM]. The CONTROL byte is not used in this standard: the CONTROL byte should be set to zero and it shall be ignored by UFS device. No vendor specific interpretation and Normal ACA are assumed.

**Auto Contingent Allegiance (ACA)** - Establishing an ACA condition the application client may request that the device server alter command processing when a command terminates with a CHECK CONDITION status. UFS device does not support ACA.

## 11.3.2 INQUIRY Command

The INQUIRY command (see Table 11.2) is a request for information regarding the logical units and UFS target device be sent to the application client. Refer to [SPC] for more details regarding the INQUIRY command.

### Table 11.2 — INQUIRY Command

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-------------|---|---|---|---|---|---|---|---|
| 0 | | | | OPERATION CODE (12h) | | | | |
| 1 | | | Reserved | | | | Obsolete | EVPD |
| 2 | | | | PAGE CODE | | | | |
| 3 | (MSB) | | | | | | | |
| 4 | | | ALLOCATION LENGTH* | | | | | (LSB) |
| 5 | | | | CONTROL = 00h | | | | |

\* Allocation Length = Number of response bytes to return

### 11.3.2.1 VITAL PRODUCT DATA

When EVPD = 1, the device server shall return the vital product data specified by the PAGE CODE field as defined in [SPC]. Support for all vital product data except Mode Page Policy VPD is optional for UFS. Mode Page Policy VPD shall be supported by UFS device to provide information about Mode pages which are applicable to Device level or logical unit level. See [SPC] for data format definition of Mode Page Policy VPD page.

---
JEDEC Standard No. 220G  
Page 185

# JEDEC Standard No. 220G
Page 186

## 11.3.2.2 STANDARD INQUIRY DATA

When EVPD = 0 and Page Code = 0, the Standard INQUIRY DATA is responded to INQUIRY command. The standard INQUIRY data format is shown on Table 11.3. INQUIRY data shall contain at least 36 bytes. Table 11.4 defines the INQUIRY response data for UFS.

The INQUIRY command requests that information regarding the logical unit and SCSI target device be sent to the Application Client.

The INQUIRY command may be used by an Application Client after a hard reset or power on condition to determine information about the device for system configuration. If a INQUIRY command is received with a pending UNIT ATTENTION condition (i.e., before the device server reports CHECK CONDITION status), the device server shall perform the INQUIRY command.

INQUIRY information is returned in standard INQUIRY response data structure (see Table 11.3).

• Client requests number of bytes to return
• First 36 bytes are defined for UFS as standard
• Requesting zero byte is valid
• Requesting 36 bytes will result in the device returning the complete record
• Requesting more bytes than defined will result in truncation to max number device has defined

The Device Server should process the INQUIRY command even when an error occurs that prohibits normal command completion

• When in UNIT ATTENTION
• During other conditions that may affect medium access

The Command CDB shall be sent in a single COMMAND UPIU

### Table 11.3 — Standard INQUIRY Data Format

| Bit<br>Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|-------------|---|---|---|---|---|---|---|---|
| 0 | PERIPHERAL QUALIFIER | | | PERIPHERAL DEVICE TYPE | | | | |
| 1 | RMB | | | Reserved | | | | |
| 2 | | | VERSION | | | | | |
| 3 | Obsolete | Obsolete | NORMACA | HISUP | | RESPONSE DATA FORMAT | | |
| 4 | | | ADDITIONAL LENGTH (n-4) | | | | | |
| 5 | ScCS | ACC | | TPGS | | 3PC | Reserved | PROTECT |
| 6 | Obsolete | ENCSERV | VS | MULTIP | Obsolete | Obsolete | Obsolete | ADDR16 |
| 7 | Obsolete | Obsolete | WBUS16 | SYNC | Obsolete | Obsolete | CMDQUE | VS |
| 8 | (MSB) | | | | | | | |
| 15 | | | VENDOR IDENTIFICATION | | | | | (LSB) |
| 16 | (MSB) | | | | | | | |
| 31 | | | PRODUCT IDENTIFICATION | | | | | (LSB) |
| 32 | (MSB) | | | | | | | |
| 35 | | | PRODUCT REVISION LEVEL | | | | | (LSB) |

# JEDEC Standard No. 220G
Page 187

## 11.3.2.3 Inquiry Command Data Response

• Data returned from an INQUIRY command will be transferred to the Application Client in a single DATA IN UPIU

• The Device Server will transfer the Response Data in the Data Segment area of a DATA IN UPIU

• An Allocation Length of zero specifies that no data shall be transferred. This condition shall not be considered as an error, and DATA IN UPIU shall not be generated.

• No DATA IN UPIU will be transferred if an error occurs

• For Standard INQUIRY Data,
  ○ the Device Server shall return a number of bytes equal to the minimum between 36 and the value specified in the Allocation Length.
  ○ Standard INQUIRY Response Data is shown in Table 11.4.

## 11.3.2.4 Inquiry Response Data

### Table 11.4 — Standard INQUIRY Response Data

| Byte | Bit | Value | Description |
|------|-----|-------|-------------|
| 0 | 7:5 | 000b | PERIPHERAL QUALIFIER: 0 |
| 0 | 4:0 | 00h/1Eh | PERIPHERAL DEVICE TYPE: 00h: Direct Access Device for logical unit (non well known) 1Eh: Well known logical unit |
| 1 | 7 | 0b | RMB: Medium not removable |
| 1 | 6:0 | 0000000b | RESERVED |
| 2 | 7:0 | 06h | VERSION: Conformance to [SPC] |
| 3 | 7:4 | 0000b | N/A |
| 3 | 3:0 | 0010b | RESPONSE DATA FORMAT: Type 2 |
| 4 | 7:0 | 31d | ADDITIONAL LENGTH: 31 bytes |
| 5 | 7:0 | 00h | N/A |
| 6 | 7:0 | 00h | N/A |
| 7 | 7:2 | 000000b | N/A |
| 7 | 1:1 | 1b | CMDQUE: Support command management (SAM) |
| 7 | 0:0 | 0b | N/A |
| 8:15 | 7:0 | ASCII | VENDOR IDENTIFICATION: Left justified (e.g., "Micron ") |
| 16:31 | 7:0 | ASCII | PRODUCT IDENTIFICATION: Left justified (e.g., "UFS MSD M33-X ") |
| 32:35 | 7:0 | ASCII | PRODUCT REVISION LEVEL: Left justified (e.g., "1.23") |

NOTE 1 The fields marked with N/A are not applicable for UFS, and their values shall be zero.

The 4-byte PRODUCT REVISION LEVEL in the Inquiry Response Data shall identify the firmware version of the UFS device and shall be uniquely encoded for any firmware modification implemented by the UFS device vendor.