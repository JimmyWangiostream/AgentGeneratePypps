# JEDEC Standard No. 220G
Page 372

## 13.4 Host Device Interaction

### 13.4.1 Overview

This sub- clause describes several UFS features conceived to improve performance and/or reliability. Some of them are related directly to commands present in the logical unit queues (e.g., inter-LU priority, system data tag, context management), others are related to the device state (e.g., background operations, dynamic device capacity) or focused on reliability (e.g., data reliability, real-time clock information).

### 13.4.2 Applicable Devices

All the features described 13.4 should be implemented on UFS devices. The extent to which the features are implemented will be up to the device manufacturer. It is expected that poor implementations will result in lower device performance or reliability and higher max power consumption in the low power modes.

### 13.4.3 Command Queue: Inter-LU Priority

The specific details of how commands interact in a queue of a specific logical unit are handled in other clauses. This sub-clause outlines how the queues within a device interact with each other. There can be many different implementations of a UFS device. For example, it may be implemented as a single or multithreaded processor. In order to make the UFS spec implementation agnostic this sub-clause outlines a parameter that allow the host to communicate to the device its priorities so that the device can take this into account when executing commands from the host.

In the implementation case where several queues are serviced from a single execution unit, it is necessary for the host to either designate all queues as having the same priority or designate a single Queue as having a higher priority. A parameter value shall be defined to allow the host to designate a queue as having high or no priority. In the case where a queue is designated as having a higher priority, whenever a command enters the queue with the high priority it will be executed as soon as possible resulting in commands from other queues being stalled.

One example of where a host may want to take advantage of this feature is when the host has allocated one logical unit to be a code execution unit and another unit to be a mass storage unit. In this example the execution of code takes priority over mass storage transfers, so the host would set the parameter bit associated with the code logical unit to be high priority and leave the remaining queues as lower priority. The logical unit supports two level of queue priorities:

1. High priority – This is used for logical unit with high priority requests. Any commands sent to this logical unit will have higher priority than commands sent to logical units with lower priority. For example, when servicing demand-paging applications, read commands would have this priority.

2. No priority – This is used for all regular logical units which do not belong to priority #1

In addition to the execution of commands explicitly issued by the host, the device may execute background operations for device house-keeping. In general those operations have a much lower priority than the commands sent by the host and are implemented using a specific method described in 0, Background Operations Mode.

# JEDEC Standard No. 220G
Page 373

## 13.4.3.1 Implementation

The bHighPriorityLUN parameter in the Device Descriptor shall be set to configure which logical unit has the command queue with the higher priority.

bHighPriorityLUN shall be set to:

• 7Fh: if all logical units have the same priority.

• LUN of the higher priority logical unit.

| Name | Description | Valid Values | Default⁽¹⁾ |
|------|-------------|--------------|-------------|
| bHighPriorityLUN | bHighPriorityLUN defines the high priority logical unit. If this parameter value is 7Fh all logical units have the same priority. | 0 to the number of LU specified by bMaxNumberLU, and 7Fh | 7Fh |

NOTE 1 The column "Default" defines the parameter value set by the device manufacturer.

## 13.4.4 Background Operations Mode

### 13.4.4.1 Introduction

A managed device requires time to execute management tasks. The background operations mode grants the device time to execute the commands associated with these flash management tasks. Flash management operations may include, but are not limited to, wear leveling, bad block management, wipe and garbage collection. The operations completed during the background operations period are determined by the device manufacturer and are not covered by the UFS spec.

### 13.4.4.2 Purpose

**Performance Improvement**
The intent of this mode is to improve a device response to host commands by allowing the device to postpone device management activities that occur as a result of host initiated operations to periods when the host is not using the device.

Systems that will use a UFS device tend to have peak periods of activity, in which the best response possible is needed from the UFS device. These peak periods are followed by idle periods, where the host can allow the device to do device management operations. Allowing better communication between the host and the device on when these idle periods will occur allows the UFS device to perform more optimally in the system.

The device will still be permitted to do device management when the host initiates operations, however the downside of doing this may be poorer device performance. This mode will just give device manufacturers the option to delay device management operations to improve performance. It is recommended that devices postpone as many tasks as possible to take full advantage of the possible performance improvements associated with this feature.

# JEDEC Standard No. 220G
Page 374

## 13.4.4.2 Purpose (cont'd)

### Host Power Management
This mode will also allow the host to control when the device uses power to perform management activities. The host will have more knowledge about the power consumed by the system and can make the appropriate tradeoffs about when to use system power and when to conserve it.

An example of where host control over power consumed by the device could be an advantage would be the case where the system has very little battery power and the UFS device has a lot of unused memory.

In this case the host may not wish for the device to perform clean up operations but conserve the power for more critical system functions.

Allowing the host to communicate with the device on when activities can be performed will allow better system power management, which can be controlled by the host.

## 13.4.4.3 Background Operations Status

The device signals to the host that the device has a need for background operations using the Exception Event mechanism, and in particular the URGENT_BKOPS bit in wExceptionEventStatus

• '0': No immediate need to execute background operation (corresponds to no operations or non-critical)

• '1': Immediate need to execute background operation (corresponds to performance being impacted or critical)

When the host detects a request for executing background operations (URGENT_BKOPS set to one) it may read the bBackgroundOpStatus attribute to find out the need level, as follows:

00h : No operations required  
01h : Operations outstanding (non-critical)  
02h : Operations outstanding (performance being impacted)  
03h : Operations outstanding (critical)

The URGENT_BKOPS bit is set to zero if the bBackgroundOpStatus is set to zero or one, otherwise it is set to one.

It is expected that the host will respond as soon as possible when the status changes to service, since if the background operations are not properly managed, then the device could fail to operate in an optimal way.

If device status is operations outstanding (critical), commands other than mode sense and mode select may be terminated with CHECK CONDITION status. The host should put in all possible measures to ensure the device never reaches this state since it means the device is no longer able to operate.

The point at which the device enters each of these states is up to the manufacturer and is not defined in this standard.

# JEDEC Standard No. 220G
Page 375

## 13.4.4.4 Operation Initiation

There is no explicit command to start the background operations. A mode enable bit indicates whether the device is allowed to execute background operations. If the background operations enable bit is set and the device is in Active power mode or Idle power mode, then the device is allowed to execute any internal operations.

When the device receives a command which requires a data transfer and if all command queues are empty, then the device shall start the data transfer sending DATA IN UPIU or RTT UPIU within the time declared in BackgroundOpsTermLat. The host can minimize the device response time by disabling background operations mode during critical performance times.

In the case where the background operations status is "operations outstanding (critical)", the aforementioned latency limit does not apply.

# JEDEC Standard No. 220G
Page 376

## 13.4.4.5 Power Failure

It is the device's responsibility to ensure that the data in the device is not corrupted if a power failure occurs during a background operation.

## 13.4.4.6 Implementation

### 13.4.4.6.1 Background Operations Enable

fBackgroundOpsEn is the Flag to be used to enable or disable the execution of background operations. This Flag is defined as follows:

• 0 = Device is not permitted to run background operations
• 1 = Device is permitted to run background operations.

The default value of this Flag is one: background operations permitted. The device shall terminate ongoing background operations when this Flag is cleared by the host. For more details see Table 14.26.

### 13.4.4.6.2 Background Operations Status

bBackgroundOpStatus is an attribute defined as follows:
00h = not required
01h = required, not critical
02h = required, performance impact
03h = critical.

For more details, see 14.3.

### 13.4.4.6.3 Background Operations Termination Latency

bBackgroundOpsTermLat defines the maximum latency for starting data transmission when background operations are ongoing. The termination latency limit applies to two cases:
• When the device receives a COMMAND UPIU with a transfer request. The device shall start the data transfer and send a DATA IN UPIU or a RTT UPIU within the latency limit.
• When the device receives QUERY REQUEST UPIU clearing fBackgroundOpsEn Flag. The device is expected to terminate background operations within the latency limit.

The termination limit does not apply in the case where the background operations status is "operations outstanding (critical)".

bBackgroundOpsTermLat is a parameter of the Device Descriptor and its granularity is 10msec. It is expected that transitions between link states (e.g., HIBERNATE to ACTIVE) or temporary congestion on the link occur in shorter timescales and are therefore negligible in comparison to the background operations timescale.

## 13.4.5 Power Off Notification

A UFS host will notify the device when it is going to power the device off by requesting the device to move to UFS-PowerDown power mode. This will give the device time to cleanly complete any ongoing operations. The device will respond to the host when it is ready for power off, meaning that the device entered the UFS-PowerDown power mode. Host can then power off the device without the risk of data loss.

# 13.4.6 Dynamic Device Capacity

Common storage devices assume a fixed capacity. This presents a problem as the device ages and gets closer to its end of life. When some blocks of the device become too old to be used reliably, spare blocks are reallocated to replace them. A device contains some spare blocks for this purpose, as well as for some housekeeping operations. However, when all spare blocks are consumed, the device can no longer meet its fixed capacity definition and it stops being functional (some become read-only, some stop responding completely).

A simple solution to enable the host to continue operation at the end of the device lifetime, would be to allow the capacity to be dynamic. If the device is allowed to reduce its reported capacity, it can reallocate blocks that have used to store data as new spare blocks to compensate for aging. To support this, the device needs to report to the host how much more spare blocks it needs for each logical unit, and then the host needs to relinquish some used blocks to let the device reallocate them as spares.

A device may implement a spare blocks resource management policy either per logical unit, allocating a fixed amount of spare blocks per logical unit, or per memory type, allocating a fixed amount of spare blocks for all logical units with the same memory type (bMemoryType).

bDynamicCapacityResourcePolicy parameter in the Geometry Descriptor indicates which spare blocks resource management policy is implemented.

## 13.4.6.1 Implementation

### 13.4.6.1.1 Initial Device Requirements

• Only logical units that support thin provisioning and logical block provisioning management functions can be involved in the dynamic device capacity process. The host can discover if thin provisioning is enabled and if a logical unit supports logical block provisioning management functions at UTP level, reading the bProvisioningType parameter in the Unit Descriptor of each logical unit, or at SCSI level through the TPE bit in the READ CAPACITY (16) parameter data.

  ○ bProvisioningType shall be either 02h or 03h.
  
  ○ TPE bit shall be set to one.

• The Unit Descriptor of each logical unit includes the following two parameters: qLogicalBlockCount and qPhyMemResourceCount.

  ○ The qLogicalBlockCount is equal to the total number of addressable logical blocks in the logical unit. Its value is established when the logical unit is configured and never changes during the device life time. In particular, the qLogicalBlockCount value shall be equal to RETURNED_LOGICAL_BLOCK ADDRESS + 1 (RETURNED_LOGICAL_BLOCK_ADDRESS is a field included in the Read Capacity Parameter Data and corresponds to the last addressable block on medium under control of logical unit).
  
  ○ The qPhyMemResourceCount is equal to the total physical memory resources available in the logical unit, expressed in 2^bLogicalBlockSize unit. Its value decreases with the execution of dynamic capacity process.

• UFS requires that there shall be sufficient resource in the physical memory resources pool to support the logical addressable memory space reported in READ_CAPACITY when the device is first configured. Therefore, qPhyMemResourceCount shall be equal to qLogicalBlockCount in the Unit Descriptor initially.

• Dynamic device capacity feature does not involve the following logical units: RPMB well known logical unit, power-on write protected logical units (independently of fPowerOnWPEn flag value), permanently write protected logical units (independently of fPermanentWPEn flag value), or logical units configured as boot logical unit (Boot LUN ID = 01h or 02h, independently of bBootLunEn value).

# JEDEC Standard No. 220G
Page 378

## 13.4.6.1.2 Dynamic Capacity Procedural Flow

1) When the physical memory resources necessary for proper operation in a logical unit has been drawn down, the device may request to the host to remove some resources from the physical memory resources pool serving the logical address space of the logical units. This is achieved setting to one the DYNCAP_NEEDED bit in the wExceptionEventStatus attribute. If DYNCAP_EVENT_EN bit in wExceptionEventControl attribute is one, then the EVENT_ALERT bit of Device Information field included in the RESPONSE UPIU will be set to one.

