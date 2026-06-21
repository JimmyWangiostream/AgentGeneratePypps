# 5 UFS Architecture Overview

## 5.1 UFS Top Level Architecture

Figure 5.1 shows the Universal Flash Storage (UFS) top level architecture.

[**Figure 5.1 — UFS Top Level Architecture**

This is a layered architecture diagram showing:

**Top Layer - UFS Application Layer (UAP)** (shown in yellow):
- Contains "UFS Command Set (UCS)" which includes:
  - UFS Native Command Set (orange)
  - Simplified SCSI Command Set (orange) 
  - Future Extension... (white)
- Device Manager (Query Request) (green, left side)
- Task Manager (orange, right side)
- Service Access Points: UDM_SAP, UTP_CMD_SAP, TP_TM_SAP

**Middle Layer - UFS Transport Protocol Layer (UTP)** (shown in blue):
- Service Access Points: UIO_SAP, UIC_SAP

**Bottom Layer - UFS InterConnect Layer (UIC)** (shown in purple):
- MIPI UniPro
- MIPI M-PHY]

**Figure 5.1 — UFS Top Level Architecture**

UFS communication is a layered communication architecture. It is based on SCSI SAM architectural model [SAM].

### 5.1.1 Application Layer

The application layer consists of the UFS command set (UCS), the device manager and the Task Manager. The UCS will handle the normal commands like read, write, and so on. UFS may support multiple command sets. UFS is designed to be protocol agnostic. The command set for this version UFS standard is based on SCSI command set. In particular, a simplified SCSI command set was selected for UFS. UFS Native command set can be supported when it is needed to extend the UFS functionalities.

The Task Manager handles commands meant for command queue control. The Device Manager will provide device level control like Query Request and lower level link-layer control.

### 5.1.2 UFS Device Manager

The device manager has the following two responsibilities:

• Handling device level operations.
• Managing device level configurations.

Device level operations include functions such as device power management, settings related to data transfer, background operations enabling, and other device specific operations.

Device level configuration is managed by the device manager by maintaining and storing a set of descriptors. The device manager handles commands like query request which allow to modify or retrieve configuration information of the device.

---
*JEDEC Standard No. 220G*  
*Page 9*

# 5.1.3 Service Access Points

As seen from the diagram the device manager interacts with lower layers using the following two service access points:

• UDM_SAP
• UIO_SAP

UDM_SAP is the service access point exposed by the UTP for the device manager to allow handling of device level operations and configurations. For example the handling of query request for descriptors would be done using this service access point. Figure 5.2 depicts the usage of the service access point.

[Figure 5.2 - Diagram showing Device Manager at the top connected by an arrow labeled "Query Request Device Descriptors etc." to two lower layers: UFS InterConnect Layer (UIC) on the left with UIO_SAP service access point, and UFS Transport Protocol Layer (UTP) on the right with UDM_SAP service access point. Both layers are represented as rectangular blocks with service access points shown as oval shapes above them.]

**Figure 5.2 — Usage of UDM_SAP**

UIO_SAP is the service access point exposed by the UIC layer for the device manager to trigger the reset of the UIC layer and to transfer requests and responses related to UIC management functions. Figure 5.3 depicts the usage of the service access point.

[Figure 5.3 - Diagram showing Device Manager at the top connected by an arrow labeled "UIC reset, Link reset etc." to two lower layers: UFS InterConnect Layer (UIC) on the left with UIO_SAP service access point, and UFS Transport Protocol Layer (UTP) on the right with UDM_SAP service access point. Both layers are represented as rectangular blocks with service access points shown as oval shapes above them.]

**Figure 5.3 — Usage of UIO_SAP**

---
JEDEC Standard No. 220G  
Page 10

# JEDEC Standard No. 220G
Page 11

## 5.1.4 UIO_SAP

UIO_SAP is the service access point exposed by the UIC layer. In UniPro, UIO_SAP corresponds to DME_SAP. The DME_SAP provides service primitives including one for resetting the entire UniPro protocol stack and one for UFS device reset, etc.

• DME_RESET : It is used when the UniPro stack has to be reset.
• DME_ENDPOINTRESET: It is used when UFS host wants the UFS device to perform a reset.

For the detailed internal mechanism, refer the UniPro specification [MIPI-UniPro] released by MIPI (MIPI is Mobile Industry Processor Interface).

