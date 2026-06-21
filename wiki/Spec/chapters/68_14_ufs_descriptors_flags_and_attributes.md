# 14 UFS Descriptors, Flags And Attributes

## 14.1 UFS Descriptors

A descriptor is a data structure with a defined format. Descriptors are accessed via QUERY REQUEST UPIU packets. Descriptors are independently addressable data structures. Descriptors may be stand alone and unique per device or they may be interrelated and linked in a hierarchical fashion to other descriptors by parameters defined within the top-level descriptor. Descriptors can range in size from 2 bytes through 255 bytes. A 2 byte descriptor is an empty descriptor. All descriptors have a length value as their first element. The length represents the entire length of the descriptor, including the length byte. All descriptors have a type identification as their second byte. If a parameter in a Descriptor has a size greater than one byte, the byte containing the MSB is stored at the lowest offset and the byte containing the LSB is stored at the highest offset (i.e., big-endian byte ordering). A descriptor can be partially read, but starting point is always the offset 00h.

A Descriptor is a block or page of parameters that describe something about a Device. For example, there are Device Descriptors, Configuration Descriptors, Unit Descriptors, etc. In general, all Descriptors are readable, some may be write once, others may have a write protection mechanism. The Configuration Descriptor is writable and allows modification of the device configuration set by the manufacturer.

Table 14.1 specifies the descriptor identification values.

## Table 14.1 — Descriptor Identification Values

| Descriptor IDN | Descriptor Type |
|----------------|-----------------|
| 00h | DEVICE |
| 01h | CONFIGURATION |
| 02h | UNIT |
| 03h | Reserved |
| 04h | INTERCONNECT |
| 05h | STRING |
| 06h | Reserved |
| 07h | GEOMETRY |
| 08h | POWER |
| 09h | DEVICE HEALTH |
| 0Ah | Reserved for File Based Optimization (FBO) Extension Specification |
| 0Bh ... EFh | Reserved |
| F0h ... FFh | Reserved for Vendor Specific.<br>Content and function of these Descriptors may vary based on Manufacturer Name String Descriptor and Product Revision Level String Descriptor.<br>For detailed definition of these Descriptors please refer to the device manufacturer datasheet. |

---

JEDEC Standard No. 220G  
Page 422

# JEDEC Standard No. 220G
## Page 423

### 14.1.1 Descriptor Types

Descriptors are classified into types, as indicated in Table 14.1. Some descriptors are singular entities, such as a Device descriptor. Others can have multiple copies, depending upon the quantity defined, such as UNIT descriptors. See Figure 14.1.

### 14.1.2 Descriptor Indexing

Each descriptor type has an index number associated with it. The index value starts at zero and increments by one for each additional descriptor that is instantiated. For example, the first and only Device Descriptor has an index value of 0. The first String Descriptor will have an index value of 0. The Nth String Descriptor will have an index value of N-1.

### 14.1.3 Accessing Descriptors and Device Configuration

Descriptors are accessed by requesting a descriptor IDN and a descriptor INDEX. For example, to request the fifth Unit descriptor, the request would reference TYPE UNIT (numeric value = 2) and INDEX 4 (numeric value = N-1).

[Figure 14.1 shows a hierarchical diagram of Descriptor Organization. At the top is a "DEVICE" descriptor in blue. Below it are several descriptors in the second level: "Geometry" (blue), "Interconnect" (blue), "Power" (blue), "CONFIG #1" (orange), "STRING MANUF" (green), "STRING MODEL" (green), "STRING PROD" (green), "STRING FW LEVEL" (green), and "STRING DATE" (green). Under some of these are third-level descriptors: "String GT" (green) under Geometry, "String IT" (green) under Interconnect, "String PT" (green) under Power, "STRING C1" (green) under CONFIG #1, and "UNIT X" and "UNIT Y" (both blue) under CONFIG #1. Finally, at the bottom level under UNIT X and UNIT Y are "STRING UX" and "STRING UY" (both green) respectively.]

**Figure 14.1 — Descriptor Organization**

All descriptors are read-only, except the Configuration Descriptors and the OEM_ID String Descriptor which are: readable, writeable if bConfigDescrLock attribute value is equal to 00h.

In particular, the Configuration Descriptors allow modification of the device configuration set by the manufacturer. Parameter settings in the Configuration Descriptors are used to calculate and populate the parameter fields in the Device Descriptor and the Unit Descriptors – an internal operation by the device. The host may write the Configuration Descriptors multiple times if bConfigDescrLock attribute is equal to zero.

A device that supports 8 logical units has only one Configuration Descriptor, while a device that supports 32 logical units has four Configuration Descriptors. The host may write only the Configuration Descriptors related to the logical units to be configured, and avoid to send write descriptor query requests for the Configuration Descriptors that do not need to be changed.

# 14.1.4 Accessing Descriptors and Device Configuration

The bConfDescContinue parameter in Configuration Descriptor indicates the end of a sequence of write descriptor query requests during device configuration. In particular, if bConfDescContinue is set to one, the current query request will be followed by another one, and the device shall not start internal operations to implement the new configuration. If bConfDescContinue is set to zero, the current query request is the last one, and the device shall start internal operations to implement the new configuration.

For example, to configure LU 0, LU 1, LU 2, LU 18 and LU 20 the following write descriptor query request may be sent.

1) write descriptor query request with INDEX = 0, bConfDescContinue = 01h, Device Descriptor parameters, logical unit parameters from 0 to 7

2) write descriptor query request with INDEX = 2, bConfDescContinue = 00h, Device Descriptor parameters, logical unit parameters from 16 to 23

The latency of a write descriptor request with bConfDescContinue is set to zero may be significantly longer than a query request with bConfDescContinue set to one. If bConfDescContinue = 00h, then the device shall send a QUERY RESPONSE UPIU only after completing the configuration process.

If bConfDescContinue = 0h, then the Query Response field in the QUERY RESPONSE UPIU shall be set to "Success" only if

• parameters in Device Descriptor and Unit Descriptors have been updated successfully

• logical units configuration has been completed successfully

• logical units are ready for operation (read, write, etc.)

If the query request fails, it shall be possible to repeat the configuration procedure sending a new sequence of write descriptor query requests.

The device may not be able to properly process SCSI commands while updating its configuration, therefore Host should not send them.

The Configuration Descriptor for same index may be sent more than once by host (eg, Configuration Descriptor with Index = 00h) with bConfDescContinue = 01h. The last received values of each Configuration Descriptor index before bConfDescContinue set to zero, shall be considered as valid configuration.

If power cycle happens while bConfDescContinue is 01h, then all the configuration descriptor values shall be reset to pre-successful configuration value or if there is no previous configuration then they shall be reset to MDV values as per UFS Specification.

Once the device has been configured, the setting of bConfigDescrLock to one permanently locks the device configuration. Some devices may be configured multiple times during system setup or system development. The details and restrictions related to multiple device configurations are vendor specific and out of scope for this standard.

NOTE This version of the standard does not require a power cycle to complete the device configuration.

# JEDEC Standard No. 220G
Page 425

## 14.1.4.1 Read Descriptor

A Query Request operation with READ DESCRIPTOR opcode is sent by the host to the device. The host builds a QUERY REQUEST UPIU places a READ DESCRIPTOR opcode within the UPIU, sets the appropriate values in the required fields and sends that UPIU to the target device.

Upon reception of the QUERY REQUEST UPIU the device will decode the READ DESCRIPTOR opcode field and retrieve the descriptor indicated by the DESCRIPTOR IDN field, the INDEX field and the SELECTOR field. When the device is ready to return data to the host the device will construct a QUERY RESPONSE UPIU, set the appropriate fields and place the entire retrieved descriptor within a single Data Segment area of the QUERY RESPONSE UPIU.

Upon transmission of the QUERY RESPONSE UPIU the device will consider the Query Request operation complete.

Upon reception of the QUERY RESPONSE UPIU the host will retrieve the requested descriptor from the Data Segment area, and decode the Status and other fields within the UPIU and take the appropriate completion action. Upon reception of the QUERY RESPONSE UPIU the host will consider that the Query Request operation is complete.

[**Figure 14.2 — Read Request Descriptor**: A flow diagram showing communication between Initiator Device and Target Device over TIME (vertical axis). The diagram shows two UPIU transfers: 1) A blue "QUERY REQUEST UPIU READ DESCRIPTOR" flowing from Initiator to Target, and 2) An orange "QUERY RESPONSE UPIU DESCRIPTOR DATA" flowing from Target back to Initiator.]

# JEDEC Standard No. 220G
Page 426

## 14.1.4.2 Write Descriptor

A Query Request operation with WRITE DESCRIPTOR opcode is sent by the host to the device. The host builds a QUERY REQUEST UPIU places a WRITE DESCRIPTOR opcode within the UPIU, sets the appropriate values in the required fields and sends that UPIU to the target device. A QUERY REQUEST UPIU with a WRITE DESCRIPTOR opcode will additionally include a data segment that contains the descriptor data the host is sending to the device.

Upon reception of the QUERY REQUEST UPIU the device will decode the WRITE DESCRIPTOR opcode field and access the descriptor indicated by the DESCRIPTOR IDN field, the INDEX field and the SELECTOR field. The device will extract the descriptor data within the data segment of the UPIU and will internally overwrite the addressed descriptor with the extracted data. When the device has completed this process it will then notify the host of the success or failure of this operation by returning to the host a QUERY RESPONSE UPIU with the RESPONSE field containing the response code

After the transmission of the QUERY RESPONSE UPIU the device will consider the operation complete. Upon reception of the QUERY RESPONSE UPIU the host will decode the RESPONSE field and other fields within the UPIU and take the appropriate completion action. Upon reception of the QUERY RESPONSE UPIU the host will consider that the operation is complete.

[Diagram showing Write Request Descriptor flow between Initiator Device and Target Device:
- Initiator Device sends QUERY REQUEST UPIU with WRITE DESCRIPTOR and DESCRIPTOR DATA to Target Device
- Target Device responds with QUERY RESPONSE UPIU back to Initiator Device
- A "TIME" arrow shows the temporal flow downward on the left side]

Figure 14.3 — Write Request Descriptor

# JEDEC Standard No. 220G
Page 427

## 14.1.5 Descriptor Definitions

### 14.1.5.1 Generic Descriptor Format

The format of all descriptors begins with a header which contains the length of the descriptor and a type value that identifies the specific type of descriptor. The length value includes the length of the header plus any additional data.

**Table 14.2 — Generic Descriptor Format**

| Offset | Size | DEVICE DESCRIPTOR Name | Description |
|--------|------|------------------------|-------------|
| 0 | 1 | bLength | Size of this descriptor inclusive = N |
| 1 | 1 | bDescriptorIDN | Descriptor Type Identifier |
| 2 ... N-1 | N-2 | DATA | Descriptor Information |

For unit descriptors, the format includes an indication for the unit being addressed.

