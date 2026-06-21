# 10.7.7 TASK MANAGEMENT RESPONSE UPIU

The TASK MANAGEMENT RESPONSE UPIU is sent by the Target device in response to a Task Management Request from the Initiator device. The Task Management Response function closely follows the SCSI Architecture Model [SAM].

If the Target device is processing a task which requires Data-Out data transfer, and it receives a task management request to abort that command, then Target device should stop sending READY TO TRANSFER UPIUs for the command requested to abort. Target device shall wait until it receives all DATA OUT UPIUs related to any outstanding READY TO TRANSFER UPIUs before sending the TASK MANAGEMENT RESPONSE UPIU.

Task management functions that may cause a task abort are: Abort Task, Abort Task Set, Clear Task Set and Logical Unit Reset.

## Table 10.30 — Task Management Response UPIU

| Byte | 0 | 1 | 2 | 3 |
|------|---|---|---|---|
| **TASK MANAGEMENT RESPONSE UPIU** | | | | |
| 0 | xx10 0100b | Flags | LUN | Task Tag |
| 4 | IID | Reserved | EXT_IID | Reserved |
| 5 | | | 6 | 7 |
| | | | Response | Reserved |
| 8 | Total EHS Length (00h) | Reserved | (MSB) | (LSB) |
| 9 | | | 10 | 11 |
| | | | Data Segment Length (0000h) | |
| 12 | (MSB) | | | (LSB) |
| | | 13 | 14 | 15 |
| | | Output Parameter 1 | | |
| 16 | (MSB) | | | (LSB) |
| | | 17 | 18 | 19 |
| | | Output Parameter 2 | | |
| 20 | | 21 | 22 | 23 |
| | | Reserved | | |
| 24 | | 25 | 26 | 27 |
| | | Reserved | | |
| 28 | | 29 | 30 | 31 |
| | | Reserved | | |
| | | Header E2ECRC (omit if HD=0) | | |

---
*JEDEC Standard No. 220G*  
*Page 116*

# JEDEC Standard No. 220G
Page 117

## 10.7.7.1 Basic Header

The first 12 bytes of the TASK MANAGEMENT RESPONSE UPIU contain the Basic Header as described in 10.6.2, Basic Header Format. Specific details are as follows:

**a) Transaction Type**

A type code value of xx10 0100b indicates a TASK MANAGEMENT RESPONSE UPIU.

**b) IID**

This field is the LSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2 for details.

**c) EXT_IID**

This field is the MSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2 for details.

**d) Response**

The Response field contains the UFS response that indicates the success or failure of the Task Management Request. See 10.6.2 for details.

**e) Task Management Output Parameters**

| Field | Description |
|-------|-------------|
| Output Parameter 1 | LSB: Task Management Service Response (see Table 10.32)<br>Other bytes: Reserved |
| Output Parameter 2 | Reserved |

**Table 10.31 — Task Management Output Parameters**

# JEDEC Standard No. 220G
## Page 118

### 10.7.7.1 Basic Header (cont'd)

f) **Task Management Service Response**

#### Table 10.32 — Task Management Service Response

| Service Response | Value |
|------------------|-------|
| Task Management Function Complete | 00h |
| Task Management Function Not Supported | 04h |
| Task Management Function Failed (1) | 05h |
| Task Management Function Succeeded | 08h |
| Incorrect Logical Unit Number | 09h |

**NOTE 1** This response shall be returned whenever the UFS device is not able to process the request due to TMR processing capacity exceed.