2) Device shall indicate the amount of physical memory to be removed from the resource pool in dDynCapNeeded attribute. Each element of the dDynCapNeeded[LUN] shall be equal to the amount of bytes to be removed divided by the optimal write block size (bOptimalWriteBlockSize is a parameter in the Geometry Descriptor). Therefore, the host can calculate the amount of physical memory to be removed from the resource pool for each logical unit multiplying the dDynCapNeeded[LUN] attribute by bOptimalWriteBlockSize parameter. UFS device shall not request to remove physical memory from the resource pool of logical units which are write protected or configured as boot logical unit (dDynCapNeeded[LUN] shall be zero).

3) The host ensures that all outstanding tasks in the device queues have been completed or aborted.

4) If the device spare blocks resource management policy is per memory type (bDynamicCapacityResourcePolicy = 01h), then the host should ensure that the amount of LBAs in the deallocated state in all logical units with the same memory type (bMemoryType) is equal to or greater than the amount of requested physical memory resources from all logical units with the same memory type (bMemoryType).

   For example, assuming that bDynamicCapacityResourcePolicy = 01h and the device asks to remove logical blocks from the resource pool of a single logical unit, the host may remove blocks from one or more logical units having that particular memory type as long as the total amount of logical blocks in a deallocated state results be greater than or equal to the total amount of logical blocks specified by the device.

   However, if the device spare blocks resource management policy is per logical unit (bDynamicCapacityResourcePolicy = 00h), then host ensures that the amount of LBAs in the deallocated state is equal or greater than the amount of requested physical memory resources for each logical unit.

   The host deallocates LBAs sending one or more UNMAP commands.
   a) The range(s) of LBA in the deallocate state shall be aligned to a bOptimalWriteBlockSize boundary, and their size shall be an integer multiple of bOptimalWriteBlockSize .
   b) The LBA range(s) shall be equal or greater than the memory resources amount that has been requested by the device for each logical unit.
   c) The LBA range(s) does not need to be at the end of the logical address space.

5) The host sets fPhyResourceRemoval flag to one and triggers an EndPointReset or a device hardware reset to initiate the dynamic capacity operation.

6) The host may either execute the complete boot process as described in 13.1, UFS Boot, or may skip reading the boot logical unit and set fDeviceInit flag to one to start the device initialization. During this phase the device will execute the dynamic capacity operation. The host waits until the device clears fDeviceInit flag. The device initialization may take a time longer than normal initialization due to internal processes necessary to re-arrange physical memory resources. If a power loss occurs, the dynamic capacity operation will proceed at the next power up during the device initialization.

# JEDEC Standard No. 220G
## Page 379

### 13.4.6.1.3 Dynamic Capacity Procedural Flow (cont'd)

7) When the dynamic capacity operation is completed, the device will clear fDeviceInit flag and the fPhyResourceRemoval flag. If the operation is completed successfully, the DYNCAP_NEEDED bit is cleared too. Therefore the EVENT_ALERT bit in Device Information will return to zero, if no other exception events are active. The qPhyMemResourceCount parameter in the Unit Descriptors is updated with a new value reflecting the amount of physical memory resources remaining in the resource pool.

   **NOTE:** The qLogicalBlockCount parameter in the Unit Descriptors and the RETURNED_LOGICAL_BLOCK ADDRESS parameter in Read Capacity Parameter Data will stay the same as initially configured. Therefore, the updated qPhyMemResourceCount value will be less than those two parameters after dynamic capacity operation.

8) If the dynamic capacity operation does not succeed, for example because LBA range(s) does not meet one or more of the requirements described in point 4, the DYNCAP_NEEDED bit shall remain set to one. Therefore, the EVENT_ALERT bit in the Device Information field of the RESPONSE UPIU will remain set to one to notify the host that further dynamic capacity operation is needed.

   **NOTE:** The dDynCapNeeded[LUN] attribute value may have been updated.

9) To account for the reduction of the physical memory resources pool after dynamic capacity operation, the host maintains a range(s) of LBA's in deallocated state that are aligned in address and size to integer multiples of bOptimalWriteBlockSize, with the total equal to or greater than qLogicalBlockCount minus qPhyMemResourceCount. Otherwise, a write error will result when the host attempts to write (map) more LBA's than the available physical memory resources.

   **NOTE:** The host may change the LBA range(s) that are in deallocate state during the use of the device.

### 13.4.6.1.3 Dynamic Device Capacity Notification

The dynamic device capacity is one of the exception events that may set the EVENT_ALERT bit of the Device Information field included in the RESPONSE UPIU.

To enable the setting of this bit, the DYNCAP_EVENT_EN bit in the wExceptionEventControl attribute shall be set to one.

When the host detects that the EVENT_ALERT bit is set to one, it should read the wExceptionEventStatus attribute to discover if the source of this event is a request for reducing the device capacity. In particular, if DYNCAP_NEEDED bit is set to one, the host should process the request as described in this standard.

The DYNCAP_EVENT_EN bit shall be set to zero if the host is not capable or does not intend to use the dynamic device capacity feature. Otherwise, a dynamic capacity request event will set the EVENT_ALERT bit to one, masking out notification of other exception events.

# JEDEC Standard No. 220G
## Page 380

### 13.4.6.1.4 Error Handling

• Success/failure to unmap (release) LBA's is as defined in UNMAP command.

• If the host ignores the dynamic device capacity notification and continues to write to the device without unmapping LBA's to free up physical memory, the device may become non-writable over time and cause a WRITE command to fail. In which case, the device server shall return the following error condition in response to the WRITE command.

  ○ The device server shall terminate the command requesting the operation with CHECK CONDITION status with the sense key set to DATA PROTECT and the additional sense code set to SPACE ALLOCATION FAILED WRITE PROTECT.

• When the qPhyMemResourceCount is less than qLogicalBlockCount in Unit Descriptors, it indicates that the physical memory resources pool is smaller than the logical addressable memory space (LBA's) in the logical unit. It is the host's responsibility to keep track of the amount of physical memory available. If the host attempts to write more data than the available physical memory resources and the device is unable to complete the write operation successfully, the device shall return the following error condition.

  ○ The device server shall terminate the command requesting the operation with CHECK CONDITION status with the sense key set to DATA PROTECT and the additional sense code set to SPACE ALLOCATION FAILED WRITE PROTECT.

### 13.4.6.1.5 Physical Memory Resource State Machine

Figure 13.5 shows the state machine for the physical memory resources. In addition to the "Mapped" state and the "Deallocated" state, which are defined in logical block provisioning state machine too, there is the "Removed from the Resource Pool" state.

[THIS IS FIGURE: A state machine diagram showing three states connected by arrows:
1. "Mapped" (green oval) at the top
2. "Deallocated" (yellow oval) on the right 
3. "Removed from resource pool" (orange oval) on the left
Arrows show transitions: (1) WRITE from Deallocated to Mapped, (2) UNMAP from Mapped to Deallocated, and (3) from Deallocated to Removed from resource pool. Labels indicate "Initial state for UFS", "UFS definition outside SCSI", and "Device initialization with fPhyResourceRemoval = '1'"]

**Figure 13.5 — Physical Memory Resource State Machine**

1) Write operation: physical memory resource from the resource pool is mapped to LBA containing valid data.
2) UNMAP operation for erase/discard:
   a) Physical memory resource is unmapped (deallocated) from LBA and returned to the resource pool.
   b) Residual data in unmapped physical memory resource is not valid.
3) Device re-initialization with fPhyResourceRemoval flag previously set to one causes some physical memory resources to be removed from the resource pool servicing the logical address space. After completion the qPhyMemResourceCount is updated by UFS device to indicate the amount of physical memory resources remaining in the resource pool of each logical unit.

# 13.4.7 Data Reliability

## 13.4.7.1 Description

The UFS host has the ability to define the level of data reliability during normal operation and power failure per logical unit.

There are two components to the data reliability that are defined for UFS. The first component deals with the data currently being written and the second deals with the data that has previously been stored in the medium.

The first component, also known as Reliable Write, means that if the device loses power during a write operation to the medium (when executing a SCSI write command, a host initiated flush of data to the medium, etc.), the data in the range affected by the operation will be either the old data or the new written data when the device recovers from power failure.

Keeping either the old or new data is important for the file system to recover after power loss. The file system may keep its structures segmented and signed with CRC or equivalent mechanism. The device insures that a large enough granularity of data is authentic either with an old or new copy, to make sure the file system can validate or invalidate these segments.

The resolution for the old and new data shall be aligned to the logical block size. Figure 13.6 shows some of the possible scenarios that the host will see when it recovers from power failure during a 32 Kbyte write operation in a logical unit with 4 Kbyte logical block size.

For RPMB well known logical unit, the data reliability granularity shall be equal to bRPMB_ReadWriteSize × 256 bytes in Normal RPMB & bRPMB_ReadWriteSize X 4K bytes in Advanced RPMB. The bRPMB_ReadWriteSize value shall be changed to the appropriate value based on RPMB configuration.

[Figure 13.6 shows a diagram illustrating data status after power failure during a reliable write operation. The diagram displays a 32 Kbyte write operation divided into 8 blocks of 4 Kbyte each. Two possible scenarios are shown:
1. Top row: NEW | OLD | NEW | NEW | NEW | NEW | OLD | OLD
2. Bottom row: NEW | NEW | NEW | NEW | OLD | OLD | OLD | OLD

The diagram demonstrates how after power failure, each 4 Kbyte block contains either completely old data or completely new data, with no partial writes within individual blocks.]

**Figure 13.6 — Example of Data Status After a Power Failure During Reliable Write Operation**

The second component, also known as Data Reliability, allows the host to define the level of protection to be applied to existing data on the device. In some technologies that will be used to implement UFS devices, the device has the option to potentially sacrifice some of the existing data on a device during a power failure in order to provide better write performance. Depending on the application for the end device the host can select per logical unit whether the data in that logical unit shall be protected during power failure, which may have a performance impact, or to select device performance with the risk of losing data during a power failure.

Data Reliability feature for each logical unit can be set when the device is configured during system integration.

---
*JEDEC Standard No. 220G*
*Page 381*

# JEDEC Standard No. 220G
## Page 382

### 13.4.7.1 Description (cont'd)

In particular, if Data Reliability is enabled, the logical unit will execute Reliable Write operation and the data already stored in the medium will not be corrupted by a power failure occurred during the execution of a write operation to the medium.

The data reliability feature will be configurable only for logical units and not for well known logical units.

The RPMB well known logical unit will automatically select data reliability.

### 13.4.7.2 Implementation

bDataReliability parameter in the Unit Descriptor shall be used by the host to configure the logical unit data reliability.

bDataReliability values are defined as in the following:
- 00h: Data reliability disabled  
  Corruption of the existing data in the medium of the specific logical unit may occur if a power loss happens during device activity like writing of data to medium.
- 01h: Data reliability enabled  
  The existing data stored in the medium of the specific logical unit shall not be corrupted if a power loss occurs, and the memory range that was accessed by the interrupted write command shall contain the old data or new data (or a mixture of old and new data as explained in 13.4.7.1) once power is restored.

#### Table 13.4 — Parameter for Controlling Logical Unit Data Reliability

| Parameter Name | Description |
|----------------|-------------|
| bDataReliability | bDataReliability defines the device behavior when a power failure occurs when writing data to the medium<br>00h: Data reliability disabled<br>01h: Data reliability enabled<br>Others: Reserved |

### 13.4.8 Real-Time Clock Information

Providing Real Time Clock (RTC) information to a storage device could be useful for the device internal maintenance operations (execution of RTC internal operations is not affected by fBackgroundOpsEn flag value).

Host may provide either absolute time if available, or relative time information. This feature provides a mechanism for the host to update either absolute or relative time.

The host sends RTC information when a wPeriodicRTCUpdate has passed since the last RTC information update. In case the device is not powered up or asleep when the period has expired, the host wakes it up and update RTC information.

**NOTE** When device is configured with wPeriodicRTCUpdate as 'undefined' (see Device Descriptor) a wPeriodicRTCUpdate could not expire and the host may update RTC information considering vendor recommendations.

# JEDEC Standard No. 220G
## Page 383

### 13.4.8 Real-Time Clock Information (cont'd)

It is recommended to provide RTC information after transitioning from UFS-Sleep, UFS-DeepSleep or UFS-PowerDown power mode to Active power mode.

Updating RTC information is done by writing to dSecondsPassed attribute.

