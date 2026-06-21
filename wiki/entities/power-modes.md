---
type: entity
title: "UFS Power Modes"
tags: [power, state-machine, bCurrentPowerMode, start-stop-unit, vcc, vccq]
sources: [spec]
created: 2026-06-21
updated: 2026-06-21
aliases: [power mode, bCurrentPowerMode, PowerMode, UFS-Sleep, UFS-DeepSleep, UFS-PowerDown]
---

# UFS Power Modes

UFS devices support nine defined power modes (five stable + four transitional) controlled by the `START STOP UNIT` (SSU) command and the `bCurrentPowerMode` attribute. The current mode is readable at any time (except Pre-DeepSleep and UFS-DeepSleep).

## bCurrentPowerMode Values

| Value | State | Description |
|-------|-------|-------------|
| 00h | **Idle** | Device not executing any operation; may be reached from Active when all operations complete |
| 10h | **Pre-Active** | Transitional: preparing to accept commands; only SSU and REQUEST SENSE allowed on Device W-LUN |
| 11h | **Active** | Full operation; all commands accepted; all three power supplies on |
| 20h | **Pre-Sleep** | Transitional: flushing outstanding operations before entering UFS-Sleep |
| 22h | **UFS-Sleep** | Reduced power; VCC may be off; UniPro link recommended in HIBERN8 |
| 30h | **Pre-PowerDown** | Transitional: completing operations before UFS-PowerDown |
| 33h | **UFS-PowerDown** | Minimal power; device retains data; only SSU and REQUEST SENSE on Device W-LUN |
| 44h | **UFS-DeepSleep** | Deepest power saving (optional feature); no commands accepted; VCC and M-PHY may be fully off |
| — | **Pre-DeepSleep** | Transitional before UFS-DeepSleep; no commands accepted |

## Power State Machine (ASCII)

```
                     Power On / HW Reset / EndPointReset
                               |
                         [Powered On]
                               |
                           [Active] <-----------+
                          /   |   \             |
              SSU PC=2h  /    |    \ SSU PC=3h  |
                        /     |     \           |
                  [Pre-Sleep] |  [Pre-PowerDown]|
                       |      |  SSU PC=4h  |   |
                       v      |      v      |   |
                 [UFS-Sleep]  | [Pre-DeepSleep] |
                  /   \       |      |           |
      SSU PC=1h  /     \ SSU  |   HIBERN8        |
                /    PC=3h,4h |      v           |
         [Pre-Active]  \   [UFS-DeepSleep]       |
               |         \       (HW Reset only) |
               v           v                     |
            [Active]  [UFS-PowerDown]             |
                           |                     |
                      SSU PC=1h ------------------+
                           |
                        [Pre-Active] -> [Active]
```

**Key transitions:**
- `Active → Pre-Sleep`: SSU PC=2h, or end-of-init with `bInitPowerMode=00h`
- `Active → Pre-PowerDown`: SSU PC=3h
- `Active/UFS-Sleep → Pre-DeepSleep`: SSU PC=4h
- `UFS-DeepSleep exit`: **HW Reset or power cycle only** (no SSU accepted)
- `UFS-Sleep/UFS-PowerDown → Pre-Active`: SSU PC=1h

## START STOP UNIT — POWER CONDITION Field Values

| PC Value | Action | Sent to |
|----------|--------|---------|
| 0h | LU Start (START=1) or Stop (START=0) | LU (not Device W-LUN) |
| 1h | Transition to **Active** power mode | Device W-LUN (50h/D0h) |
| 2h | Transition to **UFS-Sleep** power mode | Device W-LUN |
| 3h | Transition to **UFS-PowerDown** power mode | Device W-LUN |
| 4h | Transition to **Pre-DeepSleep** → UFS-DeepSleep | Device W-LUN; IMMED must be 0 |
| 5h | UFS-Sleep or UFS-DeepSleep (legacy alias) | — |
| 7h | LU Control | — |
| Bh | Force Idle | — |
| Ch | Force Standby | — |

