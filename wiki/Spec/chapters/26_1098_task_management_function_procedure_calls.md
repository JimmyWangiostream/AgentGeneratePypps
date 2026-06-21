# 10.9.8 Task Management Function Procedure Calls

An application client requests the processing of a task management function by invoking the SCSI transport protocol services:

• Service Response = Function name (IN (Nexus), OUT (| Additional Response Information|))

## Table 10.77 — Task Management Function Procedure Calls

| Task Management Function (Function name) | Nexus argument |
|-------------------------------------------|----------------|
| Abort Task | I_T_L_Q Nexus |
| Abort Task Set | I_T_L Nexus |
| Clear Task Set | I_T_L Nexus |
| Logical Unit Reset | I_T_L Nexus |
| Query Task | I_T_L_Q Nexus |
| Query Task Set | I_T_L Nexus |

One of the following SCSI transport protocol specific service responses shall be returned:

## Table 10.78 — SCSI Transport Protocol Service Responses

| Response | Description |
|----------|-------------|
| FUNCTION COMPLETE | A task manager response indicating that the requested function is complete.<br>Unless another response is required, the task manager shall return this response upon completion of a task management request supported by the logical unit or SCSI target device to which the request was directed. |
| FUNCTION SUCCEEDED | A task manager response indicating that the requested function is supported and completed successfully. This task manager response shall only be used by functions that require notification of success (e.g., QUERY TASK, QUERY TASK SET) |
| FUNCTION REJECTED | A task manager response indicating that the requested function is not supported by the logical unit or SCSI target device to which the function was directed. |
| INCORRECT LOGICAL UNIT NUMBER | A task router response indicating that the function requested processing for an incorrect logical unit number. |
| SERVICE DELIVERY OR TARGET FAILURE | The request was terminated due to a service delivery failure SCSI target device malfunction. The task manager may or may not have successfully performed the specified function. |

---
JEDEC Standard No. 220G  
Page 174

# JEDEC Standard No. 220G
Page 175

## 10.9.8.1 ABORT TASK

This function shall be supported by all logical units.

The task manager shall abort the specified command, if it exists. Previously established conditions, including mode parameters, and reservations shall not be changed by the ABORT TASK function.

A response of FUNCTION COMPLETE shall indicate that the command was aborted or was not in the task set. In either case, the SCSI target device shall guarantee that no further requests or responses are sent from the command.

If the processing of the task that is requested to be aborted requires Data-Out data transfer, then Target device shall wait until it receives all DATA OUT UPIUs related to any outstanding READY TO TRANSFER UPIUs before sending the task management response.

All SCSI transport protocol standards shall support the ABORT TASK task management function.

Service Response = ABORT TASK (IN ( I_T_I_Q Nexus ))

## 10.9.8.2 ABORT TASK SET

This function shall be supported by all logical units.

The task manager shall abort all commands in the task set that were received on the specified I_T_L nexus. Commands received on other I_T nexuses or in other task sets shall not be aborted. This task management function performed is equivalent to a series of ABORT TASK requests.

All pending status and sense data for the commands that were aborted shall be cleared. Other previously established conditions, including mode parameters, and reservations shall not be changed by the ABORT TASK SET function.

If the processing of one or more tasks in the task set require Data-Out data transfer, then Target device shall wait until it receives all DATA OUT UPIUs related to any outstanding READY TO TRANSFER UPIUs before sending the task management response.

All SCSI transport protocol standards shall support the ABORT TASK SET task management function.
Service Response = ABORT TASK SET (IN ( I_T_L Nexus ))

## 10.9.8.3 CLEAR TASK SET

This function shall be supported by all logical units.

The task manager shall abort all commands in the task set.

If the processing of one or more tasks in the task set require Data-Out data transfer, then Target device shall wait until it receives all DATA OUT UPIUs related to any outstanding READY TO TRANSFER UPIUs before sending the task management response.

# JEDEC Standard No. 220G
## Page 176

### 10.9.8.3 CLEAR TASK SET (cont'd)

All pending status and sense data for the task set shall be cleared. Other previously established conditions, including mode parameters, and reservations shall not be changed by the CLEAR TASK SET function.

All SCSI transport protocol standards shall support the CLEAR TASK SET task management function.
Service Response = CLEAR TASK SET (IN ( I_T_L Nexus ))

### 10.9.8.4 LOGICAL UNIT RESET

This function shall be supported by all logical units.

Before returning a FUNCTION COMPLETE response, the logical unit shall perform the logical unit reset functions.

If the processing of one or more tasks in the logical unit requires Data-Out data transfer, then Target device shall wait until it receives all DATA OUT UPIUs related to any outstanding READY TO TRANSFER UPIUs before sending the task management response.

All SCSI transport protocol standards shall support the LOGICAL UNIT RESET task management function.

Service Response = LOGICAL UNIT RESET (IN ( I_T_L Nexus ))

### 10.9.8.5 QUERY TASK

UFS transport protocols shall support QUERY TASK.

The task manager in the specified logical unit shall:

1) If the specified command is present in the task set, then return a service response set to FUNCTION SUCCEEDED; or

2) If the specified command is not present in the task set, then return a service response set to FUNCTION COMPLETE.

