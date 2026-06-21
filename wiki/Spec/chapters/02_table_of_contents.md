# Table of Contents

This page intentionally left blank.

# JEDEC Standard No. 220G

# UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

## Contents

| | Page |
|---|---|
| **Forword** | -xv- |
| **Introduction** | -xv- |
| **1 Scope** | 1 |
| **2 Normative References** | 2 |
| **3 Terms and Definitions** | 3 |
| 3.1 Acronyms | 4 |
| 3.2 Conventions | 5 |
| 3.3 Keywords | 6 |
| 3.4 Abbreviations | 6 |
| **4 Introduction** | 7 |
| 4.1 General Features | 7 |
| 4.2 Interface Features | 8 |
| 4.3 Functional Features | 8 |
| **5 UFS Architecture Overview** | 9 |
| 5.1 UFS Top Level Architecture | 9 |
| | 5.1.1 Application Layer | 9 |
| | 5.1.2 UFS Device Manager | 9 |
| | 5.1.3 Service Access Points | 10 |
| | 5.1.4 UIO_SAP | 11 |
| | 5.1.5 UDM_SAP | 11 |
| | 5.1.6 UFS Transport Protocol Layer | 11 |
| | 5.1.7 UFS Interconnect Layer | 11 |
| | 5.1.8 UFS Technology | 11 |
| 5.2 UFS System Model | 12 |
| 5.3 System Boot and Enumeration | 12 |
| 5.4 UFS Interconnect (UIC) Layer | 13 |
| | 5.4.1 UFS Physical Layer Signals | 13 |
| | 5.4.2 MIPI UniPro | 13 |
| | 5.4.3 MIPI UniPro Related Attributes | 14 |
| 5.5 UFS Transport Protocol (UTP) Layer | 14 |
| | 5.5.1 Architectural Model | 15 |
| 5.6 UFS Application and Command Layer | 19 |
| 5.7 Mechanical | 20 |
| **6 UFS Electrical Clock, Reset, Signals and Supplies** | 20 |
| 6.1 UFS Signals | 20 |
| 6.2 Reset Signal and LSS Signal | 23 |
| 6.3 Power Supplies | 23 |
| 6.4 Reference Clock | 24 |
| | 6.4.1 HS Gear Rates | 28 |
| | 6.4.2 Host Controller requirements for reference clock generation | 29 |
| 6.5 External Charge Pump Capacitors (Optional) | 30 |
| 6.6 ZQ Calibration Resistor (optional) | 31 |
| 6.7 Absolute Maximum DC Ratings and Operating Conditions | 32 |
| 6.8 AC and DC Operating Conditions | 33 |
| **7 Reset, Power-Up and Power-Down** | 34 |
| 7.1 Reset | 34 |
| | 7.1.1 Power-on Reset | 34 |
| | 7.1.2 Hardware Reset | 35 |
| | 7.1.3 EndPointReset | 36 |
| | 7.1.4 Logical Unit Reset | 37 |
| | 7.1.5 Host UniPro Warm Reset | 37 |

-i-

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

| | | Page |
|---|---|---|
| 7.1.6 | Summary of Resets and Device Behavior | 38 |
| 7.2 | Power up ramp | 39 |
| 7.3 | Power off ramp | 40 |
| 7.4 | UFS Device Power Modes and LU Power Condition | 41 |
| 7.4.1 | Device Power Modes | 41 |
| 7.4.2 | Power Management Command: START STOP UNIT | 52 |
| 7.4.3 | Power Mode Control | 54 |
| 7.4.4 | Logical Unit Power Condition | 56 |
| 8 | UFS HIC Layer: MIPI M-PHY | 57 |
| 8.1 | Termination | 57 |
| 8.2 | Drive Levels | 57 |
| 8.3 | PHY State machine | 57 |
| 8.4 | HS Burst | 58 |
| 8.4.1 | HS Prepare Length Control | 58 |
| 8.4.2 | HS Sync Length Control | 58 |
| 8.5 | PWM Burst | 58 |
| 8.5.1 | LS Prepare Length Control | 58 |
| 8.6 | Adapt | 58 |
| 8.7 | UFS PHY Attributes | 59 |
| 8.8 | Electrical characteristics | 60 |
| 8.8.1 | Transmitter Characteristics | 60 |
| 8.8.2 | Receiver Characteristics | 60 |
| 9 | UFS HIC Layer: MIPI UniPro | 61 |
| 9.1 | Overview | 61 |
| 9.2 | Architectural Model | 61 |
| 9.3 | UniPro/UFS Transport Protocol Interface (Data Plane) | 62 |
| 9.3.1 | Flow Control | 62 |
| 9.3.2 | Object Sizes | 62 |
| 9.4 | UniPro/UFS Control Interface (Control Plane) | 63 |
| 9.5 | UniPro/UFS Transport Protocol Address Mapping | 64 |
| 9.6 | Options and Tunable Parameters of UniPro | 65 |
| 9.6.1 | UniPro PHY Adapter | 65 |
| 9.6.2 | UniPro Data Link Layer | 66 |
| 9.6.3 | UniPro Network Layer | 66 |
| 9.6.4 | UniPro Transport Layer | 67 |
| 9.6.5 | UniPro Device Management Entity Transport Layer | 67 |
| 9.6.6 | UniPro Attributes | 68 |
| 10 | UFS Transport Protocol (UTP) Layer | 69 |
| 10.1 | Overview | 69 |
| 10.2 | UTP and UniPro Specific Overview | 70 |
| 10.2.1 | Phases | 70 |
| 10.2.2 | Data Pacing | 70 |
| 10.2.3 | UniPro | 70 |
| 10.3 | UFS Transport Protocol Transactions Overview | 70 |
| 10.4 | Service Delivery Subsystem | 71 |
| 10.5 | UPIU Transactions | 71 |
| 10.6 | General UFS Protocol Information Unit Format | 73 |
| 10.6.1 | Overview | 74 |
| 10.6.2 | Basic Header Format | 74 |
| 10.7 | UFS Protocol Information Units | 82 |
| 10.7.1 | COMMAND UPIU | 82 |

-ii-

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

