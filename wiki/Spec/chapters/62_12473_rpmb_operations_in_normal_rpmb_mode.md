# JEDEC Standard No. 220G
Page 305

## 12.4.7.3 RPMB Operations in Normal RPMB Mode

### 12.4.7.3.1 Authentication Key Programming

• The Authentication Key programming is initiated by a SECURITY PROTOCOL OUT command
  
  ○ An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame includes the Request Message Type = 0001h and the Authentication Key.
  
  ○ The device returns GOOD status in status response when Authentication Key programming is completed.

• The Authentication Key programming verification process starts by issuing a SECURITY PROTOCOL OUT command
  
  ○ An initiator sends a SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame contains the Request Message Type = 0005h (Result read request). Note that any request other than the Result read request from any initiator will overwrite the Result register of the RPMB Region.
  
  ○ The device returns GOOD status in status response when the operation result is ready for retrieval.

• An initiator retrieves the operation result by issuing a SECURITY PROTOCOL IN command.
  
  ○ The SECURITY PROTOCOL field is set to ECh and the SECURITY PROTOCOL SPECIFIC field indicates the RPMB region.
  
  ○ Device returns the RPMB data frame containing the Response Message Type = 0100h and the Result code.
  
  ○ If programming of Authentication Key failed then returned result is "Write failure" (0005h). If some other error occurred during Authentication Key programming then returned result is "General failure" (0001h).

Access to RPMB data area is not possible before the Authentication Key is programmed in the corresponding RPMB region. The state of the device can be checked by trying to write/read data to/from the RPMB data area: if the Authentication Key is not programmed then the Result field in the response message will be set to "Authentication Key not yet programmed" (0007h).

# JEDEC Standard No. 220G
Page 306

## 12.4.7.3.1 Authentication Key Programming (cont'd)

[FIGURE: This is a sequence diagram showing the Authentication Key Programming Flow between Host-UCS, Host-UTP, and Device. The diagram shows three main phases:

1. **Authentication Key Programming Request Phase:**
   - Host-UCS sends "Authentication key programming request" to Host-UTP
   - Host-UTP sends "SECURITY PROTOCOL OUT" and "COMMAND UPIU" to Device
   - Device responds with "READY TO TRANSFER UPIU" and "DATA OUT UPIU"
   - Host-UTP sends "RESPONSE UPIU" back to Host-UCS
   - Host-UCS receives "RESPONSE"

2. **Result Read Request Phase:**
   - Host-UCS sends "Result read request" to Host-UTP
   - Host-UTP sends "SECURITY PROTOCOL OUT" and "COMMAND UPIU" to Device
   - Device responds with "READY TO TRANSFER UPIU" and "DATA OUT UPIU"
   - Host-UTP sends "RESPONSE UPIU" back to Host-UCS
   - Host-UCS receives "RESPONSE"

3. **Result Read Response Phase:**
   - Host-UCS sends "Result read response" to Host-UTP
   - Host-UTP sends "SECURITY PROTOCOL IN" and "COMMAND UPIU" to Device
   - Device responds with "DATA IN UPIU" and "RESPONSE UPIU"
   - Host-UTP sends "RESPONSE" back to Host-UCS]

**Authentication Key Programming Request**

| Offset | Field Name | Value |
|--------|------------|-------|
| 0:195 | Stuff bytes | 0...00h |
| 196:227 | MAC / Key | Key |
| 228:483 | Data | 0...00h |
| 484:499 | Nonce | 0...00h |
| 500:503 | Write counter | 0...00h |
| 504:505 | Address | 0000h |
| 506:507 | Block Count | 0000h |
| 508:509 | Result | 0000h |
| 510:511 | Req./Resp. | 0001h |

**Result Read Request**

| Offset | Field Name | Value |
|--------|------------|-------|
| 0:195 | Stuff bytes | 0...00h |
| 196:227 | MAC / Key | 0...00h |
| 228:483 | Data | 0...00h |
| 484:499 | Nonce | 0...00h |
| 500:503 | Write counter | 0...00h |
| 504:505 | Address | 0000h |
| 506:507 | Block Count | 0000h |
| 508:509 | Result | 0000h |
| 510:511 | Req./Resp. | 0000h |

**Result Read Response**

| Offset | Field Name | Value |
|--------|------------|-------|
| 0:195 | Stuff bytes | 0...00h |
| 196:227 | MAC / Key | 0...00h |
| 228:483 | Data | 0...00h |
| 484:499 | Nonce | 0...00h |
| 500:503 | Write counter | 0000 0000h |
| 504:505 | Address | 0000h |
| 506:507 | Block Count | 0000h |
| 508:509 | Result | Result code |
| 510:511 | Req./Resp. | 0100h |

**Figure 12.5 — Authentication Key Programming Flow**

# 12.4.7.3.2 Read Counter Value

• The Read Counter Value sequence is initiated by a SECURITY PROTOCOL OUT command.
  ○ An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame includes the Request Message Type = 0002h and the Nonce.

• When a GOOD status in the status response is received, the write counter value is retrieved sending a SECURITY PROTOCOL IN command.
  ○ An initiator sends the SECURITY PROTOCOL IN command with the SECURITY PROTOCOL field is set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field.
  ○ The device returns a RPMB data frame with Response Message Type = 0200h, a copy of the Nonce received in the request, the Write Counter value, the MAC and the Result.

If reading of the counter value fails then returned result is "Read failure" (0006h/0086h).
If some other error occurs then Result is "General failure" (0001h/0081h).
If counter has expired also bit 7 is set to 1 in returned results.

