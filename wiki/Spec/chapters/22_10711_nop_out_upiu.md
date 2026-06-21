# 10.7.11 NOP OUT UPIU

The Initiator device may use NOP OUT UPIU to check the connection to a device. The Target device will respond to a NOP OUT UPIU sending a NOP IN UPIU back to the Initiator device.

## Table 10.61 — NOP OUT UPIU

| **NOP OUT UPIU** |
|------------------|

| 0 | 1 | 2 | 3 |
|---|---|---|---|
| xx00 0000b | Flags | Reserved | Task Tag |
| **4** | **5** | **6** | **7** |
| Reserved | Reserved | Reserved (MSB) | Reserved (LSB) |
| **8** | **9** | **10** | **11** |
| Total EHS Length (00h) | Reserved | Data Segment Length (0000h) |  |
| **12** | **13** | **14** | **15** |
|  |  | Reserved |  |
| **16** | **17** | **18** | **19** |
|  |  | Reserved |  |
| **20** | **21** | **22** | **23** |
|  |  | Reserved |  |
| **24** | **25** | **26** | **27** |
|  |  | Reserved |  |
| **28** | **29** | **30** | **31** |
|  |  | Reserved |  |
| **32** (MSB) | **33** | **34** | **35** (LSB) |
|  |  | Header E2ECRC (omit if HD=0) |  |

---

*JEDEC Standard No. 220G*  
*Page 147*

# JEDEC Standard No. 220G
## Page 148

### 10.7.11.1 Basic Header

The first 12 bytes of the NOP OUT UPIU contain the Basic Header as described in 10.6.2, Basic Header Format. Specific details are as follows:

**a) Task Tag**

Task Tag normally is related to I_T_L_Q nexus addressing of SCSI while here it is used in a pure UTP (device level) context.

**b) Transaction Type**

A type code value of x\00 00000b indicates a NOP OUT UPIU.

**c) Flags**

The Flags field value shall be equal to zero.

**d) Data Segment Length**

The Data Segment Length field shall contain zero as there is no Data Segment in this UPIU.