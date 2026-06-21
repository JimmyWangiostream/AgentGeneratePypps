# JEDEC Standard No. 220G
Page 119

## 10.7.8 QUERY REQUEST UPIU

The QUERY REQUEST UPIU is used to transfer data between the Initiator device and Target device that is outside domain of standard user data transfers for command read and write.

The QUERY REQUEST UPIU can be used to read and write parametric data to or from the Target device. It can be used to get information for configuration or enumeration, to set or clear bus or overall device conditions, to set or reset global flag values, parameters or attributes, to set or get power or bus or network information or to get or set descriptors, to get serial numbers or GUID's (globally unique identifiers), etc.

The Target device will send a QUERY RESPONSE UPIU in response to a QUERY REQUEST UPIU. After sending a QUERY REQUEST UPIU the Initiator device shall not send a new QUERY REQUEST UPIU until it receives the QUERY RESPONSE UPIU for the pending request. If the Target device receives a QUERY REQUEST UPIU while it is still processing a previous QUERY REQUEST UPIU, it shall ignore the latest request.

The QUERY REQUEST UPIU follows the general UPIU format with a field defined for query function. The Transaction Specific Fields are defined specifically for each type of operation.

The Data Segment Area is optional depending upon the query function value. The Data Segment Length field will be set to zero if there is no data segment in the packet.

### Table 10.33 — QUERY REQUEST UPIU

| QUERY REQUEST UPIU | | | |
|---|---|---|---|
| 0 | 1 | 2 | 3 |
| xx01 0110b | Flags | Reserved | Task Tag |
| 4 | 5 | 6 | 7 |
| Reserved | Query Function | Reserved | Reserved |
| 8 | 9 | 10 (MSB) | 11 (LSB) |
| Total EHS Length (00h) | Reserved | Data Segment Length | |
| 12 | 13 | 14 | 15 |
| | Transaction Specific Fields | | |
| 16 | 17 | 18 | 19 |
| | Transaction Specific Fields | | |
| 20 | 21 | 22 | 23 |
| | Transaction Specific Fields | | |
| 24 | 25 | 26 | 27 |
| | Transaction Specific Fields | | |
| 28 | 29 | 30 | 31 |
| | Reserved | | |
| | Header E2ECRC (omit if HD=0) | | |
| k | k+1 | k+2 | k+3 |
| Data[0] | Data[1] | Data[2] | Data[3] |
| ... | ... | ... | ... |
| k+ Length-4 | k+ Length-3 | k+ Length-2 | k+ Length-1 |
| Data[Length - 4] | Data[Length - 3] | Data[Length - 2] | Data[Length - 1] |
| | Data E2ECRC (omit if DD=0) | | |

# JEDEC Standard No. 220G
Page 120

## 10.7.8.1 Overview

Queries are used to read and write data structures between the host and the device. This data is outside the scope of normal device reads or writes; data that would be considered system data, configuration data, production information, descriptors, special parameters and flags and other.

For UFS the query function will generally be used to read or write Descriptors, Attributes and Flags. There are also a range of Vendor Specific operations that can be used to transfer vendor specific data between host and device.

All these items reside within the device memory and used by the device to control or define its operation.

The following is a short overview of the most common data structures that are transferred using the Query Request function. Please see the related sub-clauses for more detail on these data structures:

**a) Descriptors**

A Descriptor is a block or page of parameters that describe something about a Device. For example, there are Device Descriptors, Configuration Descriptors, Unit Descriptors, etc.

**b) Attributes**

An Attribute is a single parameter that represents a specific range of numeric values that can be set or read. This value could be a byte or word or floating point number. For example, baud rate or block size would be an attribute. Attribute size can be from 1-bit to 64-bit. Attributes of the same type can be organized in arrays, each element of them identified by an index.

**c) Flags**

A Flag is a single Boolean value that represents a TRUE or FALSE, '0' or '1', ON or OFF type of value. A Flag can be cleared or reset, set, toggled or read. Flags are useful to enable or disable certain functions or modes or states within the device.

# JEDEC Standard No. 220G
## Page 121

### 10.7.8.2 Query Function

