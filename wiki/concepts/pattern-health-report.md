---
type: concept
title: "Pattern: Health Report Implementation Guide"
tags: [pattern, script, implementation, health-report, device-health, eol]
sources: [script, spec, modeldefault]
created: 2026-06-21
updated: 2026-06-21
---

# Pattern: Health Report (设备健康报告) Implementation Guide

## 概述

Health Report pattern 测试 UFS 设备通过标准和扩展健康报告命令正确汇报设备健康状态的能力。健康报告包含 EOL 信息、寿命估计、刷新计数、温度历史、读取错误统计等关键字段。

该 pattern 包含 2 个核心测试文件，以及大量其他 pattern（PSA、Wear Leveling、RAIN 等）在 post-condition 验证中使用健康报告进行交叉验证。

---

## 测试文件一览

| 测试文件 | 目的 |
|---------|------|
| PSW_F_P3_HealthReport_0001 | 基础健康报告：最小化验证健康报告检索 |
| PSW_F_P3_HealthReport_0002 | 增强健康报告：30+ 字段的全面验证，覆盖电源管理和温度边界场景 |

---

## 健康报告 API

### 基础健康报告（VU）

```python
# 读取 Micron 专有健康报告
health_report = project_api.get_micron_health_report()
```

### 增强健康报告（VU 40FE）

```python
# 读取增强健康报告（30+ 字段）
enhanced_hr = project_api.issue_40FE_to_read_enhanced_health_report()
```

### VDET 信息（VU 40B8）

```python
# 读取 VDET（Voltage Detection）信息
vdet_info = project_api.issue_40B8_to_get_vdet_information()
```

---

## 关键字段说明

### bPreEOLInfo — 预期寿命终止信息

`bPreEOLInfo` 表示设备距离 EOL（End of Life）的预期状态：

| 值 | 含义 |
|----|------|
| `0x00` | 未定义（Normal） |
| `0x01` | 正常（设备寿命 < 80%） |
| `0x02` | 警告（设备寿命 80%–90%） |
| `0x03` | 紧急（设备寿命 > 90%，接近 EOL） |

此字段来自 UFS 设备健康描述符（Device Health Descriptor）的标准字段，通过 `ReadDescriptor(DescriptorIDN.DEVICE_HEALTH)` 读取。

### bDeviceLifeTimeEstA / bDeviceLifeTimeEstB — 设备寿命估计

| 字段 | 含义 |
|------|------|
| `bDeviceLifeTimeEstA` | 基于主机写入数据量的寿命估计（Type A，已用寿命百分比，10% 为一档） |
| `bDeviceLifeTimeEstB` | 基于最大擦除次数的寿命估计（Type B，已用寿命百分比，10% 为一档） |

两个字段的取值范围均为 `0x01`（0–10%）到 `0x0A`（90–100%），`0x00` = 未定义，`0x0B` = 超出（EOL 后）。

```python
# 从设备健康描述符读取
descriptor = ExecuteCMD.ReadDescriptor().assign(DescriptorIDN.DEVICE_HEALTH, 0, 0)
health_desc = DeviceHealthDescriptor310.from_bytes(descriptor.data)
eol_info = health_desc.bPreEOLInfo
life_est_a = health_desc.bDeviceLifeTimeEstA
life_est_b = health_desc.bDeviceLifeTimeEstB
```

### dRefreshTotalCount — 刷新总次数

在增强健康报告中，刷新相关计数器：

| 字段 | 含义 |
|------|------|
| `read_reclaim_count_for_slc_table` | SLC 系统表刷新（read reclaim）次数 |
| `read_reclaim_count_for_tlc` | TLC 用户数据刷新次数 |
| `read_reclaim_count_for_em1` | EM1（SLC LUN）用户数据刷新次数 |

这些字段在 Refresh_0001 测试中通过 C088 StartRefresh 后验证计数递增。

### dRefreshProgress — 刷新进度

UFS 标准属性 `AttributeIDN.REFRESH_STATUS` 报告当前刷新进度：

| 状态值 | 含义 |
|-------|------|
| `0x00` | Idle（无刷新进行中） |
| `0x01` | Refreshing in progress |
| `0x05` | Refresh required（XTEMP booking 触发） |