[THIS IS DIAGRAM: A sequence diagram showing communication flow between Host-UCS, Host-UTP, and Device for reading counter values. The diagram shows:

1. First exchange:
   - Host-UCS sends "Write Counter read request" via SECURITY PROTOCOL OUT
   - Commands flow through COMMAND UPIU, READY TO TRANSFER UPIU, DATA OUT UPIU
   - Device responds via RESPONSE UPIU and RESPONSE

2. Second exchange:
   - Host-UCS sends "Write Counter read response" via SECURITY PROTOCOL IN
   - Commands flow through COMMAND UPIU, DATA IN UPIU
   - Device responds via RESPONSE UPIU and RESPONSE

The diagram includes two data tables showing the structure of Write Counter Read Request and Write Counter Read Response with their respective offsets, field names, and values.]

**Figure 12.6 — Read Counter Value Flow**

---
*JEDEC Standard No. 220G*  
*Page 307*

# JEDEC Standard No. 220G
## Page 308

### 12.4.7.3.3 Authenticated Data Write

• The Authenticated Data Write sequence is initiated by a SECURITY PROTOCOL OUT command.

  ○ An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB message is composed of one or more RPMB message data frames, each of which includes: Request Message Type = 0003h, Block Count, Address, Write Counter, Nonce, Data and MAC.

  ○ When the device receives the RPMB message, it first checks whether the write counter has expired. If the write counter is expired then the device sets the Result to "Write failure, write counter expired" (0085h). No data is written to the RPMB data area.

  ○ Next the address is checked. If the Address value is equal to or greater than the size of target RPMB region which is defined as bRPMBRegion0Size – bRPMBRegion3Size parameter value in the RPMB Unit Descriptor, then the Result is set to "Address failure" (0004h). No data is written to the RPMB data area.

  ○ If the Address value plus the Block Count value is greater than the size of target RPMB region which is defined as bRPMBRegion0Size – bRPMBRegion3Size parameter value, then the Result is set to "Address failure" (0004h). No data is written to the RPMB data area.

  ○ If the Block Count indicates a value greater than bRPMB_ReadWriteSize, then the authenticated data write operation fails and the Result is set to "General failure" (0001h).

  ○ If the write counter was not expired then the device calculates the MAC of request type, block count, write counter, address and data, and compares this with the MAC in the request. If the two MAC's are different, then the device sets the Result to "Authentication failure" (0002h). No data is written to the RPMB data area.

  ○ If the MAC in the request and the calculated MAC are equal then the device compares the write counter in the request with the write counter stored in the device. If the two counters are different then the device sets the Result to "Counter failure" (0003h). No data is written to the RPMB data area.

  ○ If the MAC and write counter comparisons are successful then the write request is considered to be authenticated. The data is written to the address indicated in the request.

  ○ The write counter is incremented by one if the write operation is successfully executed.

  ○ If write fails then returned result is "Write failure" (0005h).

  ○ If some other error occurs during the write procedure then returned result is "General failure" (0001h).

  ○ In an authenticated data write request with Block Count greater than one

    ▪ the MAC is included only in the last RPMB message data frame. The MAC field is zero in all previous data frames. The device behavior is undefined if a MAC field is non-zero in any but the last RPMB message data frame.

    ▪ In each data frame, the write counter indicates the current counter value, the address is the start address of the full access (not address of the individual logical block) and the block count is the total count of the blocks (not the block numbers).

# JEDEC Standard No. 220G
Page 309

## 12.4.7.3.3 Authenticated Data Write (cont'd)

○ When the authenticated data write operation is completed, the device may return GOOD status in response to the SECURITY PROTOCOL OUT command regardless of whether the Authenticated data write was successful or not.

• The authenticated data write verification process starts by issuing a SECURITY PROTOCOL OUT command.

  ○ An initiator sends a SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame contains the Request Message Type = 0005h (Result read request). Note that any request other than the Result read request from any initiator will overwrite the Result register of the RPMB Region.

  ○ The device returns GOOD status when the operation result is ready for retrieval.

• An initiator retrieves the operation result by issuing a SECURITY PROTOCOL IN command.

  ○ The SECURITY PROTOCOL field is set to ECh and the SECURITY PROTOCOL SPECIFIC field indicates the RPMB region.

• Device returns the RPMB data frame containing the Response Message Type = 0300h, the counter value (incremented if the write operation is successfully executed), a copy of the Nonce received in the request, the address received in the Authenticated data write request, the MAC and result of the authenticated data write operation.

# JEDEC Standard No. 220G
Page 310

## 12.4.7.3.3 Authenticated Data Write (cont'd)

[THIS IS DIAGRAM: A sequence diagram showing communication flow between Host - UCS, Host - UTP, and Device for Authenticated Data Write Request. The diagram shows three main phases:

1. **Authenticated data write request**
   - SECURITY PROTOCOL OUT from Host-UCS to Device
   - COMMAND UPIU from Host-UTP to Device
   - Loop: READY TO TRANSFER UPIU ← DATA OUT UPIU
   - RESPONSE ← RESPONSE UPIU

2. **Result read request**
   - SECURITY PROTOCOL OUT from Host-UCS to Device
   - COMMAND UPIU from Host-UTP to Device
   - READY TO TRANSFER UPIU ← DATA OUT UPIU
   - RESPONSE ← RESPONSE UPIU

3. **Result read response**
   - SECURITY PROTOCOL IN from Host-UCS to Device
   - COMMAND UPIU from Host-UTP to Device
   - DATA IN UPIU ←
   - RESPONSE ← RESPONSE UPIU]

