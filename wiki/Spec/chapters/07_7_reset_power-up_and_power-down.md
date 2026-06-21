# 7 Reset, Power-Up And Power-Down

## 7.1 Reset

Following sub-clauses define the means for resetting the UFS device or a layer of it.

### 7.1.1 Power-on Reset

A power-on reset is obtained switching the VCCQ, VCCQ2 and VCC power supplies off and back on. The UFS device shall have its own power-on detection circuitry which puts the UFS device and all the different layers of it into a defined state after the power-on.

[**Figure 7.1 — Power-on Reset**

This is a detailed diagram showing the power-on reset process for UFS devices. The diagram consists of two main sections - Host and Device:

**Host Side:**
- Application Client with "Power on Events" (yellow box)
- Hard Reset (pink box)
- DME SAP (blue circle)
- Device Management Entity (DME) with multiple Sub Access Points (SAPs) for different layers:
  - SAP L4: Transport Layer (L4)
  - SAP L3: Network Layer (L3) 
  - SAP L2: Data Link Layer (L2)
  - SAP L1.5: PHY Adapter Layer (L1.5)

**Device Side:**
- Two Logical Units (LU I and LU n) each with "Logical Unit Reset" (pink boxes)
- "Power on Events" (yellow box)
- Hard Reset (pink box)
- Device Manager
- DME SAP (blue circle)
- Device Management Entity (DME) with corresponding SAPs for all layers

**Communication Flow:**
1. DME_RESET.req (flows from both Host and Device DME SAPs)
2. DME_RESET.cnf_L (confirmation response)

**Legend:**
- Yellow boxes = Event
- Pink boxes = Action]

---
*JEDEC Standard No. 220G*  
*Page 34*

# 7.1.2 Hardware Reset

A dedicated hardware reset signal is defined for the UFS device.

[**Figure 7.2 — Hardware Reset**

This is a system diagram showing the hardware reset flow between Host and Device components:

**Host side:**
- Application Client generates HW Reset Event
- Hard Reset component
- DME SAP layer connected to Device Management Entity (DME)
- Protocol stack with Transport Layer (L4), Network Layer (L3), Data Link Layer (L2), and PHY Adapter Layer (L1.5)

**Device side:**
- Multiple Logical Units (LU 1 through LU n) each with Logical Unit Reset capability
- HW Reset Event flows to Device Manager
- Hard Reset component
- DME SAP layer connected to Device Management Entity (DME)  
- Same protocol stack as host side

The diagram shows two main signals:
1. DME_RESET.req (flowing from host to device)
2. DME_RESET.cnf_L (confirmation signal)

Legend indicates Events (yellow boxes) and Actions (pink boxes)]

Figure 7.3 shows the hardware reset AC timings.

[**Figure 7.3 — Reset AC timings**

This is a timing diagram showing the RST_n signal with the following periods marked:
- tRSTW: RST_n Pulse Width (active low period)
- tRSTH: RST_n High Period (Interval) - the time between reset pulses]

## Table 7.1 — Reset timing parameters

| Symbol | Comment | Min | Max | Unit |
|--------|---------|-----|-----|------|
| tRSTW | RST_n Pulse Width | 1 | | μs |
| tRSTH | RST_n High Period (Interval) | 1 | | μs |
| tRSTF | RST_n filter | 100 | | ns |

The reset signal is active low. The UFS device shall not detect 100 ns or less of positive or negative RST_n pulse. The UFS device shall detect more than or equal to 1μs of positive or negative RST_n pulse width.

---
*JEDEC Standard No. 220G*  
*Page 35*

# 7.1.3 EndPointReset

The EndPointReset feature is defined in the MIPI UniPro specification.

Function call from Host Application Client to Host UniPro via DME_SAP:DME_ENDPOINTRESET.req = 1.

Device Manager receives the EndPointReset function call from the device UniPro via DME_SAP and executes the EndPointReset function.

A UFS device shall completely reset itself on reception of an EndPointReset: UFS Flags (except Power on reset UFS Flags), UFS Attributes (except Power on reset UFS Attributes), and UniPro attributes are reset to their default value and the UniPro link startup is initiated.

The device may need to be configured again since attributes are reset to their default value. Further, downloading the boot code from the UFS device is optional, and is based on system-level conditions. A UFS Host should ignore the reception of an EndPointReset from a UFS device.

[**Figure 7.4 — EndPointReset**: This is a sequence diagram showing the communication flow between Host and Device during an EndPointReset operation. The diagram shows:

**Host side:**
- Application Client at the top
- Host SAP layer
- Device Management Entry (DME) connected to multiple protocol layers (2.5 through 2.5a) for Transport Layer (L4), Network Layer (L3), Data Link Layer (L2), and PHY Adapter Layer (L1.5)

**Device side:**
- Logical Unit Reset boxes (LU 1 through LU n) at the top
- Device Manager connected to Hard Reset
- Device SAP layer  
- Device Management Entry (DME) connected to multiple protocol layers (2.5 through 2.5a) for Transport Layer (L4), Network Layer (L3), Data Link Layer (L2), and PHY Adapter Layer (L1.5)

**Message flow:**
1. DME_ENDPOINTRESET.req (Host to Device SAP)
2. PA_LM_ENDPOINTRESET.req (Host DME to PHY layer)
3. TRG_EPR (between PHY layers)
4. PA_LM_ENDPOINTRESET.ind (Device PHY to DME)
5. DME_ENDPOINTRESET.ind (Device SAP)

The diagram includes a legend showing Event (yellow) and Action (pink) indicators.]

---
*JEDEC Standard No. 220G*  
*Page 36*

# 7.1.4 Logical Unit Reset

