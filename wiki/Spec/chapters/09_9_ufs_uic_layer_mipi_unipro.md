# 9 UFS UIC Layer: MIPI Unipro

## 9.1 Overview

UFS builds on the MIPI Unified Protocol (UniPro) as its Interconnect (Service Delivery Subsystem) to provide basic transfer capabilities to the UFS Transport Protocol (UTP) Layer. On the data plane UTP and UniPro communicate via the Service Primitives of the UniPro Transport Layer CPorts (T_CO_SAPs). Control plane interaction (e.g., discovery, enumeration and configuration of the Link) between higher layer protocol functions of UFS and UniPro are accomplished using the Device Management Entity Service Primitives as defined by the UniPro specification.

## 9.2 Architectural Model

UniPro is internally composed of several sub-layers which are all well defined by the MIPI UniPro specification [MIPI-UniPro]. In the context of UFS the entire UniPro protocol stack shall be viewed as a black box model (see Figure 9) to the greatest extent possible. The following sub-clauses therefore only:

• Specify number and type of the required interfaces between UFS and UniPro

• Specify the mapping between UFS and UniPro addressing scheme

• Select optional features and definable attributes of the UniPro specification

[Figure 9.1 shows two diagrams side by side:
(a) UniPro Internal Layering View - A detailed layered diagram showing:
- Application Protocol layer at the top
- Transport (L4) layer in yellow
- Network (L3) layer in orange
- Data Link (L2) layer in red
- PHY Adapter (L1.5) layer in dark red
- PHY Tx and PHY Rx components at the bottom in red
- DME component on the left side spanning multiple layers

(b) UniPro Black Box View - A simplified black box representation of the same protocol stack]

**Figure 9.1 — UniPro Internal Layering View (a) and UniPro Black Box View (b)**

---
JEDEC Standard No. 220G
Page 61

# 9.3 UniPro/UFS Transport Protocol Interface (Data Plane)

UniPro provides CPorts as conceptual interfaces to applications or protocol layers on top of UniPro. CPorts can be viewed as instantiations of the T_CO_SAPs as specified in 8.8 of the UniPro specification. The physical implementation of T_CO_SAP was deliberately not defined in MIPI as implementers should be free to choose, e.g., a SW implementations of higher UniPro layers, HW implementations based on buffering per CPort or DMA channels per CPort, etc.

A Service Access Point (SAP) provides Service Primitives (SP) which can be used by specifications of applications or protocols as UFS on top of UniPro to define their interactions. For more information on the concept of SAP/SP in protocol specifications please refer to Annex C of the UniPro specification.

The T_CO_SAP provides the following core data transfer service primitives (see UniPro specification 8.8.1):

• **T_CO_DATA.req( MessageFragment, EOM)**
  ○ Issued by service user of UniPro to send a message (Fragment)

**NOTE** Whenever a UFS layer requests the UIC layer to transfer data that UFS layer shall ensure that the last fragment of said data will be transmitted with the EOM flag set. One way to ensure such a behavior is for the UFS layer to invoke this UIC data transfer service primitive only once per atomic protocol data unit (e.g., once per UFS Transport Layer 'UPIU') with the EOM flag set to 'true' always.

• **T_CO_DATA.cnf_L( L4CPortResultCode )**
  ○ Issued by UniPro to report the result of a Message (Fragment) transfer request

• **T_CO_DATA.ind( MessageFragment, EOM, SOM, MsgStatus )**
  ○ Issued by UniPro to deliver a received Message (Fragment) towards the service user
  ○ EOM informs the service user that this is the last Message Fragment (EndOfMessage)
  ○ SOM informs the service user that this is the first Message Fragment (StartOfMessage)

• **T_CO_DATA.rsp_L( )**
  ○ Issued by a service user of UniPro to report readiness to receive the next Message (Fragment)

## 9.3.1 Flow Control

