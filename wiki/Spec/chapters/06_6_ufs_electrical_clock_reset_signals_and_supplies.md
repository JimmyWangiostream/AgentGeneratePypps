# JEDEC Standard No. 220G
## Page 20

### 5.7 Mechanical

Packaging and requirements for UFS embedded device should adhere to the following guidelines if possible

• Reset and data transfer pins should be located in the second (PoP) or third row (MCP) in from the side of the package to prevent access.

---

## 6 UFS Electrical: Clock, Reset, Signals And Supplies

### 6.1 UFS Signals

Figure 6.1 represents a conceptual drawing of UFS device. Utilization of internal regulators and connection of those to different parts of the sub-system may differ per implementation.

[**Figure 6.1 — Conceptual UFS Device Block Diagram**: This is a complex block diagram showing the internal architecture of a UFS device. The diagram includes:

- Power supply inputs: VCC, VCCQ, VCCQ2 at the top
- Internal voltage regulators (VCC Regulator, VCCQ Regulator, VCCQ2 Regulator) shown in dashed boxes
- A charge pump circuit
- Core components including:
  - UFS controller on the left side
  - Core Logic in the center
  - Memory I/O on the right side of the core
  - Memory block on the far right
- Various signal pins including:
  - CCP-IN (capacitor input)
  - C+ and C- (charge pump outputs)
  - CPOUT1 and CPOUT2 (charge pump outputs)
  - RST_n (reset)
  - REF_CLK (reference clock)
  - DIN_t/c and DOUT_t/c (data input/output differential pairs)
  - LSS (low speed serial)
- Output voltage rails: VDDI, VDDIQ, VDDIQ2 with associated capacitors
- Ground connections: VSS
- Pull-up/pull-down resistors ROUT1 and ROUT2]

**NOTE 1** The memory core power supply may be connected to VCC power supply ball, or the VCC regulator output, while it is connected to the charge pump output if VCC ≈1.8 V and the memory requires 2.5 V core power supply.

**NOTE 2** The memory IO may consume power from any power supply: VCC, VCCQ or VCCQ2.

**NOTE 3** CCP-IN, CCP and CCP-OUT may be required only when internal charge pump is used.

**Figure 6.1 — Conceptual UFS Device Block Diagram**

# JEDEC Standard No. 220G
## Page 21

## 6.1 UFS Signals (cont'd)

### Table 6.1 — Signal Name and Definitions

| Name | Type | Description |
|------|------|-------------|
| VCC | Supply | Supply voltage for the memory devices |
| VCCQ | Supply | Supply voltage used typically for the memory controller and optionally for the PHY interface, the memory IO, and any other internal very low voltage block |
| VCCQ2 | Supply | Supply voltage used typically for the PHY interface and the memory controller and any other internal low voltage block |
| VDDIQ (1) | Input | Input terminal to provided bypass capacitor for VCCQ internal regulator |
| VDDIQ2 (1) | Input | Input terminal to provide bypass capacitor for VCCQ2 internal regulator |
| VDDi (1) | Input | Input terminal to provide bypass capacitor for VCC internal regulator |
| VSS | Supply | Ground |
| RST_n | Input | Input hardware reset signal. This is an active low signal |
| REF_CLK | Input | Input reference clock. When not active, this signal should be pull-down or driven low by the host SoC. |

**Differential input signals into UFS device from the host**

| Name | Type | Description |
|------|------|-------------|
| DIN_t or DIN0_t (2)<br>DIN_c or DIN0_c (2) | Input | Downstream data lane 0.<br>DIN_t is the positive node of the differential signal. |
| DIN1_t (2), DIN1_c (2) | Input | Downstream data lane 1. |

**Differential output signals from the UFS device to the host**

