---
type: concept
title: "Pattern: RPMB Implementation Guide"
tags: [pattern, script, implementation, rpmb, authentication, security, write-counter]
sources: [script, spec, modeldefault]
created: 2026-06-21
updated: 2026-06-21
---

# Pattern: RPMB (Replay Protected Memory Block) Implementation Guide

## 概述

RPMB（Replay Protected Memory Block，重放保护存储块）pattern 测试 UFS 设备对 RPMB 认证机制的正确实现。RPMB 通过共享密钥（HMAC-SHA256）对写操作进行认证，并维护单调递增的写计数器（write counter）以防止重放攻击。

RPMB 相关测试分散在多个 pattern 文件夹中：`custom_vu`（0009、0036）、PSA、RAIN、APL Rebuild 等均使用 RPMB 进行 APL 块创建或安全验证。

---

## RPMB 区域配置

标准测试配置使用 4 个 RPMB 区域（Region 0–3）：

```python
# CustomVU_0009 配置
config_region_num = 4
region1_size == region2_size == region3_size == 1  # 每个区域大小为 1
```

---

## RPMB 初始化流程

### 标准初始化：Clear Key → Program Key → Write Counter

```
Step 1: Clear RPMB Key（如果已有旧密钥）
   VU D079: issue_D079_to_clear_rpmb_key(region)

Step 2: Program RPMB Key
   rpmb.rpmb_key_programming()

Step 3: Read Write Counter（验证密钥编程成功）
   counter = rpmb.rpmb_read_counter(region)
   # counter 应为 0（新初始化设备）

Step 4（可选）: Set Write Counter via VU D078
   issue_D078_to_set_rpmb_write_counter(region, counter_val)
```

### CustomVU_0009 完整流程

```python
# 对 4 个 RPMB 区域依次执行
for region in range(4):
    # 1. 清除密钥
    project_api.issue_D079_to_clear_rpmb_key(region)

    # 2. 编程密钥
    rpmb.rpmb_key_programming()

    # 3. 设置随机写计数器
    random_counter = randint(1, 0xFFFFFFFF)
    project_api.issue_D078_to_set_rpmb_write_counter(region, random_counter)

    # 4. 验证写计数器
    actual_counter = rpmb.rpmb_read_counter(region)
    assert actual_counter == random_counter

    # 5. 再次清除密钥
    project_api.issue_D079_to_clear_rpmb_key(region)

    # 6. 验证计数器重置为 0
    counter_after_clear = rpmb.rpmb_read_counter(region)
    assert counter_after_clear == 0
```

---

## RPMB VU 命令

| VU 编号 | 函数 | 作用 |
|--------|------|------|
| D079 | `issue_D079_to_clear_rpmb_key(region)` | 清除 RPMB 认证密钥 |
| D078 | `issue_D078_to_set_rpmb_write_counter(region, val)` | 设置 RPMB 写计数器（绕过认证，仅用于测试） |
| 4047 | `issue_4047_to_set_clear_query_RPMB_erase_password(password, cmd)` | 设置/清除/查询 RPMB 擦除密码 |
| 4048 | `issue_4048_to_trigger_RPMB_erase_status(password, cmd)` | 触发 RPMB 擦除 |

---

## 认证写入/读取流程

### RPMB 认证写入

```python
# 构建 RPMB 实例（指定区域）
rpmb = RPMB(RPMBRegion.REGION_0)

# 获取当前写计数器（防止重放）
counter = rpmb.rpmb_read_counter()

# 执行认证写入
rpmb.rpmb_write_data(lba=0, count=4)  # 写入 4 个 LBA
```

### RPMB 认证读取

```python
# 执行认证读取
data = rpmb.rpmb_read_data(lba=0, count=N)

# 验证数据内容（以每 512-byte LBA 中 bytes[228:484] 为有效数据）
for lba_idx in range(N):
    actual = data[lba_idx * 512 + 228 : lba_idx * 512 + 484]
    expected = expected_data[lba_idx]
    assert actual == expected
```

---

## RPMB 擦除测试（CustomVU_0036）

RPMB 擦除需要密码认证，流程如下：