While the device is busy handling an RTC update event and the related background operation, the device may keep the fBusyRTC flag is set to one.

The device may perform operations in the background as a result of receiving RTC update. In order to allow optimal efficiency of these background operations, it is recommended that the host refrains from sending commands, other than Query Request to the device, and keep the device powered and in Active power mode as long as fBusyRTC flag is set to one. The device may consume active power during that time. Therefore, it would be desirable to update RTC in times where the system is usually idle and has no specific power limitations, e.g., at night time when battery is being charged.

### 13.4.9 Timestamp Information

Providing Timestamp information (qTimestamp) to a storage device could be useful for synchronizing device Error Log (retrieved through READ BUFFER command) and host error log.

This feature provides a mechanism for the host to provide a time tag (timestamp) to the device; the device may store this information in non-volatile memory and utilize for time tagging in the device error log when an event occurs.

In case the device is not in Active state, device may not know how much time elapsed since it was last active. Hence, it is recommended that the host set the device qTimestamp upon device power-on Reset / HW reset or when switching to Active state (using Start Stop Unit command).

# JEDEC Standard No. 220G
Page 384

## 13.4.10 Context Management

To better differentiate between large sequential operations and small random operations and to improve multitasking support, contexts can be associated with groups of read or write commands. Associating a group of commands with a shared context allows the device to optimize data handling.

A context can be seen as an active session, configured for a specific read/write pattern (e.g., sequential in some granularity). Multiple read or write commands are associated with this context to create some logical association between them, to allow device performance optimization. For example, a large sequential write pattern may have better performance by allowing the device to improve internal locality and reduce some overhead (e.g., if some large unit of data is allowed to be affected by a power failure as a whole while it is being written, all of the commands that fill this unit can work faster because they can reduce the overhead usually required to protect each write individually in case of a power failure). Furthermore, handling of multiple concurrent contexts allows the device to better recognize each of the write patterns when they are all mixed together.

The maximum number of contexts the device can support is reported in the bMaxContextIDNumber field of the Geometry Descriptor. When the host configures the device, it divides this number across the created LUs and writes the number of contexts to be supported in each LU to wContextCapabilities field in the Configuration Descriptor.

To use a context, an available Context ID shall be picked. Then, it shall be initialized by writing the configuration attribute of the relevant LU (wContextConf). Then, data can be read/written associated to the context by specifying the Context ID in GROUP NUMBER field of the CDB of the read/write command. When the context is no longer used, the configuration attribute (wContextConf) should be written as all '00' by the host to close the context. A context shall be closed prior to re-configuring it for another configuration/use.

No ContextID shall be open after power cycle.

### 13.4.10.1 Context Configuration

Before any context can be used it shall be configured.

Configuration is done by setting the context configuration attribute of the relevant LU (setting wContextConf with INDEX equal to LUN and SELECTOR equal to ContextID, SELECTOR '0' is reserved.). Then, all read commands or write commands that are associated with this ContextID shall be sent using GROUP NUMBER set to ContextID.

When the context is no longer needed, it should be closed by writing a zero byte to the configuration attribute.

# JEDEC Standard No. 220G
## Page 385

### 13.4.10.1 Context Configuration (cont'd)

To configure a specific ContextID for a specific LU, the following fields shall be written to the context configuration attribute of the specific context needed:

• **Activation and direction mode** (read-only, write-only or read/write)
  The direction indicates if all following accesses to this context would be either read-only, write-only or both read/write. Writing a non-zero direction to this field is the 'activation code' for the context. A zero in this field means a closed context which can no longer be addressed by its ID until re-configured.

• **Large Unit context flag**
  This indicates if the context is following Large Unit rules or not
  ○ If Large Unit context flag is set, then the Large Unit multiplier is used to specify the larger unit size.

• **Reliability mode**
  Controls how data written to a context should respond to interruptions.

### 13.4.10.2 Activation and Direction Mode

A non-zero context can be configured as a read-only context, a write-only context or a read/write context.

Any read command associated with any context to an address that is part of an active write-only context is not allowed, and may either fail the command or return dummy data.

Any write command associated with any context to an address that is part of an active read-only context is not allowed, and may either fail the command, ignore the data written or cause unexpected data to return in the read commands.

A context that is configured as read/write context may be read or written, as long as the writing follows the context rules.

NOTE read/write context may have reduced performance compared to read-only or write-only contexts.

### 13.4.10.3 Large-Unit Mode

The Large Unit is the smallest unit that can be used for large sequential read/write operations, in order to reduce internal overhead and improve performance.

Accessing a Large Unit (both read and write) shall:

• Use a ContextID configured to operate in Large Units.

• Always access a full Large Unit, in order and from beginning to end.
  ○ Multiple read/write commands with TRANSFER LENGTH smaller than the Large Unit size may be used to read or write the Large Unit. Read/write commands may be interleaved with other accesses and commands, as long as the specific Large Unit is being accessed with its own separate Context ID.
  ○ A Large Unit that is being written shall not be modified outside the scope of the context (e.g., no other writes from other contexts to the address range of the Large Unit shall be used, no erases/trims to that range, etc.).

# JEDEC Standard No. 220G
Page 386

## 13.4.10.3 Large Unit Mode (cont'd)

○ Different Large Units belonging to the same context may be located in non consecutive addresses on the media, as long as alignment is kept (a Large Unit shall be accessed in order from beginning to end, but only within the range of the specific Large Unit – the next Large Unit can be non-consecutive and even in a lower address).

• When writing a Large Unit context, data shall always be aligned and in multiples of bOptimalWriteBlockSize.

When writing a Large Unit context, the last Large Unit before closing the context may be partially written, as long as it is written from the beginning, in order and up to a specific point where it is closed. The rest of the Large Unit may be padded by the device to the end of the Large Unit with random data.

## 13.4.10.4 Reliability Mode

In case a write command to a Context ID is interrupted, the device behaves as if all the writes to the context from its configuration were written in one large write command.

In case of a power failure or software reset before closing an active context – even if not in the middle of a write command to the specific context (even if not in the middle of any command) – is considered as if the event occurred during writing the entire context.

A context behavior is determined as part of its configuration and is applied to all writes to this context until it is closed. Interruption during any of the writes may cause some of the data not to be fully programmed on the device. Still no partial Logical Block (of bLogicalBlockSize size) shall exist – any Logical Block written as part of the context shall contain either the new data written or its old data before the context was configured. The scope of data that may be affected by the interruption depends on the mode configured:

• For non-Large Unit contexts:
  ○ MODE0 – Normal mode – Any data written to the context from the time it was configured may be affected.
  ○ MODE1 – Non-Large Unit, reliable mode – Only data written by a specifically interrupted write command may be affected. Any previously completed write to the context shall not be changed because of any interruption.

• For Large Unit contexts:

  NOTE In the following cases, the unit N refers to the current Large Unit which is being written when interruption occurs, unit N-1 refers to the last Large Unit of the context that was written completely before the current one and unit N-2 and earlier are Large Units that were completed before the N-1 unit.

  ○ MODE0 – Normal mode – Any unit may be affected: Any data written to the context from the time it was configured may be affected.
  
  ○ MODE1 – Large Unit, unit-by-unit mode – Unit N may be affected, units N-1 and earlier are not: Any data written to a Large Unit context may affect the entire specific Large Unit accessed. Any previously completed Large Units in the context shall not be changed because of any interruption.
  
  ○ MODE2 – Large Unit, one-unit-tail mode – Unit N and N-1 may be affected, units N-2 and earlier are not: Any data written to a Large Unit context may affect the entire specific Large Unit accessed and the entire completed Large Unit that was accessed before the current one. Any other completed Large Units in the context shall not be changed because of any interruption.

# JEDEC Standard No. 220G
Page 387

## 13.4.10.4 Reliability Mode (cont'd)

In case the host sends a Task Management Request to abort a write command to a non-zero context or the write command fails with an error, the write may still be interrupted like any context-less write. In case these scenarios are interrupting a write to a Large Unit context, the device shall always stop writing on a bOptimalWriteBlockSize boundary.

## 13.4.10.5 Large-Unit Multiplier

In order to allow increased performance by parallelism, the device may allow reading or writing in multiples of the Large Unit granularity.

The granularity of Large Unit size is provided by bLargeUnitGranularity_M1 parameter in the Unit Descriptor as indicated in the following:

Large Unit size granularity = 1 Mbyte × (bLargeUnitGranularity_M1+1)

The device reports through a Unit Descriptor parameter (wContextCapabilities) the maximum multiplier that is supported by the logical unit.

The Large Unit size is configured setting the Large Unit Multiplier as defined in the following:

Large Unit size = Large Unit size granularity × Large Unit Multiplier =

= 1 Mbyte × (bLargeUnitGranularity_M1+1) × Large Unit Multiplier

For example, if bLargeUnitGranularity_M1 = 0 and Large Unit Multiplier = 2, then the Large Unit granularity is 1 Mbyte and the Large Unit size is 2 Mbyte.

## 13.4.11 System Data Tag Mechanism

The System Data Tag mechanism enables the host to notify the device when System Data is sent for storage (for instance file system metadata, operating system data, time stamps, configuration parameters, etc.). This notification (using GROUP NUMBER field in the CDB) would guide the device to handle the System Data optimally. By matching storage characteristics to the System Data characteristics the device could improve access rate of read and update operations and offer a more reliable and robust storage characteristics.

A UFS device has a limited amount of System Data area, a storage area with special characteristics which are tailored to the characteristics and needs of system data. When receiving System Data Tag notification along with the write command, the device will store the system data in the System Data area. In case the capacity available for storing System Data is completely consumed, the device will store the System Data in regular storage and the SYSPOOL_EXHAUSTED bit in the wExceptionEventStatus attribute shall be set to one. Additionally, if SYSPOOL_EVENT_EN bit is equal to one, then the EVENT_ALERT bit of Device Information field present in the RESPONSE UPIU will be forced to one

The SYSPOOL_EVENT_EN bit is included in the wExceptionEventControl attribute.

The host may free up System Data area by unmapping LBAs that were previously written with system data tag characteristics.

# JEDEC Standard No. 220G
Page 388

## 13.4.11 System Data Tag Mechanism (cont'd)

The device handles the System Data Tag mechanism in units of system data, the size of system data unit is device specific and can be retrieved reading the bSysDataTagUnitSize parameter in the Geometry Descriptor.

The total available capacity for System Data is indicated by the bSysDataTagResSize parameter of the Geometry Descriptor (see 14.1.4.4 for details).

When a host tags system data during a write operation, an entire storage area of bSysDataTagUnitSize size is handled by the device as system data area even if the size of the data being written is less than bSysDataTagUnitSize. In addition, any command (Write, Unmap, etc.) which updates a system data unit with data not tagged as System Data will change the entire system data unit storage characteristics to regular data. Therefore, it is recommended to handle system data in full units of bSysDataTagUnitSize size.

System Data areas are available only in Normal memory type logical units.

## 13.4.12 Exception Events Mechanism

The Exception Events Mechanism is used by the device to report occurrence of certain events to the host. It consists of three components EVENT_ALERT bit, the wExceptionEventStatus attribute and wExceptionEventControl attribute:

• A bit in wExceptionEventStatus attribute is assigned to each exception event. The device shall set the wExceptionEventStatus bits to one when the corresponding exception events are active, otherwise they shall be set to zero.

• A bit in wExceptionEventControl attribute is assigned to each exception event. EVENT_ALERT bit shall be set if there is at least one wExceptionEventStatus bit and wExceptionEventControl bit pair set to one. The setting of an wExceptionEventStatus bit to one will not force the EVENT_ALERT bit to one if the corresponding bit in the wExceptionEventControl is zero.

• The EVENT_ALERT is a bit in the Device Information field of the RESPONSE UPIU which is the logical OR of all bits in the wExceptionEventStatus masked by the bits of the wExceptionEventControl. The EVENT_ALERT bit is set to one when at least one bit in the wExceptionEventStatus is set and the corresponding wExceptionEventControl bit is one. The EVENT_ALERT is set to zero if all exception events that are enabled in the wExceptionEventControl are not active.

# JEDEC Standard No. 220G
Page 389

## 13.4.12 Exception Events Mechanism (cont'd)