| Name | Type | Description |
|------|------|-------------|
| DOUT_t or DOUT0_t (3)<br>DOUT_c or DOUT0_c (3) | Output | Upstream data lane 0.<br>DOUT_t is the positive node of the differential signal. |
| DOUT1_t (3), DOUT1_c (3) | Output | Upstream data lane 1. |
| C+ | Input | Optional charge pump capacitor, positive terminal. For more information, please refer to 6.6 |
| C- | Input | Optional charge pump capacitor, negative terminal. For more information, please refer to 6.6 |
| CPOUT1, CPOUT2 | Input | Optional Charge pump output capacitor terminal. For more information, please refer to 6.6 |

# JEDEC Standard No. 220G
## Page 22

### 6.1 UFS Signals (cont'd)

#### Table 6.1 — Signal Name and Definitions (cont'd)

| Name | Type | Description |
|------|------|-------------|
| LSS^(4) | Input | Input Link Startup Sequence (LSS) mode.<br>0: low speed link startup sequence (LS-LSS)<br>1: high speed link startup sequence (HS-LSS)<br>This pin may be directly driven by the host or connected to external pull-up or pull-down according to the selected Link Startup Sequence mode. This value is expected to be fixed before RST_n is high to determine the Link Startup mode. |
| R_ZQ1/R_ZQ2 | Input | External Calibration Resistor (optional). Refer to datasheet to determine if resistors are needed. |

**NOTE 1** If there is no internal regulator requiring output capacitor then VDDi pins should be internally connected as follows: VDDi to VCC, VDDiQ to VCCQ, and VDDiQ2 to VCCQ2.

**NOTE 2** DIN0_t/_c and DIN1_t/_c apply if the device has two downstream lanes.

**NOTE 3** DOUT0_t/_c and DOUT1_t/_c apply if the device has two upstream lanes.

**NOTE 4** HS-LSS mode support is optional and LS-LSS mode support is mandatory. Refer to the vendor datasheet to determine if HS-LSS mode is supported or not. Based on HS-LSS support, a system vendor could connect LSS to establish the link in either LS-LSS or HS-LSS mode.

It is recommended to apply [HBM-MM] and [CDM] to all signals described in Table 6.1. See Table 6.2 for ESD specification This standard does not require use of the Machine Model for ESD qualification.

#### Table 6.2 — Electrostatic Discharge Sensitivity Characteristics

| Parameter | Symbol | Min | Max | Unit | NOTEs |
|-----------|--------|-----|-----|------|-------|
| Human body model (HBM) | ESD_HBM | 1000 | - | V | 1 |
| Charged-device model (CDM) | ESD_CDM | 250 | - | V | 2 |

**NOTE 1** Refer to ESDA/JEDEC Joint Standard JS-001-2024 for HBM measurement procedures.

**NOTE 2** Refer to ESDA/JEDEC Joint Standard JS-002-2022 for CDM measurement procedures.

# JEDEC Standard No. 220G
## Page 23

## 6.2 Reset Signal and LSS Signal

To meet the requirements of the JEDEC Standard [JESD8-12A], the RST_n and LSS signal voltages shall be within the specified ranges for VCCQ in Table 6.3.

### Table 6.3 — Reset Signal and LSS Signal Electrical Parameters

| Parameter | Symbol | Min | Max | Unit | Notes |
|-----------|--------|-----|-----|------|-------|
| Input HIGH voltage | VIH | 0.65*VCCQ | VCCQ+0.3 | V | For VCCQ as defined in Table 6.4 |
| Input LOW voltage | VIL | VSS-0.3 | 0.35*VCCQ | V | For VCCQ as defined in Table 6.4 |
| Input Capacitance | Cin | | 10 | pF | |
| Input leakage Current | Ilkg | | 10 | µA | |

## 6.3 Power Supplies

### Table 6.4 — UFS Power Supply Parameters