The Logical Unit Reset feature is defined in the SCSI Architectural Model [SAM]. This reset is triggered via the SCSI Task Management features described in 10.9.8.4.

LU reset (LU 0, ... , Maximum LU specified by bMaxNumberLU):

Function Call from Host Application Client to Host UTP via UTP_TM_SAP: Task management LOGICAL UNIT RESET (IN ( I_T_L Nexus )).

LU Task manager shall receive the function call from device UTP via UTP_TM_SAP and executes the LU reset function.

**NOTE** The Logical Unit Reset does not set the device parameters to their default value, therefore it is not recommended to use Logical Unit Reset to prepare the UFS device for a system boot.

[**Figure 7.5 — Logical Unit Reset**: This diagram shows the communication flow between Host and Device for a Logical Unit Reset operation. On the Host side, there's an Application Client that sends a Task Mgmt Request (LOGICAL UNIT RESET LU n) through various protocol layers including UTP SAP, T_SAP, Transport Layer (L4), Network Layer (L3), Data Link Layer (L2), and PHY Adapter Layer (L1.5). On the Device side, the request is received through corresponding layers and processed by the Device Manager, which handles LU 1 Logical Unit Reset through LU n Logical Unit Reset. The diagram shows the processing of a LOGICAL UNIT RESET Task Mgmt Req. A legend indicates Events in yellow and Actions in pink.]

## 7.1.5 Host UniPro Warm Reset

A UniPro Warm Reset event in the host is an indirect cause for a UFS device reset. See [MIPI-UniPro] for details.

The Host System resets its own UniPro stack; the host's UniPro stack reset activity is signaled to the UFS Device's UniPro stack via the DME_LINKLOST.ind message. In case the UFS device receives such DME_LINKLOST.ind message from the host system, it shall start process of re-initializing its own UniPro stack. In addition all UFS device level activity shall be aborted, task queue lists in all logical units shall be cleared and UFS power mode shall return to UFS-Sleep power mode or Active power mode depending on bInitPowerMode.

---
*JEDEC Standard No. 220G*  
*Page 37*

# 7.1.6 Summary of Resets and Device Behavior

Table 7.2 and Table 7.3 summarize the different types of reset and the UFS device behavior related to them.

## Table 7.2 — Reset States

| Reset Type | Initiator Device | Current Power Mode | Power Mode after Reset |  | Boot Process^(2) |
|------------|------------------|-------------------|----------------------|----------------------|------------------|
|            |                  |                   | bInitPowerMode = 00h | bInitPowerMode = 01h |                  |
| Power-on | Host | Any | UFS-Sleep^(1) | Active | Enabled |
| HW Reset | Host | Any | UFS-Sleep^(1) | Active | Enabled |
| EndPointReset | Host | Any | UFS-Sleep^(1) | Active | Enabled |
| LU Reset | Host | Active or Idle | Maintain the current power mode | Maintain the current power mode | Disabled |
| Host UniPro Warm Reset | Host | Any | UFS-Sleep^(1) | Active | Enabled |

**NOTE 1** At the end of the device initialization, the power mode transitions from Active to Pre-Sleep and then UFS-Sleep (after an implementation specific time).

**NOTE 2** The column "Boot process" shows after which type of reset the system can execute the boot process as described in 13.1, UFS Boot. The boot process is enabled if the reset event restores the UFS device to the default state: all parameters are set to the default value, queue are empty, etc.

## Table 7.3 — UniPro Attributes, UFS Attributes and UFS Flags reset

| Reset Type | UniPro Stack and Attributes | Volatile and Set Only Attributes and Flags^(1) | Power on reset Attributes and Flags^(1) | Logical Unit Queue |
|------------|---------------------------|------------------------------------------|--------------------------------------|-------------------|
| Power-on | Reset | Reset | Reset | Reset (all logical units) |
| HW Reset | Reset | Reset | Reset | Reset (all logical units) |
| EndPointReset | Reset | Reset | Not affected | Reset (all logical units) |
| LU Reset | Not affected | Not affected | Not affected | Reset (addressed logical unit) |
| Host UniPro Warm Reset | Reset | Reset | No affected | Reset (all logical units) |

**NOTE 1** See Table 14.25 and Table 14.27 for the definition of Flags and Attributes write access properties.

**NOTE 2** Values of Attributes and Flags with "Write once" or "Persistent" access property are kept after power cycle or any type of reset event.

# 7.2 Power Up Ramp

During power up, VCC and VCCQ2 should be applied as described in the following.

• Ta is the point where VCCQ or VCCQ2 power supply first reaches 300 mV.

• After Ta is reached, VCCQ2 should be greater than VCCQ - 200 mV.

• VCC can be ramped up independently from VCCQ value or VCCQ2 value.

• While powering on the device,
  ○ RST_n signal should be kept low
  ○ REF_CLK signal should be between VSS and VCCQ.

Figure 7.6 shows three power up ramp examples: case A and case B meet the requirement, while case C violates it in the time interval from Ta to Tb (VCCQ2 is lower VCCQ - 200 mV).

[THIS IS FIGURE: Power Up Ramps diagram showing three cases (A, B, C) with voltage ramp patterns. Each case shows three voltage lines (VCC, VCCQ2, VCCQ) rising from 0.3V over time. Case A and B show compliant ramping patterns, while Case C shows a violation where VCCQ2 drops below the required threshold between Ta and Tb. A green band indicates the acceptable voltage range between VCCQ-200 mV and VCCQ.]

**Figure 7.6 — Power Up Ramps**

NOTE 1 The green band represents the voltage range between VCCQ-200 mV and VCCQ.

---
*JEDEC Standard No. 220G*  
*Page 39*

# 7.3 Power Off Ramp

During power off, VCC and VCCQ2 should be removed as described as follows:

• Tx is the point where VCCQ or VCCQ2 power supply decreases under its minimum operating condition value specified (see Table 6.4).

• Tz is the point where VCCQ and VCCQ2 power supplies are below 300 mV.

• VCCQ2 should be greater than VCCQ - 200 mV between Tx and Tz.

• VCC can be ramped down independently from VCCQ value or VCCQ2 value.

• While powering off the device, RST_n signal and REF_CLK signal should be between VSS and VCCQ.

Figure 7.7 shows three power down ramp examples: case A and case B meet the requirement, while case C violates it in the time interval from Tb to Tz.

[Three power ramp diagrams showing voltage vs time:

**Case A**: VCC, VCCQ2, and VCCQ lines ramping down from high voltage to 0.3V, with Tx and Tz time markers. VCCQ2 stays above the green band (VCCQ-200mV to VCCQ range) throughout.

**Case B**: Similar layout to Case A, with VCC, VCCQ2, and VCCQ ramping down, maintaining proper voltage relationships between Tx and Tz.

**Case C**: Shows VCC, VCCQ2, and VCCQ ramping down, but with an additional Tb marker. VCCQ2 dips below the green band between Tb and Tz, with annotation "VCCQ2 is too low between Tb and Tz"]

NOTE 1 The green band represents the voltage range between VCCQ-200 mV and VCCQ.

**Figure 7.7 — Power Off Ramps**

The requirements described in this paragraph may not be met only in case of a sudden power off event. Uncontrolled power off should be avoided.

A violation of the power off ramp requirement should not result in any corruption of stored data.

---
JEDEC Standard No. 220G  
Page 40

# 7.4 UFS Device Power Modes and LU Power Condition

## 7.4.1 Device Power Modes

The device supports multiple power modes, which are controlled by the START STOP UNIT command and some attributes. The device power mode is independent of the bus state of the upstream or downstream links, which are controlled independently.

In order to minimize power consumption in a variety of operating environments, UFS devices support five basic power modes. One where the device is working, one where it is awaiting the next instruction, one where it has been put to sleep until the host wants it to awake, one where it has been put to deep sleep for the lowest power consumption, and a final mode where it can be turned off completely. These five power modes cover the need for the host to control the power consumed by the device, while still maintaining appropriate responsiveness from the device. There are also four transitional modes needed to facilitate the change from one mode to the next.

While in active mode processing instructions, there are several possible power scenarios. UFS devices may be expected to be battery powered. However, they may be plugged directly into a power source to recharge those batteries. During those times, a larger current may be available, and large amounts of data may be processed at the same time. There is also the possibility that the device is attached to a mobile device with a failing battery, in which case minimal power consumption is a requirement. Finally, there is the possibility that the host would know nothing of the device with which it is paired, and the device would need to be configured to operate within the host's current requirements.

In order to support these varied scenarios, UFS supports up to sixteen active configurations, each with its own current profile. The host may choose from either pre-defined or user-defined current profiles to deliver the highest performance possible. The following nine power modes are defined: Active, Idle, Pre-Active, UFS-Sleep, Pre-Sleep, UFS-DeepSleep, Pre-DeepSleep, UFS-PowerDown, Pre-PowerDown. The details of the system are described in the following sub-clauses.

### 7.4.1.1 Active Power Mode

In the Active power mode, the device is responding to a command or performing a background operation. In general, the M-PHY® interface may be in either STALL or HS-BURST state (if in high-speed operation), or SLEEP or PWM-BURST (if in low-speed operation).

The maximum power consumption in Active is determined by the bActivICCLevel attribute, and there are sixteen different current consumption levels. The maximum current consumption associated with each level for the three power supplies is described in the Power Parameters Descriptor by:

• wActivICCLevelsVCC[15:0] parameter for VCC,
• wActivICCLevelsVCCQ[15:0] parameter for VCCQ,
• wActivICCLevelsVCCQ2[15:0] parameter for VCCQ2.

For example, when the bActivICCLevel attribute is set to N, the maximum current consumed on VCC is specified by wActivICCLevelsVCC[N], the maximum current consumed on VCCQ is specified by wActivICCLevelsVCCQ[N], and the maximum current consumed on VCCQ2 is specified by wActivICCLevelsVCCQ2[N].

---
JEDEC Standard No. 220G  
Page 41

# JEDEC Standard No. 220G
Page 42

## 7.4.1.1 Active Power Mode (cont'd)

The assumption is that the current consumption levels are ordered in terms of performance: that is, that level 0 is lower performance than level 1, which is lower than level 2, and so on until level 15 which corresponds to the highest performance. The host may then read current consumption values associated with each level in the Power Parameters descriptor, and choose the highest performance levels which fits within its current limitations on each power supply.

Valid values for the bActiveICCLevel are from "00h" to "0Fh", other values are reserved and should not be set. A request to set to bActiveICCLevel should be made only when there is no outstanding operation, i.e., queue of all logical units is empty. If a request to set to bActiveICCLevel is raised when any queue is not empty, then device may be terminated with Query Response field set to "General Failure".

UFS devices should primarily use settings of "06h" and "0Ch", for normal (battery) and high (plugged in) power operating modes. See vendor datasheet for the maximum current consumption of those two Active ICC levels and the maximum current consumption of the UFS-Sleep power mode, the UFS DeepSleep power mode, and the UFS-PowerDown power mode.

The bInitActiveICCLevel parameter in the Device Descriptor allows the user to configure the Active ICC level after power on or reset.

The bInitPowerMode parameter in the Device Descriptor defines the power mode to which the device shall transition to after completing the initialization phase (fDeviceInit cleared to zero).

Active power mode may be entered from the Powered On power mode or the Pre-Active power mode after the completion of all setup necessary to handle commands.

The following power mode may be: Idle, Pre-Sleep, Pre-DeepSleep, or Pre-PowerDown.
All supported commands are available in Active Mode.

## 7.4.1.2 Idle Power Mode

The Idle power mode is reached when the device is not executing any operation. In general, the M-PHY® interface may be in STALL, SLEEP or HIBERN8 state. If background operations are continuing, the device should be considered Active power mode.

This mode may only be entered from an Active power mode, and the following state is always the Active power mode. The receipt of any command will transition the device into Active power mode.

## 7.4.1.3 Pre-Active Power Mode

The Pre-Active power mode is a transitional mode associated with Active power mode. The power consumed shall be no more than that consumed in Active power mode. The device shall remain in this power mode until all of the preparation needed to accept commands has been completed.

Pre-Active power mode may be entered from Pre-Sleep, UFS-Sleep, Pre-PowerDown, or UFS-PowerDown power modes. The following power mode is the Active power mode.

# JEDEC Standard No. 220G
## Page 43

### 7.4.1.3 Pre-Active Power Mode (cont'd)

While in Pre-Active power mode:

a) the Device well known logical unit may successfully complete only: START STOP UNIT command and REQUEST SENSE command; other commands may be terminated with CHECK CONDITION status, with the sense key set to NOT READY, with the additional sense code set to LOGICAL UNIT IS IN PROCESS OF BECOMING READY, see 7.4.1.11 for further details;