| Section | Description | Page |
|---------|-------------|------|
| 10.7.2 | RESPONSE UPIU | 85 |
| 10.7.3 | DATA OUT UPIU | 97 |
| 10.7.4 | DATA IN UPIU | 101 |
| 10.7.5 | READY TO TRANSFER UPIU | 107 |
| 10.7.6 | TASK MANAGEMENT REQUEST UPIU | 113 |
| 10.7.7 | TASK MANAGEMENT RESPONSE UPIU | 116 |
| 10.7.8 | QUERY REQUEST UPIU | 119 |
| 10.7.9 | QUERY RESPONSE UPIU | 132 |
| 10.7.10 | REJECT UPIU | 144 |
| 10.7.11 | NOP OUT UPIU | 147 |
| 10.7.12 | NOP IN UPIU | 149 |
| 10.7.13 | Data In Transfer Rules | 151 |
| 10.7.14 | Overview - Data Out of Order Transfer | 155 |
| 10.8 | Logical Units | 157 |
| 10.8.1 | UFS SCSI Domain | 157 |
| 10.8.2 | UFS Logical Unit Definition | 157 |
| 10.8.3 | Well Known Logical Unit Definition | 158 |
| 10.8.4 | Logical Unit Addressing | 158 |
| 10.8.5 | Well Known Logical Unit Defined in UFS | 159 |
| 10.8.6 | Translation of 8-bit UFS LUN to 64-bit SCSI LUN Address | 160 |
| 10.8.7 | SCSI Write Command | 161 |
| 10.8.8 | SCSI Read Command | 162 |
| 10.8.9 | Unit Attention Condition | 163 |
| 10.9 | Application Layer and Device Manager Transport Protocol Services | 164 |
| 10.9.1 | UFS Initiator Port and Target Port Attributes | 164 |
| 10.9.2 | Execute Command Procedure Call Transport Protocol Services | 165 |
| 10.9.3 | SCSI Command Transport Protocol Service | 166 |
| 10.9.4 | SCSI Command Received Transport Protocol | 167 |
| 10.9.5 | Send Command Complete Transport Protocol Service | 168 |
| 10.9.6 | Command Complete Received Transport Protocol Service | 169 |
| 10.9.7 | Data transfer SCSI Transport Protocol Services | 170 |
| 10.9.8 | Task Management Function Procedure Calls | 174 |
| 10.9.9 | Query Function Transport Protocol Services | 180 |
| 11 | UFS Application (UCL) Layer – SCSI Commands | 183 |
| 11.1 | Universal Flash Storage Command Layer (UCL) Introduction | 183 |
| 11.1.1 | The Command Descriptor Block (CDB) | 183 |
| 11.2 | Universal Flash Storage Native Commands (UNC) | 183 |
| 11.3 | Universal Flash Storage SCSI Commands | 184 |
| 11.3.1 | General Information about SCSI Commands in UFS | 185 |
| 11.3.2 | INQUIRY Command | 185 |
| 11.3.3 | MODE SELECT (10) Command | 188 |
| 11.3.4 | MODE SENSE (10) Command | 190 |
| 11.3.5 | READ (6) Command | 193 |
| 11.3.6 | READ (10) Command | 194 |
| 11.3.7 | READ (16) Command | 196 |
| 11.3.8 | READ CAPACITY (10) Command | 198 |
| 11.3.9 | READ CAPACITY (16) Command | 201 |
| 11.3.10 | START STOP UNIT Command | 204 |
| 11.3.11 | TEST UNIT READY Command | 205 |
| 11.3.12 | REPORT LUNS Command | 206 |
| 11.3.13 | VERIFY (10) Command | 211 |

-iii-

Downloaded by Lei Hock Chua (leihock.chua@dso.org.sg) on Jan 7, 2025, 1:31 pm PST

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

| | | Page |
|---|---|---|
| 11.3.14 | WRITE (6) Command | 213 |
| 11.3.15 | WRITE (10) Command | 215 |
| 11.3.16 | WRITE (16) Command | 218 |
| 11.3.17 | REQUEST SENSE Command | 221 |
| 11.3.18 | FORMAT UNIT Command | 223 |
| 11.3.13 | VERIFY (10) Command | 211 |
| 11.3.14 | WRITE (6) Command | 213 |
| 11.3.15 | WRITE (10) Command | 215 |
| 11.3.16 | WRITE (16) Command | 218 |
| 11.3.17 | REQUEST SENSE Command | 221 |
| 11.3.18 | FORMAT UNIT Command | 223 |
| 11.3.19 | PRE-FETCH (10) Command | 225 |
| 11.3.20 | PRE-FETCH (16) Command | 228 |
| 11.3.21 | SECURITY PROTOCOL IN Command | 229 |
| 11.3.22 | SECURITY PROTOCOL OUT Command | 230 |
| 11.3.23 | SEND DIAGNOSTIC Command | 232 |
| 11.3.24 | SYNCHRONIZE CACHE (10) Command | 234 |
| 11.3.25 | SYNCHRONIZE CACHE (16) Command | 237 |
| 11.3.26 | UNMAP Command | 238 |
| 11.3.27 | READ BUFFER Command | 242 |
| 11.3.28 | WRITE BUFFER Command | 248 |
| 11.3.29 | BARRIER Command | 252 |
| 11.4 | Mode Pages | 253 |
| 11.4.1 | Mode Page Overview | 253 |
| 11.4.2 | UFS Supported Pages | 258 |
| 11.5 | Vital product data parameters | 265 |
| 11.5.1 | Overview | 265 |
| 11.5.2 | VPD Page Format | 265 |
| 11.5.3 | Supported VPD Pages VPD Page | 266 |
| 11.5.4 | Mode Page Policy VPD Page | 267 |
| 12 | UFS Security | 269 |
| 12.1 | UFS Security Feature Support Requirements | 269 |
| 12.2 | Secure Mode | 269 |
| 12.2.1 | Description | 269 |
| 12.2.2 | Requirements | 270 |
| 12.2.3 | Implementation | 272 |
| 12.3 | Device Data Protection | 277 |
| 12.3.1 | Description and Requirements | 277 |
| 12.3.2 | Implementation | 277 |
| 12.4 | RPMB | 278 |
| 12.4.1 | Introduction | 278 |
| 12.4.2 | RPMB Well Known Logical Unit Description | 278 |
| 12.4.3 | Requirements | 279 |
| 12.4.4 | Implementation in Normal RPMB Mode | 293 |
| 12.4.5 | Implementation in Advanced RPMB Mode | 294 |
| 12.4.6 | SECURITY PROTOCOL IN/OUT Commands | 295 |
| 12.4.7 | RPMB Operations | 301 |
| 12.5 | Malware Protection | 353 |
| 13 | UFS Functional Descriptions | 354 |
| 13.1 | UFS Boot | 354 |
| 13.1.1 | Introduction | 354 |