**Table 14.3 — Logical Unit Descriptor Format**

| Offset | Size | UNIT DESCRIPTOR Name | Description |
|--------|------|---------------------|-------------|
| 0 | 1 | bLength | Size of this descriptor inclusive = N |
| 1 | 1 | bDescriptorIDN | Descriptor Type Identifier |
| 2 | 1 | bUnitIndex | Unit index 00h to the number of LU specified by bMaxNumberLU |
| 3 ... N-1 | N-3 | DATA | Descriptor Information |

### 14.1.5.2 Device Descriptor

This is the main descriptor and should be the first descriptor retrieved as it specifies the device class and sub-class and the protocol (command set) to use to access this device and the maximum number of logical units contained within the device. The Device Descriptor is read only, some of its parameters may be changed writing the corresponding parameter of the Configuration Descriptor.

In a QUERY REQUEST UPIU, the Device Descriptor is addressed setting: DESCRIPTOR IDN = 00h, INDEX = 00h and SELECTOR = 00h.

Table 14.4 is a table of Device Descriptor names and attributes that runs consecutively through the next several pages.

# JEDEC Standard No. 220F
Page 428

## 14.1.5.2 Device Descriptor (cont'd)

### Table 14.4. — Device Descriptor

| Offset | Size | Name | MDV (1) | User Conf. | Description |
|--------|------|------|---------|------------|-------------|
| 00h | 1 | bLength | 59h | No | Size of this descriptor |
| 01h | 1 | bDescriptorIDN | 00h | No | Device Descriptor Type Identifier |
| 02h | 1 | bDevice | 00h | No | Device type<br>00h: Device<br>Others: Reserved |
| 03h | 1 | bDeviceClass | 00h | No | UFS Device Class<br>00h: Mass Storage<br>Others: Reserved |
| 04h | 1 | bDeviceSubClass | Device specific | No | UFS Mass Storage Subclass<br>Bits (0/1) specify as follows:<br>Bit 0: Bootable / Non-Bootable<br>Bit 1: Embedded / Removable<br>Bit 2: Reserved (or JESD220-1 (UME))<br>Others: Reserved<br>Examples:<br>00h: Embedded Bootable<br>01h: Embedded Non-Bootable<br>02h: Removable Bootable<br>03h: Removable Non-Bootable |
| 05h | 1 | bProtocol | 00h | No | Protocol supported by UFS Device<br>00h: SCSI<br>Others: Reserved |
| 06h | 1 | bNumberLU | 00h | Yes(3) | Number of Logical Units<br>bNumberLU does not include well known logical units. |
| 07h | 1 | bNumberWLU | 04h | No | Number of Well known Logical Units |
| 08h | 1 | bBootEnable | 00h | Yes | Boot Enable<br>Indicate whether the device is enabled for boot.<br>00h: Boot feature disabled<br>01h: Bootable feature enabled<br>02h: Permanent-bootable feature enabled<br>Others: Reserved |

**DEVICE DESCRIPTOR**

# JEDEC Standard No. 220F
Page 429

## 14.1.5.2 Device Descriptor (cont'd)

### Table 14.4. — Device Descriptor

| Offset | Size | Name | MDV⁽¹⁾ | User Conf. | Description |
|--------|------|------|---------|------------|-------------|
| 09h | 1 | bDescrAccessEn | 00h | Yes | **Descriptor Access Enable**<br>Indicate whether the Device Descriptor can be read after the partial initialization phase of the boot sequence<br>00h: Device Descriptor access disabled<br>01h: Device Descriptor access enabled<br>Others: Reserved |
| 0Ah | 1 | bInitPowerMode | 01h | Yes | **Initial Power Mode**<br>bInitPowerMode defines the Power Mode after device initialization or hardware reset<br>00h: UFS-Sleep Mode<br>01h: Active Mode<br>Others: Reserved |
| 0Bh | 1 | bHighPriorityLUN | 7Fh | Yes | **High Priority LUN**<br>bHighPriorityLUN defines the high priority logical unit.<br>Valid values are: from 0 to the number of LU specified by bMaxNumberLU, and 7Fh.<br>If this parameter value is 7Fh all logical units have the same priority. |
| 0Ch | 1 | bSecureRemovalType | 00h | Yes | **Secure Removal Type**<br>00h: information removed by an erase of the physical memory<br>01h: information removed by overwriting the addressed locations with a single character followed by an erase.<br>02h: information removed by overwriting the addressed locations with a character, its complement, then a random character.<br>03h: information removed using a vendor define mechanism.<br>Others: Reserved |
| 0Dh | 1 | bSecurityLU | 01h | No | **Support for security LU**<br>00h: not supported<br>01h: RPMB<br>Others: Reserved |

# JEDEC Standard No. 220F
Page 430

## 14.1.5.2 Device Descriptor (cont'd)

### Table 14.4. — Device Descriptor

| Offset | Size | Name | MDV (1) | User Conf. | Description |
|--------|------|------|---------|------------|-------------|
| 0Eh | 1 | bBackgroundOpsTermLat | Device specific | No | Background Operations Termination Latency<br>bBackgroundOpsTermLat defines the maximum latency for the termination of ongoing background operations.<br>When the device receives a COMMAND UPIU with a transfer request, the device shall start the data transfer and send a DATA IN UPIU or a RTT UPIU within the latency declared in bBackgroundOpsTermLat.<br>The latency is expressed in units of 10 ms (e.g., 01h= 10ms, FFh= 2550ms). The latency is undefined if the value of this parameter is zero. |
| 0Fh | 1 | bInitActiveICCLevel | 00h | Yes | Initial Active ICC Level<br>bInitActiveICCLevel defines the bActiveICCLevel value after power on or reset.<br>Valid range from 00h to 0Fh. |
| 10h | 2 | wSpecVersion | 0410h | No | Specification version<br>Bits[15:8] = Major version in BCD format<br>Bits[7:4] = Minor version in BCD format<br>Bits[3:0] = Version suffix in BCD format<br>Example: version 3.21 = 0321h |
| 12h | 2 | wManufactureDate | Device specific | No | Manufacturing Date<br>BCD version of the device manufacturing date, i.e., August 2010 = 0810h |
| 14h | 1 | iManufacturerName | Device specific | No | Manufacturer Name<br>Index to the string which contains the Manufacturer Name. |
| 15h | 1 | iProductName | Device specific | No | Product Name<br>Index to the string which contains the Product Name. |
| 16h | 1 | iSerialNumber | Device specific | No | Serial Number<br>Index to the string which contains the Serial Number. |
| 17h | 1 | iOemID | Device specific | No | OEM ID<br>Index to the string which contains the OEM ID. |

# JEDEC Standard No. 220F
Page 431

## 14.1.5.2 Device Descriptor (cont'd)

### Table 14.4. — Device Descriptor

| Offset | Size | Name | MDV⁽¹⁾ | User Conf. | Description |
|--------|------|------|---------|------------|-------------|
| 18h | 2 | wManufacturerID | Device specific | No | Manufacturer ID<br>Manufacturer ID as defined in JEDEC JEP106, Standard Manufacturer's Identification Code. |
| 1Ah | 1 | bUD0BaseOffset | 16h | No | Unit Descriptor 0 Base Offset<br>Offset of the Unit Descriptor 0 configurable parameters within the Configuration Descriptor. |
| 1Bh | 1 | bUDConfigPLength | 1Ah | No | Unit Descr. Config. Param. Length<br>Total size of the configurable Unit Descriptor parameters. |
| 1Ch | 1 | bDeviceRTTCap | Device specific | No | RTT Capability of device<br>Maximum number of outstanding RTTs supported by device. The minimum value is 2. |
| 1Dh | 2 | wPeriodicRTCUpda​te | 0000h | Yes | Frequency and method of Real-Time Clock update.<br>Bits [15:10] Reserved<br>Bits [9] TIME_BASELINE<br>&nbsp;&nbsp;0b: Time elapsed from the previous<br>&nbsp;&nbsp;dSecondsPassed update.<br>&nbsp;&nbsp;1b: Absolute time elapsed from January<br>&nbsp;&nbsp;1st 2010 00:00.<br>NOTE If the host device has a Real Time Clock it should use TIME BASELINE = '1'. If the host device has no Real Time Clock it should use TIME BASELINE = '0'.<br>Bits [8:6] TIME_UNIT<br>&nbsp;&nbsp;000b = Undefined<br>&nbsp;&nbsp;001b = Months<br>&nbsp;&nbsp;010b = Weeks<br>&nbsp;&nbsp;011b = Days<br>&nbsp;&nbsp;100b = Hours<br>&nbsp;&nbsp;101b = Minutes<br>&nbsp;&nbsp;110b = Reserved<br>&nbsp;&nbsp;111b = Reserved<br>Bits [5:0] TIME_PERIOD<br>If TIME_UNIT is 0 TIME_PERIOD is ignored and the period between RTC update is not defined. All fields are configurable by the host. |

**DEVICE DESCRIPTOR**

# JEDEC Standard No. 220F
Page 432

## 14.1.5.2 Device Descriptor (cont'd)

### Table 14.4. — Device Descriptor

| Offset | Size | Name | MDV⁽¹⁾ | User Conf. | Description |
|--------|------|------|--------|------------|-------------|
| 1Fh | 1 | bUFSFeaturesSupport | Device specific | No | UFS Features Support<br>This field indicates which features are supported by the device. A feature is supported if the related bit is set to one.<br>&nbsp;&nbsp;bit[0]: Field Firmware Update (FFU)<br>&nbsp;&nbsp;bit[1]: Production State Awareness (PSA)<br>&nbsp;&nbsp;bit[2]: Device Life Span<br>&nbsp;&nbsp;bit[3]: Refresh Operation<br>&nbsp;&nbsp;bit[4]: TOO_HIGH_TEMPERATURE<br>&nbsp;&nbsp;bit[5]: TOO_LOW_TEMPERATURE<br>&nbsp;&nbsp;bit[6]: Extended Temperature<br>&nbsp;&nbsp;bit[7]: Reserved for Host Performance Booster(HPB) Extension Standard<br>&nbsp;&nbsp;Others: Reserved<br>Bit 0 shall be set to one. |
| 20h | 1 | bFFUTimeout | Device specific | No | Field Firmware Update Timeout<br>The maximum time, in seconds, that access to the device is limited or not possible through any ports associated due to execution of a WRITE BUFFER command.<br><br>A value of zero indicates that no timeout is provided. |
| 21h | 1 | bQueueDepth | Device specific | No | Queue Depth<br>&nbsp;&nbsp;0: The device implements the per-LU queueing architecture.<br><br>&nbsp;&nbsp;1… 255: The device implements the shared queueing architecture. This parameter indicates the depth of the shared queue.<br><br>If bLUQueueDepth>0 for any LU (except RPMB LU), then bQueueDepth shall be 0. |
| 22h | 2 | wDeviceVersion | Device specific | No | Device Version<br>This field provides the device version. |
| 24h | 1 | bNumSecureWPArea | Device specific | No | Number of Secure Write Protect Areas<br>This value specifies the total number of Secure Write Protect Areas supported by the device. The value shall be equal to or greater than bNumberLU and shall not exceed 32 (bNumberLU ≤ bNumSecureWPArea ≤ 32). |