b) a REQUEST SENSE command shall terminated with GOOD status and provide pollable sense data with the sense key set to NO SENSE, and the additional sense code set to LOGICAL UNIT TRANSITIONING TO ANOTHER POWER CONDITION.

### 7.4.1.4 UFS-Sleep Power Mode

The UFS-Sleep power mode allows to reduce considerably the power consumption of the device.

VCC power supply may be turned off in this power mode.The UFS-Sleep power mode is entered from Pre-Sleep power mode.

While in UFS-Sleep power mode:

a) the Device well known logical unit may successfully complete only: START STOP UNIT command and REQUEST SENSE command; other commands may be terminated with CHECK CONDITION status, with the sense key set to NOT READY and the additional sense code set to LOGICAL UNIT NOT READY, INITIALIZING COMMAND REQUIRED, see 7.4.1.11 for further details;

b) a REQUEST SENSE command shall be terminated with GOOD status and provide pollable sense data with the sense key set to NOT READY and the additional sense code set to LOGICAL UNIT NOT READY, INITIALIZING COMMAND REQUIRED.

In general, the M-PHY® interface may be in STALL, SLEEP or HIBERN8 state, but it is recommended for the host to put the link in HIBERN8 state to lower power consumption.

VCC power supply should be restored before issuing START STOP UNIT command to request transition to Active, UFS-DeepSleep, or UFS-PowerDown power mode.

