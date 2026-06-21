# JEDEC Standard No. 220G
## Page 132

### 10.7.9 QUERY RESPONSE UPIU

The QUERY RESPONSE UPIU is used to transfer data between the Target device and Initiator device in response to a QUERY REQUEST UPIU.

The QUERY RESPONSE UPIU is used to return parametric data to the requesting Initiator device in case of read descriptor/attribute/flag query request, or to provide response to write descriptor/attribute query request or set/clear/toggle flag query request.

#### Table 10.46 — QUERY RESPONSE

| **QUERY RESPONSE UPIU** |||||
|---|---|---|---|---|
| 0 | 1 | 2 | 3 |
| xx11 0110b | Flags | Reserved | Task Tag |
| 4 | 5 | 6 | 7 |
| Reserved | Query Function | Query Response | Reserved |
| 8 | 9 | 10 | 11 |
| Total EHS Length (00h) | Device Information | (MSB) | (LSB) |
| | | Data Segment Length |
| 12 | 13 | 14 | 15 |
| | Transaction Specific Fields |
| 16 | 17 | 18 | 19 |
| | Transaction Specific Fields |
| 20 | 21 | 22 | 23 |
| | Transaction Specific Fields |
| 24 | 25 | 26 | 27 |
| | Transaction Specific Fields |
| 28 | 29 | 30 | 31 |
| | Reserved |
| | Header E2ECRC (omit if HD=0) |
| k | k+1 | k+2 | k+3 |
| Data[0] | Data[1] | Data[2] | Data[3] |
| … | … | … | … |
| k+ Length-4 | k+ Length-3 | k+ Length-2 | k+ Length-1 |
| Data[Length - 4] | Data[Length - 3] | Data[Length - 2] | Data[Length - 1] |
| | Data E2ECRC (omit if DD=0) |

The QUERY RESPONSE UPIU follows the general UPIU format a field defined for query function. The transaction specific fields are defined specifically for each type of operation.

The Data Segment Area is optional depending upon the Query Function value. The Data Segment Length field will be set to zero if there is no data segment in the packet.

# JEDEC Standard No. 220G
Page 133

## 10.7.9.1 Overview

The Query Response function will respond to the query function that was sent from the Initiator device in the QUERY REQUEST UPIU. The Query Response may or may not return data depending upon the function. If data needs to be returned it will be returned in the Data Segment of the UPIU or one of the Transaction Specific Fields.

## 10.7.9.2 Query Function

The Query Function field will contain the original query function value that was received in the corresponding QUERY REQUEST UPIU.

## 10.7.9.3 Query Response

The Query Response field indicates the completion code of the action taken in response to the QUERY REQUEST UPIU. Possible values are listed in Table 10.47.

NOTE In case of unsuccessful operation, the Target device may either set Query Response field to FFh, or optionally provide more detailed information about the failure using one of the other values.

### Table 10.47 — Query Response Code

| Value | Description |
|-------|-------------|
| 00h | Success |
| 01h-F5h | Reserved |
| F6h | Parameter not readable |
| F7h | Parameter not writeable |
| F8h | Parameter already written (1) |
| F9h | Invalid LENGTH |
| FAh | Invalid value (2) |
| FBh | Invalid SELECTOR |
| FCh | Invalid INDEX |
| FDh | Invalid IDN |
| FEh | Invalid OPCODE |
| FFh | General failure |

NOTE 1 This value applies to parameters with "Write once" or "Power on reset" write access property.

NOTE 2 This value applies to the following operations: write descriptor, write attribute, set flag, clear flag.

# JEDEC Standard No. 220G
Page 134

## 10.7.9.4 Device Information

See Device Information field definition in RESPONSE UPIU, 10.7.3.2 Basic Header.

## 10.7.9.5 Transaction Specific Fields

The transaction specific fields are defined specifically for each type of operation. For the STANDARD READ REQUEST and STANDARD WRITE REQUEST, the operation specific fields are defined as in Table 10.48.

### Table 10.48 — Transaction Specific Fields

| Transaction Specific Fields for Standard Read/Write Request |
|---|---|---|---|---|
| 12 | 13 | 14 | 15 |
| OPCODE | OSF[0] | OSF[1] | OSF[2] |
| 16 | 17 | 18 (MSB) | 19 (LSB) |
| OSF[3] | OSF[4] | CSF[5] |
| 20 (MSB) | 21 | 22 | 23 (LSB) |
| | | OSF[6] |
| 24 (MSB) | 25 | 26 | 27 (LSB) |
| | | OSF[7] |

**a) OPCODE**

The opcode indicates the operation to perform. Possible opcode values are listed in Table 10.36.

