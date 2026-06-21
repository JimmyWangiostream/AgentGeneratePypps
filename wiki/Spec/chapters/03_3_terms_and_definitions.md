# 3 Terms and Definitions

For the purposes of this standard, the terms and definitions given in the document included in clause 2, Normative Reference, and the following apply.

**Application Client:** An entity that is the source of SCSI commands and task management function requests in the host.

**Byte:** An 8-bit data value with most significant bit labeled as bit 7 and least significant bit as bit 0.

**Command Descriptor Block:** The structure used to communicate commands from an application client to a device server. A CDB may have a fixed length of up to 16 bytes or a variable length of between 12 and 260 bytes.

**Device ID:** The bus address of a UFS device.

**Device Server:** An entity in the device that processes SCSI commands and task management functions.

**Doubleword:** A 32-bit data value with the most significant bit labeled as bit 31 and least significant bit as bit 0.

**Dword:** 32-bit data value, a Doubleword.

**Gigabyte:** 1,073,741,824 or 2³⁰ bytes.

**Host:** An entity or a device with the characteristics of a primary computing device that includes one or more SCSI initiator devices.

**Initiator device:** Within a transaction, the originator of a SCSI command request message to a target device.

**Kilobyte:** 1024 or 2¹⁰ bytes.

**Logical Unit:** A logical unit is an internal entity of a bus device that performs a certain function or addresses a particular space or configuration within a bus device.

**Logical Unit Number:** A numeric value that identifies a logical unit within a device

**Megabyte:** 1,048,576 or 2²⁰ bytes.

**Quadword:** A 64-bit data value with most significant bit labeled as bit 63 and least significant bit as 0.

**Segment:** A specified number of sequentially addressed bytes representing a data structure or section of a data structure.

**Segment ID:** A 16-bit value that represents an index into a table or an address of a segment descriptor or simply an absolute value when an element of an absolute address

**SCSI Request Block:** A data packet that contains a multi-byte SCSI command and additional contextual information needed to carry out the command operation. A SCSI Request Block is built by the host and is targeted at a particular bus device.

**Target device:** Within a transaction, the recipient of a SCSI command request message from an initiator device.

**Task:** A task is a SCSI command which includes all transactions to complete all data transfers and a status response that will satisfy the requirements of the requested services of the command.

**Transaction:** A UFS primitive action which results in transmission of serial data packets between a target device and initiator device.

---
*JEDEC Standard No. 220G*  
*Page 3*

# JEDEC Standard No. 220G
## Page 4

## 3 Terms and Definitions (cont'd)

**Terabyte:** 1.099.511.627.776 or 2⁴⁰ bytes.

**UFS Protocol Information Unit:** Information transfer (communication) between a UFS host and device is done through messages which are called UFS Protocol Information Units. These messages are UFS defined data structures that contain a number of sequentially addressed bytes arranged as various information fields.

**Unit:** A bus device

**Unit Attention:** A condition of a bus device utilizing the SCSI protocol where it needs to be serviced before it can continue processing requests and responses.

**Word:** A 16-bit data value with most significant bit labeled as bit 15 and least significant bit as bit 0.

### 3.1 Acronyms

| Acronym | Definition |
|---------|------------|
| CDB | Command Descriptor Block |
| CPort | A CPort is a Service Access Point on the UniPro Transport Layer (L4) within a Device that is used for Connection-oriented data transmission |
| DMA | Direct Memory Access |
| DSC | Digital Still Camera |
| FFU | Field Firmware Update |
| GB | Gigabyte |
| HCI | Host Controller Interface |
| HPB | UFS Host Performance Booster |
| KB | Kilobyte |
| LBA | Logical Block Address |
| LSS | Link Startup Sequence |
| LUN | Logical Unit Number |
| MB | Megabyte |
| MIPI | Mobile Industry Processor Interface |
| MP3 | MPEG-2 Audio Layer 3 |
| NA | Not applicable |
| NU | Not used |
| PDU | Protocol Data Unit |
| PLL | Phase-Locked Loop |
| PMP | Portable media player |
| PSA | Production State Awareness |
| PWM | Pulse Width Modulation |
| RFU | Reserved for future use |
| RPMB | Replay Protected Memory Block |

# JEDEC Standard No. 220G
Page 5

## 3.1 Acronyms (cont'd)