The bits in the wExceptionEventStatus associated with those exception events are described as follows:

• **DYNCAP_NEEDED** – the device requests a Dynamic Capacity operation (see 13.4.6). This bit is cleared once a Dynamic Capacity operation has completed successfully, releasing the entire capacity that the device had requested to release.

• **SYSPOOL_EXHAUSTED** – the device ran out of resources to treat further host data as System Data (see 13.4.11). This bit is cleared once the host has turned enough memory areas that were previously handled as System data areas, to non-system data areas.

• **URGENT_BKOPS** – the device requests host attention for the level of need in Background Operations (see 13.4.4, Background Operations Model). This bit is cleared once bBackgroundOpStatus returns to 00h or 01h.

• **TOO_HIGH_TEMP** – the device requests that the host takes action to reduce the device's Tcase temperature.

• **TOO_LOW_TEMP** – the device requests that the host takes action to increase the device's Tcase temperature.

• **PERFORMANCE_THROTTLING** – the device is operating at reduced performance. The host may read bThrottlingStatus to determine the cause of reduced performance.

• **WRITEBOOSTER_FLUSH_NEEDED** – Buffer for WriteBooster needs to be flushed. The host is expected to issue a flush command by setting fWriteBoosterBufferFlushEn as '1'.

• **DEVICE_LEVEL_EXCEPTION_OCCURRED** – The device requests that the host takes action to examine the device level exception occurrence as described in 13.4.12.1. This bit is cleared once the attribute qDeviceLevelExceptionID is read.

• **WRITEBOOSTER_RESIZE_HINT** – the device recommends to increase or decrease the WriteBooster Buffer size. The host may read bWriteBoosterBufferResizeHint to identify hint information about which type of resize is recommended, then enable decrease or increase the WriteBooster Buffer size by setting the bWriteBoosterBufferResizeEn attribute.

• **PINNED_WRITEBOOSTER_FULL** – the device informs the host that the allocated buffer for pinned data in WriteBooster is full, so further pinned data may be written to normal storage.

• **HEALTH_CRITICAL** – Notify the host of a critical health condition. Following fields may change to reflect critical health condition and host may read following fields to get detailed information: bPreEOLInfo, bDeviceLifeTimeEstA, bDeviceLifeTimeEstB, bWriteBoosterBufferLifeTimeEst, bRPMBLifeTimeEst. Clear condition of the bit is met when host reads wExceptionEventStatus, which cause device to clear the HEALTH_CRITICAL.

In the Device Information field of the RESPONSE UPIU, the device will only indicate the events that were enabled by the host through writing to the wExceptionEventControl attribute. The event bits in the wExceptionEventStatus attribute and in the Device Information field of the Response UPIU are cleared by the device when the clear conditions are met.

# 13.4.12.1 Device Level Exception Event Notification

This feature provides a notification to the host if a device-level exception occurs.

The device issues the DEVICE_LEVEL_EXCEPTION_OCCURED exception event using the Exception Event Mechanism defined in 13.4.12 to inform the host of a device level exception event occurrence.

The host may read the device qDeviceLevelExceptionID attribute to discover the detailed exception type for the device level exception event. On read, the qDeviceLevelExceptionID attribute shall be reset to 0. For a detailed definition of the qDeviceLevelExceptionID attribute's values, refer to the device manufacturer datasheet.

This feature is optional. The device indicates whether the feature is supported or not by reading dExtendedUFSFeaturesSupport in the Device Descriptor.

---

**Document Information:**
- JEDEC Standard No. 220G
- Page 390

# 13.4.13 Queue Depth Definition

Each logical unit is responsible for managing its own task set. Independently from the task set, the resources used for queueing tasks may either be statically allocated to each LU, so that the LU is capable of queueing new tasks up to a certain depth, or be shared by all LUs, so that queueing resources are dynamically allocated to LUs, depending on tasks received.

A device may implement one of the two queueing architectures described above. The device informs the host software on the policy implemented using read only parameters in the Device Descriptor and the Unit Descriptors.

The depth of a queue is defined as the number of pending commands which can be stored in the queue.

## 13.4.13.1 Shared Queue

In the shared queue architecture, the device has a fixed-depth queue where tasks are queued as they are received, regardless of their LUN designation.

When a COMMAND UPIU is received, resources are allocated from the shared queue and the command is accounted towards the queue depth limit. The host is expected to track the queue depth and not issue more commands than can be stored in the queue. If queue resources are unavailable, the device shall return a response with TASK SET FULL status.

QUERY REQUEST UPIUs, NOP OUT UPIUs, and TASK MANAGEMENT REQUEST UPIUs are not stored in the shared queue.

When this queueing architecture is implemented, the parameter bQueueDepth in the Device Descriptor shall indicate the depth of the queue. The value of bQueueDepth shall be equal to, or larger than, 1. The bLUQueueDepth parameters in all Unit Descriptors shall all be equal to 0, while bLUQueueDepth in RPMB Descriptor may be 0 or equal to the number of enabled RPMB regions (see 13.4.13.3).

## 13.4.13.2 Per-Logical Unit Queues

In the per-LU queueing architecture, the device implements separate fixed-depth queues, one queue for each LU, or, in other words, allocates a fixed number of queueing resources for each LU.

When a COMMAND UPIU is received, resources are allocated from the queue associated with its logical unit, as indicated by the LUN field in the UPIU Header. The command is accounted towards the depth limit of the respective queue. The host is expected to track the queue depths and not issue more commands than can be stored in their designated queue. If resources are unavailable for the designated LU, the device shall return a response with TASK SET FULL status (even if queueing resources are available for other LUs). QUERY REQUEST UPIUs, NOP OUT UPIUs, and TASK MANAGEMENT REQUEST UPIUs are not stored in the LU queues.

When this queueing architecture is implemented, the bLUQueueDepth parameters in Unit Descriptors shall indicate the depth of the queue of each logical unit. If a logical unit is enabled, the value of bLUQueueDepth in its Unit Descriptor shall be equal to, or larger than, 1.

bQueueDepth parameter in the Device Descriptor shall be equal to 0.

# JEDEC Standard No. 220G
## Page 392

### 13.4.12.2 Per Logical Unit Queues (cont'd)

**NOTE** For backward compatibility with previous revisions of the standard, if bLUQueueDepth for an LU is 0, and bQueueDepth is also 0, the queue depth should be treated by the host as unknown. The host is expected to infer the queue depth using software algorithms.

### 13.4.13.3 RPMB Well Known Logical Unit Queue

RPMB logical unit may use shared queue resources or may use its own separate queue, as implemented by the device manufacturer.

If the RPMB logical unit uses the shared queue resources, its bLUQueueDepth parameter shall be equal to 0. When a COMMAND UPIU is received, resources are allocated from the shared queue, and the command is accounted towards the queue depth limit. The host is expected to track the queue depth and not issue more commands than can be stored in the queue. If queue resources are unavailable, the device shall return a response with TASK SET FULL status.

If the RPMB logical unit uses a separate queue, its queue depth shall be equal to the value of bLUQueueDepth, except for 0. The host is expected to not issue more than one command to an RPMB region at any given time. Therefore, if more than the number of commands specified by bLUQueueDepth is issued to the RPMB LU, the device shall return a response with TASK SET FULL status.

It should be noted that, unlike other LUs, it is permitted that RPMB LU has a fixed depth queue while other LUs use a shared queue.

### 13.4.14 Device Life Span Mode

The intent of this mode is to improve the device life span by increasing the device endurance. Devices use mechanism like wear leveling etc. for improving the device life time which is limited to P/E cycle count given by a memory vendor. In this mode, device may use technology like lower programming voltage etc. for operations to increase the P/E cycle count and result in improving the device life.

Read and write operation performance in UFS are very high. However maximum operation speed is not required always e.g., when user is sleeping, device is in screen-off mode, downloading large size files/video and so on. During such scenarios, UFS host may indicate to device to use technology like lower programming voltage etc. for operations by enabling fDeviceLifeSpanModeEn flag. On disabling this flag, device uses normal voltage for operations. It is expected that the device will respond normally as soon as the flag is disabled.

There may be performance degradation in this mode, therefore fDeviceLifeSpanModeEn should be set only when the device is not actively used.

The improvement of device life span is dependent on device implementation.

# JEDEC Standard No. 220G
Page 393

## 13.4.14.1 Implementation

**Device Life Span Mode Enable**
fDeviceLifeSpanModeEn is the Flag to be used to enable or disable the execution of technology like lower programming voltage etc. for operations.

0 = Device Life Span Mode is disabled.

1 = Device Life Span Mode is enabled.

The default value of this flag is zero. Host can enable this flag depending on scenarios like screen-off, downloading large files etc.

## 13.4.15 Refresh Operation

In order to improve reliability (e.g., retention), the device data can be refreshed at the physical block level by erasing and re-programming its physical blocks.

The refresh operation mechanism provides a better capability for the host to control refresh operations explicitly with the refresh configuration, initiation, interruption, and progress management.

This feature is optional. The device indicates whether the feature is supported or not in bUFSFeaturesSupport parameter in Device descriptor. It aims at addressing reliability requirements.

It depends on device implementations how the reliability improves on this feature.

### 13.4.15.1 Configuration

#### 13.4.15.1.1 Refresh Method

From refresh perspective, there are three types of blocks:
- Type 1: Physical blocks that don't contain data (i.e., unmapped physical blocks). Blocks of this type will not be refreshed.

- Type 2: Physical blocks that contain data but the device doesn't consider them to be in need of refresh

- Type 3: Physical blocks that contain data and the device considers them to be in need of refresh

The device shall support two refresh methods: Manual-Force or Manual-Selective.
- Manual-Force
  The device is obliged to refresh the amount of physical blocks as requested by the host, regardless whether these blocks need refresh or not. Only type 2 and type 3 blocks will be refreshed.

- Manual-Selective
  The device only refreshes the physical blocks that it considers to be in need of refresh.Specifically these are blocks of type 3.

The attribute bRefreshMethod needs to be initially set to either Manual-Force or Manual-Selective mode before initiating a device refresh operation.

# JEDEC Standard No. 220G
Page 394

## 13.4.15.1.1 Refresh Method (cont'd)

Upon the host request, the device shall perform a refresh operation following the specified method (Manual-Force or Manual-Selective). In addition to the host initiated refresh modes, the device may implement an additional automatic refresh mode which is transparent to the host.

## 13.4.15.1.2 Refresh Unit

The host may configure bRefreshUnit attribute to specify the amount of physical blocks to be refreshed upon a single refresh request.

The device refreshes the amount of physical blocks specified by bRefreshUnit starting from the first physical block. In order to refresh the whole device (i.e., all physical blocks), the host has to send the refresh command one (bRefreshUnit = 01h: 100%) or more times (bRefreshUnit = 00h: Minimum refresh capability of Device).

In any case the device stops refreshing when dRefreshProgress reaches 100000 (100.000%).

## 13.4.15.1.3 Refresh Frequency

The device provides the refresh frequency indicator (bRefreshFreq attribute) in unit of month. The host should make sure that the whole device has been refreshed within the time period specified by the bRefreshFreq attribute. dRefreshTotalCount is incremented to indicate that the whole device refresh is completed.

Since the required refresh frequency depends on the use condition (e.g., temperature), bRefreshFreq attribute may be configured by OEM to let the host know how often it needs to send refresh requests.

## 13.4.15.2 Initiation and Interruption

The host initiates a refresh operation by setting fRefreshEnable to 1b and interrupts it by clearing fRefreshEnable to 0b. After interruption, fRefreshEnable can be also used to resume the refresh operation where it last stopped by setting it to 1b.

bRefreshStatus attribute provides information about a single refresh operation status.

The host should send a query request to set fRefreshEnable flag to one only if command queues are empty. A query request to set fRefreshEnable flag which is processed when device command queues are not empty may fail. If the request fails,, Query Response field in the QUERY RESPONSE UPIU shall be set to FFh ("General Failure"), the refresh operation shall not start, and the bRefreshStatus shall be set to 04h.

If a refresh operation is in progress, any request, other than Query Request (READ) and the refresh interruption described above, will fail.

Host should check the Device lifetime remained by reading bDeviceLifeTimeEst of Device Health Descriptor. Host should consider more carefully whether refresh operation will be issued or not since the refresh operation is consuming remained life time of device.