### Authenticated Data Write Request
| Offset | Field Name | Value |
|--------|------------|-------|
| 0:195 | Stuff bytes | 0...00h |
| 196:227 | MAC / Key | MAC from the host |
| 228:483 | Data | Data |
| 484:499 | Nonce | Nonce from the Host |
| 500:503 | Write counter | Current Counter value |
| 504:505 | Address | Address |
| 506:507 | Block Count | Number of 256B blocks |
| 508:509 | Result | 0000h |
| 510:511 | Req./Resp. | 0003h |

### Result Read Request
| Offset | Field Name | Value |
|--------|------------|-------|
| 0:195 | Stuff bytes | 0...00h |
| 196:227 | MAC / Key | 0...00h |
| 228:483 | Data | 0...00h |
| 484:499 | Nonce | 0...00h |
| 500:503 | Write counter | 0...00h |
| 504:505 | Address | 0000h |
| 506:507 | Block Count | 0000h |
| 508:509 | Result | 0000h |
| 510:511 | Req./Resp. | 0005h |

### Result Read Response
| Offset | Field Name | Value |
|--------|------------|-------|
| 0:195 | Stuff bytes | 0...00h |
| 196:227 | MAC / Key | MAC from the device |
| 228:483 | Data | 0...00h |
| 484:499 | Nonce | Copy of the Nonce |
| 500:503 | Write counter | New Counter value |
| 504:505 | Address | Address |
| 506:507 | Block Count | 0000h |
| 508:509 | Result | Result code |
| 510:511 | Req./Resp. | 0300h |

**Note 1** The Write Counter is incremented only if the operation was successfully completed.

**Figure 12.7 — Authenticated Data Write Flow**

# 12.4.7.3.4 Authenticated Data Read

• The Authenticated Data Read sequence is initiated by a SECURITY PROTOCOL OUT command.

    ○ An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame includes the Request Message Type = 0004h, the nonce, the data address, and the block count.

    ○ When the device receives this request it first checks the address. If the Address value is equal to or greater than the size of target RPMB region which is defined as bRPMBRegion0Size – bRPMBRegion3Size parameter value in the RPMB Unit Descriptor, then Result is set to "Address failure" (0004h/0084h). The data read is not valid.

    ○ If the Address value plus the Block Count value is greater than the size of target RPMB region which is defined as bRPMBRegion0Size – bRPMBRegion3Size parameter value, then the Result is set to "Address failure" (0004h/0084h). No data is read from the RPMB data area.

    ○ If the Block Count indicates a value greater than bRPMB_ReadWriteSize, then the Authenticated Data Read operation fails and the Result is set to "General failure" (0001h).

    ○ After successful data fetch the MAC is calculated from response type, nonce, address, data and result. If the MAC calculation fails then returned result is "Authentication failure" (0002h/0082h).

• If the SECURITY PROTOCOL OUT command completes with GOOD status, data can be retrieved sending a SECURITY PROTOCOL IN command.

    ○ An initiator sends the SECURITY PROTOCOL IN command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field.

    ○ The device returns a RPMB message with Response Message Type = 0400h, the block count, a copy of the nonce received in the request, the address received in the Authenticated data read request, the data, the MAC and the result.

    ○ In an authenticated data read response with Block Count greater than one,
        ▪ the MAC is included only in the last RPMB message data frame. The MAC field is zero in all previous data frames.
        ▪ In each data frame, the Nonce contains a copy of the received nonce, the address is the start address of the full access (not address of the individual logical block) and the block count is the total count of the blocks (not the sequence number of blocks).

• When the authenticated data read operation is completed, the device may return GOOD status in response to the SECURITY PROTOCOL IN command regardless of whether the Authenticated data read was successful or not.

• If data fetch from addressed location inside device fails then returned result is "Read failure" (0006h/0086h). If some other error occurs during the read procedure then returned result is "General failure" (0001h/0081h).

---

JEDEC Standard No. 220G  
Page 311

# JEDEC Standard No. 220G
Page 312

## 12.4.7.3.4 Authenticated Data Read (cont'd)

[THIS IS FIGURE: Authenticated Data Read Flow diagram showing communication between Host-SCSI, Host-UTP, and Device-UTP with two main sections - Request and Response flows]

The diagram shows:

**Request Flow:**
- Host-SCSI sends "Authenticated data read request" via SECURITY PROTOCOL OUT
- Host-UTP sends COMMAND UPIU, READY TO TRANSFER UPIU, and DATA OUT UPIU
- Device-UTP responds with RESPONSE UPIU

**Response Flow:**
- Host-SCSI sends "Authenticated data read response" via SECURITY PROTOCOL IN
- Host-UTP sends COMMAND UPIU
- Device-UTP responds with DATA IN UPIU (in a Loop) and RESPONSE UPIU

### Authenticated Data Read Request

| Offset | Field Name | Value |
|--------|------------|--------|
| 0:195 | Stuff bytes | 0..00h |
| 196:227 | MAC / Key | 0..00h |
| 228:483 | Data | 0..00h |
| 484:499 | Nonce | Nonce from the host |
| 500:503 | Write counter | 0..00h |
| 504:505 | Address | Address |
| 506:507 | Block Count | Number of 256B blocks |
| 508:509 | Result | 0000h |
| 510:511 | Req./Resp. | 0004h |

### Authenticated Data Read Response

| Offset | Field Name | Value |
|--------|------------|--------|
| 0:195 | Stuff bytes | 0..00h |
| 196:227 | MAC / Key | MAC from the device |
| 228:483 | Data | Data |
| 484:499 | Nonce | Copy of the Nonce |
| 500:503 | Write counter | 0..00h |
| 504:505 | Address | Address |
| 506:507 | Block Count | Number of 256B blocks |
| 508:509 | Result | Result code |
| 510:511 | Req./Resp. | 0400h |