The Query Function field holds the requested query type describing the query function to perform. Common query functions are listed in Table 10.34. Currently, there are two general query functions defined: Read Request and Write Request. Additional Transaction Specific Fields will be used to specify further information needed for the transaction. These fields can describe the specific operation to perform, the target data or information to access, the amount of data to transfer and additional parameters and data.

#### Table 10.34 — Query Function Field Values

| QUERY FUNCTION |  |
|---|---|
| 00h | Reserved |
| 01h | STANDARD READ REQUEST |
| 02h-3Fh | Reserved |
| 40-7Fh | Vendor Specific Read Functions |
| 80h | Reserved |
| 81h | STANDARD WRITE REQUEST |
| 82h-BFh | Reserved |
| C0h-FFh | Vendor Specific Write Functions |

**a) Standard Read Request**

The Standard Read Request function type is used to read requested information from a Target device. The Target device will return the requested information to the Initiator device within a QUERY RESPONSE UPIU packet.

**b) Standard Write Request**

The Standard Write Request function type is used to write information and data to a Target device. The information and data to write to the Target device will be included within the Data Segment field of the QUERY REQUEST UPIU packet.

# JEDEC Standard No. 220G
Page 122

## 10.7.8.3 Transaction Specific Fields

The transaction specific fields are defined specifically for each type of operation. For the STANDARD READ REQUEST and STANDARD WRITE REQUEST, the operation specific fields are defined as in Table 10.35.

### Table 10.35 — Transaction Specific Fields

**Transaction Specific Fields for Standard Read/Write Request**

| 12 | 13 | 14 | 15 |
|---|---|---|---|
| OPCODE | OSF[0] | OSF[1] | OSF[2] |
| 16 | 17 | 18 | 19 |
| OSF[3] | OSF[4] | (MSB) | (LSB) |
| 20 | 21 | 22 | 23 |
| (MSB) | | OSF[5] | (LSB) |
| | | OSF[6] | |
| 24 | 25 | 26 | 27 |
| (MSB) | | OSF[7] | (LSB) |

**a) OPCODE**

The opcode indicates the operation to perform. Possible opcode values are listed in Table 10.36.

### Table 10.36 — Query Function Opcode Values

| OPCODE | Operation | QUERY FUNCTION |
|--------|-----------|----------------|
| 00h | NOP | Any value |
| 01h | READ DESCRIPTOR | STANDARD READ REQUEST |
| 02h | WRITE DESCRIPTOR | STANDARD WRITE REQUEST |
| 03h | READ ATTRIBUTE | STANDARD READ REQUEST |
| 04h | WRITE ATTRIBUTE | STANDARD WRITE REQUEST |
| 05h | READ FLAG | STANDARD READ REQUEST |
| 06h | SET FLAG | STANDARD WRITE REQUEST |
| 07h | CLEAR FLAG | STANDARD WRITE REQUEST |
| 08h | TOGGLE FLAG | STANDARD WRITE REQUEST |
| 09h-EFh | Reserved | Reserved |
| F0h-FFh | Vendor Specific | Vendor Specific |

**b) OSF**

The OSF field is an Opcode Specific Field. The OSF fields will be defined for each specific OPCODE.

# 10.7.8.4 Read Descriptor Opcode

The READ DESCRIPTOR OPCODE is used to retrieve a UFS Descriptor from the Target device. A descriptor can be a fixed or variable length. There are up to 256 possible descriptor types. The OSF fields are used to select a particular descriptor and to read a number of descriptor bytes. The OSF fields are defined in Table 10.37.

## Table 10.37 — Read Descriptor

| **Transaction Specific Fields for READ DESCRIPTOR OPCODE** |
|---|
| **12** | **13** | **14** | **15** |
| 01h | DESCRIPTOR IDN | INDEX | SELECTOR |
| **16** | **17** | **18** | **19** |
| Reserved | Reserved | (MSB) | (LSB) |
| | | LENGTH | |
| **20** | **21** | **22** | **23** |
| | | Reserved | |
| **24** | **25** | **26** | **27** |
| | | Reserved | |

**a) DESCRIPTOR IDN**