```python
# 命令编码
SET_CMD   = 0   # 设置密码
CLEAR_CMD = 1   # 清除密码
QUERY_CMD = 2   # 查询密码状态

TRIGGER_CMD = 0  # 触发擦除
QUERY_STATUS_CMD = 1  # 查询擦除状态

# 状态码
STATUS_IDLE_SUCCESS  = 0
STATUS_COMPLETE      = 1
STATUS_IN_PROGRESS   = 2

# 流程
# 1. 查询初始密码状态
issue_4047(password=None, cmd=QUERY_CMD)

# 2. 清除已有密码
issue_4047(password=old_pwd, cmd=CLEAR_CMD)

# 3. 设置随机 64-bit 密码
password = random_64bit()
issue_4047(password=password, cmd=SET_CMD)

# 4. 查询状态，期望 status=1（已设置）
issue_4047(password=None, cmd=QUERY_CMD)

# 5. 写入 RPMB 数据
rpmb.rpmb_write_data(0, 4)

# 6. 触发擦除
issue_4048(password=password, cmd=TRIGGER_CMD)

# 7. 轮询直到擦除完成
while True:
    status = issue_4047(cmd=QUERY_CMD)
    if status == STATUS_COMPLETE:
        break

# 8. 验证 RPMB 数据归零
data = rpmb.rpmb_read_data(0, N)
assert all_zeros(data)

# 9. 错误测试：用错误密码尝试清除，期望 result=2
issue_4047(password=password-1, cmd=CLEAR_CMD)  # 期望失败

# 10. 正确密码清除
issue_4047(password=password, cmd=CLEAR_CMD)  # 期望 result=0
```

---

## RPMB 在 PSA Flow 中的使用（PSA_0001 Step 29）

在 PSA 完整流程的 step 29 中，RPMB 写入用于创建 APL（Application Layer）块：

```python
# PSA_0001 step 29
# 目的：创建 APL 块，使 VBINFO_BIT_IS_APL == 1

# 1. 确保 RPMB 密钥已编程
project_api.rpmb_key_programming()

# 2. 执行 RPMB 写入
rpmb = RPMB(RPMBRegion.REGION_0)
rpmb.rpmb_write_data(lba=0, count=4)

# 3. 执行 SPOR
api.init_tester_to_unit_ready(
    resetmode=Dcmd5ResetType.HW_RESET,
    powerdown=True
)

# 4. 验证 APL 标志
vbinfo = project_api.issue_40C0_to_get_VPCT_description(vb_num, option=0)
assert vbinfo.VBINFO_BIT_IS_APL == 1
```

### RPMB 在 APL Rebuild 测试中的使用

```python
# apl_system_rebuild/CustomVU_0001 step6
# RPMB write + SPOR → verify VBINFO_BIT_IS_APL == 1
project_api.rpmb_key_programming()
rpmb.rpmb_write_data(0, 4)
api.init_tester_to_unit_ready(HW_RESET, powerdown=True)
vbinfo = project_api.issue_40C0_to_get_VPCT_description(vb_num)
assert vbinfo.VBINFO_BIT_IS_APL == 1
```

---

## 进入 Vendor Mode 后的 RPMB 清理

在 test 完成后需要恢复 RPMB 状态：

```python
# 清除 RPMB 密钥（恢复初始状态）
access_vendor_mode()  # 进入 vendor mode（必须在清除前执行）
vuc_clear_rpmb_key(RPMBRegion.REGION_0)
```

---

## 常见异常和处理方式

| 异常 | 触发场景 | 处理方式 |
|------|---------|---------|
| `SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET` | RPMB 写入/读取前密钥未编程 | 确保 `rpmb_key_programming()` 在任何 RPMB 操作前执行 |
| `SPEC_ASSERT_RPMB_KEY_NOT_CLEARED` | 尝试清除密钥但密钥已经不存在 | 先用 QUERY_CMD 检查密钥状态 |
| `SIGHTING_FAIL_DATA_COMPARE_FAIL` | RPMB 读取数据与写入数据不匹配 | 检查 bytes[228:484] 数据格式，验证 LBA 范围 |
| `DLL_RESPONSE_ERROR` | RPMB 命令返回错误响应 | 检查写计数器（write counter）是否因重放攻击被拒绝 |

---

## 相关链接

- [[rpmb-key]] — RPMB 认证密钥编程和管理
- [[write-counter]] — RPMB 写计数器机制（防重放攻击）
- [[psa-state]] — PSA flow 中的 RPMB 使用（step 29）
- [[apl-rebuild]] — APL 块在 SPOR 后的重建机制
- [[vbinfo-bits]] — VBINFO_BIT_IS_APL 标志位含义