| Parameter | Symbol | Min | Max | Unit | NOTEs |
|-----------|--------|-----|-----|------|-------|
| VCC DC operating range | VCC | 2.4 | 2.7 | V | 3 |
| VCCQ DC operating range | VCCQ | 1.14 | 1.26 | V | 1, 3 |
| VCCQ2 DC operating range | VCCQ2 | 1.70 | 1.95 | V | 3 |
| Supply Voltage power up timing for 2.5 V | tPRUH | | 35 | ms | 2 |
| Supply Voltage power up timing for 1.8 V | tPRUL | | 25 | ms | 2 |
| Supply Voltage power up timing for 1.2 V | tPRUV | | 20 | ms | 2 |
| VCC internal regulator capacitor | CVDDI | 1 | | µF | |
| VCCQ internal regulator capacitor | CVDDIQ | 1 | | µF | |
| VCCQ2 internal regulator capacitor | CVDDIQ2 | 1 | | µF | |

NOTE 1 See [JESD8-12A.01].

NOTE 2 Power up timing starts when the supply voltage crosses 300 mV and ends when it reaches the minimum operating value.

NOTE 3 Depending on the vendor, valid power configuration may be defined in each UFS device vendor's data sheet. Refer to the vendor datasheet for the detail.

# JEDEC Standard No. 220G
## Page 24

### 6.3 Power Supplies (cont'd)

Figure 6.2 shows tPRUH, tPRUL and tPRUV timings.

[THIS IS FIGURE: Supply Voltage Power Up Timings diagram showing three voltage ramp-up sequences:

1. Left graph: VCC rising from 0V to VCCMIN over time period tPRUH, starting from 300mV threshold
2. Middle graph: VCCO2 rising from 300mV to VCCO2MIN over time period tPRUL  
3. Right graph: VCCO rising from 300mV to VCCOMIN over time period tPRUV

Each graph shows voltage on the y-axis and time (t) on the x-axis, with arrows indicating the direction of time progression.]

**Figure 6.2 — Supply Voltage Power Up Timings**

### 6.4 Reference Clock

The M-PHY specification defines the reference clock optional for the State Machine Type I [MIPI M-PHY]. As the PWM signaling is self-clocked the reference clock is not required for the data latching. Therefore, UFS devices shall be able to operate without reference clock in LS-MODE (SLEEP and PWM-BURST).

Still existence of the reference clock may be utilized to enable lower BER and faster HS-MODE PLL/DLL locking. Thus a UFS device shall implement a square wave single ended reference clock input and it requires the presence of a reference clock with the characteristics described in this sub-clause when operating in HS-MODE (STALL and HS-BURST). In order to avoid potential race conditions, it is recommended that such reference clock is already present when requesting a power mode change into Fast_Mode or FastAuto_Mode.

# 6.4 Reference Clock (cont'd)

## Table 6.5 — Reference Clock Parameters

| Parameter | Symbol | Nominal | Unit | NOTEs |
|-----------|--------|---------|------|-------|
| Frequency | f_ref | 19.2, 26.0, 38.4, 52.0 | MHz | 1 |
| | | Min | Max | | |
| Frequency Error | f_ERROR | -150 | +150 | ppm | |
| Input High Voltage | V_IH | 0.65 * VCCQ | | V | 2 |
| Input Low Voltage | V_IL | | 0.35 * VCCQ | V | 2 |
| Input Clock Rise Time | t_fRISE | | 2 | ns | 3 |
| Input Clock Fall Time | t_fFALL | | 2 | ns | 3 |
| Duty Cycle | t_DC | 45 | 55 | % | 4 |
| Random Jitter (f_ref = 19.2) | | | 5.9 | | |
| Random Jitter (f_ref = 26.0) | | | 4.6 | | |
| Random Jitter (f_ref = 38.4) | RJ_RMS | | 3.5 | ps | 5 |
| Random Jitter (f_ref = 52.0) | | | 2.8 | | |
| Deterministic Jitter | DJ_δδ | | 15 | ps | 6 |
| | RL_Rx | 100 | | kΩ | |
| Input Impedance | | | | | 7 |
| | CL_Rx | | 5 | pF | |

**NOTE 1** HS-BURST rates A and B are achieved with integer multipliers of f_ref.

**NOTE 2** Figure 6.4 shows the input levels V_IH_MAX to V_IH_MINS.

