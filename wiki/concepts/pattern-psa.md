---
type: concept
title: "Pattern: PSA (Pre-Soldering Authentication) Implementation Guide"
tags: [pattern, script, implementation, psa, pre-soldering, authentication]
sources: [script, spec, modeldefault]
created: 2026-06-21
updated: 2026-06-21
---

# Pattern: PSA (Pre-Soldering Authentication) Implementation Guide

## 概述

PSA（Pre-Soldering Authentication，焊前认证）pattern 测试 UFS 设备在出厂前的完整生命周期：从初始 LUN 配置，经过 PRE_SOLDERING、LOADING_COMPLETE，最终到达 SOLDERED 状态。PSA 机制确保设备在焊接到主板之前已经完成认证数据写入，保护生产流程中的固件完整性。

该 pattern 包含 6 个测试文件（PSA_0001 到 PSA_0006），覆盖完整流程、中断恢复、事件日志、VU 命令验证、Boot EM1 写入以及 HIR 交互场景。

---

## 测试文件一览

| 测试文件 | 目的 |
|---------|------|
| PSW_F_P3_PSA_0001 | 完整 PSA 38 步骤生命周期验证，覆盖所有状态转换、数据写入和验证点 |
| PSW_F_P3_PSA_0002 | SPOR 中断恢复：在 PRE_SOLDERING 状态下的 SPOR 行为，以及 HIR/HID 拒绝验证 |
| PSW_F_P3_PSA_0003 | 事件日志：温度阈值越限和 EC 阈值越限事件在 PSA 模式下的正确记录 |
| PSW_F_P3_PSA_0004 | VU 命令验证：VU 4050（剩余 buffer 大小）、VU 404F（迁移状态）、VU 405C（post-reflow 进度） |
| PSW_F_P3_PSA_0005 | Boot LUN 编程：BootLUN A 和 B 的 EM1 数据写入，CE 计数处理和 BootLUN 分配验证 |
| PSW_F_P3_PSA_0006 | HIR 交互：INHIBITION_TIME=240s 时 HIR 的行为，VB MLC trim 从 PSA_TRIM 转换为 POR_TRIM |

---

## PSA 状态机

```
OFF → PRE_SOLDERING → LOADING_COMPLETE → SOLDERED
```

状态通过写 UFS 属性 `AttributeIDN.PSA_STATE` 推进，相关状态枚举为 `api.PSAState`。

---

## PSA_0001：完整 38 步骤流程

### 核心流程摘要

| 阶段 | 关键动作 |
|------|---------|
| pre_process | 配置 LUN 布局（config_lun） |
| step1–2 | PSA block 创建，检查 `VBINFO_BIT_IS_PSA`、VPC、`PMNTRAINEN` |
| step3 | 写 `PSA_DATA_SIZE` 属性 |
| step4 | UNMAP 准备目标 LBA |
| step5 | 写 `PSA_STATE = PRE_SOLDERING` |
| step6–25 | 通过 sequential_write 写入 PSA 数据 payload（最大 dPSADataSize） |
| step26 | 写 `PSA_STATE = LOADING_COMPLETE` |
| step27 | HW_RESET + power-down（模拟焊接后上电） |
| step28 | 写入第一笔非 PSA 主机数据 |
| step29 | RPMB 写入操作（见下方 RPMB 交互） |
| step30–37 | 验证所有状态转换和数据完整性 |
| step38 | 写 `PSA_STATE = SOLDERED` |
| post_process | `VU_clear_PSA_state()` 重置 PSA 状态 |

### 关键参数计算

**dPSADataSize（PSA 数据大小）**

PSA 数据大小从固件参数读取：
```python
psa_max_data_size = param.gDevice.l37_psa_max_data_size
api.write_attribute(AttributeIDN.PSA_DATA_SIZE, psa_max_data_size)
```

**SLC_VB_size 计算**

```python
fw_geometry = api.get_fw_geometry()
slc_vb_size = fw_geometry.l84_vb_size_u0   # SLC VB 大小
tlc_vb_size = fw_geometry.l88_vb_size_u1   # TLC VB 大小
```

**psa_timeout 计算**

PSA 写入完成后，超时阈值与写入数据量相关，通常以 ERS 读取次数为基准：
```python
# CustomVU_0092 中的参考实现
api.write_attribute(AttributeIDN.PSA_DATA_SIZE, psa_max_data_size)
api.write_attribute(AttributeIDN.PSA_STATE, PSAState.PRE_SOLDERING)
api.sequential_write(lun, 0, psa_max_data_size)  # 写满 PSA buffer
```

### config_precondition → PSA 状态转换流程