-iv-

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

| Section | Title | Page |
|---------|-------|------|
| 13.1.2 | Boot Configuration | 354 |
| 13.1.3 | Initialization and Boot Code Download Process | 357 |
| 13.1.4 | Initialization Process without Boot Code Download | 360 |
| 13.1.5 | Boot Logical Unit Operations | 360 |
| 13.1.6 | Configurability | 361 |
| 13.1.7 | Security | 362 |
| 13.2 | Logical Unit Management | 362 |
| 13.2.1 | Introduction | 362 |
| 13.2.2 | Logical Unit Features | 362 |
| 13.2.3 | Logical Unit Configuration | 365 |
| 13.3 | Logical Block Provisioning | 371 |
| 13.3.1 | Overview | 371 |
| 13.3.2 | Full Provisioning | 371 |
| 13.3.3 | Thin Provisioning | 371 |
| 13.4 | Host Device Interaction | 372 |
| 13.4.1 | Overview | 372 |
| 13.4.2 | Applicable Devices | 372 |
| 13.4.3 | Command Queue: Inter-LU Priority | 372 |
| 13.4.4 | Background Operations Mode | 373 |
| 13.4.5 | Power Off Notification | 376 |
| 13.4.6 | Dynamic Device Capacity | 377 |
| 13.4.7 | Data Reliability | 381 |
| 13.4.8 | Real-Time Clock Information | 382 |
| 13.4.9 | Timestamp Information | 383 |
| 13.4.10 | Context Management | 384 |
| 13.4.11 | System Data Tag Mechanism | 387 |
| 13.4.12 | Exception Events Mechanism | 388 |
| 13.4.13 | Queue Depth Definition | 391 |
| 13.4.14 | Device Life Span Mode | 392 |
| 13.4.15 | Refresh Operation | 393 |
| 13.4.16 | Temperature Event Notification | 396 |
| 13.4.17 | Performance Throttling Event Notification | 396 |
| 13.4.18 | WriteBooster | 397 |
| 13.4.19 | BARRIER COMMAND | 406 |
| 13.4.20 | Host Initiated Defragmentation | 409 |
| 13.4.21 | Fast Recovery Mode | 416 |
| 13.5 | UFS Cache | 417 |
| 13.6 | Production State Awareness (PSA) | 418 |
| 13.6.1 | Introduction | 418 |
| 13.6.2 | PSA Life-cycle | 419 |
| **14** | **UFS Descriptors, Flags and Attributes** | **422** |
| 14.1 | UFS Descriptors | 422 |
| 14.1.1 | Descriptor Types | 423 |
| 14.1.2 | Descriptor Indexing | 423 |
| 14.1.3 | Accessing Descriptors and Device Configuration | 423 |
| 14.1.4 | Descriptor Definitions | 429 |
| 14.2 | Flags | 468 |
| 14.3 | Attributes | 473 |
| **15** | **UFS Mechanical Standard** | **499** |

-v-

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

| | | Page |
|---|---|---|
| **ANNEX A** | **(Informative) Dynamic Capacity Host Implementation Example** | **500** |
| A.1 | Overview | 500 |
| A.2 | Method Outline | 500 |
| **ANNEX B** | **(Informative) Reference Clock Measurement Procedure** | **501** |
| B.1 | Random RMS Jitter Measurement Procedure | 501 |
| B.2 | Deterministic Jitter Measurement Procedure | 502 |
| B.3 | Equipment Requirements | 503 |
| B.4 | Test Setup | 503 |
| **ANNEX C** | **(Informative) Reference Clock Detection in HS-LSS_A: An Implementation Example** | **504** |
| C.1 | Overview | 504 |
| C.2 | Method Outline | 504 |
| **ANNEX D** | **(Informative) Board Design Guideline** | **505** |
| D.1 | Overview | 505 |
| D.2 | Allowed Max Impedance & Typical Cap for System Board PCB | 506 |
| D.3 | System Board PCB Noise Margin Recommendation | 508 |
| **ANNEX E** | **(Informative) Differences between Revisions** | **509** |
| E.1 | Changes between JESD220G and its predecessor JESD220F (August 2022) | 509 |
| | E.1.1 NEW Features or Definitions | 509 |
| | E.1.2 Changes in Clause 2 "Normative Reference" | 509 |
| | E.1.3 Changes in Features Already Defined in UFS 4.0 | 509 |
| E.2 | Changes between JESD220F and its predecessor JESD220E (January 2020) | 510 |
| | E.2.1 NEW Features or New Definitions | 510 |
| | E.2.2 Changes in Clause 2 "Normative Reference" | 510 |
| | E.2.3 Changes in Features Already Defined in UFS 3.1 | 511 |
| E.3 | Changes between JESD220E and its predecessor JESD220D (January 2018) | 512 |
| | E.3.1 New Features or New Definitions | 512 |
| | E.3.2 Changes in Clause 2 "Normative Reference" | 512 |
| | E.3.3 Changes in Features Already Defined in UFS 3.0 | 512 |
| E.4 | Changes between JESD220D and its predecessor JESD220C (March 2016) | 513 |
| | E.4.1 New Features or New Definitions | 513 |
| | E.4.2 Changes in Clause 2 "Normative Reference" | 513 |
| | E.4.3 Changes in Features Already Defined in UFS 2.1 | 513 |
| E.5 | Changes between JESD220C and its predecessor JESD220B (September 2013) | 513 |
| | E.5.1 New Features or New Definitions | 514 |
| | E.5.2 Changes in Clause 2 "Normative Reference" | 514 |
| | E.5.3 Changes in Features Already Defined in UFS 2.0 | 514 |
| E.6 | Changes between JESD220B and its predecessor JESD220A (June 2012) | 517 |
| | E.6.1 New Features or New Definitions | 517 |
| | E.6.2 Changes in Clause 2 "Normative Reference" | 517 |
| | E.6.3 Changes in Features Already Defined in UFS 1.1 | 517 |

-vi-

Downloaded by Lai Hock Chai (lai.hock.chai@ephsoft.com) on Jan 1, 2025, 1:51 pm PST

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