If in a QUERY REQUEST UPIU, the Query Function field is set to STANDARD READ REQUEST and the OPCODE field is set to WRITE DESCRIPTOR, WRITE ATTRIBUTE, SET FLAG, CLEAR FLAG, or TOGGLE FLAG; then the query request shall fail and the Query Response field shall be set to either "Invalid OPCODE" or "General failure".

If in a QUERY REQUEST UPIU, the Query Function field is set to STANDARD WRITE REQUEST and the OPCODE field is set to READ DESCRIPTOR, READ ATTRIBUTE, or READ FLAG; then the query request shall fail and the Query Response field shall be set to either "Invalid OPCODE" or "General failure".

**b) OSF**

The OSF field is an Opcode Specific Field. The OSF fields will be defined for each specific OPCODE.

# 10.7.9.6 Read Descriptor Opcode

The READ DESCRIPTOR OPCODE is used to retrieve a UFS DESCRIPTOR from the Target device. A descriptor can be a fixed or variable length. There are up to 256 possible descriptor types. The OSF fields are used to select a particular descriptor and to read a number of descriptor bytes. The OSF fields are defined in Table 10.49.

The READ DESCRIPTOR OPCODE is returned in response to a QUERY REQUEST UPIU containing the same value in the OPCODE field.

## Table 10.49 — Read Descriptor

| **Transaction Specific Fields for READ DESCRIPTOR OPCODE** |
|---|
| **12** | **13** | **14** | **15** |
| 01h | DESCRIPTOR IDN | INDEX (MSB) | SELECTOR (LSB) |
| **16** | **17** | **18** | **19** |
| Reserved | Reserved |  | LENGTH |
| **20** | **21** | **22** | **23** |
|  |  | Reserved |  |
| **24** | **25** | **26** | **27** |
|  |  | Reserved |  |

### a) DESCRIPTOR IDN

The DESCRIPTOR IDN field contains the same DESCRIPTOR IDN value sent from the corresponding QUERY REQUEST UPIU.

### b) INDEX

The Index field value returned is the same INDEX value of the corresponding QUERY REQUEST UPIU.

### c) SELECTOR

The SELECTOR field returned is the same SELECTOR value of the corresponding QUERY REQUEST UPIU.

### d) LENGTH

The LENGTH field is used to indicate the number of bytes returned in response to the corresponding QUERY REQUEST UPIU. This value could be less than the requested size, if the size of the data item is smaller than the size requested in the corresponding QUERY REQUEST UPIU.

### e) Data Segment

The Data Segment area contains the descriptor data.

---

*JEDEC Standard No. 220G*  
*Page 135*

# 10.7.9.7 Write Descriptor Opcode

The WRITE DESCRIPTOR OPCODE is used to respond to a write descriptor query request. A descriptor can be a fixed or variable length. There are up to 256 possible descriptor types. The OSF fields are used to select a particular descriptor. The OSF fields are defined in Table 10.50.

## Table 10.50 — Write Descriptor

**Transaction Specific Fields for WRITE DESCRIPTOR OPCODE**

| 12 | 13 | 14 | 15 |
|---|---|---|---|
| 02h | DESCRIPTOR IDN | INDEX (MSB) | SELECTOR (LSB) |
| 16 | 17 | 18 | 19 |
| Reserved | Reserved | | LENGTH |
| 20 | 21 | 22 | 23 |
| | | Reserved | |
| 24 | 25 | 26 | 27 |
| | | Reserved | |

### a) DESCRIPTOR IDN

The Descriptor IDN field contains the same DESCRIPTOR IDN value sent from the corresponding QUERY REQUEST UPIU.

### b) INDEX

The Index field value returned is the same INDEX value of the corresponding QUERY REQUEST UPIU.

### c) SELECTOR

The SELECTOR field returned is the same SELECTOR value of the corresponding QUERY REQUEST UPIU.

### d) LENGTH

The LENGTH field is used to indicate the number of descriptor bytes written. Only the entire descriptor may be written; there is no partial write or update possible.

### e) Data Segment

The Data Segment area is empty.

---

*JEDEC Standard No. 220G*  
*Page 136*

# 10.7.9.8 Read Attribute Opcode

The READ ATTRIBUTE OPCODE is used to retrieve a UFS attribute from the Target device. Attribute size can be from 1-bit to 64-bit. There are up to 256 possible attributes, identified by an identification number, IDN, which ranges from 0 to 255.

The response to a READ ATTRIBUTE request will be returned in a QUERY RESPONSE UPIU. A success or failure code for the entire operation will be contained within the RESPONSE field.

The attribute data will be returned within the transaction specific fields. The Transaction Specific fields are formatted as indicated in Table 10.51. The first two 32-bit words of those fields will echo the first 32-bit word of the transaction specific fields of the QUERY REQUEST UPIU. The second and third words will contain the Attribute data.

## Table 10.51 — Read Attribute Response Data Format

