# JEDEC Standard No. 220G
Page 303

## 12.4.7.2 Response Type Message Delivery

• A initiator requests the RPMB well known logical unit to send a response type message to retrieve the result of a previous operation, to retrieve the Write Counter, to retrieve data from the RPMB data area, or to retrieve the contents of a Secure Write Protect Configuration Block.

• To request the delivery of a response type message, the host sends a SECURITY_PROTOCOL_IN command with SECURITY_PROTOCOL field is set to ECh (i.e., the JEDEC Universal Flash Storage) and indicating the RPMB region in the SECURITY_PROTOCOL_SPECIFIC field.

• For an Authenticated Data Read request, the data read from the RPMB data area is included in the response message. The maximum data size in a single Authenticated Data Read request is equal to bRPMB_ReadWriteSize × 256 bytes in Normal RPMB and bRPMB_ReadWriteSize × 4K bytes in Advanced RPMB; multiple Authenticated Data Read operations should be executed if the desired data size exceeds this value. The bRPMB_ReadWriteSize value shall be changed to the appropriate value based on RPMB configuration.

• For SECURITY_PROTOCOL_IN command, the Flags.R in the COMMAND UPIU is set to one since data is transferred from the device to the host.

• Table 12.22 defines the Expected Data Transfer Length field value in the COMMAND UPIU for the various cases.

### Table 12.22 — Expected Data Transfer Length Value for Response Type Messages

| RPMB Message | Value |  |
|---|---|---|
|  | Normal RPMB | Adv. RPMB |
| Authentication Key programming response | 512 | N/A |
| Authenticated data write response | 512 | N/A |
| Secure Write Protect Configuration Block write response | 512 | N/A |
| Write Counter read response | 512 | 0 |
| Secure Write Protect Configuration Block read response | 512 | 4096 |
| Authenticated data read response | 512 × Block Count | 4096 × Advanced RPMB Block Count |
| RPMB Purge Enable response | 512 | N/A |
| RPMB Purge Status Read response | 512 | 4096 |
| Authenticated Vendor Specific Command Response (Advanced RPMB Mods only) | N/A | N/A |
| Authenticated Vendor Specific Command Status Response | 512 × Block Count | 4096 × Advanced RPMB Block Count |

NOTE In Normal RPMB mode, Block Count is equal to the data size divided by 256.

• The device returns the result or data requested in the RPMB message. The RPMB message is delivered by sending one or more DATA IN UPIU in the data phase. A single DATA IN UPIU may deliver one or more RPMB Messages.

• The data size in DATA IN UPIU shall not exceed the value indicated by bMaxDataInSize attribute.

• To complete the SECURITY_PROTOCOL_IN, the device sends a RESPONSE UPIU with the status.

# JEDEC Standard No. 220G
Page 304

## 12.4.7.2 Response Type Message Delivery (cont'd)

• Figure 12.4 depicts a response type message delivery. An application client requests a RPMB Region to transfer the RPMB Message in the Data In Buffer specifying the RPMB Region ID in SECURITY PROTOCOL SPECIFIC field of the CDB.

[THIS IS FIGURE: Diagram showing Response Type Message Delivery between SCSI Initiator Device and SCSI Target Device (UFS Device). 

Left side shows SCSI Initiator Device containing:
- Application Client
- Application Client Task Set
- SECURITY PROTOCOL IN section with details:
  - I_T_L_Q Nexus
  - CDB: SECURITY PROTOCOL IN (
  - OPERATION CODE = A2h
  - SECURITY_PROTOCOL = ECh
  - SECURITY_PROTOCOL SPECIFIC = RPMB region
  - INC_512 = 0h
  - ALLOCATION LENGTH )
  - Task Attribute
  - Data In Buffer: RPMB Message
  - etc.

Right side shows SCSI Target Device: UFS Device containing:
- RPMB well known logical unit with:
  - Device Server
  - Task Manager
  - Task Set with SECURITY PROTOCOL IN
  - RPMB Regions section showing:
    - RPMB Region with Authentication Key, Write Counter, Result Register, RPMB Data Area, and Secure Write Protect Configuration Block
- RPMB Message flow indicated between components]

**Figure 12.4 — Response Type Message Delivery**