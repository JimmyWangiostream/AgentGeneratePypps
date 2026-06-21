# JEDEC Standard No. 220G
Page 180

## 10.9.9 Query Function Transport Protocol Services

UFS defines Query Function to get/set UFS-specific device-level registers and parameters (not part of SCSI definition).

### 10.9.9.1 Send Query Request UFS Transport Protocol Service

An application client uses the Send Query Request UFS transport protocol service request to request that a UFS initiator port send a Query Request function.

Send Query Request UFS transport protocol service request:
Send Query Request(L_T Nexus, Operation: Read|Write, Type: UFS|Vendor, Identifier: Descriptor|Attribute|Flag,Length: n, [Index], [Selector], [WriteData])

#### Table 10.83 — Send Query Request UFS Transport Protocol Service

| Argument | Implementation |
|----------|----------------|
| Nexus | I_T nexus |
| Operation | Argument encoding the operation to be performed |
| Type | Indicates UFS defined or vendor-specific operation |
| Identifier | Identifier for descriptor type, attribute or flag |
| Length | Number of bytes to read or write |
| Index | Index reference for the descriptor, attribute or flag |
| Selector | Reserved |
| WriteData | Data to be written in a write query request |

[**Figure 10.23 — UFS Query Function**: This is a sequence diagram showing the interaction between App Client, UTP, UniPort, UTP, and UFS Device Manager components. The diagram illustrates the flow of a UFS query function request, starting with the App Client sending a query request through multiple UTP and UniPort layers, then executing the query at the UFS Device Manager, and finally returning the response back through the same layers. The diagram shows specific message types like T_CO_DATA.req, T_CO_DATA.ind, T_CO_DATA.cnf_L(), T_CO_DATA.rsp_L(), and various query-related parameters being passed between components.]

# JEDEC Standard No. 220G
Page 181

## 10.9.9.2 Query Request Received UFS Transport Protocol Service Indication

A UFS target port uses the Query Request Received UFS transport protocol service indication to notify a UFS device manager that it has received a query function.

Query Request Received UFS transport protocol service indication:
Query Request Received(I_T Nexus, Operation: Read|Write, Type: UFS|Vendor, Identifier:Descriptor|Attribute|Flag,Length:n, [Index], [Selector], [WriteData])

### Table 10.84 — Query Request Received UFS Transport Protocol Service Indication

| Argument | Implementation |
|----------|----------------|
| Nexus | I_T nexus |
| Operation | Argument encoding the operation to be performed |
| Type | Indicates UFS defined or vendor-specific operation |
| Identifier | Identifier for descriptor type, attribute or flag |
| Length | Number of bytes to read or write |
| Index | Index reference for the descriptor, attribute or flag |
| Selector | Reserved |
| WriteData | Data to be written in a write query request |

## 10.9.9.3 Query Function Executed UFS Transport Protocol Service Response

A device manager uses the Query Function Executed UFS transport protocol service response to request that a UFS target port transmit query function executed information.

Query Function Executed UFS transport protocol service response:
Query Executed(I_T Nexus, Service Response,[ReadData])

### Table 10.85 — Query Function Executed UFS Transport Protocol Service Response

| Argument | Implementation |
|----------|----------------|
| Nexus | I_T nexus |
| Service Response | FUNCTION SUCCEEDED<br>FUNCTION FAILED |
| ReadData | Data to be returned in a read query request |

# JEDEC Standard No. 220G
Page 182

## 10.9.9.4 Received Query Function Executed UFS Transport Protocol Service Confirmation

A UFS initiator port uses the Received Query Function Executed UFS transport protocol service confirmation to notify an application client that it has received task management function executed information.

Received Query Function Executed UFS transport protocol service confirmation:
Received Query Executed(I_T Nexus, Service Response,[ReadData])

### Table 10.86 — Received Query Function Executed UFS Transport Protocol Service Confirmation

| Argument | Implementation |
|----------|----------------|
| Nexus | I_T nexus |
| Service Response | FUNCTION SUCCEEDED<br>FUNCTION FAILED |
| ReadData | Data to be returned in a read query request |