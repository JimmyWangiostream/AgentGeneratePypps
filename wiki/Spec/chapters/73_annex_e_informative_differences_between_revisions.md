# JEDEC Standard No. 220G
Page 509

---

## Annex E (Informative) Differences Between Revisions

### E.1 Changes Between JESD220G and its Predecessor JESD220F (August 2022)

#### E.1.1 NEW Features

The following items were added:

• Device Level Exception Event (see 13.4.12.1)
• Host Initiated Defragmentation (see 13.4.20)
• Device Health Exception (see 13.4.12)
• WriteBooster buffer Resizing (13.4.18.6)
• Partial Flush Modes of WriteBooster (13.4.18.7)
• bBootLunEn attribute protection improvement (see 13.1.2)
• Authentication via RPMB in for vendor specific commands (see 12.4.7.3.9-10 and 12.4.7.4.9-10)
• Fast Recovery Mode (see 13.4.21)

#### E.1.2 Changes in Clause 2 "Normative References"

Updated the following references cited in this document:

• UniPro 2.0's publication date
• JEDEC publication references are updated to their respective latest revision and publication date

#### E.1.3 Changes in Features Already Defined in UFS 4.0

• VCCO Absolute DC Max alignment to NAND interface standard (see 6.7)
• Defined the number of simultaneous operations allowed in RPMB (see 13.4.13)
• Added precision in Capacity Adjustment Factors (see 13.2.3 and 14.1.4.4)
• Authenticated Secure Write Protect Configuration Block Write LUN mismatch error in Advanced RPMB mode (see 12.4.7.4.5)
• 13.4.18.5 sub-clause title changed from Preserve User Space Option to User Space Modes

Minor editorial clarifications were added, typographic errors were corrected, and minor formatting changes were made to comply with *Style Manual for Standards and Other Publications of JEDEC, JM7A*, in addition to what is summarized above.

# JEDEC Standard No. 220G
Page 510

## E.2 Changes between JESD220F and its Predecessor JESD220E (January 2020)

### E.2.1 NEW Features or New Definitions

The following items were added:

• Optional LSS signal added for HighSpeed-LinkStartup control, see 6.1

• Electrostatic Discharge Sensitivity Characteristics added, see 6.1

• M-PHY HS reference clock operating requirements added, see 6.4

• REF_CLK frequency detection added for HS-LS, see 6.4

• Optional RZQ1 and RZQ2 added, see 6.6

• AC noise specification added, see 6.8

• EXT_IID added to extend Initiator ID, see 10.6.2(k)

• BARRIER Command added, see 11.3.29, 13.4.19

• RPMB Purge added, see 12.2.2.4.1

• Advanced RPMB using EHS added, see 12.4

• qTimestamp available for tagging Error Log entries, see 13.4.9

• Added Vendor Specific Descriptor, see 14.1.4.15

• Added Vendor Specific Flags, see 14.2

• Reserved Attribute 01h for HPB Extension, see 14.3

• Defined wHostHintCacheSize Attribute, see 14.3

• Added Vendor Specific Attributes, see 14.3

• Added Annex B (informative) Reference Clock Measurement Procedure

• Added Annex C (informative) Reference Clock Detection in HS-LSS

• Added Annex D (informative) Board Design Guideline

### E.2.2 Changes in Clause 2 "Normative Reference"

Updated the following document references:

• M-PHY® specification: from version 4.1 to version 5.0

• Unified Protocol (UniPro®) specification: from version 1.8 to version 2.0

• Added UFS File Based Optimization (FBO) Extension Specification

# JEDEC Standard No. 220G
Page 511

## E.2.3 Changes in Features Already Defined in UFS 3.1

• M-PHY HS-Gear5 is mandatory, see 4.1

• M-PHY LS support reduced to Gear1 only, see 4.1

• Support for VCC=3.3V dropped, see 4.2, 6.3

• BER reduced from under 10-10 to 10-12, see 4.2

• Reference clock frequency of 52.0MHz reintroduced, now as default, see 6.4

• Reference clock phase noise parameter refined as Random Jitter and Deterministic Jitter, see 6.4

• Power Parameter element format change, see 7.4.3

• UFS PHY capability listed attributes reduced to set that differs from M-PHY 5.0, see 8.7

• UFS Target Port Identifiers updated, see 9.1

• Extended Header Segments enabled, see 10.6

• Out of order data sequencing with added hinting, see 10.7.14