The Descriptor IDN field contains a value that indicates the particular type of descriptor to retrieve. For example, it could indicate a Device Descriptor or Unit Descriptor or String Descriptor. Some descriptor types are unique and can be fully identified by the Descriptor Type value. Other descriptors can exist in multiple forms, such as String Descriptors, and they are furthered identified with subsequent fields.

**b) INDEX**

The Index value is used to further identify a particular descriptor. For example, there may be multiple String Descriptors defined. In the case of multiple descriptors the INDEX field is used to select a particular one. Multiple descriptors are indexed starting from 0 through 255. The actual index value for a particular descriptor will be provided by other means, usually contained within a field of some other related descriptor.

**c) SELECTOR**

The SELECTOR field may be needed to further identify a particular descriptor.

**d) LENGTH**

The LENGTH field is used to indicate the number of bytes to read of the descriptor. These bytes will be returned in a QUERY RESPONSE UPU packet. This is the requested length to read, which may be less than, or equal to, or greater than the number of bytes within the actual descriptor. If less than, or equal to the actual descriptor size, the number of bytes specified will be returned. If the LENGTH is greater than the descriptor size, the response will provide the exact descriptor size in the LENGTH field of the QUERY RESPONSE UPIU.

**e) Data Segment**

The Data Segment area is empty.

---
*JEDEC Standard No. 220G*
*Page 123*

# 10.7.8.5 Write Descriptor Opcode

The WRITE DESCRIPTOR OPCODE is used to write a UFS Descriptor and it is sent from the host to the device. A descriptor can be a fixed or variable length. There are up to 256 possible descriptor types. The OSF fields are used to select a particular descriptor. The OSF fields are defined as listed in Table 10.38.

## Table 10.38 — Write Descriptor

**Transaction Specific Fields for WRITE DESCRIPTOR OPCODE**

| 12 | 13 | 14 | 15 |
|----|----|----|----| 
| 02h | DESCRIPTOR IDN | INDEX (MSB) | SELECTOR (LSB) |
| 16 | 17 | 18 | 19 |
| Reserved | Reserved |  | LENGTH |
| 20 | 21 | 22 | 23 |
|  |  | Reserved |  |
| 24 | 25 | 26 | 27 |
|  |  | Reserved |  |

**a) DESCRIPTOR IDN**

The Descriptor IDN field contains a value that identifies a particular of descriptor to write. For example, it could indicate a Device Descriptor or Unit Descriptor or String Descriptor. Some descriptor types are unique and can be fully identified by the Descriptor IDN value. Other descriptors can exist in multiple forms, such as STRING DESCRIPTORS, and they are furthered identified with subsequent fields.

**b) INDEX**

The Index value is used to further identify a particular descriptor. For example, there may be multiple String Descriptors defined. In the case of multiple descriptors the INDEX field is used to select a particular one. Multiple descriptors are indexed starting from 0 through 255. The actual index value for a particular descriptor will be provided by other means, usually contained within a field of some other related descriptor.

**c) SELECTOR**

The SELECTOR field may be needed to further identify a particular descriptor.

**d) LENGTH**

The LENGTH field is used to indicate the number of descriptor bytes to write. Only the entire descriptor may be written; there is no partial write or update possible. These bytes will be contained within the DATA SEGMENT area of the QUERY REQUEST UPIU packet. The DATA SEGMENT LENGTH field of the UPIU shall also be set to this same value. If LENGTH is not equal to the descriptor size the operation will fail: the descriptor is not updated and the Query Response field of the QUERY RESPONSE UPIU is set FAILURE.

**e) Data Segment**

The Data Segment area contains the data to be written.

---
*JEDEC Standard No. 220G*  
*Page 124*

# JEDEC Standard No. 220G
Page 125

## 10.7.8.6 Read Attribute Opcode

The READ ATTRIBUTE OPCODE is used to retrieve a UFS Attribute from the Target device. Attribute size can be from 1-bit to 64-bit. There are up to 256 possible Attributes, identified by an identification number, IDN, which ranges from 0 to 255. The OSF fields for this opcode are listed in Table 10.39.

### Table 10.39 — Read Attribute