# 13.4.15.3 Progress Management

The device shall indicate the refresh progress with respect to its entire physical blocks. The two parameters are defined as progress monitors in Device Health Descriptor.

- **dRefreshTotalCount**  
  Indicate how many times the device complete refresh for the entire device. Incremented by 1 when dRefreshProgress reach 100%.

- **dRefreshProgress**  
  Indicate the refresh progress with respect to its entire physical blocks in %.

They work both in Manual-Force and Manual-Selective methods, and will not be changed by any operation (e.g., WRITE(10)) other than refresh operations.

It is host responsibility to keep pace of sending refresh requests based on:
- Refresh Frequency (bRefreshFreq)
- Refresh Unit (bRefreshUnit)
- Progress monitor (dRefreshProgress, dRefreshTotalCount)

For example, the host should send refresh request 1000 times during 6 month if
- bRefreshFreq = 06h (6 month)
- bRefreshUnit = 00h (e.g., 0.100% as Minimum refresh capability of Device)

bRefreshMethod (00h: Manual-Force, 01h: Manual-Selective) does not affect on how the progress monitor grows. Regardless of the actually refreshed blocks, dRefreshProgress is increased by the same amount. In particular this means that even if type 1 blocks (see 13.4.15.1.1) are not refreshed in Manual-Force mode and neither type 1 nor type 2 blocks are refreshed in Manual-Selective mode, dRefreshProgress is increased by the same amount.

When bRefreshMethod = 02h (Manual-Selective), even though some of physical blocks are not refreshed by device choice, dRefreshProgress should be incremented by the same amount.

For example, dRefreshProgress will be increased by 2% both in Manual-Force and Manual-Selective mode in the following conditions.

• Device has 100 physical blocks in total
• bRefreshUnit is set to 00h (e.g., 2% as Minimum refresh capability of Device)
• dRefreshProgress initially indicates 0%
• 1st physical block is empty
• 2nd physical block has data but does not need refresh

**Case 1: bRefreshMethod = Manual-Force**  
Upon a single refresh command completion, dRefreshProgress will be increased by 2% even though the device ignores 1st physical block and refreshes 2nd physical block.

**Case 2: bRefreshMethod = Manual-Selective**  
Upon a single refresh command completion, dRefreshProgress will be increased by 2% even though the device ignores both 1st and 2nd physical blocks.

---
*JEDEC Standard No. 220G  
Page 395*

# JEDEC Standard No. 220G
Page 396

## 13.4.16 Temperature Event Notification

The purpose of this feature is to provide notification to host in advance when UFS device temperature approaches defined upper and lower boundary of temperature. This feature is optional. Two bits in bUFSFeaturesSupport parameter specify the temperature event notification support (see 14.1.4.2)

When temperature of device is too high or too low that host's awareness is needed, device shall notify this situation to host by using wExceptionEventStatus Attribute in exception event mechanism defined in 13.4.12. When TOO_HIGH_TEMP in wExceptionEventStatus is raised, it is recommended for host to do throttling or other cooling activities for lowering device Tcase temperature. When TOO_LOW_TEMP in wExceptionEventStatus is raised, it is recommended for host to do activities for increasing device's Tcase temperature.

When this temperature alarming is raised, host may want to know temperature reported by device even though UFS device only could give rough temperature. In this purpose, device case rough temperature shall be provided through bDeviceCaseRoughTemperature attribute. Since the temperature sensor inside semiconductor device is not expected enough accurate, this temperature information shown in bDeviceCaseRoughTemperature is to provide the rough temperature range only. And there could some variation depending on location of measurement also, host should assume that this temperature information from device have around ± 10 °C error range. Therefore, this temperature information should be referred by host only as rough device case temperature.

To give a temperature boundary information for too high or too low temperature alarming, bDeviceTooHighTempBoundary and bDeviceTooLowTempBoundary attribute Is defined. The temperature alarming status held in wExceptionEventStatus shall be automatically cleared by device when device case temperature is going within boundary temperature range.

## 13.4.17 Performance Throttling Event Notification

The purpose of this feature is to provide notification to the host if the device is limiting performance. If the device needs to reduce performance, the host will be notified through the Exception Event Mechanism defined in 13.4.11. While the PERFORMANCE_THROTTLING exception event bit is set, the host should expect reduced performance from the device.

The host may read the device bThrottlingStatus attribute to discover why the device is operating at lower performance. Bits in bThrottlingStatus attribute will remain set while the condition exists.

This feature is optional. The device indicates whether the feature is supported or not by dExtendedUFSFeaturesSupport parameter in Device Descriptor.

How much the performance of the UFS device is reduced when a performance throttling event is notified depends on the device implementation.

# 13.4.18 WriteBooster

## 13.4.18.1 Overview

The write performance of TLC NAND is considerably lower than SLC NAND because the logically defined TLC bits require more programming steps and have higher error correction probability. To improve the write performance, part of the TLC NAND (normal storage) is configured as SLC NAND and used as write buffer, temporarily or permanently. Using SLC NAND as a WriteBooster Buffer enables the write request to be processed with lower latency and improves the overall write performance. Some portions of TLC NAND allocated for the user area are assigned as the WriteBooster Buffer. The data written in the WriteBooster Buffer can be flushed into TLC NAND storage by an explicit host command or implicitly while in hibernate (HIBERN8) state. Technologies other than TLC and SLC NAND may be used as normal storage and WriteBooster Buffer.

[THIS IS FIGURE: A flow diagram showing the WriteBooster concept. It shows a Host on the left connecting to a WriteBooster Buffer (SLC) in the middle, which then connects to Normal Storage (e.g. TLC) on the right. The flow shows: (1) Write data in WriteBooster mode from Host to WriteBooster Buffer, (2) Faster response back to Host, and (3) Flush from WriteBooster Buffer to Normal Storage.]

**Figure 13.7 — Concept of WriteBooster Feature**

Bit[8] of dExtendedUFSFeaturesSupport indicates if the device supports the WriteBooster feature.

There are two WriteBooster mode of operations: "LU dedicated buffer" mode and "shared buffer" mode. In the "LU dedicated buffer" mode, the WriteBooster Buffer is dedicated to a logical unit, while in the "shared buffer" mode all logical units share the same WriteBooster Buffer except well-known logical units. bSupportedWriteBoosterBufferTypes indicates which modes are supported by the device. In both WriteBooster mode of operations, the WriteBooster Buffer size is configurable.

There are two user space configuration modes: "user space reduction" and "preserve user space". With "user space reduction", the WriteBooster Buffer reduces the total configurable user space; while with "preserve user space", the total space is not reduced.

The WriteBooster feature is enabled when fWriteBoosterEn flag is set to one.

bAvailableWriteBoosterBufferSize attribute indicates the available space in the WriteBooster Buffer. An exception event is triggered when there is the need to flush the WriteBooster Buffer: bit[5] of wExceptionEventStatus is set to indicate that data in WriteBooster Buffer should be flushed to normal storage.

There are two flags for controlling the WriteBooster Buffer flush operation. fWriteBoosterBufferFlushEn flag enables the flush operation: when it is set to one, the device shall flush the WriteBooster Buffer. fWriteBoosterBufferFlushDuringHibernate enables the flush operation during hibernate: the device initiates a WriteBooster Buffer flush operation whenever the link enters in the hibernate state.

---

*JEDEC Standard No. 220G*  
*Page 397*

# JEDEC Standard No. 220G
Page 398

## 13.4.18.1 Overview (cont'd)

bWriteBoosterBufferFlushStatus attribute provides the flush operation status, while bWriteBoosterBufferLifeTimeEst attribute indicates the estimated lifetime of the WriteBooster Buffer.

## 13.4.18.2 WriteBooster Configuration

Bit[8] of dExtendedUFSFeaturesSupport indicates if the device supports the WriteBooster feature. If the device does not support this feature, a query request that attempts to set a WriteBooster parameter in a Configuration Descriptor to a value different from zero shall fail, and the Query Response field in QUERY RESPONSE UPIU shall be set to "General Failure".

The WriteBooster Buffer can be configured in "LU dedicated buffer" mode or "shared buffer" mode according to the device capability. bSupportedWriteBoosterBufferTypes indicates which modes are supported by the device.

If bWriteBoosterBufferPreserveUserSpaceEn is set to 00h, the WriteBooster Buffer reduces the total user space that can be configured at provisioning. The amount of the reduction can calculated multiplying the WriteBooster Buffer size by the value indicated by bWriteBoosterBufferCapAdjFac. For example, if bWriteBoosterBufferCapAdjFac value for a TLC NAND storage device with a SLC NAND WriteBooster Buffer is 3; therefore, the total user capacity that can be configured is reduced by 3 × WriteBoosterBufferCapacity.

Setting bWriteBoosterBufferPreserveUserSpaceEn to 01h avoids the reduction of the total user space that can be configured at provisioning, but it may result in lower performance, see 13.4.18.5.

### LU dedicated buffer mode

If the device supports the "LU dedicated buffer" mode, this mode is configured by setting bWriteBoosterBufferType to 00h. The logical unit WriteBooster Buffer size is configured by setting the dLUNumWriteBoosterBufferAllocUnits field of the related Unit Descriptor. Only a value greater than zero enables the WriteBooster feature in the logical unit. When bConfigDescrLock attribute is set to 01h, logical unit configuration can no longer be changed.

The maximum number of supported WriteBooster Buffers is defined in the bDeviceMaxWriteBoosterLUs parameter of the Geometry Descriptor. bDeviceMaxWriteBoosterLUs is 01h, therefore the WriteBooster Buffer can be configured in only one logical unit.

Figure 13.8 shows an example of device configuration with a 2 GB WriteBooster Buffer.