## 5.1.5 UDM_SAP

UDM_SAP is the service access point exposed by the UTP layer to the Device Manager for UFS device level functions. UDM_SAP corresponds to the Query Request and Query Response functions defined by the UFS UTP layer.

For further details refer to the following subclauses: 10.9.9, Query Function Transport Protocol Services, 10.7.8, QUERY REQUEST UPIU, and 10.7.9, QUERY RESPONSE UPIU.

## 5.1.6 UFS Transport Protocol Layer

The UFS Transport Protocol (UTP) layer provides services for the higher layer . UPIU is "UFS Protocol Information Unit" which is exchanged between UTP layers of UFS host and UFS device. For example, if host side UTP receives the request from application layer or Device Manager, UTP generates a UPIU for that request and transports the generated UPIU to the peer UTP in UFS device side. The UTP layer provides the following three service access points.

1) UFS Device Manager Service Access Point (UDM_SAP) to perform the device level management like descriptor access.

2) UTP Command Service Access Point (UTP_CMD_SAP) to transport commands.

3) UTP Task Management Service Access Point (UTP_TM_SAP) to transport task-management function like "abort task" function.

## 5.1.7 UFS Interconnect Layer

The lowest layer is UFS Interconnect Layer (UIC) which handles connection between UFS host and UFS device. UIC consists of MIPI UniPro and MIPI M-PHY. The UIC provides two service access points to upper layer. The UIC Service Access Point (UIC_SAP) to transport UPIU between UFS host and UFS device. The UIC_SAP corresponds to T_SAP in UniPro. The UIC IO control Service Access Point (UIO_SAP) to manage UIC. The UIO_SAP corresponds to DME_SAP in UniPro.

## 5.1.8 UFS Topology

This version of the standard assumes that only one device is connected to a UFS port. Other topologies may be defined in future versions of the standard.

# JEDEC Standard No. 220G
Page 12

## 5.2 UFS System Model

Figure 5.4 shows an example of UFS system. It shows how a UFS host is connected to a UFS device, the position of UFS host controller and its related UFS HCI interface.

[**Figure 5.4 — UFS System Model**: A block diagram showing the UFS system architecture with two main sections:

**UFS Host** (left side):
- Application layer at top
- Driver section containing UFS Driver
- UFS Host Controller containing UFS Host Reg
- UIC (UniPro Interface Controller) with MIPI UniPro layers
- Connection signals: RST_n, REF_CLK, and UIC interface with DOUT_t, DOUT_c, DIN_t, DIN_c

**UFS Device** (right side):
- Device Level Managing component with bidirectional connection to Descriptors
- Control and Config connections shown with dashed lines
- LU-0 through LU-N (Logical Units) connected to Storage units (shown with dashed boxes)
- UIC interface matching the host side]

The UFS host consists of the application which wishes to communicate with the UFS device. It communicates with the device using the UFS driver. The UFS driver is meant for managing the UFS host controller through the UFS HCI (UFS Host Controller Interface). The UFS HCI is basically a set of registers exposed by the host controller.

Figure 5.4 also indicates the UFS interface between the UFS host and the UFS device. The UFS Interconnect (UIC) layer consists of MIPI UniPro and MIPI M-PHY. The physical layer M-PHY is differential, dual simplex PHY that includes TX and RX pairs.

Potential UFS devices can be memory card (full size and micro size), embedded bootable mass storage devices, IO devices, etc. A UFS device is comprised of multiple logical units, a device manager and descriptors. The device manager performs device level functions like power management while the logical unit performs functions like read, write etc. The descriptors are meant for storage of configuration related information.

## 5.3 System Boot and Enumeration

The system boot from a bootable UFS device will initiate after power up when the UFS InterConnect Layer (MIPI M-PHY and UniPro) has completed its boot sequence. The boot code can be read from the appropriate boot logical unit, or as desired, boot ROM code can re-configure MIPI M-PHY and UniPro to appropriate setting before reading the boot code.

Multiple boot logical units may be available in a UFS device. However, only one boot logical unit will be active at power-up. Appropriate descriptors are available to configure the boot process.

During boot, accesses to boot logical unit are supported via SCSI commands.

# 5.4 UFS Interconnect (UIC) Layer