HIR 测试（PSW_F_P3_HIR_0003）中使用 `REFRESH_METHOD=2`（selective），进度计算：
```python
progress_increment = (1 / total_vb_cnt) * 100000  # 每个 slice 增加的进度值
```

---

## 增强健康报告字段（40FE）

PSW_F_P3_HealthReport_0002 验证的 30+ 字段：

### 温度字段

| 字段 | 含义 |
|------|------|
| `highest_temp` | 设备生命周期内记录的最高温度 |
| `lowest_temp` | 设备生命周期内记录的最低温度 |
| `power_on_highest_temp` | 本次上电后的最高温度 |
| `power_on_lowest_temp` | 本次上电后的最低温度 |

**温度偏移**：固件内部温度 = 实际温度 + 80（同 Thermal Protection pattern）

### 温度分布区间计数（temperature_profile）

| 字段 | 温度范围 |
|------|---------|
| `temperature_profile_t_37` | ≤ -37°C |
| `temperature_profile_37_t_25` | -37°C 到 -25°C |
| `temperature_profile_25_t_0` | -25°C 到 0°C |
| `temperature_profile_0_t_95` | 0°C 到 95°C |
| `temperature_profile_95_t_115` | 95°C 到 115°C |
| `temperature_profile_t_115` | > 115°C |

### 温度变化量计数（temperature_delta）

| 字段 | 变化量范围 |
|------|----------|
| `temperature_delta_t_1` | 相邻采样差 < 1°C |
| `temperature_delta_1_t_5` | 1°C–5°C |
| `temperature_delta_5_t_10` | 5°C–10°C |
| `temperature_delta_10_t_15` | 10°C–15°C |
| `temperature_delta_t_15` | ≥ 15°C |

### PSA 状态字段

在 PSA_0002 中，健康报告响应的 `payload[469]` 包含当前 PSA FW 状态。

### 其他关键字段

| 字段 | 含义 |
|------|------|
| `lun_reconfig_ec_warning` | 偏移 `0x140h`：LUN 重新配置的 EC 警告（EC > 30 时置位） |
| `prl` | Product Revision Level（当前 PRL） |
| `fw_current_prl` | FW 当前 PRL |

---

## 电源管理测试（PSW_F_P3_HealthReport_0002）

在增强健康报告测试中，设备经历不同电源状态并验证健康报告字段不受影响：

| 电源状态 | SSU 命令值 |
|---------|----------|
| Sleep | `0x02` |
| Powerdown | `0x03` |
| Deep Sleep | `0x04` |

```python
# 进入 Sleep 状态
ExecuteCMD.StartStopUnit().assign(power_condition=0x02)
# 读取健康报告，验证字段一致性
enhanced_hr = project_api.issue_40FE_to_read_enhanced_health_report()
```

---

## 健康报告在其他 Pattern 中的使用

| Pattern | 使用场景 |
|---------|---------|
| RAIN_0002 | 验证 RAIN 恢复后的失败计数器递增 |
| Refresh_0001 | 验证刷新后 `read_reclaim_count` 递增 |
| Reconfiguration_0001 | 验证 `lun_reconfig_ec_warning` 字段 |
| PSA_0002 | 读取 `payload[469]` 获取 PSA FW 状态 |
| CustomVU_0092 | 验证 ERS（Error Recovery Statistics）Index 65 在 PSA 后持久化 |

---

## 常见异常和处理方式

| 异常 | 触发场景 | 处理方式 |
|------|---------|---------|
| `SIGHTING_FAIL_DATA_COMPARE_FAIL` | 健康报告字段值与预期不符 | 检查设备状态、电源状态，确认测试前后 EC 变化 |

---

## 相关链接

- [[device-health-descriptor]] — UFS 设备健康描述符（Device Health Descriptor）
- [[eol-info]] — EOL 预测机制（bPreEOLInfo）
- [[psa-state]] — PSA FW 状态在健康报告中的体现
- [[refresh]] — 刷新计数器和进度（dRefreshTotalCount / dRefreshProgress）
- [[wear-leveling]] — 磨损均衡与寿命估计
