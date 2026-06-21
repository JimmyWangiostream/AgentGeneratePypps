---
type: concept
title: "Pattern: Inhibition Time Implementation Guide"
tags: [pattern, script, implementation, inhibition-time, background-operations, bg-task]
sources: [script, spec, modeldefault]
created: 2026-06-21
updated: 2026-06-21
---

# Pattern: Inhibition Time (抑制时间) Implementation Guide

## 概述

Inhibition Time pattern 测试 UFS 固件在"抑制窗口"（inhibition window）内正确阻塞后台（BG）任务的能力，并验证窗口到期后任务能恢复正常执行。抑制机制的目的是在主机密集写入期间（刚完成写入后的短暂窗口）阻止固件执行可能影响性能的后台操作。

测试文件夹包含 11 个测试文件，使用共享的 `mutual_fun.py` 提供触发器、轮询和验证助手函数。

---

## 测试文件一览

| 测试文件 | 目的 |
|---------|------|
| PSW_F_P3_InhibitionTime_0001 | Disable/Enable Timing：抑制定时器启动与到期行为验证 |
| PSW_F_P3_InhibitionTime_0002 | BG Task Inhibition：GC 等后台任务在抑制窗口内被阻塞，`gInhibitMgr.lock == 1` 验证 |
| PSW_F_P3_InhibitionTime_0003 | GC inhibition：GC 在抑制窗口内被阻塞 |
| PSW_F_P3_InhibitionTime_0004 | MS/BF/RD scan inhibition：Media Scan、BFEA、Read Disturb 扫描被阻塞 |
| PSW_F_P3_InhibitionTime_0005 | BBM scan inhibition：Bad Block Management 扫描被阻塞 |
| PSW_F_P3_InhibitionTime_0006 | Read Back Open TLC inhibition：开放 TLC 块的 read-back 被阻塞 |
| PSW_F_P3_InhibitionTime_0007 | HIR Read Back inhibition：HIR（高强度刷新）read-back 被阻塞 |
| PSW_F_P3_InhibitionTime_0008 | Purge Read Back inhibition：purge 期间的 read-back 被阻塞 |
| PSW_F_P3_InhibitionTime_0009 | HID Read Back inhibition：HID（主机发起碎片整理）read-back 被阻塞 |
| PSW_F_P3_InhibitionTime_0010 | PSA Refresh inhibition：PSA 相关刷新在抑制期间被阻塞 |
| PSW_F_P3_InhibitionTime_0011 | Other Refresh inhibition：其他杂项刷新任务被阻塞 |

**注意**：0003–0011 中的许多 step 实体是当前实现中的占位存根（stub），标注为未来完成。

---

## mutual_fun.py 共享函数

### 触发器函数

| 函数 | 作用 |
|------|------|
| `trigger_read_disturb()` | 触发 Read Disturb (RD) 扫描 |
| `trigger_wear_leveling()` | 触发 Wear Leveling (WL) 刷新 |
| `trigger_read_scan_UECC()` | 注入 UECC 错误以启动 read scan |
| `trigger_refresh()` | 触发 HIR（高强度刷新）刷新 |
| `trigger_bfea_refresh_and_check_if_trigger()` | 触发 BFEA 刷新并验证是否成功 |

### 验证函数

| 函数 | 作用 |
|------|------|
| `leave_inhibition_mode()` | 发出 1001 次连续读取以退出抑制窗口 |
| `polling_bkops_idle()` | 轮询 `BG_OP_STATUS` 直到为 0（idle） |
| `polling_bfea_idle()` | 以 2000 秒超时轮询 BFEA idle 状态 |
| `check_if_read_disturb_triggered()` | 验证 Read Disturb 扫描是否正确触发 |
| `check_if_wear_leveling_triggered()` | 验证 WL 扫描是否正确触发 |
| `check_if_Read_Back_triggered()` | 验证 read-back 操作是否正确触发 |
| `check_timeout()` | 超时断言助手 |

### 其他辅助函数

