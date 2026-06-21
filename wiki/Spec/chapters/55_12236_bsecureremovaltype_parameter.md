# JEDEC Standard No. 220G
Page 276

## 12.2.3.6 bSecureRemovalType Parameter

The bSecureRemovalType parameter within the Device Descriptor defines how information is removed from the physical memory during a Purge operation. This parameter may be set during system integration writing the Configuration Descriptors. bSecureRemovalType values are defined as follows:

• Value of '03h' will result in the information being removed using a vendor defined mechanism.

• Value of '02h' will result in all information being removed by overwriting the addressed locations with a character, its complement, then a random character.

• Value of '01h' will result in all information being removed by overwriting the addressed locations with a single character followed by an erase.

• Value of '00h' will result in all information being removed by an erase of the physical memory (default).

• Other values are reserved for future use and shall not be set.

Device manufacturers are only required to support the mechanism required by their memory array technology.

For additional information please refer to the http://www.killdisk.com/dod.htm or to the following documents for more details:

○ DoD 5220.22-M (http://www.dtic.mil/whs/directives/corres/pdf/522022m.pdf) and

○ NIST SP 800-88 (http://csrc.nist.gov/publications/nistpubs/800-88/NISTSP800-88_rev1.pdf)

# JEDEC Standard No. 220G
Page 277

## 12.3 Device Data Protection

### 12.3.1 Description and Requirements

UFS device data content can be protected at the logical unit level. The following protection modes shall be available:

• Permanent write protection (permanent: once enabled it cannot be reversed)

• Power on write protection (write protection can be cleared with a power cycle or a hardware reset event)

• Secure write protection (write protection can only be configured and enabled/disabled using secure authenticated methods)

These modes of write protections are not implemented in the RPMB well known logical unit. There shall also be a method to read the protection mode that is currently enabled for a logical unit.

### 12.3.2 Implementation

The protection mode can be defined at logical unit level configuring the bLUWriteProtect parameter of the Unit Descriptor. The write protection modes are encoded as in the following:

00h: Logical unit not write protected (or secure write protected if one or more secure write protect entry is set)

01h: Logical unit power on write protected

02h: Logical unit permanently write protected

A power on write protected logical unit (bLUWriteProtect = 01h) can be written only if fPowerOnWPEn flag is equal to zero. The fPowerOnWPEn flag is set to zero after a power cycle or hardware reset event; once it is set to one it cannot be toggled or cleared by the host.

The fPermanentWPEn flag shall be set to one to enable the write protection of all permanently write protected logical unit (bLUWriteProtect = 02h); logical unit can be written if fPermanentWPEn flag is equal to 0b. The fPermanentWPEn flag is write once: it cannot be toggled or cleared once it is set. The fPermanentWPEn flag shall be zero after device manufacturing.

LBA areas within logical units may be write protected using the secure write protection mode.

Secure write protect areas are configured setting the Secure Write Protect Configuration Block, and they may only be created in logical units configured as "not write protected" (bLUWriteProtect=00h).

One logical unit may have up to four secure write protect areas. However the total number of secure write protect areas in a device shall not be more than bNumSecureWPArea.

A secure write protect area can be written only if write protection is disabled in the related Secure Write Protect Entry (WPF flag = 0b). (See 12.4.3.1)

It is recommended to set fPowerOnWPEn flag, fPermanentWPEn flag or WPF flag when all command queues are empty, and wait device query response before enqueuing write command.

If an LBA is write protected, then otherwise valid commands that request unmap, format or alteration of the medium related to that LBA shall be rejected with CHECK CONDITION status with the sense key set to DATA PROTECT.

# 12.4 RPMB

## 12.4.1 Introduction

A signed access to a Replay Protected Memory Block is provided. This function provides means for the system to store data to the specific memory area in an authenticated and replay protected manner. This is provided by first programming authentication key information to the UFS device memory (shared secret).

As the system cannot be authenticated yet in this phase the authentication key programming have to take in a secure environment like in an OEM production. Further on the authentication key is utilized to sign the read and write accesses made to the replay protected memory area with a Message Authentication Code (MAC).

Usage of random number generation and count register are providing additional protection against replay of messages where messages could be recorded and played back later by an attacker.

There are two RPMB modes; Normal RPMB mode and Advanced RPMB mode using EHS.

The RPMB mode can be configured by setting Bit4 of bRPMBRegionEnable parameter of the RPMB descriptor in the configuration stage. If the device receives an RPMB operation request of a different mode than the configured RPMB mode, the device shall respond with ILLEGAL REQUEST.

## 12.4.2 RPMB Well Known Logical Unit Description

The RPMB is contained in a unique well known logical unit whose size is defined in the RPMB Unit Descriptor. RPMB well known logical unit size shall be a multiple of 128 Kbytes, therefore its minimum size is 128 Kbytes. The contents of the RPMB well known logical unit can only be read or written via successfully authenticated read and write accesses. The data may be overwritten by the host but can never be erased.

All accesses to the RPMB will reference the specific RPMB well known logical unit number (W-LUN).

RPMB well known logical unit may be configured into multiple RPMB regions where each RPMB region has its own dedicated authentication key, write counter, result register, and logical address which starts from zero. Refer to 13.2.3 to see how to configure RPMB well known logical unit into multiple RPMB regions.

Each RPMB region can process a single RPMB authenticated operation at any given point in time where a single authenticated RPMB operation corresponds to whole UFS 12.5 Authentication Key Programming Flow, Figure 12.6 Read Counter Value Flow, or Figure 12.10 Authenticated Secure Write Protect Configuration Block Read Flow, and so on as listed in Table 12.8 Request Message Types. For example, the Initiator 3 may start an authenticated operation in RPMB Region 0 and Initiator 4 in RPMB Region 1. The RPMB Region 0 should be accessed by a new authenticated operation request after completing the authenticated operation started by Initiator 3; and RPMB Region 1 after completing the request from the Initiator 4.

---
*JEDEC Standard No. 220G*  
*Page 278*