**Page**

#### Figures

Figure 5.1 — UFS Top Level Architecture .................................................................................................................9
Figure 5.2 — Usage of UDM_SAP ...........................................................................................................................10
Figure 5.3 — Usage of UIO_SAP .............................................................................................................................10
Figure 5.4 — UFS System Model .............................................................................................................................12
Figure 5.5 — SCSI Domain Class Diagram ...............................................................................................................16
Figure 5.6 — UFS Domain Class Diagram ................................................................................................................17
Figure 6.1 — Conceptual UFS Device Block Diagram .............................................................................................20
Figure 6.2 — Supply Voltage Power Up Timings......................................................................................................24
Figure 6.3 — bRefClkGatingWaitTime ....................................................................................................................27
Figure 6.4 — Clock Input Levels, Rise Time, and Fall Time ....................................................................................28
Figure 6.5 — Test Load Impedance .........................................................................................................................29
Figure 6.6 — Output Driver and Input Receiver Levels............................................................................................29
Figure 6.7 — Clock Output Levels, Rise Time and Fall Time ..................................................................................30
Figure 6.8 — DC and AC Voltage Range for VCC/VCCQ/VCCQ2 ...........................................................................33
Figure 7.1 — Power-on Reset .................................................................................................................................34
Figure 7.2 — Hardware Reset ..................................................................................................................................35
Figure 7.3 — Reset AC Timings ..............................................................................................................................35
Figure 7.4 — EndPointReset ...................................................................................................................................36
Figure 7.5 — Logical Unit Reset ..............................................................................................................................37
Figure 7.6 — Power Up Ramps ...............................................................................................................................39
Figure 7.7 — Power Off Ramps ...............................................................................................................................40
Figure 7.8 — Power Mode State Machine ...............................................................................................................47
Figure 8.1 — Simplified Example for I/O Termination ............................................................................................57
Figure 9.1 — UniPro Internal Layering View (a) and UniPro Black Box View (b) ..................................................61
Figure 9.2 — Physical Lane Connections .................................................................................................................66
Figure 10.1 — EHS Entry Format ............................................................................................................................80
Figure 10.2 — Data Out Transfer Example .............................................................................................................100
Figure 10.3 — Data In Transfer Example ...............................................................................................................105
Figure 10.4 — DATA IN UPIU with Retransmission Sequence Example ..............................................................106
Figure 10.5 — READY TO TRANSFER UPIU Sequence Example.......................................................................111
Figure 10.6 — READY TO TRANSFER UPIU with Retransmission Sequence Example ......................................112
Figure 10.7 — Example for Data Out Transfer Rule 1...........................................................................................151
Figure 10.8 — Example for Data Transfer Count Mismatch ..................................................................................152
Figure 10.9 — Example for Data Out Transfer Rule 2...........................................................................................153
Figure 10.10 — Example for Data Out Transfer Rule 3..........................................................................................154
Figure 10.11 — Example for Data Out of Order Transfer - 1 ................................................................................155
Figure 10.12 — Example for Data Out of Order Transfer - 2 ................................................................................156
Figure 10.13 — UFS SCSI Domain ........................................................................................................................157
Figure 10.14 — Logical Unit Addressing ...............................................................................................................158
Figure 10.15 — SCSI Write ....................................................................................................................................161
Figure 10.16 — SCSI Read .....................................................................................................................................162
Figure 10.17 — Command without Data Phase ......................................................................................................165
Figure 10.18 — Command + Read Data Phase 1/2 .................................................................................................171
Figure 10.19 — Command + Read Data Phase 2/2 .................................................................................................171
Figure 10.20 — Command + Write Data Phase 1/2 ................................................................................................173
Figure 10.21 — Command + Write Data Phase 2/2 ................................................................................................173
Figure 10.22 — Task Management Function ..........................................................................................................177
Figure 10.23 — UFS Query Function .....................................................................................................................180
Figure 11.1 — UFS Command Layer......................................................................................................................183

**-vii-**

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

| Figure | Description | Page |
|--------|-------------|------|
| Figure 12.1 | Purge Operation State Machine | 274 |
| Figure 12.2 | Advanced RPMB Message Structure in EHS Field | 294 |
| Figure 12.3 | Request Type Message Delivery | 302 |
| Figure 12.4 | Response Type Message Delivery | 304 |
| Figure 12.5 | Authentication Key Programming Flow | 306 |
| Figure 12.6 | Read Counter Value Flow | 307 |
| Figure 12.7 | Authenticated Data Write Flow | 310 |
| Figure 12.8 | Authenticated Data Read Flow | 312 |
| Figure 12.9 | Authenticated Secure Write Protect Configuration Block Write Flow | 315 |
| Figure 12.10 | Authenticated Secure Write Protect Configuration Block Read Flow | 317 |
| Figure 12.11 | RPMB Purge Enable Flow | 319 |
| Figure 12.12 | RPMB Purge Status Read Flow | 320 |
| Figure 12.13 | Authenticated Vendor Specific Command Request Flow | 322 |
| Figure 12.14 | Authenticated Vendor Specific Command Read Request Flow | 324 |
| Figure 12.15 | Authentication Key Programming Flow (in Advanced RPMB Mode) | 326 |
| Figure 12.16 | Read Counter Value Flow (in Advanced RPMB Mode) | 328 |
| Figure 12.17 | Authenticated Data Write Flow (in Advanced RPMB Mode) | 331 |
| Figure 12.18 | Authenticated Data Read Flow (in Advanced RPMB Mode) | 334 |
| Figure 12.19 | Authenticated Secure Write Protect Configuration Block Write Flow (in Advanced RPMB Mode) | 338 |
| Figure 12.20 | Authenticated Secure Write Protect Configuration Block Read Flow (in Advanced RPMB Mode) | 341 |
| Figure 12.21 | RPMB Purge Enable Flow (in Advanced RPMB Mode) | 344 |
| Figure 12.22 | RPMB Purge Status Read Flow (in Advanced RPMB Mode) | 347 |
| Figure 12.23 | Authenticated Vendor Specific Command Request Flow (in Advanced RPMB Mode) | 351 |
| Figure 12.24 | Authenticated Vendor Specific Command Status Read Request Flow (in Advanced RPMB Mode) | 353 |
| Figure 13.1 | UFS System Diagram | 354 |
| Figure 13.2 | Example of UFS Device Memory Organization for Boot | 356 |
| Figure 13.3 | Device Initialization and Boot Procedure Sequence Diagram | 359 |
| Figure 13.4 | Example of UFS Device Memory Organization | 363 |
| Figure 13.5 | Physical Memory Resource State Machine | 380 |
| Figure 13.6 | Example of Data Status After a Power Failure During Reliable Write Operation | 381 |
| Figure 13.7 | Concept of WriteBooster Feature | 397 |
| Figure 13.8 | Example of "LU Dedicated Buffer" Mode Configuration | 398 |
| Figure 13.9 | Example of "Shared Buffer" Mode Configuration | 399 |
| Figure 13.10 | (Example) Initiating a WriteBooster Buffer Resize Operation | 402 |
| Figure 13.11 | (Example) Checking the Status of Resize Operation And Updated WriteBooster Buffer Size | 403 |
| Figure 13.12 | Example of Barrier Operation | 406 |
| Figure 13.13 | Example of the Barrier between Commands with Simple Property | 407 |
| Figure 13.14 | Example of the Barrier Command between Commands with Different Properties | 407 |
| Figure 13.15 | Example of the Barrier Command between Commands with High Priorities | 407 |
| Figure 13.16 | Barrier Operation Scope (LU level) | 408 |
| Figure 13.17 | (Example) Transition of bHIDState Attribute | 410 |
| Figure 13.18 | (Example) HID Analysis Operation | 413 |
| Figure 13.19 | (Example) HID Defrag Operation | 414 |
| Figure 13.20 | (Example) HID Analysis & HID Defrag Operation | 415 |
| Figure 13.21 | (Example) Monitoring the Progress of Defragmenting | 415 |
| Figure 13.22 | FAST_RECOVERY_NEEDED from RESPONSE UPIU | 416 |
| Figure 13.23 | PSA Flow | 420 |