• READ BUFFER command available at Boot Ready for Error Log, see 13.1.3.3

• Existing RPMB renamed Normal RPMB, see 12.4

• Clarified bDataOrdering in Geometry Descriptor, see 14.1.4.4

• RPMB bLogicalBlockSize and qLogicalBlockCount adapted for use with Advanced RPMB, see 14.1.4.6

• Further definition of OEM ID STRING DESCRIPTOR, see 14.1.4.11

• Clarified bOutOfOrderDataEn Attribute, see 14.3

• Moved (informative) Differences between Specification Revisions from Annex B to Annex E

Several clarifications were added and editorial changes were implemented in addition to what is summarized in this annex.

# JEDEC Standard No. 220G
Page 512

## E.3 Changes between JESD220E and its Predecessor JESD220D (January 2018)

### E.3.1 New Features or New Definitions

The following items were added:

• UFS-DeepSleep Power Mode, see 7.4 "UFS Device Power Modes and LU Power Condition"

• Performance Throttling, see 13.4.17 "Performance Throttling Event Notification"

• WriteBooster, see 13.4.18 "Write"

### E.3.2 Changes in Clause 2 "Normative Reference"

Added the following documents:

• Application Note for UniPro® v1.8

• UFS Host Performance Booster (HPB) Extension Specification

### E.3.3 Changes in Features Already Defined in UFS 3.0

Changes related to features already defined in the previous version of the standard are summarized in the following:

• Added the following Exception Events: PERFORMANCE_THROTTLING and WRITEBOOSTER_FLUSH_NEEDED. See 13.4.12 "Exception Events Mechanism".

Several clarifications were added and editorial changes were implemented in addition to what is summarized in this annex.

# JEDEC Standard No. 220G
Page 513

## E.4 Changes between JESD220D and its Predecessor JESD220C (March 2016)

### E.4.1 New Features or New Definitions

The following items were added:

• VCC = 2.5V, see 4.2 "Interface Features" and 6 "UFS ELECTRICAL: CLOCK, RESET, SIGNALS AND SUPPLIES"

• M-PHY(R) HS-GEAR4, see 6.4 "Reference Clock" and 8.7 "UFS PHY Attributes"

• bRefClkGatingWaitTime attribute, see 6.4 "Reference Clock"

• Extended temperature ranges, see 6.6 "Absolute Maximum DC Ratings and Operating Conditions"

• M-PHY(R) Adapt, see 8.6

• Error History Mode (MODE = 1Ch) in READ BUFFER Command, see 11.3.27.3

• RPMB Regions, see 12.4 RPMB

• Refresh Operation, see 13.4.14

• Temperature Event Notification, see 13.4.15

### E.4.2 Changes in Clause 2 "Normative Reference"

• M-PHY(R) specification: from version 3.00 to version 4.1.

• Unified Protocol (UniPro) specification: from version 1.6 to version 1.8.

Added the following specifications:

• JEDEC Standard Manufacturer's identification code, JEP106

• JEDEC Multichip Packages (MCP) and Discrete eMMC, e2MMC, and UFS, JESD21C

### E.4.3 Changes in Features Already Defined in UFS 2.1

Changes related to features already defined in the previous version of the standard are summarized in the following:

• Support for HS-GEAR3 has been changed to mandatory, see 4.1 "General Features"

• Removed VCC = 1.8V, see 6 "UFS ELECTRICAL: CLOCK, RESET, SIGNALS AND SUPPLIES"

• Support for READ BUFFER command has been changed to mandatory, see Table 11.1

• Removed 52 MHz reference clock frequency, see 6.4

• Support for some M-PHY features has been changed to optional (PWM-G2 to PWM-G4, small amplitude, LCC functionality), see 8

• Added Unit Attention Condition details, see 10.8.9

Several clarifications were added and editorial changes were implemented in addition to what is summarized in this annex.

# JEDEC Standard No. 220G
Page 514

## E.5 Changes between JESD220C and its Predecessor JESD220B (September 2013)

### E.5.1 New Features or New Definitions

The following items were added

• Multi-initiator, see 10.6.2 "Basic Header Format"

• Command priority, see 10.7.1 "COMMAND UPIU"

• Field Firmware Update, see 11.3.28 "WRITE BUFFER Command"

• Vital product data parameters see 11.5

