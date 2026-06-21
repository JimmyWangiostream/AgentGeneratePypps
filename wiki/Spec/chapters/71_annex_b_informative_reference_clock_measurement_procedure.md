# JEDEC Standard No. 220G
## Page 501

---

## Annex B (Informative) Reference Clock Measurement Procedure

In order to verify that the jitter of the Reference Clock meets the requirements of Table 6.4, two procedures are outlined in this annex, one for the measurement of the Random Jitter, the other for the measurement of the Deterministic Jitter.

Previous versions of this standard used the phase noise parameter as a measure of the quality of the reference clock signal. This parameter has been converted to random RMS jitter in this version of the standard so that it can be measured with a real-time Digital Storage Oscilloscope's (DSO) jitter separation tool.

### B.1 Random RMS Jitter Measurement Procedure

The Table B.1 represents the maximum random RMS jitter amount by different UFS reference clock frequencies.

#### Table B.1 — Maximum Random RMS Jitter Amount

| Reference Clock Frequency [MHz] | Integrated Phase Noise Power (Max) [dBc] | RMS Jitter (Max) [ps] |
|--------------------------------|------------------------------------------|----------------------|
| 19.2                           | -66                                      | 5.9                  |
| 26.0                           | -66                                      | 4.6                  |
| 38.4                           | -66                                      | 3.5                  |
| 52.0                           | -66                                      | 2.8                  |

In order to comply with the UFS Standards' jitter parameters, it is mandated that the random RMS jitter value of the DSO shall be less or equal than the value of Table B.1. To perform this test that complies with the phase noise parameter, it is recommended to use the TIE (time interval error) bandpass filter that is directly correlated to the specification, from 50 kHz to the Nyquist frequency of the reference clock, when extracting random RMS jitter value.

Note that, to correlate measurement difference between phase noise measurement equipment and jitter measurement equipment (DSO), the DSO should have a bandwidth limit to 2GHz so that DSO cannot detect noise from wider bandwidth input above 2GHz, the DSO has a sampling rate between 10Gsa/s to 20Gsa/s.

For consistency purpose, it is necessary to specify what kind of reference clock waveforms are to be used for this measurement. The reference clock can be a burst type of waveform or a continuous type of waveform depending on the operation, this measurement should be performed while DUT sends a continuous reference clock signal and acquires at least 500Kcycles of the clock period.

Note that this test is required for the DUT that supports HS Gear 3, 4, and 5 speed only. When DUT operates at HS Gear5 speed, the 19.2MHz and 26.0 MHz reference frequencies shall not be used, so the test is performed on the 38.4MHz and the 52.0 MHz reference cases.

The value of the reference clock's random RMS jitter for all supported reference clock frequency should be less than or equal to the maximum value specified in Table B.1, above in order to be considered conformant.

**Test Setup**
See B.4.

# JEDEC Standard No. 220G
## Page 502

### B.1 Random RMS Jitter Measurement Procedure (cont'd)

**Test Procedure**
1. Connect the DUT's reference clock output to the DSO with a cable.
2. Configure the DUT to transmit a continuous reference clock signal.
3. Capture more than 500K cycles of clock period waveform.
4. Measure the RJ rms value as described above.
5. Repeat steps 1 to 4 for other reference clock frequencies (if supported).

**Observable Results**
For all test cases:
• Verify that every reference clock's RJ rms is below or equal to the RMS jitter value.

### B.2 Deterministic Jitter Measurement Procedure

The UFS specification needs to test the reference clock's deterministic jitter for UFS devices that supports HS Gear3, 4, and 5 speed. This document covers how to test the UFS reference clock deterministic portion of jitter with a digital storage oscilloscope (DSO).

Same as in the previous random jitter test, it is recommended to use the TIE bandpass filter that is directly correlated to the specification, from 50KHz to the Nyquist frequency of the reference clock, when extracting random RMS jitter value.

Note that, to correlate measurement results of random jitter, DSO should have a bandwidth limit to 2GHz so that DSO cannot add noise from wider bandwidth input above 2GHz, while DSO has a sampling rate between 10Gsa/s to 20Gsa/s.

