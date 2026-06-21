# 13 UFS Functional Descriptions

## 13.1 UFS Boot

### 13.1.1 Introduction

Some computing systems can have the need to download the system boot loader from an external non-volatile source. This task can be accomplished through an internal boot ROM contained in the host SOC whose code when executed determines a minimal initialization of the system to start the boot code transfer. Several features of the boot functionality can be configured in order to be adapted to different system requirements.

Moreover specific features to ensure boot data integrity and no corruption of boot code are defined.

### 13.1.2 Boot Configuration

During boot operation the UFS host controller retrieves the system boot code stored in the UFS device. In this version of the standard, the boot mechanism is defined for a point-to-point topology (see Figure 13.1).

[**Figure 13.1 — UFS System Diagram**: A diagram showing the Host SOC containing four components: Host CPU (teal), DRAM Controller (dark blue), DRAM (green), and UFS Host Controller (dark blue). The UFS Host Controller connects to an external UFS Device (orange) via bidirectional communication links. Green arrows indicate downstream communication from host to device, while red arrows indicate upstream communication from device to host.]

Two logical units (Boot LU A, Boot LU B) can be used to store the boot code, but only one of them will be active during the boot process. Any logical unit can be configured as "Boot LU A" or "Boot LU B". No more than one logical unit may be configured as "Boot LU A", no more than one logical unit may be configured as "Boot LU B". The logical unit active during boot is mapped onto the Boot well known logical unit (W-LUN = 30h) for read access. In this way, when the host updates the boot code, a fix logical unit number is kept when the active logical unit is swapped from A to B or vice versa.

---
JEDEC Standard No. 220G
Page 354

# 13.1.2 Boot Configuration (cont'd)

Several configurable fields of the Device Descriptor and the Unit Descriptors determine the device behavior during boot. Device Descriptor and Unit Descriptors are configured by writing the Configuration Descriptor.

For a UFS bootable device, the boot feature is enabled if bBootEnable field in the Device Descriptor is set to 01h or 02h.

The characteristics of the logical units used during boot are configured setting the corresponding fields of the Configuration Descriptor. (See 14.1.5.3)

The number of allocation units (dNumAllocUnits) field configures the logical unit size, and the boot logical unit ID (bBootLunID) field allows to designate the logical unit as being "Boot LU A" or "Boot LU B".

The logical unit active during the boot shall be configured by writing the bBootLunEn attribute, as described in Table 13.1.

## Table 13.1 — bBootLunEn Attribute

| bBootLunEn | Description |
|------------|-------------|
| 00h | Boot LU A = disabled<br>Boot LU B = disabled |
| 01h | Boot LU A = enabled<br>Boot LU B = disable |
| 02h | Boot LU A = disable<br>Boot LU B = enabled |
| Others | Reserved |

The host should not attempt to set bBootLunEn to 'Reserved' values, and UFS device shall generate an error in case of an attempt to set 'Reserved' values and not execute the request.

When bBootLunEn attribute is 00h the boot feature is disabled, the device behaves as if bBootEnable would be equal to zero.

The boot feature is critical for the initialization of the platform and it is important that the boot feature will not be disabled unintentionally.

When bBootEnable is provisioned to 02h, the device is in permanent-bootable configuration in which a Query Request to change bBootLunEn value from 01h or 02h to 00h shall fail and and the Query Response field shall be set to 'General failure (FFh). In this configuration, the device still enable transitions of bBootLunEn between 01h and 02h, and vice versa.

The active boot logical unit will be mapped onto the Boot well known boot logical unit (W-LUN = 30h) once the bBootLunEn has been properly configured.

Figure 13.2 shows an example of a UFS device having eight logical units: LU 1 and LU 4 are configured, respectively, as "Boot LU A" and "Boot LU B". In particular, LU 1 is the active one (bBootLunEn = 01h).

---

*JEDEC Standard No. 220G*  
*Page 355*

# JEDEC Standard No. 220G
Page 356

## 13.1.2 Boot Configuration (cont'd)

[**Figure Description**: A diagram showing UFS Device Memory Organization for Boot. The left side shows a vertical stack of logical units 0-7, with units 1 and 4 highlighted as "Boot LU A" and "Boot LU B" respectively. Below these are three additional units: "REPORT LUN well known logical unit", "DEVICE well known logical unit", and "RPMB well known logical unit". An arrow points from "BOOT well known logical unit" to "Logical unit 1 → Boot LU A".]

**bBootLunID in Unit Descriptors**

| LU | Value | Description |
|----|-------|-------------|
| 0  | 00h   | Disabled    |
| 1  | 01h   | Boot LU A   |
| 2  | 00h   | Disabled    |
| 3  | 00h   | Disabled    |
| 4  | 02h   | Boot LU B   |
| 5  | 00h   | Disabled    |
| 6  | 00h   | Disabled    |
| 7  | 00h   | Disabled    |

bBootLunEn = 01h. "Boot LU A" is the active logical unit for boot. Therefore, the logical unit 1 is mapped onto the Boot well known logical unit (W-LUN=30h, LUN field in UPIU = B0h).

