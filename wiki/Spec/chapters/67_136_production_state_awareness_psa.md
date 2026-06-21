# JEDEC Standard No. 220G
## Page 418

### 13.5 UFS Cache (cont'd)

Following commands shall be implemented by the device server to enable application client to control the behavior of the cache:

• PRE-FETCH commands: see 11.3.19 and 11.3.20.
• SYNCHRONIZE CACHE commands: see 11.3.24 and 11.3.25.

### 13.6 Production State Awareness (PSA)

#### 13.6.1 Introduction

UFS device can utilize knowledge about its production status and adjust internal operations accordingly. For example, content which was loaded into the storage device prior to device soldering might be corrupted, at a higher probability than in regular mode. The UFS device could use "special" internal operations for loading content prior to device soldering which would reduce production failures and use "regular" operations post-soldering.

The sensitivity for device soldering is a property of the logical unit, some logical units may be sensitive to device soldering while some logical units may not be sensitive to it. Before loading the data to the device the host should read bPSASensitive, to identify the LU which are sensitive to device soldering.

Pre-loaded data is data which is loaded on the device after device configuration is completed (bConfigDescrLock is set and reset of the device), and before device soldering to the host platform. The combined maximum amount of data which could be pre-loaded to all sensitive LUs is device specific and defined by dPSAMaxDataSize attribute.

#### 13.6.2 PSA flow

PSA feature is based on the device capability to uniquely identify which data is written before the soldering process. The PSA flow may be initiated only if all LBAs in logical units with bPSASensitive = 01h are unmapped. In case the host does not know if LBAs are unmapped, then it should set bPSAState 'Off', send an UNMAP command for the entire LBA range of each LU with bPSASensitive set to 01h, to unmap that data and re-start the PSA flow as described in the following.

Depicted in Figure 13.23 is the PSA flow. To start the PSA flow, the host first checks if PSA feature is supported by the device (see bUFSFeaturesSupport parameter in Device descriptor).

The host is expected to set dPSADataSize to indicate amount of data it plans to pre-load in all logical units with bPSASensitive = 01h. In case the host tries to set dPSADataSize > dPSAMaxDataSize, then the device shall return a General failure error.

The host writes bPSAState attribute to 'Pre-soldering' and then pre-loads the data in the logical units through WRITE commands.

The host should count towards dPSAMaxDataSize limit only data written through a WRITE command to a LU with bPSASensitive descriptor set to '1'. During PSA flow the host is not expected to write data to the same LBA more than once, in such case device behavior may be undefined.

# 13.6.2 PSA Flow (cont'd)

Once the host finishes pre-loading all LU (wrote total of dPSADataSize amount of data) the host is expected to change the state of bPSAState from 'Pre-soldering' to 'Loading Complete' to indicate to the device that pre-loading of data is complete.

Prior to soldering, at 'Loading Complete' bPSAState state, device may stop using special internal operations and resume regular operations. Therefore, the host should not write data to the device as data may be corrupted during soldering; a WRITE Command in this situation may result in an error.

After the setting of bPSAState to 'Loading Complete', the device may be soldered. The device shall set bPSAState to 'Soldered' during the processing of the first WRITE command after a power-up occurred with bPSAState = 'Loading Complete'.

---

*JEDEC Standard No. 220G  
Page 419*

# JEDEC Standard No. 220G
Page 420

## 13.6.2 PSA Flow (cont'd)

[This is a flowchart diagram showing the PSA (Preload Secure Application) Flow process. The flowchart contains the following elements connected by arrows:

**Start** (rectangle at top)
↓
**Host checks if device supports PSA** - Diamond decision box asking "bUFSFeaturesSupport[1] = 1b?" with "No" path leading to **Exit** box on right, and "Yes" path continuing down
↓
**Host reads Max Allowed Data Size to be preloaded (Device Descriptor, dPSAMaxDataSize)** (rectangle)
↓
**Host sets the amount of data it plans to pre-load (dPSADataSize)** (rectangle)
↓
**Host sets an Attribute to start the PSA Flow (bPSAState= 'Pre-soldering')** (rectangle)
↓
**Host pre-loads data** (rectangle)
↓
**Host sets bPSAState to 'Loading Complete'** (rectangle)
↓
**Host may Verify preloaded data** (rectangle)
↓
**Verify Pass?** (diamond decision box) with "No" path leading to **Host stops PSA flow (bPSAState= 'Off')** which connects to **Host unmap all pre-loaded data** which loops back to the stop PSA flow step
↓ "Yes"
**Device power down** (rectangle)
↓
**Device soldered on host platform** (rectangle)
↓
**Device power up** (rectangle)
↓
**First write command with bPSAState = 'Loading Complete'** (rectangle)
↓
**Device sets bPSAState to 'Soldered'** (rectangle)
↓
**Exit** (rectangle at bottom)]

**Figure 13.23 — PSA Flow**

# 13.6.2 PSA flow(cont'd)

Depicted in Figure 13.24 is the PSA state machine which describes the different states of the bPSAState attribute and the transitions between its states.

Host misbehavior of writing, during pre-soldering phase, more data than indicated by dPSADataSize may result in data corruption during device soldering.

At any time before setting bPSAState to 'Soldered' the host may re-start the PSA flow by switching bPSAState to 'Off', unmap all sensitive data and set bPSAState to 'Pre-soldering'.

A change in bPSAState attribute may involve additional operations by the device which may require some time. bPSAStateTimeout indicates the maximum allowed timeout in which the device may return a response.

[STATE DIAGRAM: The PSA state machine shows five circular states connected by arrows:

1. "bPSAState: 'Off'" at the top
2. "bPSAState: 'Pre-soldering'" below it
3. "bPSAState: 'Loading Complete'" in the middle
4. "bPSAState: 'Soldered'" at the bottom

The diagram shows transitions between states with labeled arrows:
- From Off to Pre-soldering: "Start: bPSAState set by the host before pre-loading at production"
- From Pre-soldering to Loading Complete: "Write Complete: bPSAState changed by host after host writes dPSADataSize amount of data"
- From Loading Complete to Soldered: "Device power up and Host write data at bPSAState 'Loading Complete'"
- From any pre-soldered state back to Pre-soldering: "Restart: bPSAState set by the host at production followed by Unmap of all allocated LBAs"

The diagram is divided by a dashed horizontal line separating "Pre-soldering" (top) from "Post-soldering" (bottom) phases.]

**Figure 13.24 — PSA state machine**

---
*JEDEC Standard No. 220G*  
*Page 421*