| Acronym | Definition |
|---------|------------|
| SBC | SCSI Block Commands |
| SID | Segment ID |
| SDU | Service Data Unit |
| SPC | SCSI Primary Commands |
| TB | Terabyte |
| T_PDU | MIPI Unipro Protocol Data Unit |
| T_SDU | MIPI Unipro protocol Service Data Unit |
| UFS | Universal Flash Storage |
| UMPC | Ultra-Mobile PC |
| UniPro | Unified Protocol |
| UPIU | UFS Protocol Information Unit |
| UTP | UFS Transport Protocol |

## 3.2 Conventions

This standard follows some conventions used in SCSI documents since it adopts several SCSI standards.

A binary number is represented in this standard by any sequence of digits consisting of only the Western-Arabic numerals 0 and 1 immediately followed by a lower-case b (e.g., 0101b). Spaces may be included in binary number representations to increase readability or delineate field boundaries (e.g., 0 0101 1010b).

A hexadecimal number is represented in this standard by any sequence of digits consisting of only the Western-Arabic numerals 0 through 9 and/or the upper-case English letters A through F immediately followed by a lower-case h (e.g., FA23h). Spaces may be included in hexadecimal number representations to increase readability or delineate field boundaries (e.g., B FDBC FA23h).

A decimal number is represented in this standard by any sequence of digits consisting of only the Western-Arabic numerals 0 through 9 not immediately followed by a lower-case b or lower-case h (e.g., 25).

A range of numeric values is represented in this standard in the form "a to z", where a is the first value included in the range, all values between a and z are included in the range, and z is the last value included in the range (e.g., the representation "0h to 3h" includes the values 0h, 1h, 2h, and 3h).

When the value of the bit or field is not relevant, x or xx appears in place of a specific value.

The first letter of the name of a Flag is a lower-case f (e.g., fMyFlag).

The first letter of the name of a parameter included in a Descriptor or the first letter of the name of an Attribute is:
• a lower-case b if the parameter or the Attribute size is one byte (e.g., bMyParameter),
• a lower-case w if the parameter or the Attribute size is two bytes (e.g., wMyParameter),
• a lower-case l if the parameter or the Attribute size is four bytes (e.g., dMyParameter),
• a lower-case q if the parameter or the Attribute size is eight bytes (e.g., qMyParameter).

# JEDEC Standard No. 220G
## Page 6

### 3.3 Keywords

Several keywords are used to differentiate levels of requirements and options, as follow:

**Can** - A keyword used for statements of possibility and capability, whether material, physical, or causal (*can* equals *is able to*).

**Expected** - A keyword used to describe the behavior of the hardware or software in the design models assumed by this standard. Other hardware and software design models may also be implemented.

**Ignored** - A keyword that describes bits, bytes, quadlets, or fields whose values are not checked by the recipient.

**Mandatory** - A keyword that indicates items required to be implemented as defined by this standard.

**May** - A keyword that indicates a course of action permissible within the limits of the standard (*may* equals *is permitted*).

**Must** - The use of the word *must* is deprecated and shall not be used when stating mandatory requirements; *must* is used only to describe unavoidable situations.

**Obsolete** - A keyword indicating that an item was defined in prior standards but has been removed from this standard.

**Optional** - A keyword that describes features which are not required to be implemented by this standard. However, if any optional feature defined by the standard is implemented, it shall be implemented as defined by the standard.

**Reserved** - A keyword used to describe objects—bits, bytes, and fields—or the code values assigned to these objects in cases where either the object or the code value is set aside for future standardization. Usage and interpretation may be specified by future extensions to this or other standards. A reserved object shall be zeroed or, upon development of a future standard, set to a value specified by such a standard. The recipient of a reserved object shall not check its value. The recipient of a defined object shall check its value and reject reserved code values.

**Shall** - A keyword that indicates a mandatory requirement strictly to be followed in order to conform to the standard and from which no deviation is permitted (*shall* equals *is required to*). Designers are required to implement all such mandatory requirements to assure interoperability with other products conforming to this standard.

**Should** - A keyword used to indicate that among several possibilities one is recommended as particularly suitable, without mentioning or excluding others; or that a certain course of action is preferred but not necessarily required; or that (in the negative form) a certain course of action is deprecated but not prohibited (*should* equals *is recommended that*).

**Will** - The use of the word *will* is deprecated and shall not be used when stating mandatory requirements; *will* is only used in statements of fact.

### 3.4 Abbreviations

**etc.** - And so forth (Latin: et cetera)

**e.g.** - For example (Latin: exempli gratia)

**i.e.** - That is (Latin: id est)