# JEDEC Standard No. 220F
Page 433

## 14.1.5.2 Device Descriptor (cont'd)

### Table 14.4. — Device Descriptor

| Offset | Size | Name | MDV (1) | User Conf. | Description |
|--------|------|------|---------|------------|-------------|
| 25h | 4 | dPSAMaxDataSize | Device specific | No | PSA Maximum Data Size<br>This parameter specifies the maximum amount of data that may be written during the pre-soldering phase of the PSA flow.<br>The value indicates the total amount of data for all logical units with bPSASensitive = 01h.<br>Value expressed in units of 4 Kbyte. |
| 29h | 1 | bPSAStateTimeout | Device specific | No | PSA State Timeout<br>This parameter specifies the command maximum timeout for a change in bPSAState state.<br>00h means undefined.<br>Otherwise, the formula to calculate the max timeout value is:<br>Production State Timeout = 100us * 2^bPSAStateTimeout<br>For example:<br>01h means 100us x 2^1 = 200us<br>02h means 100us x 2^2 = 400us<br>17h means 100us x 2^23 = 838.86s |
| 2Ah | 1 | iProductRevisionLevel | Device specific | No | Product Revision Level<br>Index to the string which contains the Product Revision Level |
| 2Bh | 5 | Reserved | - | - | Reserved |
| 30h | 16 | Reserved | - | - | Reserved for Unified Memory Extension standard |
| 40h | 3 | Reserved | - | - | Reserved for Host Performance Booster (HPB) Extension Standard |
| 43h | 10 | Reserved | - | - | Reserved |

# JEDEC Standard No. 220F
Page 434

## 14.1.5.2 Device Descriptor (cont'd)

### Table 14.4. — Device Descriptor

| Offset | Size | Name | MDV (1) | User Conf. | Description |
|--------|------|------|---------|------------|-------------|
| 4Dh | 2 | wExtendedWriteBoosterSupport | Device specific | No | Extended WriteBooster Support<br>This field indicates which extended WriteBooster features are supported by the device.<br><br>This field is valid only when WriteBooster is enabled, i.e. bit [8] for WriteBooster Enable in the ExtendedUFSFeaturesSupport is one. A feature is supported if the related bit is set to one.<br><br>bit[0]: WriteBooster Buffer Resize<br>bit[1]: FIFO Partial Flush Mode<br>bit[2]: Pinned Partial Flush Mode<br>Others: Reserved |

**DEVICE DESCRIPTOR**

# JEDEC Standard No. 220F
Page 435

## 14.1.5.2 Device Descriptor (cont'd)

### Table 14.4. — Device Descriptor

| Offset | Size | Name | MDV⁽¹⁾ | User Conf. | Description |
|--------|------|------|---------|------------|-------------|
| 4Fh | 4 | dExtendedUFSFeaturesSupport | Device specific | No | Extended UFS Features Support<br/>This field indicates which features are supported by the device. This field value will be exactly same value and same functionality as defined in the bit[0~7] of bUFSFeaturesSupport device descriptor. Since bUFSFeaturesSupport will be obsoleted, it is recommended to refer this descriptor to find out device feature support. A feature is supported if the related bit is set to one.<br/><br/>bit[0]: Field Firmware Update (FFU)<br/>bit[1]: Production State Awareness (PSA)<br/>bit[2]: Device Life Span<br/>bit[3]: Refresh Operation<br/>bit[4]: TOO_HIGH_TEMPERATURE<br/>bit[5]: TOO_LOW_TEMPERATURE<br/>bit[6]: Extended Temperature<br/>bit[7]: Reserved for Host-aware Performance Booster (HPB) Extension Specification<br/>bit[8]: WriteBooster<br/>bit[9]: Performance Throttling<br/>bit[10]: Advanced RPMB<br/>bit[11]: Reserved for Zoned UFS Extension Specification<br/>bit[12]: Device Level Exception Warning<br/>bit[13]: HID (Host Initiated Defragmentation)<br/>bit[14]: Barrier<br/>bit[15]: Clear Error History functionality<br/>bit[16]: EXT_IID<br/>bit[17]: Reserved for File Based Optimization (FBO) Extension Specification<br/>bit[18]: Fast Recovery Mode<br/>bit[19]: RPMB Authenticated Vendor Command<br/>bit[20-31]: Reserved |

# JEDEC Standard No. 220F
Page 436

## 14.1.5.2 Device Descriptor (cont'd)

### Table 14.4. — Device Descriptor

| Offset | Size | Name | MDV (1) | User Conf. | Description |
|--------|------|------|---------|------------|-------------|
| 53h | 1 | bWriteBoosterBufferPreserveUserSpaceEn | 0 | Yes | Preserve User Space mode<br/>00h: User space is reduced if WriteBooster Buffer is configured. The WriteBooster Buffer reduces the user space that can be configured at provisioning.<br/>01h: User space shall not be reduced if WriteBooster Buffer is configured. If the user space is almost consumed the WriteBooster Buffer space may be used as the user space. During the migration of the WriteBooster Buffer space to the user space, there could be performance degradation.<br/><br/>Others: Reserved |
| 54h | 1 | bWriteBoosterBufferType | 0 | Yes | WriteBooster Buffer Type<br/>00h: LU dedicated buffer type<br/>01h: Single shared buffer type |
| 55h | 4 | dNumSharedWriteBoosterBufferAllocUnits | 0 | Yes | The WriteBooster Buffer size for the shared WriteBooster Buffer configuration.<br/>The dNumSharedWriteBoosterBufferAllocUnits value shall be calculated using the following equation:<br/>dNumSharedWriteBoosterBufferAllocUnits = CEILING((WriteBoosterBufferCapacity × 1)/(bAllocationUnitSize × dSegmentSize × 512))<br/>where WriteBoosterBufferCapacity is the desired WriteBooster Buffer size expressed in bytes. For example, to configure 4 GB WriteBooster Buffer if bAllocationUnitSize = 8, and dSegmentSize = 1024, then the value for the dNumSharedWriteBoosterBufferAllocUnits is 400h.<br/>If this value is zero, then the shared WriteBooster is not configured for this device. |

# 14.1.5.2 Device Descriptor (cont'd)

## Table 14.4. — Device Descriptor

### DEVICE DESCRIPTOR

| Offset | Size | Name | MDV (1) | User Conf. | Description |
|--------|------|------|---------|------------|-------------|

**NOTE 1** The column "MDV" (Manufacturer Default Value) specifies parameter values after device manufacturing. Some parameters may be configured by the user writing the Configuration Descriptor.

**NOTE 2** "User Conf." column specifies which fields can be configured by the user writing the Configuration Descriptor: "Yes" means that the field can be configured, "No" means that the field is a capability of the device and cannot be changed by the user. The desired value shall be set in the equivalent parameter of the Configuration Descriptor.

**NOTE 3** The NumberLU field value is calculated by the device based on bLUEnable field value in the Unit Descriptors.

## a) wManufacturerID

This parameter contains manufacturer identification information for the device manufacturer. The Manufacturer ID is defined by JEDEC in Standard Manufacturer's identification code [JEP106]. The wManufacturerID consists of two fields: Manufacturer ID Code and Bank Index.

### Table 14.5 — wManufacturerID Definition

| Bit | | | | | | | | |
|-----|---|---|---|---|---|---|---|---|
| Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
| 0 | | | | Bank Index | | | | |
| 1 | | | Manufacturer ID Code | | | | | |

## b) Bank Index

This field contains an index value of the bank that contains the manufacturer identification code. The Bank Index value shall be equal to the number of the continuation fields that precede the manufacturer identification code as specified by [JEP106].

## c) Manufacturer ID Code

Manufacturer identification code as defined by JEDEC in Standard Manufacturer's identification code [JEP106].

---

*JEDEC Standard No. 220F*  
*Page 437*

# 14.1.5.3 Configuration Descriptor

The device configuration set by the manufacturer can be modified by writing the Configuration Descriptor. In particular, the Configuration Descriptor allows to configure parameters included in the Device Descriptor, RPMB Unit Descriptor, and Unit Descriptors. The Configuration Descriptor can be written if bConfigDescrLock attribute value is equal to 00h. If bConfigDescrLock attribute value is 01h the Configuration Descriptor is locked and a write request shall fail.

There are up to four Configuration Descriptors.

The first Configuration Descriptor is addressed by setting DESCRIPTOR IDN = 01h, INDEX = 00h and SELECTOR = 00h in a QUERY REQUEST UPIU, and used to change configurable parameters of Device Descriptor, RPMB Unit Descriptor, and the first eight Unit Descriptors (LU 0 to LU 7).

The second Configuration Descriptor is addressed by setting DESCRIPTOR IDN = 01h, INDEX = 01h and SELECTOR = 00h in a QUERY REQUEST UPIU, and used to change configurable parameters of the next eight Unit Descriptors (LU 8 to LU 15).

The third Configuration Descriptor is addressed by setting DESCRIPTOR IDN = 01h, INDEX = 02h and SELECTOR = 00h in a QUERY REQUEST UPIU, and used to change configurable parameters of the next eight Unit Descriptors (LU 16 to LU 23).

The fourth Configuration Descriptor is addressed by setting DESCRIPTOR IDN = 01h, INDEX = 03h and SELECTOR = 00h in a QUERY REQUEST UPIU, and used to change configurable parameters of the last eight Unit Descriptors (LU 24 to LU 31).

Table 14.6 shows the Configuration Descriptor format with DESCRIPTOR IDN = 01h, INDEX = 00h and SELECTOR = 00h: the lower address space is used for Configuration Descriptor header, Device Descriptor configurable parameters, and RPMB Unit Descriptor configurable parameters. Then there are eight address spaces for user configurable parameters included in the Unit Descriptors of LU 0 to LU 7.

**Table 14.6 — Configuration Descriptor Format (INDEX = 00h)**

| Offset | Description |
|--------|-------------|
| 00h … (B-1)h | Configuration Descriptor header, Device Descriptor configurable parameters, and RPMB Unit Descriptor configurable parameters |
| (B)h … (B+L-1)h | Unit Descriptor 0 configurable parameters |
| (B+L)h … (B+2*L-1)h | Unit Descriptor 1 configurable parameters |
| … | … |
| (B+7*L)h … (B+8*L-1)h | Unit Descriptor 7 configurable parameters |

