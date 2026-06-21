# JEDEC Standard No. 220G
Page 170

## 10.9.7 Data Transfer SCSI Transport Protocol Services

The data transfer services provide mechanisms for moving data to and from the SCSI initiator port while processing commands. All SCSI transport protocol standards shall define the protocols required to implement these services.

The application client's Data-In Buffer and/or Data-Out Buffer each appears to the device server as a single, logically contiguous block of memory large enough to hold all the data required by the command.

### 10.9.7.1 Send Data-In Transport Protocol Service

A device server uses the Send Data-In transport protocol service request to request that a UFS target port sends data.

• Send Data-In (IN (I_T_L_Q Nexus, Device Server Buffer, Application Client Buffer Offset, Request Byte Count))

A device server shall only call Send Data-In () during a read operation.

A device server shall not call Send Data-In () for a given I_T_L_Q nexus after it has called Send Command Complete () for that I_T_L_Q nexus (e.g., a RESPONSE UPIU with for that I_T_L_Q nexus) or called Task Management Function Executed for a task management function that terminates that task (e.g., an ABORT TASK).

#### Table 10.73 — Send Data-In Transport Protocol Service

| Argument | Implementation |
|----------|----------------|
| I_T_L_Q Nexus | I_T_L_Q of the corresponding COMMAND UPIU |
| Device Server Buffer | Internal to device server |
| Application Client Buffer Offset | Offset in bytes from the beginning of the application client's buffer to the first byte of transferred data. |
| Request Byte Count | Specifies the length of the read data specified by the command |

### 10.9.7.2 Data-In Delivered Transport Protocol Service

This confirmation notifies the device server that the specified data was successfully delivered to the application client buffer, or that a UniPro delivery subsystem error occurred while attempting to deliver the data.

• Data-In Delivered (IN (I_T_L_Q Nexus, Delivery Result))

#### Table 10.74 — Data-In Delivered Transport Protocol Service

| Argument | Implementation |
|----------|----------------|
| I_T_L_Q Nexus | I_T_L_Q of the corresponding COMMAND UPIU |
| Delivery Result | DELIVERY SUCCESSFUL: The data was delivered successfully.<br>DELIVERY FAILURE: A UTP service delivery error occurred while attempting to deliver the data. |

# JEDEC Standard No. 220G
Page 171

## 10.9.7.2 Data-In Delivered Transport Protocol Service (cont'd)

[Figure 10.18 — Command + Read Data Phase 1/2

This is a sequence diagram showing interactions between App Client, UTP, UniPort, UTP, and UFS Unit DevServer components. The diagram shows:

1. App Client sends "Send Command( L_T_L_Q, CDB (Read CMD),...)"
2. UTP processes "T_CO_DATA.req( Command UPIU, EOM)"
3. UniPort processes "T_CO_DATA.ind( Command UPIU, MsgStatus)" and "Command Received( L_T_L_Q, CDB (Read CMD),...)"
4. UTP confirms with "T_CO_DATA.cnf_L( L4CPortResultCode )" and "T_CO_DATA.rsp_L()"
5. In a loop, UTP copies Data In to App Client Buffer while processing "T_CO_DATA.ind( Data In UPIU, MsgStatus)"
6. UniPort sends "Send Data-In ( L_T_L_Q, Device Service Response, Application Client Buffer Offset, Request Byte Count )"
7. UTP processes "T_CO_DATA.req( Data In UPIU, EOM)" and "T_CO_DATA.cnf_L( L4CPortResultCode )"
8. Finally "Data-In Delivered ( L_T_L_Q, Delivery Result )" and "T_CO_DATA.rsp_L()" complete the process
9. The diagram ends with "Execute Read CMD"]

[Figure 10.19 — Command + Read Data Phase 2/2

This is a continuation sequence diagram showing:

1. UFS Unit DevServer executes "Execute Read CMD"
2. Sends "Send Command Complete( L_T_L_Q, Status, Service Response,...)"
3. UTP processes "T_CO_DATA.req( Response UPIU, EOM)" and "T_CO_DATA.ind( Response UPIU, MsgStatus)"
4. App Client receives "Command Complete Received( L_T_L_Q, Status, Service Response,...)"
5. UTP confirms with "T_CO_DATA.cnf_L( L4CPortResultCode )" and "T_CO_DATA.rsp_L()"]

# JEDEC Standard No. 220G
Page 172

## 10.9.7.3 Receive Data-Out Transport Protocol Service

A device server uses the Receive Data-Out transport protocol service request to request that a UFS target port receives data.

• Receive Data-Out (IN (I_T_L_Q Nexus, Application Client Buffer Offset, Request Byte Count, Device Server Buffer))

A device server shall only call Receive Data-Out () during a write operation.

A device server shall not call Receive Data-Out () for a given I_T_L_Q nexus after a Send Command Complete () has been called for that I_T_L_Q nexus or after a Task Management Function Executed () has been called for a task management function that terminates that command (e.g., an ABORT TASK).

### Table 10.75 — Receive Data-Out Transport Protocol Service

| Argument | Implementation |
|----------|----------------|
| I_T_L_Q Nexus | I_T_L_Q of the corresponding COMMAND UPIU |
| Application Client Buffer Offset | Offset in bytes from the beginning of the application client's buffer to the first byte of transferred data |
| Device Server Buffer | Internal to device server |
| Request Byte Count | Number of bytes to be moved by this request |

## 10.9.7.4 Data-Out Received Transport Protocol Service

A UFS target port uses the Data-Out Received transport protocol service indication to notify a device server that it has received data.

• Data-out Received (IN (I_T_L_Q Nexus, Delivery Result))

### Table 10.76 — Data-Out Received Transport Protocol Service

| Argument | Implementation |
|----------|----------------|
| I_T_L_Q Nexus | I_T_L_Q of the corresponding COMMAND UPIU |
| Delivery Result | DELIVERY SUCCESSFUL: The data was delivered successfully. DELIVERY FAILURE: A UTP service delivery error occurred while attempting to deliver the data. |

# JEDEC Standard No. 220G
Page 173

## 10.9.7.4 Data-Out Received Transport Protocol Service (cont'd)

[Figure 10.20 - Command + Write Data Phase 1/2: This is a sequence diagram showing interactions between App Client, UTP, UniPort, UTP, and UFS Unit DevServer components. The diagram shows the flow of a Write CMD execution with various protocol messages including T_CO_DATA.req, T_CO_DATA.ind, T_CO_DATA.cnf, and T_CO_DATA.rsp calls. There's a loop section showing UTP fetching data from App Client Buffer and the execution of the Write CMD, with data transfer between components. Key messages include Command Received, Receive Data-Out, and UTP copies Data-Out to Device Server Buffer.]

[Figure 10.21 - Command + Write Data Phase 2/2: This is a simpler sequence diagram showing the completion phase of the Write CMD execution between the same components (App Client, UTP, UniPort, UTP, and UFS Unit DevServer). The diagram shows the Send Command Complete message flow, with T_CO_DATA.req for Response UPIU, followed by T_CO_DATA.ind, T_CO_DATA.cnf, and T_CO_DATA.rsp messages, ultimately resulting in Command Complete Received at the App Client with Status and Service Response.]