# 7.4.1.5 Pre-Sleep Power Mode

The Pre-Sleep power mode is a transitional mode associated with UFS-Sleep entry. The power consumed shall be no more than that consumed in Active power mode. Pre-Sleep may be entered from Active power mode.

The device shall automatically advance to UFS-Sleep power mode once any outstanding operations and management activities have been completed.

The device shall transition from Pre-Sleep power mode to Pre-Active power mode if START STOP UNIT command with POWER CONDITION = 1h is received.

While in Pre-Sleep power mode:

a) the Device well known logical unit may successfully complete only: START STOP UNIT command, REQUEST SENSE command and task management functions; other commands may be terminated with CHECK CONDITION status, with the sense key set to ILLEGAL REQUEST, see 7.4.1.11 for further details;

b) a REQUEST SENSE command shall be terminated with GOOD status and provide pollable sense data with the sense key set to NO SENSE and the additional sense code set to LOGICAL UNIT TRANSITIONING TO ANOTHER POWER CONDITION.

---

*JEDEC Standard No. 220G*  
*Page 44*

# JEDEC Standard No. 220G
Page 45

## 7.4.1.6 UFS-DeepSleep Power Mode

The UFS-DeepSleep power mode is used to achieve the lowest power consumption of the device. VCC power supply may be turned off in this power mode.

The UFS-DeepSleep power mode is entered from Pre-DeepSleep power mode.

While in UFS-DeepSleep power mode, the Device does not respond to any host commands. The M-PHY® interface may be put in UNPOWERED state by the UFS device to minimize the power consumption.

Host is expected to request the transition to UFS-DeepSleep power mode only when there is no pending task request or task management request. No further command are accepted in Pre-DeepSleep power mode and UFS-DeepSleep power mode. Also IMMED bit shall be set to zero for the START STOP UNIT command requesting transition to UFS-DeepSleep power mode. Device responds to START STOP UNIT command when the device is ready to transition from Pre-DeepSleep power mode to UFS-DeepSleep power mode. Transition to UFS-DeepSleep power mode occurs when the device link has entered HIBERN8 state. The only way to exit from this power mode is using a hardware reset or a power cycle. Host is expected to wake up the device by using a hardware reset or a power cycle after receiving response to START STOP UNIT command because UFS device may be performing management activities in Pre-DeepSleep power mode. After a hardware reset or a power cycle, UFS power mode shall return to UFS-Sleep power mode or Active power mode depending on bInitPowerMode.

## 7.4.1.7 Pre-DeepSleep Power Mode

The Pre-DeepSleep power mode is a transitional mode associated with UFS-DeepSleep entry. The power consumed shall be no more than that consumed in Active power mode. Pre-DeepSleep may be entered from Active or UFS-Sleep power mode.

