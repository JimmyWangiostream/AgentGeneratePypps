---
type: concept
title: "Pattern: APL System Rebuild Implementation Guide"
tags: [pattern, script, implementation, apl, rebuild, uecc, hecc, spor, system-table]
sources: [script, spec, modeldefault]
created: 2026-06-21
updated: 2026-06-21
---

# Pattern: APL System Rebuild (APL 系统重建) Implementation Guide

## 概述

APL System Rebuild（Application Layer 系统重建）pattern 测试 UFS 固件在系统表块（BBT、Page Table、Index、List、Log、ISP、PTE）或用户数据块发生 UECC（不可纠正错误）或 HECC（硬 ECC 错误）后，经过 SPOR（Sudden Power Off and Recovery），固件能否正确重建这些结构并恢复数据完整性。

该 pattern 包含 21 个测试文件和共享的 `mutual_fun.py`。

---

## 测试文件一览

| 测试范围 | 目的 |
|---------|------|
| PSW_F_P3_APL_Rebuild_0001 | BBT（Bad Block Table）UECC 注入后 SPOR 重建 |
| PSW_F_P3_APL_Rebuild_0002 | Page Table UECC 注入后 SPOR 重建 |
| PSW_F_P3_APL_Rebuild_0003 | Index 块 UECC 注入后 SPOR 重建 |
| PSW_F_P3_APL_Rebuild_0004 | List 块 UECC 注入后 SPOR 重建 |
| PSW_F_P3_APL_Rebuild_0005 | Log 块 UECC 注入后 SPOR 重建 |
| PSW_F_P3_APL_Rebuild_0006 | ISP 块 UECC 注入后 SPOR 重建 |
| PSW_F_P3_APL_Rebuild_0007 | PTE（Page Table Entry）UECC 注入后 SPOR 重建 |
| PSW_F_P3_APL_Rebuild_0008 | GC UECC 场景：GC 源 VB 发生 UECC |
| PSW_F_P3_APL_Rebuild_0009–0017 | 各种 EM1/TLC UECC/HECC 重建场景 |
| PSW_F_P3_APL_Rebuild_0018 | PSA 模式下的重建（PRE_SOLDERING 状态） |
| PSW_F_P3_APL_Rebuild_0019 | PSA 模式下的重建（LOADING_COMPLETE 状态） |
| PSW_F_P3_APL_Rebuild_0020 | GC UECC 场景二 |
| PSW_F_P3_APL_Rebuild_0021 | 综合重建场景 |

---

## TestMode 枚举

```python
class TestMode:
    TEST_TLC = 0   # TLC 用户数据测试
    SLC      = 1   # SLC（EM1）用户数据测试
    WB       = 2   # Write Booster 测试
    PTE      = 3   # Page Table Entry 测试
    L1       = 4   # Level-1 Cache 测试
    LOG      = 5   # Log Block 测试
    TMP_RAIN = 6   # Temporary RAIN 测试
```

---

## WL_Group 枚举（TLC 页边界）

```python
class WL_Group:
    GroupA    = range(0, 1620)      # pages 0–1619
    GroupB_MLC = range(1620, 1652)  # pages 1620–1651（MLC 页）
    GroupC_TLC = range(1652, 3308)  # pages 1652–3307（TLC 页）
    GroupD_SLC = range(3308, 3312)  # pages 3308–3311（SLC 页）
```

---

## mutual_fun.py 共享函数

### UECC 注入

```python
def inject_UECC(pca):
    """
    通过写入 0xAA 数据到原始 NAND 位置来损坏页面
    SLC:  写 16KB（覆盖原始数据，造成 ECC 错误）
    TLC:  写 60KB
    """
    # 使用 VU C060 写入全 0xAA 数据
    project_api.issue_C060_to_write_raw_data(
        Ce=pca.ce, Block=pca.block, Plane=pca.plane,
        Page=pca.page, SLC_Enable=is_slc,
        Ecc_Enable=1, datapayload=bytes([0xAA]*payload_size)
    )
```

```python
def injectUECC_from_FEP(vb, fep, startoffset, num):
    """
    从第一个空页（FEP）开始注入 UECC
    """
    for page_offset in range(num):
        inject_UECC(pca=compute_pca(vb, fep + startoffset + page_offset))
```

### HECC 注入（位翻转）

```python
def flipbit_on_SLC_lba_smart(lba):
    """
    SLC HECC 注入：翻转 100 位
    """
    # 读取原始数据（ECC=0）
    raw_data = issue_4060_to_read_raw_data(..., Ecc_Enable=0)
    # 翻转 100 位
    corrupted = flip_bits(raw_data, count=100)
    # 写回（ECC=0）
    issue_C060_to_write_raw_data(..., datapayload=corrupted)

def flipbit_on_TLC_smart(micron_pca):
    """
    TLC HECC 注入：翻转 150 位
    """
    raw_data = issue_4060_to_read_raw_data(..., Ecc_Enable=0)
    corrupted = flip_bits(raw_data, count=150)
    issue_C060_to_write_raw_data(..., datapayload=corrupted)
```

### LWP（Last Written Page）验证

