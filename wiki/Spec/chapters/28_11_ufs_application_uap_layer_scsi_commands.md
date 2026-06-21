# 11 UFS Application (UAP) Layer – SCSI Commands

## 11.1 Universal Flash Storage Command Layer (UCL) Introduction

This clause defines the mandatory commands set supported by the UFS device.

Commands may belong to the UFS Native command set or to the UFS SCSI command set.

This version of the standard does not define UFS native commands.These command set may be defined in the future to support specific flash storage or UFS native basic needs.

The UFS SCSI command set (USC) consists of a selection of commands from SCSI Primary Commands [SPC], and SCSI Block Commands [SBC]. Both command types share similar command descriptor block (CDB) format.

[Figure 11.1 shows a layered architecture diagram with the following components from top to bottom:
- Top layer contains three boxes: "UFS Native command set" (grayed out), "UFS SCSI command set (SPC, SBC)" (highlighted in blue), and "Future expansion..." (empty box)
- Middle layer: "UFS Transport Protocol layer"
- Bottom layer: "UFS Interconnects layer (MIPI UniPro and M-PHY)"]

**Figure 11.1 — UFS Command Layer**

### 11.1.1 The Command Descriptor Block (CDB)

SCSI commands are communicated by sending the SCSI Command Descriptor Block (CDB) to the device. There are only fixed length CDB format for UFS, unlike SCSI which has additional Variable Length CDB format.

All UFS CDBs shall have an OPERATION CODE field as their first byte and these values shall be defined by each SCSI and UFS. Detail SCSI CDB usages and structure are defined in [SPC], 4.3, The Command Descriptor Block (CDB).

The General Common CDB fields are defined in [SPC], 4.3.5, Common CDB fields.

**Operation code**
The first byte of a SCSI and USC CDB shall contain an operation code identifying the operation being requested by the CDB.

The OPERATION CODE of the CDB contains a GROUP CODE field and COMMAND CODE field. The GROUP CODE field provides eight groups of command codes and the COMMAND CODE provides thirty-two command codes in each group, see [SPC] for further details.

## 11.2 Universal Flash Storage Native Commands (UNC)

The UNC are not defined in this version of the standard; they may be defined in future versions if needed.

# 11.3 Universal Flash Storage SCSI Commands

The Basic Universal Flash Storage (UFS) SCSI commands are compatible with SCSI Primary Commands - 4 [SPC] and SCSI Block Commands - 3 [SBC].

If enabled (bLUEnable = 01h), each logical unit shall support the commands defined in Table 11.1 as mandatory.

## Table 11.1 — UFS SCSI Command Set

| Command name | Opcode | Command Support |
|--------------|--------|-----------------|
| FORMAT UNIT | 04h | M |
| INQUIRY | 12h | M |
| MODE SELECT (10) | 55h | M |
| MODE SENSE (10) | 5Ah | M |
| PRE-FETCH (10) | 34h | M |
| PRE-FETCH (16) | 90h | O |
| READ (6) | 08h | M |
| READ (10) | 28h | M |
| READ (16) | 88h | O |
| READ BUFFER | 3Ch | M |
| READ CAPACITY (10) | 25h | M |
| READ CAPACITY (16) | 9Eh | M |
| REPORT LUNS | A0h | M |
| REQUEST SENSE | 03h | M |
| SECURITY PROTOCOL IN (1) | A2h | M |
| SECURITY PROTOCOL OUT (1) | B5h | M |
| SEND DIAGNOSTIC | 1Dh | M |
| START STOP UNIT | 1Bh | M |
| SYNCHRONIZE CACHE (10) | 35h | M |
| SYNCHRONIZE CACHE (16) | 91h | O |
| TEST UNIT READY | 00h | M |
| UNMAP | 42H | M |
| VERIFY (10) | 2Fh | M |
| WRITE (6) | 0Ah | M |
| WRITE (10) | 2Ah | M |
| WRITE (16) | 8Ah | O |
| WRITE BUFFER | 3Bh | M |

M: mandatory, O: optional

**NOTE 1** SECURITY PROTOCOL IN command and SECURITY PROTOCOL OUT command are supported by the RPMB well known logical unit.

---

JEDEC Standard No. 220G  
Page 184