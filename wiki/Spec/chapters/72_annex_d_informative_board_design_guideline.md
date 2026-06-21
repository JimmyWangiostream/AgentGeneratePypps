# JEDEC Standard No. 220G
## Page 505

---

## Annex D (Informative) Board Design Guideline

### D.1 Overview

This recommended Board Design Guideline can be used as the input parameters for System Board Simulation, for UFS 4.0 only.

The Z(f) values are calculated based on the following assumptions considering UFS 4.0 as following: (Note that if this assumption is not acceptable in any reason, please contact the device vendor and PMIC vendor to define your noise budget in PCB design.).

(1) The currents assumptions for DCR calculation, considering UFS 4.0
    A. For VCC/VCCQ/VCCQ2: 500mA/800mA/600mA
        i. Z(f) = (V/I)*(1% of PCB noise budget when BUCK type PMIC is used)
            1. Z(f) = (2.5V/500mA)*1% = 50 mΩ
            2. Z(f) = (1.2V/800mA)*1% = 15 mΩ (→ reflected as 18 in Table D.1)
            3. Z(f) = (1.8V/600mA)*1% = 30 mΩ
        ii. Z(f) = (V/I)*(1.5%~2% of PCB noise budget when LDO type PMIC is used)
            1. Z(f) = V/I = (2.5V/500mA)*1.5% = 75 mΩ (1.5% to give more noise margin to LDO type PMIC in case of VCC)
            2. Z(f) = V/I = (1.2V/800mA)*2% = 30 mΩ (→ reflected as 36 in Table D.1)
            3. Z(f) = V/I = (1.8V/600mA)*2% = 60 mΩ

(2) Inductance assumptions for Z(f) calculation for AC noise margin, considering UFS 4.0
    A. For VCC/VCCQ/VCCQ2: 1.2nH/0.4nH/0.8nH (1% of PCB noise budget)
        i. Z(f) = ωL = 2*pi*f*L
        ii. Z(f=20MHz) = 2 * 3.14 * f(=20MHz) * L (=1.2nH) → 151 (→ reflected as 160 in Table D.1)
        iii. Z(f=20MHz) = 2 * 3.14 * f(=20Mhz) * L (=0.4nH) → 50
        iv. Z(f=20MHz) = 2 * 3.14 * f(=20MHz) * L (=0.8nH) → 100
        v. Z(f) for 2MHz~10MHz is 50% of Z(f) for 20MHz.

# JEDEC Standard No. 220G
Page 506

## D.2 Allowed Max Impedance & Typical Cap for System Board PCB

### Table D.1 — Allowed Max Impedance & Typical Capacitor at System Board Design

| | Z(f) Spec⁽¹⁾ | | | | Capacitor⁽²⁾ | | |
|---|---|---|---|---|---|---|---|
| | DCR spec Freq: 0Hz (Buck type regulator) | DCR spec Freq: 0Hz (LDO type regulator) | 2MHz ~ 10MHz | 20MHz | | | |
| | | | | | Unit | Cap_A | Cap_B | Unit |
| Power | Max | Max | Max | Max | | Typ | Typ | |
| VCC(2.5V) | 50 | 75 | 80 | 160 | mΩ | 4.7 | 1.0 | uF |
| VCCQ(1.2V) | 18 | 36 | 25 | 50 | mΩ | 4.7 | 1.0 | uF |
| VCCQ2(1.8V) | 30 | 60 | 50 | 100 | mΩ | 4.7 | 1.0 | uF |

**NOTE 1** Z(f) is defined for all pins per voltage domain. Z(f) does not include the UFS package and silicon die. Refer to the figure D.1 for observation point.

**NOTE 2** This capacitor is optional. The number of capacitors and each capacity can be determined by OEM to meet the Z(f) spec. However, the bigger capacity than 1uF per capacitor is recommended to avoid the resonance around 20MHz. . Refer to the figure D.1 for Capacitor connections.

In case of Buck type PMIC case, Z(f) is calculated from the Feedback point to the UFS ball and observed at UFS ball. In case of LDO Type PMIC case, Z(f) is calculated from the PMIC output to the UFS ball and observed at UFS ball. See Figure D.1.

**(A) Buck type PMIC case :**

[Figure showing Buck type PMIC circuit diagram with feedback point, PMIC (BUCK) component connected through inductors and capacitors (Cap_A, Cap_B, Cap_N) to UFS device. The diagram indicates "Z(f) is observed at UFS ball" and notes that "PMIC part (L and C in PMIC part is provided by PMIC datasheet.)"]

**(B) LDO type PMIC case :**