| | Transaction Specific Fields for READ ATTRIBUTE OPCODE | | |
|---|---|---|---|
| 12 | 13 | 14 | 15 |
| 03h | ATTRIBUTE IDN | INDEX | SELECTOR |
| 16 | 17 | 18 | 19 |
| Reserved | Reserved | Reserved | Reserved |
| 20 | 21 | 22 | 23 |
| 24 | 25 | 26 | 27 |
| | | Reserved | |
| | | Reserved | |

**a) ATTRIBUTE IDN**

The ATTRIBUTE IDN contains a value that identifies a particular Attribute to retrieve from the Target device.

**b) INDEX**

For attributes that are organized in array, the index value is used to identify the particular element. For example, the LUN is used as index to select the particular element of attributes that have logical unit specific values.

The range for the index is defined for each attribute, and it can be from 0 through 255. Index shall be set to zero for attributes composed by single element.

**c) SELECTOR**

The SELECTOR field may be needed to further identify a particular element of an attribute. Selector field shall be set to zero for attributes that do not require it.

**d) Data Segment**

The Data Segment area is empty.

# 10.7.8.7 Write Attribute Opcode

The **WRITE ATTRIBUTE OPCODE** is used to write a UFS Attribute to the Target device. Attribute size can be from 1-bit to 64-bit. There are up to 256 possible Attributes, identified by an identification number, IDN, which ranges from 0 to 255. The OSF fields for this opcode are listed in Table 10.40.

## Table 10.40 — Write Attribute

**Transaction Specific Fields for WRITE ATTRIBUTE OPCODE**

| 12 | 13 | 14 | 15 |
|----|----|----|----| 
| 04h | ATTRIBUTE IDN | INDEX | SELECTOR |
| **16** | **(MSB)** **17** | **18** | **19** |
| VALUE [63:56] | VALUE [55:48] | VALUE [47:40] | VALUE [39:32] |
| **20** | **21** | **22** | **23** **(LSB)** |
| VALUE [31:24] | VALUE [23:16] | VALUE [15:8] | VALUE [7:0] |
| **24** | **25** | **26** | **27** |
| | | Reserved | |

**a) ATTRIBUTE IDN**

The ATTRIBUTE IDN contains a value that identifies a particular Attribute to write in the Target device.

**b) INDEX**

For attributes that are organized in array, the index value is used to identify the particular element. For example, the LUN is used as index to select the particular element of attributes that have logical unit specific values.

The range for the index is defined for each attribute, and it can be from 0 through 255. Index shall be set to zero for attributes composed by single element.

**c) SELECTOR**

The SELECTOR field may be needed to further identify a particular element of an attribute. Selector field shall be set to zero for attributes that do not require it.

**d) VALUE [63:0]**

The 64-bit VALUE field contains the data value of the Attribute. The VALUE is a right justified, big Endian value. Unused upper bits shall be set to zero.

**e) Data Segment**

The Data Segment area is empty.

---

JEDEC Standard No. 220G  
Page 126

# 10.7.8.8 Read Flag Opcode

The READ FLAG OPCODE is used to retrieve a UFS Flag value from the Target device. A Flag is a fixed size single byte value that represents a Boolean value. There can be defined up to 256 possible Flag values. A Flag is identified by the FLAG IDN, an identification number that ranges in value from 0 to 255. The OSF fields for this opcode are listed in Table 10.41.

The FLAG data, either one (01h) or zero (00h), is returned within the Transaction Specific Fields area of a QUERY RESPONSE UPIU packet.

## Table 10.41 — Read Flag

**Transaction Specific Fields for READ FLAG OPCODE**

| 12 | 13 | 14 | 15 |
|----|----|----|----| 
| 05h | FLAG IDN | INDEX | SELECTOR |
| **16** | **17** | **18** | **19** |
| Reserved | Reserved | Reserved | Reserved |
| **20** | **21** | **22** | **23** |
|  |  | Reserved |  |
| **24** | **25** | **26** | **27** |
|  |  | Reserved |  |

**a) FLAG IDN**

The FLAG IDN field contains a value that identifies a particular Flag to retrieve from the Target device.

**b) INDEX**

The index field may be needed to identify a particular element of a flag.

**c) SELECTOR**

The selector field may be needed to further identify a particular element of a flag. Selector field is not used in this version of the standard and its value shall be zero.

**d) Operation**