The device sends the response with GOOD status to START STOP UNIT command with the POWER CONDITION field set to 4h after any outstanding operations and management activities have been completed. Then the device waits for HIBERN8 state transition. The host is expected to put the link in HIBERN8 state after receiving the response to the START STOP UNIT command. The device shall transit to UFS-DeepSleep power mode after HIBERN8 state transition is completed.

While in Pre-DeepSleep power mode, the Device does not respond to any host commands.

# 7.4.1.8 UFS-PowerDown Power Mode

The UFS-PowerDown power mode should be used prior to completely powering off the UFS memory device. All volatile data may be lost, and VCC or all power supplies can be removed.

This mode is automatically entered from the Pre-PowerDown power mode, at the completion of the power mode transition.

While in UFS-PowerDown power mode:

a) the Device well known logical unit may successfully complete only: START STOP UNIT command and REQUEST SENSE command; other commands may be terminated with CHECK CONDITION status, with the sense key set to NOT READY and the additional sense code set to LOGICAL UNIT NOT READY, INITIALIZING COMMAND REQUIRED, see 7.4.1.11 for further details;

b) a REQUEST SENSE command shall be terminated with GOOD status and provide pollable sense data with the sense key set to NOT READY, and the additional sense code set to LOGICAL UNIT NOT READY, INITIALIZING COMMAND REQUIRED.

## 7.4.1.9 Pre-PowerDown Power Mode

The Pre-PowerDown power mode is a transitional mode associated with UFS-PowerDown entry. The power consumed shall be no more than that consumed in Active power mode. Pre-PowerDown may be entered from Active or UFS-Sleep power mode.

The device shall automatically advance to UFS-PowerDown power mode once any outstanding operations and management activities have been completed.

The device shall transition to Pre-Active mode if START STOP UNIT command with POWER CONDITION field set to 1h is issued.

The following power mode may be UFS-PowerDown or Pre-Active power mode.

While in Pre-PowerDown power mode:

a) the Device well known logical unit may successfully complete only: START STOP UNIT command, REQUEST SENSE command and task management functions; other commands may be terminated with CHECK CONDITION status, with the sense key set to ILLEGAL REQUEST, see 7.4.1.11 for further details;

b) a REQUEST SENSE command shall be terminated with GOOD status and provide pollable sense data with the sense key set to NO SENSE and the additional sense code set to LOGICAL UNIT TRANSITIONING TO ANOTHER POWER CONDITION.

---
JEDEC Standard No. 220G
Page 46

# 7.4.1.10 Power Mode State Machine

The relationship amongst the different power modes is shown in Figure 7.8.

[THIS IS FIGURE: A state machine diagram showing power mode transitions. The diagram contains multiple oval-shaped nodes representing different power states: Powered On (light gray), Pre-Sleep (green), UFS-Sleep (dark green), Active (light yellow), Pre-Active (yellow), Idle (light blue), Pre-DeepSleep (purple), UFS-DeepSleep (purple), Pre-PowerDown (orange), and UFS-PowerDown (dark orange). Arrows connect these states showing possible transitions, with labels indicating SSU (Start Stop Unit) commands and PC (Power Condition) values. Some transitions are marked with conditions like "bInitPowerMode = 00h" and "M-PHY HIBERN8".]

(1) This transition may occur only if the SSU command that caused the transition to Pre-Sleep had IMMED set to one.
(2) This transition may occur only if the SSU command that caused the transition to Pre-PowerDown had IMMED set to one.
(3) This automatic transition shall occur at the end of device initialization if bInitPowerMode = 00h.
(4) The only way to exit from UFS-DeepSleep power mode is using a hardware reset or a power cycle.

**Figure 7.8 — Power Mode State Machine**

## 7.4.1.10.1 Transitions from Powered On Power Mode

The device shall enter in Powered On when: the power supplies are applied, after hardware reset, EndPointReset or Host UniPro Warm Reset.

**Transition from Powered_On to Active**
This transition shall occur when the device is ready to begin power on initialization.

## 7.4.1.10.2 Transitions from Pre-Active Power Mode

**Transition from Pre-Active to Active**
This transition shall occur when the device meets the requirements for being in Active power mode.

---
JEDEC Standard No. 220G
Page 47

# JEDEC Standard No. 220G
Page 48

## 7.4.1.10.3 Transitions from Active Power Mode

**Transition from Active to Idle**
This transition may occur when the device completes any ongoing operations.

**Transition from Active to Pre-Sleep**
This transition shall occur

• at the end of the device initialization and if the bInitPowerMode parameter is set to "00h", or

• if the device server processes a START STOP UNIT command with the POWER CONDITION field set to 2h.

**Transition from Active to Pre-DeepSleep**
This transition shall occur if the device server processes a START STOP UNIT command with the POWER CONDITION field set to 4h.

**Transition from Active to Pre-PowerDown**
This transition shall occur if the device server processes a START STOP UNIT command with the POWER CONDITION field set to 3h.

## 7.4.1.10.4 Transitions from Idle Power Mode

**Transition from Idle to Active**
This transition shall occur if the device processes a request that requires to be in Active power mode.

## 7.4.1.10.5 Transitions from Pre-Sleep Power Mode

**Transition from Pre-Sleep to Pre-Active**
This transition shall occur if the START STOP UNIT command that caused the transition to Pre-Sleep power mode had IMMED set to one, and when the device server processes a START STOP UNIT command with the POWER CONDITION field set to 1h.

**Transition from Pre-Sleep to Sleep**
This transition shall occur when the device meets the requirements for being in Sleep power mode.

## 7.4.1.10.6 Transitions from UFS-Sleep Power Mode