For consistency purpose, it is necessary to specify what kind of reference clock waveforms are to be used for this measurement. Because, the reference clock can be a burst type of waveform or a continuous type of waveform depends on the operation, this measurement should be performed while DUT sends a continuous reference clock signal and acquires at least 500Kcycles of the clock period.

The value of the reference clock's Deterministic jitter for all supported reference clock frequency should be less than or equal to 15ps in order to be considered conformant.

**Test Setup**
See B.4.

**Test Procedure**
1. Connect the DUT's reference clock output to the DSO with a cable.
2. Configure the DUT to transmit a continuous reference clock signal.
3. Capture more than 500K cycles of clock period waveform.
4. Measure deterministic jitter (DJ) value as described above.
5. Repeat Step 1to 4 for other reference clock frequencies (if supported).

**Observable Results**
For all test cases:
• Verify that every reference clock's DJ is below or equal to 15ps.

# JEDEC Standard No. 220G
Page 503

## B.3 Equipment Requirements

In order to perform the UFS reference clock test, the following resources are required:

1. 1 x UFS Host DUT, properly mounted on an SMA based (or similar lab-grade connector) evaluation PCB.
2. 1 x Real-Time Digital Storage Oscilloscope (DSO), 2GHz bandwidth minimum with 10-20G sampling rate.
3. 1 x Short SMA test cable for connecting evaluation PCB and oscilloscope.

## B.4 Test Setup

[Figure B.1 shows a test setup diagram with a green DUT (Device Under Test) board on the left containing a black component labeled "ref_clock" and several yellow SMA connectors. A black cable connects from one of these connectors to a blue DSO (Digital Storage Oscilloscope) on the right, which has a display screen showing a purple waveform and several gray control buttons below.]

**Figure B.1 — Test Setup**

Note on the above setup.

• The DUT is connected to the DSO using low loss 50Ω SMA or equivalent lab grade cable.

• The cable measures the single-ended reference clock signal with respect to PCB ground (VSS).

• The DUT should be configured to transmit continuous reference clock signaling for consistency purpose.

• The DSO vertical gain should be optimized so that the signaling spans as much of the vertical height of the DSO screen as possible to reduce jitter measurement error.

• The DSO bandwidth should be limited to 2GHz, so that the DSO does not include unnecessary noise from higher bandwidth.

# JEDEC Standard No. 220G
**Page 504**

---

## Annex C (Informative) Reference Clock Detection in HS-LSS : An Implementation Example

### C.1 Overview

This standard defines HS-LSS for faster initialization. In HS-LSS, the reference clock should be identified by device automatically.

This application note outlines a method for the UFS device to easily identify the current reference clock frequency given by the host at M-PHY layer initialization stage.

### C.2 Method Outline

1. The device has two counters, called SYS_CNT and REF_CNT, and reset those counters at the same time.

2. The SYS_CNT counter is clocked by the UFS device internal system clock SYS_CLK.

3. The REF_CNT counter is clocked by Reference Clock REF_CLK provided by the host.

4. Since the UFS device knows its internal system clock frequency, the UFS device can identify the reference clock frequency given by the host, based on the ratio of the counter value of SYS_CNT and REF_CNT.

[**Figure C.1 — REF CLK Frequency Detection in HS-LSS**

The figure shows a timing diagram and flowchart:

**Timing Diagram:**
- REF_CLK signal showing clock pulses
- REF_CNT counter showing values 0, 1, and incrementing to Y
- SYS_CLK signal showing higher frequency clock pulses
- SYS_CNT counter showing values 0, 1, 2, 3, 4, 5, 6, 7, 8 and incrementing to X
- Note: "X:Y ratio used to identify REF_CLK Frequency"

**Flowchart:**
- Start
- Decision diamond: "Is both REF_CLK Toggles & SYS_CLK Toggles?" (No loop back)
- Process box: "REF CLK frequency Detecting"
- Process box: "MPHY Ref clock Setting"
- END]