**Figure 12.8 — Authenticated Data Read Flow**

# JEDEC Standard No. 220G
Page 313

## 12.4.7.3.5 Authenticated Secure Write Protect Configuration Block Write

• Authenticated Secure Write Protect Configuration Block write operation is supported by RPMB region 0 only. If Authenticated Secure Write Protect Configuration Block write operation is issued to the RPMB region other than RPMB region 0, then returned result is "General failure" (0001h/0081h).

• The Authenticated Secure Write Protect Configuration Block write sequence is initiated by a SECURITY PROTOCOL OUT command.

  ○ An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region 0 in the SECURITY PROTOCOL SPECIFIC field.

  ○ If the INC_512 bit and TRANSFER LENGTH field are not set to zero and 512 respectively, then the command shall be terminated with CHECK CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to INVALID FIELD IN CDB.

  ○ The SECURITY PROTOCOL OUT command delivers a single RPMB message data frame which contains the Secure Write Protect Configuration Block in the Data field. The Secure Write Protect Configuration Block is specific of the logical unit indicated by the LUN field (byte 228 of the data frame).

  ○ The other fields of RPMB data frame are set as specified in the following: Request Message Type = 0006h, Result = 0000h, Block Count = 0001h, Address = 0000h, Write Counter = current counter value, Nonce from the host, and MAC = see 12.4.4.2.

  ○ When the device receives the RPMB message data frame, it first checks whether the write counter has expired. If the write counter is expired then the device sets the result to "Write failure, write counter expired" (0085h). The Secure Write Protect Configuration Block is not updated.

  ○ If the write counter was not expired, then the device calculates the MAC of request type, block count, write counter, address and data, and compares this with the MAC in the request. If the two MAC's are different, then the device sets the result to "Authentication failure" (0002h). The Secure Write Protect Configuration Block is not updated.

  ○ If the MAC in the request and the calculated MAC are equal, then the device compares the write counter in the request with the write counter stored in the device. If the two counters are different then the device sets the result to "Counter failure" (0003h). The Secure Write Protect Configuration Block is not updated.

  ○ If the MAC and write counter comparisons are successful then the write request is considered to be authenticated.

  ○ If the LUN field indicates a logical unit with eLUWriteProtect set to a value different from zero, then the device sets the result to "Secure Write Protection not applicable" (000Ah). The Secure Write Protect Configuration Block is not updated.

# JEDEC Standard No. 220G
Page 314

## 12.4.7.3.5 Authenticated Secure Write Protect Configuration Block Write (cont'd)

○ The device sets the result to "Invalid Secure Write Protect Block Configuration parameter" (0009h) and it does not update the Secure Write Protect Configuration Block if one or more of the following conditions occurs.

▪ the LUN field is invalid: greater than the value specified by bMaxNumberLU or if the logical unit is not enabled (bLUEnable=00h).
▪ the DATA LENGTH is set to a value different from the following ones: 0, 16, 32, 48, 64.
▪ the LOGICAL BLOCK ADDRESS in a Secure Write Protect entry exceeds the logical unit capacity.
▪ the LOGICAL BLOCK ADDRESS plus the NUMBER OF LOGICAL BLOCKS in a Secure Write Protect entry exceeds the logical unit capacity.
▪ two or more Secure Write Protect entries specify overlapping areas,
▪ with this request, the number of Secure Write Protect areas set in the entire device is increased to a value greater than what indicated by bNumSecureWPArea.

○ If some other error occurs during the write procedure then returned result is "Secure Write Protect Configuration Block access failure" (0008h). The Secure Write Protect Configuration Block is not updated.

○ If no error occurred, then the Secure Write Protect Configuration Block is updated overwriting the former configuration and the write counter is incremented by one.

• The device may return GOOD status in response to the SECURITY PROTOCOL OUT command regardless of whether the Authenticated Secure Write Protect Configuration Block Write was successful or not.

• The successfulness of the programming of the data can be checked by retrieving the result register of the RPMB.

• The verification process starts by issuing a SECURITY PROTOCOL OUT command.

○ An initiator sends a SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region 0 in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame contains the Request Message Type = 0005h (Result read request). Note that any request other than the Result read request from any initiator will overwrite the Result register of the RPMB Region.

○ The device returns "Good" status when the operation result is ready for retrieval.

• An initiator retrieves the operation result by issuing a SECURITY PROTOCOL IN command.

• The SECURITY PROTOCOL field is set to ECh and the SECURITY PROTOCOL SPECIFIC field indicates the RPMB region.

• Device returns the RPMB data frame containing the Response Message Type = 0600h, the incremented counter value, a copy of the Nonce received in the request, the MAC and result of the Authenticated Secure Write Protect Configuration Block write operation.

# JEDEC Standard No. 220G
Page 315

## 12.4.7.3.5 Authenticated Secure Write Protect Configuration Block Write (cont'd)

[THIS IS FIGURE: A sequence diagram showing the Authenticated Secure Write Protect Configuration Block Write Flow between Host-UCS, Host-UTP, and Device. The diagram shows three main phases:

1. **Secure Write Protect Configuration Block write request** from Host-UCS to Device via UTP, with SECURITY PROTOCOL OUT, COMMAND UPIU, READY TO TRANSFER UPIU, DATA OUT UPIU, and RESPONSE UPIU exchanges.

2. **Result read request** from Host-UCS to Device via UTP, with similar UPIU exchanges.

3. **Result read response** from Device to Host-UCS via UTP, with SECURITY PROTOCOL IN, COMMAND UPIU, DATA IN UPIU, and RESPONSE UPIU exchanges.

The diagram includes three data tables on the right side:]