```
config_lun()
    ↓
write_attribute(PSA_DATA_SIZE)
    ↓
issue_unmap(target_lbas)
    ↓
write_attribute(PSA_STATE = PRE_SOLDERING)   ← state: OFF → PRE_SOLDERING
    ↓
sequential_write(lun, 0, psa_max_data_size)  ← 写入 PSA payload
    ↓
write_attribute(PSA_STATE = LOADING_COMPLETE) ← state: PRE_SOLDERING → LOADING_COMPLETE
    ↓
init_tester_to_unit_ready(HW_RESET, powerdown=True)  ← 模拟焊接重启
    ↓
write(first_non_psa_data)                    ← step 28
    ↓
rpmb_write(...)                              ← step 29（APL 块创建）
    ↓
write_attribute(PSA_STATE = SOLDERED)        ← state: LOADING_COMPLETE → SOLDERED
```

### PSA 状态写入后的 RPMB 交互（step 29）

在 PSA 完成后进行 RPMB 写入会触发 APL（Application Layer）块创建：
```python
# step29: RPMB write → creates APL block → VBINFO_BIT_IS_APL == 1
project_api.rpmb_key_programming()
rpmb.rpmb_write_data(lba=0, count=4)
# 之后 SPOR → verify VBINFO_BIT_IS_APL == 1
```

---

## PSA_0002：中断恢复流程

PSA 中断恢复通过 SPOR（Sudden Power Off and Recovery）触发：

- **PSA FW 状态读取**：健康报告响应中 `payload[469]` 包含 PSA FW 当前状态
- **HIR 拒绝验证**：在 PRE_SOLDERING 状态中，`bRefreshEn` 的 SetFlag 应返回 `GENERAL_FAILURE (0xFF)`
- **HID 拒绝验证**：在 PSA 流程期间，Host-Initiated Defrag 同样被拒绝

---

## PSA_0004：PSA 专用 VU 命令

| VU 编号 | 函数 | 用途 |
|--------|------|------|
| 4050 | `issue_4050_check_PSA_buffer_size()` | 读取剩余 PSA buffer 大小 |
| 404F | `issue_404F_get_PSA_migration_state()` | 读取当前 PSA 迁移状态 |
| 405C | `issue_405C_get_PSA_post_reflow_progress()` | 读取 post-reflow 迁移进度 |

---

## PSA_0006：HIR 与 Inhibition 交互

```python
# 设置 inhibition 时间为 240 秒
api.write_attribute(idn=AttributeIDN.INHIBITION_TIME, val=240)

# 验证 HIR 在 inhibition 期间被抑制，并触发 XTEMP booking
# 验证 VB MLC trim 状态转换
check_vb_mlc_trim(expected_from=PSA_TRIM, expected_to=POR_TRIM)
```

---

## 共享 VU 命令 API

```python
# PSA 状态查询
project_api.issue_405C_get_PSA_post_reflow_progress()
project_api.issue_404F_get_PSA_migration_state()
project_api.issue_4050_check_PSA_buffer_size()

# PSA 清理（post_process 中调用）
project_api.VU_clear_PSA_state()  # 通过 VendorCmdWrite 清除 PSA 状态

# PSA 属性写入
api.write_attribute(idn=AttributeIDN.PSA_STATE, val=PSAState.PRE_SOLDERING)
api.write_attribute(idn=AttributeIDN.PSA_STATE, val=PSAState.LOADING_COMPLETE)
api.write_attribute(idn=AttributeIDN.PSA_STATE, val=PSAState.OFF)
api.write_attribute(idn=AttributeIDN.PSA_DATA_SIZE, val=psa_max_data_size)
```

---

## 常见异常和处理方式

| 异常 | 触发场景 | 处理方式 |
|------|---------|---------|
| `SIGHTING_FAIL_DATA_COMPARE_FAIL` | PSA 数据写入后读回比对失败 | 检查 PSA_DATA_SIZE 写入是否正确，验证 sequential_write 数据 |
| `SIGHTING_RESPONSE_UNEXPECTED` | PSA 状态转换时设备返回意外响应 | 确认当前 PSA state，检查转换顺序是否正确 |
| `SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH` | VU 返回值与预期不符 | 检查 LUN 配置和 PSA 参数 |
| `SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET` | RPMB 操作前密钥未编程 | 确保 rpmb_key_programming() 在 RPMB 写入前执行 |

---

## 相关链接

- [[psa-state]] — PSA 状态枚举（OFF / PRE_SOLDERING / LOADING_COMPLETE / SOLDERED）
- [[rpmb]] — RPMB 认证和写计数器机制
- [[inhibition-timeout]] — Inhibition Time 与 PSA 的交互
- [[apl-rebuild]] — APL 块在 SPOR 后的重建机制
- [[health-report]] — `payload[469]` PSA FW 状态字段