| 函数 | 作用 |
|------|------|
| `write_data()` | 顺序写入助手，准备抑制测试前的数据 |
| `config_lun()` | 配置抑制测试的 LUN 布局 |
| `get_sorted_VB_list()` | 返回排序后的 VB 列表（用于扫描/刷新目标） |
| `power_cycle()` | 随机执行 HW_RESET（含或不含 powerdown），之后调用 `access_vendor_mode()` |
| `get_hwsetting_inhibition_time()` | 从 HwSetting 读取配置的抑制时间 |
| `get_read_back_node()` | 从固件获取 read-back 节点信息 |

---

## 核心实现流程：set_inhibition_time_test()

所有 0003–0011 测试遵循相同的模式：

```python
def set_inhibition_time_test(inhibition_time_val):
    """
    inhibition_time_val: 单位为秒，从测试值列表中选取
    """
    # Step 1: 写入抑制时间属性
    api.write_attribute(idn=AttributeIDN.INHIBITION_TIME, val=inhibition_time_val)

    # Step 2: 准备数据
    write_data()

    # Step 3: 触发目标 BG 任务（因测试而异）
    trigger_xxx()   # 如 trigger_read_disturb()

    # Step 4: 验证任务被抑制
    lock_val = api.read_fw_value('gInhibitMgr.lock')
    assert lock_val == 1, "Inhibition lock should be active"

    # Step 5: 退出抑制窗口
    leave_inhibition_mode()  # 发出 1001 次连续读取

    # Step 6: 验证 BG 任务恢复
    check_if_xxx_triggered()  # 如 check_if_read_disturb_triggered()
    polling_bkops_idle()
```

---

## gInhibitMgr.lock 读取和验证

抑制状态通过直接读取固件变量验证：

```python
# 读取抑制锁状态
lock_value = api.read_fw_value('gInhibitMgr.lock')
# lock_value == 1: 抑制激活（BG 任务被阻塞）
# lock_value == 0: 抑制未激活（BG 任务可以执行）
```

**注意**：`read_fw_value()` 通过符号名称直接读取固件内存中的变量值，不需要任何 VU 命令。

---

## Inhibition Time 测试值列表

标准测试使用以下抑制时间值（单位：秒）：

```python
INHIBITION_TIME_TEST_VALUES = [180, 150, 90, 60, 30, 210, 240, 255]
```

PSA_0006 中使用的特殊值：
```python
api.write_attribute(idn=AttributeIDN.INHIBITION_TIME, val=240)
```

HwSetting 中读取的配置值通过 `get_hwsetting_inhibition_time()` 获取，用于对照验证。

---

## leave_inhibition_mode() 实现原理

退出抑制模式需要发出足够多的读取操作，使固件计数器超过阈值：

```python
def leave_inhibition_mode():
    """发出 1001 次连续读取以退出抑制窗口"""
    for i in range(1001):
        api.read(lun=test_lun, lba=0, count=1)
    # 之后 gInhibitMgr.lock 应变为 0
```

---

## Inhibition Time 与其他模块的关系

| 关联模块 | 被抑制的操作 |
|---------|------------|
| GC（Garbage Collection） | FG/BG GC 在抑制期间排队等待 |
| Media Scan | MS 扫描推迟到抑制结束 |
| BFEA（Block Fail Early Abort）| BFEA 刷新推迟 |
| Read Disturb | RD 扫描推迟 |
| BBM（Bad Block Management）| BBM 扫描推迟 |
| HIR（Host-Initiated Refresh）| read-back 操作推迟 |
| HID（Host-Initiated Defrag）| read-back 操作推迟 |
| PSA Refresh | PSA 相关刷新推迟 |

---

## 常见异常和处理方式

| 异常 | 触发场景 | 处理方式 |
|------|---------|---------|
| `SIGHTING_FAIL_DATA_COMPARE_FAIL` | 抑制期间任务意外执行，数据不一致 | 检查抑制时间属性写入，确认 lock == 1 |
| `PATTERN_ASSERT_STUCK_WHILE_TIMEOUT` | BG 任务在抑制结束后未能恢复 | 检查 leave_inhibition_mode() 调用，确认 1001 次读取完成 |

---

## 相关链接

- [[inhibition-timeout]] — Inhibition Time UFS 属性（`AttributeIDN.INHIBITION_TIME`）
- [[background-operations]] — BG 任务管理（GC、Media Scan、BFEA 等）
- [[psa-state]] — PSA 状态与抑制的交互（PSA_0006）
- [[health-report]] — BG 任务完成计数器验证