### Secure Write Protect Configuration Block write request
| Offset | Field Name | Value |
|--------|------------|-------|
| 0..195 | Stuff bytes | 0...00h |
| 196.227 | MAC / Key | MAC from the host |
| 228.483 | Data | LUN, DATA LENGTH, Secure Write Protect Entries |
| 484.499 | Nonce | Nonce from the host |
| 500.503 | Write counter | Current Counter value |
| 504.505 | Address | 0000h |
| 506.507 | Block Count | 0001h |
| 508.509 | Result | 0000h |
| 510.511 | Req./Resp. | 0006h |

### Result Read Request
| Offset | Field Name | Value |
|--------|------------|-------|
| 0.195 | Stuff bytes | 0...00h |
| 196.227 | MAC / Key | 0...00h |
| 228.483 | Data | 0...00h |
| 484.499 | Nonce | 0...00h |
| 500.503 | Write counter | 0...00h |
| 504.505 | Address | 0000h |
| 506.507 | Block Count | 0000h |
| 508.509 | Result | 0000h |
| 510.511 | Req./Resp. | 0005h |

### Result Read Response
| Offset | Field Name | Value |
|--------|------------|-------|
| 0.195 | Stuff bytes | 0...00h |
| 196.227 | MAC / Key | MAC from the device |
| 228.483 | Data | 0...00h |
| 484.499 | Nonce | Copy of the Nonce |
| 500.503 | Write counter | New Counter value |
| 504.505 | Address | 0000h |
| 506.507 | Block Count | 0000h |
| 508.509 | Result | Result code |
| 510.511 | Req./Resp. | 0600h |

**NOTE 1** The Write Counter is incremented only if the operation was successfully completed.

**Figure 12.9 — Authenticated Secure Write Protect Configuration Block Write Flow**

# JEDEC Standard No. 220G
## Page 316

### 12.4.7.3.6 Authenticated Secure Write Protect Configuration Block Read

• Authenticated Secure Write Protect Configuration Block read operation is supported by RPMB region 0 only. If Authenticated Secure Write Protect Configuration Block read operation is issued to the RPMB region other than RPMB region 0, then returned result is "General failure" (0001h/0081h).

• The Authenticated Secure Write Protect Configuration Block Read sequence is initiated by a SECURITY PROTOCOL OUT command.

    ○ An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region 0 in the SECURITY PROTOCOL SPECIFIC field.

    ○ If the INC_512 bit and TRANSFER LENGTH field are not set to zero and 512 respectively, then the command shall be terminated with CHECK_CONDITION status with the sense key set to ILLEGAL REQUEST and the additional sense code set to INVALID FIELD IN CDB.

    ○ The SECURITY PROTOCOL OUT command delivers a single RPMB message data frame which contains in the Data field a LUN value (byte 228 of the data frame). The Secure Write Protect Configuration Block that will be returned is specific of the logical unit indicated by the LUN field.

    ○ The RPMB data frame delivered from the host to the device includes the Request Message Type = 0007h, Block Count=0001h, Address=0000h, the Data and Nonce. In this request, the LUN is the only relevant byte of the Data field, all other bytes shall be considered reserved and they shall be ignored.

    ○ If the LUN field is not valid, then the device sets the result to "Invalid Secure Write Protect Block Configuration parameter" (0009h/0089h). The LUN field is invalid if it is greater than the value specified by bMaxNumberLU or if the logical unit is not enabled (bLUEnable=00h).

    ○ If the LUN field indicates a logical unit with bLUWriteProtect set to a value different from zero, then the device sets the result to "Secure Write Protection not applicable" (000Ah/008Ah).

    ○ After successful fetch of the Secure Write Protect Configuration Block, the MAC is calculated from response type, nonce, address, data and result. If the MAC calculation fails then returned result is "Authentication failure" (0002h/0082h).

• If the SECURITY PROTOCOL OUT command completes with GOOD status, then the Secure Write Protect Configuration Block can be retrieved sending a SECURITY PROTOCOL IN command.

    ○ An initiator sends the SECURITY PROTOCOL IN command with SECURITY PROTOCOL field set to ECh, indicating the RPMB region 0 in the SECURITY PROTOCOL SPECIFIC field, and in which INC_512 bit and ALLOCATION LENGTH field indicate 512 bytes.

• The device returns a RPMB data frame with Response Message Type = 0700h, the block count, a copy of the nonce received in the request, the contents of the Secure Write Protect Configuration Block in the Data field, the MAC and the result

• If data fetch from addressed location inside device fails or some other error occurs during the read procedure then returned result is "Secure Write Protect Configuration Block access failure" (0008b/0088h).

# JEDEC Standard No. 220G
## Page 317

### 12.4.7.3.6 Authenticated Secure Write Protect Configuration Block Read (cont'd)

[THIS IS FIGURE: A sequence diagram showing the Authenticated Secure Write Protect Configuration Block Read Flow between Host-SCSI, Host-UTP, and Device-UTP. The diagram shows message flows including:

1. Secure Write Protect Configuration Block Read Request from Host-SCSI to Host-UTP
2. SECURITY PROTOCOL OUT and COMMAND UPIU from Host-UTP to Device-UTP
3. READY TO TRANSFER UPIU from Device-UTP to Host-UTP
4. DATA OUT UPIU from Host-UTP to Device-UTP
5. RESPONSE UPIU from Device-UTP to Host-UTP
6. RESPONSE back to Host-SCSI
7. Secure Write Protect Configuration Block Read Response from Host-UTP to Host-SCSI
8. SECURITY PROTOCOL IN and COMMAND UPIU from Host-UTP to Device-UTP
9. DATA IN UPIU from Device-UTP to Host-UTP
10. RESPONSE UPIU from Device-UTP to Host-UTP
11. RESPONSE back to Host-SCSI]