**IMMED bit:**
- `IMMED=0`: Response sent only after mode transition is complete.
- `IMMED=1`: Response sent immediately after command decode (transitional state begins).
- `IMMED` **must be 0** for PC=4h (UFS-DeepSleep); any other value → CHECK CONDITION, ILLEGAL REQUEST.

## Power Supply Status per Mode

| Power Mode | VCC | VCCQ | VCCQ2 | M-PHY |
|-----------|-----|------|-------|-------|
| Active | On | On | On | HS-BURST or STALL |
| Idle | On | On | On | STALL/SLEEP/HIBERN8 |
| UFS-Sleep | **May be off** | On | On | Recommended: HIBERN8 |
| UFS-DeepSleep | **May be off** | May be off | May be off | **UNPOWERED** (optional) |
| UFS-PowerDown | **May be removed** | May be removed | May be removed | — |

Power supplies: VCC = 2.4–2.7 V, VCCQ = 1.14–1.26 V, VCCQ2 = 1.70–1.95 V.

VCC must be **restored** before issuing SSU to leave UFS-Sleep (except to UFS-PowerDown).

## Commands Allowed per Power Mode

| Power Mode | Device W-LUN | Other LUs | UPIU Transactions |
|-----------|-------------|-----------|-------------------|
| Active | Any | Any | Any |
| Idle | Any | Any | Any |
| Pre-Active | SSU, REQUEST SENSE | None | CMD, RSP, REJECT, DATA IN, QUERY REQ/RSP |
| UFS-Sleep | SSU, REQUEST SENSE | None | CMD, RSP, REJECT, DATA IN, QUERY REQ/RSP |
| Pre-Sleep / Pre-PowerDown | SSU, REQUEST SENSE, Task Mgmt | None | Any |
| Pre-DeepSleep / UFS-DeepSleep | **None** | **None** | **None** |
| UFS-PowerDown | SSU, REQUEST SENSE | None | CMD, RSP, REJECT, DATA IN, QUERY REQ/RSP |

`bCurrentPowerMode` is the **only attribute required to be returned** in any power mode (except Pre-DeepSleep and UFS-DeepSleep).

## Initialization-Related Attributes

| Attribute | Offset | Description |
|-----------|--------|-------------|
| `bInitPowerMode` | Device Descriptor 0Ah | Power mode after init: 00h = UFS-Sleep, 01h = Active |
| `bInitActiveICCLevel` | Device Descriptor 0Fh | Initial Active ICC level after power-on or reset |
| `bActiveICCLevel` | Attribute | Current max active current level (00h–0Fh); volatile |

**bInitPowerMode = 00h** (UFS-Sleep) is the more common default. After initialization, device transitions Active → Pre-Sleep → UFS-Sleep automatically.

## Active ICC Levels

Up to 16 levels (00h–0Fh); defined in Power Parameters Descriptor:
- `wActivICCLevelsVCC[15:0]` — per level, format: bits[15:14]=unit(nA/uA/mA/A), bits[11:0]=value
- Recommended settings: `06h` (battery/normal), `0Ch` (plugged in/high)
- Can only be changed when all LU queues are empty.

## Key Claims (Spec §7)

- HW Reset, EndPointReset, Host UniPro Warm Reset all return device to Powered-On state and reset all Volatile and Power-on-reset Attributes and Flags.
- LU Reset does **not** reset device parameters; not recommended for boot preparation.
- Three mandatory power supplies: VCC, VCCQ, VCCQ2 (VCC 3.3V dropped in UFS 4.0; VCC 1.8V removed in UFS 3.0).

## Related

[[rpmb]] | [[device-descriptor]] | [[flags]] | [[inhibition-timeout]] | [[thermal-protection-mode]] | [[shipping-mode]]
