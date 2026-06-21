# 10.7.6 TASK MANAGEMENT REQUEST UPIU

The TASK MANAGEMENT REQUEST UPIU is used by the Initiator device to manage the execution of one or more tasks within the Target device. The Task Management Request function closely follows the SCSI Architecture Model [SAM].

Task Management functions in UFS device requires the LU task manager to have the capability to process at least one Task Management Request. If more than one Task Management Request is accepted by a task manager in the device, the task manager may execute the requests in any order. The task manager may reject a Task Management Request with Task Management Function Failed service response when the number of outstanding Task Management Requests submitted by the Host exceeds the capability of the Task Manager.

## Table 10.27 — Task Management Request UPIU

| Byte | 0 | 1 | 2 | 3 |
|------|---|---|---|---|
| 0 | xx00 0100b | Flags | LUN | Task Tag |
| 4 | IID | Reserved | Task Manag. Function | Reserved | EXT_IID | Reserved |
| 8 | Total EHS Length (00h) | Reserved | (MSB) | (LSB) |
| | | | Data Segment Length (0000h) | |
| 12 | (MSB) | 13 | 14 | 15 (LSB) |
| | | | Input Parameter 1 | |
| 16 | (MSB) | 17 | 18 | 19 (LSB) |
| | | | Input Parameter 2 | |
| 20 | (MSB) | 21 | 22 | 23 (LSB) |
| | | | Input Parameter 3 | |
| 24 | | 25 | 26 | 27 |
| | | | Reserved | |
| 28 | | 29 | 30 | 31 |
| | | | Reserved | |
| | | | Header E2ECRC (omit if HD=0) | |

---
*JEDEC Standard No. 220G*  
*Page 113*

# 10.7.6.1 Basic Header

The first 12 bytes of the TASK MANAGEMENT REQUEST UPIU contain the Basic Header as described in 10.6.2 Basic Header Format. Specific details are as follows:

## a) Transaction Type

A type code value of xx00 010b indicates a TASK MANAGEMENT REQUEST UPIU.

## b) IID

This field is the LSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2 for details.

## c) EXT_IID

This field is the MSB nibble of the Initiator ID nexus, as described in bullet k) of the Basic Header Format. The Initiator ID nexus indicates the identity of the Initiator device who created the task request. See Initiator ID description in 10.6.2 for details.

## d) Task Management Function

Table 10.28 defines UFS Task Management Functions based on [SAM].

### Table 10.28 — Task Management Function Values

| Function | Value | Description |
|----------|--------|-------------|
| Abort Task | 01h | Abort specific task in queue in a specific LU. Identify by IID, LUN and Task Tag |
| Abort Task Set | 02h | Abort the task queue list in a specific LU. Identify by IID and LUN. |
| Clear Task Set ⁽¹⁾ | 04h | Clear the task queue list in specific LU. Identify by LUN. |
| Logical Unit Reset | 08h | Reset the designated LU. Identify by LUN |
| Query Task | 80h | Query a specific task in a queue list in a specific LU. Identify by IID, LUN and Task Tag. If the specific task is present in the queue, Function Succeeded is returned in the response. If the specific task is not present in the queue, Function Complete is returned in the response. |
| Query Task Set | 81h | Query a specific LU to see if there is any Task in queue. Identify by IID and LUN. If there is one of more tasks present in the queue, Function Succeeded is returned in the response. If no task is present in the queue, Function Complete is returned in the response. |

NOTE 1   If TST = 1 (i.e., per LT nexus), it aborts all commands in the task set, identified by IID and LUN. Since this standard supports TST = 0, all commands in the task set from all initiators are aborted.

---

JEDEC Standard No. 220G  
Page 114

# JEDEC Standard No. 220G
## Page 115

### 10.7.6.1 Basic Header (cont'd)

e) Task Management Input Parameters

#### Table 10.29 — Task Management Input Parameters

| Field | Description |
|-------|-------------|
| Input Parameter 1 | LSB: LUN of the logical unit operated on by the task management function.<br>Other bytes: Reserved |
| Input Parameter 2 | LSB: Task Tag of the task/command operated on by the task management function.<br>Other bytes: Reserved |
| Input Parameter 3 | Initiator ID [7:0] Initiator ID of the task/command operated on by the task management function.<br>• If bEXTIIDEn is set to 00h, the MSB nibble of this field shall be set to 0000b<br>• If bEXTIIDEn is set to 01h, the MSB nibble of this field shall be set to EXT_IID of the task/command operated on by the task management function<br><br>The LSB nibble shall be set to the IID of the task/command operated on by the task management function. |

**NOTE 1** Input Parameter 1 and LUN field in the basic header should be set to the same value.

**NOTE 2** Input Parameter 3 and IID field in the basic header shall indicate the same value.