**Secure Write Protect Configuration Block Read Request**

| Offset | Field Name | Value |
|--------|------------|--------|
| 0:195 | Stuff bytes | 0...00h |
| 196:227 | MAC / Key | 0...00h |
| 228:483 | Data | LUN, 0...00h |
| 484:499 | Nonce | Nonce from the host |
| 500:503 | Write counter | 0...00h |
| 504:505 | Address | 0...00h |
| 506:507 | Block Count | 0001h |
| 508:509 | Result | 0000h |
| 510:511 | Req./Resp. | 0007h |

**Secure Write Protect Configuration Block Read Response**

| Offset | Field Name | Value |
|--------|------------|--------|
| 0:195 | Stuff bytes | 0...00h |
| 196:227 | MAC / Key | MAC from the device |
| 228:483 | Data | LUN, DATA LENGTH, Secure Write Protect Entries |
| 484:499 | Nonce | Copy of the Nonce |
| 500:503 | Write counter | 0...00h |
| 504:505 | Address | 0...00h |
| 506:507 | Block Count | 0001h |
| 508:509 | Result | Result code |
| 510:511 | Req./Resp. | 0700h |

**Figure 12.10 — Authenticated Secure Write Protect Configuration Block Read Flow**

# JEDEC Standard No. 220G
Page 318

## 12.4.7.3.7 RPMB Purge Enable

The RPMB Purge Enable Request sequence is initiated by a SECURITY PROTOCOL OUT command. The sequence is completed by a SECURITY PROTOCOL IN command. This pair of commands is the RPMB Purge Enable Request operation.

• An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame includes the Request Message Type = 0008h (RPMB Purge Enable Request), Write Counter, Nonce, and MAC.
  ○ When the device receives the Request message (RPMB Purge Enable Request), it first checks whether the write counter has expired. If the write counter is expired then the device sets the Result to "Write failure, write counter expired" (0085h) and the RPMB Purge is not initiated.
  ○ If the Write Counter was not expired, then the device calculates the MAC of request and compares this with the MAC in the request. If the two MAC's are different, then the device sets the Result to "Authentication failure" (0002h) and RPMB Purge operation is not initiated.
  ○ If the Write Counter and MAC comparisons are successful, then the RPMB Purge Enable Request is considered to be authenticated and the RPMB Purge operation on the target RPMB Region is initiated.
  ○ When the device is ready to start purge the RPMB, the device can return a GOOD status in response to the SECURITY PROTOCOL OUT command, regardless of whether the RPMB purge operation was successful or not. The success or failure of RPMB purge can be known by the operation of RPMB Purge Status Read.

• When a GOOD status in the status response is received, the RPMB operation result is retrieved by sending a SECURITY PROTOCOL IN command.
  ○ The initiator sends the SECURITY PROTOCOL IN command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field.
  ○ The device returns an RPMB data frame with the Request Message Type = 0800h (RPMB Purge Enable Response), Write Counter, Nonce, and MAC.
  ○ On the successful completion of the RPMB Purge Enable Request Message, the device shall update the write counter in the RPMB Purge Read Enable Response.

• If a GOOD status is not returned, a general failure error should be reported.

# 12.4.7.3.7 RPMB Purge Enable (cont'd)

[**Figure Description**: This is a sequence diagram showing the RPMB Purge Enable Flow between Host-UCS, Host-UTP, and Device. The diagram shows the communication flow with arrows indicating message direction and includes two detailed data tables showing the structure of RPMB Purge Enable Request and Response messages.]

**RPMB Purge Enable Request**

| Offset | Field Name | Value |
|--------|------------|-------|
| 0-195 | Stuff bytes | 00h |
| 196-227 | MAC / Key | MAC From Host |
| 228-483 | Data | 00...00h |
| 484-499 | Nonce | Current Nonce |
| 500-503 | Write Counter | Current Counter value |
| 504-505 | Address | 0000h |
| 506-507 | Block Count | 0001h |
| 508-509 | Result | 0000h |
| 510-511 | Req./Resp. | 000Bh |

**RPMB Purge Enable Response**

| Offset | Field Name | Value |
|--------|------------|-------|
| 0-195 | Stuff bytes | 00h |
| 196-227 | MAC / Key | MAC From Device |
| 228-483 | Data | 00...00h |
| 484-499 | Nonce | Copy of the Nonce |
| 500-503 | Write Counter | New Counter value (If purge enable successfully) |
| 504-505 | Address | 0000h |
| 506-507 | Block Count | 0001h |
| 508-509 | Result | Result Code |
| 510-511 | Req./Resp. | 0B00h |

**Figure 12.11 — RPMB Purge Enable Flow**

---

JEDEC Standard No. 220G  
Page 319

# 12.4.7.3.8 RPMB Purge Status Read

RPMB Purge Status Read Request sequence is initiated by a SECURITY PROTOCOL OUT command. The sequence is completed by a SECURITY PROTOCOL IN command. This pair of commands is the RPMB Purge Status Read Request operation.

• An initiator sends a SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame contains the Request Message Type = 0009h (RPMB Purge Status Read Request) and Nonce.
  ○ Note that any request other than the RPMB Purge Status Read Request from any initiator will overwrite the Result register of the RPMB Region.
  
  ○ The device returns GOOD status when the operation result is ready for retrieval.

