# 11.3.18 FORMAT UNIT Command

The FORMAT UNIT command requests that the Device Server format the medium into Application Client accessible logical blocks as specified in the parameter lists. The Device Server may also certify the medium and create control structures for the management of the medium and defects. The degree that the medium is altered by the command is vendor specific.

A FORMAT UNIT command sent to the Device well known logical unit requests the device format all enabled logical units except the RPMB well known logical unit (see 12.2.3.4).

If the medium is write-protected, then the command shall be terminated with CHECK CONDITION status with the sense key set to DATA PROTECT.

Following a successful format operation all LBAs:

a) shall be mapped on a fully provisioned logical unit (bProvisioningType set to 00h)
b) shall be unmapped on a thin provisioned logical unit (bProvisioningType set to 02h or 03h)

For a LBA in a formatted logical unit specified by a read operation, the device server shall send user data with all bits set to zero to the data in buffer.

The Command CDB shall be sent in a single COMMAND UPIU.

## Table 11.33 — FORMAT UNIT Command

| Bit Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 | | | | OPERATION CODE (04h) | | | | |
| 1 | FMTPINFO = 00b | LONGLIST | FMTDATA = 0b | CMPLST | DEFECT LIST FORMAT= 000b |
| 2 | | | | Vendor Specific = 00b | | | | |
| 3 | | | | | | | | |
| 4 | | | | Obsolete | | | | |
| 5 | | | | CONTROL = 00h | | | | |

---

*JEDEC Standard No. 220G*  
*Page 223*

# 11.3.18.1 Format Unit Command Parameters

## Table 11.34 — Format Unit Command Parameters

| Byte | Bit | Description |
|------|-----|-------------|
| 1 | 7:6 | **FMTPINFO**: Specifies the FORMAT PROTECTION INFORMATION as detailed in [SBC]. |
| 1 | 5 | **LONGLIST**: If set to '0' then the parameter list, if any, will use the SHORT parameter list header as defined in [SBC]. If set to '1' then the parameter list uses the LONG format. |
| 1 | 4 | **FMTDATA**: If set to '1' specifies that parameter list data shall be transferred from the data-out buffer. |
| 1 | 3 | **CMPLST**: Complete List. '0' indicates that the parameter list contains a partial growing list of defects. A '1' indicates the list is complete. See [SBC]. |
| 1 | 2:0 | **DEFECT LIST FORMAT**: If the FMTDATA bit is set to one, then the DEFECT LIST FORMAT field specifies the format of the address descriptors in the defect list. See [SBC]. |
| 2 | 7:0 | **VENDOR SPECIFIC**: Vendor specified field. |

## 11.3.18.2 Format Unit Command Data Transfer

• If needed, the Device Server requests to transfer the FORMAT UNIT parameter list from the Application Client data-out buffer by issuing a series of READY TO TRANSFER UPIU's (RTT).

• The FORMAT UNIT parameter list is delivered in one or more segments sending DATA OUT UPIU packets, as indicated in the RTT requests.

• Zero or an incomplete number of segments may be requested if an error occurs before the entire data transfer is complete.

## 11.3.18.3 Format Unit Command Status Response

• STATUS response will be sent in a single RESPONSE UPIU.

• If the requested format of the medium is performed successfully then the command will terminate with a STATUS response of GOOD.

• If the unit is not ready to accept a new command (e.g., still processing previous command) a STATUS response of BUSY will be returned.

• Other failures can occur for numerous reasons. When the FORMAT UNIT command fails, a STATUS response of CHECK CONDITION will be returned along with an appropriate SENSE KEY, such as:
  ○ ILLEGAL REQUEST (range or CDB errors)
  ○ MEDIUM ERROR (medium failure, ECC, etc.)
  ○ HARDWARE ERROR (hardware failure)
  ○ UNIT ATTENTION (reset, power-on, etc.)
  ○ DATA PROTECT (permanent, power-on, secure write protect, etc.)
  ○ etc.

---

JEDEC Standard No. 220G  
Page 224