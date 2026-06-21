---
type: concept
title: "Pattern: Wear Leveling Implementation Guide"
tags: [pattern, script, implementation, wear-leveling, erase-count, vb-version, gc]
sources: [script, spec, modeldefault]
created: 2026-06-21
updated: 2026-06-21
---

# Pattern: Wear Leveling (磨损均衡) Implementation Guide

## 概述

Wear Leveling（WL，磨损均衡）pattern 测试 UFS 固件在所有 VB（Virtual Block）之间均匀分布写入操作的能力。固件通过跟踪擦除次数（EC）和版本值（VER），当 EC 差距或版本差距超过阈值时触发静态（Static WL）或动态（Dynamic WL）磨损均衡，将数据从高 EC 块迁移到低 EC 块。

该 pattern 包含 4 个测试文件和共享的 `mutual_fun.py`。

---

## 测试文件一览

| 测试文件 | 目的 |
|---------|------|
| PSW_F_P3_WearLeveling_0001 | WL 信息测试：VBListNum/OpenVBType、EC/版本设置与读回、健康报告交叉验证 |
| PSW_F_P3_WearLeveling_0002 | 静态 WL 刷新测试：ICS/Static/Dynamic 池触发、cold/prior-round、TH1/TH2 阈值、booking queue 验证 |
| PSW_F_P3_WearLeveling_0003 | 静态 WL GC 测试：USED_BLK_POOL_EM1/TLC/TLC_WB GC 触发，`totalSWLGCTriggerCount` 递增 |
| PSW_F_P3_WearLeveling_0004 | 动态 WL 测试：在搜索范围内按最低 EC 选择 VB |

---

## mutual_fun.py 共享函数

### VB Entry 解析（get_VB_group）

每个 VB 条目为 4 字节，`get_VB_group()` 解析位域：

```python
def get_VB_group(vb_entry: int) -> dict:
    return {
        'group':       (vb_entry >>  0) & 0x3F,   # bits 0–5
        'access_mode': (vb_entry >>  6) & 0x03,   # bits 6–7
        'dirty':       (vb_entry >>  8) & 0x01,   # bit 8
        'partition':   (vb_entry >>  9) & 0x03,   # bits 9–10
        'src_uecc':    (vb_entry >> 15) & 0x01,   # bit 15
        'vb_trim':     (vb_entry >> 16) & 0x03,   # bits 16–17
        'risky_type':  (vb_entry >> 18) & 0x03,   # bits 18–19 (0=Safe/1=Hot/2=Cold)
    }
```

### 其他共享函数

| 函数 | 作用 |
|------|------|
| `check_WL_value_change()` | 验证 WL 触发计数器已变更 |
| `get_sorted_VB_list()` | 返回排序后的 VB 列表 |

---

## 核心 API：WearLevelingInformation（VU 4098）

```python
# 获取磨损均衡信息
wl_info = project_api.issue_4098_to_get_wear_leveling_information()
```

`WearLevelingInformation` 结构包含：

| 字段 | 含义 |
|------|------|
| `EC_data` | 各 VB 的擦除次数数据 |
| `VER_data` | 各 VB 的版本数据 |
| `global_version` | 全局版本号 |
| `boundary_version` | 边界版本号 |
| `EC_gaps` | EC 差距数组 |
| `totalSWLTriggerCount` | 静态 WL 触发总次数（刷新类型） |
| `totalSWLGCTriggerCount` | 静态 WL GC 触发总次数 |

---

## 核心 API：静态 WL EC 差距阈值设置（VU C072）

```python
# 设置静态 WL EC 差距阈值（11 个参数）
project_api.issue_C072_to_set_static_wear_leveling_EC_gap_threshold(
    param0,   # TH1 阈值
    param1,   # TH2 阈值
    param2,   # ICS 池参数
    param3,   # Static 池参数
    param4,   # Dynamic 池参数
    param5,   # cold 轮次参数
    param6,   # prior-round 参数
    param7,   # ...
    param8,
    param9,
    param10,
)
```

---

## 核心 API：FTL 版本设置

```python
# 设置 VB 的 FTL 版本（用于测试版本差距触发 WL）
api.set_ftl_version(mlc_partition_current_vb_version)
```

---

## PSW_F_P3_WearLeveling_0001：WL 信息测试

### 测试流程