• When a GOOD status in the status response is received, the RPMB purge status is retrieved by sending a SECURITY PROTOCOL IN command.
  ○ An initiator sends the SECURITY PROTOCOL IN command with the SECURITY PROTOCOL field is set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field.
  
  ○ The device returns a RPMB data frame with Response Message Type = 0900h (RPMB Purge Status Read Response), a copy of the Nonce received in the request, the MAC and the Result.
  
  ○ Supported purge status value are as follows, reported in the RPMB Purge Response Packet:
    ▪ 00 - RPMB Purge not initiated (reset value)
    ▪ 01 - RPMB Purge in progress
    ▪ 02 - RPMB Purge successfully completed
    ▪ 03 – RPMB Purge general failure

• If a GOOD status is not returned, a general failure error should be reported.

[Flow diagram showing RPMB Purge Status Read Request sequence between Host-UCS, Host-UTP, and Device with following components:

RPMB Purge Status Read Request table:
| Offset | Field Name | Value |
|--------|------------|-------|
| 0-195 | Stuff Bytes | 00h |
| 196-197 | MAC / Key | 00_00h |
| 198-481 | Data | 00_00h |
| 482-499 | Nonce | Nonce Value |
| 500-503 | Write Counter | 00_00h |
| 504-505 | Address | 0000h |
| 506-507 | Block Count | 0001h |
| 508-509 | Result | 0000h |
| 510-511 | Req./Resp. | 0009h |

RPMB Purge Status Read Response table:
| Offset | Field Name | Value |
|--------|------------|-------|
| 0-195 | Stuff Bytes | 00h |
| 196-197 | MAC / Key | MAC From Device |
| 198-481 | Data | RPMB Purge Response |
| 482-499 | Nonce | Copy of the Nonce |
| 500-503 | Write Counter | 00_00h |
| 504-505 | Address | 0000h |
| 506-507 | Block Count | 0001h |
| 508-509 | Result | Result Code |
| 510-511 | Req./Resp. | 0900h |

The diagram shows message flow with SECURITY PROTOCOL OUT/IN commands, COMMAND UPIU, READY TO TRANSFER UPIU, DATA OUT/IN UPIU, and RESPONSE UPIU between the three entities.]

**Figure 12.12 — RPMB Purge Status Read Flow**

---
JEDEC Standard No. 220G  
Page 320

# 12.4.7.3.9 Authenticated Vendor Specific Command Request

Authenticated Vendor Specific Command allows the vendor command & response to be tunneled to the device via RPMB authentication mechanism.

The Authenticated Vendor Specific Command Request sequence is initiated by a SECURITY PROTOCOL OUT command.

An initiator sends the SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame includes the Request Message Type = 0010h (Authenticated Vendor Specific Command Request), Block Count, Write Counter, Nonce, data and MAC.

• When the device receives the Request message (Authenticated Vendor Specific Command Request), it first checks whether the write counter has expired. If the write counter is expired then the device sets the Result to "Write failure, write counter expired" (0085h) and the Vendor Specific Command operation is not initiated.

• If the Write Counter was not expired, then the device calculates the MAC of request and compares this with the MAC in the request. If the two MAC's are different, then the device sets the Result to "Authentication failure" (0002h) and Vendor Specific Command operation is not initiated.

• If the Write Counter and MAC comparisons are successful, then the Vendor Specific Command operation Request is considered to be authenticated and the operation is initiated.

• When the device is ready to start the vendor specific command, the device can return a GOOD status in response to the SECURITY PROTOCOL OUT command, regardless of whether the vendor specific command was successful or not. The success or failure of vendor specific command request can be known by the operation of Authenticated Vendor Specific Command Response Read Request.

• On the successful completion of the Vendor Specific Command Request Message, the device shall increment the write counter.

When a GOOD status in the status response is received, the result of the vendor specific command request is retrieved by sending a SECURITY PROTOCOL OUT command.

If a GOOD status is not returned, a general failure error should be reported.

• In an Authenticated Vendor Specific Command Request with Block Count greater than one,
  ○ the MAC is included only in the last RPMB message data frame. The MAC field is zero in all previous data frames. The device behavior is undefined if a MAC field is non-zero in any but the last RPMB message data frame.
  
  ○ In each data frame, the write counter indicates the current counter value, the block count is the total count of the blocks (not the block numbers).

---
JEDEC Standard No. 220G  
Page 321

# 12.4.7.3.9 Authenticated Vendor Specific Command Request (cont'd)

[THIS IS FIGURE: A flow diagram showing the Authenticated Vendor Specific Command Request Flow between Host-UCS, Host-UTP, and Device. The diagram shows three main phases:

1. Initial command flow from Host-UCS through Security Protocol Out, Command UPIU, Ready to Transfer UPIU, and Data Out UPIU, with a response back through Response UPIU
2. Status read request phase with Security Protocol Out, Command UPIU, Ready to Transfer UPIU, Data Out UPIU, and Response through Response UPIU
3. Status response phase with Security Protocol In, Command UPIU, Data In UPIU, and Response through Response UPIU

The diagram includes three data tables on the right side:]

**Authenticated Vendor Specific Command Request**
| Offset | Field Name | Value |
|--------|------------|-------|
| 0-195 | Stuff bytes | 0...00h |
| 196-227 | MAC/Key | Mac from the host |
| 228-483 | Data | Vendor Specific Command + Data |
| 484-499 | Nonce | Nonce from the host |
| 500-503 | Write counter | Current Counter value |
| 504-505 | Address | 0000h |
| 506-507 | Block Count | Number of 256B blocks |
| 508-509 | Result | 0000h |
| 510-511 | Req./Resp. | 0010h |