**Figure 13.2 — Example of UFS Device Memory Organization for Boot**

# 13.1.3 Initialization and Boot Code Download Process

The initialization and boot code download process is made up of the following phases: partial initialization, boot transfer and initialization completion.

## 13.1.3.1 Partial Initialization

The partial initialization phase starts after power on, or hardware reset, or EndPointReset and involves the entire UFS stack. At the end of this phase, the UniPro boot sequence shall be completed, and the UTP layer shall be capable of accessing Device Descriptor (if the bDescrAccessEn field of the Device Descriptor is '01h') and exchanging UPIU for READ command and TEST UNIT READY command. If the bDescrAccessEn field is '00h' descriptors will be accessible only after the initialization completion phase.

Each single layer in the UFS protocol stack executes the initialization process on both UFS host and UFS device sides.

**a) Physical Layer (M-PHY)**

After reset events, the physical layer will move from DISABLED state to HIBERN8 state.

**b) Link Layer (UniPro)**

On host and device side UniPro boot sequence takes place:
1) The UniPro stack is reset using the DME_RESET.req primitive.
2) Wait until the reset completion is indicated by the DME_RESET.cnf_L primitive.
3) The UniPro stack is enabled using the DME_ENABLE.req primitive.
4) Wait until the enable completion is indicated by the DME_ENABLE.cnf_L primitive.
5) The UniPro Link StartUp sequence is initiated using the DME_LINKSTARTUP.req primitive. The UniPro Link Startup consists of a series of multiphase handshakes to establish initial link communication in both directions between UFS host and device.
6) Wait until the link startup completion is indicated by the DME_LINKSTARTUP.cnf_L primitive.

**c) UFS Transport Layer (UTP)**

At the end of the UFS Interconnect Layer initialization on both host and device side, the host shall send a NOP OUT UPIU to verify that the device UTP Layer is ready.

For some implementations, the device UTP layer may not be initialized yet, therefore the device may not respond promptly to NOP OUT UPIU sending NOP IN UPIU.

The host waits until it receives the NOP IN UPIU from the device. When the NOP IN UPIU is received, the host is acknowledged that the UTP layer on the device is ready to execute UTP transactions.

**d) Link Configuration**

The host may configure the Link Attributes (i.e., Gear, HS Series, PWM Mode in Rx and Tx) by using DME primitives at UniPro level.

---

JEDEC Standard No. 220G  
Page 357

# JEDEC Standard No. 220G
Page 358

## 13.1.4.1 Partial Initialization (cont'd)

### e) Device Descriptor Reading

The UFS host may optionally discover relevant device info for the boot process by accessing the Device Descriptor (i.e., Device Class/Subclass, Boot Enable, Boot LUs size, etc.). The UFS host is allowed to access the Device Descriptor only if the bDescrAccessEn is '01h', otherwise this descriptor can be accessed only after the device has fully completed its initialization.

### 13.1.1.2 Boot Transfer

The following steps can be executed only if bBootEnable field is set.

**Boot code download**

At first, the UFS host issues a TEST UNIT READY command to the Boot well known logical unit to verify if the latter can be accessed. If the command succeeds, the UFS host reads the Boot well known logical unit by issuing SCSI READ commands and the UFS device will start to send the boot code on the Upstream Link. During this phase only the Boot well known logical unit is accessible: this logical unit shall accept read commands, while other logical units may not be ready.

### 13.1.1.3 Initialization Completion

After the host has completed the boot code download from the Boot well known logical unit, the initialization process proceeds as described in the following. The host sets the fDeviceInit flag to "01h" to communicate to the UFS device that it can complete its initialization. The device shall reset the fDeviceInit flag when the initialization is complete. The host polls the fDeviceInit flag to check the completion of the process. When the fDeviceInit is reset, the device is ready to accept any command.

# JEDEC Standard No. 220G
Page 359

## 13.1.3.3 Initialization Completion (cont'd)

[This is a sequence diagram showing the Device Initialization and Boot Procedure between UFS Host and UFS Device. The diagram shows the following sequence:

**Initial State:**
- UFS Host and UFS Device are shown as two columns
- Power-on Reset / HW Reset / EndPointReset occurs
- Both sides show "No active tasks in the device UFS Descriptors, Attributes and Flags set to their default value UniPro attributes reset"
- Note: "In case of LS-LSS, M-PHY layer initialization on both sides shall lead to PWM-G1 speed gear. In case of HS-LSS, M-PHY layer initialization on both sides shall lead to HS-G1 speed gear."
- "UniPro Boot sequence and Attributes configuration"

**Communication Sequence:**
1. **NOP OUT/IN:** Host sends NOP OUT UPIU, Device responds with NOP IN UPIU

2. **Query Request (READ DESCRIPTOR):** 
   - UFS host queries the UFS device Descriptor
   - bDeviceClass, bDeviceSubClass – Mass Storage Bootable Device
   - bBootEnable – Boot process enabled
   - bBootLunEn – LU configured for Boot
   - bBootLssID – RFU
   - This operation is optional and allowed only if bDescAccessEn is equal to one.

3. **TEST UNIT READY (Boot LU):**
   - The host issues a TEST UNIT READY to check if the Boot W-LU is operational
   - This operation is optional if the host does not read the Boot W-LU
   - In case the LU is not ready or is busy, the device reports UNIT ATTENTION with CHECK CONDITION status to the host.

4. **SCSI READ (Boot LU):**
   - Host reads the boot code from the Boot well known logical unit by issuing one or more SCSI READ commands

5. **READ BUFFER (Boot LU):**
   - The host may issue multiple READ BUFFER commands (Mode 1Ch) in order to read device error log before device full initialization

6. **Query Request (SET FLAG fDeviceInit):**
   - The host enables the device initialization completion by setting fDeviceInit flag.

7. **Query Request (READ FLAG fDeviceInit):**
   - fDeviceInit flag is polled by the host to verify the device initialization completion.
   - At the end of the initialization process, fDeviceInit shall be reset by the device]