Service Response = QUERY TASK (IN ( I_T_L_Q Nexus ))

### 10.9.8.6 QUERY TASK SET

UFS transport protocols shall support QUERY TASK SET.

The task manager in the specified logical unit shall:

1) If there is any command present in the task set specified I_T_L nexus, then return a service response set to FUNCTION SUCCEEDED; or

2) If there is no command present in the task set specified I_T nexus, then return a service response set to FUNCTION COMPLETE.

Service Response = QUERY TASK SET (IN ( I_T_L Nexus ))

# 10.9.8.7 Task Management SCSI Transport Protocol Services

UFS standard shall define the SCSI transport protocol specific requirements for implementing the Send Task Management Request request, the Task Management Request Received indication, the Task Management Function Executed response, and the Received Task Management Function Executed confirmation SCSI transport protocol services.

A SCSI transport protocol standard may specify different implementation requirements for the Send Task Management Request request SCSI transport protocol service for different values of the Function Identifier argument.

All SCSI initiator devices shall implement the Send Task Management Request request and the Received Task Management Function Executed confirmation SCSI transport protocol services as defined in the applicable SCSI transport protocol standards.

All SCSI target devices shall implement the Task Management Request Received indication and the Task Management Function Executed response SCSI transport protocol services as defined in the applicable SCSI transport protocol standards.

[Figure 10.22 — Task Management Function: A sequence diagram showing interactions between App Client, UTP, UniPort, UFS, and UFS Unit Task Manager components. The diagram illustrates the flow of task management requests and responses, including:

1. App Client sends "Send Task Management Request" to UTP
2. UTP sends "T_CO_DATA.req" to UniPort 
3. UniPort sends "T_CO_DATA.ind" to UFS
4. UFS Unit Task Manager receives "Task Management Request Received" and executes "Execute Task MGMT"
5. Response flows back through the same components in reverse
6. Various SCSI transport protocol messages are exchanged between components including confirmations and status updates]

**Figure 10.22 — Task Management Function**

---
*JEDEC Standard No. 220G*  
*Page 177*

# JEDEC Standard No. 220G
Page 178

## 10.9.8.8 Send Task Management Request SCSI Transport Protocol Service Request

An application client uses the Send Task Management Request SCSI transport protocol service request to request that a SCSI initiator port send a task management function.

Send Task Management Request SCSI transport protocol service request:
Send Task Management Request (IN ( Nexus, Function Identifier ))

### Table 10.79 — Send Task Management Request SCSI Transport Protocol Service Request

| Argument | Implementation |
|----------|----------------|
| Nexus | I_T nexus, I_T_L nexus, or I_T_L_Q nexus |
| Function Identifier: | Argument encoding the task management function to be performed. |

## 10.9.8.9 Task Management Request Received SCSI Transport Protocol Service Indication

A task router uses the Task Management Request Received SCSI transport protocol service indication to notify a task manager that it has received a task management function.

Task Management Request Received SCSI transport protocol service indication:
Task Management Request Received (IN ( Nexus, Function Identifier ))

### Table 10.80 — Task Management Request Received SCSI Transport Protocol Service Indication

| Argument | Implementation |
|----------|----------------|
| Nexus | I_T nexus, I_T_L nexus, or I_T_L_Q nexus |
| Function Identifier: | Argument encoding the task management function to be performed. |

## 10.9.8.10 Task Management Function Executed SCSI Transport Protocol Service Response

A task manager uses the Task Management Function Executed SCSI transport protocol service response to request that a SCSI target port transmit task management function executed information.

Task Management Function Executed SCSI transport protocol service response:
Task Management Function Executed (IN (Nexus, Service Response, [Additional Response Information]))

### Table 10.81 — Task Management Function Executed SCSI Transport Protocol Service Response

| Argument | Implementation |
|----------|----------------|
| Nexus | I_T nexus, I_T_L nexus, or I_T_L_Q nexus |
| | FUNCTION COMPLETE |
| | FUNCTION SUCCEEDED: |
| Service Response | FUNCTION REJECTED |
| | INCORRECT LOGICAL UNIT NUMBER |
| | SERVICE DELIVERY OR TARGET FAILURE |
| Additional Response Information | The Additional Response Information output argument for the task management procedure call |

# 10.9.8.11 Received Task Management Function Executed SCSI Transport Protocol Service Confirmation

A SCSI initiator port uses the Received Task Management Function Executed SCSI transport protocol service confirmation to notify an application client that it has received task management function executed information.

Received Task Management Function Executed SCSI transport protocol service confirmation:
Received Task Management Function Executed (IN (Nexus, Service Response, [Additional Response Information]))

## Table 10.82 — Received Task Management Function Executed SCSI Transport Protocol Service Confirmation

| Argument | Implementation |
|----------|----------------|
| Nexus | I_T nexus, I_T_L nexus, or I_T_L_Q nexus |
|  | FUNCTION COMPLETE |
|  | FUNCTION SUCCEEDED: |
| Service Response | FUNCTION REJECTED |
|  | INCORRECT LOGICAL UNIT NUMBER |
|  | SERVICE DELIVERY OR TARGET FAILURE |
| Additional Response Information | The Additional Response Information output argument for the task management procedure call |

---

JEDEC Standard No. 220G
Page 179