• Secure write protection, see
  ○ 12.4 "RPMB"
  ○ 12.4.6.7 "Authenticated Secure Write Protect Configuration Block Write"
  ○ 12.4.6.8 "Authenticated Secure Write Protect Configuration Block Read"

• Device Life Span Mode, see 13.4.13

• Production State Awareness, see 13.6

• Product Revision Level String Descriptor, see 14.1.4.13

• Device Health Descriptor, see 14.1.4.14

### E.5.2 Changes in Clause 2 "Normative Reference"

Added the following specifications:

• 1.2 V +/- 0.1V (Normal Range) and 0.8 - 1.3 V (Wide Range) Power Supply Voltage and Interface Standard for Nonterminated Digital Integrated Circuits

• JEDEC Recommended ESD Target Levels for HBM/MM Qualification, JEP155A.01, March

• JEDEC Recommended ESD-CDM Target Levels, JEP157, October 2009

• Eastlake, D. and T. Hansen, "US Secure Hash Algorithms (SHA and HMAC-SHA)", RFC

### E.5.3 Changes in Features Already Defined in UFS 2.0

Changes for features already defined in the previous version of the standard are summarized in the following:

• 3.2 "Terms and Definitions", added: "application client", "device server"; changed the definition for: "initiator device", "target device", "transaction".

• 3.3 "Keywords", added "obsolete".

• 6.1 "UFS Signals" Table 6.1, added reference to ESD specifications.

• 6.3 "Power Supplies", added figure for tPRUH, tPRUL and tPRUV.

• 6.4 "Reference Clock", clarified reference clock details and bRefClkFreq attribute setting.

• 7.4.1.4 "UFS-Sleep Power Mode", fixed sense key and additional sense code values for commands other than START STOP UNIT or REQUEST SENSE.

# JEDEC Standard No. 220G
Page 515

## E.5.3 Changes in Features Already Defined in UFS 2.0 (cont'd)

• 7.4.1.5 "Pre-Sleep Power Mode", fixed sense key value in pollable sense data.

• 7.4.1.7 "Pre-PowerDownPower Mode", fixed sense key value in pollable sense data.

• 8.4 "HS Burst" removed 8.4.3 "Slew Rate Control".

• 8.6 "UFS PHY Attributes", extended the ranges of the following capability attributes: TX_Min_STALL_NoConfig_Time_Capability, RX_Min_STALL_NoConfig_Time_Capability, RX_HS_G1_SYNC_LENGTH_Capability, RX_HS_G2_SYNC_LENGTH_Capability, RX_HS_G3_SYNC_LENGTH_Capability

• 9.5 "UniPro/UFS Transport Protocol Address Mapping", added Table 9.1 "UFS Port IDs"

• 9.6.5 "UniPro Device Management Entity Transport Layer", substituted Table 9.1 "DME Service Primitives" with a text.

• 10.7.1 "COMMAND UPIU", added Flags.CP bit and IID field.

• 10.7.2 "RESPONSE UPIU", added requirements for the termination of a command with Data-Out data transfer, added IID field.

• 10.7.3 "DATA OUT UPIU", added: IID field, the requirement that Data Segment area shall contain an integer number of logical blocks and an example for Data out transfer.

• 10.7.4 "DATA IN UPIU", added: IID field, the requirement that Data Segment area shall contain an integer number of logical blocks and an example for Data in transfer.

• 10.7.5 "READY TO TRANSFER UPIU", added: IID field, the requirement to request the transfer of an integer number of logical blocks and an example for READY TO TRANSFER UPIU sequence.

• 10.7.6 "TASK MANAGEMENT REQUEST UPIU", added IID field, clarified behavior if more than one task management request are received, added IID field in Task Management Input Parameters.

• 10.7.7 "TASK MANAGEMENT RESPONSE UPIU", added IID field, added requirements for the termination of a command with Data-Out data transfer.

• 10.7.8.3 "Transaction Specific Fields", indicated QUERY FUNCTION value for each opcode in Table 10.30.

• 10.7.10 "REJECT UPIU", added IID field.

• 10.7.13 "Data out transfer rules", in UFS 2.0 this sub-clause was in clause 13, while in UFS 2.1 it was moved in clause 10, figures were updated.

• 10.8.5 "Well Known Logical Unit Defined in UFS", added FORMAT UNIT command in the list of commands supported by the Device well known logical unit.

• 10.9.8 "Task Management Function procedure calls", added requirements for the termination of a command with Data-Out data transfer.

