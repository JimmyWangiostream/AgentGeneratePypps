# JEDEC Standard No. 220G
## Page 362

### 13.1.7 Security

#### 13.1.7.1 Boot Area Protection

Boot areas might be protected in order to avoid boot code alteration by a third party: the write protection mechanism for the boot logical units can be defined configuring the corresponding bLUWriteProtect parameter of the Unit Descriptor.

In particular, the boot logical units may be permanently write protected or power-on write protected. In case of power-on write protection, the boot logical units can be written only when the fPowerOnWPEn flag is equal to zero.

### 13.2 Logical Unit Management

#### 13.2.1 Introduction

The functionality aims to provide a mechanism to let an external application define and use a virtual memory organization which could easily fit different usage models in a versatile way.

Besides segmenting the available addressable space, the mechanism introduces the possibility of differentiating each logical unit through dedicated functionalities and features.

This sub-clause describes the procedure to configure the UFS device in terms of: number of logical units, logical unit size, logical unit memory type, etc. Security features can be configured as described in clause 12, UFS Security.

A UFS device can be organized in different logical units. Each one represents an autonomous computing entity with independent logical address ranges and singularly accessible.

Moreover, each logical unit can be defined for a specified use and with peculiar attributes (i.e., memory type) in order to be adapted to different UFS host usage models and operating systems requirements.

#### 13.2.2 Logical Unit Features

UFS device address space is organized in several memory areas configurable by the user. In particular, such memory areas are denoted as logical units and characterized by the fact that they have independent logical addressable spaces starting from the logical address zero.

In addition to the logical units, the UFS device supports the following well known logical units for specific purposes: UFS Device, REPORT LUNS, Boot and RPMB. Logical units are addressed by the LUN (logical unit number), while well known logical unit are addressed by the W-LUN (well known logical unit number).

# JEDEC Standard No. 220G
## Page 363

### 13.2.2 Logical Unit Features (cont'd)

[THIS IS FIGURE: A diagram showing UFS Device Memory Organization with the following structure:

- **Logical unit 0** (orange): LUN = 0h, Boot LU A, LU size, starting at Logical Address zero
- **Logical unit 1** (orange): LUN = 1h, Boot LU B Active LU for boot, LU size, starting at Logical Address zero  
- **Logical unit 3** (blue): LUN = 3h, LU size, starting at Logical Address zero
- **Logical unit 4** (blue): LUN = 4h, LU size, starting at Logical Address zero
- **Logical unit 7** (blue): LUN = 7h, LU size, starting at Logical Address zero
- **RPMB well known logical unit** (purple): W-LUN = 44h, LU size]

NOTE 1 The figure shows an example of device configuration in which LU 0 and LU 1 are used as boot logical units, and the logical units 3, 4 and 7 for code and data storage. LU 1 is the boot active logical unit and it may be accessed in read using the W-LUN = 30h (LUN field in UPIU = B0h).

**Figure 13.4 — Example of UFS Device Memory Organization**

Each logical unit will have a physical implementation on the non-volatile storage media

In particular, the UFS device shall support:

• The number of logical units specified by bMaxNumberLU. Each of them configurable as boot logical units with a maximum of two.

• One RPMB well known logical unit (W-LUN = 44h, LUN field in UPIU = C4h). RPMB well known logical unit may be further configured into up to four separate RPMB regions (RPMB region 0 - RPMB region 3).

Two logical units can be configured as boot logical unit, with only one of them active and readable through the Boot well known logical unit (W-LUN = 30h) for the execution of the system boot (see 13.2). The RPMB well known logical unit is accessed by authenticated operations by a well defined security algorithm (see 12.4). The other logical units will be used to fulfill other use cases.

# JEDEC Standard No. 220G
Page 364

## 13.2.2 Logical Unit Features (cont'd)

Common features of each logical unit are:

• Independent logical addressable spaces (starting from logical address zero up to the logical unit size).

• Configurable logical unit size.

The size of each logical unit is determined by the number of allocation units assigned to it: dNumAllocUnits parameter value of the Configuration Descriptor. The dNumAllocUnits is expressed in terms of allocation unit size (bAllocationUnitSize).

Moreover each logical unit is characterized by the memory type parameter which can be configured. Examples of memory types to differentiate logical unit properties are the following ones:

• Default type – regular memory characteristic.

• System Code type – a logical unit that is rarely updated (e.g., system files or binary code executable files or the host operating system image and other system data structures).

• Non-Persistent type – a logical unit that is used for temporary information (e.g., swap file extend the host virtual memory space).

• Enhanced Memory type – vendor specific attribute.

The definition of the Enhanced Memory type is left open in order to accomplish different needs and vendor specific implementations.

Mechanisms of write protection can be configured for each logical unit. Write protection feature types are:

• Permanent write protection (permanent read only).