```python
def collect_lwp_checks():
    """收集重建前的 LWP 状态"""
    return issue_409D_to_do_power_loss_analysing(opcode=0)  # LWP check

def compare_lwp_checks(before, after):
    """比较重建前后的 LWP，验证固件正确恢复"""
    # LWP 应在 SPOR 后保持或正确更新
    pass

def write_data_until_dedicate_lwp():
    """写入数据直到特定 LWP 位置"""
    pass
```

### SPOR + MP 初始化

```python
def SPOR_init_mp():
    """
    执行 SPOR 并进行 Manufacturing Protocol 初始化
    """
    api.init_tester_to_unit_ready(
        resetmode=Dcmd5ResetType.HW_RESET,
        powerdown=True
    )
    api.access_vendor_mode()  # 重新进入 MP
```

---

## 核心 VU 命令

| VU 编号 | 函数 | 用途 |
|--------|------|------|
| 40C1 | `issue_40C1_to_get_open_vb_information()` | 获取开放 VB 信息（查找目标块） |
| 4051 | `issue_4051_to_get_physical_address(luID, lba)` | LBA → 物理地址转换 |
| 4060 | `issue_4060_to_read_raw_data(Die, Plane, Block, Page, SLC_Enable, Ecc_Enable, Scrambler_Enable, REH_Enable)` | 原始 NAND 读取 |
| C060 | `issue_C060_to_write_raw_data(Ce, Block, Plane, Page, SLC_Enable, Ecc_Enable, datapayload)` | 原始 NAND 写入（注入错误） |
| D060 | `issue_D060_to_erase_specific_block(Ce, Plane, Block, SlcEnable, psaEnable)` | 擦除指定块 |
| 409D | `issue_409D_to_do_power_loss_analysing(opcode, ...)` | LWP 检查（opcode=0）/ APL 参数操作 |
| 40FE | `issue_40FE_to_read_enhanced_health_report()` | 重建后健康报告验证 |

---

## 系统表块重建测试流程（0001–0007）

```
1. apl_pattern_precondition()
   ↓
2. 获取目标系统表块的物理地址
   issue_4051_to_get_physical_address(luID, lba)
   ↓
3. 注入 UECC（写 0xAA 损坏页面）
   inject_UECC(pca)
   ↓
4. SPOR（模拟突然断电重启）
   SPOR_init_mp()
   ↓
5. 验证固件重建系统表
   - collect_lwp_checks() 验证 LWP 正确恢复
   - compare_lwp_checks(before, after)
   ↓
6. 验证数据完整性
   api.read_compare()  ← 确认用户数据未损坏
```

---

## EM1/TLC UECC 重建测试流程（0008–0021）

```
1. apl_pattern_precondition()
   ↓
2. 写入数据（准备待损坏的 VB）
   api.sequential_write() 或 api.random_write()
   ↓
3. 获取写入数据的物理位置
   issue_40C1_to_get_open_vb_information()
   ↓
4. 注入 UECC 或 HECC
   inject_UECC(pca)           ← UECC
   flipbit_on_SLC_lba_smart() ← SLC HECC (100 bits)
   flipbit_on_TLC_smart()     ← TLC HECC (150 bits)
   ↓
5. SPOR
   SPOR_init_mp()
   ↓
6. 执行 LWP 分析
   issue_409D_to_do_power_loss_analysing(opcode=4)  ← power-loss check
   ↓
7. 验证数据完整性
   api.read_compare()
```

---

## build_write_payload()：构建 TLC 页写入 payload

```python
def build_write_payload(lp, up, xp):
    """
    构建 60KB TLC 页 payload
    lp: Lower Page 数据
    up: Upper Page 数据
    xp: Extra Page 数据
    返回: 60KB 完整 TLC 页 payload
    """
    return lp + up + xp  # 各 20KB，合计 60KB
```

---

## PSA 模式下的重建（0018–0019）

测试 PSA 状态（PRE_SOLDERING / LOADING_COMPLETE）下 UECC 发生后的重建：

```python
# 0018: PRE_SOLDERING 状态
api.write_attribute(AttributeIDN.PSA_STATE, PSAState.PRE_SOLDERING)
inject_UECC(pca)
SPOR_init_mp()
# 验证固件在 PSA 状态下正确处理重建

# 0019: LOADING_COMPLETE 状态
api.write_attribute(AttributeIDN.PSA_STATE, PSAState.LOADING_COMPLETE)
inject_UECC(pca)
SPOR_init_mp()
```

---

## 常见异常和处理方式

| 异常 | 触发场景 | 处理方式 |
|------|---------|---------|
| `SIGHTING_FAIL_DATA_COMPARE_FAIL` | SPOR 后读回数据与写入不符 | 检查 UECC 注入的物理位置，确认 LWP 正确 |
| `SIGHTING_RESPONSE_UNEXPECTED` | SPOR 后固件未能正确重建系统表 | 检查注入位置是否正确（系统表 vs 用户数据） |

---

## 相关链接

- [[uecc]] — UECC（不可纠正 ECC 错误）注入和检测
- [[hecc]] — HECC（硬 ECC 错误）位翻转注入
- [[spor]] — SPOR（突然断电恢复）流程
- [[lwp]] — Last Written Page（最后写入页）分析（VU 409D）
- [[psa-state]] — PSA 状态下的系统重建行为
- [[rain]] — RAIN（冗余 NAND 阵列）与重建的交互
- [[vbinfo-bits]] — VBINFO_BIT_IS_APL 标志位含义