• 11.3 "Universal Flash Storage SCSI Commands" changed WRITE BUFFER command support from optional to mandatory.

• 11.3.2.4 "Inquiry Response Data", specified the PERIPHERAL DEVICE TYPE value for well known logical unit (e.g., 1Eh).

• 11.3.18 "FORMAT UNIT Command", added description related to Device well known logical unit.

# JEDEC Standard No. 220G
Page 516

## E.5.3 Changes in Features Already Defined in UFS 2.0 (cont'd)

• 11.3.28 "WRITE BUFFER Command", added Field Firmware Update.

• 11.4.2.1 "Control Mode Page", changed EXTENDED SELF-TEST COMPLETION TIME field value from 0000h to device specific. BUSY TIMEOUT PERIOD field from changeable to not changeable, defined TST as not changeable.

• 12.2.3.4 "Wipe Device", added wipe device feature using Device well known logical.

• 12.4.5.1 "CDB format of SECURITY PROTOCOL IN/OUT", specified command response in case of invalid ALLOCATION LENGTH or TRANSFER LENGTH values.

• 13.2.3 "Logical Unit Configuration", added an example for dNumAllocUnits calculation, changed the recommendation for setting logical block size: in UFS 2.1 references dOptimalLogicalBlockSize instead of bOptimalWriteBlockSize or OptimalReadBlockSize.

• 13.4.6 "Dynamic Device Capacity", added Dynamic Capacity Resource Policy.

• 13.4.12 "Queue Depth Definition", new section which describes shared queue and per-logical unit queue implementations.

• 14.1.4.2 "Device Descriptor", changed bSecurityLU parameter value from "Device specific" to "01h", changed wSpecVersion parameter value from "0200h" to "0210h", added the following parameters: bUFSFeaturesSupport, bFFUTimeout, bQueueDepth, wDeviceVersion, bNumSecureWPArea, dPSAMaxDataSize, bPSAStateTimeout, iProductRevisionLevel.

• 14.1.6.3 "Configuration Descriptor", added three Configuration Descriptors and bConfDescContinue parameter.

• 14.1.4.4 "Geometry Descriptor", added the following parameters: bMaxNumberLU, bDynamicCapacityResourcePolicy, dOptimalLogicalBlockSize.

• 14.1.4.5 "Unit Descriptor", added bPSASensitive parameter.

• 14.1.4.6 "RPMB Unit Descriptor", added bPSASensitive parameter, changed bLUQueueDepth value from "00h" to "Device specific".

• 14.2 "Flags", added fDeviceLifeSpanModeEn flag.

• 14.3 "Attributes", changed bActiveICCLevel access property from "Persistent" to "Volatile", changed bRefClkFreq access property from "Write once" to "Persistent", defined as obsolete the dCorrPrgBlkNum (IDN=11h), added bDeviceFFUStatus, bPSAState and dPSADataSize.

• Global
  ○ Removed the use of "embedded UFS", " UFS Card"
  ○ Reviewed the use of "initiator device", "target device", "UFS host", "UFS device"
  ○ Added optional support for 32 logical units are related Configuration Descriptors
    ▪ 14.1.3 "Accessing Descriptors and Device Configuration"
    ▪ 14.1.6.3 "Configuration Descriptor"

Several clarifications were added and editorial changes were implemented in addition to what is summarized in this annex.

# JEDEC Standard No. 220G
Page 517

## E.6 Changes between JESD220B and its Predecessor JESD220A (June 2012)

### E.6.1 New Features or New Definitions

The following items were added

• HS-GEAR3 support (optional)

• Multi-lane support (two lanes, optional)

• New 6.5.1"HS Gear Rates", Defined HS-BURST rates

• New 6.7 "Absolute Maximum DC Ratings", Defined absolute maximum DC ratings for signal voltages, power supply voltages, and storage temperature.

• New 7.2 "Power up ramp", Defined requirements for power up ramp.

• New 7.3 "Power off ramp", Defined requirements power off ramp.

• Mode Page Policy VPD support (see 11.3.2.1 "VITAL PRODUCT DATA")

• New 11.3.21 "SECURITY PROTOCOL IN Command"

• New 11.3.22 "SECURITY PROTOCOL OUT Command"

### E.6.2 Changes in Clause 2 "Normative Reference"

• M-PHY^SM specification: from version 2.00.00 to version 3.0.

• Unified Protocol (UniPro^SM) specification: from version 1.41.00 to version 1.6.