• Power on write protection (write protection can be cleared with a power cycle or a hardware reset event).

Write protection is not available in the RPMB well known logical unit.

# 13.2.3 Logical Unit Configuration

The user shall configure the logical units of the UFS device according to the following rules:

• Maximum number of logical units is specified by bMaxNumberLU.

• One or two logical units can be configured as boot logical units.

When a UFS device is shipped only the following well known logical units will be available: UFS Device, REPORT LUNS and the RPMB. All other logical units shall be configured before they can be accessed.

The RPMB well known logical unit shall be configured by the device manufacturer before shipping the device. Only RPMB region 0 shall be enabled and bRPMBRegion0Size shall be set to the same size as the total RPMB well known logical unit size before shipping the device.

Logical units and RPMB regions may be configured writing the Configuration Descriptors. (See 14.1.3)

RPMB regions may be configured multiple times until the Configuration Descriptor is locked by setting bConfigDescrLock attribute value to 01h. RPMB key may be programmed any time when the target RPMB region is enabled, and may be programmed independent to whether the value of bConfigDescrLock attribute is set or not. When RPMB regions are re-configured with different configuration setting, the data which was previously written in any RPMB region shall be erased while RPMB key and RPMB write counter are maintained. To keep the compatibility to the previous version of the standard, RPMB region 0 is always enabled independent of configuration value of bRPMBRegionEnable.

The configuration of each logical unit and the configuration of RPMB regions may be retrieved by reading the corresponding Unit Descriptor.

It is recommended to execute logical unit configuration and RPMB region configuration during the system manufacturing phase.

---

JEDEC Standard No. 220G  
Page 365

# JEDEC Standard No. 220G
Page 366

## 13.2.3 Logical Unit Configuration (cont'd)

Table 13.3 summarizes the configurable parameters per logical unit. See 14.1.5, Descriptor Definitions, for details about these parameters.

### Table 13.3 — Logical Unit Configurable Parameters

| Configurable parameters |  | Logical Unit |
|---|---|---|
| **Name** | **Description** |  |
| bLUEnable | Logical Unit Enable | LU 0, …, Maximum LU specified by bMaxNumberLU |
| bBootLunID | Boot LUN ID | LU 0, …, Maximum LU specified by bMaxNumberLU |
| bLUWriteProtect | Logical Unit Write Protect | LU 0, …, Maximum LU specified by bMaxNumberLU |
| bMemoryType | Memory Type | LU 0, …, Maximum LU specified by bMaxNumberLU |
| dNumAllocUnits | Number of allocation units assigned to the logical unit. The value shall be calculated considering the capacity adjustment factor of the selected memory type. | LU 0, …, Maximum LU specified by bMaxNumberLU |
| bDataReliability | Data Reliability | LU 0, …, Maximum LU specified by bMaxNumberLU |
| bLogicalBlockSize | Logical Block Size | LU 0, …, Maximum LU specified by bMaxNumberLU |
| bProvisioningType | Provisioning Type | LU 0, …, Maximum LU specified by bMaxNumberLU |
| bRPMBRegionEnable | RPMB Region Enable | RPMB W-LU |
| bRPMBRegion0Size | RPMB Region 0 Size | RPMB W-LU |
| bRPMBRegion1Size | RPMB Region 1 Size | RPMB W-LU |
| bRPMBRegion2Size | RPMB Region 2 Size | RPMB W-LU |
| bRPMBRegion3Size | RPMB Region 3 Size | RPMB W-LU |

# JEDEC Standard No. 220G
Page 367

## 13.2.3 Logical Unit Configuration (cont'd)

### Table 13.3—Logical Unit Configurable Parameters (cont'd)

| Configurable parameters | | Logical Unit |
|---|---|---|
| **Name** | **Description** | |
| dLUNumWriteBoosterBufferAllocUnits | WriteBooster Buffer size for the corresponding Logical Unit | Valid only for LU 0, …, LU 7 |

The following Geometry Descriptor parameters provide relevant information for configuring the logical units:

• qTotalRawDeviceCapacity (total raw device density in unit of 512 bytes)

• dSegmentSize

• bAllocationUnitSize (Allocation Unit Size, value expressed in number of segments)

• wSupportedMemoryTypes

• Maximum number of allocation unit for each memory type (dSystemCodeMaxNAllocU, dNonPersistMaxNAllocU, etc.)

• Capacity Adjustment Factor for each memory type (wSystemCodeCapAdjFac, wNonPersistCapAdjFac, etc.)

• bMinAddrBlockSize (this parameter indicates a value equal or greater than 4Kbyte)

• bOptimalReadBlockSize and bOptimalWriteBlockSize

• bMaxInBufferSize

• bMaxOutBufferSize

To enable the access to a logical unit, the user shall configure Unit Descriptor parameters as described in the following:

• bLUEnable  
  bLUEnable shall be set to 01h to enable the logical unit. If bLUEnable is equal to 00h the logical unit is disabled and all Unit Descriptor parameters are don't care.

• bMemoryType  
  bMemoryType shall be set to value corresponding to the desired memory type. The wSupportedMemoryTypes parameter in the Geometry Descriptor indicates which memory types are supported by the device.

• bLogicalBlockSize  
  bLogicalBlockSize value shall adhere to the following rules:
  
  ○ 2^bLogicalBlockSize ≥ bMinAddrBlockSize × 512,
  
  ○ 2^bLogicalBlockSize ≤ bMaxInBufferSize × 512,
  
  ○ 2^bLogicalBlockSize ≤ bMaxOutBufferSize × 512.

# JEDEC Standard No. 220G
Page 368

## 13.2.3 Logical Unit Configuration (cont'd)

To optimize the device performance, it is recommended to configure the logical block size (bLogicalBlockSize) to represent the value indicated by dOptimalLogicalBlockSize for the specific logical unit memory type.

Supported bLogicalBlockSize values are device specific, refer to the vendor datasheet for further information.

• **dNumAllocUnits**  
dNumAllocUnits determines the size of the logical unit. If LUCapacity is the desired logical unit size expressed in bytes, the dNumAllocUnits value shall be calculated using the following equation:  
If (bCapAdjFacRepresentation == 0h) then

```
dNumAllocUnits = CEILING((LUCapacity × CapacityAdjFactor)/(bAllocationUnitSize × dSegmentSize × 512))
```

Else
```
dNumAllocUnits = CEILING((LUCapacity × MSB(CapacityAdjFactor))/(bAllocationUnitSize × dSegmentSize × 512 × LSB(CapacityAdjFactor)))
```

where:
○ CapacityAdjFactor = Capacity Adjustment Factor of the particular memory type  
The Capacity Adjustment Factor value for Normal memory type is one.  
The following example shows dNumAllocUnits calculation for two logical units (LU 1 and LU 4) with the characteristics:  
○ LU 1: 12 Gbyte, Normal memory type  
○ LU 4: 32Mbyte, Enhanced memory type 1  

Assuming that the medium of the UFS device is composed by NAND flash memories which support 2 bit-per-cell and 1 bit-per-cell operation modes. The 2 bit-per-cell operation mode may be associated with the Normal memory type, while the 1 bit-per-cell operation mode may be associated with the Enhanced memory type 1.

The Capacity Adjustment Factor for the Enhanced memory type 1 will be equal to 2.

If:
○ dSegmentSize = 1024
○ bAllocationUnitSize = 8  
Then dNumAllocUnits for LU 1 and LU 4 are:

```
dNumAllocUnits LU 1 = CEILING((12 Gbyte × 1)/(8 × 1024 × 512 byte)) = CEILING(12 Gbyte/4 Mbyte) = 3072

dNumAllocUnits LU 4 = CEILING((32 Mbyte × 2)/(8 × 1024 × 512 byte)) = CEILING(64Mbyte/4 Mbyte) = 16
```

The logical unit capacity can be retrieved by either reading the qLogicalBlockCount parameter in the Unit Descriptor or issuing the READ CAPACITY command.

# JEDEC Standard No. 220G
Page 369

## 13.2.3 Logical Unit Configuration (cont'd)

In particular, the relations between the parameters returned by READ CAPACITY (RETURNED LOGICAL BLOCK ADDRESS and LOGICAL BLOCK LENGTH IN BYTES), and bLogicalBlockSize and qLogicalBlockCount parameters in Unit Descriptors are:
- RETURNED LOGICAL BLOCK ADDRESS = qLogicalBlockCount – 1,
- LOGICAL BLOCK LENGTH IN BYTES = 2^bLogicalBlockSize

• **bBootLunID**  
bBootLunID shall be set as described in the following:  
00h: if the logical unit is not a boot logical unit,  
01h: to configure the logical unit as "Boot LU A",  
02h: to configure the logical unit as "Boot LU B".  
**NOTE** The 01h value and 02h value shall be assigned to no more than one logical unit.

• **bLUWriteProtect**  
bLUWriteProtect shall be set as described in the following:  
00h: if the logical unit is not write protected,  
01h: to configure power on write protection,  
02h: to configure permanent write protection.

• **bDataReliability**  
bDataReliability shall be set to configure the device behavior when a power failure occurs during a write operation to the logical unit:  
00h: logical unit is not protected. Logical unit's entire data may be lost as a result of a power failure during a write operation,  
01h: logical unit is protected. Logical unit's data is protected against power failure.

• **bProvisioningType**  
bProvisioningType shall be set to configure the logical unit provisioning type:  
00h: to disable thin provisioning,  
02h: to enable thin provisioning with TPRZ = 0,  
03h: to enable thin provisioning with TPRZ = 1.