UFS interconnect layer is composed by MIPI UniPro, which provides basic transfer capabilities to the upper layer (UTP), and MIPI M-PHY, adopted as UFS physical layer.

## 5.4.1 UFS Physical Layer Signals

The UFS physical layer defines the physical portion of the UFS interface that connects UFS device and UFS host. This is based on MIPI M-PHY specification. UFS interface can support multiple lanes in each direction. Each lane consists of a differential pair. Basic configuration is based on one transmit lane and one receive lane.

Optionally, a UFS device may support two downstream lanes and two upstream lanes. An equal number of downstream and upstream lanes shall be provided in each link.

Table 5.1 summarizes the signals required for a UFS device. Only the single lane, per direction, per link, configuration is shown. See clause 6 and clause 8 for full details about UFS signals.

### Table 5.1 — UFS Signals

| Name | Type | Description |
|------|------|-------------|
| REF_CLK | Input | Reference clock<br>Relatively low speed clock common to all UFS devices in the chain,<br>used as a reference for the PLL in each device. |
| DIN_t<br>DIN_c | Input | Downstream lane input<br>Differential input true and complement signal pair. |
| DOUT_t<br>DOUT_c | Output | Upstream lane output<br>Differential output true and complement signal pair. |
| RST_n | Input | Reset<br>UFS Device hardware reset signal |

## 5.4.2 MIPI UniPro

In UFS, UniPro is responsible for management of the link, including the PHY.

**NOTE** Device management is outside the scope of the interconnect layer and is the responsibility of the upper layers.

The basic interface to the interconnect layer is UniPro definition of a CPort. CPort is used for all data transfer as well as all control and configuration messages. In general, multiple CPorts can be supported on a device and the number of CPorts is implementation dependent.

Traffic sent over UniPro link can be classified as TC0 or TC1 traffic class with TC1 as higher priority traffic class. This version of UFS standard only uses a single CPort and TC0 traffic class.

UFS takes advantage of the basic types of UniPro services. These include data transfer service, and config/control/status service.

For more details, please refer to clause 9, UIC layer: MIPI UniPro, and MIPI UniPro specification [MIPI-UniPro].

---

JEDEC Standard No. 220G  
Page 13

# JEDEC Standard No. 220G
## Page 14

### 5.4.3 MIPI UniPro Related Attributes

In general the UniPro related attributes, values and use of them are defined in the MIPI UniPro specification. The attributes may be generic for all UniPro applications and thus out of scope of this document. Following attributes are defined in this standard specifically for UFS application as indicated in Table 5.2.

#### Table 5.2 — ManufacturerID and DeviceClass Attributes

| Attribute | AttributeID⁽¹⁾ | Value | Description |
|-----------|----------------|--------|-------------|
| DME_DDBL1_ManufacturerID | 0x5003 | | MIPI manufacturer ID. MIPI MID shall be used in this Attribute also for UFS applications. The ID can be requested from MIPI. |
| DME_DDBL1_DeviceClass | 0x5002 | Memory = 0x02<br>Host = 0x03 | UniPro DeviceClass ID for UFS application |

**NOTE 1** Reference MIPI Alliance Specification for Device Descriptor Block [MIPI-DDB]

### 5.5 UFS Transport Protocol (UTP) Layer

As mentioned previously, the Transport Layer is responsible for encapsulating the protocol into the appropriate frame structure for the interconnect layer. UFS is protocol agnostic and thus any protocol will need the appropriate translation layer. For this version of UFS standard, this is UTP (UFS Transport Protocol) layer.

In this version of the standard, all accesses are supported only through SCSI, however additional API/service/extension may be added in future versions to introduce new features or address specific requirements.

A design feature of UTP is to provide a flexible packet architecture that will assist the UFS controller in directing the encapsulated command, data and status packets into and out of system memory. The intention is to allow the rapid transmittal of data between the host system memory and the UFS device with minimal host processor intervention. Once the data structures are set up in host memory and the target device is notified, the entire command transaction can take place between the UFS device and the host memory. The means by which the UFS controller transfers data into and out of host memory is via a hardware and/or firmware mechanism that is beyond the scope of this document. See the UFS controller standard for further information.