| | Transaction Specific Fields for READ ATTRIBUTE OPCODE | | |
|--|--|--|--|
| 12 | 13 | 14 | 15 |
| 03h | ATTRIBUTE IDN | INDEX | SELECTOR |
| 16 (MSB) | 17 | 18 | 19 |
| VALUE [63:56] | VALUE [55:48] | VALUE [47:40] | VALUE [39:32] |
| 20 | 21 | 22 | 23 (LSB) |
| VALUE [31:24] | VALUE [23:16] | VALUE [15:8] | VALUE [7:0] |
| 24 | 25 | 26 | 27 |
| | | Reserved | |

**a) ATTRIBUTE IDN**

The ATTRIBUTE IDN field contains the same ATTRIBUTE IDN value sent from the corresponding QUERY REQUEST UPIU.

**b) INDEX**

The Index field value returned is the same INDEX value of the corresponding QUERY REQUEST UPIU.

**c) SELECTOR**

The SELECTOR field returned is the same SELECTOR value of the corresponding QUERY REQUEST UPIU.

**d) VALUE [63:0]**

The 64-bit VALUE field contains the data value of the ATTRIBUTE. The VALUE is a right justified, big Endian value. Unused upper bits shall be set to zero.

**e) Data Segment**

The Data Segment area is empty.

---
*JEDEC Standard No. 220G*  
*Page 137*

# 10.7.9.9 Write Attribute Opcode

The WRITE ATTRIBUTE OPCODE is used to respond to a write attribute query request. Attribute size can be from 1-bit to 64-bit. There are up to 256 possible attributes, identified by an identification number, IDN, which ranges from 0 to 255. The OSF fields for this opcode are listed in Table 10.52

## Table 10.52 — Write Attribute

**Transaction Specific Fields for WRITE ATTRIBUTE OPCODE**

| 12 | 13 | 14 | 15 |
|----|----|----|----| 
| | 04h | ATTRIBUTE IDN | INDEX | SELECTOR |
| 16 | 17 | 18 | 19 |
| (MSB) | | | |
| VALUE [63:56] | VALUE [55:48] | VALUE [47:40] | VALUE [39:32] |
| 20 | 21 | 22 | 23 |
| VALUE [31:24] | VALUE [23:16] | VALUE [15:8] | (LSB) VALUE [7:0] |
| 24 | 25 | 26 | 27 |
| | | Reserved | |

**a) ATTRIBUTE IDN**

The ATTRIBUTE IDN field contains the same ATTRIBUTE IDN value sent from the corresponding QUERY REQUEST UPIU.

**b) INDEX**

The Index field value returned is the same INDEX value of the corresponding QUERY REQUEST UPIU.

**c) SELECTOR**

The SELECTOR field returned is the same SELECTOR value of the corresponding QUERY REQUEST UPIU.

**d) VALUE [63:0]**

This field contains the same data provided in write attribute query request.

**e) Data Segment**

The Data Segment area is empty.

# 10.7.9.9.1 Read Flag Opcode

The READ FLAG OPCODE is used to retrieve a UFS FLAG value from the Target device. A FLAG is a fixed size single byte value that represents a Boolean value. There can be defined up to 256 possible FLAG values. A FLAG is identified by its FLAG IDN, an identification number that ranges in value from 0 to 255. The FLAG data, either '1' or '0', is returned within the Transaction Specific Fields area of a QUERY RESPONSE UPIU packet.

The response to a READ ATTRIBUTE request will be returned in a QUERY RESPONSE UPIU. A success or failure code for the entire operation will be contained within the RESPONSE field.

The attribute data will be returned within the transaction specific fields. The Transaction Specific fields are formatted as indicated in Table 10.53. The first two 32-bit words of those fields will echo the first two 32-bit words of the transaction specific fields of the QUERY REQUEST UPIU. The third word will contain the FLAG data, a '0' or '1' value.

## Table 10.53 — Read Flag Response Data Format

| Transaction Specific Fields for READ FLAG OPCODE |     |     |     |
|---|---|---|---|
| 12 | 13 | 14 | 15 |
| 05h | FLAG IDN | INDEX | SELECTOR |
| 16 | 17 | 18 | 19 |
| Reserved | Reserved | Reserved | Reserved |
| 20 | 21 | 22 | 23 |
| Reserved | Reserved | Reserved | FLAG VALUE |
| 24 | 25 | 26 | 27 |
|  |  | Reserved |  |

**a) FLAG IDN**

The FLAG IDN field contains the same FLAG IDN value sent from the corresponding QUERY REQUEST UPIU

**b) INDEX**

The Index field value returned is the same INDEX value of the corresponding QUERY REQUEST UPIU.

**c) SELECTOR**

The SELECTOR field returned is the same SELECTOR value of the corresponding QUERY REQUEST UPIU