RPMB well known logical unit may be divided in multiple RPMB regions configuring the parameters described in the following.

The total size of the RPMB well known logical unit is indicated by qLogicalBlockCount of RPMB Unit Descriptor. An attempt to configure the device setting the RPMB regions with total size that exceeds the value indicated by qLogicalBlockCount shall fail. An attempt to configure the device setting a RPMB Region with enable bit to one and size to zero shall fail. An attempt to configure the device setting a RPMB Region with enable bit to zero and size greater than zero shall fail.

# JEDEC Standard No. 220G
Page 370

## 13.2.3 Logical Unit Configuration (cont'd)

• **bRPMBRegionEnable**
  RPMB regions may be enabled setting the bits of bRPMBRegionEnable parameter of the RPMB Descriptor. To keep the compatibility to the previous version of the standard, RPMB region 0 is always enabled.
  ○ Bit-0: Don't care. RPMB region 0 is always enabled independent of this bit value.
  ○ Bit-1: Set to 1 to enable RPMB region 1
  ○ Bit-2: Set to 1 to enable RPMB region 2
  ○ Bit-3: Set to 1 to enable RPMB region 3
  ○ Bit-4: Set to 1 to enable Advanced RPMB Mode. ( Set to 0 to enable Normal RPMB Mode.)
  ○ Bit-5: Set to 1 to enable RPMB Purge Operation
  ○ Bit-6 to Bit-7: Reserved

• **bRPMBRegion0Size**
  bRPMBRegion0Size configures the size of RPMB region 0 in 128KB unit (00h: 0KB, 01h: 128KB, …, 80h: 16384KB). The size is not directly configurable, instead it is determined by the following formula.

  In Normal RPMB mode:
  bRPMBRegion0Size = qLogicalBlockCount / 512 - bRPMBRegion1Size (if enabled) – bRPMBRegion2Size (if enabled) – bRPMBRegion3Size (if enabled)

  In Advanced RPMB mode:
  bRPMBRegion0Size = qLogicalBlockCount / 32 - bRPMBRegion1Size (if enabled) – bRPMBRegion2Size (if enabled) – bRPMBRegion3Size (if enabled)
  qLogicalBlockCount's value shall be changed appropriately based on RPMB configuration.

• **bRPMBRegion1Size**
  bRPMBRegion1Size configures the size of RPMB region 1 in 128KB unit (00h: 0KB, 01h: 128KB, …, 80h: 16384KB) if RPMB region 1 is enabled.

• **bRPMBRegion2Size**
  bRPMBRegion2Size configures the size of RPMB region 2 in 128KB unit (00h: 0KB, 01h: 128KB, …, 80h: 16384KB) if RPMB region 2 is enabled.

• **bRPMBRegion3Size**
  bRPMBRegion3Size configures the size of RPMB region 3 in 128KB unit (00h: 0KB, 01h: 128KB, …, 80h: 16384KB) if RPMB region 3 is enabled.

# 13.3 Logical Block Provisioning

## 13.3.1 Overview

Logical Block Provisioning is the concept that describes the relationship between the logical block address space and the physical memory resources that supports the logical address space.

Logical units in a UFS device shall be either a Full Provisioned LU or a Thin Provisioned LU.

## 13.3.2 Full Provisioning

Every LBA in a fully provisioned logical unit is mapped.

A logical unit that is fully provisioned shall provide enough LBA mapping resources to contain all logical blocks for the logical unit's capacity as reported by the device server in response to a READ CAPACITY command.

The device server shall not cause any LBA on a fully provisioned logical unit to become unmapped.

A fully provisioned logical unit does not support logical block provisioning management – i.e., does not support UNMAP command.

## 13.3.3 Thin Provisioning

In thin provisioning there is no requirement that the available physical memory resources match the size of the logical address space.

A thin provisioned logical unit is not required to provide LBA mapping resources sufficient to contain all logical blocks for the logical unit's capacity as reported by the device server in response to a READ CAPACITY command.

In UFS device, a thin provisioned logical unit shall have sufficient physical memory resources for all addressable logical blocks when the logical unit is configured by writing the Configuration Descriptor: the number of LBAs reported in READ CAPACITY shall not exceed the number of physical memory blocks available.

Logical address to physical resource allocation is managed by Logical Block Provisioning Management. Every LBA in a thin provisioned logical unit shall be either mapped or deallocated.

In UFS device, a thin provisioned logical unit shall support the Mapped and Deallocated states in the Logical Block Provisioning State Machine. The anchored state defined in [SBC] is not supported. An unmapped LBA is a deallocated LBA.

UFS device shall support Thin Provisioned logical unit including: Logical Block Provisioning Management, UNMAP command, erased, discard and purge functionalities as described in clause 12, UFS Security.

---

*JEDEC Standard No. 220G*  
*Page 371*