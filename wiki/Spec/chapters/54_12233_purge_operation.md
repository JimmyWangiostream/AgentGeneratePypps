# JEDEC Standard No. 220G
## Page 273

### 12.2.3.3 Purge Operation

The purge operation is implemented via Query Functions with Attributes and Flags. In particular, the fPurgeEnable flag allows to enable or disable the execution of a purge operation, and the bPurgeStatus attribute provides information about the operation status.

• **fPurgeEnable flag**

  ○ Write only volatile flag, set to zero after power on or reset.

  ○ Purge operation is enabled when this flag is equal to one, otherwise it is disabled.

  ○ This flag can only be set when the command queue of all logical units are empty.

  ○ This flag is automatically cleared by the UFS device when the operation completes or an error condition occurs.

  ○ This flag can be cleared by the host to interrupt an ongoing purge operation.

• **bPurgeStatus attribute**

  ○ Read only attribute.

  ○ This attribute can be set to one of the following values:

    - 00h: Idle (purge operation disabled).

    - 01h: Purge operation in progress.

    - 02h: Purge operation stopped prematurely by the host.

    - 03h: Purge operation completed successfully.

    - 04h: Purge operation failed due to logical unit queue not empty

    - 05h: Purge operation general failure.

  Other values are reserved and shall not be set.

  ○ bPurgeStatus is set to 00h (Idle) after power on or reset.

  ○ When the host enables the purge operation setting fPurgeEnable flag to one, and if all logical unit command queue are empty, the bPurgeStatus will be set to 01h to indicate that the purge operation is in progress. The bPurgeStatus shall be set to 03h if the operation is completed successfully, or to 05h if a failure occurred.

  ○ The host should send a query request to set fPurgeEnable flag to one only if command queues are empty. A query request to set fPurgeEnable flag which is processed when device command queues are not empty may fail. If the request fails,Query Response field in the QUERY RESPONSE UPIU shall be set to FFh ("General Failure"), the purge operation shall not start, and the bPurgeStatus shall be set to 04h.

  ○ If an ongoing purge operation is interrupted by the host setting the fPurgeEnable flag to zero, the bPurgeStatus shall be set to 02h.

  ○ When the bPurgeStatus is equal to the values 02h, 03h, 04h or 05h, the bPurgeStatus shall be automatically cleared to 00h (Idle) the first time that it is read. The bPurgeStatus values of 00h and 01h shall not be modified as a result of a read.

# JEDEC Standard No. 220G
Page 274

## 12.2.3.3 Purge operation (cont'd)

• If a purge operation is in progress (bPurgeStatus = 01h) commands sent to any logical units or to the RPMB well known logical unit will fail. The device shall return the sense key "NOT READY" to show that the command failed because a purge operation was in progress. Descriptors, attributes and flags may be read when a purge operation is in progress, while only fPurgeEnable flag may be written. A query request to write descriptors, attributes or flags (except fPurgeEnable) shall be terminated with Query Response field set to "General Failure".

• If the host needs to execute a command urgently when a purge operation is in progress, it may interrupt the purge operation. In particular, before issuing any command, the host sets fPurgeEnable flag to zero, waits until the device interrupts the operation, and then sets the bPurgeStatus attribute to 02h (purge operation stopped prematurely).

• If a power failure occurs the fPurgeEnable flag and bPurgeStatus attribute shall be reset to zero. In this case the device will not indicate that operation failed.

Figure 12.1 shows the Purge operation state machine. There are two states: "Idle" and "Purge Op. in progress". After power on, the purge operation state is "Idle", and the purge operation is disabled.

To enable the execution of a purge operation, the host sets fPurgeEnable flag to one sending a QUERY REQUEST UPU. If the setting is executed successfully, the state will transition to "Purge Op. in progress", and the purge operation will start (bPurgeStatus = 01h). If there is at least one logical unit with command queue not empty, the setting of fPurgeEnable flag shall fail, the purge operation shall not start, the state shall remain "Idle", and bPurgeStatus shall be set to 04h.

When the purge operation is completed, the state will transition automatically to "Idle", and bPurgeStatus shall be set to 03h if the operation is completed successfully, or 05h in case of failure.

[State machine diagram showing two states (Idle and Purge op. in progress) with numbered transitions:

| State | bPurgeStatus |
|-------|-------------|
| Idle | 00h, 02h, 03h, 04h, 05h |
| Purge op. in progress | 01h |

| Transition | Description |
|------------|-------------|
| 1 | Set fPurgeEnable and LU command queues not empty |
| 2 | Set fPurgeEnable and LU command queues empty |
| 3 | Clear fPurgeEnable |
| 4 | Automatic transition when the purge operation completes successfully or with failure |

The diagram shows:
- Power-on leads to Idle state
- Transition paths between states with labels:
  - (1) Set fPurgeEnable / Fail (loops back to Idle)
  - (2) Set fPurgeEnable / Success (goes to Purge op. in progress)
  - (3) Clear fPurgeEnable / Success (returns to Idle)
  - (4) Purge op. completed / Success or Fail (returns to Idle)]

NOTE 1 On each transition the input event (triggering the state transition) and the output of the transition itself are mentioned.

**Figure 12.1 — Purge Operation State Machine**

The host may interrupt an ongoing purge operation clearing the fPurgeEnable flag, when the operation has been interrupted the state will transition to "Idle" and bPurgeStatus will be set to 02h.

# JEDEC Standard No. 220G
## Page 275

### 12.2.3.4 Wipe Device

The wipe device operation is fulfilled issuing the FORMAT UNIT command to all enabled logical units. If the logical unit is write protected using one of the methods described in 12.3, Device Data Protection, or if the SWP bit in Control Mode Page is one, then the FORMAT UNIT command shall fail and the content of the medium shall not be altered.

A FORMAT UNIT command sent to the Device well known logical unit requests the device format all enabled logical units except the RPMB well known logical unit. If any logical unit is write protected when the FORMAT UNIT command is issued to Device well known logical unit, the FORMAT UNIT command shall fail and the content of the medium shall not be altered.

The fields of the FORMAT UNIT command should be set as described in the following:

• The Format data (FMTDATA) bit shall be set to zero to specify that no parameter list will be provided.

• The DEFECT LIST FORMAT shall be set to 000b.

• The format protection information (FMTPINFO) shall be set to 00b.

• The vendor specific byte shall be set to 00h.

The UFS device shall ignore CMPLST and LONGLIST bits since FMTDATA is set to zero.

### 12.2.3.5 bProvisioningType Parameter

Logical units can be configured in secure mode using bProvisioningType parameter of the Unit Descriptor. This parameter allows to enable thin provisioning and define TPRZ bit value in the READ CAPACITY parameter data.

The secure mode is enabled if thin provisioning is enabled and TPRZ bit is equal to one. In this mode all operations shall be performed using the mode defined by bSecureRemovalType parameter in the Device Descriptor. Only one type of removal type can be defined for an entire device.

bProvisioningType parameter can be set to the following values:

• 00h: to disable thin provisioning

• 02h: to enable thin provisioning and set TPRZ to zero

• 03h: to enable thin provisioning and set TPRZ to one

TPRZ bit value of zero indicates the device is in normal mode.

As all other Unit Descriptor configurable parameters, the bProvisioningType value is set writing the Configuration Descriptor. (See 14.1.5.3)