Table 14.7 shows the Configuration Descriptor format with DESCRIPTOR IDN = 01h, INDEX = 01h and SELECTOR = 00h: the lower address space is used for Configuration Descriptor header, then there are eight address spaces for user configurable parameters included in the Unit Descriptors of LU 8 to LU 15.

---
JEDEC Standard No. 220F  
Page 438

# JEDEC Standard No. 220F
Page 439

## 14.1.5.3 Configuration Descriptor (cont'd)

### Table 14.7 — Configuration Descriptor Format (INDEX = 01h)

| Offset | Description |
|--------|-------------|
| 00h … (B-1)h | Configuration Descriptor header |
| (B)h … (B+L-1)h | Unit Descriptor 8 configurable parameters |
| (B+L)h … (B+2*L-1)h | Unit Descriptor 9 configurable parameters |
| … | … |
| (B+7*L)h … (B+8*L-1)h | Unit Descriptor 15 configurable parameters |

Table 14.8 shows the Configuration Descriptor format with DESCRIPTOR IDN = 01h, INDEX = 02h and SELECTOR = 00h: the lower address space is used for Configuration Descriptor header, then there are eight address spaces for user configurable parameters included in the Unit Descriptors of LU 16 to LU 23.

### Table 14.8 — Configuration Descriptor Format (INDEX = 02h)

| Offset | Description |
|--------|-------------|
| 00h … (B-1)h | Configuration Descriptor header |
| (B)h … (B+L-1)h | Unit Descriptor 16 configurable parameters |
| (B+L)h … (B+2*L-1)h | Unit Descriptor 17 configurable parameters |
| … | … |
| (B+7*L)h … (B+8*L-1)h | Unit Descriptor 23 configurable parameters |

Table 14.9 shows the Configuration Descriptor format with DESCRIPTOR IDN = 01h, INDEX = 03h and SELECTOR = 00h: the lower address space is used for Configuration Descriptor header, then there are eight address spaces for user configurable parameters included in the Unit Descriptors of LU 24 to LU 32. Parameter offsets are defined based on:

• Offset of the Unit Descriptor 0 configurable parameters within the Configuration Descriptor (B).

• Length of Unit Descriptor configurable parameters (L).

Values for B and L are stored in the Device Descriptor parameters bUD0BaseOffset and bUDConfigPLength, respectively.

### Table 14.9 — Configuration Descriptor Format (INDEX = 03h)

| Offset | Description |
|--------|-------------|
| 00h … (B-1)h | Configuration Descriptor header |
| (B)h … (B+L-1)h | Unit Descriptor 24 configurable parameters |
| (B+L)h … (B+2*L-1)h | Unit Descriptor 25 configurable parameters |
| … | … |
| (B+7*L)h … (B+8*L-1)h | Unit Descriptor 31 configurable parameters |

**NOTE 1** B is offset of the Unit Descriptor 0/8/16/24 configurable parameters within the Configuration Descriptor. L is the total size of the configurable Unit Descriptor parameters.

# JEDEC Standard No. 220F
Page 440

## 14.1.5.3 Configuration Descriptor (cont'd)

Table 14.10 defines Configuration Descriptor header, Device Descriptor configurable parameters, and RPMB Unit Descriptor configurable parameters within the Configuration Descriptor with INDEX = 00h.

defines Configuration Descriptor header, Device Descriptor configurable parameters, and RPMB Unit Descriptor configurable parameters within the Configuration Descriptor with INDEX = 00h.

See 14.1.5.2 for details about configurable parameters.

# JEDEC Standard No. 220F
Page 441

## 14.1.5.3 Configuration Descriptor (cont'd)

### Table 14.10 — Configuration Descr. Header and Device Descr. Conf. Parameters (INDEX = 00h)

| Offset | Size | Name | Configuration Descriptor Header and Device Descriptor configurable parameters |  |
|--------|------|------|-------------|-------------|
|        |      |      | **MDV** | **Description** |
| 00h | 1 | bLength | E5h | Size of this descriptor |
| 01h | 1 | bDescriptorIDN | 01h | Configuration Descriptor Type Identifier<br>00h: This value indicates that this is the last Configuration Descriptor in a sequence of write descriptor query requests. Device shall perform internal configuration based on received Configuration Descriptor(s). |
| 02h | 1 | bConfDescContinue | 00h | 01h: This value indicates that this is not the last Configuration Descriptor in a sequence of write descriptor query requests. Other Configuration Descriptors will be sent by host. Therefore the device should not perform the internal configuration yet.<br>Others: Reserved. |
| 03h | 1 | bBootEnable |  | Boot Enable<br>Enables to boot feature. |
| 04h | 1 | bDescrAccessEn |  | Descriptor Access Enable<br>Enables access to the Device Descriptor after the partial initialization phase of the boot sequence. |
| 05h | 1 | bInitPowerMode |  | Initial Power Mode<br>Configures the power mode after device initialization or hardware reset. |
| 06h | 1 | bHighPriorityLUN |  | High Priority LUN<br>Configures the high priority logical unit. |
| 07h | 1 | bSecureRemovalType |  | Secure Removal Type<br>Configures the secure removal type. |
| 08h | 1 | bInitActivelCCLevel |  | Initial Active ICC Level<br>Configures the ICC level in Active mode after device initialization or hardware reset |
| 09h | 2 | wPeriodicRTCUpdate |  | Frequency and method of Real-Time Clock update (see Device Descriptor). |
| 0Bh | 1 | Reserved | - | Reserved for Host Performance Booster (HPB) Extension Standard |
| 0Ch | 1 | bRPMBRegionEnable |  | RPMB Region Enable<br>Configures which RPMB regions are enabled in RPMB well known logical unit. |
| 0Dh | 1 | bRPMBRegion1Size |  | RPMB Region 1 Size<br>Configures the size of RPMB region 1 if RPMB region 1 is enabled. |
| 0Eh | 1 | bRPMBRegion2Size |  | RPMB Region 2 Size<br>Configures the size of RPMB region 2 if RPMB region 2 is enabled. |
| 0Fh | 1 | bRPMBRegion3Size |  | RPMB Region 3 Size<br>Configures the size of RPMB region 3 if RPMB region 3 is enabled. |
| 10h | 1 | bWriteBoosterBufferPrese rveUserSpaceEn | 00h | Enable preserve user space when WriteBooster Buffer is configured. |
| 11h | 1 | bWriteBoosterBufferType | 00h | Configure the WriteBooster Buffer type |
| 12h | 4 | dNumSharedWriteBooster BufferAllocUnits | 00h | Configure the WriteBooster Buffer size for a shared WriteBooster Buffer configuration. |

**NOTE 1** The column "MDV" (Manufacturer Default Value) specifies parameter values after device manufacturing.  
**NOTE 2** See Table 14.4, Device Descriptor, for the default parameters value set by the device manufacturer.

# JEDEC Standard No. 220F
## Page 442

### 14.1.5.3 Configuration Descriptor (cont'd)

Table 14.4 defines Configuration Descriptor header within the Configuration Descriptor with INDEX = 01h, 02h, or 03h.

#### Table 14.4— Configuration Descr. Header with INDEX = 01h/02h/03h

**Configuration Descriptor Header**

| Offset | Size | Name | MDV⁽¹⁾ | Description |
|--------|------|------|--------|-------------|
| 00h | 1 | bLength | E6h | Size of this descriptor |
| 01h | 1 | bDescriptorIDN | 01h | Configuration Descriptor Type Identifier |
| 02h | 1 | bConfDescContinue | 00h | 00h: This value indicates that this is the last Configuration Descriptor in a sequence of write descriptor query requests. Device shall perform internal configuration based on received Configuration Descriptor(s).<br>01h: This value indicates that this is not the last Configuration Descriptor in a sequence of write descriptor query requests. Other Configuration Descriptors will be sent by host. Therefore the device should not perform the internal configuration yet.<br>Others: Reserved. |
| 03h | 19 | Reserved | | |

**NOTE 1** The column "MDV" (Manufacturer Default Value) specifies parameter values after device manufacturing.

# JEDEC Standard No. 220F
Page 443

## 14.1.5.3 Configuration Descriptor (cont'd)

Table 14.5 defines the Unit Descriptors user configurable parameters within the Configuration Descriptor. See 14.1.5.5.

### Table 14.5 — Unit Descriptor Configurable Parameters

| Offset | Size | Name | Description |
|--------|------|------|-------------|
| 00h | 1 | bLUEnable | Logical Unit Enable |
| 01h | 1 | bBootLunID | Boot LUN ID |
| 02h | 1 | bLUWriteProtect | Logical Unit Write Protect |
| 03h | 1 | bMemoryType | Memory Type |
| 04h | 4 | dNumAllocUnits | Number of Allocation Units<br>Number of allocation units assigned to the logical unit.<br>The value shall be calculated considering the capacity<br>adjustment factor of the selected memory type |
| 08h | 1 | bDataReliability | Data Reliability |
| 09h | 1 | bLogicalBlockSize | Logical Block Size |
| 0Ah | 1 | bProvisioningType | Provisioning Type |
| 0Bh | 2 | wContextCapabilities | Context Capabilities |
| 0Dh | 3 | Reserved | |
| 10h | 6 | Reserved | See Host Performance Booster (HPB) Extension Standard |
| 16h | 4 | dLUNumWriteBooster<br>BufferAllocUnits | The WriteBooster Buffer size for the Logical Unit. The value is<br>expressed in the unit of Allocation Units. If this value is '0',<br>then the WriteBooster is not supported for this LU.<br>The Logical unit among LU0 ~ LU7 can be configured for<br>WriteBooster Buffer. |

## 14.1.5.4 Geometry Descriptor

The Geometry Descriptor describes the device geometric parameters. In a QUERY REQUEST UPIU, the Geometry Descriptor is addressed setting: DESCRIPTOR IDN = 07h, INDEX = 00h and SELECTOR = 00h.

Table 14.13 is a table of Geometry Descriptor names and attributes that runs consecutively through the next several pages.

# JEDEC Standard No. 220F
Page 444

## 14.1.5.4 Geometry Descriptor (cont'd)