**Authenticated Vendor Specific Command Status Read Request**
| Offset | Field Name | Value |
|--------|------------|-------|
| 0-195 | Stuff bytes | 0...00h |
| 196-227 | MAC/Key | 0...00h |
| 228-483 | Data | 0...00h |
| 484-499 | Nonce | 0...00h |
| 500-503 | Write counter | 0...00h |
| 504-505 | Address | 0000h |
| 506-507 | Block Count | Number of 256B blocks |
| 508-509 | Result | 0000h |
| 510-511 | Req./Resp. | 0011h |

**Authenticated Vendor Specific Command Status Response**
| Offset | Field Name | Value |
|--------|------------|-------|
| 0-195 | Stuff bytes | 0...00h |
| 196-227 | MAC/Key | Mac from the device |
| 228-483 | Data | Vendor Specific Response + Data |
| 484-499 | Nonce | Copy of the Nonce |
| 500-503 | Write counter | New Counter value |
| 504-505 | Address | 0000h |
| 506-507 | Block Count | Number of 256B blocks |
| 508-509 | Result | Status |
| 510-511 | Req./Resp. | 1100h |

**Figure 12.13 — Authenticated Vendor Specific Command Request Flow**

---
JEDEC Standard No. 220G
Page 322

# 12.4.7.3.10 Authenticated Vendor Specific Command Status Read Request

Authenticated Vendor Specific Command Status Read Request sequence is initiated by a SECURITY PROTOCOL OUT command. The sequence is completed by a SECURITY PROTOCOL IN command. This pair of commands is the Authenticated Vendor Specific Command Status Read Operation.

An initiator sends a SECURITY PROTOCOL OUT command with SECURITY PROTOCOL field set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field. The RPMB data frame contains the Request Message Type = 0011h (Authenticated Vendor Specific Command Read Request), Block Count and Nonce.

• Note that any request other than the Authenticated Vendor Specific Command Response Read Request from any initiator will overwrite the Result register of the RPMB Region.

• The device returns GOOD status when the operation result is ready for retrieval.

When a GOOD status in the status response is received, the Authenticated Vendor Specific Command status is retrieved by sending a SECURITY PROTOCOL IN command.

• An initiator sends the SECURITY PROTOCOL IN command with the SECURITY PROTOCOL field is set to ECh and indicating the RPMB region in the SECURITY PROTOCOL SPECIFIC field.

• The device returns a RPMB data frame with Response Message Type = 1100h (Authenticated Vendor Specific Command Status Response), the Block Count, a copy of the Nonce received in the request, the data, the MAC and the Result.

• In an Authenticated Vendor Specific Command Status Response with Block Count greater than one,
  ○ the MAC is included only in the last RPMB message data frame. The MAC field is zero in all previous data frames.
  ○ In each data frame, the Nonce contains a copy of the received nonce, the block count is the total count of the blocks (not the sequence number of blocks).

• Supported Vendor Command status value are as follows, reported in the Authenticated Vendor Specific Command Response Packet's Result field:
  ▪ 00 – Vendor Specific Command not initiated (reset value)
  ▪ 01 – Vendor Specific Command in progress
  ▪ 02 – Vendor Specific Command completed
  ▪ 03 – Vendor Specific Command general failure

If a GOOD status is not returned, a general failure error should be reported.

---

JEDEC Standard No. 220G  
Page 323

# JEDEC Standard No. 220G
Page 324

## 12.4.7.3.10 Authenticated Vendor Specific Command Status Read Request (cont'd)

[THIS IS FIGURE: A sequence diagram showing communication flow between Host-UCS, Host-UTP, and Device for Authenticated Vendor Specific Command Read Request Flow. The diagram shows multiple exchanges including:

1. Initial "Authenticated Vendor Specific Command Request" from Host-UCS with SECURITY PROTOCOL OUT, followed by COMMAND UPIU, READY TO TRANSFER UPIU, DATA OUT UPIU, and RESPONSE UPIU between Host-UTP and Device.

2. A second "Authenticated Vendor Specific Command Status Read Request" exchange with similar UPIU flow pattern.

3. A third exchange showing SECURITY PROTOCOL IN, COMMAND UPIU, DATA IN UPIU, and RESPONSE UPIU.

On the right side are two tables showing request and response field structures:]

**Authenticated Vendor Specific Command Status Read Request:**
| Offset | Field Name | Value |
|--------|------------|-------|
| 0-195 | Stuff bytes | 0..00h |
| 196-227 | MACKey | 0..00h |
| 228-483 | Data | 0..00h |
| 484-499 | Nonce | 0..00h |
| 500-503 | Write counter | 0..00h |
| 504-505 | Address | 0000h |
| 506-507 | Block Count | Number of 256B blocks |
| 508-509 | Result | 0000h |
| 510-511 | Req./Resp. | 0011h |

**Authenticated Vendor Specific Command Status Response:**
| Offset | Field Name | Value |
|--------|------------|-------|
| 0-195 | Stuff bytes | 0..00h |
| 196-227 | MACKey | Mac from the device |
| 228-483 | Data | Vendor Specific Response + Data |
| 484-499 | Nonce | Copy of the Nonce |
| 500-503 | Write counter | New Counter value |
| 504-505 | Address | 0000h |
| 506-507 | Block Count | Number of 256B blocks |
| 508-509 | Result | Status |
| 510-511 | Req./Resp. | 1100h |

**Figure 12.14 — Authenticated Vendor Specific Command Read Request Flow**