**Transition from UFS-Sleep to Pre-Active**
This transition shall occur if the device server processes a START STOP UNIT command with the POWER CONDITION field set to 1h.

**Transition from UFS-Sleep to Pre-DeepSleep**
This transition shall occur if the device server processes a START STOP UNIT command with the POWER CONDITION field set to 4h.

**Transition from UFS-Sleep to Pre-PowerDown**
This transition shall occur if the device server processes a START STOP UNIT command with the POWER CONDITION field set to 3h.

# JEDEC Standard No. 220G
## Page 49

### 7.4.1.10.7 Transitions from Pre-DeepSleep Power Mode

**Transition from Pre-DeepSleep to UFS-DeepSleep**
This transition shall occur if the device link has entered HIBERN8 state.

### 7.4.1.10.8 Transitions from UFS-DeepSleep Power Mode

**Transition from UFS-DeepSleep to Power On**
This transition shall occur if hardware reset or power cycle occurs.

### 7.4.1.10.9 Transitions from Pre-PowerDown Power Mode

**Transition from Pre-PowerDown to Pre-Active**
This transition shall occur if the START STOP UNIT command that caused the transition to Pre-PowerDown power mode had IMMED set to one, and when the device server processes a START STOP UNIT command with the POWER CONDITION field set to 1h.

**Transition from Pre-PowerDown to UFS-PowerDown**
This transition shall occur when the device meets the requirements for being in UFS-PowerDown power mode.

### 7.4.1.10.10 Transitions from UFS-PowerDown Power Mode

**Transition from UFS-PowerDown to Pre-Active**
This transition shall occur if the device server processes a START STOP UNIT command with the POWER CONDITION field set to 1h.

### 7.4.1.10.11 SCSI Command and UPIU Transactions

The current power mode may be retrieved reading the bCurrentPowerMode attribute.

bCurrentPowerMode is the only attribute the device is required to return in any power mode, with exception that device is not required to return any attribute in UFS-DeepSleep and Pre-DeepSleep power mode. If the device is not in Active power mode or Idle power mode, a QUERY REQUEST UPIU to access descriptors, flags, or attributes other than bCurrentPowerMode may fail.

By setting the IMMED bit to one during the START STOP UNIT command, the device can be instructed to respond at the entrance to the transitional mode, once the command is received.

The effects of concurrent power mode changes requested by START STOP UNIT commands with the IMMED bit set to one are vendor specific.

A START STOP UNIT command with the IMMED bit set to zero causing a transition to Active, UFS-Sleep, or UFS-PowerDown power modes shall not complete with GOOD status until the device reaches the power mode specified by the command.

A START STOP UNIT command with the IMMED bit set to zero causing a transition to UFS-DeepSleep power mode shall not complete with GOOD status until the device is ready to transition from Pre-DeepSleep power mode to UFS-DeepSleep power mode.

# JEDEC Standard No. 220G
## Page 50

### 7.4.1.10.11 SCSI Command and UPIU Transactions (cont'd)

The IMMED bit shall be set to zero for the START STOP UNIT command requesting transition to UFS-DeepSleep power mode, otherwise the command shall be terminated with CHECK CONDITION status with the sense key set to ILLEGAL REQUEST.

Table 7.4 summarizes which SCSI commands and UPIU transactions are allowed for each power mode.

#### Table 7.4 — Allowed SCSI Commands and UPIU for Each Power Mode

| Power Mode | SCSI Commands |  | UPIU Transactions |
|------------|---------------|------------------|-------------------|
|            | Device well known logical unit | Other logical units |                   |
| Active | Any commands | Any commands | Any UPIU |
| Idle | Any commands | Any commands | Any UPIU |
| Pre-Active | START STOP UNIT, REQUEST SENSE | No command | COMMAND UPIU, RESPONSE UPIU, REJECT UPIU, DATA IN UPIU, QUERY REQUEST UPIU, QUERY RESPONSE UPIU |
| UFS-Sleep | START STOP UNIT, REQUEST SENSE | No command | COMMAND UPIU, RESPONSE UPIU, REJECT UPIU, DATA IN UPIU, QUERY REQUEST UPIU, QUERY RESPONSE UPIU |
| Pre-Sleep | START STOP UNIT, REQUEST SENSE | No command Task Managem. Fun. | Any UPIU |
| UFS-DeepSleep | None | None | None |
| Pre-DeepSleep | None | None | None |
| UFS-PowerDown | START STOP UNIT, REQUEST SENSE | No command | COMMAND UPIU, RESPONSE UPIU, REJECT UPIU, DATA IN UPIU, QUERY REQUEST UPIU, QUERY RESPONSE UPIU |
| Pre-PowerDown | START STOP UNIT, REQUEST SENSE | No command Task Managem. Fun. | Any UPIU |

# JEDEC Standard No. 220G
Page 51

## 7.4.1.11 Responses to SCSI Commands

Table 7.5 defines the Device well known logical unit response to a START STOP UNIT command for a given power mode. It is assumed that the IMMED bit in START STOP UNIT commands is set to zero.

### Table 7.5 — Device Well Known Logical Unit Responses to SSU Command