**NOTE 3** Clock rise time and clock full time shall be measured from 20% to 80% of the window defined by V_IH_MAX to V_IH_MINS, see Figure 6.4.

**NOTE 4** Clock duty cycle shall be measured at the crossings of the REF_CLK signal with the midpoint V_MID, defined as: V_MID = (V_IH_MAX + V_IH_MINS) / 2, see Figure 6.4.

**NOTE 5** The RJRMS magnitudes are based on the phase noise parameters of previous versions of this standard and replace them. RJRMS is computed with the integration range from 50 kHz to the Nyquist frequency of the reference clock.

**NOTE 6** Reference Clock frequencies of 19.2 MHz and 26.0 MHz cannot be used for HS-G5 and above, because the corresponding RJRMS values are beyond the allowable limit for HS-G5 operation. The frequency of the reference clock shall be 38.4 MHz or 52.0 MHz for HS-G5 and above operation.

**NOTE 7** RL_Rx and CL_Rx include Rx package and Rx input impedance.

---

*JEDEC Standard No. 220G*  
*Page 25*

# 6.4 Reference Clock (cont'd)

bRefClkFreq attribute indicates to the device the frequency of the REF_CLK signal in LS-LSS mode, and its default value corresponds to 52.0 MHz.

Table 6.6 provides an overview of the relationship between reference clock frequencies and HS operation.

## Table 6.6 — Reference Clock Frequency and HS Operation

| Reference Clock Frequency [MHz] | HS-G1 | HS-G2 | HS-G3 | HS-G4 | HS-G5 |
|--------------------------------|-------|-------|-------|-------|-------|
| 19.2                           | Y     | Y     | Y     | Y     | N     |
| 26.0                           | Y     | Y     | Y     | Y     | N     |
| 38.4                           | Y     | Y     | Y     | Y     | Y     |
| 52.0                           | Y     | Y     | Y     | Y     | Y     |

bRefClkFreq attribute can be written only if both sub-links are in LS-MODE. This attribute indicates the REF_CLK frequency. In HS-LSS mode, the UFS device shall detect the frequency of the REF_CLK signal. A stable REF_CLK signal is expected when RST_n signal goes high. REF_CLK is not expected to change in HS-Mode. See Annex C for details.

The reference clock is not required and it may be turned off when both SUB-LINKS have reached and are operating in one of the following M-PHY states:

• LS-MODE (SLEEP or PWM-BURST state)

• HIBERN8 state

If power mode change from HS-MODE to LS-MODE or HIBERN8 is initiated by UFS Host, then it shall be ensured that at least the minimum time duration defined by bRefClkGatingWaitTime has elapsed before turning off the reference clock, see Figure 6.3.

---

*JEDEC Standard No. 220G*  
*Page 26*

# 6.5 Reference Clock (cont'd)

[THIS IS FIGURE: Two timing diagrams showing Device Receiver and Device Transmitter operations. Each diagram shows signal timing for REF_CLK, toggling periods, and various control signals including PACP_PWR_req/cnt, FLRs, MK2, Trailing FLRs, and timing parameters like bRefClkGatingWaitTime, Device_PA_MinRxTrailingClocks, Host_PA_MinRxTrailingClocks, 20 UIHS, TOB, and DIF-N.]

**Figure 6.3 — bRefClkGatingWaitTime**

UFS Host may start a timer when DME_POWERMODE.ind is received for HS-MODE to LS-MODE transition or DME_HIBERNATE_ENTER.ind is received for HS-MODE to HIBERN8 transition.

In addition to bRefClkGatingWaitTime, Device PA_MinRxTrailingClocks and Host PA_MinRxTrailingClocks should be considered to determine when the reference clock may be stopped. In case of a transition from HS-MODE to HIBERN8 to reach the UFS-DeepSleep power mode, this constraint for turning off the reference clock shall be applied as well.

Unipro layer defines re-initialization process using PA_INIT mechanism. See [MIPI-Unipro] for details. During this process both the sub-links may briefly enter LS-MODE before returning to HS-MODE. The reference clock shall not be gated during the entire PA_INIT procedure.