A second feature of the UTP design is that once a device receives a command request notification from the host, the device will control the pacing and state transitions needed to satisfy the data transfers and status completion of the request. The idea here is that the device knows its internal condition and state and when and how to best transfer the data that makes up the request. It is not necessary for the host system or controller to continually poll the device for "ready" status or for the host to estimate when to start a packet transfer. The device will start the bus transactions when it determines its conditions and status are optimal. This approach cuts down on the firmware and logic needed within the host to communicate with a device. It also affords the maximum possible throughput with the minimum number of bus transactions needed to complete the operation.

# JEDEC Standard No. 220G
## Page 15

### 5.5.1 Architectural Model

The SCSI Architecture Model [SAM] is used as the general architectural model for UTP. The SAM architecture is a client-server model or more commonly a request-response architecture.

#### 5.5.1.1 Client-Server Model

A client-server transaction is represented as a procedure call with inputs supplied by the application client on the Initiator device. The procedure call is processed by the server and returns outputs and a procedure call status. Client-server relationships are not symmetrical. A client only originates requests for service. A server only responds to such requests.

Initiator device and Target device are mapped into UFS physical network devices. An Initiator device may request processing of a command or a task management function through a request directed to the Target device. Device service requests are used to request the processing of commands and task manager requests are used to request the processing of task management functions.

Target device is a UFS device. A UFS device will contain one or more Logical Units. A Logical Unit is an independent processing entity within the device.

An Initiator request is directed to a single Logical Unit within a device. A Logical Unit will receive and process the client command or request. Each Logical Unit has an address within the Target device called a Logical Unit Number (LUN).

Communication between the Initiator device and Target device is divided into a series of messages. These messages are formatted into UFS Protocol Information Units (UPIU) as defined within this standard. There are a number of different UPIU types defined. All UPIU structures contain a common header area at the beginning of the data structure (lowest address). The remaining fields of the structure vary according to the type of UPIU.

A Task is a command or sequence of actions that perform a requested service. A Logical Unit contains a task queue that will support the processing of one or more Tasks. The Task queue is managed by the Logical Unit. A unique Task Tag is generated by the Initiator device when building the Task. This Task Tag is used by the Target device and the Initiator device to distinguish between multiple Tasks. All transactions and sequences associated with a particular Task will contain that Task Tag in the transaction associated data structures.

Command structures consist of Command Descriptor Blocks (CDB) that contain a command opcode and related parameters, flags and attributes. The description of the CDB content and structure are defined in detail in the [SAM], [SBC] and [SPC] INCITS T10 draft standards.

# 5.5.1.1 Client-Server Model (cont'd)

[THIS IS FIGURE: SCSI Domain Class Diagram showing the relationships between various SCSI components. The diagram illustrates:

- At the top level: SCSI Target Device, SCSI Port, and SCSI Initiator Device, each with cardinality of 1
- Below SCSI Target Device: Level 1 Hierarchical Logical Unit (cardinality 1)
- Connected components include:
  - Logical Unit (cardinality 1..*)
  - SCSI Target Port (cardinality 0..1)
  - SCSI Initiator Port (cardinality 0..1) 
  - Application Client (cardinality 1..*)
- The Logical Unit "routes to" Task Router (cardinality 1..*)
- Task Router connects to Device Server (cardinality 1)
- Device Server connects to Task Manager (cardinality 1)
- SCSI Initiator Port "routes to" Application Client (cardinality 1..*)

The diagram uses UML notation with diamonds indicating relationships and numerical cardinalities showing the multiplicity of connections between components.]

**Figure 5.5 — SCSI Domain Class Diagram**

---
JEDEC Standard No. 220G  
Page 16

# 5.5.1.1 Client-Server Model (cont'd)

[THIS IS FIGURE: UFS Domain Class Diagram showing the relationships between various UFS components. The diagram contains several boxes representing different classes:

- **UFS Target Device** (top left) - connected to Device Manager with multiplicity 1
- **UFS Port** (top center) - containing UFS Target Port and UFS Initiator Port
- **UFS Initiator Device** (top right) - connected to Application Client
- **Device Manager** (center left) - routes to other components with multiplicity 1..*
- **UFS Logical Unit** (bottom left) - connected to Device Server and Task Manager, both with multiplicity 1
- **Task Router** (bottom center) - routes to other components

The diagram shows various connections between these components with arrows and multiplicity indicators (1, 1..*, etc.). Green diamonds indicate composition relationships, while red arrows show routing relationships.]

**Figure 5.6 — UFS Domain Class Diagram**