-viii-

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

**Page**

Figure 13.24 — PSA State Machine...........................................................................................................................421
Figure 14.1 — Descriptor Organization ....................................................................................................................423
Figure 14.2 — Read Request Descriptor .....................................................................................................................425
Figure 14.3 — Write Request Descriptor ....................................................................................................................426
Figure B.1 — Test Setup ...........................................................................................................................................503
Figure C.1 — REF CLK Frequency Detection in HS-LSS .......................................................................................504
Figure D.1 — Z(t) Measured and Observation Point.................................................................................................506
Figure D.2 — Zprofile Z(t) of the System at the UFS Package Solder Ball (without UFS Component) ..................507
Figure D.3 — A Simplified Z(t) System Electrical Model and Frequency Response of the Behavioral PDN Electrical
Load Model without the UFS Component Per Voltage Domain Per Channel..................................507

### Tables

Table 5.1 — UFS Signals ............................................................................................................................................13
Table 5.2 — Manufacturer and DeviceClass Attributes .............................................................................................14
Table 6.1 — Signal Name and Definitions..................................................................................................................21
Table 6.2 — Electrostatic Discharge Sensitivity Characteristics.................................................................................22
Table 6.3 — Reset Signal and LSS Signal Electrical Parameters...............................................................................23
Table 6.4 — UFS Power Supply Parameters..............................................................................................................23
Table 6.5 — Reference Clock Parameters..................................................................................................................25
Table 6.6 — Reference Clock Frequency and HS Operation .....................................................................................26
Table 6.7 — HS-BURST Rates ..................................................................................................................................28
Table 6.8 — Host Controller Reference Clock Parameters .........................................................................................29
Table 6.9 — Charge Pump Capacitors Description....................................................................................................30
Table 6.10 — Charge Pump Related Ball Names.......................................................................................................31
Table 6.11 — ZQ Calibration Resistors Description ..................................................................................................31
Table 6.12 — Absolute Maximum DC Ratings and Operating Conditions.................................................................32
Table 6.13 — AC and DC Voltage Operating Conditions ..........................................................................................33
Table 7.1 — Reset Timing Parameters .......................................................................................................................35
Table 7.2 — Reset States ............................................................................................................................................38
Table 7.3 — UniPro Attributes, UFS Attributes and UFS Flags Reset .......................................................................38
Table 7.4 — Allowed SCSI Commands and UPIU for Each Power Mode................................................................50
Table 7.5 — Device Well Known Logical Unit Responses to SSU Command...........................................................51
Table 7.6 — Device Well Known Logical Unit Responses to Commands Other Than SSU .....................................52
Table 7.7 — Pollable Sense Data for Each Power Modes..........................................................................................52
Table 7.8 — START STOP UNIT Command.............................................................................................................52
Table 7.9 — START STOP UNIT Fields....................................................................................................................53
Table 7.10 — Attributes for Power Mode Control......................................................................................................54
Table 7.11 — Device Descriptor Parameters ..............................................................................................................54
Table 7.12 — Power Parameters Descriptor Fields....................................................................................................55
Table 7.13 — Format for Power Parameter Element..................................................................................................55
Table 7.14 — Logical Unit Response to SCSI Command..........................................................................................56
Table 8.1 — UFS PHY M-TX Capability Attributes(0) ..............................................................................................59
Table 8.2 — UFS PHY M-RX Capability Attributes(0) ..............................................................................................60
Table 9.1 — UFS Initiator and Target Port Identifiers ...............................................................................................65
Table 9.2 — UniPro Attribute Summary ....................................................................................................................68
Table 10.1 — UPIU Transaction Codes .....................................................................................................................71
Table 10.2 — UPIU Transaction Code Definitions....................................................................................................72
Table 10.3 — General format of the UFS Protocol Information Unit ........................................................................73
Table 10.4 — Basic Header Format ............................................................................................................................74

-ix-

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