The reference clock shall be turned ON and stably running before initiation of the state transition to STALL from a SLEEP or HIBERN8 state. Reference Clock shall not be gated in HS modes.

---
JEDEC Standard No. 220G  
Page 27

# 6.4 Reference Clock (cont'd)

Figure 6.4 shows clock rise time and fall time measurements.

[FIGURE 6.4: A timing diagram showing clock input levels, rise time, and fall time. The diagram displays a clock signal transitioning between VCCQ (high) and VSS (low) levels, with voltage thresholds marked at VIH,MIN (80%), VMID (middle), and VIL,MAX (20%). The rise time (tRISE) and fall time (tFALL) are indicated with arrows showing the transition periods between the 20% and 80% voltage levels.]

**Figure 6.4 — Clock Input Levels, Rise Time, and Fall Time**

## 6.5.1 HS Gear Rates

Table 6.7 defines the data rate values for the two rate series with respect REF_CLK frequency value (fref).

**Table 6.7 — HS-BURST Rates**

| HS-GEAR | Rate A-series | Rate B-series | Unit |
|---------|---------------|---------------|------|
|         | fref | | fref | |
|         | 19.2 / 26.0 / 38.4 / 52.0 | 19.2 / 38.4 | 26.0 / 52.0 |
| HS-GEAR1 | 1248 ⁽²⁾ | 1459.2 | 1456.0 | Mbps |
| HS-GEAR2 | 2496 | 2918.4 | 2912.0 | Mbps |
| HS-GEAR3 | 4992 | 5836.8 | 5824.0 | Mbps |
| HS-GEAR4 | 9984 | 11673.6 | 11648.0 | Mbps |
| HS-GEAR5 | 19968 | 23347.2 | 23296.0 | Mbps |

NOTE 1 "Mbps" indicates 1,000,000 bits per second.

NOTE 2 1248 Mbps with fref = 38.4 MHz may be obtained using a prescaler. fref * M /P, M = 65 (PLL multiplier), P = 2 (Prescaler).

# 6.5.2 Host Controller Requirements for Reference Clock Generation

## Table 6.8 — Host Controller Reference Clock Parameters

| Parameter | Symbol | Min | Max | Unit | NOTEs |
|-----------|---------|-----|-----|------|-------|
| DC Output High Voltage | V_OH | 0.75 * VCCQ | | V | 1, 2 |
| DC Output Low Voltage | V_OL | | 0.25 * VCCQ | V | 1, 2 |
| Output Clock Rise Time | t_RISE | | 2 | ns | 3 |
| Output Clock Fall Time | t_FALL | | 2 | ns | 3 |
| Test Load Impedance | RL_Test | 100 | | kΩ | 1, 4, 5 |
| | CL_Test | 20 | | pF | 1, 4, 5 |

**NOTE 1** Output load resistive and capacitance component are defined as 20 pF shunted by 100 KΩ.

[**Figure 6.5 — Test Load Impedance**: Circuit diagram showing a TX buffer connected to REF_CLK output, with V_RefClk measured across a parallel combination of 20pF capacitor and 100KΩ resistor connected to VSS]

**NOTE 2** Figure 6.6 shows Output driver and Input receiver levels. REF_CLK driver AC voltage (e.g., ring back) shall be kept inside Output Voltage limit.

[**Figure 6.6 — Output Driver and Input Receiver Levels**: Voltage level diagram showing:
- VCCQ_MAX at the top
- TX Output High region (blue) with V_OH, MIN threshold
- RX Input High region (green) with V_IH, MIN threshold  
- RX Threshold Region (red) in the middle
- RX Input Low region (green) with V_IL, MAX threshold
- TX Output Low region (blue) with V_OL, MAX threshold
- VSS at the bottom
- Left side labeled "Transmitter", right side labeled "Receiver"]

---
JEDEC Standard No. 220G  
Page 29

# JEDEC Standard No. 220G
Page 30

