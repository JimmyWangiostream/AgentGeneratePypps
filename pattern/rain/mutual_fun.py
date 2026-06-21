import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from typing import Dict, List, cast, Optional
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api.vendor_cmd.functions import *
from enum import Enum, IntEnum
from Script.project_api.functions import get_physical_layout
import math
import copy
import time
from typing import Any, List, Tuple


from types import FrameType

import inspect


USE_MICRON_VU = True

_flash_setting:FlashSetting = FlashSetting()
_fw_geometry:FwGeometry = FwGeometry()
_TestNormalLun = 0
_TestEM1Lun = 1
_TestWBLun = 3
_reconfig_au_toggle = -1
class TestMode(IntEnum):
    TEST_TLC = 0x00
    TEST_SLC = 0x01
    TEST_WB = 0x02
    TEST_PTE = 0x03
    TEST_L1 = 0x4
    TEST_LOG = 0x5
    TEST_TMP_RAIN = 0x6
    Dummy = 0xFF
    
def rain_pattern_precondition() -> tuple[int,int,int,FlashSetting, FwGeometry]:
    global _flash_setting, _fw_geometry, _TestNormalLun, _TestEM1Lun, _TestWBLun
    _flash_setting = api.get_flash_setting()
    _fw_geometry = api.get_fw_geometry()
    _TestNormalLun = 0
    _TestEM1Lun = 1
    _TestWBLun = 3
    config_lun(normal_list=[_TestNormalLun, _TestWBLun], em1_list=[_TestEM1Lun])
    au_size = shared.param.gGeometry.l79_write_booster_buffer_max_n_alloc_units
    config_WB_block = int((au_size * shared.param.gGeometry.b17_allocation_unit_size) * (shared.param.gGeometry.l13_segment_size) / 4096) * 512
    
    sorted_vb_dict = get_sorted_VB_list()
    if project_api.VBListNum.PTE_POOL in sorted_vb_dict:
        vb_list = [vb for vb in sorted_vb_dict[project_api.VBListNum.PTE_POOL]]
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.TableVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.MediumPriority)
    if project_api.VBListNum.CURRENT_L1 in sorted_vb_dict:
        vb_list = [vb for vb in sorted_vb_dict[project_api.VBListNum.CURRENT_L1]]
        project_api.issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type=project_api.VUC087VB_type.HostVB, VB_list=vb_list, booking_user=project_api.VUC087Paremeter.MediumPriority)
    polling_bkops_idle()
    return _TestNormalLun, _TestEM1Lun, _TestWBLun, _flash_setting, _fw_geometry

def get_geometry_parameter() -> tuple[int,int,int]:
    global _flash_setting, _fw_geometry
    max_ce = _flash_setting.Max_Fdevice
    max_plane = _flash_setting.Plane_Per_Die
    sector_per_page = 32
    max_pageline = _fw_geometry.l16_vb_size_pb_d1 // max_ce // max_plane // sector_per_page
    return max_ce, max_plane, max_pageline