| Table | Description | Page |
|-------|-------------|------|
| Table 10.5 | Transaction Type Format | 74 |
| Table 10.6 | UPIU Flags | 76 |
| Table 10.7 | Task Attribute Definition | 76 |
| Table 10.8 | UTP Response Values | 77 |
| Table 10.9 | UPIU Associated to a Single Task | 77 |
| Table 10.10 | Initiator ID Composition | 78 |
| Table 10.11 | Command Set Type | 78 |
| Table 10.12 | EHS Entry Format | 80 |
| Table 10.13 | COMMAND UPIU | 82 |
| Table 10.14 | Flags Definition for COMMAND UPIU | 83 |
| Table 10.15 | RESPONSE UPIU | 86 |
| Table 10.16 | Flags Definition for RESPONSE UPIU | 87 |
| Table 10.17 | SCSI Status Values | 89 |
| Table 10.18 | Flags and Residual Count Relationship | 91 |
| Table 10.19 | SCSI Fixed Format Sense Data | 94 |
| Table 10.20 | Sense Key | 96 |
| Table 10.21 | DATA OUT UPIU | 97 |
| Table 10.22 | Flags Definition for DATA OUT UPIU | 98 |
| Table 10.23 | DATA IN UPIU | 101 |
| Table 10.24 | Flags Definition for DATA IN UPIU | 102 |
| Table 10.25 | READY TO TRANSFER UPIU | 107 |
| Table 10.26 | Flags Definition for RTT UPIU | 108 |
| Table 10.27 | Task Management Request UPIU | 113 |
| Table 10.28 | Task Management Function values | 114 |
| Table 10.29 | Task Management Input Parameters | 115 |
| Table 10.30 | Task Management Response UPIU | 116 |
| Table 10.31 | Task Management Output Parameters | 117 |
| Table 10.32 | Task Management Service Response | 118 |
| Table 10.33 | QUERY REQUEST UPIU | 119 |
| Table 10.34 | Query Function Field Values | 121 |
| Table 10.35 | Transaction Specific Fields | 122 |
| Table 10.36 | Query Function Opcode Values | 122 |
| Table 10.37 | Read Descriptor | 123 |
| Table 10.38 | Write Descriptor | 124 |
| Table 10.39 | Read Attribute | 125 |
| Table 10.40 | Write Attribute | 126 |
| Table 10.41 | Read Flag | 127 |
| Table 10.42 | Set Flag | 128 |
| Table 10.43 | Clear Flag | 129 |
| Table 10.44 | Toggle Flag | 130 |
| Table 10.45 | NOP | 131 |
| Table 10.46 | QUERY RESPONSE | 132 |
| Table 10.47 | Query Response Code | 133 |
| Table 10.48 | Transaction Specific Fields | 134 |
| Table 10.49 | Read Descriptor | 135 |
| Table 10.50 | Write Descriptor | 136 |
| Table 10.51 | Read Attribute Response Data Format | 137 |
| Table 10.52 | Write Attribute | 138 |
| Table 10.53 | Read Flag Response Data Format | 139 |
| Table 10.54 | Set Flag | 140 |
| Table 10.55 | Clear Flag | 141 |

-x-

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

| Table | Description | Page |
|-------|-------------|------|
| Table 10.56 | Toggle Flag | 142 |
| Table 10.57 | NOP | 143 |
| Table 10.58 | Reject UPIU | 144 |
| Table 10.59 | Basic Header Status Description | 146 |
| Table 10.60 | EEE Status Definition | 146 |
| Table 10.61 | NOP OUT UPIU | 147 |
| Table 10.62 | NOP IN UPIU | 149 |
| Table 10.63 | Parameters Related to Data Out Transfer Rules | 154 |
| Table 10.64 | Well Known Logical Unit Commands | 159 |
| Table 10.65 | Examples of Logical Unit Representation Format | 160 |
| Table 10.66 | Events for UAC Establishment | 163 |
| Table 10.67 | Commands for Exceptional Behavior on UAC | 163 |
| Table 10.68 | UFS Initiator Port and Target Port Attributes | 164 |
| Table 10.69 | Send SCSI Command Transport Protocol Service | 166 |
| Table 10.70 | SCSI Command Received Transport Protocol | 167 |
| Table 10.71 | Send Command Complete Transport Protocol Service | 168 |
| Table 10.72 | Command Complete Received Transport Protocol Service | 169 |
| Table 10.73 | Send Data-In Transport Protocol Service | 170 |
| Table 10.74 | Data-In Delivered Transport Protocol Service | 170 |
| Table 10.75 | Receive Data-Out Transport Protocol Service | 172 |
| Table 10.76 | Data-Out Received Transport Protocol Service | 172 |
| Table 10.77 | Task Management Function Procedure Calls | 174 |
| Table 10.78 | SCSI Transport Protocol Service Responses | 174 |
| Table 10.79 | Send Task Management Request SCSI Transport Protocol Service Request | 178 |
| Table 10.80 | Task Management Request Received SCSI Transport Protocol Service Indication | 178 |
| Table 10.81 | Task Management Function Executed SCSI Transport Protocol Service Response | 178 |
| Table 10.82 | Received Task Management Function Executed SCSI Transport Protocol Service Confirmation | 179 |
| Table 10.83 | Send Query Request UFS Transport Protocol Service | 180 |
| Table 10.84 | Query Request Received UFS Transport Protocol Service Indication | 181 |
| Table 10.85 | Query Function Executed UFS Transport Protocol Service Response | 181 |
| Table 10.86 | Received Query Function Executed UFS Transport Protocol Service Confirmation | 182 |
| Table 11.1 | UFS SCSI Command Set | 184 |
| Table 11.2 | INQUIRY Command | 185 |
| Table 11.3 | Standard INQUIRY Data Format | 186 |
| Table 11.4 | Standard INQUIRY Response Data | 187 |
| Table 11.5 | MODE SELECT (10) Command | 188 |
| Table 11.6 | Mode Select Command Parameters | 189 |
| Table 11.7 | MODE SENSE (10) Command | 191 |
| Table 11.8 | Mode Sense Command Parameters | 191 |
| Table 11.9 | Page Control Function | 192 |
| Table 11.10 | READ (6) Command | 193 |
| Table 11.11 | READ (10) Command | 194 |
| Table 11.12 | READ (16) Command | 196 |
| Table 11.13 | READ CAPACITY (10) Command | 198 |
| Table 11.14 | Read Capacity (10) Parameter Data | 199 |
| Table 11.15 | READ CAPACITY (16) Command | 201 |
| Table 11.16 | Read Capacity (16) Parameter Data | 202 |
| Table 11.17 | START STOP UNIT Command | 204 |
| Table 11.18 | TEST UNIT READY Command | 205 |
| Table 11.19 | REPORT LUNS Command | 206 |
| Table 11.20 | Report LUNS Command Parameters | 207 |

-xi-

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