**Figure 13.3 — Device Initialization and Boot Procedure Sequence Diagram**

# JEDEC Standard No. 220G
Page 360

## 13.1.3.3 Initialization Completion (cont'd)

### Table 13.2 — Valid UPIUs and SCSI Commands for Each Initialization Phase

| Phase | Event | Valid UPIU | Valid SCSI command |
|-------|--------|------------|-------------------|
| Before Initialization | Power On Reset / HW Reset / EndPointReset M-PHY layer initialization | None | None |
| UIC Layer Initialization Phase | UniPro Boot sequence and UIC Layer Attributes configuration | None | None |
| UTP Layer Initialization Phase | Receive a single NOP OUT UPIU Send NOP IN UPIU for response to NOP OUT UPIU | NOP OUT UPIU NOP IN UPIU | None |
| Boot W-LU Ready Phase (Optional) | Read Device Descriptor (Optional) (1) | QUERY REQUEST UPIU (READ DESCRIPTOR Device Descriptor) | None |
|  | Boot Transfer (Optional) (2) | COMMAND UPIU for Boot W-LU | INQUIRY, REQUEST SENSE, TEST UNIT READY, READ (6), READ (10), READ (16) (3), READ BUFFER |
| Application Layer Initialization Phase | Receive QUERY REQUEST UPIU (SET FLAG fDeviceInit to '01h') Send QUERY RESPONSE UPIU with fDeviceInit = '00h' | QUERY REQUEST UPIU (SET FLAG fDeviceInit to 01h') QUERY REQUEST UPIU (READ FLAG fDeviceInit) QUERY RESPONSE UPIU | None |
| Device initialization completed Phase | Any normal operation | Any supported UPIU | Any supported SCSI commands |

NOTE1 Device Descriptor may be read only if bDescrAccessEn is set to '01h'.
NOTE2 Boot well-known logical unit may be read if bBootEnable is set to '01h' or '02h', at least one logical unit is configured for boot (bBootLunEn) and bBootLunID selects the desired boot logical unit.
NOTE3 READ (16) command support is optional.

## 13.1.4 Initialization Process without Boot Code Download

If the boot process is not enabled on the UFS device, or it is not supported by the device class, or the host does not need to transfer the boot code, the host executes the initialization process as described in 13.1.3, omitting the boot transfer phase.

## 13.1.5 Boot Logical Unit Operations

The Boot well known logical unit is read only, therefore the boot code can be stored only writing the boot logical units (A or B).

Boot logical units are written to store the boot code during the system manufacturing phase and they may be also updated during the system lifecycle. These logical units can be read to verify their content.

# JEDEC Standard No. 220G
## Page 361

### 13.1.6 Boot Logical Unit Operations (cont'd)

Therefore the following operations are permitted on the Boot logical units:

1. boot code write – for boot code upload/update

2. boot code read – to verify the content programmed

3. boot code removal – to remove the content of the Boot logical unit

These operations can be executed regardless the bBootEnable field value in the Device Descriptor.

Boot logical units (A or B) can be write protected using the methods described in 12.3, Device Data Protection.

### 13.1.6 Configurability

The boot process is configurable through several parameters in the Configuration Descriptor (See 14.1.5.3) to adapt it to different usage models and system features.

The following parameters refer to boot capabilities.

• Device Descriptor parameters:
  - bBootEnable (Boot Enable)
  - bDescrAccessEn (Descriptor Access Enable)
  - bInitPowerMode (Initial Power Mode)
  - bInitActiveICCLevel (Initial Active ICC Level)

• Unit Descriptor parameters for Boot LU A and Boot LU B:
  - bLUEnable (Logical Unit Enable)
  - bBootLunID (Boot LUN ID)
  - bLUWriteProtect (Logical Unit Write Protect)
  - bMemoryType (Memory Type)
  - dNumAllocUnits (Number of Allocation Units)
  - bDataReliability (Data Reliability)
  - bLogicalBlockSize (Logical Block Size)
  - bProvisioningType (Provisioning Type)

**NOTE** These parameters are non volatile and they may be programmed during the system manufacturing phase.

In addition to the parameters mentioned, the following attributes are relevant for device initialization and boot
• bBootLunEn (Boot LUN Enable)
• bRefClkFreq (Reference Clock Frequency value)