| Current Power Mode | PC | STATUS | SENSE KEY | ASC, ASCQ |
|-------------------|----|---------|-----------|-----------| 
| Pre-Active | 1h | GOOD (1) | - | - |
|           | Others | CHECK CONDITION | NOT READY | LOGICAL UNIT NOT READY, START STOP UNIT COMMAND IN PROGRESS |
| Active | 1h, 2h, 3h, 4h | GOOD (1) | - | - |
|        | Others | CHECK CONDITION | ILLEGAL REQUEST | INVALID FIELD IN CDB |
| Pre-Sleep | 2h | GOOD (1) | - | - |
|           | Others | CHECK CONDITION | NOT READY | LOGICAL UNIT NOT READY, START STOP UNIT COMMAND IN PROGRESS |
| UFS-Sleep | 1h, 2h, 3h, 4h | GOOD (1) | - | - |
|           | Others | CHECK CONDITION | ILLEGAL REQUEST | INVALID FIELD IN CDB |
| Pre-DeepSleep | | Device is not able to accept START STOP UNIT command in this power mode |
| UFS-DeepSleep | | Device is not able to accept START STOP UNIT command in this power mode |
| Pre-PowerDown | 3h | GOOD (1) | - | - |
|               | Others | CHECK CONDITION | NOT READY | LOGICAL UNIT NOT READY, START STOP UNIT COMMAND IN PROGRESS |
| UFS-PowerDown | 1h, 3h | GOOD (1) | - | - |
|               | Others | CHECK CONDITION | ILLEGAL REQUEST | INVALID FIELD IN CDB |

NOTE 1 The START STOP UNIT command may not terminate with GOOD status for condition not due to CDB content.

Table 7.6 summarizes the response that the Device well known logical unit may provide to a command other than START STOP UNIT for various device power modes.

# JEDEC Standard No. 220G
Page 52

## 7.4.1.11 Responses to SCSI Commands (cont'd)

### Table 7.6 — Device Well Known Logical Unit Responses to Commands Other Than SSU

| Power Mode | Command | STATUS | SENSE KEY | ASC, ASCQ |
|------------|---------|---------|-----------|-----------|
| Pre-Active | REQUEST SENSE | GOOD (1) | - | - |
|            | Others (1) | CHECK CONDITION | NOT READY | LOGICAL UNIT IS IN PROCESS OF BECOMING READY |
| Pre-Sleep, Pre-PowerDown | REQUEST SENSE | GOOD (1) | - | - |
|            | Others (1) | CHECK CONDITION | ILLEGAL REQUEST | - |
| UFS-Sleep, UFS-PowerDown | REQUEST SENSE | GOOD (1) | - | - |
|            | Others (1) | CHECK CONDITION | NOT READY | LOGICAL UNIT NOT READY, INITIALIZING COMMAND REQUIRED |
| Pre-DeepSleep, UFS-DeepSleep | | Device is not able to accept any command in this power mode | | |

NOTE 1 Rows identified with "Others" define Device well known logical unit response to command other than START STOP UNIT command and REQUEST SENSE command.

Table 7.7 defines the pollable sense data for various device power modes.

### Table 7.7 — Pollable Sense Data for Each Power Modes

| Power Mode | SENSE KEY | ASC, ASCQ |
|------------|-----------|-----------|
| Pre-Active, Pre-Sleep, Pre-PowerDown | NO SENSE | LOGICAL UNIT TRANSITIONING TO ANOTHER POWER CONDITION |
| UFS-PowerDown, UFS-Sleep | NOT READY | LOGICAL UNIT NOT READY, INITIALIZING COMMAND REQUIRED |

## 7.4.2 Power Management Command: START STOP UNIT

When the START STOP UNIT command is sent to a logical unit, it can be used to enable or disable that logical unit, flush all cached logical blocks to the medium (for logical units that contain cache), or load or eject the medium. When the START STOP UNIT command is sent to the UFS Device well-known logical unit (W-LUN = 50h), it can be used to select the device power mode.

### Table 7.8 — START STOP UNIT Command

| Bit/Byte | 7 | 6 | 5 | 4 | 3 | 2 | 1 | 0 |
|----------|---|---|---|---|---|---|---|---|
| 0 |   |   | OPERATION CODE (1Bh) |   |   |   |   |   |
| 1 |   |   | Reserved |   |   |   |   | IMMED |
| 2 |   |   |   | Reserved |   |   |   |   |
| 3 |   |   | Reserved |   | POWER CONDITION MODIFIER (Reserved = 0000b) |   |   |   |
| 4 |   |   | POWER CONDITION |   | Reserved | NO_FLUSH | LOEJ = 0b | START |
| 5 |   |   |   | CONTROL (00h) |   |   |   |   |

# JEDEC Standard No. 220G
## Page 53

### 7.4.2 Power Management Command: START STOP UNIT (cont'd)

The POWER CONDITION field selects the desired mode. If the command is sent to a logical unit other than the Device well known logical unit, the POWER CONDITION field may be ignored.

#### Table 7.9 — START STOP UNIT Fields

| IMMED | No Flush | Power Condition | Start | LUN or WLUN LUN Field in UPIU | Action |
|-------|----------|-----------------|-------|-------------------------------|--------|
| 0 | - | - | - | - | Response is sent after change is complete. |
| 1 | - | - | - | - | Response is sent immediately after command decode |
| - | 0 | - | - | - | Dynamic data should be flushed to non-volatile storage |
| - | 1 | - | - | - | No requirements regarding dynamic data |
| - | - | 0h | 0 | 00h to N-1 ⁽¹⁾ 00h to N-1 ⁽¹⁾ | Stop the designated LU. |
| - | - | 0h | 1 | 00h to N-1 ⁽¹⁾ 00h to N-1 ⁽¹⁾ | Start the designated LU. |
| - | - | 1h | 0 | 50h D0h | Cause a transition to the Active power mode |
| - | - | 2h | 0 | 50h D0h | Cause a transition to the UFS-Sleep power mode |
| - | - | 3h | 0 | 50h D0h | Cause a transition to the UFS-PowerDown power mode |
| - | - | 4h | 0 | 50h D0h | Cause a transition to the Pre-DeepSleep power mode |