---
JEDEC Standard No. 220G  
Page 17

# JEDEC Standard No. 220G
## Page 18

### 5.5.1.2 CDB, Status, Task Management

UTP adopts Command Descriptor Block (CDB) format for commands, device status data hierarchy and reporting method, and task management functions of outstanding commands, described in [SAM]. Regardless of the command protocol to be delivered by UTP, SCSI CDB, Status and Task Management Functions should be adopted uniformly in UFS devices.

### 5.5.1.3 Nexus

The nexus represents the relationship among the Initiator, Target, Logical Unit and Command (Task)

• Nexus notation: I_T_L_Q nexus; where I =Initiator, T = Target, L = Logical Unit, Q = Command

There shall be at least one initiator device in the UFS definition. There shall only one target device, the UFS device. There shall be one or more logical units in a UFS device. The command identifier (i.e., the Q in an I_T_L_Q nexus) is assigned by the Initiator device to uniquely identify one command in the context of a particular I_T_L nexus, allowing more than one command to be outstanding for the I_T_L nexus at the same time.

An overlapped command occurs when a task manager or a task router detects the use of a duplicate I_T_L_Q nexus in a command before that I_T_L_Q nexus completes its command lifetime (see [SAM]). Concurrent overlapped commands are not allowed in UFS. Each command shall have an unique Task Tag. The UFS device is not required to detect overlapped commands.

### 5.5.1.4 SCSI Command Model

All command requests originate from application clients in an Initiator device. An application Client requests the processing of a command with the following procedure call:

• Service Response = Execute Command (IN (I_T_L_Q Nexus, CDB, Task Attribute, [Data-In Buffer Size], [Data-Out Buffer], [Data-Out Buffer Size], [CRN], [Command Priority]), OUT ([Data-In Buffer], [Sense Data], [Sense Data Length], Status, [Status Qualifier]))

Parameter fields in the UTP Command, Response, Ready-to-Transfer, Data-Out, Data-In UPIU headers contain the requisite information for the input and output arguments of the Execute Command procedure call in compliance with [SAM].

### 5.5.1.5 SCSI Task Management Functions

An application client requests the processing of a task management function with the following procedure call:

• Service Response = Function name (IN (Nexus), OUT ([Additional Response Information])

Parameters fields in the UTP Task Management Request and UTP Task Management Response headers contain the requisite information for the input and output arguments of the Task Management Function procedure call in compliance with [SAM].

# 5.6 UFS Application and Command Layer

UFS interface is designed to be protocol agnostic interface. However, as mentioned previously, SCSI has been selected as the baseline protocol layer for this standard. Descriptors are available to identify and select the appropriate protocol for UFS interface.

The primary functions of the Command Set Layer are to establish a method of data exchange between the UFS host and UFS device and to provide fundamental device management capability. SCSI SBC and SPC commands are the baseline for UFS. UFS will not modify the SBC and SPC Compliant commands. The goal is to maximize re-use and leverage of the software codebase available on platforms (PC, netbook, MID) that are already supporting SCSI.

Options are available to define UFS Native commands and extension as needed.

UFS SCSI command set includes:

1. SBC compliant commands [SBC]:
   • FORMAT UNIT
   • READ (6) and READ (10)
   • READ CAPACITY (10)
   • REQUEST SENSE
   • SEND DIAGNOSTIC
   • UNMAP
   • WRITE (6) and WRITE (10)

2. SPC compliant commands [SPC]:
   • INQUIRY
   • REPORT LUNS
   • READ BUFFER
   • TEST UNIT READY
   • WRITE BUFFER
   • SECURITY PROTOCOL IN and SECURITY PROTOCOL OUT

3. SCSI operational commands for UFS applications and compatible with existing SCSI driver
   • MODE SELECT (10) and MODE SENSE (10)
   • PRE-FETCH (10)
   • START STOP UNIT
   • SYNCHRONIZE CACHE (10)
   • VERIFY (10)

4. Value-added optional commands for UFS:
   • READ (16), WRITE(16), PRE-FETCH (16), SYNCHRONIZE CACHE (16), and READ CAPACITY(16).

NOTE These commands support logical units with larger capacities having an 8-byte LBA field.

Refer to clause 11, UFS Application (UAP) Layer – SCSI Commands, for more details.

---
*JEDEC Standard No. 220G*
*Page 19*