| | Page |
|---|---|
| Table 11.21 — SELECT REPORT Field | 207 |
| Table 11.22 — Report LUNS Parameter Data Format | 208 |
| Table 11.23 — Single Level LUN Structure Using Peripheral Device Addressing Method | 208 |
| Table 11.24 — Well Known Logical Unit Extended Addressing Format | 209 |
| Table 11.25 — Format of LUN Field in UPIU | 210 |
| Table 11.26 — Well Known Logical Unit Numbers | 210 |
| Table 11.27 — VERIFY (10) Command | 211 |
| Table 11.28 — Verify Command Parameters | 212 |
| Table 11.29 — WRITE (6) Command | 213 |
| Table 11.30 — WRITE (10) Command | 215 |
| Table 11.31 — WRITE (16) Command | 218 |
| Table 11.32 — REQUEST SENSE Command | 221 |
| Table 11.33 — FORMAT UNIT Command | 223 |
| Table 11.34 — Format Unit Command Parameters | 224 |
| Table 11.35 — PRE-FETCH Command | 225 |
| Table 11.36 — PRE-FETCH Command Parameters | 226 |
| Table 11.37 — PRE-FETCH (16) Command | 228 |
| Table 11.38 — SECURITY PROTOCOL IN Command | 229 |
| Table 11.39 — SECURITY PROTOCOL OUT Command | 230 |
| Table 11.40 — SEND DIAGNOSTIC Command | 232 |
| Table 11.41 — Send Diagnostic Parameters | 232 |
| Table 11.42 — SYNCHRONIZE CACHE (10) Command | 234 |
| Table 11.43 — Synchronize Cache Command Parameters | 235 |
| Table 11.44 — SYNCHRONIZE CACHE (16) Command Descriptor Block | 237 |
| Table 11.45 — UNMAP Command | 238 |
| Table 11.46 — UNMAP Parameter List | 239 |
| Table 11.47 — UNMAP Block Descriptor | 240 |
| Table 11.48 — READ BUFFER Command | 242 |
| Table 11.49 — Read Buffer Command Mode Field Values | 243 |
| Table 11.50 — Buffer ID Field for Error History Mode | 244 |
| Table 11.51 — Error History Directory | 245 |
| Table 11.52 — EHS_SCSI_RCP Field | 246 |
| Table 11.53 — Error History Directory Entry | 246 |
| Table 11.54 — WRITE BUFFER Command | 248 |
| Table 11.55 — Write Buffer Command Parameters | 249 |
| Table 11.56 — Write Buffer Command Mode Field Values | 249 |
| Table 11.57 — BARRIER Command | 252 |
| Table 11.58 — Mode Page Code Usage | 253 |
| Table 11.59 — UFS Mode Parameter List | 254 |
| Table 11.60 — UFS Mode Parameter Header (10) | 254 |
| Table 11.61 — Mode Parameter Header Detail | 255 |
| Table 11.62 — Page_0 Mode Page Format | 256 |
| Table 11.63 — Page 0 Format Parameters | 256 |
| Table 11.64 — Sub_page Mode Page Format | 257 |
| Table 11.65 — Subpage Format Parameters | 257 |
| Table 11.66 — UFS Supported Pages | 258 |
| Table 11.67 — Control Mode Page Default Value | 259 |
| Table 11.68 — Control Mode Page Parameters | 260 |
| Table 11.69 — Read-Write Error Recovery Mode Page Default Value | 261 |
| Table 11.70 — Read-Write Error Recovery Parameters | 262 |
| Table 11.71 — Caching Mode Page Default Value | 263 |

-xii-

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

| Item | Page |
|------|------|
| Table 11.72 — Caching Mode Page Parameters | 264 |
| Table 11.73 — VPD Page Format | 265 |
| Table 11.74 — Supported VPD Pages VPD Page | 266 |
| Table 11.75 — Mode Page Policy VPD Page | 267 |
| Table 11.76 — Mode Page Policy Descriptor | 267 |
| Table 11.77 — MODE PAGE POLICY Field | 268 |
| Table 12.1 — Secure Write Protect Configuration Block for Normal RPMB | 281 |
| Table 12.2 — Secure Write Protect Configuration Block for Advanced RPMB | 282 |
| Table 12.3 — Secure Write Protect Entry | 283 |
| Table 12.4 — Write Protect Type Field | 284 |
| Table 12.5 — RPMB Purge Response Packet Format (Legacy RPMB Mode) | 285 |
| Table 12.6 — RPMB Purge Response Packet Format (Advanced RPMB Mode) | 285 |
| Table 12.7 — RPMB Message Components | 288 |
| Table 12.8 — Request Message Types | 289 |
| Table 12.9 — Response Message Types | 290 |
| Table 12.10 — Result Data Structure | 291 |
| Table 12.11 — Result Code Definition | 292 |
| Table 12.12 — RPMB Message Data Frame | 293 |
| Table 12.13 — Advanced RPMB Meta Information | 295 |
| Table 12.14 — CDB Format of SECURITY PROTOCOL IN/OUT Commands | 296 |
| Table 12.15 — SECURITY PROTOCOL SPECIFIC Field for Protocol ECh | 297 |
| Table 12.16 — Security Protocol Specific Field Values for Protocol 00h | 298 |
| Table 12.17 — Supported Security Protocols SECURITY PROTOCOL IN Parameter Data | 299 |
| Table 12.18 — UFS Supported Security Protocols SECURITY PROTOCOL IN Parameter Data | 299 |
| Table 12.19 — Certificate Data SECURITY PROTOCOL IN Parameter Data | 300 |
| Table 12.20 — UFS Certificate Data SECURITY PROTOCOL IN Parameter Data | 300 |
| Table 12.21 — Expected Data Transfer Length Value for Request Type Messages | 301 |
| Table 12.22 — Expected Data Transfer Length Value for Response Type Messages | 303 |
| Table 13.1 — bBootLunEn Attribute | 355 |
| Table 13.2 — Valid UPIUs and SCSI Commands for Each Initialization Phase | 360 |
| Table 13.3 — Logical Unit Configurable Parameters | 366 |
| Table 13.4 — Parameter for Controlling Logical Unit Data Reliability | 382 |
| Table 14.1 — Descriptor Identification Values | 422 |
| Table 14.2 — Generic Descriptor Format | 427 |
| Table 14.3 — Logical Unit Descriptor Format | 427 |
| Table 14.4 — Device Descriptor | 428 |
| Table 14.5 — wManufacturerID Definition | 437 |
| Table 14.6 — Configuration Descriptor Format (INDEX = 00h) | 438 |
| Table 14.7 — Configuration Descriptor Format (INDEX = 01h) | 439 |
| Table 14.8 — Configuration Descriptor Format (INDEX = 02h) | 439 |
| Table 14.9 — Configuration Descriptor Format (INDEX = 03h) | 439 |
| Table 14.10 — Configuration Descr. Header and Device Descr. Conf. Parameters (INDEX = 00h) | 441 |
| Table 14.11 — Configuration Descr. Header with INDEX = 01h/02h/03h | 442 |
| Table 14.12 — Unit Descriptor Configurable Parameters | 443 |
| Table 14.13 — Geometry Descriptor | 444 |
| Table 14.14 — Unit Descriptor | 454 |
| Table 14.15 — RPMB Unit Descriptor | 458 |
| Table 14.16 — Power Parameters Descriptor | 461 |
| Table 14.17 — Interconnect Descriptor | 462 |
| Table 14.18 — Manufacturer Name String | 462 |
| Table 14.19 — Product Name String | 463 |