NOTE 1 The value of N is indicated by bMaxNumberLU parameter in the Geometry Descriptor.

# JEDEC Standard No. 220G
Page 54

## 7.4.3 Power Mode Control

Table 7.10 defines a series of attributes used to control the active current levels and power modes.

### Table 7.10 — Attribute for Power Mode Control

| Attribute Name | Size | Type | Description |
|---|---|---|---|
| bCurrentPowerMode | 1 byte | Read only | Current device Power Mode Status<br>00h: Idle power mode<br>10h: Pre-Active power mode<br>11h: Active power mode<br>20h: Pre-Sleep power mode<br>22h: UFS-Sleep power mode<br>30h: Pre-PowerDown power mode<br>33h: UFS-PowerDown power mode<br>Others: Reserved |
| bActiveICCLevel | 1 byte | Read /<br>Volatile | bActiveICCLevel defines the maximum current consumption allowed during Active mode.<br>00h: Lowest Active ICC level<br>...<br>0Fh: Highest Active ICC level<br>Others: Reserved<br>Valid range from 00h to 0Fh. |

Table 7.11 shows the Device Descriptor parameters that specify the power mode and the Active ICC level after power on or reset. See 14.1.5.2 for details about device configuration.

### Table 7.11 — Device Descriptor Parameters

| Parameter Name | Size | Description |
|---|---|---|
| bInitActiveICCLevel | 1 byte | Initial Active ICC Level<br>bInitActiveICCLevel defines the bActiveICCLevel value after power on or reset.<br>Valid range from 00h to 0Fh. |
| bInitPowerMode | 1 byte | Initial Power Mode<br>bInitPowerMode defines the Power Mode after device initialization or hardware reset<br>00h: UFS-Sleep Mode<br>01h: Active Mode<br>Others: Reserved |

# JEDEC Standard No. 220G
## Page 55

### 7.4.3 Power Mode control (cont'd)

Table 7.12 defines the parameters of the Power Parameters Descriptor. Each parameter is composed by sixteen elements, the size of each element is two bytes, and it is structured as shown in Table 7.13. Maximum peak current is defined as absolute maximum value not to be exceeded at all. The conditions under which wActiveCCLevelsVCC, wActiveCCLevelsVCCQ, and wActiveCCLevelsVCCQ2 are defined are:

• Maximum supported HS-GEAR mode with Rate B-series
• Maximum supported number of lanes enabled
• Worst case functional operation
• Worst case environmental parameters (temperature, … )

Each parameter of wActiveCCLevelsVCC, wActiveCCLevelsVCCQ, or wActiveCCLevelsVCCQ2 may have its own operating condition to reach to its maximum value.

#### Table 7.12 — Power Parameters Descriptor Fields

| Parameter Name | Size | Type | Description |
|---|---|---|---|
| wActiveCCLevelsVCC[15:0] | 32 bytes | Read Only | Active ICC Levels for VCC<br>Maximum peak current consumed from VCC in each of the sixteen current consumption levels defined for the Active mode. |
| wActiveCCLevelsVCCQ [15:0] | 32 bytes | Read Only | Active ICC Levels for VCCQ<br>Maximum peak current consumed from VCCQ in each of the sixteen current consumption levels defined for the Active mode. |
| wActiveCCLevelsVCCQ2 [15:0] | 32 bytes | Read Only | Active ICC Levels for VCCQ2<br>Maximum peak current consumed from VCCQ2 in each of the sixteen current consumption levels defined for the Active mode. |

#### Table 7.13 — Format for Power Parameter Element

| Field Name | Bit Range | Description |
|---|---|---|
| Unit | bit [15:14] | 00b:nA<br>01b:uA<br>10b:mA<br>11b: A |
| - | bit [13:12] | Reserved (00b) |
| Value | bit [11: 0] | The maximum current expected in each current consumption level |

# 7.4.4 Logical Unit Power Condition

Each logical unit may be in active power condition and stopped power condition. See [SPC] and [SBC] for the definition of these two logical unit power conditions.

All logical units shall be in the active power condition after power on or any type of reset event.

Transition from active power condition to stopped power condition shall occur if the device server processes a START STOP UNIT command with the START bit set to zero and the POWER CONDITION field set to 0h.

Transition from stopped power condition to active power condition shall occur if the device server processes a START STOP UNIT command with the START bit set to one and the POWER CONDITION field set to 0h.

START STOP UNIT command to change the logical unit power condition should be issued only if the device is in Active power mode or Idle power mode.

A request to move to the stopped power condition should be made only when the logical unit command queue is empty.

A transition in the device power mode state shall not change the logical unit power condition.

Table 7.14 defines the logical unit responses to SCSI commands for various device power modes, assuming that the logical unit is in active power condition. See 7.4.1.11 for details about Device well known logical unit.

## Table 7.14 — Logical Unit Response to SCSI Command

| Power Mode | COMMAND | STATUS | SENSE KEY | ASC, ASCQ |
|------------|---------|---------|-----------|-----------|
| Pre-Active, Pre-Sleep, UFS-Sleep, Pre-PowerDown, UFS-PowerDown | Any | CHECK CONDITION | NOT READY | - |
| Pre-DeepSleep, UFS-DeepSleep | Device is not able to accept any command in this power mode |

If the logical unit is in the stopped power condition, then the device server shall

• provide pollable sense data with sense key set to NOT READY and the additional sense code set to LOGICAL UNIT NOT READY, INITIALIZING COMMAND REQUIRED;

• terminate each media access command or TEST UNIT READY command with CHECK CONDITION status with the sense key set to NOT READY and the additional sense code set to LOGICAL UNIT NOT READY, INITIALIZING COMMAND REQUIRED.