[**Figure 13.8**: Diagram showing LU dedicated buffer mode configuration with 8 logical units (LU #0 through LU #7) arranged horizontally. LU #1 contains a green box labeled "Write Booster Buffer (2 GB)". Below the diagram is a configuration example showing:
- bWriteBoosterBufferType: '0' (LU dedicated type)
- LU #1: dLUNumWriteBoosterBufferAllocUnit: 2 GB
- Other LU's dLUNumWriteBoosterBufferAllocUnit: 0]

**Figure 13.8 — Example of "LU Dedicated Buffer" Mode Configuration**

# 13.4.18.2 WriteBooster Configuration (cont'd)

The WriteBooster Buffer is available only for the logical units from 0 to 7 which are configured as "normal memory type" (bMemoryType = 00h) and "not Boot well known logical unit" (bBootLunID = 00h), otherwise the Query Request shall fail and the Query Response field shall be set to "General Failure".

**Shared buffer mode**
If the device supports the "shared buffer" mode, this mode is configured by setting bWriteBoosterBufferType to 01h.

The WriteBooster Buffer size is configured by setting the dNumSharedWriteBoosterBufferAllocUnits field of the Device Descriptor. NOTE1 Number of supported logical unit is indicated by bMaxNumberLU.

Figure 13.9 shows an example of device configuration with a 2 GB WriteBooster Buffer.

[Figure 13.9 shows a diagram with boxes representing logical units LU #0 through LU #31, with LU #5 and additional units shown with "...". All logical units are connected by lines pointing down to a green box labeled "Shared Write Booster Buffer (2 GB)". To the right is a configuration example showing:
- bWriteBoosterBufferType: '1' (shared type)
- dNumSharedWriteBoosterBufferAllocUnits: 2 GB]

NOTE1 Number of supported logical unit is indicated by bMaxNumberLU.

**Figure 13.9 — Example of "shared buffer" Mode Configuration**

Note that, if bWriteBoosterBufferType is set to 01h but dNumSharedWriteBoosterBufferAllocUnits is set to zero, the WriteBooster feature is disabled.

## 13.4.18.3 Writing Data to WriteBooster Buffer

If the fWriteBoosterEn flag is set to zero, data written to any logical unit is written in normal storage.

If the fWriteBoosterEn flag is set to one and the device is configured in "shared buffer" mode, data written to any logical unit is written in the shared WriteBooster Buffer.

If the fWriteBoosterEn flag is set to one and the device is configured in "LU dedicated buffer" mode, data written to the logical unit configured to use a dedicated buffer is written in the logical unit WriteBooster Buffer. Data written to any logical unit not configured to use a dedicated buffer is written in normal storage.

Writes to the WriteBooster Buffer may decrease the lifetime and the availability of the WriteBooster Buffer.

In the "LU dedicated buffer" mode, the device may write data from other LUs to the WriteBooster Buffer in case there are multiple pending commands while fWriteBoosterEn is set to one.

---
JEDEC Standard No. 220G
Page 399

# JEDEC Standard No. 220G
## Page 400

### 13.4.18.3 Writing Data to WriteBooster Buffer (cont'd)

Whenever the endurance of the WriteBooster Buffer is consumed completely, a write command is processed as if WriteBooster feature was disabled. Therefore, it is recommended to set fWriteBoosterEn to one, only when WriteBooster performance is needed, so that WriteBooster feature can be used for a longer time.

In the shared buffer configuration, the data that may not need the performance of WriteBooster will be written to the WriteBooster Buffer when fWriteBoosterEn is one, there is higher probability to fill the WriteBooster Buffer and consume its endurance earlier.

If there is no available buffer, write data in WriteBooster mode will be stored in normal storage with normal write performance. The host can identify the available WriteBooster Buffer size by referring to the bAvailableWriteBoosterBufferSize attribute. This available buffer size is decreased by the WriteBooster operation and increased by the WriteBooster Buffer flush operation. The available buffer size can be increased by UNMAP commands.

The WriteBooster Buffer lifetime is indicated by the bWriteBoosterBufferLifeTimeEst attribute. If the value of bWriteBoosterBufferLifeTimeEst is equal to 0Bh (Exceed its maximum estimated WriteBooster Buffer lifetime), a write command shall be processed as if the WriteBooster feature was disabled.

### 13.4.18.4 Flushing WriteBooster Buffer

When the entire buffer for WriteBooster is consumed, data will be written in normal storage instead of in the WriteBooster Buffer. The device informs the host when the WriteBooster Buffer is full or near full with the exception event WRITEBOOSTER_FLUSH_NEEDED, see 13.4.12.

The WRITEBOOSTER_FLUSH_NEEDED event mechanism is enabled by setting the WRITEBOOSTER_EVENT_EN bit of the wExceptionEventControl attribute.

There are two methods for flushing data from the WriteBooster Buffer to the normal storage: one is using an explicit flush command, the other enabling the flushing during link hibernate state. If the fWriteBoosterBufferFlushEn flag is set to one, the device shall flush the data stored in the WriteBooster Buffer to the normal storage. If fWriteBoosterBufferFlushDuringHibernate is set to one, the device flushes the WriteBooster Buffer data automatically whenever the link enters the hibernate (HIBERN8) state.

The time needed to flush the WriteBooster Buffer depends on the amount of data to be flushed. The bWriteBoosterBufferFlushStatus attribute indicates the status of the WriteBooster flush operation. The device shall execute the WriteBooster flush operation only when the command queue is empty. If the device receives a command while flushing the WriteBooster Buffer, the device may suspend the flush operation to expedite the processing of that command. Note that bWriteBoosterBufferFlushStatus will still indicate "Flush operation in progress" (01b) even if it has been temporarily suspended. After completing the host command, the device will resume flushing the data from the WriteBooster Buffer automatically. While the flushing operation is in progress, the device is in Active power mode.

The device shall stop the flushing operation if both fWriteBoosterBufferFlushEn and fWriteBoosterBufferFlushDuringHibernate are set to zero.

# 13.4.18.5 User Space Modes

There are two user space configuration modes: "user space reduction" and "preserve user space". With the "user space reduction", the WriteBooster Buffer reduces the total configurable user space. While with the "preserve user space", the total space is not reduced. However, the physical storage allocation may be smaller than total capacity of all logical units, since part of the physical storage is used for the WriteBooster Buffer.

When the physical storage allocated for the logical units is fully used, the device will start using the physical storage allocated for the WriteBooster Buffer. Therefore, the WriteBooster Buffer size may be less than what was initially configured. The current size of the WriteBooster Buffer can be discovered by reading the dCurrentWriteBoosterBufferSize attribute. Approximate available space in the WriteBooster Buffer can be calculated by multiplying the value of bAvailableWriteBoosterBufferSize (percentage of available WriteBooster Buffer) by the value of dCurrentWriteBoosterBufferSize (current WriteBooster Buffer size).

The bSupportedWriteBoosterBufferUserSpaceReductionTypes parameter of the Geometry Descriptor indicates which options are supported. Setting the bWriteBoosterBufferPreserveUserSpaceEn parameter of the Device Descriptor to 01h enables "preserve user space" mode.

The disadvantage of the "preserve user space" mode is that there could be performance degradation when the physical storage used for the WriteBooster Buffer is returned to user space, since the device may adjust internal data structures as well as flush existing WriteBooster Buffer data. If the free storage is not enough, the device may restore its decreased WriteBooster Buffer size from available physical storage. If the remaining storage is repeatedly increased and decreased, the WriteBooster Buffer could be repeatedly built from and returned to the user storage space and performance degradation may occur.

The amount of performance degradation due to returning the storage used for WriteBooster Buffer to user storage space is device specific. This is because the condition for migration between user space and the WriteBooster Buffer depends on device capacity and vendor's migration policy, which includes the granularity and frequency of migration, what percentage of free user space remains from which the migration starts, etc. For more details, see the device datasheet.

---

JEDEC Standard No. 220G  
Page 401

# 13.4.18.6 WriteBooster Buffer Resize

In preserve user space mode, without host involvement, the device may move allocation units between normal memory and WriteBooster Buffer based on the device's physical utilization. However, during these allocation unit changes, READ and WRITE commands may experience performance degradation. The host may initiate a Resize operation to prevent performance degradation. The device provides a hint to the host to recommend Resize operations, but the host selects the timing and type of Resize operations to be performed.

WriteBooster Buffer size can be decreased or increased during runtime when the host initiates a WriteBooster Resize operation. This feature is supported only in preserve user space mode. If the WriteBooster Resize operation is initiated in user space reduction mode, Query Response shall return "General Failure"

As shown in Figure 13.10, the host initiates a Resize operation to increase or decrease the WriteBooster Buffer Size based on the information provided in the device's bWriteBoosterBufferResizeHint attribute. The host initiates a Resize operation by issuing a QUERY REQUEST UPIU with a write request for the bWriteBoosterBufferResizeEn attribute.

When there is a recommendation about resize for the WriteBooster Buffer, the device informs the host by the WRITEBOOSTER_RESIZE_HINT exception mechanism. It is enabled by setting the WRITEBOOSTER_RESIZE_HINT_EN bit of the wExceptionEventControl attribute.

The device may adjust the WriteBooster Buffer size when the command queue is empty. When size adjustment is completed, the device updates dCurrentWriteBoosterBufferSize. However, if the WriteBooster Buffer size cannot be increased or decreased due to device internal status, the WriteBooster Buffer size is not changed.

[Figure 13.10 - (Example) Initiating a WriteBooster Buffer Resize Operation: This is a sequence diagram showing communication between UFS Host (blue box) and UFS Device (orange box). The diagram shows the following sequence:

1. Query Request (READ bWriteBoosterBufferResizeHint) from Host to Device
2. Query Response (bWriteBoosterBufferResizeHint) from Device to Host
   - Annotation: "Host can check the device's recommendation about WriteBooster buffer resize. (decrease, increase, or keep the current WriteBooster buffer size.)"
3. Query Request (WRITE bWriteBoosterBufferResizeEn) from Host to Device
4. Query Response from Device to Host
   - Annotation: "Host can enable increase or decrease of the WriteBooster Buffer Size referring to the value of the bWriteBoosterBufferResizeHint."
5. A gray box at the bottom states "Resizing the WriteBooster Buffer is performed."]

---

JEDEC Standard No. 220G  
Page 402

# JEDEC Standard No. 220G
Page 403

## 13.4.18.6 WriteBooster Buffer Resize (cont'd)

As shown in Figure 13.11, the host can check the progress of the WriteBooster Buffer Resize operation by reading the bWriteBoosterBufferResizeStatus attribute. While a WriteBooster Resize is in progress, any QUERY REQUEST attempting to write bWriteBoosterBufferResizeEn shall not change the value nor interfere with the resize in progress and the device shall reply with a QUERY RESPONSE with Query Response of Success.

The amount of increase or decrease in WriteBooster Buffer is determined by the device. The host can check the updated WriteBooster Buffer size after completing those resize operation by reading the dCurrentWriteBoosterBufferSize attribute. The WriteBooster Buffer size shall not exceed the size indicated by the dNumSharedWriteBoosterBufferAllocUnits or dLUNumWriteBoosterBufferAllocUnits descriptor.

[THIS IS FIGURE: A sequence diagram showing communication between UFS Host and UFS Device. The diagram illustrates:

1. Query Request (READ bWriteBoosterBufferResizeStatus) from UFS Host to UFS Device
2. Query Response (bWriteBoosterBufferResizeStatus) from UFS Device to UFS Host
   - Note: "Host can check the status of WriteBooster Buffer Resize operation by reading bWriteBoosterBufferResizeStatus attribute."
3. Query Request (READ dCurrentWriteBoosterBufferSize) from UFS Host to UFS Device
4. Query Response (dCurrentWriteBoosterBufferSize) from UFS Device to UFS Host
   - Note: "Host can check the updated WriteBooster Buffer size by reading dCurrentWriteBoosterBufferSize attribute."]

**Figure 13.11 – (Example) Checking the Status of Resize Operation and Updated WriteBooster Buffer Size**

## 13.4.18.7 Partial Flush Modes of WriteBooster Buffer

If the data is expected to be accessed soon or frequently, it is better to keep it in the WriteBooster Buffer for as long as possible in consideration of overall performance.

Using the partial flush mode, the host can indicate the data which is not to be moved out from the WriteBooster Buffer. The overall performance can be improved since higher speed access for those data can be continued.

There are two partial flush modes selected by the bWriteBoosterBufferPartialFlushMode attribute:

• FIFO(First-In First-Out) mode

• Pinned mode ( supported only in preserved user space option of WriteBooster )

# JEDEC Standard No. 220G
Page 404

## 13.4.18.7.1 FIFO Partial Flush Mode

If bWriteBoosterBufferPartialFlushMode is 0x1, then FIFO mode partial flush mode is selected.

In the FIFO partial flush mode, the data written later are excluded from the WriteBooster flush operation, and the dCurrentFIFOSizeForWriteBoosterPartialFlushMode indicates the data size to be excluded from the WriteBooster flush operation.

The dMaxFIFOSizeForWriteBoosterPartialFlushMode value shall not be set to a value greater than dNumSharedWriteBoosterBufferAllocUnits or dLUNumWriteBoosterBufferAllocUnits. If the host attempts to write a value higher than what indicated by dNumSharedWriteBoosterBufferAllocUnits or dLUNumWriteBoosterBufferAllocUnits, the value shall not be changed and the QUERY RESPONSE UPIU shall have Query Response field set to "Invalid VALUE".

## 13.4.18.7.2 Pinned Partial Flush Mode

If bWriteBoosterBufferPartialFlushMode is 0x2, then Pinned mode partial flush mode is selected.

In the Pinned Partial flush mode, the data of WRITE command with GROUP NUMBER set to 18h is intended to be written to the Pinned WriteBooster Buffer, and the data written in the Pinned WriteBooster Buffer is excluded from WriteBooster flush operation.

The Pinned WriteBooster Buffer size is indicated by dPinnedWriteBoosterBufferNumAllocUnits.

The minimum size recommendation for Non-Pinned WriteBooster Buffer area in Pinned Partial Flush Mode is indicated by dNonPinnedWriteBoosterBufferMinNumAllocUnits. Even if the WriteBooster buffer size is reduced, the size of the non-pinned area is recommended to be maintained larger than dNonPinnedWriteBoosterBufferMinNumAllocUnits size if possible. For example, if only the non-pinned buffer of this size remains in the device and the WriteBooster buffer size needs to be further reduced, the pinned data area is returned first to maintain the non-pinned WB buffer size indicated by dNonPinnedWriteBoosterBufferMinNumAllocUnits as long as possible.

The sum of dPinnedWriteBoosterBufferNumAllocUnits value and dNonPinnedWriteBoosterBufferMinNumAllocUnits value shall not be set to a value greater than dNumSharedWriteBoosterBufferAllocUnits or dLUNumWriteBoosterBufferAllocUnits. If the host attempts to write a value higher than what indicated by dNumSharedWriteBoosterBufferAllocUnits or dLUNumWriteBoosterBufferAllocUnits, the value shall not be changed and the QUERY RESPONSE UPIU shall have Query Response field set to "Invalid VALUE".

When the WriteBooster Buffer size decrease, the Pinned WriteBooster Buffer size can be decreased less than the size indicated by the dPinnedWriteBoosterBufferNumAllocUnits. Therefore, the host can check the currently allocated size for pinned WriteBooster Buffer by reading the dPinnedWriteBoosterBufferCurrentAllocUnits attribute. The currently available portion in the currently allocated Pinned WriteBooster Buffer is indicated by the bPinnedWriteBoosterBufferAvailablePercentage attribute.

If the Pinned WriteBooster Buffer is not available( i.e full or not configured), even data of WRITE command with GROUP NUMBER set to 18h can be written to the Non-Pinned WriteBooster Buffer area, or to the normal storage if the Non-Pinned WriteBooster Buffer area is also not available(i.e full or not configured ).

# 13.4.18.7.2 Pinned Partial Flush Mode (cont'd)

When the pinned WriteBooster buffer is full, the device notifies the host with the PINNED_WRITEBOOSTER_BUFFER_FULL exception mechanism. It is enabled by setting the PINNED_WRITEBOOSTER_EVENT_EN bit of the wExceptionEventControl attribute.

When the WriteBooster Buffer size is increased by the WriteBooster Buffer Resize operation or the WriteBooster Buffer size is implicitly increased in user space preservation mode, the Pinned WriteBooster Buffer cannot be increased to exceed the size indicated by the dNumSharedWriteBoosterBufferAllocUnits or dLUNumWriteBoosterBufferAllocUnits descriptor.

When the WriteBooster Buffer size is decreased, either or both Pinned Buffer size and non-pinned Buffer size can be decreased depending on the device's internal status.

When the WriteBooster Buffer size is decreased, the WriteBooster Buffer for the amount of non-pin data indicated by dNonPinnedWriteBoosterBufferMinAllocUnits remains as long as possible and shall be reduced at the end.

The pinned data is released by setting the fUnpinEn flag as 0x1 or by changing the bWriteBoosterBufferPartialFlushMode to 0x0(No partial flush mode) or 0x1(FIFO partial flush mode). The released pinned data is flushed by WriteBooster flush operation.

The cumulative amount written to the Pinned WriteBooster Buffer is reported by the dPinnedWriteBoosterCumulativeWrittenSize attribute.

---

JEDEC Standard No. 220G  
Page 405

# 13.4.19 BARRIER COMMAND

## 13.4.19.1 Overview

The formal definition of the Barrier rule is as follows:

Denote a sequence of requests Ci, i=1,..., N. Assuming a Barrier is set between requests Cx and Cx+1 (1<x<N) then all the requests C1...Cx must be flushed to the non-volatile memory before any of the requests Cx+1...CN.

In the example of Figure 13.10, the device server shall process all the requests in Group 1 before the requests in Group 2. On the other hand, between two barriers the device is free to write data into the non-volatile memory in any order. In other words, the Barrier function does not guarantee the order from C1 to Cx (requests in Group 1) or from Cx+1 to CN (requests in Group 2). If the host wants to preserve a certain order it shall flush the cache or set another barrier at a point where the order of execution is important.

[Figure 13.12 shows a diagram titled "Example of Barrier Operation" depicting a Task Set with two groups. Group 1 contains commands C1, C2, ..., Cx followed by a Barrier. Group 2 contains commands Cx+1, Cx+2, ..., CN followed by another Barrier. An arrow points from left to right indicating the direction of command flow.]

**Figure 13.12 — Example of Barrier Operation**

Ensuring order is also important where data should be restored in order when a sudden power-off event occurs. Assume that C1, Barrier, C2, Barrier, and C3 are sequentially requested and then a sudden power-off event occurs. In this case, all or sequential from the beginning recovery is only allowed, such as (C1, C2, C3) or (C1, C2). On the other hand, recovery like the following is not allowed: (C1, C3) or (C2, C3).

BARRIER command shall be issued with Simple task attribute with a normal command priority (CP). Otherwise, the BARRIER command may not work in the way the host expected. Also, the BARRIER command shall affect only the normal priority commands having a simple task attribute. The WRITE command, UNMAP command, and FORMAT UNIT command shall be affected by the BARRIER command.

Figure 13.11 shows an example where the Barrier is located between commands with a simple task attribute. Since both C1 and C2 are simple properties, the Barrier guarantees the order between C1 and C2. That is, the device server shall ensure that data for C1 is programmed in the non-volatile memory before data for C2.

# JEDEC Standard No. 220G
Page 407

## 13.4.19.1 Overview (cont'd)

### Task Set

[**Figure 13.13 — Example of the Barrier between Commands with Simple Property**]

[This figure shows a horizontal task set containing three boxes arranged left to right:
- Left box (green): "C1 Simple"
- Middle box (orange): "Barrier"  
- Right box (green): "C2 Simple"
A dotted arrow points right below the boxes indicating execution order.]

On the other hand, despite the presence of the Barrier between C1 command and C2 command, the BARRIER command are not affected to the higher priority command as shown in below two examples;

In Figure 13.12, The barrier effect is not applied to the C2 command because C2 has a Head of Queue property, a higher priority attribute. I.e., C2 may be scheduled ahead of the BARRIER command as the high priority characteristic requires processing before normal priority(see [SAM]).

### Task Set

[**Figure 13.14 — Example of the Barrier Command between Commands with Different Properties**]

[This figure shows a horizontal task set containing three boxes arranged left to right:
- Left box (green): "C1 Simple"
- Middle box (orange): "Barrier"
- Right box (green): "C2 Head of Queue"
A dotted arrow points right below the boxes indicating execution order.]

Commands in Figure 13.13 are all simple properties, but the barrier effect is not applied to the C2 command because the C2 command has a high priority, not a normal priority. I.e, C2 may be scheduled ahead of the BARRIER command as the high priority characteristic requires processing before normal priority. (See 10.7.1.1)

### Task Set

[**Figure 13.15 — Example of the Barrier Command between Commands with High Priorities**]

[This figure shows a horizontal task set containing three boxes arranged left to right:
- Left box (green): "High Priority C1 Simple"
- Middle box (orange): "Barrier"
- Right box (green): "High Priority C2 Simple"
A dotted arrow points right below the boxes indicating execution order.]

# JEDEC Standard No. 220G
## Page 408

### 13.4.19.1 Overview (cont'd)

The BARRIER command ensures the order only commands to the target logical unit specified in the LUN field. In Figure 13.14, if the BARRIER command is issued to LU 0 and ensures order in LU 0, C4 can be recovered if only C1 and C2 that were issued to LU 0 can be recovered.

[**Figure 13.16 - Barrier Operation Scope (LU Level)**]
[This is a diagram showing a Task Set with 5 sequential commands: C1 (LU 0), C2 (LU 0), C3 (LU 1), Barrier (LU 0), and C4 (LU 0). There's a lightning bolt symbol labeled "Sudden Power Off" pointing to C4, and a dotted arrow underneath spanning the entire sequence.]

**Figure 13.16—Barrier Operation Scope (LU Level)**

When the device receives the BARRIER command, the device may flush data to the medium during its idle time according to the definition of the BARRIER command. However, it may or may not flush all data immediately depending on the device situation. Therefore, if the host would like to guarantee the data to be flushed into the medium immediately, the host is expected to send Synchronize Cache command to the device.

# 13.4.20 Host Initiated Defragmentation

## 13.4.20.1 Overview

In storage devices, the fragmentation of Logical-to-Physical (L2P) mapping is inevitable because of the NAND flash-based memory's inherent structure and it can affect the performance and device lifetime. Therefore, NAND-based conventional memory devices, including UFS devices, may include memory maintenance mechanisms such as Garbage Collection to reduce fragmentation and secure the free space in the device.

This Host Initiated Defrag (HID) feature consists of the explicit analysis of storage and explicit execution of defragmentation which, for example, physically collects data distributed in many NAND blocks into one or a small number of NAND blocks in NAND-based memory device.. The host has a better overview of the optimal time for defragmentation, therefore a more effective memory maintenance can be done if the HID operations are initiated by the host.

This Host Initiated Defragmentation feature allows the host to check the status of whether defragmentation is needed or not and enable the device's internal defrag operation explicitly. I.e. host can enable or disable defragmentation analysis or defragmentation execution.

## 13.4.20.2 Supportability

The supportability of the Host Initiated Defrag (HID) feature is indicated by the Bit [13] of dExtendedUFSFeaturesSupport in Device Descriptor.

If this feature is not supported, all Query Requests related HID features shall fail and the Query Response field shall be set to "Invalid IDN".

## 13.4.20.3 Checking the Need or Status of Analysis or Defragmentation

The host can read the bHIDState attribute to check whether the HID analysis operation or the HID Defrag operation is required or in progress.

• **bHIDState attribute**
  ○ Read Only Attribute
  ○ This attribute can be set to one of the following values:
    ▪ 00h: Idle (default mode after device initialization. Analysis operation is needed because there is no valid fragmentation status information of the device.)
    ▪ 01h: Analysis in Progress
    ▪ 02h: Defragmentation is Required
    ▪ 03h: Defragmentation is In Progress
    ▪ 04h: Defragmentation is Completed
    ▪ 05h: Defragmentation is Not Required
    ▪ Other values are reserved.

Figure 13.15 shows a state transition example that describes the state of the bHIDState attribute and the transition between the states. The bHIDState attribute may be updated when the device receives any write-type (WRITE, Query Requests (WRITE Request), FORMAT UNIT, UNMAP, WRITE BUFFER) command that changes medium status. The bHIDState attribute is updated when the host sets bDefragOperation to operate HID analysis or defrag.

---
*JEDEC Standard No. 220G*  
*Page 409*

# JEDEC Standard No. 220G
Page 410

## 13.4.20.3 Checking the Need or Status of Analysis or Defragmentation (cont'd)

[THIS IS FIGURE: State diagram showing the transition of bHIDState attribute. The diagram shows various states connected by arrows:

- Starting with "Device initialization" at the top
- "Idle (00h)" state in the center
- "Defrag Completion (04h)" on the left
- "Defrag Not Required (05h)" on the left-center
- "Analysis in progress (01h)" on the right
- "Defrag Required (02h)" in the lower-center
- "Defrag in progress (03h)" at the bottom

The states are connected with labeled transitions including:
- "bDefragOperation == 00h" (multiple paths)
- "bDefragOperation == 01h or 02h"
- "Device doesn't require Defrag"
- "Device requires Defrag"
- "bDefragOperation == 02h"
- "Defrag is completed"]

**NOTE** If any UFS command for changing the media status of a UFS device is received during HID analysis operation or HID defrag operation processing, the processing HID operation may be terminated. The host can read from time to time the value of bHIDState to verify the operation was terminated or the device managed to resume the HID operation.

**Figure 13.17 – (Example) Transition of bHIDState Attribute**

• The default value, i.e. after power on or reset, of the bHIDState attribute is 00h (idle state).

• When bDefragOperation (00h) is received from any state, it transitions to Idle (00h) State.

• If the host sets bDefragOperation to 01h (HID analysis is enabled) or 02h (HID analysis and HID defrag are enabled), then the bHIDState attribute shall be updated to 01h (Analysis is in Progress).

• After the device completed HID analysis, the device shall update bHIDState to 02h (Defrag Required) or 05h (Defrag Not Required) depending on whether the HID defrag operation is needed or not.

• If the bHIDState is 02h(Defrag Required) and bDefragOperation is 02h, the device shall update bHIDState to 03h (Defrag in Progress) to start the Defrag operation. After completing the HID Defrag operation, the device shall update bHIDState to 04h (Defrag Completion).

# JEDEC Standard No. 220G
Page 411

## 13.4.20.3 Checking the Need or Status of Analysis or Defragmentation (cont'd)

After the host reads the bHIDState value when it is 04h (Defrag Completion) or 05h (Defrag Not Required), the following parameters shall be initialized:

• bHIDState value to 00h (Idle)

• bHIDProgressRatio value to 00h (0%)

• bDefragOperation value to 00h (HID operations are disabled)

• dHIDAvailableSize value to FFFFFFFFh (indicating no valid information available about the fragmented size).

Additionally, after the host reads bHIDProgressRatio when it is 64h (100%), all the above parameters shall be initialized together.

## 13.4.20.4 Size to be Defragmented

After completing the HID analysis operation, the host can check the total fragmented size in the device by reading dHIDAvailableSize attribute.

• **dHIDAvailableSize attribute**
  ○ The attribute indicates the size of all fragmented data to be moved to completely defragment all data during the HID defrag operation.
  ○ The attribute set to be a multiple of 4KB unit.
  ○ The attribute has Read Only access property (i.e. updated only by the device, and cannot be written by the host.)
  ○ The attribute will be set to 0xFFFFFFFFh when HID analysis is needed.
  ○ The attribute is updated only when the device has completed the HID analysis operation initiated by the host.

The defrag execution time for a large dHIDAvailableSize value may take a long time and affect I/O. To avoid doing all defragmentation during a single operation, the host sets dHIDSize to limit the amount of data the device should move during one defragmentation operation.

• **dHIDSize attribute**
  ○ The attribute is set by the host to configure the size to be defragmented by next defrag operation.
  ○ The attribute set to be a multiple of 4KB unit.
  ○ The default value is 0xFFFFFFFFh indicating that the device defrag as much as possible.
  ○ The attribute has Persistent access property (i.e. value is kept after the power cycle or any type of reset event.)
  ○ The value indicates the size to be defragmented by an HID defrag operation.
  ○ The host can set the value of this attribute less than, or equal to the value of dHIDAvailableSize.
  ○ If the host set dHIDSize bigger than dHIDAvailableSize, then the device will perform defragmentation as much as the amount indicated by dHIDAvailableSize.

# JEDEC Standard No. 220G
Page 412

## 13.4.20.5 Enables and Disable HID Analysis or HID Defrag Operations

The HID analysis and the HID defrag operations are implemented using Query Functions and related Attributes. In particular, the bDefragOperation attribute can enable or disable HID analysis and HID defrag operations.

• **bDefragOperation attribute**

  ○ This attribute has one of the following values:
    00h: HID operations (i.e. HID analysis and HID defrag) are disabled
    01h: HID analysis is enabled
    02h: HID analysis and HID defrag are enabled
    Other values are reserved.

  ○ If the host sends a Query Request to set the bDefragOperation attribute to 01h or 02h so that HID analysis or HID defrag can be performed while the device command queue is not empty, the Query Request shall be processed after completing all previous commands in the command queue. The device will respond to the QUERY request but will not start the analysis till after the queue is empty. When the command queue is empty and the HID operation can be performed, the device performs the HID operation based on the most recently received bDefragOperation value.

  ○ This attribute can be set to 0 by the host to stop the ongoing HID analysis or HID defrag operation.

  ○ This attribute is automatically set to 0 by the UFS device when the operation is completed.

  ○ If any UFS command for changing the media status of a UFS device is received during HID analysis operation or HID defrag operation processing, the processing HID operation may be terminated and the value of bDefragOperation, bHIDProgressRatio, and bHIDState are initialized to 0. The host can read from time to time the value of bHIDState to verify the operation was terminated or the device managed to resume the HID operation

  ○ If the host enables the HID analysis operation or HID defrag operation during the purge operation, the HID analysis or HID defrag request shall fail and the Query Response field in the QUERY RESPONSE UPIU shall be set to 0xFFh ("General Failure").

  ○ This attribute can be set only after the UFS initialization phase (i.e. fDeviceInit cleared to zero by UFS device). If a Query Request to write bDefragOperation attribute is issued before the initialization phase is completed, the request shall fail and the Query Response field in the QUERY RESPONSE UPIU shall be set to 0xFFh ("General Failure").

# 13.4.20.5 Enables and Disable HID Analysis or HID Defrag Operations (cont'd)

When the host sets the bDefragOperation attribute to 01h, the device starts the analysis to calculate the total fragmented amount and reports the result as the dHIDAvailableSize attribute.

[THIS IS FIGURE: A sequence diagram showing interaction between UFS Host and UFS Device. The diagram shows:
1. UFS Host sends a "Query Request( Set bDefragOperation = 01h)" to UFS Device
2. UFS Device responds with "Query Response( SUCCESS)" back to UFS Host
3. There's a note on the right side stating "- The host enables the HID Analysis by setting bDefragOperation as 01h."
4. Below the interaction, there's a box labeled "Fragmentation Analysis in Progress"]

**Figure 13.18 – (Example) HID Analysis Operation**

---
*JEDEC Standard No. 220G*  
*Page 413*

# JEDEC Standard No. 220G
Page 414

## 13.4.20.5 Enables and Disable HID Analysis or HID Defrag Operations (cont'd)

When the HID analysis is completed, the device updates dHIDAvailableSize to indicate the total fragmented size in the device. The host can set dHIDSize attribute to set the size to be defragmented by an HID defrag operation.

When the bDefragOperation attribute is set to 02h, the device shall start executing the HID for the defragmentation.

[THIS IS FIGURE: A sequence diagram showing HID Defrag Operation between UFS Host and UFS Device. The diagram shows multiple steps:

1. Query Request (READ bHIDState) from Host to Device, with response Query Response (bHIDState). Note: "The host can check bHIDState whether Defragmentation is needed or not."

2. Query Request (READ dHIDAvailableSize) from Host to Device, with response Query Response (dHIDAvailableSize). Note: "The host can read dHIDAvailableSize attribute to identify the total fragmented size in device"

3. Query Request (Set dHIDSize) from Host to Device, with response Query Response (SUCCESS). Note: "The host can configure the size to be defragmented by setting dHIDSize attribute."

4. Query Request (Set bDefragOperation = 02h) from Host to Device, with response Query Response (SUCCESS). Note: "The host enable the HID defragmentation operation."

5. Finally shows "Defragmentation is in Progress"

All steps are marked as "OPT" (optional) on the left side.]

**Figure 13.19 – (Example) HID Defrag Operation**

# JEDEC Standard No. 220G
Page 415

## 13.4.20.5 Enables and Disable HID Analysis or HID Defrag Operations (cont'd)

When the bDefragOperation attribute is set to 02h in Idle state, the device performs the HID analysis operation and then starts executing defrag operation only if the analysis result is Defrag is Required. Note that if the device has already been analyzed, the device can start HID defrag operation without additional HID analysis operation.

[DIAGRAM: UFS Host to UFS Device communication flow showing:
- UFS Host sends "Query Request( Set bDefragOperation = 02h)"
- UFS Device responds with "Query Response( SUCCESS)"
- Note: "If host sets bDefragOperation attribute to 02h, the device perform HID analysis operation then shall execute the defrag operation."
- Box showing "After performing the analysis, the defrag operation is performed."]

**Figure 13.20 – (Example) HID Analysis & HID Defrag operation**

## 13.4.20.6 Monitoring the Progress of the Defrag Operation

The host can check defrag progress by reading the bHIDProgressRatio attribute.

This attribute indicates the ratio of the completed defragmentation size over the requested defragmentation size. The requested defragmentation size is calculated as the minimum value of the size indicated by dHIDSize and the size indicated by dHIDAvailableSize.

• **bHIDProgressRatio attribute**
  ○ The attribute has Read Only access property.
  ○ The value of the attribute is expressed in units of 1%.
  ○ The attribute is updated while the device performs a defrag operation. If the device completes the defrag operation, the value of this attribute shall be set to 64h (i.e. to indicate the 100% completion of the requested defragmentation size).

[DIAGRAM: UFS Host to UFS Device communication flow showing:
- "OPT" box on left
- UFS Host sends "Query Request( READ bHIDProgress )"
- UFS Device responds with "Query Response( bHIDProgress )"
- Note: "The host can monitor the defragmentation progress in %."]

**Figure 13.21 – (Example) Monitoring the Progress of Defragmenting**

# JEDEC Standard No. 220G
Page 416

## 13.4.21 Fast Recovery Mode

### 13.4.21.1 Overview

Typically, the UFS host waits for the device's response to the requested command based on its timeout policy. This is not a one-time situation but is repeated multiple times to check the device status and proceed with the recovery procedure, resulting in a long wait time for the host side.

### 13.4.21.2 Introduction

To ease this burden, Fast Recovery Mode can quickly notice issue status of the device and request a device HW Reset from the host. The host can quickly perform a device HW Reset based on device hints and internal policy, resulting in fast recovery. It also provides the device idle time to perform background operations before the host initiates a HW Reset, reducing the waiting time for the host in situations where a HW Reset is necessary due to the device being unresponsive. The host can choose whether to utilize Fast Recovery Mode or proceed with the existing recovery process.

### 13.4.21.3 Implementation

When a non-recoverable hardware error occurs on the device due to internal or external issues while the device is performing an operation, the device will no longer respond and operate normally. The device determines that any operation cannot be completed and decides whether to send a hint requesting HW Reset through RESPONSE UPIU to the host before losing its operation. After the host notices the device's internal status by checking FAST_RECOVERY_NEEDED bits of Device Information field in Response UPIU, the host also can determine how much time the device needs before the host proceeds with a HW Reset. The host determines whether to proceed with a HW Reset based on the device's hint or its own recovery policy.

[Sequence diagram showing communication between Host and Device:
- Host sends "CMD UPIU" to Device
- Device responds with "Response UPIU with Device Information FAST_RECOVERY_NEEDED" to Host
- Host sends "HW Reset" to Device]

**Figure 13.22 – FAST_RECOVERY_NEEDED from RESPONSE UPIU**

# 13.5 UFS Cache

Cache is a temporary storage space in a UFS device. The cache should in typical case reduce the access time (compared to an access to the medium) for both write and read. The cache is not directly accessible by the host but is a separate element in a UFS device. This temporary storage space may be utilized also for some implementation specific operations like as an execution memory for the memory controller and/or as storage for an address mapping table etc. but which definition is out of scope of this standard.

The implementation of the cache is optional for the UFS devices but the related commands shall be implemented so that compatibility with host software driver is seamless independent from the implementation. Devices may explicitly indicate that cache is supported by setting INQUIRY Data VPD page (see [SPC]) parameter V_SUP=1b. V_SUP=0b means that there may or may not be cache implemented. INQUIRY Data VPD page parameter NV_SUP shall be set to 0b.

The cache is a device level cache and applies for all LUs generally. Data written to and read from a Boot W-LU and RPMB W-LU shall not be cached due to the specific nature of these LUs.

The cache is expected to be volatile by nature. Data in the cache is not expected to remain data valid over power cycles or HW/SW resets. The UFS device is expected to manage the cache so that it shall not be possible to read stale data from the device.

While the cache is implemented the device server may utilize the cache during write and read operations for storing data which an application client may request later. The algorithm to manage the cache is out of scope of this standard and is left for the implementation. There are parameters related to the management of the cache defined in CDBs (see bullets) and in 11.4.2.3, Caching Mode Page.

• The disable page out (DPO) bit in the CDB of write, read and verify commands allows the application client to influence the replacement of the logical blocks in the cached data blocks (e.g., in case the cache is full). Setting the DPO bit to 1 means that the device server should not replace the existing logical blocks in the cache with the new logical blocks written or read. When the DPO and FUA bits are set to one, write and read operations effectively bypass the cache.

• The force unit access (FUA) bit in the CDB of write and read commands enables the application client to access the medium. Setting the FUA bit to 1 means that the device server shall perform the write to the medium before completing the command and to read logical blocks from the medium (not from the cache).

During write operations the device server may use the cache to store data that is to be written to the medium at a later time (write-back caching) and thus the command may complete prior to logical blocks being written to the medium. This means also that such data may get lost if sudden power loss or reset occurs. There is also possibility of an error occurring during the actual write operation to the medium later. If an error occurred during such write operation it may be reported as a deferred error on a later command.

An UNMAP operation or any other operation which affects data of a logical block in the medium shall cause the device server to update potential data related to the logical block in the cache accordingly.

It is recommended that the host synchronizes the cache before initiating a PURGE operation.

When a VERIFY command is processed both force unit access and synchronize cache operation are implied.

---

JEDEC Standard No. 220G  
Page 417