-xiii-

# JEDEC Standard No. 220G

## UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

### Contents (cont'd)

| Table | Description | Page |
|-------|-------------|------|
| Table 14.20 | OEM_ID String | 463 |
| Table 14.21 | Serial Number String Descriptor | 464 |
| Table 14.22 | Product Revision Level String | 464 |
| Table 14.23 | Device Health Descriptor | 465 |
| Table 14.24 | Vendor Specific Descriptor | 467 |
| Table 14.25 | Flags Access Properties | 467 |
| Table 14.26 | Flags | 468 |
| Table 14.27 | Attributes Access Properties | 472 |
| Table 14.28 | Attributes | 473 |
| Table B.1 | Maximum Random RMS Jitter Amount | 501 |
| Table D.1 | Allowed Max Impedance & Typical Capacitor at System Board Design | 506 |
| Table D.2 | Recommended Max PMIC & PCB Noise Margin | 508 |
| Table D.3 | (Alternative) 2.55 VCC to Allow More PMIC & PCB Noise Margin | 508 |

-xiv-

Downloaded by Lai Hong Chua (laihong.chua@phison.com) on Jun 7, 2025, 1:34 pm PST

# JEDEC Standard No. 220G

## Foreword

This standard has been prepared by JEDEC. The purpose of this standard is definition of a UFS Universal Flash Storage electrical interface and a UFS memory device. This standard defines a unique UFS feature set and includes the feature set of eMMC standard as a subset. This standard references several other standard specifications by MIPI (M-PHY and UniPro specifications) and INCITS T10 (SBC, SPC and SAM draft standards) organizations.

## Introduction

The UFS electrical interface is a universal serial communication bus which can be utilized for different types of applications. It's based on MIPI M-PHY specification as physical layer for optimized performance and power. The UFS architectural model references the INCITS T10 SAM model for ease of adoption. The UFS device is a universal data storage and communication media. It is designed to cover a wide area of applications as smart phones, cameras, organizers, PDAs, digital recorders, MP3 players, internet tablets, electronic toys, etc.

-xv-

# JEDEC Standard No. 220G

---

This page intentionally left blank.

---

-xvi-

# JEDEC Standard No. 220G
## Page 1

# UNIVERSAL FLASH STORAGE (UFS), VERSION 4.1

(From JEDEC Board Ballot JCB-24-49, formulated under the cognizance of the JC-64.1 Subcommittee on Electrical Specifications and Command Protocols.)

---

## 1 Scope

This standard specifies the characteristics of the UFS electrical interface and the memory device. Such characteristics include (among others) low power consumption, high data throughput, low electromagnetic interference and optimization for mass memory subsystem efficiency. The UFS electrical interface is based on an advanced differential interface by MIPI M-PHY specification which together with the MIPI UniPro specification forms the interconnect of the UFS interface. The architectural model is referencing the INCITS T10 (SCSI) SAM standard and the command protocol is based on INCITS T10 (SCSI) SPC and SBC standards.

# 2 Normative References

The following normative documents contain provisions that, through reference in this text, constitute provisions of this standard. For dated references, subsequent amendments to, or revisions of, any of these publications do not apply. However, parties to agreements based on this standard are encouraged to investigate the possibility of applying the most recent editions of the normative documents indicated. For undated references, the latest edition of the normative document referred to applies.

[MIPI-M-PHY], *MIPI Alliance Specification for M-PHY®, Version 5.0, 23 June 2021*

[MIPI-UniPro], *MIPI Alliance Specification for Unified Protocol (UniPro®), Version 2.0, 19 February 2022*

[MIPI-DDB], *MIPI Alliance Specification for Device Descriptor Block (DDB), Version 1.0*

[MIPI-AP], *Application Note for UniPro® v1.8*

[SAM], *INCITS T10 draft standard: SCSI Architecture Model – 5 (SAM–5), Revision 05, 19 May 2010*

[SPC], *INCITS T10 draft standard: SCSI Primary Commands – 4 (SPC-4), Revision 27, 11 October 2010*

[SBC], *INCITS T10 draft standard: SCSI Block Commands – 3 (SBC–3), Revision 24, 05 August 2010*

[JESD8-12], *1.2 V +/- 0.1V (Normal Range) and 0.8 - 1.3 V (Wide Range) Power Supply Voltage and Interface Standard for Nonterminated Digital Integrated Circuits, JESD8-12A.01, Sept 2007*

[HBM-MM], *JEDEC Recommended ESD Target Levels for HBM/MM Qualification, JEP155B, July, 2019*

[CDM], *JEDEC Recommended ESD-CDM Target Levels, JEP157A, April 2022*

[HMAC-SHA], *Eastlake, D. and T. Hansen, US Secure Hash Algorithms (SHA and HMAC-SHA), RFC 4634, July 2006.*

[JEP106], *Standard Manufacturer's identification code, JEP106BK, Sept 2024*

[JESD21], *Multichip Packages (MCP) and Discrete eMMC, e2MMC, and UFS, JESD21C, Jan 2020*

[JESD220-3], *UFS Host Performance Booster (HPB) Extension Specification, JESD220-3A, Sept 2020*

[JESD220-4], *UFS File Based Optimization (FBO) Extension Specification, JESD220-4 Version 1.01, Nov 2020*