## 6.4.2 Host Controller Requirements for Reference Clock Generation (cont'd)

### Table 6.8 — Host Controller Reference Clock Parameters (cont'd)

**NOTE 3** Clock rise time and clock fall time shall be measured from 20% to 80% of the window defined by V_OH,MAX and V_OH,MIN.

[Figure 6.7 shows a clock signal waveform diagram with:
- VCCQ at the top
- V_OH,MIN marked at 80% level
- V_OL,MAX marked at 20% level  
- VSS at the bottom
- t_ORISE marked as the rise time between 20% and 80% levels
- t_OFALL marked as the fall time between 80% and 20% levels]

**Figure 6.7 — Clock Output Levels, Rise Time and Fall Time**

**NOTE 4** Including transmitter output, Tx package, interconnect, Rx package and Rx input impedance

**NOTE 5** The Test Load Impedance is placed at the output of the driver, with the shortest interconnect.

## 6.6 External Charge Pump Capacitors (Optional)

In order to produce memory devices that can accommodate a low voltage core supply (VCC=1.8 V) an internal charge pump circuit may be required.

Charge pump circuit requires extra-sized passive components. An optional usage of external charge pump capacitors is provided.

Figure 6.1 shows the electrical connections required in case of charge pump implementation that uses external capacitors. Table 6.9 provides description of the capacitors to be used.

### Table 6.9 — Charge Pump Capacitors Description

| Capacitor Name | Min | Typ | Max | Description |
|----------------|-----|-----|-----|-------------|
| C_CP-IN | TBD | 4.7uF | TBD | When charge pump is used, this capacitor is used as the charge pump input bypass capacitor. When charge pump is not used this capacitor is used as a bypass capacitor for the memory. |
| C_CP-OUT | TBD | 4.7uF | TBD | Charge pump output bypass capacitor |
| C_CP | TBD | 0.22uF | TBD | Charge pump flying capacitor |

The charge pump capacitors are optional for UFS devices. Table 6.10 specifies name and description of the balls for connecting external charge pump capacitors.

# 6.5 External Charge Pump Capacitors (Optional) (cont'd)

## Table 6.10 — Charge Pump Related Ball Names

| Ball Name | Description |
|-----------|-------------|
| C+ | CCP capacitor's positive terminal |
| C- | CCP capacitor's negative terminal |
| CPOUT1, CPOUT2 | Charge pump output capacitor (2 balls)¹ |

**NOTE 1** Two CPOUT balls are required to reduce inductance, improve ripple and transient response

**NOTE 2** The given capacitors shall be placed close to the memory device to minimize the inductance. As a guideline for package design, it is recommended to place the CP related balls close to each other and close to the edge of the package.

# 6.7 ZQ Calibration Resistor (optional)

In order to produce memory devices that can accommodate high performance, ZQ calibration resistors may be required.

A ZQ calibration resistor requires a passive component. An optional usage of external ZQ calibration resistors is provided.

Figure 6.1 shows an example of the electrical connections needed if the ZQ calibration implementation uses external resistors. Table 6.11 provides a description of the resistors to be used.

## Table 6.11 — ZQ Calibration Resistors Description

| Resistor Name | Type | Nominal | Accuracy | Description |
|---------------|------|---------|----------|-------------|
| RZQ1 | Input | Vendor specific | 1% | Optional resistor for device internal calibration |
| RZQ2 | Input | 300ohm | 1% | Optional resistor for NAND interface's calibration |

---
*JEDEC Standard No. 220G*  
*Page 31*

# JEDEC Standard No. 220G
Page 32

## 6.8 Absolute Maximum DC Ratings and Operating Conditions

Stresses greater than those listed in Table 6.12 may cause permanent damage to the device. This is a stress rating only, and functional operation of the device at these or any other conditions above those indicated in the operational sections of this standard is not implied. Exposure to absolute maximum rating conditions for extended periods may affect reliability.

### Table 6.12 — Absolute Maximum DC ratings and Operating Conditions