### Table 14.13 — Geometry Descriptor

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 00h | 1 | bLength | 69h | Size of this descriptor |
| 01h | 1 | bDescriptorIDN | 07h | Geometry Descriptor Type Identifier |
| 02h | 1 | bMediaTechnology | 00h | Reserved |
| 03h | 1 | Reserved | 00h | Reserved |
| 04h | 8 | qTotalRawDeviceCapacity | Device specific | Total Raw Device Capacity<br>Total memory quantity available to the user to configure the device logical units (RPMB excluded). It is expressed in unit of 512 bytes |
| 0Ch | 1 | bMaxNumberLU | Device specific | Maximum number of Logical Unit supported by the UFS device<br>00h: 8 Logical units<br>01h: 32 Logical units<br>Others: Reserved |
| 0Dh | 4 | dSegmentSize | Device specific | Segment Size<br>Value expressed in unit of 512 bytes |
| 11h | 1 | bAllocationUnitSize | Device specific | Allocation Unit Size<br>Value expressed in number of Segments<br>Each logical unit can be allocated as a multiple of Allocation Units. |
| 12h | 1 | bMinAddrBlockSize | Device specific | Minimum addressable block size<br>Value expressed in unit of 512 bytes.<br>Its minimum value is 08h, which corresponds to 4 Kbyte. |
| 13h | 1 | bOptimalReadBlockSize | Device specific | Optimal Read Block Size<br>Value expressed in unit of 512 bytes.<br>This is an optional parameter.<br>A value of zero indicates that this information is not available. If not zero, bOptimalReadBlockSize shall be equal to or greater than bMinAddrBlockSize. |
| 14h | 1 | bOptimalWriteBlockSize | Device specific | Optimal Write Block Size<br>Value expressed in unit of 512 bytes.<br>bOptimalWriteBlockSize shall be equal to or greater than bMinAddrBlockSize. |
| 15h | 1 | bMaxInBufferSize | Device specific | Max. data-in buffer size<br>Value expressed in unit of 512 bytes.<br>Its minimum value is 08h, which corresponds to 4 Kbyte |

**GEOMETRY DESCRIPTOR**

# 14.1.5.4 Geometry Descriptor (cont'd)

## Table 14.13 — Geometry Descriptor

### GEOMETRY DESCRIPTOR

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 16h | 1 | bMaxOutBufferSize | Device specific | Max. data-out buffer size<br>Value expressed in unit of 512 bytes.<br>Its minimum value is 08h, which corresponds to 4 Kbyte |
| 17h | 1 | bRPMB_ReadWriteSize | Device specific | Maximum number of RPMB frames (256-byte of data in Normal RPMB mode, 4KB of data in Advanced RPMB mode) allowed in Security Protocol In and Security Protocol Out (i.e., associated with a single command UPIU)<br><br>In Normal RPMB mode, if the data to be transferred is larger than bRPMB_ReadWriteSize x 256 bytes, the host will transfer it using multiple Security Protocol In/Out commands<br><br>In Advanced RPMB mode, If the data to be transferred is larger than bRPMB_ReadWriteSize x 4K bytes, the host will transfer it using multiple Security Protocol In/Out commands.<br><br>This value shall be changed to the appropriate value based on RPMB configuration. |
| 18h | 1 | bDynamicCapacityResourcePolicy | Device specific | Dynamic Capacity Resource Policy<br>This parameter specifies the device spare blocks resource management policy:<br><br>00h: Spare blocks resource management policy is per logical unit. The host should release amount of logical blocks from each logical unit as asked by the device.<br><br>01h: Spare blocks resource management policy is per memory type. The host may deallocate the required amount of logical blocks from any logical units with the same bMemoryType. |

---

JEDEC Standard No. 220F  
Page 445

# JEDEC Standard No. 220F
Page 446

## 14.1.5.4 Geometry Descriptor (cont'd)

### Table 14.13 — Geometry Descriptor

**GEOMETRY DESCRIPTOR**

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 19h | 1 | bDataOrdering | Device specific | Support for out-of-order data transfer<br/>00h: out-of-order data transfer is not supported by the device, in-order data transfer is required for both DATA IN and DATA OUT UPIUs<br/>01h: out-of-order data transfer is supported by the device for both DATA IN and DATA OUT UPIUs<br/>02h: out-of-order data transfer is supported by the device for DATA IN UPIUs only, and DATA OUT UPIUs must be transferred in-order<br/>03h: out-of-order data transfer is supported by the device for DATA OUT UPIUs only, and DATA IN UPIUs must be transferred in-order<br/>All others: Reserved |
| 1Ah | 1 | bMaxContextIDNumber | Device specific | Max. available number of contexts which are supported by the device. Minimum number of supported contexts shall be 5. |
| 1Bh | 1 | bSysDataTagUnitSize | Device specific | bSysDataTagUnitSize provides system data tag unit size, which can be calculated as in the following (in bytes)<br/>Tag Unit Size = 2^bSysDataTagUnitSize x bMinAddrBlockSize x 512 |
| 1Ch | 1 | bSysDataTagResSize | Device specific | This field is defined to inform the host about the maximum storage area size in bytes allocated by the device to handle system data by the tagging mechanism:<br/>System Data Tag Resource Size =<br/>Tag Unit Size<br/>× floor((qTotalRawDeviceCapacity × 2^bSysDataTagResSize-10)/Tag Unit Size)<br/><br/>The range of valid bSysDataTagResSize values is from 0 to 6. Values in range of 07h to FFh are reserved.<br/>The formula covers a range from about 0.1% to 6.25% of the device capacity |

# JEDEC Standard No. 220F
Page 447

## 14.1.5.4 Geometry Descriptor (cont'd)

### Table 14.13 — Geometry Descriptor

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 1Dh | 1 | bSupportedSecRTypes | Device specific | **Supported Secure Removal Types**<br>Bit map which represents the supported Secure Removal types.<br>• bit 0: information removed by an erase of the physical memory<br>• bit 1: information removed by overwriting the addressed locations with a single character followed by an erase.<br>• bit 2: information removed by overwriting the addressed locations with a character, its complement, then a random character.<br>• bit 3: information removed using a vendor define mechanism.<br>Others: Reserved<br>A value of one means that the corresponding Secure Removal type is supported. |
| 1Eh | 2 | wSupportedMemoryTypes | Device specific | **Supported Memory Types**<br>Bit map which represents the supported memory types.<br>• bit 0: Normal memory type<br>• bit 1: System code memory type<br>• bit 2: Non-Persistent memory type<br>• bit 3: Enhanced memory type 1<br>• bit 4: Enhanced memory type 2<br>• bit 5: Enhanced memory type 3<br>• bit 6: Enhanced memory type 4<br>• bit 7: Reserved<br>…<br>• bit 14: Reserved<br>• bit 15: RPMB memory type<br>A value one means that the corresponding memory type is supported. Bit 0 and bit 15 shall be one for all UFS device. |
| 20h | 4 | dSystemCodeMaxNAllocU | Device specific | **Max Number of Allocation Units for the System Code memory type**<br>Maximum available quantity of System Code memory type for the entire device.<br>Value expressed in number of Allocation Unit |

# 14.1.5.4 Geometry Descriptor (cont'd)

## Table 14.13 — Geometry Descriptor

### GEOMETRY DESCRIPTOR

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 24h | 2 | wSystemCodeCapAdjFac | Device specific | Capacity Adjustment Factor for the System Code memory type<br><br>This parameter is the ratio between the capacity obtained with the Normal memory type and the capacity obtained with the System Code memory type for the same amount of allocation units.<br><br>CapacityAdjFactor =<br>CapacityNormalMem / CapacitySystemCode<br><br>If bCapAdjFacRepresentation == 0h<br>wSystemCodeCapAdjFac =<br>INTEGER(256 × CapacityAdjFactor)<br>Else<br>wSystemCodeCapAdjFac [15:8] =<br>numerator(CapacityAdjFactor)<br>wSystemCodeCapAdjFac [7:0] =<br>denominator(CapacityAdjFactor) |
| 26h | 4 | dNonPersistMaxNAllocU | Device specific | Max Number of Allocation Units for the Non-Persistent memory type<br><br>Maximum available quantity of Non-Persistent memory type for the entire device.<br>Value expressed in number of Allocation Unit |
| 2Ah | 2 | wNonPersistCapAdjFac | Device specific | Capacity Adjustment Factor for the Non-Persistent memory type<br><br>This parameter is the ratio between the capacity obtained with the Normal memory type and the capacity obtained with the Non-Persistent memory type for the same amount of allocation units.<br><br>CapacityAdjFactor =<br>CapacityNormalMem / CapacityNonPersist<br><br>If bCapAdjFacRepresentation == 0h<br>wNonPersistCapAdjFac =<br>INTEGER(256 × CapacityAdjFactor)<br>Else<br>wNonPersistCapAdjFac [15:8] =<br>numerator(CapacityAdjFactor)<br>wNonPersistCapAdjFac [7:0] =<br>denominator(CapacityAdjFactor) |

---
*JEDEC Standard No. 220F*  
*Page 448*

# 14.1.5.4 Geometry Descriptor (cont'd)

## Table 14.13 — Geometry Descriptor

### GEOMETRY DESCRIPTOR

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 2Ch | 4 | dEnhanced1MaxNAllocU | Device specific | Max Number of Allocation Units for the Enhanced memory type 1<br>Maximum available quantity of Enhanced memory type 1 for the entire device<br>Value expressed in number of Allocation Unit |
| 30h | 2 | wEnhanced1CapAdjFac | Device specific | Capacity Adjustment Factor for the Enhanced memory type 1<br>This parameter is the ratio between the capacity obtained with the Normal memory type and the capacity obtained with the Enhanced memory type 1 for the same amount of allocation units.<br>CapacityAdjFactor =<br>CapacityNormalMem / CapacityEnhanced1<br>If bCapAdjFacRepresentation == 0h<br>wEnhanced1CapAdjFac =<br>INTEGER(256 × CapacityAdjFactor)<br>Else<br>wEnhanced1CapAdjFac [15:8] =<br>numerator(CapacityAdjFactor)<br>wEnhanced1CapAdjFac [7:0] =<br>denominator(CapacityAdjFactor) |
| 32h | 4 | dEnhanced2MaxNAllocU | Device specific | Max Number of Allocation Units for the Enhanced memory type 2<br>Maximum available quantity of Enhanced memory type 2 for the entire device<br>Value expressed in number of Allocation Unit |

---

*JEDEC Standard No. 220F*  
*Page 449*

# JEDEC Standard No. 220F
Page 450

## 14.1.5.4 Geometry Descriptor (cont'd)

### Table 14.13 — Geometry Descriptor

| Offset | Size | Name | Value | Description |
|--------|------|------|--------|-------------|
| 36h | 2 | wEnhanced2CapAdjFac | Device specific | Capacity Adjustment Factor for the Enhanced memory type 2<br><br>This parameter is the ratio between the capacity obtained with the Normal memory type and the capacity obtained with the Enhanced memory type 2 for the same amount of allocation units.<br>CapacityAdjFactor =<br>CapacityNormalMem / CapacityEnhanced2<br><br>If bCapAdjFacRepresentation == 0h<br>wEnhanced2CapAdjFac =<br>INTEGER(256 × CapacityAdjFactor)<br>Else<br>wEnhanced2CapAdjFac [15:8] =<br>numerator(CapacityAdjFactor)<br>wEnhanced2CapAdjFac [7:0] =<br>denominator(CapacityAdjFactor) |
| 38h | 4 | dEnhanced3MaxNAllocU | Device specific | Max Number of Allocation Units for the Enhanced memory type 3<br><br>Maximum available quantity of Enhanced memory type 3 for the entire device<br>Value expressed in number of Allocation Unit |
| 3Ch | 2 | wEnhanced3CapAdjFac | Device specific | Capacity Adjustment Factor for the Enhanced memory type 3<br><br>This parameter is the ratio between the capacity obtained with the Normal memory type and the capacity obtained with the Enhanced memory type 3 for the same amount of allocation units.<br>CapacityAdjFactor =<br>CapacityNormalMem / CapacityEnhanced3<br><br>If bCapAdjFacRepresentation == 0h<br>wEnhanced3CapAdjFac =<br>INTEGER(256 × CapacityAdjFactor)<br>Else<br>wEnhanced3CapAdjFac [15:8] =<br>numerator(CapacityAdjFactor)<br>wEnhanced3CapAdjFac [7:0] =<br>denominator(CapacityAdjFactor) |