def reconfig_to_erase_all_lun(write_record: List[List[api.WriteRecordNode]]) -> None:
    global _reconfig_au_toggle
    f = ExecuteCMD.FormatUnit()
    f.assign(lun=api.WellKnownLUN.UFS_DEVICE, longlist=0, cmplist=0)
    ExecuteCMD.enqueue(f)
    ExecuteCMD.send(clear_on_success=True)
    config_descs = api.get_config_descriptors(print=False)
    for index in range(4):
        config_descs[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
    for index in range(4):
        for unit_idx in range(8):
            if config_descs[index].units[unit_idx].b0_lu_enable == api.LUNEnable.ENABLE:
                config_descs[index].units[unit_idx].l4_num_alloc_units += _reconfig_au_toggle
    _reconfig_au_toggle *= -1
    for index in range(4):
        api.push_write_config(config_descs[index], index=index)
    ExecuteCMD.send()
    write_record[:] = api.get_empty_write_record()


def bytearray_xor(bytearray_list:List[bytearray], initXOR:Optional[bytearray] = None, check_len:int = 0) -> bytearray:
    if not check_len:
        check_len = len(bytearray_list[0])
    if not initXOR:
        outputXOR = bytearray(check_len)
    else:
        outputXOR = initXOR[0:check_len].copy()
    for temp in bytearray_list:
        for i in range(len(outputXOR)):
            outputXOR[i] ^= temp[i]
    return outputXOR

def config_lun(normal_list:List[int], em1_list:List[int]) -> None:
    selector = 0x00
    length = 0xE6
    Total_AU_Count = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
    EM1_total_AU = min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u, Total_AU_Count//(len(normal_list) + len(em1_list)) * len(em1_list))
    normal_total_AU = Total_AU_Count//(len(normal_list) + len(em1_list)) * len(normal_list)
    for index in range(4):
        cmd = ExecuteCMD.WriteDescriptor()
        cmd.assign(api.DescriptorIDN.CONFIGURATION, index, selector, length)

        desc = api.ConfigDescriptor310()
        desc.header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
        desc.header.b3_boot_enable = api.BootEnable.BOOT_DISABLE
        desc.header.b4_descr_access_en = api.DescrAccessEn.DISABLE
        desc.header.b5_init_power_mode = api.InitPowerMode.ACTIVE
        desc.header.b6_high_priority_lun = api.HighPriorityLUN.ALL_LUN_SAME_PRIORITY
        desc.header.b7_secure_removal_type = api.SecureRemovalType.BY_PHYSICAL_ERASE
        desc.header.b8_init_active_icc_level = api.InitActiveICCLevel.LVL_00
        desc.header.w9_periodic_rtc_update = 0
        desc.header.b11_hpb_control = 0
        desc.header.b12_rpmb_region_enable = api.RPMBRegionEnable.REGION_0_ENABLE
        desc.header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.DISABLE
        desc.header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
        desc.header.l18_num_shared_write_booster_buffer_alloc_units = shared.param.gGeometry.l79_write_booster_buffer_max_n_alloc_units if index==0 else 0

        
        for unit_idx in range(8):
            lun = index * 8 + unit_idx
            if lun in normal_list:
                desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                desc.units[unit_idx].b3_memory_type = api.MemoryType.NORMAL
                desc.units[unit_idx].l4_num_alloc_units = (normal_total_AU) // len(normal_list)
                desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
            elif lun in em1_list:
                desc.units[unit_idx].b0_lu_enable = api.LUNEnable.ENABLE
                desc.units[unit_idx].b1_boot_lun_id = api.BootLUNID.NOT_BOOTABLE
                desc.units[unit_idx].b2_lu_write_protect = api.LUNWriteProtect.NOT_WRITE_PROTECTED
                desc.units[unit_idx].b3_memory_type = api.MemoryType.ENHANCED_1
                desc.units[unit_idx].l4_num_alloc_units = (EM1_total_AU) // len(em1_list)
                desc.units[unit_idx].b8_data_reliability = api.DataReliability.LUN_NOT_PROTECTED
                desc.units[unit_idx].b9_logical_block_size = api.LogicalBlockSize.SIZE_4KB
                desc.units[unit_idx].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
            else:
                desc.units[unit_idx].b0_lu_enable = api.LUNEnable.DISABLE
                desc.units[unit_idx].l4_num_alloc_units = 0
                desc.units[unit_idx].b9_logical_block_size = 0

        cmd.set_desc(desc)
        ExecuteCMD.enqueue(cmd)
        ExecuteCMD.send()
    unit_desc_idxes:List[int] = []
    for lun in range(0, shared.param.gMaxNumberLU):
        unit_descriptor = ExecuteCMD.ReadDescriptor()
        unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
        unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

    ExecuteCMD.send(clear_on_success=False)
    for index in unit_desc_idxes:
        api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
    ExecuteCMD.clear()

    for lun in range(shared.param.gMaxNumberLU):
        if shared.param.gUnit[lun].b3_lu_enable:
            test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
            test_unit_ready.set_option(lun)
            ExecuteCMD.enqueue(test_unit_ready)
    ExecuteCMD.send()
    return

def get_invalid_plane_list() -> List[int]:
    global _flash_setting, _fw_geometry
    rsp, ics_table_payload = api.get_ics_table()
    ics_table:List[int] = [0xFF for i in range(_fw_geometry.l52_total_vb_count)]
    for idx in range(_fw_geometry.l52_total_vb_count):
        ics = api.ICSUnit(ics_table_payload, idx*4, (idx+1)*4 -1)
        if ics.ICS_block_index.value == 0xFFFF:
            break
        vb = ics.ICS_block_index.value
        ics_table[vb] = ics.Invalid_logical_plane.value
    return ics_table

def format_bytearray(barr:bytearray) -> str:
    return f"[{', '.join(f'0x{b:02x}' for b in barr)}]"

def get_PCA_and_print(lun: int, lba: int) -> project_api.physical_address_info:
    global _flash_setting, _fw_geometry
    max_plane = _flash_setting.Plane_Per_Die
    _, pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=lba)
    vb = pca.virtual_block_number.value
    Die = pca.die.value
    Plane = pca.plane.value
    Block = pca.physical_block_number_w_BBT.value
    Page = pca.page.value
    _, BB_info = project_api.issue_40C7_to_get_bad_block_info(Block, Die*max_plane+Plane)
    if BB_info.replaced_physical_block.value != 0xFFFFFFFF:
        RemapPB = BB_info.replaced_physical_block.value
    else:
        RemapPB = Block
    logger.info(f'Lun{lun}, LBA = {lba}: VB = {vb}, PhyBlock = {Block}, RemapPB = {RemapPB}, CE = {Die}, Plane = {Plane}, Page = {Page}')
    out_pca = copy.deepcopy(pca)
    out_pca.physical_block_number_w_BBT.value = RemapPB
    return out_pca

def print_open_vb_info_cursor(cursor:api.OpenVBInfoUnit, cursor_name:str) -> None:
    logger.info(f"===== {cursor_name} =====")
    logger.info(f"logical_vb: {cursor.logical_vb.value}")
    logger.info(f"physical_vb: {cursor.physical_vb.value}")
    logger.info(f"first_empty_CE: {cursor.first_empty_CE.value}")
    logger.info(f"first_empty_plane: {cursor.first_empty_plane.value}")
    logger.info(f"first_empty_physical_page: {cursor.first_empty_physical_page.value}")
    logger.info(f"first_empty_node: {cursor.first_empty_node.value}")

    