UFS will not make use of the End-to-End Flow Control feature of UniPro for data communication as the UFS Transport Layer already avoids any overflow by a strict client-server communication model, tagged command queues and Device side throttling of Data transfers. Therefore UFS will not use the T_CO_FLOWCONTROL service primitive of UniPro and hence does not require its implementation.

## 9.3.2 Object Sizes

A UniPro Message can be of any size and its content is not interpreted in any way by UniPro. Messages can be delivered from/to UniPro as multiple Message Fragments.

A Message Fragment is a portion of a Message that can be passed to, or received by, a CPort. Received Fragments are not generally identical to transmitted Fragments. Message Fragments may or may not carry an End-of-Message (EoM) flag.

A Message Fragment shall have maximum of T_MTU bytes to avoid further splitting in lower layers.

---

**JEDEC Standard No. 220G**  
**Page 62**

# 9.4 UniPro/UFS Control Interface (Control Plane)

UniPro provides access to its Device Management Entity (DME) via a Service Access Point (DME SAP) with the following services exposed to UFS allowing control of properties and the behavior of UniPro:

**DME Configuration Primitives**

• **DME_GET / DME_SET**
  ○ Provide read/write access to all UniPro and M-PHY attributes of the local UniPort

• **DME_PEER_GET (optional) / DME_PEER_SET (optional)**
  ○ Provide read/write access to all UniPro and M-PHY attributes of the peer UniPort

**NOTE** The order in which attributes are set is in some cases relevant for UniPro's correct operation. Therefore higher UFS layers shall preserve the ordering of DME Configuration Primitives invocations by UFS applications. If internally generated by UFS itself, DME Configuration Primitives shall be issued correctly ordered as defined by the UniPro specification.

**DME Control Primitives**

• **DME_POWERON (optional) / DME_POWEROFF (optional)**
  ○ Allow to power up or power down all UniPro layers (L1.5 through L4)

• **DME_ENABLE**
  ○ Allow enabling of the entire local UniPro stack (UniPro L1.5 -L4)

• **DME_RESET**
  ○ Allows to reset the entire local UniPro stack (UniPro L1.5-L4)

• **DME_ENDPOINTRESET**
  ○ Allows sending an end-point reset request command to a link end point.

• **DME_LINKSTARTUP**
  ○ Allows locally to startup the Link and informs about remote link startup invocation

• **DME_HIBERNATE_ENTER / DME_HIBERNATE_EXIT**
  ○ Allow to put the entire Link into HIBERNATE power mode and to wake the Link up
    ▪ Affects the local and the peer UniPort (UniPro L1.5-L4 and M-PHY)

**NOTE** After exit from Hibernate all UniPro Transport Layer attributes (including L4 T_PeerDeviceID, L4 T_PeerCPortID, L4 T_ConnectionState, etc.) will be reset to their reset values. All required attributes must be restored properly on both ends before communication can resume.

• **DME_POWERMODE**
  ○ Allows to change the power mode of one or both directions of the M-PHY Link

• **DME_TEST_MODE (optional)**
  ○ Allows to set the peer UniPro Device on the Link in a specific test mode

• **DME_LINKLOST**
  ○ Indication of the UniPro stack towards higher layers that the Link has been lost

• **DME_ERROR**
  ○ Indication of the UniPro stack towards higher layers that an error condition has been encountered in one of the UniPro Layers

---
*JEDEC Standard No. 220G*  
*Page 63*

# 9.5 UniPro/UFS Transport Protocol Address Mapping

UniPro has fundamentally two levels of addressing to control the exchange of information between remote UniPro entities.

**Network Layer (L3): Device ID, lowest level of addressability**

• Provided for future UniPro networks of devices. During connection establishment the side creating a connection uses this value to select the physical entity on the remote end of the connection. It shall be considered static for the lifetime of this connection.

**Transport Layer (L4): CPort ID, highest level of end-to-end addressability**

• During connection establishment the side creating a connection uses this value to select the logical entity inside the targeted UniPro device on the remote end of the connection. It shall be considered static for the lifetime of this connection.

UFS adopts the addressing notation of the SCSI Architecture Model [SAM] based on Nexus definition.

