# JEDEC Standard No. 220G
Page 270

## 12.2.2 Requirements

### 12.2.2.1 Secure Removal

The way in which data is removed securely from the device is dependent on the type of memory technology that is used to implement the UFS device. Three common methods that apply to most memory types implemented at the time of this spec are:

1) The device controller shall issue an erase operation to the addressed location.

2) The device controller shall overwrite the addressed locations with a single character and erase the device.

3) The device controller shall overwrite the addressed locations with a character, its complement, then a random character

UFS devices shall support at least one secure removal method.

### 12.2.2.2 Erase Operation

Erase is an operation that moves data from the mapped address space to the unmapped address space. Logical blocks where erase was applied will be set to the erased value of zero. This operation places no requirement on what the device is required to do with the data in the unmapped address space. After an erase is executed, software on the host should not be able to retrieve the erased logical block data.

The minimum data range that an erase operates on is the logical block.

### 12.2.2.3 Discard Operation

Discard is a non-secure variant of the erase functionality. The distinction between discard and erase is the device behavior where the device is not required to guarantee that host would not retrieve the original data from one or more LBA's that were marked for discard when a read operation is directed to the LBA's.

### 12.2.2.4 Purge Operation

The Purge operation shall be performed on physical blocks that are not being used to store logical block data (e.g.,physical blocks previously used to store logical block data). When the operation is executed it results in removing all the data from such physical blocks. Note that data of LBA that were discarded (bProvisioningType=02h) may not be removed. This is done in accordance with the bSecureRemovalType parameter value of the Device Descriptor. This mode allows the host system to protect against die level attacks.

# 12.2.2.4.1 RPMB Purge Overview

RPMB Purge is a variant of the Purge operation, targeting an RPMB region where overwritten physical copies are made un-recoverable by the device. This allows the host system to overwrite logical blocks in an RPMB region, send RPMB Purge Enable Request messages, and receive acknowledgement that the device has erased the overwritten physical copies of those logical blocks in accordance with bSecureRemovalType. The benefit of RPMB Purge is that the purge targets an RPMB region's physical blocks, based on how the device manages physical blocks in RPMB region. Therefore, an RPMB Purge to these regions may be treated as an independent region or as an entire RPMB LU. This may allow the device to minimize processing time without incurring the penalty of erasing all the device's physical blocks. Note: the write counter should only increment for the region of the RPMB purge request, not for other regions. However, the life time of the RPMB regions shall be the RPMB LU life time as highlighted in "bRPMBLifeTimeEst" status.

While the RPMB Purge is in progress, any other operation received by the device may be delayed or rejected by the device. When rejected, device shall return a good status with the result code (000Ch/008Ch), "Rejected, a RPMB purge operation in progress".

For UFS4.0, RPMB Purge operation is a mandatory feature. Note: since RPMB purge will impact the remaining life of RPMB LU, the host should use RPMB Purge judiciously.

---

*JEDEC Standard No. 220G*  
*Page 271*

# JEDEC Standard No. 220G
Page 272

## 12.2.3 Implementation

### 12.2.3.1 Erase

The erase functionality is implemented using the UNMAP command and it is enabled if the bProvisioningType parameter in the Unit Descriptor is set to 03h (TPRZ = 1).

The device behavior shall comply with the UNMAP definition in [SBC] when the TPRZ bit in the READ CAPACITY(16) parameter data is set to one.

As defined in [SBC],

• The UNMAP command causes a mapped LBA to transition from mapped state to deallocated state if an unmap operation completes without error.

• Since the TPRZ bit is set to one if the erase functionality is enabled, a READ command specifying a deallocated LBA shall return zero.

• The device server may maintain a deallocated LBA in deallocated state until a write operation specifying that LBA is completed without error.

• Or, the device server may transition a deallocated LBA from deallocated state to mapped state at any time (autonomous state transition). For UFS, if TPRZ bit is set to one and an autonomous transition to the mapped state occurs, the LBA shall be mapped to a physical block(s) containing data with all bits set to zero.

LBA's to be erased may be aligned to multiples of the dEraseBlockSize parameter value, where it is possible, to minimize performance impact. dEraseBlockSize is a parameter included in the Unit Descriptor.

### 12.2.3.2 Discard

The discard functionality is implemented using the UNMAP command and it is enabled if the bProvisioningType parameter in the Unit Descriptor is set to 02h (TPRZ = 0). The device behavior shall comply with the UNMAP definition in [SBC] when the TPRZ bit in the READ CAPACITY(16) parameter data is set to zero.

As defined in [SBC],

• The UNMAP command causes a mapped LBA to transition from mapped state to deallocated state if an unmap operation completes without error.

• Since the TPRZ bit is set to zero if the discard functionality is enabled, a READ command specifying a deallocated LBA may return any data.

• The device server may maintain a deallocated LBA in deallocated state until a write operation specifying that LBA is completed without error.

• Or, the device server may transition a deallocated LBA from deallocated state to mapped state at any time (autonomous state transition). For UFS, if TPRZ bit is set to zero and an autonomous transition to the mapped state occurs, the LBA shall be mapped to a physical block(s) containing any data including the original data before UNMAP operation.

LBA's to be discarded may align to multiples of the dEraseBlockSize where possible to minimize performance impact. dEraseBlockSize is a parameter included in the Unit Descriptor.