# 14.1.5.4 Geometry Descriptor (cont'd)

## Table 14.13 — Geometry Descriptor

### GEOMETRY DESCRIPTOR

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 3Eh | 4 | dEnhanced4MaxNAllocU | Device specific | Max Number of Allocation Units for the Enhanced memory type 4<br/>Maximum available quantity of Enhanced memory type 4 for the entire device<br/>Value expressed in number of Allocation Unit |
| 42h | 2 | wEnhanced4CapAdjFac | Device specific | Capacity Adjustment Factor for the Enhanced memory type 4<br/>This parameter is the ratio between the capacity obtained with the Normal memory type and the capacity obtained with the Enhanced memory type 4 for the same amount of allocation units.<br/>CapacityAdjFactor =<br/>CapacityNormalMem / CapacityEnhanced4<br/>If bCapAdjFacRepresentation == 0h<br/>wEnhanced4CapAdjFac =<br/>INTEGER(256 × CapacityAdjFactor)<br/>Else<br/>wEnhanced4CapAdjFac [15:8] =<br/>numerator(CapacityAdjFactor)<br/>wEnhanced4CapAdjFac [7:0] =<br/>denominator(CapacityAdjFactor) |
| 44h | 4 | dOptimalLogicalBlockSize | Device specific | Optimal Logical Block Size<br/>bit [3:0]: Normal memory type<br/>bit [7:4]: System code memory type<br/>bit [11: 8]: Non-Persistent memory type<br/>bit [15:12]: Enhanced memory type 1<br/>bit [19:16]: Enhanced memory type 2<br/>bit [23:20]: Enhanced memory type 3<br/>bit [27:24]: Enhanced memory type 4<br/>bit [31:28]:Reserved<br/>The optimal logical block size for each memory type can be calculated from the related dOptimalLogicalBlockSize field as indicated in the following:<br/>Optimal Logical Block Size = 2^(dOptimalLogicalBlockSize field) x bMinAddrBlockSize x 512 byte |
| 48h | 5 | Reserved | - | Reserved for Host Performance Booster (HPB) Extension Standard |

---

JEDEC Standard No. 220F  
Page 451

# 14.1.5.4 Geometry Descriptor (cont'd)

## Table 14.13 — Geometry Descriptor

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 4Dh | 2 | Reserved | - | Reserved |
| 4Fh | 4 | dWriteBoosterBufferMaxN AllocUnits | Device specific | Maximum total WriteBooster Buffer size which is supported by the entire device. The summation of the WriteBooster Buffer size for all LUs should be equal to or less than size value indicated by this descriptor. |
| 53h | 1 | bDeviceMaxWriteBoosterL Us | Device specific | Number of maximum WriteBooster Buffer supported by the device. In this version of the standard, the valid value of this field is 1. Other values are reserved. |
| 54h | 1 | bWriteBoosterBufferCapA djFac | Device specific | Capacity Adjustment Factor for the WriteBooster Buffer memory type. This value provides the LBA space reduction multiplication factor when WriteBooster Buffer is configured in user space reduction mode. Therefore, this parameter applies only if bWriteBoosterBufferPreserveUserSpaceEn is 00h. For "LU dedicated buffer" mode, the total user space is decreased by the following amount: bWriteBoosterBufferCapAdjFac * dLUNumWriteBoosterBufferAllocUnits * bAllocationUnitSize * dSegmentSize * 512 byte'. For "shared buffer" mode, the total user space is decreased by the following amount: bWriteBoosterBufferCapAdjFac * dNumSharedWriteBoosterBufferAllocUnits * bAllocationUnitSize * dSegmentSize * 512 byte. The value of this parameter is 3 for TLC NAND when SLC mode is used as WriteBooster Buffer, 2 for MLC NAND. |
| 55h | 1 | bSupportedWriteBoosterB ufferUserSpaceReduction Types | Device specific | The supportability of user space reduction mode and preserve user space mode. 00h: WriteBooster Buffer can be configured only in user space reduction type. 01h: WriteBooster Buffer can be configured only in preserve user space type. 02h: Device can be configured in either user space reduction type or preserve user space type. Others : Reserved |

# JEDEC Standard No. 220F
## Page 453

### 14.1.5.4 Geometry Descriptor (cont'd)

#### Table 14.13 — Geometry Descriptor

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 56h | 1 | bSupportedWriteBoosterBufferTypes | Device specific | The supportability of WriteBooster Buffer type.<br>00h: LU based WriteBooster Buffer configuration<br>01h: Single shared WriteBooster Buffer configuration<br>02h: Supporting both LU based WriteBooster Buffer and Single shared WriteBooster Buffer configuration<br>Others: Reserved |
| 57h-67h | 17 | Reserved | - | Reserved for Zoned Storage Extension Standard |
| 68h | 1 | bCapAdjFacRepresentation | Device specific | CapacityAdjFactor representation format<br>00h: Legacy 256ths<br>01h: Simple Fraction<br>Others: Reserved |

**NOTE 1** The Capacity Adjustment Factor value for Normal memory type is one.

### 14.1.5.5 Unit Descriptor

The Unit Descriptor describes specific characteristics and capabilities of an individual logical unit, for example geometry of the device and maximum addressable item. There are up to thirty two unit descriptors. In a QUERY REQUEST UPIU, an Unit Descriptor is addressed setting: DESCRIPTOR IDN = 02h, INDEX = unit index, and SELECTOR = 00h.

Table 14.14 is a table of Unit Descriptor names and attributes that runs consecutively through the next several pages.

# JEDEC Standard No. 220F
Page 454

## 14.1.5.5 Unit Descriptor (cont'd)

### Table 14.14. — Unit Descriptor

**UNIT DESCRIPTOR**

| Offset | Size | Name | MDV (1) | User Conf. (2) | Description |
|--------|------|------|---------|----------------|-------------|
| 00h | 1 | bLength | 2Dh | No | Size of this descriptor |
| 01h | 1 | bDescriptorIDN | 02h | No | Unit Descriptor Type Identifier |
| 02h | 1 | bUnitIndex | 00h to the number of LU specified by bMaxNumberLU | No | Unit Index |
| 03h | 1 | bLUEnable | 00h | Yes | Logical Unit Enable<br>00h: Logical Unit disabled<br>01h: Logical Unit enabled<br>02h: Reserved for Host Performance Booster (HPB) Extension Standard<br>Others: Reserved |
| 04h | 1 | bBootLunID | 00h | Yes | Boot LUN ID<br>00h: Not bootable<br>01h: Boot LU A<br>02h: Boot LU B<br>Others: Reserved. |
| 05h | 1 | bLUWriteProtect | 00h | Yes | Logical Unit Write Protect<br>00h: LU not write protected<br>01h: LU write protected when fPowerOnWPEn =1<br>02h: LU permanently write protected when fPermanentWPEn =1 03h: Reserved (for UFS Security Extension standard)<br>Others: Reserved |
| 06h | 1 | bLUQueueDepth | Device specific | No | Logical Unit Queue Depth<br>0 : LU queue not available (shared queuing is used)<br>[1 ... 255] : LU queue depth<br>If any bQueueDepth>0, bLUQueueDepth shall be 0. |
| 07h | 1 | bPSASensitive | Device specific | No(3) | 00h: LU is not sensitive to soldering<br>01h: LU is sensitive to soldering<br>Others: Reserved |

# JEDEC Standard No. 220F
Page 455

## 14.1.5.5 Unit Descriptor (cont'd)

### Table 14.14. — Unit Descriptor

| Offset | Size | Name | MDV⁽¹⁾ | User Conf.⁽²⁾ | Description |
|--------|------|------|---------|---------------|-------------|
| 08h | 1 | bMemoryType | 00h | Yes | Memory Type<br/>bMemoryType defines logical unit memory type.<br/>00h: Normal Memory<br/>01h: System code memory type<br/>02h: Non-Persistent memory type<br/>03h: Enhanced memory type 1<br/>04h: Enhanced memory type 2<br/>05h: Enhanced memory type 3<br/>06h: Enhanced memory type 4<br/>Others: Reserved |
| 09h | 1 | bDataReliability | 00h | Yes | Data Reliability<br/>bDataReliability defines the device behavior when a power failure occurs during a write operation to the logical unit<br/>00h: the logical unit is not protected. Logical unit's entire data may be lost as a result of a power failure during a write operation<br/>01h: logical unit is protected. Logical unit's data is protected against power failure.<br/>Others: Reserved |
| 0Ah | 1 | bLogicalBlockSize | 0Ch | Yes | Logical Block Size<br/>The size of addressable logical blocks is equal to the result of exponentiation with as base the number two and as exponent the bLogicalBlockSize value; 2^(bLogicalBlockSize) (i.e., bLogicalBlockSize = 0Ch corresponds to 4 Kbyte Logical Block Size).<br/>Its minimum value is 0Ch, which corresponds to 4 Kbyte |
| 0Bh | 8 | qLogicalBlockCount | 00h | Yes⁽⁴⁾ | Logical Block Count<br/>Total number of addressable logical blocks in the logical unit |
| 13h | 4 | dEraseBlockSize | 00h⁽⁵⁾ | No | Erase Block Size<br/>Optimal granularity for erase and discard operations.<br/>Value in number of Logical Blocks |
| 17h | 1 | bProvisioningType | 00h | Yes | Provisioning Type<br/>00h:Thin Provisioning is disabled (default)<br/>02h:Thin Provisioning is enabled and TPRZ = 0<br/>03h:Thin Provisioning is enabled and TPRZ = 1<br/>Others: Reserved |

**UNIT DESCRIPTOR**

# JEDEC Standard No. 220F
Page 456

## 14.1.5.5 Unit Descriptor (cont'd)

### Table 14.14. — Unit Descriptor