def direct_read_raw_data_and_check_status(pca:project_api.physical_address_info, SLC_enable:bool = False, expect_status:Optional[project_api.ReadStatus] = None, REH_Enable:bool = False) -> bytearray:
    vb = pca.virtual_block_number.value
    Die = pca.die.value
    Plane = pca.plane.value
    Block = pca.physical_block_number_w_BBT.value
    Page = pca.page.value
    logger.info(f'Direct Read: PhyBlock = {Block}, CE = {Die}, Plane = {Plane}, Page = {Page}, SLC_enable = {SLC_enable}')

    _,dire_read_payload = project_api.issue_4060_to_read_raw_data(Die=Die, Plane=Plane, Block=Block, Page=Page, SLC_Enable=SLC_enable, Ecc_Enable=1, Scrambler_Enable=1, REH_Enable=REH_Enable)
    expect_name = expect_status.name if expect_status else 'any'
    logger.info(f'Direct Read status = {format_bytearray(dire_read_payload[0x4000:0x4004])} (expect {expect_name})')
        
    if expect_status != None:
        expect_array = bytearray(4)
        for i in range(len(expect_array)):
            expect_array[i] = expect_status
        if dire_read_payload[0x4000:0x4004] != expect_array:
            dumpfile(f"direct_read_data_Block{Block}_CE{Die}_Plane{Plane}_Page{Page}.bin", dire_read_payload)
            logger.error_lb(f'check data read status of PhyBlock = {Block}, CE = {Die}, Plane = {Plane}, Page = {Page}')
            logger.error_fp(f'expect read_status of PhyBlock = {Block} is {expect_status}({expect_status.name}), but current payload[4000:4003] = {format_bytearray(dire_read_payload[0x4000:0x4004])}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    return dire_read_payload
    
    
def inject_UECC(pca:project_api.physical_address_info, SLC_enable:bool) -> project_api.physical_address_info:
    # inject_bitflip(pca=pca, SLC_enable=SLC_enable, flip_bits=[1000,1000,1000,1000])
    # return pca
    
    
    vb = pca.virtual_block_number.value
    Die = pca.die.value
    Plane = pca.plane.value
    Block = pca.physical_block_number_w_BBT.value
    Page = pca.page.value
    _, WL_type, phy_WL, SubBlock, FlushGroup, TwoWLGroup, RainGoup = get_physical_layout(pageline=Page, block_type="SLC" if SLC_enable else "TLC")
    for p in range(Page - 1, -1, -1):
        _, temp_WL_type, _, temp_SB, _, _, _ = get_physical_layout(pageline=p, block_type="SLC" if SLC_enable else "TLC")
        if temp_SB < 0 or temp_SB != SubBlock:
            break
        Page = p
        WL_type = temp_WL_type

    logger.info(f'Inject UECC: PhyBlock = {Block}, CE = {Die}, Plane = {Plane}, Page = {Page} (WL_type={WL_type}), SLC_enable = {SLC_enable}')
    if SLC_enable:
        dire_write_payload = bytearray(DATA_SIZE_16K_BYTE)
    else:
        dire_write_payload = bytearray(DATA_SIZE_20K_BYTE*3)
    for i in range(len(dire_write_payload)):
        dire_write_payload[i] = 0xAA
    _ = project_api.issue_C060_to_write_raw_data(Ce=Die,Block=Block,Plane=Plane, Page=Page,SLC_Enable=SLC_enable,Ecc_Enable=1, datapayload=dire_write_payload)

    # Return updated PCA with corrected page
    out_pca = copy.deepcopy(pca)
    out_pca.page.value = Page
    return out_pca

def inject_bitflip(pca:project_api.physical_address_info, SLC_enable:bool,
                 flip_bits: 'int | list[int]' = 50) -> project_api.physical_address_info:
    """
    在指定的 PCA page 上對 raw data 翻 bit，模擬 NAND cell error。

    翻多翻少決定結果是 HECC (correctable) 還是 UECC (uncorrectable)，
    取決於 ECC 強度與 flip_bits 數量。這個 function 本身只做翻 bit。 

    Step:
      1. 關 ECC/Scrambler 讀取 raw data
      2. 在各 4KB 區塊內隨機翻指定位元（每個 byte 只翻 1 bit）
      3. Erase block (D060)
      4. 將 flip 過的 data 以 ECC=0 寫回 (C060)
      5. 重新啟用 BKOPS

    FW 之後用 ECC on 讀這頁時，會 detect correctable errors 而進入 HECC 流程。

    Args:
        pca:           目標 page 的 physical address
        SLC_enable:    True=SLC, False=TLC
        flip_bits:     int 或 list[int]
                       - int: 只對第一個 4KB 翻該數量的 bit（向下相容）
                       - list[int]: 依序指定每個 4KB 區塊要翻的 bit 數。
                         SLC page 16K = block0~3（各 4KB）；
                         TLC sub-page 也是前 16K = block0~3，最後 4K 是 FW metadata 不動。
                         例如 SLC [50, 30, 0, 0] = block0 翻 50、block1 翻 30、
                         block2/3 不翻。長度不足的區塊視為 0。

    Returns:
        更新後的 PCA（page 維持原始指定的 page 不變）
    """
    vb = pca.virtual_block_number.value
    Die = pca.die.value
    Plane = pca.plane.value
    Block = pca.physical_block_number_w_BBT.value
    target_page = pca.page.value            # 使用者指定的原始 page
    wl_base = target_page                   # TLC 寫入時要用 WL base

    # 往後找到同一 subblock 的第一頁（WL base），但只作為內部定址用
    # TLC 的 C060 需要以 WL base (LP) 寫入 60KB 涵蓋 LP/UP/XP
    _, WL_type, _, SubBlock, _, _, _ = get_physical_layout(
        pageline=target_page, block_type="SLC" if SLC_enable else "TLC")
    for p in range(wl_base - 1, -1, -1):
        _, temp_WL_type, _, temp_SB, _, _, _ = get_physical_layout(
            pageline=p, block_type="SLC" if SLC_enable else "TLC")
        if temp_SB < 0 or temp_SB != SubBlock:
            break
        wl_base = p
        WL_type = temp_WL_type

    logger.info(f'Inject bitflip: PhyBlock = {Block}, CE = {Die}, Plane = {Plane}, '
                f'target_page = {target_page}, wl_base = {wl_base} '
                f'(WL_type={WL_type}), SLC_enable = {SLC_enable}, '
                f'flip_bits = {flip_bits}')

    # 停 BKOPS，避免 FW 背景動作出來干擾
    project_api.issue_D0FD_en_disable_BKOPS(bValue=0x00)

    # ─── 統一的 per-4K-block bit flip ─────────────────────────────────
    def _flip_4k_blocks(buf: bytearray, config: 'int | list[int]') -> int:
        """對 buf 的各 4KB 區塊套用 config 指定的翻 bit 數，回傳總翻 bit 數。"""
        per_block = config if isinstance(config, list) else [config]
        rng = random.Random()
        total = 0
        num_blk = (len(buf) + 4095) // 4096
        for bi in range(num_blk):
            n = per_block[bi] if bi < len(per_block) else 0
            if n <= 0:
                continue
            start = bi * 4096
            max_b = min(4096, len(buf) - start)
            if n > max_b:
                n = max_b
            for b_idx in rng.sample(range(start, start + max_b), n):
                buf[b_idx] ^= (1 << rng.randint(0, 7))
            total += n
        return total

    # ──────────────────────────────────────────────────────────────────

    if SLC_enable:
        # ───────── SLC：單一 16K page ─────────
        # 1) 關 ECC + Scrambler 讀 raw data
        _, raw_data = project_api.issue_4060_to_read_raw_data(
            Die=Die, Plane=Plane, Block=Block, Page=target_page,
            SLC_Enable=SLC_enable, Ecc_Enable=0, Scrambler_Enable=0)

        # 2) 在各 4KB 區塊翻指定位元
        flip_data = bytearray(raw_data)
        total_flipped = _flip_4k_blocks(flip_data, flip_bits)

        diff = sum(1 for i in range(len(raw_data)) if raw_data[i] != flip_data[i])
        logger.info(f'bitflip SLC: flipped {total_flipped} bits, {diff} bytes differ')

        # 3) Erase block
        project_api.issue_D060_to_erase_specific_block(
            Ce=Die, Plane=Plane, Block=Block, SlcEnable=SLC_enable, psaEnable=0)

        # 4) Write flipped data (ECC=0 避免 controller 重新 encode 蓋掉 error)
        project_api.issue_C060_to_write_raw_data(
            Ce=Die, Block=Block, Plane=Plane, Page=target_page,
            SLC_Enable=SLC_enable, Ecc_Enable=0, datapayload=flip_data)

    else:
        # ───────── TLC：LP/UP/XP 三頁一組 60KB ─────────
        pagelist: List[bytearray] = []
        for offset in range(3):
            _, rd = project_api.issue_4060_to_read_raw_data(
                Die=Die, Plane=Plane, Block=Block, Page=wl_base + offset,
                SLC_Enable=SLC_enable, Ecc_Enable=0, Scrambler_Enable=0)
            pagelist.append(bytearray(rd))

        # 決定要 flip LP(0)、UP(1)、還是 XP(2)
        target_offset = target_page - wl_base
        if target_offset < 0 or target_offset > 2:
            target_offset = 0

        raw_data_flip = pagelist[target_offset]
        # 只對前 16K (4 個 4KB) 翻 bit，最後 4K 是 FW metadata 不動
        flip_buf = bytearray(raw_data_flip[:DATA_SIZE_16K_BYTE])
        total_flipped = _flip_4k_blocks(flip_buf, flip_bits)
        pagelist[target_offset] = flip_buf + raw_data_flip[DATA_SIZE_16K_BYTE:]

        subpage_names = {0: "LP", 1: "UP", 2: "XP"}
        diff = sum(1 for i in range(DATA_SIZE_16K_BYTE)
                   if pagelist[target_offset][i] != raw_data_flip[i])
        logger.info(f'bitflip TLC: flipped {total_flipped} bits on {subpage_names[target_offset]} '
                    f'(page+{target_offset}), {diff} bytes differ')

        # 組出 60KB payload：[LP 20K][UP 20K][XP 20K]
        write_payload = bytearray(DATA_SIZE_20K_BYTE * 3)
        write_payload[0:DATA_SIZE_20K_BYTE] = pagelist[0]
        write_payload[DATA_SIZE_20K_BYTE:DATA_SIZE_20K_BYTE*2] = pagelist[1]
        write_payload[DATA_SIZE_20K_BYTE*2:] = pagelist[2]

        # Erase block
        project_api.issue_D060_to_erase_specific_block(
            Ce=Die, Plane=Plane, Block=Block, SlcEnable=SLC_enable, psaEnable=0)

        # Write three pages at once (C060 Page = WL 第一頁 = LP)
        project_api.issue_C060_to_write_raw_data(
            Ce=Die, Block=Block, Plane=Plane, Page=wl_base,
            SLC_Enable=SLC_enable, Ecc_Enable=0, datapayload=write_payload)

    # 恢復 BKOPS
    project_api.issue_D0FD_en_disable_BKOPS(bValue=0x01)

    # 回傳原始 PCA（page 維持 target_page 不變）
    out_pca = copy.deepcopy(pca)
    out_pca.page.value = target_page
    return out_pca

def create_closed_vb(testMode:TestMode, lun:int, write_record: List[List[api.WriteRecordNode]]) -> tuple[int, int]:
    if testMode not in [TestMode.TEST_TLC, TestMode.TEST_SLC, TestMode.TEST_WB]:
        logger.error_lb(f'create_closed_vb: unexpected testMode')
        logger.error_fp(f'{testMode.name} not expect, result Fail!')
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION
    if testMode == TestMode.TEST_WB:
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
    global _flash_setting, _fw_geometry
    slc_vb_size = (_fw_geometry.l84_vb_size_u0 * 512 // 4096)
    tlc_vb_size = (_fw_geometry.l88_vb_size_u1 * 512 // 4096)
    lba = 0
    total_size = tlc_vb_size if testMode == TestMode.TEST_TLC else slc_vb_size
    chunk_size = api.BLOCK4K_SIZE_128M_BYTE
    api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunk_size, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)
    lba+=total_size
    pca = get_PCA_and_print(lun=lun, lba=0)
    if testMode == TestMode.TEST_WB:
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
    return lba -1, pca.virtual_block_number.value

def read_compare_rain_result(write_record: List[List[api.WriteRecordNode]], compare_method: int = api.CompareMethod.HW_COMPARE, expect_error:bool = False) -> None:
    try:
        api.read_compare(write_record = write_record, compare_method = compare_method)
        if expect_error:
            logger.error_lb(f'read compare data')
            logger.error_fp(f'expect compare fail, but compare pass, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    except (DLL_CRC32_COMPARE_FAIL, DLL_PATTERN_2_ERROR) as e:
        if expect_error:
            ExecuteCMD.clear()
            pass
        else:
            raise e

def get_specific_open_vb_cursor(testMode:TestMode, print_info:bool = True) -> api.OpenVBInfoUnit:
    _, open_vb_info = api.get_open_vb_info()
    if testMode == TestMode.TEST_TLC:
        cursor = open_vb_info.TLC_L2
        name = "TLC_L2"
    elif testMode == TestMode.TEST_SLC:
        cursor = open_vb_info.SLC_L2
        name = "SLC_L2"
    elif testMode == TestMode.TEST_WB:
        cursor = open_vb_info.WB
        name = "WB"
    elif testMode == TestMode.TEST_PTE:
        cursor = open_vb_info.PTE
        name = "PTE"
    elif testMode == TestMode.TEST_L1:
        cursor = open_vb_info.TLC_L1
        name = "TLC_L1"
    elif testMode == TestMode.TEST_LOG:
        cursor = open_vb_info.LOG
        name = "LOG"
    elif testMode == TestMode.TEST_TMP_RAIN:
        cursor = open_vb_info.SWAP
        name = "SWAP"
    else:
        logger.error_lb(f'api {cast(FrameType, inspect.currentframe()).f_code.co_name}, validate_testMode: unexpected {testMode.name}')
        logger.error_fp(f'{testMode.name} not expect, result Fail!')
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION
    if print_info:
        print_open_vb_info_cursor(cursor, name)
    return cursor

def get_specific_RAIN_SWAP_vb(testMode:TestMode) -> tuple[int, int, int]:
    rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
    project_api.print_object_info_ai(open_vb_information)
    if testMode == TestMode.TEST_TLC:
        vb = open_vb_information.open_logical_VB_number_for_SWAP_RAIN_TLC.value
        pageline = open_vb_information.start_physical_page_of_parity_storage_VB_for_SWAP_RAIN_TLC.value
        ffp = open_vb_information.first_free_physical_page_of_SWAP_RAIN_TLC.value
    elif testMode == TestMode.TEST_SLC:
        vb = open_vb_information.open_logical_VB_number_for_SWAP_RAIN_EM1.value
        pageline = open_vb_information.start_physical_page_of_parity_storage_VB_for_SWAP_RAIN_EM1.value
        ffp = open_vb_information.first_free_physical_page_of_SWAP_RAIN_EM1.value
    elif testMode == TestMode.TEST_WB:
        vb = open_vb_information.open_logical_VB_number_for_SWAP_RAIN_WB.value
        pageline = open_vb_information.start_physical_page_of_parity_storage_of_SWAP_RAIN_WB.value
        ffp = open_vb_information.first_free_physical_page_of_SWAP_RAIN_WB.value
    elif testMode == TestMode.TEST_TMP_RAIN:
        vb = open_vb_information.open_Logical_VB_of_TMP_RAIN_VB_SSU_VB.value
        pageline = open_vb_information.start_physical_page_of_VB_of_TMP_RAIN_VB_SSU_VB.value
        ffp = 0
    else:
        logger.error_lb(f'api {cast(FrameType, inspect.currentframe()).f_code.co_name}, validate_testMode: unexpected {testMode.name}')
        logger.error_fp(f'{testMode.name} not expect, result Fail!')
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION
    return vb, pageline, ffp

def write_data_more_than_N_pageline(pageline_cnt:int, lun:int, testMode:TestMode, write_record: List[List[api.WriteRecordNode]], start_lba:int = 0) -> tuple[int, api.OpenVBInfoUnit]:
    if testMode == TestMode.TEST_WB:
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
    global _flash_setting, _fw_geometry
    cursor = get_specific_open_vb_cursor(testMode, print_info=False)
    lba = start_lba
    fua = 1
    prog_pageline = 3 if testMode == TestMode.TEST_TLC else 1
    if testMode == TestMode.TEST_PTE:
        page_line_len = api.BLOCK4K_SIZE_128M_BYTE
    elif testMode == TestMode.TEST_L1:
        page_line_len = api.BLOCK4K_SIZE_16K_BYTE
    else:
        page_line_len = api.BLOCK4K_SIZE_16K_BYTE * _flash_setting.Max_Fdevice * _flash_setting.Plane_Per_Die
    if cursor.logical_vb.value == 0xFFFFFFFF:
        cursor.first_empty_physical_page.value = 0
    
    total_size = math.ceil((pageline_cnt - cursor.first_empty_physical_page.value)/prog_pageline)*prog_pageline * page_line_len
    chunksize = min(WRITE_10_MAX_BLOCK_LEN, total_size) // (page_line_len * prog_pageline) * (page_line_len * prog_pageline)
    if pageline_cnt > cursor.first_empty_physical_page.value:
        api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunksize, fua = fua,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)
        lba += total_size
    cursor = get_specific_open_vb_cursor(testMode)

    chunksize = page_line_len * prog_pageline
    max_write_len = api.BLOCK4K_SIZE_32G_BYTE
    while cursor.first_empty_physical_page.value <= pageline_cnt - 1 and max_write_len > 0:
        api.sequential_write(lun=lun, start_lba=lba, total_size=chunksize, chunk_size=chunksize, fua = fua,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)
        lba += chunksize
        max_write_len -= chunksize
        cursor = get_specific_open_vb_cursor(testMode)
    if testMode == TestMode.TEST_WB:
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
    return lba -1 , cursor

def write_data_more_than_N_page(page_cnt:int, lun:int, testMode:TestMode, write_record: List[List[api.WriteRecordNode]], start_lba:int = 0) -> tuple[int, api.OpenVBInfoUnit]:
    if testMode == TestMode.TEST_WB:
        api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
    global _flash_setting, _fw_geometry
    cursor = get_specific_open_vb_cursor(testMode, print_info=False)
    ce_plane = _flash_setting.Plane_Per_Die * cursor.first_empty_CE.value + cursor.first_empty_plane.value
    lba = start_lba
    fua = 1
    if testMode == TestMode.TEST_PTE:
        page_len = api.BLOCK4K_SIZE_8M_BYTE
    else:
        page_len = api.BLOCK4K_SIZE_16K_BYTE
    if cursor.logical_vb.value == 0xFFFFFFFF:
        ce_plane = 0
    total_size = (page_cnt - ce_plane) * page_len
    chunksize = min(WRITE_10_MAX_BLOCK_LEN, total_size)//page_len * page_len
    if page_cnt > ce_plane:
        api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunksize, fua = fua,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)
        lba += total_size
    cursor = get_specific_open_vb_cursor(testMode)
    ce_plane = _flash_setting.Plane_Per_Die * cursor.first_empty_CE.value + cursor.first_empty_plane.value
    old_first_empty_physical_page = cursor.first_empty_physical_page.value
    chunksize = page_len
    max_write_len = api.BLOCK4K_SIZE_32G_BYTE
    while ce_plane < page_cnt and max_write_len>0 and cursor.first_empty_physical_page.value == old_first_empty_physical_page:
        api.sequential_write(lun=lun, start_lba=lba, total_size=chunksize, chunk_size=chunksize, fua = fua,
                            need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)
        lba += chunksize
        max_write_len -= chunksize
        cursor = get_specific_open_vb_cursor(testMode)
        ce_plane = _flash_setting.Plane_Per_Die * cursor.first_empty_CE.value + cursor.first_empty_plane.value
    if testMode == TestMode.TEST_WB:
        api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
    return lba -1 , cursor

def get_rain_parity_parameter(testMode:TestMode)-> tuple[int, project_api.RainUser]:
    if testMode == TestMode.TEST_TLC:
        rain_goup_cnt = 24
        rain_user = project_api.RainUser.HOST_TLC_RAIN
    elif testMode == TestMode.TEST_SLC:
        rain_goup_cnt = 8
        rain_user = project_api.RainUser.HOST_EM1_RAIN
    elif testMode == TestMode.TEST_WB:
        rain_goup_cnt = 8
        rain_user = project_api.RainUser.WB_RAIN
    elif testMode == TestMode.TEST_PTE:
        rain_goup_cnt = 1
        rain_user = project_api.RainUser.TABLE_RAIN
    elif testMode == TestMode.TEST_L1:
        rain_goup_cnt = 1
        rain_user = project_api.RainUser.TABLE_RAIN
    elif testMode == TestMode.TEST_LOG:
        rain_goup_cnt = 1
        rain_user = project_api.RainUser.TABLE_RAIN
    else:
        logger.error_lb(f'api {cast(FrameType, inspect.currentframe()).f_code.co_name}, validate_testMode: unexpected {testMode.name}')
        logger.error_fp(f'{testMode.name} not expect, result Fail!')
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION
    return rain_goup_cnt, rain_user
    
def get_rain_enable_disable_parameter(testMode:TestMode)-> tuple[project_api.RainVB, project_api.RainVB]:
    if testMode == TestMode.TEST_TLC:
        keep_rain = project_api.RainVB.TLC
        data_recovery = project_api.RainVB.TLC_recovery
    elif testMode == TestMode.TEST_SLC:
        keep_rain = project_api.RainVB.EM1
        data_recovery = project_api.RainVB.EM1_recovery
    elif testMode == TestMode.TEST_WB:
        keep_rain = project_api.RainVB.WB
        data_recovery = project_api.RainVB.WB_recovery
    elif testMode == TestMode.TEST_PTE:
        keep_rain = project_api.RainVB.Table
        data_recovery = project_api.RainVB.Table_recovery
    elif testMode == TestMode.TEST_L1:
        keep_rain = project_api.RainVB.S_CHK
        data_recovery = project_api.RainVB.S_CHK_recovery
    elif testMode == TestMode.TEST_LOG:
        keep_rain = project_api.RainVB.Table
        data_recovery = project_api.RainVB.Table_recovery
    else:
        logger.error_lb(f'api {cast(FrameType, inspect.currentframe()).f_code.co_name}, validate_testMode: unexpected {testMode.name}')
        logger.error_fp(f'{testMode.name} not expect, result Fail!')
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION
    return keep_rain, data_recovery

def get_general_parameter(testMode:TestMode)-> tuple[int, str]:
    global _flash_setting, _fw_geometry, _TestNormalLun, _TestEM1Lun, _TestWBLun
    if testMode == TestMode.TEST_TLC:
        lun = _TestNormalLun
        mode_str = "TLC"
    elif testMode == TestMode.TEST_SLC:
        lun = _TestEM1Lun
        mode_str = "EM1"
    elif testMode == TestMode.TEST_WB:
        lun = _TestWBLun
        mode_str = "WB"
    elif testMode == TestMode.TEST_PTE:
        lun = _TestNormalLun
        mode_str = "PTE"
    elif testMode == TestMode.TEST_L1:
        lun = _TestNormalLun
        mode_str = "L1"
    elif testMode == TestMode.TEST_LOG:
        lun = _TestNormalLun
        mode_str = "LOG"
    else:
        logger.error_lb(f'api {cast(FrameType, inspect.currentframe()).f_code.co_name}, validate_testMode: unexpected {testMode.name}')
        logger.error_fp(f'{testMode.name} not expect, result Fail!')
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION
    return lun, mode_str

def print_struct_byte(struct: project_api.PacketParserComposerABC) -> None:
    fields = [
        (name, field) for name, field in struct.__dict__.items()
        if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
    ]
    fields.sort(key=lambda kv: kv[1].start_offset)
    for name, field in fields:
        logger.info(
            f'Byte[{field.start_offset}:{field.end_offset}]: {name} = {hex(field.value)}'
        )
    return
def print_struct_bit(struct: project_api.BITPacketParserComposerABC) -> None:
    fields = [
        (name, field) for name, field in struct.__dict__.items()
        if hasattr(field, "start_bit") and hasattr(field, "end_bit") and hasattr(field, "value")
    ]
    fields.sort(key=lambda kv: kv[1].start_bit)
    for name, field in fields:
        logger.info(
            f'BIT[{field.start_bit}:{field.end_bit}]: {name} = {hex(field.value)}'
        )
    return

def print_rain_info(rain_info: project_api.RainInfo) -> None:
    for name, field in rain_info.__dict__.items():
        if isinstance(field, project_api.BITPacketParserComposerABC):
            logger.info(f"=============== {name} ===============")
            print_struct_bit(field)
            logger.info(f"======================================")
        elif isinstance(field, project_api.PacketParserComposerABC):
            logger.info(f"=============== {name} ===============")
            print_struct_byte(field)
            logger.info(f"======================================")
        else:
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value"):
                logger.info(
                    f'Byte[{field.start_offset}:{field.end_offset}]: {name} = {field.value}({hex(field.value)})'
                )
    for name, field in rain_info.current_RAIN_accumulation_count_for_each_parity.__dict__.items():
        if isinstance(field, list):
            logger.info(f"{name} : ")
            for ce, ce_fields in enumerate(field):
                values = [parities_cnt.value for group, parities_cnt in enumerate(ce_fields) if hasattr(parities_cnt, "start_offset") and hasattr(parities_cnt, "end_offset") and hasattr(parities_cnt, "value")]
                logger.info(f'CE[{ce}]: {values}')
    return
class UFSMapper:
    """UFS LBA mapping utility.

    Parameters
    ----------
    M : int
        Number of CE (Column Elements).
    N : int
        Number of Plane per CE.
    """

    def __init__(self, M: int, N: int):
        self.M = M
        self.N = N
        # constants
        self.LBAS_PER_PAGE = 4  # each page holds 4 LBA
        self.FPAGE_PER_LBA = 8   # each LBA occupies 8 fPage units

    def _lmu_count(self, pageline: int, is_TLC: bool = False) -> int:
        """Return the number of LMU for a given pageline and LUN.
        General LMU = 1, but LUN 0 has special ranges.
        """
        if not is_TLC:
            return 1
        # LUN 0 special rules
        if 540 <= pageline <= 555:
            return 2
        if 1108 <= pageline <= 1111:
            return 1
        return 3

    def lba_to_location(self, lba: int, is_TLC: bool = False) -> Dict[str,int]:
        """Convert an LBA to its physical location.

        Returns a dictionary with keys: ce, plane, fpage, lmu, pageline.
        """
        if lba < 0:
            raise ValueError("LBA must be non‑negative")

        remaining = lba
        pageline = 0
        # Find the pageline that contains the LBA
        while True:
            lmu_cnt = self._lmu_count(pageline, is_TLC)
            per_pageline = self.M * self.N * lmu_cnt * self.LBAS_PER_PAGE
            if remaining < per_pageline:
                break
            remaining -= per_pageline
            pageline += 1

        # Within the pageline, decode CE, LMU, Plane, and offset inside the page
        per_ce = self.N * lmu_cnt * self.LBAS_PER_PAGE
        ce = remaining // per_ce
        rem_ce = remaining % per_ce

        lmu = rem_ce // (self.N * self.LBAS_PER_PAGE)
        rem_lmu = rem_ce % (self.N * self.LBAS_PER_PAGE)

        plane = rem_lmu // self.LBAS_PER_PAGE
        # offset within the page (0‑3)
        offset_in_page = rem_lmu % self.LBAS_PER_PAGE
        # Compute absolute fPage based on pageline and offset within the page (32 fPages per pageline)
        fpage = pageline * 32 + offset_in_page * self.FPAGE_PER_LBA

        return {
            "ce": ce,
            "plane": plane,
            "fpage": fpage,
            "lmu": lmu,
            "pageline": pageline,
        }

    def location_to_lba(self, ce: int, plane: int, lmu: int, pageline: int, offset_in_page: int = 0, is_TLC: bool = False) -> int:
        """Convert a physical location back to its LBA.

        Parameters must be consistent with the mapping rules.
        `offset_in_page` is the index within a page (0‑3). Defaults to 0 for callers that omit it.
        """
        # Validate offset within page
        if not (0 <= offset_in_page < self.LBAS_PER_PAGE):
            raise ValueError("offset_in_page must be between 0 and 3")
        # Validate LMU index for the given pageline
        lmu_cnt = self._lmu_count(pageline, is_TLC)
        if not (0 <= lmu < lmu_cnt):
            raise ValueError(f"lmu {lmu} out of range for pageline {pageline} (max {lmu_cnt - 1})")

        # Accumulate LBA count of all previous pagelines
        base = 0
        for p in range(pageline):
            base += self.M * self.N * self._lmu_count(p, is_TLC) * self.LBAS_PER_PAGE

        per_ce = self.N * lmu_cnt * self.LBAS_PER_PAGE
        per_lmu = self.N * self.LBAS_PER_PAGE
        per_plane = self.LBAS_PER_PAGE

        offset = (
            ce * per_ce +
            lmu * per_lmu +
            plane * per_plane +
            offset_in_page
        )
        return base + offset
    
def get_sorted_VB_list() -> Dict[project_api.VBListNum, List[int]]:
    resp = project_api.custom_vu.issue_406D_get_VB_list_info()
    sorted_VB_list_dict:Dict[project_api.VBListNum, List[int]] = {}
    offset = 0
    VB_list = 0
    while offset < len(resp.data):
        vb_count = int.from_bytes(resp.data[offset:offset+2], byteorder='little')
        offset +=2
        for i in range(vb_count):
            vb = int.from_bytes(resp.data[offset:offset+2], byteorder='little')
            if project_api.VBListNum(VB_list) not in sorted_VB_list_dict:
                sorted_VB_list_dict[project_api.VBListNum(VB_list)] = []
            sorted_VB_list_dict[project_api.VBListNum(VB_list)].append(vb)
            offset +=2
        VB_list+=1
    return sorted_VB_list_dict

def polling_bkops_idle() -> None:
    while 1:
        bkops_status = api.read_attribute(idn=api.AttributeIDN.BG_OP_STATUS)
        if bkops_status == 0:
            break
        time.sleep(1)
        
def phison_pca_to_micron_pca(pca:PCA) -> project_api.physical_address_info:    
    pageline, WL_type, phy_WL, SubBlock, FlushGroup, TwoWLGroup, RainGoup = get_physical_layout(pca=pca)
    out_pca = project_api.physical_address_info()
    out_pca.die.value = pca.b5_ce
    out_pca.plane.value = pca.b6_plane
    out_pca.physical_block_number_w_BBT.value = (pca.b11_block_h<<8) | (pca.b10_block_l)
    out_pca.page.value = pageline
    return out_pca

def check_UECC_refresh_booking_Q(VB_list:List[int] = [], bookingUser:project_api.BookingUser = project_api.BookingUser.EH_BOOKSIGNALUECC_BOOKING_0) -> None:
    logger.info(f"issue VU 40C5 to check the refresh booking queue")
    _, booking_q = project_api.issue_40C5_to_get_booking_queue()
    if booking_q.LogicalVBNumberInBookingQueue.value == 0:
        logger.error_lb(f'check LogicalVBNumberInBookingQueue after RAIN decode')
        logger.error_fp(f'expect LogicalVBNumberInBookingQueue is not 0, but current value = {booking_q.LogicalVBNumberInBookingQueue.value}, result Fail!')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    for idx, VBs in enumerate(booking_q.BookingQueueVB):
        vb = VBs.LogicalVBNumber.value
        Priority_bit = project_api.BookingUser(VBs.TheBookingUser.value & 0x700)
        if Priority_bit == project_api.BookingUser.BOOKING_IN_HP:
            Priority = project_api.VUC087Paremeter.HighPriority
        elif Priority_bit == project_api.BookingUser.BOOKING_IN_MP:
            Priority = project_api.VUC087Paremeter.MediumPriority
        else:
            Priority = project_api.VUC087Paremeter.LowPriority
        TheBookingUser = project_api.BookingUser(VBs.TheBookingUser.value & project_api.BookingUser.MAX_BOOKING_USER_COUNT-1)
        logger.info(f'BookingQ[{idx}]: VB {vb}, TheBookingUser: {TheBookingUser.name} ({Priority.name})')
        expect_user = bookingUser
        expect_priority = project_api.VUC087Paremeter.HighPriority
        if vb in VB_list:
            if expect_user != TheBookingUser or expect_priority != Priority:
                logger.error_lb(f'check vb {vb} after Booking')
                logger.error_fp(f'expect VB {vb} is {expect_user.name} ({expect_priority.name}),  but current is {TheBookingUser.name} ({Priority.name}), result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            VB_list.remove(vb)
        pass     
    if VB_list:
        logger.error_lb(f'check all vb book in refresh booking queue')
        logger.error_fp(f'expect VBs {VB_list} is booked, but not found in 40C5, result Fail!')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    logger.info(f"issue VU C088 to start refresh")
    project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StartRefresh)
    logger.info(f"polling until refresh idle")
    polling_bkops_idle()
    pass


def check_BB_retirementafter_refresh(VB_list:List[int] = [], expect_reason:project_api.BBRetirementReaspnType = project_api.BBRetirementReaspnType.DUMMY) -> None:
    _, bbt_data = project_api.issue_405E_to_get_bad_block_information()
    total_BB_count = int.from_bytes(bbt_data[0:4], 'little')
    if total_BB_count == 0:
        logger.error_lb(f'check total_BB_count of VU')
        logger.error_fp(f'expect total_BB_count from BB Table not equal to 0 after UECC, but total_BB_count value = {total_BB_count}, result Fail!')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    start = 4
    for idx in range(total_BB_count):
        BB_retirement_reason = project_api.BB_retirement_reason(bbt_data[start + idx*8: start + idx*8 +4])
        PBA = project_api.PBA_format(bbt_data[start + 4 + idx*8: start + 4 + idx*8 +4])
        vb = PBA.blockNum.value
        BlkType = project_api.BBRetirementReaspnBlkType(BB_retirement_reason.BlkType.value)
        Reason = project_api.BBRetirementReaspnType(BB_retirement_reason.Type.value)
        # if BB_retirement_reason.BlkType.value != 0 or BB_retirement_reason.Type.value != 0:
        logger.info(f'idx = {idx}, Block : {vb},  BlkType = {BlkType} ({BlkType.name}), Reason = {Reason} ({Reason.name})')
        if vb in VB_list:
            if expect_reason != Reason:
                logger.error_lb(f'check vb {vb} BBRetirementReaspn after refresh')
                logger.error_fp(f'expect VB {vb} is {expect_reason.name},  but current is {Reason.name}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            VB_list.remove(vb)
        pass  
    if VB_list:
        logger.error_lb(f'check all vb BBRetirementReaspn in BBT')
        logger.error_fp(f'expect VBs {VB_list} is updated, but not found in 405E, result Fail!')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    return

def check_RAIN_cnt_in_heatlth_report(before_health:project_api.ReadEnhanceHealthReport, 
                                        d1_closed_raind_recovery_fail_count:Optional[bool] = None, 
                                        d3_closed_raind_recovery_fail_count:Optional[bool] = None, 
                                        d1_closed_raind_recovery_ok_count:Optional[bool] = None, 
                                        d3_closed_raind_recovery_ok_count:Optional[bool] = None, 
                                        d1_open_raind_recovery_fail_count:Optional[bool] = None, 
                                        d3_open_raind_recovery_fail_count:Optional[bool] = None, 
                                        d1_open_raind_recovery_ok_count:Optional[bool] = None, 
                                        d3_open_raind_recovery_ok_count:Optional[bool] = None, 
                                        ) -> None:
    def get_fields_lsit(any_struct: Any) -> list[tuple[Any, Any]]:
        raw_fields = [
            (name, field) for name, field in any_struct.__dict__.items()
            if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
        ]
        raw_fields.sort(key=lambda kv: kv[1].start_offset)
        return raw_fields
        
    def print_struct_different(before_struct: Any, after_struct: Any) -> None:
        before_fields = get_fields_lsit(before_struct)
        current_fields = get_fields_lsit(after_struct)            
        for (name0, raw), (name1, expect) in zip(
                                    before_fields,
                                    current_fields,
                                ):
            if hasattr(raw, "value") and hasattr(expect, "value") and name0 == name1:
                if raw.value != expect.value:
                    logger.info(f'{name0}: {raw.value} (0x{raw.value:X}) -> {expect.value} (0x{expect.value:X})')
            pass
    
    def check_value_modify(before_struct: Any, after_struct: Any, string:str, expect_modify:Optional[bool] = None) -> None:
        if expect_modify == None:
            return
        before_fields = get_fields_lsit(before_struct)
        current_fields = get_fields_lsit(after_struct)            
        for (name0, current), (name1, before) in zip(
                                    current_fields,
                                    before_fields,
                                ):
            if name0 == string:
                value = current.value
                value_before = before.value

                if value_before >= value and expect_modify:
                    logger.error_lb(f'check {string} value')
                    logger.error_fp(f'expect {string} increase, but current value = {value}, before value = {value_before}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                elif value_before != value and not expect_modify:
                    logger.error_lb(f'check {string} value')
                    logger.error_fp(f'expect {string} not increase, but current value = {value}, before value = {value_before}, result Fail!')
                    raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                return
            pass
    response, health_report = project_api.issue_40FE_to_read_enhanced_health_report()
    print_struct_different(before_health, health_report)
    check_value_modify(before_health, health_report, "d1_closed_raind_recovery_fail_count", d1_closed_raind_recovery_fail_count)
    check_value_modify(before_health, health_report, "d3_closed_raind_recovery_fail_count", d3_closed_raind_recovery_fail_count)
    check_value_modify(before_health, health_report, "d1_closed_raind_recovery_ok_count", d1_closed_raind_recovery_ok_count)
    check_value_modify(before_health, health_report, "d3_closed_raind_recovery_ok_count", d3_closed_raind_recovery_ok_count)
    check_value_modify(before_health, health_report, "d1_open_raind_recovery_fail_count", d1_open_raind_recovery_fail_count)
    check_value_modify(before_health, health_report, "d3_open_raind_recovery_fail_count", d3_open_raind_recovery_fail_count)
    check_value_modify(before_health, health_report, "d1_open_raind_recovery_ok_count", d1_open_raind_recovery_ok_count)
    check_value_modify(before_health, health_report, "d3_open_raind_recovery_ok_count", d3_open_raind_recovery_ok_count)
    before_health = health_report