```python
# Step 1: 读取 VB 列表信息
vb_list_info = project_api.custom_vu.issue_406D_get_VB_list_info()
# 验证 VBListNum（各池中的 VB 数量）
# 验证 OpenVBType（开放 VB 类型）

# Step 2: 设置 EC 并读回
target_ec = 100
api.set_ftl_version(target_version)
api.set_all_VB_erase_count(target_ec)

# Step 3: 读取 WL 信息验证
wl_info = project_api.issue_4098_to_get_wear_leveling_information()
assert wl_info.EC_data == target_ec

# Step 4: 健康报告交叉验证
health = project_api.issue_40FE_to_read_enhanced_health_report()
# 验证 bDeviceLifeTimeEstA/B 与 EC 一致
```

---

## PSW_F_P3_WearLeveling_0002：静态 WL 刷新测试

### 触发场景

| 场景 | 说明 |
|------|------|
| ICS 池触发 | ICS（Invalid Cell Status）块 EC 差距超过阈值 |
| Static 池触发 | 静态数据块 EC 差距超过 TH1 |
| Dynamic 池触发 | 动态数据块 EC 差距超过 TH2 |
| cold 场景 | 冷数据（long-time un-accessed）WL 触发 |
| prior-round 场景 | 上一轮 WL 后的后续处理 |

### 验证方式

```python
# 1. 记录触发前的计数
wl_before = project_api.issue_4098_to_get_wear_leveling_information()
trigger_count_before = wl_before.totalSWLTriggerCount

# 2. 制造 EC 差距（设置部分 VB 为高 EC，部分为低 EC）
project_api.set_all_VB_erase_count(high_ec)
# 对目标 VB 设置低 EC...

# 3. 触发 WL（通过写入数据促使固件执行 GC/WL）
api.random_write(size=write_size)
api.random_erase()
polling_bkops_idle()

# 4. 验证 booking queue
booking_queue = project_api.issue_40C5_to_get_booking_queue()
check_booking_queue(booking_queue, expected_vb_list)

# 5. 验证触发计数递增
wl_after = project_api.issue_4098_to_get_wear_leveling_information()
assert wl_after.totalSWLTriggerCount > trigger_count_before
```

---

## PSW_F_P3_WearLeveling_0003：静态 WL GC 测试

针对不同 VB 池类型的 GC 触发验证：

```python
# 针对三种 VB 池类型验证 WL GC
for pool_type in ['USED_BLK_POOL_EM1', 'TLC', 'TLC_WB']:
    # 触发对应池类型的 GC
    gc_count_before = wl_info.totalSWLGCTriggerCount
    # ...执行写入触发 GC...
    gc_count_after = project_api.issue_4098_to_get_wear_leveling_information().totalSWLGCTriggerCount
    assert gc_count_after > gc_count_before

# VB 列表信息（按池类型分类）
vb_list = project_api.custom_vu.issue_406D_get_VB_list_info()
```

---

## PSW_F_P3_WearLeveling_0004：动态 WL 测试

动态 WL 在搜索范围内选择 EC 最低的 VB 作为写入目标：

```python
# 验证 VB 选择策略：按最低 EC 选择
vb_list = project_api.custom_vu.issue_406D_get_VB_list_info()
# 验证选中的目标 VB 确实是 EC 最低的 VB
min_ec_vb = min(vb_list, key=lambda v: v.erase_count)
assert selected_vb == min_ec_vb.vb_num
```

---

## VB 池类型和 EC 差距关系

| 池类型 | 触发条件 |
|-------|---------|
| `USED_BLK_POOL_EM1` | EM1（SLC）用户数据块 EC 差距超过阈值 |
| `TLC` | TLC 用户数据块 EC 差距超过 TH2 |
| `TLC_WB` | Write Booster 块 EC 差距超过阈值 |

---

## 常见异常和处理方式

| 异常 | 触发场景 | 处理方式 |
|------|---------|---------|
| `SIGHTING_FAIL_DATA_COMPARE_FAIL` | WL 后 EC/版本值读回不符 | 检查 EC 设置是否持久化（RAM vs flash），确认 PURGE 周期完成 |

---

## 相关链接

- [[erase-count]] — 擦除次数（EC）跟踪和设置
- [[vb-group]] — VB Group 分类和池类型
- [[gc]] — Garbage Collection 与 WL 的交互
- [[health-report]] — 寿命估计（bDeviceLifeTimeEstA/B）与磨损均衡
- [[block-budget]] — VB 池分配和预算管理
