# JEDEC Standard No. 220G
Page 296

## 12.4.6.1 CDB Format of SECURITY PROTOCOL IN/OUT Commands

### Table 12.14 — CDB Format of SECURITY PROTOCOL IN/OUT Commands

| Byte | Bit |   7   |   6   |   5   |   4   |   3   |   2   |   1   |   0   |
|------|-----|-------|-------|-------|-------|-------|-------|-------|-------|
| 0    |     |       |       |       | OPERATION CODE (1) |       |       |       |       |
| 1    |     |       |       |       | SECURITY PROTOCOL |       |       |       |       |
| 2    |     |       |       |       |                   |       |       |       |       |
|      |     |       |       | SECURITY PROTOCOL SPECIFIC |       |       |       |       |
| 3    |     |       |       |       |                   |       |       |       |       |
| 4    |     | INC_512 = 0b |       |       | Reserved      |       |       |       |       |
| 5    |     |       |       |       | Reserved          |       |       |       |       |
| 6    |     | (MSB) |       |       |                   |       |       |       |       |
|      |     |       |       | ALLOCATION / TRANSFER LENGTH (2) |       |       |       |       |
| 9    |     |       |       |       |                   |       |       |       | (LSB) |
| 10   |     |       |       |       | Reserved          |       |       |       |       |
| 11   |     |       |       |       | CONTROL = 00h     |       |       |       |       |

**NOTE 1** OPERATION CODE = A2h for SECURITY PROTOCOL IN command, OPERATION CODE = B5h for SECURITY PROTOCOL OUT command.

**NOTE 2** ALLOCATION LENGTH for SECURITY PROTOCOL IN command, TRANSFER LENGTH for SECURITY PROTOCOL OUT command.

The RPMB well known logical unit shall support the following SECURITY PROTOCOL field values:
- 00h: Security protocol information
- ECh: JEDEC Universal Flash Storage (security protocol ID assigned for JEDEC UFS application)

Other values are invalid.

SECURITY PROTOCOL IN/OUT commands shall consider the unique Security Protocol ID assigned to JEDEC UFS application as the only valid Security Protocol ID.

# JEDEC Standard No. 220G
Page 297

## 12.4.6.1 CDB Format of SECURITY PROTOCOL IN/OUT Commands (cont'd)

When the SECURITY PROTOCOL field is set to ECh (i.e., the JEDEC Universal Flash Storage),

• INC_512 bit shall be set to zero to specify that the ALLOCATION LENGTH or the TRANSFER LENGTH field expresses the number of bytes to be transferred.

• If the ALLOCATION LENGTH field in a SECURITY PROTOCOL IN command is not equal to an integer multiple of 512 in Normal RPMB mode or an integer multiple of 4K in Advanced RPMB mode, then the command shall be terminated with CHECK CONDITION status.

• If the TRANSFER LENGTH field in a SECURITY PROTOCOL OUT command is not equal to an integer multiple of 512 in Normal RPMB mode or an integer multiple of 4K in Advanced RPMB mode, then the command shall be terminated with CHECK CONDITION status.

• The SECURITY PROTOCOL SPECIFIC field specifies the RPMB Protocol ID.

The RPMB Protocol ID indicates the RPMB region as defined in Table 12.15

### Table 12.15 — SECURITY PROTOCOL SPECIFIC Field for Protocol ECh

| SECURITY PROTOCOL SPECIFIC: RPMB Protocol ID | | Description |
|---|---|---|
| **CDB Byte 2** | **CDB Byte 3** |  |
| 00h | 01h | RPMB Region 0 |
| 01h | 01h | RPMB Region 1 |
| 02h | 01h | RPMB Region 2 |
| 03h | 01h | RPMB Region 3 |
| Other values | | Reserved |

If the SECURITY PROTOCOL SPECIFIC field is set to an invalid value or the corresponding RPMB region is not enabled, then SECURITY PROTOCOL IN/OUT command shall be terminated with CHECK CONDITION status, with the sense key set to ILLEGAL REQUEST and the additional sense code set to INVALID FIELD IN CDB. In this case, Total EHS length shall be '0h' and EHS field shall not be included in RESPONSE UPIU in Advanced RPMB mode.

Secure Write Protect Configuration Block write, Secure Write Protect Configuration Block read, Authenticated Vendor Specific Command, and Authenticated Vendor Specific Command Status Read requests are supported only by RPMB region 0.

As required by [SPC], the SECURITY PROTOCOL value of 00h (security protocol information) shall be supported if the SECURITY PROTOCOL IN command is supported by the device. The security protocol information security protocol (i.e., the SECURITY PROTOCOL field set to 00h in a SECURITY PROTOCOL IN command) is used to transfer security protocol related information from the logical unit.

# JEDEC Standard No. 220G
## Page 298

### 12.4.6.1 CDB Format of SECURITY PROTOCOL IN/OUT Commands (cont'd)

When the SECURITY PROTOCOL field is set to 00h in a SECURITY PROTOCOL IN command, the two bytes SECURITY PROTOCOL SPECIFIC field shall contain a numeric value as defined in Table 12.16.