The Nexus (I_T_L_Q) is composed of:

• Initiator Port Identifier (I)

• Target Port Identifier (T)

• Logical Unit Number (L)

• Command Identifier (Q).

An I_T_L_Q Nexus uniquely defines a specific command slot (Q) inside a specific Logical Unit (L) connected to a specific Device Target Port (T) accessed through a specific Host Initiator Port (I).

UFS Interconnect Layer addresses (Device ID and CPort ID) are only related to the I_T part of the Nexus.

This standard only requires and uses a single UniPro CPort on the device side and on the host side.

**Mapping Rules**

• UFS Initiator Port Identifier (I) shall be 20 bits wide and UFS Target Port Identifier (T) shall be 20 bits wide and

  ○ UFS Initiator/Target Port Identifier shall contain the UniPro Network Layer Device ID of the entity (host or device) containing said UFS Port

    ▪ The UniPro Network Layer Device ID reset value shall be 0 for the Host
    ▪ The UniPro Network Layer Device ID reset value shall be 1 for the Device

  ○ UFS Initiator/Target Port Identifier contains the UniPro Transport Layer CPort ID which said UFS Port uses to communicate to the remote entity

    ▪ The UniPro Transport Layer CPort ID reset value shall be 0 for the Host
    ▪ The UniPro Transport Layer CPort ID reset value shall be 0 for the Device

• UFS Initiator Port Identifier shall contain the Initiator ID field according to Table 9.1.

---
*JEDEC Standard No. 220G*  
*Page 64*

# 9.6 UniPro/UFS Transport Protocol Address Mapping (cont'd)

Table 9.1 defines the Initiator Port Identifier (I) and Target Port Identifier (T) for UFS.

## Table 9.1 — UFS Initiator and Target Port Identifiers

| UFS Port | UFS Port IDs |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |  |
|----------|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
|          | 19| 18| 17| 16| 15| 14| 13| 12| 11| 10| 9 | 8 | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
| Initiator Port Identifier (I) | Device ID = 000 0000b | CPort ID = 0 0000b |   |   |   | Initiator ID |   |   |   |   |
|          |   |   |   |   |   |   |   |   |   |   |   |   |   |   | EXT_IID | IID |   |   |   |   |
| Target Port Identifier (T) | Device ID = 000 0001b | CPort ID = 0 0000b |   |   | 0000b |   | 0000b |   |   |   |

The Initiator ID is comprised of two fields in the UPIU (as depicted in the figure above), IID as the least significant nibble and EXT_IID as the most significant nibble.

The single UniPro connection between the UTP layer of a UFS host and the UTP layer of a UFS device can be uniquely identified by the UFS L_T Nexus above.

**NOTE** The UFS L_T Nexus elements (Device IDs and CPort IDs) can be modified by the Host after reset using the DME Service Primitives:

• The "I" element may be modified by the Host using the DME_SET primitive

• The "T" element may be modified by the Host using DME_PEER_SET primitive

All attributes of the CPort on the Host side (including, e.g., "T_ConnectionState") can be checked and modified by the Host using the DME_GET and DME_SET primitives after reset.

All attributes of the CPort on the Device side (including, e.g., the "T_ConnectionState") can be checked and modified by the Host using the DME_PEER_GET and DME_PEER_SET primitives after reset.

## 9.7 Options and Tunable Parameters of UniPro

MIPI UniPro has been designed as a versatile protocol specification and as such has several options and parameters which an application like UFS should specify for its specialized UniPro usage scenario. Annex E of the UniPro specification details all of the possible choices.

The remaining sub-clauses define the specific requirements towards these options and parameters for this version of UFS standard. They apply to UniPro implementations for the UFS host side as well as to UniPro implementations for the UFS device side if not explicitly stated otherwise.

### 9.7.1 UniPro PHY Adapter

For MIPI M-PHY related attribute values and implementation options as defined by UFS refer to 8.7, UFS PHY Attributes.

In UFS system, host and device use the same reference clock, therefore skip symbol insertion functionality is not used and its implementation is optional.

