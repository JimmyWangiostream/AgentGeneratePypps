# 12.4.7 RPMB Operations

## 12.4.7.1 Request Type Message Delivery

• An RPMB region can process only one RPMB operation at any time.
  ○ An initiator sends a request type message to RPMB well known logical unit to request the execution of an operation.

• To deliver a request type message, the initiator sends a SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field is set to ECh (i.e., the JEDEC Universal Flash Storage) and indicating the target RPMB region in the SECURITY PROTOCOL SPECIFIC field.

• For an authenticated data write request, the data to be written into the RPMB data area is included in the request message. The maximum data size in a single Authenticated Data Write request is equal to bRPMB_ReadWriteSize × 256 bytes in Normal RPMB and bRPMB_ReadWriteSize × 4K bytes in Advanced RPMB; multiple Authenticated Data Write operations should be executed if the desired data size exceeds this value. The bRPMB_ReadWriteSize value shall be changed to the appropriate value based on RPMB configuration.

• For SECURITY PROTOCOL OUT command, the Flags.W in the COMMAND UPIU is set to one since data is transferred from the host to the device.

• Table 12.21 defines the Expected Data Transfer Length field value in the COMMAND UPIU for the various cases.

## Table 12.21 — Expected Data Transfer Length Value for Request Type Messages

| RPMB Message | Value |  |
|--------------|-------|-------|
|              | Normal RPMB | Adv. RPMB |
| Authentication Key programming request | 512 | 0 |
| Result read request | 512 | N/A |
| Write Counter read request | 512 | N/A |
| Authenticated data read request | 512 | N/A |
| Secure Write Protect Configuration Block write request | 512 | 4096 |
| Secure Write Protect Configuration Block read request | 512 | N/A |
| Authenticated data write request | 512 × Block Count | 4096 × Advanced RPMB Block Count |
| RPMB Purge Enable request | 512 | 0 |
| RPMB Purge Status Read request | 512 | N/A |
| Authenticated Vendor Specific Command Request | 512 × Block Count | 4096 × Advanced RPMB Block Count |
| Authenticated Vendor Specific Command Status Read Request | 512 × Block Count | 4096 × Advanced RPMB Block Count |

NOTE In Normal RPMB mode, Block Count is equal to the data size divided by 256.

• The device indicates to the host that it is ready to receive the request type message sending READY TO TRANSFER UPIU. If the Expected Data Transfer Length is 512 byte, then Data Buffer Offset field shall be set to a value of zero and Data Transfer Count field shall be set to a value of 512.

• The number of bytes requested in a single READY TO TRANSFER UPIU shall not be greater than the value indicated by bMaxDataOutSize attribute. A single READY TO TRANSFER UPIU may request the transfer of one or more RPMB Messages.

---

JEDEC Standard No. 220G
Page 301

# JEDEC Standard No. 220G
Page 302

## 12.4.7.1 Request Type Message Delivery (cont'd)

• In response to each READY TO TRANSFER UPIU, the host delivers the requested portion of the message sending DATA OUT UPIU. See 10.7.13 for details about data transfer.

• To complete the SECURITY PROTOCOL OUT command, the device returns a RESPONSE UPIU with the status.

• Figure 12.3 depicts a request type message delivery. The application client loads the RPMB Message in the Data Out Buffer and indicates the target RPMB Region in SECURITY PROTOCOL SPECIFIC field.

[Figure 12.3 — Request Type Message Delivery

This diagram shows the communication flow between a SCSI Initiator Device and a SCSI Target Device (UFS Device). 

On the left side is the SCSI Initiator Device containing:
- Application Client
- Application Client Task Set
- SECURITY PROTOCOL OUT command details including:
  - I_T_L_Q Nexus
  - CDB: SECURITY PROTOCOL OUT with various parameters
  - OPERATION CODE = B5h
  - SECURITY_PROTOCOL = ECh
  - SECURITY PROTOCOL SPECIFIC = RPMB region
  - INC_512 = 0b
  - TRANSFER LENGTH
  - Task Attribute
  - Data Out Buffer: RPMB Message
  - etc.

On the right side is the SCSI Target Device: UFS Device containing:
- RPMB well known logical unit
- Device Server
- Task Manager
- Task Set with SECURITY PROTOCOL OUT
- RPMB Regions containing:
  - RPMB Region with Authentication Key, Write Counter, Result Register, RPMB Data Area, and Secure Write Protect Configuration Block

An arrow labeled "RPMB Message" connects the two sides, showing the data flow from the initiator to the target device.]

**Figure 12.3 — Request Type Message Delivery**