#### Table 12.16 — Security Protocol Specific Field Values for Protocol 00h

| Security Protocol Specific Field Value |  | Description | Support |
|---|---|---|---|
| CDB Byte 2 | CDB Byte 3 |  |  |
| 00h | 00h | Supported security protocol list | Mandatory |
| 00h | 01h | Certificate data | Mandatory |
|  | Other values | Reserved |  |

# 12.4.6.2 Supported Security Protocols List Description

According to [SPC], if the SECURITY PROTOCOL field is set to 00h and the SECURITY PROTOCOL SPECIFIC field is set to 0000h in a SECURITY PROTOCOL IN command, the parameter data shall have the format shown in Table 12.17.

## Table 12.17 — Supported Security Protocols SECURITY PROTOCOL IN Parameter Data

| Byte | Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
|------|-------|-------|-------|-------|-------|-------|-------|-------|
| 0    |       |       |       |       |       |       |       |       |
| ⋮    |       |       | Reserved |       |       |       |       |       |
| 5    |       |       |       |       |       |       |       |       |
| 6    | (MSB) |       |       |       |       |       |       |       |
|      |       | SUPPORTED SECURITY PROTOCOL LIST LENGTH (m-7) |       |       |
| 7    |       |       |       |       |       |       |       | (LSB) |
| 8    |       | SUPPORTED SECURITY PROTOCOL [first] (00h) |       |       |
|      |       |       |       | ⋮ |       |       |       |       |
| m    |       | SUPPORTED SECURITY PROTOCOL [last] |       |       |
| m+1  |       |       |       |       |       |       |       |       |
| ⋮    |       |       | Pad Bytes (optional) |       |       |       |       |
| n    |       |       |       |       |       |       |       |       |

Security protocol information (00h) and the JEDEC Universal Flash Storage (ECh) are the only valid security protocol ID's supported by the RPMB well known logical unit, therefore Table 12.17 shall be implemented as defined in Table 12.18.

## Table 12.18 — UFS Supported Security Protocols SECURITY PROTOCOL IN Parameter Data

| Byte | Bit 7 | Bit 6 | Bit 5 | Bit 4 | Bit 3 | Bit 2 | Bit 1 | Bit 0 |
|------|-------|-------|-------|-------|-------|-------|-------|-------|
| 0    |       |       |       |       |       |       |       |       |
| ⋮    |       |       | Reserved |       |       |       |       |       |
| 5    |       |       |       |       |       |       |       |       |
| 6    | (MSB) |       |       |       |       |       |       |       |
|      |       | 0002h (SUPPORTED SECURITY PROTOCOL LIST LENGTH) |       |       |
| 7    |       |       |       |       |       |       |       | (LSB) |
| 8    |       | 00h (Security protocol information) |       |       |
| 9    |       | ECh (JEDEC Universal Flash Storage) |       |       |
| 10   |       |       |       |       |       |       |       |       |
| ⋮    |       |       | Pad bytes (optional) |       |       |       |       |
| n    |       |       |       |       |       |       |       |       |

---
*JEDEC Standard No. 220G*  
*Page 299*

# JEDEC Standard No. 220G
Page 300

## 12.4.6.3 Certificate Data Description

If the SECURITY PROTOCOL field is set to 00h and the SECURITY PROTOCOL SPECIFIC field is set to 0001h in a SECURITY PROTOCOL IN command, the parameter data shall have the format shown in Table 12.19.

### Table 12.19 — Certificate Data SECURITY PROTOCOL IN Parameter Data

| Byte | Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|-----|---|---|---|---|---|---|---|---|
| 0 |     |   |   |   |   |   |   |   |   |
| 1 |     |   |   | Reserved |   |   |   |   |   |
| 2 |     | (MSB) |   |   |   |   |   |   |   |
| 3 |     |   | CERTIFICATE LENGTH (m-3) |   |   |   | (LSB) |
| 4 |     |   |   |   |   |   |   |   |   |
| m |     |   |   | CERTIFICATE |   |   |   |   |   |
| m+1 |   |   |   |   |   |   |   |   |   |
| n |     |   |   | Pad bytes (optional) |   |   |   |   |   |

The Device Server does not have a certificate to transfer, the CERTIFICATE LENGTH field shall be set to 0000h. therefore Table 12.19 shall be implemented as defined in Table 12.20.

### Table 12.20 — UFS Certificate Data SECURITY PROTOCOL IN Parameter Data

| Byte | Bit | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|------|-----|---|---|---|---|---|---|---|---|
| 0 |     |   |   |   |   |   |   |   |   |
| 1 |     |   |   | Reserved |   |   |   |   |   |
| 2 |     | (MSB) |   |   |   |   |   |   |   |
| 3 |     |   | 0000h (CERTIFICATE LENGTH) |   |   | (LSB) |   |
| 4 |     |   |   |   |   |   |   |   |   |
| n |     |   |   | Pad bytes (optional) |   |   |   |   |   |