---

JEDEC Standard No. 220G  
Page 65

# JEDEC Standard No. 220G
Page 66

## 9.6.1 UniPro PHY Adapter (cont'd)

UFS device shall support the following physical lane connections:

• One lane
  ○ Tx physical lane 0 connected to Rx physical lane 0
• Two lanes
  ○ Tx physical lane 0 connected to Rx physical lane 0
  ○ Tx physical lane 1 connected to Rx physical lane 1

[Figure 9-2 shows Physical Lane Connections with six diagrams:
1. 2-lane UFS Host (Tx: PL#1, PL#0 and Rx: PL#1, PL#0) connected to 2-lane UFS Device (Rx: PL#1, PL#0 and Tx: PL#1, PL#0)
2. 2-lane UFS Host (Tx: PL#1, PL#0 and Rx: PL#1, PL#0) connected to 2-lane UFS Device (PL#1, PL#0 with Rx and Tx)
3. 2-lane UFS Host (Tx: PL#1, PL#0 and Rx: PL#1, PL#0) connected to 1-lane UFS Device (Rx: PL#0 and Tx: PL#0)
4. 1-lane UFS Host (Tx: PL#0 and Rx: PL#0) connected to 2-lane UFS Device (PL#1, PL#0 with Rx and Tx)

The diagrams show bidirectional connections between physical lanes using purple arrows.]

**Figure 9-2 — Physical Lane Connections**

## 9.7.2 UniPro Data Link Layer

• Shall implement the Data Link Layer Traffic Class "Best Effort" (TC 0)

• Data Link Layer Traffic Class 1 (TC1: 'Low Latency') is not required

• TX preemption capability is not required

• Shall provide at least DL_MTU bytes of Data Link Layer RX and TX buffering

• Shall support transmission and reception of maximum sized L2 frames (DL_MTU)

## 9.7.3 UniPro Network Layer

• Shall support transmission and reception of maximum sized L3 packets (N_MTU)

# 9.7.4 UniPro Transport Layer

• UFS Hosts and UFS Devices shall implement at least 1 CPort

  **NOTE** This standard only requires and uses a single CPort on either side of the Link.

• UFS does not mandate any CPort arbitration scheme beyond the UniPro default if more than one CPort is implemented

• Shall support the UniPro Test Feature

• UFS does not require the UniPro End-to-End Flow Control mechanism

  ○ UFS will not use 'Controlled Segment Dropping' (CSD)
  
    ▪ Hence CSD shall be disabled

• UFS will not use "CPort Safety Valve" (CSV). Hence, CSV shall be disabled.

• Shall support transmission and reception of maximum sized L4 segments (T_MTU).

## 9.7.5 UniPro Device Management Entity Transport Layer

DME service primitives provide the means to

• retrieve or set attributes,
• control the reset and run mode of the entire UniPro protocol stack.

UFS Hosts and UFS Devices shall implement the following DME service primitives:

• DME_GET, DME_SET,
• DME_ENABLE,
• DME_RESET, DME_ENDPOINTRESET,
• DME_LINKSTARTUP, DME_LINKLOST,
• DME_HIBERNATE_ENTER, DME_HIBERNATE_EXIT,
• DME_POWERMODE,
• DME_ERROR.

**UFS Hosts**

• shall implement DME_PEER_GET primitive and DME_PEER_SET primitive, which are optional in [MIPI-UniPro].

**UFS Devices**

• shall not use DME_SET primitive to modify the local PA_PWRMode attribute,
• shall use DME_RESET only in the following cases: at power-on or hardware reset, or after a DME_LINKLOST.ind,
• shall not use the following primitives
  ○ DME_PEER_GET.req, DME_PEER_SET.req,
  ○ DME_POWERON.req, DME_POWEROFF.req,
  ○ DME_ENDPOINTRESET.req,
  ○ DME_HIBERNATE_ENTER.req, DME_HIBERNATE_EXIT.req,
  ○ DME_POWERMODE.req, DME_TEST_MODE.req.

---
*JEDEC Standard No. 220G*
*Page 67*

# 9.7.6 UniPro Attributes

To optimize the UFS Boot procedure the UFS UIC implementation shall use the default reset values for all UniPro Attributes as defined by the MIPI UniPro specification. As an exception to this, the reset values of Network Layer Attributes and specific Attributes for CPort 0 shall reflect the settings which have been defined in the sub-clauses above and therefore shall contain the values as depicted in Table 9.2.

## Table 9.2 — UniPro Attribute

| UniPro Attribute Name | UFS Host Reset Value | UFS Device Reset Value |
|----------------------|---------------------|------------------------|
| N_DeviceID | 0 | 1 |
| N_DeviceID_valid | TRUE | TRUE |
| T_PeerDeviceID | 1 | 0 |
| T_PeerCPortID | 0 | 0 |
| T_CPortFlags | 6<br>(E2E_FC off, CSD off,<br>CSV off) | 6<br>(E2E_FC off, CSD off,<br>CSV off) |
| T_ConnectionState | 1 (CONNECTED) | 1 (CONNECTED) |
| T_TrafficClass | 0 | 0 |
| PA_MaxDataLanes | 2 | 2 |
| PA_AvailTxDataLanes | 1, 2 | 1, 2 |
| PA_AvailRxDataLanes | 1, 2 | 1, 2 |

**NOTE** A UFS device will support either: one TX lane and one RX lane or two TX lanes and two RX lanes

---

JEDEC Standard No. 220G  
Page 68

# 10 UFS Transport Protocol (UTP) Layer

## 10.1 Overview

The SCSI Architecture Model [SAM] is used as the general architectural model for UTP, and the SAM Task Management functions for task management. A task is generally a SCSI command or service request. While the model uses the SCSI command set as the command set, it is not necessary to use SCSI commands exclusively.

The SAM architecture is a client-server model or more commonly a request-response architecture. Clients are called Initiator devices and servers are called Target devices. Initiator devices and Target devices are mapped into UFS physical network devices. An Initiator device issues commands or service requests to a Target device that will perform the service requested. A Target device is a UFS device. A UFS device will contain one or more Logical Units. A Logical Unit is an independent processing entity within the device.

A client request is directed to a single Logical Unit within a device. A Logical Unit will receive and process the client command or request. Each Logical Unit has an address within the Target device called a Logical Unit Number (LUN).

Communication between the Initiator device and Target device is divided into a series of messages. These messages are formatted into UFS Protocol Information Units (UPIU) as defined within this standard. There are a number of different UPIU types defined. All UPIU structures contain a common header area at the beginning of the data structure (lowest address). The remaining fields of the structure vary according to the type of UPIU.

A Task is a command or sequence of actions that perform a requested service. A Logical Unit contains a task queue that will support the processing of one or more Tasks. The Task queue is managed by the Logical Unit. A unique Task Tag is generated by the Initiator device when building the Task. This Task Tag is used by the Target device and the Initiator device to distinguish between multiple Tasks. All transactions and sequences associated with a particular Task will contain that Task Tag in the transaction associated data structures.

Command structures consist of Command Descriptor Blocks (CDB) that contain a command opcode and related parameters, flags and attributes. The description of the CDB content and structure are defined in detail in [SAM], [SBC] and [SPC] INCITS T10 draft standards.

A command transaction consists of a Command, an optional Data Phase, and a Status Phase. These transactions are represented in the form of UPIU structures. The Command Phase delivers the command information and supporting parameters from the Initiator device to the Target device. If a Data Phase is required, the direction of data flow is relative to the Initiator device. A data WRITE travels from Initiator device to Target device. A data READ travels from Target device to Initiator device. At the completion of the command, the Target device will deliver a response to the Initiator device during the Status Phase. The response will contain the status and a UFS response status indicating successful completion or failure of the command. If an error is indicated the response will contain additional detailed UFS error information.

---
JEDEC Standard No. 220G  
Page 69