### E.6.3 Changes in Features Already Defined in UFS 1.1

Changes for features already defined in the previous version of the standard are summarized in the following:

• 4.1 "General Features", Mandatory support for HS-GEAR2

• 5.4.3 "MIPI UniPro Related Attributes", DME_DDBL1_ManufacturerID and DME_DDBL1_DeviceClass, Used Attribute names defined in [MIPI-UniPro] and fixed Attribute ID value.

• 5.5.1.1 "Client-Server Model", Deleted the sentence: "Only one Task can be processed at a time within a Logical Unit. If a device contains multiple Logical Units, it could have the ability to process multiple Tasks simultaneously or concurrently if so designed.".

• 7.3.1 "EndPointReset", Deleted the sentence "Note that if the device has already completed the initialization phase before receiving the EndPointReset, it is not required to set fDeviceInit to '1' and wait until the device clears it.".

# JEDEC Standard No. 220G
Page 518

## E.6.3 Changes in Features Already Defined in UFS 1.1 (cont'd)

• 7.4.1 "Device Power Modes", Clarified logical unit response to SCSI commands for each power mode. UFS-Sleep power mode: added the sentence: "VCC power supply should be restored before issuing START STOP UNIT command to request transition to Active power mode or PowerDown power mode.". Figure "Power Mode State Machine": added Powered On power mode, arrow from Active to Pre-Sleep with "bInitPowerMode=00h", and some notes. Defined all power mode transitions. Added the sentence: "The effects of concurrent power mode changes requested by START STOP UNIT commands with the IMMED bit set to one are vendor specific.". Added the sentence "A START STOP UNIT command with the IMMED bit set to zero causing a transition to Active, Sleep, or PowerDown power modes shall not complete with GOOD status until the device reaches the power mode specified by the command.". Added 7.4.1.9 "Device Well Known Logical Unit Responses to SCSI commands"

• New 7.4.4 "Logical Unit Power Condition"

• 8.6 "UFS PHY Attributes", Added the following M-PHY^SM Attributes: TX_Hibern8Time_Capability, TX_Advanced_Granularity_Capability, TX_Advanced_Hibern8Time_Capability, TX_HS_Equalizer_Setting_Capability, RX_Hibern8Time_Capability, RX_PWM_G6_G7_SYNC_LENGTH_Capability, RX_HS_G2_SYNC_LENGTH_Capability, RX_HS_G3_SYNC_LENGTH_Capability, RX_HS_G2_PREPARE_LENGTH_Capability, RX_HS_G3_PREPARE_LENGTH_Capability, RX_Advanced_Granularity_Capability, RX_Advanced_Hibern8Time_Capability, RX_Advanced_Min_ActivateTime_Capability.

• 9.6.6 "UniPro Attributes", Added the UniPro^SM PA_MaxDataLanes constant, PA_AvailTxDataLanes and PA_AvailRxDataLanes Attributes.

• Table 10.20 — Sense Key, Deleted the sentence: "The UNIT ATTENTION condition will remain set until an explicit REQUEST SENSE has been issued to the target."

• 10.5.5 "DATA OUT UPIU", Added the sentence: "Note that in case out of order DATA OUT UPIUs, the last data portion may not be transmitted by the final UPIU.".

• 10.5.6 "DATA IN UPIU", Added the sentence: "Note that in case out of order DATA IN UPIUs, the final data portion may not be transmitted by the last UPIU."

• 10.5.7 "READY TO TRANSFER UPIU"^xxx
Added the sentence: "The Data Buffer Offset shall be an integer multiple of four.".
Added the sentence: "The Data Transfer Count field shall be always an integer multiple of four bytes except for RTT which requests the final portion of data in the transfer.".

• New 10.5.10.12 "NOP"
Defined NOP OPCODE for QUERY REQUEST UPIU.

• 10.5.11 "QUERY RESPONSE UPIU", Added Device Information in byte 9 of QUERY RESPONSE UPIU. Defined Query Response value for invalid Query Function field and OPCODE field combinations.

• New 10.5.11.14 "NOP", Defined NOP OPCODE for QUERY RESPONSE UPIU.

• .3.2.4 "Inquiry Response Data", Added the sentence: "The 4-byte PRODUCT REVISION LEVEL in the Inquiry Response Data shall identify the firmware version of the UFS device and shall be uniquely encoded for any firmware modification implemented by the UFS device vendor."