| Offset | Size | Name | MDV (1) | User Conf. (2) | Description |
|--------|------|------|---------|----------------|-------------|
| 18h | 8 | qPhyMemResourceCount | Device specific | No | Physical Memory Resource Count<br>Total physical memory resources available in the logical unit.<br>Value expressed in units of Logical Block Size. |
| 20h | 2 | wContextCapabilities | 00h | Yes | Bits [3:0]: MaxContextID is the maximum amount of contexts that the LU supports simultaneously. The sum of all MaxContextID must not exceed bMaxContextIDNumber.<br><br>Bits [6:4]:<br>LARGE_UNIT_MAX_MULTIPLIER_M1 is the highest multiplier that can be configured for Large Unit contexts, minus one. Large Unit contexts may be configured to have a multiplier in the range:<br>1 ≤ multiplier ≤ (LARGE_UNIT_MAX_MULTIPLIER_M1 + 1)<br>This field is read only.<br><br>Bit [15:7]: Reserved. |
| 22h | 1 | bLargeUnitGranularity_M1 | Device specific | No | Granularity of the Large Unit, minus one.<br>Large Unit Granularity = 1MB * (bLargeUnitGranularity_M1 + 1) |
| 23h | 6 | Reserved | - | - | Reserved for Host Performance Booster (HPB) Extension Standard |

**UNIT DESCRIPTOR**

# JEDEC Standard No. 220F
## Page 457

### 14.1.5.5 Unit Descriptor (cont'd)

#### Table 14.14. — Unit Descriptor

| Offset | Size | Name | MDV (1) | User Conf. (2) | Description |
|--------|------|------|---------|----------------|-------------|
| 29h | 4 | dLUNumWriteBoosterBufferAllocUnits | 00h | Yes | The WriteBooster Buffer size for the Logical Unit.<br><br>The dLUNumWriteBoosterBufferAllocUnits value shall be calculated using the following equation:<br><br>dLUNumWriteBoosterBufferAllocUnits = CEILING (WriteBoosterBufferCapacity × 1 / (bAllocationUnitSize × dSegmentSize × 512))<br><br>where WriteBoosterBufferCapacity is the desired WriteBooster Buffer size expressed in bytes. To configure 4 GB WriteBooster Buffer, if bAllocationUnitSize = 8, and dSegmentSize = 1024, then the value for the dLUNumWriteBoosterBufferAllocUnits is 0400h.<br><br>If this value is '0', then the WriteBooster is not supported for this LU.<br><br>The Logical unit among LU0 ~ LU7 can be configured for WriteBooster Buffer. Otherwise, whole WriteBooster Buffer configuration in this device is invalid. |

**NOTE 1** The column "MDV" (Manufacturer Default Value) specifies parameters value after device manufacturing. Some fields may be configured by the user writing the Configuration Descriptor.

**NOTE 2** "User Conf." column specifies which fields can be configured by the user writing the Configuration Descriptor: "Yes" means that the field can be configured, "No" means that the field is a capability of the device and cannot be changed by the user. The desired value shall be set in the equivalent parameter of the Configuration Descriptor.

**NOTE 3** bPSASensitive value is updated automatically by the device after device configuration.

**NOTE 4** qLogicalBlockCount can be configured setting the dNumAllocUnits parameter of the Configuration Descriptor.

**NOTE 5** dEraseBlockSize value is updated automatically by the device after device configuration.

### 14.1.5.6 RPMB Unit Descriptor

In a QUERY_REQUEST UPIU, the RPMB Unit Descriptor is addressed setting: DESCRIPTOR_IDN = 02h, INDEX = C4h, and SELECTOR = 00h.

Table 14.15 is a table of RPMB Unit Descriptor names and attributes that runs consecutively through the next several pages.

# JEDEC Standard No. 220F
## Page 458

### 14.1.5.6 RPMB Unit Descriptor (cont'd)

#### Table 14.15 — RPMB Unit Descriptor

**RPMB UNIT DESCRIPTOR**

| Offset | Size | Name | MDV⁽¹⁾ | User Conf. | Description |
|--------|------|------|---------|------------|-------------|
| 00h | 1 | bLength | 23h | No | Size of this descriptor |
| 01h | 1 | bDescriptorIDN | 02h | No | Unit Descriptor Type Identifier |
| 02h | 1 | bUnitIndex | C4h | No | Unit Index |
| 03h | 1 | bLUEnable | 01h | No | Logical Unit Enable<br>01h: Logical Unit enabled |
| 04h | 1 | bBootLunID | 00h | No | Boot LUN ID<br>00h: Not bootable |
| 05h | 1 | bLUWriteProtect | 00h | No | Logical Unit Write Protect<br>00h: LU not write protected |
| 06h | 1 | bLUQueueDepth | Device specific | No | Logical Unit Queue Depth<br>0: RPMB LU queue not available (shared queuing is used)<br>N: Queue depth available in RPMB LU. Only 1 task per region may be queued at any given time. N shall be 1 to 4 according to the number of regions enabled in bRPMBRegionEnable[0:3]. For example, when RPMB regions 1, 2, and 3 are enabled, N is set to 4. |
| 07h | 1 | bPSASensitive | Device specific | No | 00h: LU is not sensitive to soldering<br>01h: LU is sensitive to soldering<br>Others: Reserved |
| 08h | 1 | bMemoryType | 0Fh | No | Memory Type<br>0Fh: RPMB Memory Type |
| 09h | 1 | bRPMBRegionEnable | 00h | Yes | RPMB Region Enable<br>Bit-0: Don't care. RPMB region 0 is always enabled independent of this bit value.<br>Bit-1: If set to 1, RPMB region 1 is enabled.<br>Bit-2: If set to 1, RPMB region 2 is enabled.<br>Bit-3: If set to 1, RPMB region 3 is enabled.<br>Bit-4: If set to 1, Advanced RPMB Mode is enabled<br>Bit-5: If set to 1, RPMB Purge Operation is enabled<br>Bit-6 to Bit-7: Reserved. |

# 14.1.5.6 RPMB Unit Descriptor (cont'd)

## Table 14.15 — RPMB Unit Descriptor

### RPMB UNIT DESCRIPTOR

| Offset | Size | Name | MDV⁽¹⁾ | User Conf. | Description |
|--------|------|------|---------|------------|-------------|
| 0Ah | 1 | bLogicalBlockSize | 08h | No | **Logical Block Size**<br>The size of addressable logical blocks is equal to the result of exponentiation with as base the number two and as exponent the bLogicalBlockSize value: 2^bLogicalBlockSize (e.g., In Normal RPMB, bLogicalBlockSize = 08h corresponds to 256 byte Logical Block Size. In Advanced RPMB, bLogicalBlockSize = 0Ch corresponds to 4KB Logical)<br>This value shall be changed to the appropriate value based on RPMB configuration. |
| 0Bh | 8 | qLogicalBlockCount | Device specific | No | **Logical Block Count**<br>Total number of addressable logical blocks in the RPMB LU. For Normal RPMB, Logical Block Count shall be a multiple of 512. For Advanced RPMB, Logical Block Count shall be a multiple of 32. (i.e., 128 Kbyte)<br>This value shall be changed to the appropriate value based on RPMB configuration. |
| 13h | 1 | bRPMBRegion0Size | Device Specific | Yes | **RPMB Region 0 Size**<br>RPMB region 0 size is defined in 128KB unit (00h: 0KB, 01h: 128KB, ... , 80h: 16384KB). |
| 14h | 1 | bRPMBRegion1Size | 00h | Yes | **RPMB Region 1 Size**<br>RPMB region 1 size is defined in 128KB unit (00h: 0KB, 01h: 128KB, ... , 80h: 16384KB). |
| 15h | 1 | bRPMBRegion2Size | 00h | Yes | **RPMB Region 2 Size**<br>RPMB region 2 size is defined in 128KB unit (00h: 0KB, 01h: 128KB, ... , 80h: 16384KB). |
| 16h | 1 | bRPMBRegion3Size | 00h | Yes | **RPMB Region 3 Size**<br>RPMB region 3 size is defined in 128KB unit (00h: 0KB, 01h: 128KB, ... , 80h: 16384KB). |
| 17h | 1 | bProvisioningType | 00h | No | **Provisioning Type**<br>00h:Thin Provisioning is disabled |

---

JEDEC Standard No. 220F  
Page 459

# JEDEC Standard No. 220F
Page 460

## 14.1.5.6 RPMB Unit Descriptor (cont'd)

### Table 14.15 — RPMB Unit Descriptor

#### RPMB UNIT DESCRIPTOR

| Offset | Size | Name | MDV (1) | User Conf. | Description |
|--------|------|------|---------|------------|-------------|
| 18h | 8 | qPhyMemResourceCount | | No | Physical Memory Resource Count<br>Total physical memory resources available in the logical unit.<br>Value expressed in units of bLogicalBlockSize.<br>The dynamic device capacity feature does not apply to the RPMB well known logical unit therefore qPhyMemResourceCount value is always equal to qLogicalBlockCount value |
| 20h | 3 | Reserved | 0000h | | |

**NOTE 1** The column "MDV" (Manufacturer Default Value) specifies parameters value after device manufacturing. Some fields may be configured by the user writing the Configuration Descriptor.

# 14.1.5.7 Power Parameters Descriptor

This descriptor contains information about the power capabilities and power states of the device. In a QUERY REQUEST UPIU, the Power Parameters Descriptor is addressed setting: DESCRIPTOR IDN = 08h, INDEX = 00h, and SELECTOR = 00h.

## Table 14.6 — Power Parameters Descriptor

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 00h | 1 | bLength | 62h | Size of this descriptor |
| 01h | 1 | bDescriptorIDN | 08h | Power Parameters Descriptor Type Identifier |
| 02h | 2 | wActiveCCLevelsVCC[0] | Device specific | Maximum VCC current value for bActiveCCLevel = 0 |
| 04h | 2 | wActiveCCLevelsVCC[1] | Device specific | Maximum VCC current value for bActiveCCLevel = 1 |
| ... | ... | ... | ... | ... |
| 20h | 2 | wActiveCCLevelsVCC[15] | Device specific | Maximum VCC current value for bActiveCCLevel = 15 |
| 22h | 2 | wActiveCCLevelsVCCQ[0] | Device specific | Maximum VCCQ current value for bActiveCCLevel = 0 |
| 24h | 2 | wActiveCCLevelsVCCQ[1] | Device specific | Maximum VCCQ current value for bActiveCCLevel = 1 |
| ... | ... | ... | ... | ... |
| 40h | 2 | wActiveCCLevelsVCCQ[15] | Device specific | Maximum VCCQ current value for bActiveCCLevel = 15 |
| 42h | 2 | wActiveCCLevelsVCCQ2[0] | Device specific | Maximum VCCQ2 current value for bActiveCCLevel = 0 |
| 44h | 2 | wActiveCCLevelsVCCQ2[1] | Device specific | Maximum VCCQ2 current value for bActiveCCLevel = 1 |
| ... | ... | ... | ... | ... |
| 60h | 2 | wActiveCCLevelsVCCQ2[15] | Device specific | Maximum VCCQ2 current value for bActiveCCLevel = 15 |