**d) FLAG VALUE**

The FLAG VALUE field contains the FLAG data: 00h or 01h.

**e) Data Segment**

The Data Segment area is empty.

---
*JEDEC Standard No. 220G*  
*Page 139*

# JEDEC Standard No. 220G
Page 140

## 10.7.9.10 Set Flag

### Table 10.54 — Set Flag
**Transaction Specific Fields for SET FLAG OPCODE**

| 12 | 13 | 14 | 15 |
|----|----|----|----|
| 06h | FLAG IDN | INDEX | SELECTOR |
| 16 | 17 | 18 | 19 |
| Reserved | Reserved | Reserved | Reserved |
| 20 | 21 | 22 | 23 |
| Reserved | Reserved | Reserved | FLAG VALUE |
| 24 | 25 | 26 | 27 |
| | | Reserved | |

**a) FLAG IDN**

The FLAG IDN field contains the same FLAG IDN value sent from the corresponding QUERY REQUEST UPIU

**b) INDEX**

The INDEX field value returned is the same INDEX value of the corresponding QUERY REQUEST UPIU.

**c) SELECTOR**

The SELECTOR field returned is the same SELECTOR value of the corresponding QUERY REQUEST UPIU.

**d) FLAG VALUE**

The FLAG VALUE field contains the FLAG data: 00h or 01h.
This field is valid only if the Query Response field indicates that the operation has been successfully completed ("Success").

**e) Data Segment**

The Data Segment area is empty.

# 10.7.9.11 Clear Flag

## Table 10.55 — Clear Flag

### Transaction Specific Fields for CLEAR FLAG OPCODE

| 12 | 13 | 14 | 15 |
|----|----|----|----| 
| 07h | FLAG IDN | INDEX | SELECTOR |
| 16 | 17 | 18 | 19 |
| Reserved | Reserved | Reserved | Reserved |
| 20 | 21 | 22 | 23 |
| Reserved | Reserved | Reserved | FLAG VALUE |
| 24 | 25 | 26 | 27 |
| | | Reserved | |

**a) FLAG IDN**

The FLAG IDN field contains the same FLAG IDN value sent from the corresponding QUERY REQUEST UPIU

**b) INDEX**

The Index field value returned is the same INDEX value of the corresponding QUERY REQUEST UPIU.

**c) SELECTOR**

The SELECTOR field returned is the same SELECTOR value of the corresponding QUERY REQUEST UPIU.

**d) FLAG VALUE**

The FLAG VALUE field contains the FLAG data: 00h or 01h.

This field is valid only if the Query Response field indicates that the operation has been successfully completed ("Success").

**e) Data Segment**

The Data Segment area is empty.

---

JEDEC Standard No. 220G
Page 141

# JEDEC Standard No. 220G
Page 142

## 10.7.9.12 Toggle Flag

### Table 10.56 — Toggle Flag

| Transaction Specific Fields for TOGGLE FLAG OPCODE |
|---|---|---|---|
| 12 | 13 | 14 | 15 |
| 08h | FLAG IDN | INDEX | SELECTOR |
| 16 | 17 | 18 | 19 |
| Reserved | Reserved | Reserved | Reserved |
| 20 | 21 | 22 | 23 |
| Reserved | Reserved | Reserved | FLAG VALUE |
| 24 | 25 | 26 | 27 |
|  |  | Reserved |  |

a) **FLAG IDN**

   The FLAG IDN field contains the same FLAG IDN value sent from the corresponding QUERY REQUEST UPIU.

b) **INDEX**

   The Index field value returned is the same INDEX value of the corresponding QUERY REQUEST UPIU.

c) **SELECTOR**

   The SELECTOR field returned is the same SELECTOR value of the corresponding QUERY REQUEST UPIU

d) **FLAG VALUE**

   The FLAG VALUE field contains the FLAG data: 00h or 01h.

   This field is valid only if the Query Response field indicates that the operation has been successfully completed ("Success").

e) **Data Segment**

   The Data Segment area is empty.

# JEDEC Standard No. 220G
## Page 143

### 10.7.9.13 NOP

Table 10.57 defines NOP OPCODE for QUERY RESPONSE UPIU.

#### Table 10.57 — NOP

**Transaction Specific Fields for NOP FLAG OPCODE**

| 12 | 13 | 14 | 15 |
|----|----|----|---- |
| 00h | Reserved | Reserved | Reserved |

| 16 | 17 | 18 | 19 |
|----|----|----|---- |
| Reserved | Reserved | Reserved | Reserved |

| 20 | 21 | 22 | 23 |
|----|----|----|---- |
|  | | Reserved | |

| 24 | 25 | 26 | 27 |
|----|----|----|---- |
|  |  | Reserved | |

**a) Data Segment**

The Data Segment area is empty.