| Parameter | Symbol | Min | Max | Unit | Notes |
|-----------|--------|-----|-----|------|-------|
| Voltage on M-PHY signals | | -0.2 | 0.9 | V | 1 |
| Voltage on REF_CLK, RST_n signals | | -0.2 | 1.5 | V | 1 |
| VCC supply voltage | VCC | -0.3 | 3.2 | V | 1 |
| VCCQ supply voltage | VCCQ | -0.2 | 1.5 | V | 1 |
| VCCQ2 supply voltage | VCCQ2 | -0.2 | 2.4 | V | 1 |
| Storage Temperature Standard | TSTG_STD | -40 | 85 | °C | 2, 5 |
| Operating Temperature Standard | TOPER_STD | -25 | 85 | °C | 3, 5 |
| Storage Temperature Extended | TSTG_EXT | -40 | 105 | °C | 2, 4, 5 |
| Operating Temperature Extended | TOPER_EXT | -40 | 105 | °C | 3, 4, 5 |

**NOTE 1** Voltage relative to VSS.

**NOTE 2** Storage Temperature is the package case surface temperature of the UFS device when power is not supplied.

**NOTE 3** Operating Temperature is the package case surface temperature of the UFS device when UFS device is operating.

**NOTE 4** This is supported only when the device supports Extended Temperature which is indicated by bit[6] of bUFSFeaturesSupport as "1".

**NOTE 5** For device safety (e.g., keeping designed reliability characteristics of device), in case package case temperature exceeds defined temperature range, device may not guarantee proper operation.

# 6.9 AC and DC Operating Conditions

Table 6.13 shows the DC and AC voltage operating conditions for UFS.

## Table 6.13 —AC and DC Voltage Operating Conditions

| Symbol | Low Freq Voltage Range (1)(3) (DC to 2MHz) |  |  | Unit | AC Noise voltage Range (2)(3) ( 2MHz ~ ) |  |
|--------|-----|-----|-----|------|-----|-----|
|        | Min | Typ | Max |      | Spec | Unit |
| UFS    |     |     |     |      |      |      |
| VCC    | 2.4 | 2.5 | 2.7 | V    | Within ± 3% of the typical voltage | V |
| VCCQ   | 1.14| 1.2 | 1.26| V    |      | V |
| VCCQ2  | 1.70| 1.8 | 1.95| V    |      | V |

**NOTE 1** DC to 2 MHz voltage range includes all noise measured at any UFS device VCC/VCCQ/VCCQ2 power ball, both DC and AC ripple fluctuations.

**NOTE 2** More than 2MHz, the AC noise shall be less than +/- 3% of the typical voltage measured at any UFS device VCC/VCCQ/VCCQ2 power ball. This AC noise specification is aligned to AC noise spec of the JEDEC NAND standard( JESD230D ) for standard and related product's compatibility and interoperability.

**NOTE 3** The voltage including DC noise and AC noise should be between Min and Max voltage spec value in any case measured at any UFS device VCC/VCCQ/VCCQ2 power ball. Refer to the Figure 6.8 illustrating that the DC noises and AC noises shall be within the Min and Max voltage spec measured at any UFS device VCC/VCCQ/VCCQ2 power ball.

[**Figure 6.8 — DC and AC voltage Range for VCC/VCCQ/VCCQ2**: This figure shows a waveform diagram with two sections. The top section shows voltage fluctuations between VCC/VCCQ/VCCQ2(max) and VCC/VCCQ/VCCQ2(typ), with AC ripple variations labeled as "VCC/VCCQ/VCCQ2_ac_ripple(pk-pk)". The bottom section shows similar voltage fluctuations between VCC/VCCQ/VCCQ2(typ) and VCC/VCCQ/VCCQ2(min), also with AC ripple variations labeled as "VCC/VCCQ/VCCQ2_ac_ripple(pk-pk)". The diagram illustrates how both DC and AC voltage variations must stay within the specified minimum and maximum voltage ranges.]

---
*JEDEC Standard No. 220G*  
*Page 33*