The Boolean value of the addressed flag is returned in a QUERY RESPONSE UPIU.

**e) Data Segment**

The Data Segment area is empty.

---
JEDEC Standard No. 220G  
Page 127

# JEDEC Standard No. 220G
## Page 128

### 10.7.8.9 Set Flag

#### Table 10.42 — Set Flag

**Transaction Specific Fields for SET FLAG OPCODE**

| 12 | 13 | 14 | 15 |
|----|----|----|----| 
| 06h | FLAG IDN | INDEX | SELECTOR |
| **16** | **17** | **18** | **19** |
| Reserved | Reserved | Reserved | Reserved |
| **20** | **21** | **22** | **23** |
|  |  | Reserved |  |
| **24** | **25** | **26** | **27** |
|  |  | Reserved |  |

**a) FLAG IDN**

The FLAG IDN field contains a value that identifies a particular Flag to set in the Target device.

**b) INDEX**

The index field may be needed to identify a particular element of a flag.

**c) SELECTOR**

The selector field may be needed to further identify a particular element of a flag. Selector field is not used in this version of the standard and its value shall be zero.

**d) Operation**

The Boolean value of the addressed flag is set to TRUE or one.

**e) Data Segment**

The Data Segment area is empty.

# 10.7.8.10 Clear Flag

## Table 10.43 — Clear Flag

**Transaction Specific Fields for CLEAR FLAG OPCODE**

| 12 | 13 | 14 | 15 |
|----|----|----|----| 
|    | 07h | FLAG IDN | INDEX | SELECTOR |
| 16 | 17 | 18 | 19 |
| Reserved | Reserved | Reserved | Reserved |
| 20 | 21 | 22 | 23 |
|    |    | Reserved |    |
| 24 | 25 | 26 | 27 |
|    |    | Reserved |    |

**a) FLAG IDN**

The FLAG IDN field contains a value that identifies a particular Flag to clear in Target device.

**b) INDEX**

The index field may be needed to identify a particular element of a flag.

**c) SELECTOR**

The selector field may be needed to further identify a particular element of a flag. Selector field is not used in this version of the standard and its value shall be zero.

**d) Operation**

The Boolean value of the addressed flag is cleared to FALSE or zero.

**e) Data Segment**

The Data Segment area is empty.

---
*JEDEC Standard No. 220G*  
*Page 129*

# 10.7.8.11 Toggle Flag

## Table 10.44 — Toggle Flag

### Transaction Specific Fields for TOGGLE FLAG OPCODE

| 12 | 13 | 14 | 15 |
|---|---|---|---|
| 08h | FLAG IDN | INDEX | SELECTOR |

| 16 | 17 | 18 | 19 |
|---|---|---|---|
| Reserved | Reserved | Reserved | Reserved |

| 20 | 21 | 22 | 23 |
|---|---|---|---|
|  |  | Reserved |  |

| 24 | 25 | 26 | 27 |
|---|---|---|---|
|  |  | Reserved |  |

**a) FLAG IDN**

The FLAG IDN field contains a value that identifies a particular Flag to toggle in the Target device.

**b) INDEX**

The index field may be needed to identify a particular element of a flag.

**c) SELECTOR**

The selector field may be needed to further identify a particular element of a flag. Selector field is not used in this version of the standard and its value shall be zero.

**d) Operation**

The Boolean value of the addressed flag is set to the negated current value.

**e) Data Segment**

The Data Segment area is empty.

---
*JEDEC Standard No. 220G*
*Page 130*

# JEDEC Standard No. 220G
Page 131

## 10.7.8.12 NOP

Table 10.455 defines NOP OPCODE for QUERY REQUEST UPIU.

### Table 10.45 — NOP

| Transaction Specific Fields for NOP FLAG OPCODE |
|---|---|---|---|
| 12 | 13 | 14 | 15 |
| 00h | Reserved | Reserved | Reserved |
| 16 | 17 | 18 | 19 |
| Reserved | Reserved | Reserved | Reserved |
| 20 | 21 | 22 | 23 |
|  |  | Reserved |  |
| 24 | 25 | 26 | 27 |
|  |  | Reserved |  |

**a) Data Segment**

The Data Segment area is empty.