# JEDEC Standard No. 220G
## Page 519

### E.6.3 Changes in Features Already Defined in UFS 1.1 (cont'd)

• 11.4.2 "UFS Supported Pages", Defined default value and configurable fields for the following Mode Pages: Control Mode Page, Read-Write Error Recovery Mode Page, Caching Mode Page.
• 12.4.6 "RPMB Operations", Changed Command Set Type field value from 1h to 0h.
• 13.1.3.1 "Partial initialization", During device initialization is no longer required to send a sequence of NOP OUT UPIU, the host sends only one NOP OUT UPIU.
• 13.1.3.3 "Initialization completion", Added a table to clarify which are the valid UPIUs and SCSI commands for each initialization phase.
• 13.2.3 "Logical Unit Configuration"
  Added the sentence: "Supported bLogicalBlockSize values are device specific, refer to the vendor datasheet for further information".
  Added the sentence: "The Capacity Adjustment Factor value for Normal memory type is one."
• 13.4.4 "Background Operations Mode"
  Removed the requirement of having empty command queues for starting background operations.
  Added bBackgroundOpsTermLat (Background Operations Termination Latency) parameter in Device Descriptor.
  Defined URGENT_BKOPS = 0 if bBackgroundOpStatus = 1.
• 13.4.7 "Data Reliability"
  Increased data reliability granularity from 512 bytes to logical block size.
  Defined RPMB data reliability granularity (bRPMB_ReadWriteSize × 256 bytes)
• 13.4.12 "Data transfer rules related with RTT (Ready-to-Transfer)"
  Added the sentence: "RTT requests related to several write commands or from different logical units may be interleaved."
• 14.1.6.2 "Device Descriptor"
  bDeviceSubClass: reserved bit 2 for Unified Memory Extension standard.
  Changed bNumberLU manufacturer default value (MDV) from 01h to 00h.
  Added bBackgroundOpsTermLat parameter.
  Reserved bytes for Unified Memory Extension standard.
  Clarified wManufacturerID definition.
• 14.1.6.3 "Configuration Descriptor" Removed bNumberLU (because this parameter is no longer configurable).
• 14.1.6.5 "Unit Descriptor" bLUWriteProtect: reserved the value 03h for UFS Security Extension standard.
• 14.2 "Flags": Added fPermanentlyDisableFwUpdate (Permanently Disable Firmware Update) flag.
• 14.3 "Attributes": Changed bRefClkFreq manufacturer default value (MDV) from 00h to 01h.

Several clarifications were added and editorial changes were implemented in addition to what is summarized above.

# JEDEC Standard No. 220G
## Page 520

This page intentionally left blank.

# JEDEC®

## Standard Improvement Form                                    JEDEC   JESD220G

The purpose of this form is to provide the Technical Committees of JEDEC with input from the industry regarding usage of the subject standard. Individuals or companies are invited to submit comments to JEDEC. All comments will be collected and dispersed to the appropriate committee(s).

If you can provide input, please complete this form and return to:

JEDEC                                    Email: angies@jedec.org  
Attn: Publications Department  
3103 10th Street North  
Suite 240S  
Arlington, VA 22201

---

1. I recommend changes to the following:

   ☐ Requirement, clause number _______________
   
   ☐ Test method number _____________ Clause number _________________
   
   The referenced clause number has proven to be:
   
   ☐ Unclear   ☐ Too Rigid   ☐ In Error
   
   ☐ Other _______________________________________________________________

---

2. Recommendations for correction:

   ________________________________________________________________________
   
   ________________________________________________________________________
   
   ________________________________________________________________________
   
   ________________________________________________________________________

---

3. Other suggestions for document improvement:

   ________________________________________________________________________
   
   ________________________________________________________________________
   
   ________________________________________________________________________

---

**Submitted by**

Name: _____________________________________     Phone: ___________________________

Company: __________________________________     E-mail: ___________________________

Address: ___________________________________

City/State/Zip: _______________________________     Date: ___________________________

# JEDEC

[The image shows the JEDEC logo, which consists of the text "JEDEC" in large, bold gray letters with a registered trademark symbol (®) after it. Below the text is a horizontal red line. There appears to be a watermark reading "Phison Electronics Corporation" diagonally across the image.]

---

*Downloaded by Lat-Fock Chua (lat.fock.chua@phison.com) on Jun 7, 2025, 4:31 pm PST.*