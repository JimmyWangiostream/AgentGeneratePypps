# 10.7.12 NOP IN UPIU

NOP IN UPIU is the response from the Target device to a NOP OUT UPIU sent by the Initiator device.

## Table 10.62 — NOP IN UPIU

| Byte | 0 | 1 | 2 | 3 |
|------|---|---|---|---|
| **0** | xx10 0000b | Flags | Reserved | Task Tag |
| **4** | Reserved | Reserved | Reserved | Reserved |
| **8** | Total EHS Length (00h) | Device Information (00h) | Response (00h) (MSB) | Reserved (LSB) |
| | | | Data Segment Length (0000h) | |
| **12** | | **13** | **14** | **15** |
| | | | Reserved | |
| **16** | | **17** | **18** | **19** |
| | | | Reserved | |
| **20** | | **21** | **22** | **23** |
| | | | Reserved | |
| **24** | | **25** | **26** | **27** |
| | | | Reserved | |
| **28** | | **29** | **30** | **31** |
| | | | Reserved | |
| **32** | (MSB) | **33** | **34** | **35** (LSB) |
| | | Header E2ECRC (omit if HD=0) | | |

---
*JEDEC Standard No. 220G*  
*Page 149*

# JEDEC Standard No. 220G
Page 150

## 10.7.12.1 Basic Header

The first 12 bytes of the NOP IN UPIU contain the Basic Header as described in 10.6.2, Basic Header Format. Specific details are as follows:

**a) Transaction Type**

A type code value of xx10 0000b indicates a NOP IN UPIU.

**b) Flags**

The Flags field value shall be equal to zero.

**c) Task Tag**

The Task Tag shall be equal to the Task Tag value of the corresponding NOP OUT UPIU.

**d) Response**

The Response field shall be set to 00h (Target Success) indicating that the Target device was able to respond to the NOP OUT UPIU.

**e) Data Segment Length**

The Data Segment Length field shall contain zero as there is no Data Segment in this UPIU.