---
*JEDEC Standard No. 220F*  
*Page 461*

# JEDEC Standard No. 220G
Page 462

## 14.1.5.8 Interconnect Descriptor

The Interconnect Descriptor contains the MIPI M-PHY® specification version number and the MIPI UniPro® specification version number. In a QUERY REQUEST UPIU, the Interconnect Descriptor is addressed setting: DESCRIPTOR IDN = 04h, INDEX = 00h, and SELECTOR = 00h.

**Table 14.7 — Interconnect Descriptor**

| Offset | Size | INTERCONNECT_DESCRIPTOR |  |  |
|--------|------|-------------------------|----------|-------------|
|        |      | **Name**                | **Value** | **Description** |
| 00h    | 1    | bLength                 | 06h      | Size of this descriptor |
| 01h    | 1    | bDescriptorIDN          | 04h      | Interconnect Descriptor Type Identifier |
| 02h    | 2    | bcdUniproVersion        | 0200h    | MIPI UniPro® version number in BCD format Example: version 3.21 = 0321h |
| 04h    | 2    | bcdMphyVersion          | 0500h    | MIPI M-PHY® version number in BCD format Example: version 3.21=0321h |

## 14.1.5.9 Manufacturer Name String Descriptor

This descriptor contains the UNICODE, left justified, manufacturer name string.

The content of the descriptor shall be identical to the content of the "VENDOR IDENTIFICATION" field in Inquiry Response Data. The length of the descriptor shall be 12h (18 decimal), containing exactly 8 UNICODE characters, to match "VENDOR IDENTIFICATION" field in Inquiry Response Data.

In a QUERY REQUEST UPIU, the Manufacturer Name String Descriptor is addressed setting: DESCRIPTOR IDN = 05h, INDEX = iManufacturerName (Device Descriptor parameter), and SELECTOR = 00h.

**Table 14.8 — Manufacturer Name String**

| Offset | Size | MANUFACTURER NAME STRING |  |  |
|--------|------|---------------------------|----------|-------------|
|        |      | **Name**                  | **Value** | **Description** |
| 00h    | 1    | bLength                   | 12h      | Size of this descriptor |
| 01h    | 1    | bDescriptorIDN            | 05h      | String Descriptor Type Identifier |
| 02h    | 2    | UC[0]                     |          | Unicode string character |
| 04h    | -    | -                         |          | - |
| 10h    | 2    | UC[7]                     |          | Unicode string character |

# JEDEC Standard No. 220G
## Page 463

### 14.1.5.10 Product Name String Descriptor

This descriptor contains the UNICODE, left justified, product name string.

The content of the descriptor shall be identical to the content of the "PRODUCT IDENTIFICATION" field in Inquiry Response Data. The length of the descriptor shall be 22h (34 decimal), containing exactly 16 UNICODE characters, to match "PRODUCT IDENTIFICATION" field in Inquiry Response Data.

In a QUERY REQUEST UPIU, the Product Name String Descriptor is addressed setting: DESCRIPTOR IDN = 05h, INDEX = iProductName (Device Descriptor parameter), and SELECTOR = 00h.

#### Table 14.9 — Product Name String

| Offset | Size | PRODUCT NAME STRING DESCRIPTOR |  |  |
|--------|------|------------------|-------|---------------------------|
|        |      | Name | Value | Description |
| 00h | 1 | bLength | 22h | Size of this descriptor |
| 01h | 1 | bDescriptorIDN | 05h | String Descriptor Type Identifier |
| 02h | 2 | UC[0] | | Unicode string character |
| 04h | - | - | - | - |
| ... | ... | ... | ... | ... |
| 20h | 2 | UC[15] | | Unicode string character |

### 14.1.5.11 OEM ID String Descriptor

This descriptor contains the UNICODE OEM ID string that may consist of up to 126 UNICODE characters. Number of UNICODE characters is calculated by (LENGTH − 2) ÷ 2.

In a QUERY REQUEST UPIU, the OEM ID String Descriptor is addressed setting: DESCRIPTOR IDN = 05h, INDEX = iOemID (Device Descriptor parameter), and SELECTOR = 00h.

The OEM ID String Descriptor identifies the OEM name (e.g. name of Phone Manufacturer, or name of Car Manufacturer, etc.).

OEM_ID String descriptor is: readable, writeable if bConfigDescrLock attribute value is equal to 00h.

#### Table 14.20 — OEM_ID String

| Offset | Size | OEM ID STRING DESCRIPTOR |  |  |
|--------|------|------------------|-------|---------------------------|
|        |      | Name | Value | Description |
| 00h | 1 | bLength | LENGTH | Size of this descriptor |
| 01h | 1 | bDescriptorIDN | 05h | String Descriptor Type Identifier |
| 02h | 2 | UC[0] | | Unicode string character |
| 04h | - | - | - | - |
| ... | ... | ... | ... | ... |
| LENGTH-2 | 2 | UC[(LENGTH-2)÷2-1] | | Unicode string character |

# JEDEC Standard No. 220G
Page 464

## 14.1.5.12 Serial Number String Descriptor

This descriptor contains the UNICODE serial number string that may consist of up to 126 UNICODE characters. Number of UNICODE characters is calculated by (LENGTH − 2) ÷ 2.

In a QUERY REQUEST UPIU, the Serial Number String Descriptor is addressed setting: DESCRIPTOR IDN = 05h, INDEX = iSerialNumber (Device Descriptor parameter), and SELECTOR = 00h.

### Table 14.21 — Serial Number String Descriptor

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 00h | 1 | bLength | LENGTH | Size of this descriptor |
| 01h | 1 | bDescriptorIDN | 05h | String Descriptor Type Identifier |
| 02h | 2 | UC[0] | | Unicode string character |
| 04h | - | | | - |
| LENGTH-2 | 2 | UC[(LENGTH-2)÷2-1] | | Unicode string character |

## 14.1.5.13 Product Revision Level String Descriptor

This descriptor contains the UNICODE, left justified, product revision level string.

The content of the descriptor shall be identical to the content of the "PRODUCT REVISION LEVEL" field in Inquiry Response Data. The length of the descriptor shall be Ah, containing exactly 4 UNICODE characters, to match "PRODUCT REVISION LEVEL" field in Inquiry Response Data.

In a QUERY REQUEST UPIU, the Product Revision Level String Descriptor is addressed setting: DESCRIPTOR IDN = 05h, INDEX = iProductRevisionLevel (Device Descriptor parameter), and SELECTOR = 00h.

### Table 14.22 — Product Revision Level String

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 00h | 1 | bLength | 0Ah | Size of this descriptor |
| 01h | 1 | bDescriptorIDN | 05h | String Descriptor Type Identifier |
| 02h | 2 | UC[0] | | Unicode string character |
| 04h | - | | | - |
| 08h | 2 | UC[3] | | Unicode string character |

# 14.1.5.14 Device Health Descriptor

Device Health Descriptor provides information related to the health of the device.

In a QUERY REQUEST UPIU, the Device Health Descriptor is addressed by setting: DESCRIPTOR IDN = 09h, INDEX = 00h and SELECTOR = 00h.

## Table 14.23 — Device Health Descriptor

| Offset | Size | Name | Value | Description |
|--------|------|------|-------|-------------|
| 00h | 1 | bLength | 2Dh | Size of this descriptor |
| 01h | 1 | bDescriptorIDN | 09h | Device Health Descriptor Type Identifier |
| | | | | Pre End of Life Information |
| | | | | This field provides indication about device life time |
| | | | | reflected by average of reserved blocks. |
| | | | | 00h: Not defined |
| | | | | 01h: Normal |
| 02h | 1 | bPreEOLInfo | Device specific | 02h: Warning. Consumed 80% of reserved blocks. |
| | | | | 03h: Critical. Consumed 90% of reserved blocks. |
| | | | | Others: Reserved |
| | | | | This field provides an indication of the device life time |
| | | | | based on the amount of performed program/erase cycles. |
| | | | | The calculation method is vendor specific and referred as |
| | | | | method A. |
| | | | | 00h: Information not available |
| | | | | 01h: 0% - 10% device life time used |
| | | | | 02h: 10% - 20% device life time used |
| | | | | 03h: 20% - 30% device life time used |
| 03h | 1 | bDeviceLifeTimeEstA | Device specific | 04h: 30% - 40% device life time used |
| | | | | 05h: 40% - 50% device life time used |
| | | | | 06h: 50% - 60% device life time used |
| | | | | 07h: 60% - 70% device life time used |
| | | | | 08h: 70% - 80% device life time used |
| | | | | 09h: 80% - 90% device life time used |
| | | | | 0Ah: 90% - 100% device life time used |
| | | | | 0Bh: Exceeded its maximum estimated device life time |
| | | | | Others: Reserved |

---

JEDEC Standard No. 220G  
Page 465

# JEDEC Standard No. 220G
Page 466

## 14.1.5.14 Device Health Descriptor (cont'd)

### Table 14.23 — Device Health Descriptor

| Offset | Size | Name | Value | Description |
|--------|------|------|--------|-------------|
| 04h | 1 | bDeviceLifeTimeEstB | Device specific | This field provides an indication of the device life time based on the amount of performed program/erase cycles. The calculation method is vendor specific and referred as method B.<br/>00h: Information not available<br/>01h: 0% - 10% device life time used<br/>02h: 10% - 20% device life time used<br/>03h: 20% - 30% device life time used<br/>04h: 30% - 40% device life time used<br/>05h: 40% - 50% device life time used<br/>06h: 50% - 60% device life time used<br/>07h: 60% - 70% device life time used<br/>08h: 70% - 80% device life time used<br/>09h: 80% - 90% device life time used<br/>0Ah: 90% - 100% device life time used<br/>0Bh: Exceeded its maximum estimated device life time<br/>Others: Reserved |
| 05h | 32 | VendorPropInfo | Device specific | Reserved for Vendor Proprietary Health Report |
| 25h | 4 | dRefreshTotalCount | Device specific | Total Refresh Count<br/>Indicate how many times the device complete refresh for the entire device. Incremented by 1 when dRefreshProgress reach 100000 (100.000%). |
| 29h | 4 | dRefreshProgress | Device specific | Refresh Progress<br/>Indicate the refresh progress in %.<br/>dRefreshProgress will indicate 0.000% ~ 100.000% in dec.<br/>dRefreshProgress = 100000 (dec) when it complete 100.000%.<br/>dRefreshProgress = 1000 (dec) when it complete 1.000%.<br/>When this value reach 100000 (100.000%)<br/>1. Device stops refreshing even if it did not complete the number of units specified by bRefreshUnit<br/>2. dRefreshProgress shall be reset to 0<br/>3. dRefreshTotalCount shall be incremented by 1<br/>When bRefreshMethod = 02h (Manual-Selective), even though some of physical blocks are not refreshed by device choice, dRefreshProgress should be incremented just as much as bRefreshUnit. |