[Figure showing LDO type PMIC circuit diagram with PMIC Output from PMIC (LDO) component connected through capacitors (Cap_A, Cap_B, Cap_N) to UFS device. The diagram indicates "Z(f) is observed at UFS ball" and notes "PMIC part"]

### Figure D.1 — Z(f) Measuring and Observation Point

# D.2 Allowed Max Impedance & Typical Cap for System Board PCB (cont'd)

[THIS IS FIGURE: A graph showing impedance Z(f) vs frequency. The y-axis shows "Ohms" and the x-axis shows frequency with markers at 2 MHz, 10, and 20. The curve shows relatively flat impedance at low frequencies, then rises sharply after 10-20 MHz.]

**Figure D.2 — Zprofile Z(f) of the System at the UFS Package Solder Ball (without UFS Component)**

A simplified electrical system load model for Z(f) with the general frequency response is shown in Figure D.3. The system resistance and inductance can be scaled to generalize the spec response to the UFS pins.

[THIS IS FIGURE: An electrical circuit diagram showing:
- Low Frequency Voltage source (AC symbol with ground)
- System Resistance (2-10MHz) - represented as a resistor
- System Inductance (>20MHz) - represented as an inductor
- Connected to "UFS Pins (per voltage)"

Below this is a frequency response graph showing Z(f) behavioral system load model response, with Z(f) on y-axis and Freq on x-axis, showing a flat response transitioning to an increasing response at higher frequencies.]

**Figure D.3 — A Simplified Z(f) System Electrical Model and Frequency Response of the Behavioral PDN Electrical Load Model without the UFS Component Per Voltage Domain Per Channel**

---
*JEDEC Standard No. 220G*  
*Page 507*

# JEDEC Standard No. 220G
## Page 508

### D.3 System Board PCB Noise Margin Recommendation

At design/simulation stage, Board designer could study which type of PMIC will be used, and can get the characteristics of the PMIC from PMIC vendor. Within DC voltage margin ( 4%/5%/5.6% ) as shown in Table D.2 and the PMIC noise characteristics, board designer can calculate the voltage noise margin remained for the system board PCB. Based on this, board designer can finally determine the PMIC type to use, and voltage drop margin remained for system board design. By using better characteristic PMIC, like LDO type which shows less than 50% less noise than Buck type normally, system board designer may have more PCB design voltage noise margin.

Table D.2 shows the budget PMIC & PCB budget in voltage level corresponding to the Z(f) value in Table D.1.

#### Table D.2 — Recommended Max PMIC & PCB Noise Margin

| Voltage spec | | | Voltage Margin | | | | in case of BUCK type PMIC | | in case of LDO type PMIC | |
|---|---|---|---|---|---|---|---|---|---|---|
| | min | typ | max | Neg delta | Neg % (margin) | Pos delta | Pos % (margin) | PMIC Budget (DC+AC) | PCB Budget (DC+AC) | PMIC Budget (DC+AC) | PCB Budget (DC+AC) |
| VCC | 2.4 | 2.5 | 2.7 | 0.1 | 4.0% | 0.2 | 8.0% | 2.0% | 2.0% | 1.5% | 2.5% |
| VCCQ | 1.14 | 1.2 | 1.26 | 0.06 | 5.0% | 0.06 | 5.0% | 3.0% | 2.0% | 2.0% | 3.0% |
| VCCQ2 | 1.7 | 1.8 | 1.95 | 0.1 | 5.6% | 0.15 | 8.3% | 3.6% | 2.0% | 2.6% | 3.0% |

If board designer wants to give more margin for LDO type PMIC for VCC, supplying typical voltage of 2.55V instead of 2.5V for VCC could give more noise margin for PMIC and Board for VCC as shown in Table D.3 alternative example

#### Table D.3 — (Alternative) 2.55 VCC to Allow More PMIC & PCB Noise Margin

| Voltage spec | | | Voltage Margin | | | | in case of BUCK type PMIC | | in case of LDO type PMIC | |
|---|---|---|---|---|---|---|---|---|---|---|
| | min | typ | max | Neg delta | Neg % (margin) | Pos delta | Pos % (margin) | PMIC Budget (DC+AC) | PCB Budget (DC+AC) | PMIC Budget (DC+AC) | PCB Budget (DC+AC) |
| VCC | 2.4 | 2.55 | 2.7 | 0.15 | 6.3% | 0.15 | 5.9% | 3.9% | 2.0% | 2.9% | 2.9% |
| VCCQ | 1.14 | 1.2 | 1.26 | 0.06 | 5.0% | 0.06 | 5.0% | 3.0% | 2.0% | 2.0% | 3.0% |
| VCCQ2 | 1.7 | 1.8 | 1.95 | 0.1 | 5.6% | 0.15 | 8.3% | 3.6% | 2.0% | 2.6% | 3.0% |