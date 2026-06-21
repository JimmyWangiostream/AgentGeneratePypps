---
type: concept
title: "Pattern: Thermal Protection Implementation Guide"
tags: [pattern, script, implementation, thermal-protection, temperature, stuck-state]
sources: [script, spec, modeldefault]
created: 2026-06-21
updated: 2026-06-21
---

# Pattern: Thermal Protection (热保护) Implementation Guide

## 概述

Thermal Protection pattern 测试 UFS 固件在温度超出安全范围（过热或过冷）时，能否正确进入"stuck/throttled"卡住状态，以及能否通过 VU D0F3 命令解除该状态。测试还覆盖 ATS 定时器行为、ASIC-NAND 温度差以及 auto-standby 的交互。

该 pattern 包含 7 个测试文件：0001–0006 和 0010（注意：0007–0009 文件不存在，编号不连续）。

---

## 测试文件一览

| 测试文件 | 目的 |
|---------|------|
| PSW_F_P3_ThermalProtection_0001 | HOT_ONLY Stuck：设置热阈值，注入超阈值温度，验证 stuck 状态，D0F3 解除 |
| PSW_F_P3_ThermalProtection_0002 | COLD_ONLY Stuck：同 0001 但为低温（低于阈值）场景 |
| PSW_F_P3_ThermalProtection_0003 | HOT_COLD Stuck：同时测试热阈值和冷阈值 |
| PSW_F_P3_ThermalProtection_0004 | Shipping Mode 切换：Shipping Mode 配置变更时的热保护行为 |
| PSW_F_P3_ThermalProtection_0005 | Shipping Mode 切换（场景二） |
| PSW_F_P3_ThermalProtection_0006 | Shipping Mode 切换（场景三） |
| PSW_F_P3_ThermalProtection_0010 | Temperature Measurement Check：ATS 定时器、delta_asic_nand 温度差、auto-standby 交互 |

**注意**：0007–0009 编号缺失，文件不存在于此 pattern 文件夹中。

---

## 温度编码规则

UFS 固件使用偏移编码表示温度：

```
UFS 报告温度 = 实际温度 + 80
```

| 实际温度 | UFS 报告值 |
|---------|----------|
| 0°C | 80 |
| 100°C | 180 |
| -20°C | 60 |
| 125°C | 205 |

---

## 共享 VU 命令

### VU D0F1 — 写入热保护阈值

```python
# 设置热保护阈值
project_api.issue_D0F1_write_thermal_stuck_threshold(WriteThermalStuckThreshold)
```

`WriteThermalStuckThreshold` 结构包含：
- `low_threshold`：冷阈值（低于此温度触发 COLD stuck）
- `high_threshold`：热阈值（高于此温度触发 HOT stuck）

### VU 40FA — 读取热保护阈值

```python
# 读取当前热保护阈值配置
thresholds = project_api.issue_40FA_read_thermal_stuck_threshold()
```

### VU D0F3 — 禁用热保护（解除 stuck 状态）

```python
# 禁用热保护，解除 stuck 状态
project_api.issue_D0F3_disable_thermal_stuck(
    ThermalProtectionType,       # HOT_ONLY / COLD_ONLY / HOT_COLD
    HardThermalProtectionType    # 硬保护类型
)
```

### VU D08A — 注入假温度

```python
# 注入虚假 NAND 温度（用于测试）
project_api.issue_D08A_set_vu_temperature(SetNandTemperature)
```

---

## Stuck State 触发和恢复流程

### HOT_ONLY Stuck 流程（PSW_F_P3_ThermalProtection_0001）

```
1. 读取当前阈值配置（VU 40FA）
2. 写入热阈值（VU D0F1）
   WriteThermalStuckThreshold(high_threshold=目标热阈值)
3. 注入超阈值温度（VU D08A）
   D08A: NAND_TEMPERATURE_DIE = hot_threshold + delta
4. 触发 I/O 操作（写/读）
5. 验证设备进入 stuck 状态
   → 期望 I/O 响应超时或返回特定错误码
6. 调用 D0F3 解除 stuck 状态
   D0F3: ThermalProtectionType = HOT_ONLY
7. 验证设备恢复正常 I/O
8. manual_rst_n()  ← 共享重置函数
```

### COLD_ONLY Stuck 流程（PSW_F_P3_ThermalProtection_0002）

与 HOT_ONLY 相同，但注入温度低于 `low_threshold`：
```python
# 注入低温
D08A: NAND_TEMPERATURE_DIE = cold_threshold - delta
# 解除时
D0F3: ThermalProtectionType = COLD_ONLY
```

### HOT_COLD 双阈值流程（PSW_F_P3_ThermalProtection_0003）

先触发热 stuck，用 D0F3 恢复；再触发冷 stuck，再次用 D0F3 恢复：
```python
D0F3: ThermalProtectionType = HOT_COLD  # 同时处理两种类型
```

---

## 枚举类型

```python
class ThermalProtectionType:
    HOT_ONLY  = ...   # 仅热保护
    COLD_ONLY = ...   # 仅冷保护
    HOT_COLD  = ...   # 同时启用热和冷保护

class HardThermalProtectionType:
    # 硬保护类型枚举（与 D0F3 配合使用）
    ...
```

---

## PSW_F_P3_ThermalProtection_0004–0006：与 Shipping Mode 的交互

这三个测试验证在 Shipping Mode 配置切换时，热保护行为是否正确：

- Shipping Mode 通过设备配置描述符控制
- 切换 Shipping Mode 不应意外触发或解除热保护状态
- 测试使用 `api.push_write_config()` 变更配置，并验证热保护状态的一致性

---

## PSW_F_P3_ThermalProtection_0010：温度测量验证

此测试覆盖更复杂的温度测量场景：

### ATS 定时器交互

```python
# 禁用/启用 Auto Standby
project_api.issue_D088_enable_disable_auto_standby(enable_flag)

# 注入温度验证 ATS 定时器停止
project_api.issue_D08A_set_vu_temperature(SetNandTemperature)
```

### FW 符号读取

```python
# 直接读取固件温度相关变量
temp_val = api.read_fw_value('gUfsApiStruct.ftl->temp.*')
```

### delta_asic_nand 温度差验证

测试验证 ASIC 温度传感器与 NAND 温度之间的差值（delta）是否在合理范围内。

---

## 常见异常和处理方式

| 异常 | 触发场景 | 处理方式 |
|------|---------|---------|
| `SIGHTING_FAIL_DATA_COMPARE_FAIL` | 温度阈值或 stuck 状态不符合预期 | 检查阈值写入（D0F1）是否正确，确认温度注入值 |
| `G_TIMEOUT_ALL` | 设备进入 stuck 后 I/O 超时（预期行为） | 此为正常行为，调用 D0F3 解除后继续测试 |

---

## 相关链接

- [[thermal-stuck-state]] — Thermal Stuck State 固件行为
- [[shipping-mode]] — Shipping Mode 与热保护的交互
- [[background-operations]] — Auto-Standby（ATS）机制
- [[nand-temperature]] — NAND 温度读取（VU 4021）和注入（VU D08A）
