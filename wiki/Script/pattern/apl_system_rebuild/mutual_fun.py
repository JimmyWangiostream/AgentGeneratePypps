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
from Script.project_api.functions import print_object_info_ai
from typing import Any, Mapping, cast, List, Final
from typing import Any, cast, Mapping as TMapping, List, Final
from Script.api.ufs_api.vendor_cmd.functions import *
from dataclasses import is_dataclass, asdict, fields
from typing import Any, Protocol, runtime_checkable, cast, TypeGuard
from Script.project_api.custom_vu.get_single_open_block.structs import SubVBInfo
import time
from typing import Iterable, List
from Script.project_api.custom_vu.do_power_loss_analysing_vu.functions import *
from Script.api.util.write_record.structs import WriteRecordNode
from Script.project_api.reh.functions import issue_409E_to_get_error_bit_numbers
def _extract_real_value(obj: Any) -> Any:
    """
    取出最終要比較的值。

    - 若是 Enum（或任何有 ``value`` 屬性的物件）回傳 ``obj.value``  
    - 否則直接回傳 ``obj``  
    - 若 ``obj`` 為 ``None``，回傳 ``None``（不會拋 ``AttributeError``）

    這樣的寫法兼容
    * enum.Enum 成員 → 取 ``.value``
    * 原始型別 (int、str、bytes …) → 直接使用
    * ``None`` → 仍回傳 ``None`` 供比較
    """
    if obj is None:
        return None
    # 只要有 ``value`` 屬性且不是內建的 ``dict``/``list`` 等容器，就取出
    if hasattr(obj, "value"):
        try:
            return obj.value
        except Exception:          # 防禦性寫法，防止屬性不是可呼叫的
            return obj
    return obj
ATTRS_TO_COMPARE = [
    "LWP",          # 例如：寫入的 LWP 數值
    "LWPStatus",    # 例如：LWP 狀態
    "FEPStatus",    # 例如：FEP 狀態
    # ... 如有其他需要比較的欄位請自行加入 ...
]

def _compare_one(a: APL_LWP_Check, b: APL_LWP_Check) -> Tuple[bool, List[str]]:
    """
    比較單一筆 APL_LWP_Check，回傳:
        - bool   : 是否完全相等
        - List[str] : 不相等欄位的說明文字
    """
    diffs: List[str] = []
    for attr in ATTRS_TO_COMPARE:
        raw_a = getattr(a, attr, None)
        raw_b = getattr(b, attr, None)
        val_a = _extract_real_value(raw_a)
        val_b = _extract_real_value(raw_b)
        if val_a != val_b:
            diffs.append(f"{attr}: {val_a!r} != {val_b!r}")

    return (len(diffs) == 0), diffs

_param = shared.param
g_dict: Mapping[str, Any] = {}
OpenVBchangeList : dict[str, dict[str, Any]] = {}
diffopenvb_dict: dict[str, dict[str, Any]] = {}
@runtime_checkable
class _HasValue(Protocol):
    value: Any
USE_MICRON_VU = True

_flash_setting:FlashSetting = FlashSetting()
_fw_geometry:FwGeometry = FwGeometry()
_TestNormalLun = 0
_TestEM1Lun = 1
_TestWBLun = 3
class TestMode(IntEnum):
    TEST_TLC = 0x00
    TEST_SLC = 0x01
    TEST_WB = 0x02
    TEST_PTE = 0x03
    TEST_L1 = 0x4
    TEST_LOG = 0x5
    TEST_TMP_RAIN = 0x6
class WL_Group(IntEnum):
    GroupA_TLC_start = 0
    GroupA_TLC_end = 1619
    GroupB_MLC_start = 1620
    GroupB_MLC_end = 1651
    GroupC_TLC_start = 1652
    GroupC_TLC_end = 3307
    GroupD_SLC_start = 3308
    GroupD_SLC_end = 3311
class TLC_parity(IntEnum):
    tlc_parity_start = 3288
    tlc_parity_end = 3311
def apl_pattern_precondition() -> None:
    global _flash_setting, _fw_geometry
    _flash_setting = api.get_flash_setting()
    _fw_geometry = api.get_fw_geometry()
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
    return _TestNormalLun, _TestEM1Lun, _TestWBLun, _flash_setting, _fw_geometry

def get_geometry_parameter() -> tuple[int,int,int]:
    global _flash_setting, _fw_geometry
    max_ce = _flash_setting.Max_Fdevice
    max_plane = _flash_setting.Plane_Per_Die
    sector_per_page = 32
    max_pageline = _fw_geometry.l16_vb_size_pb_d1 // max_ce // max_plane // sector_per_page
    return max_ce, max_plane, max_pageline

def check_timeout(start_time: float, timeout_min: int, timeout_sec:int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60 + timeout_sec:
        return True
    else:
        return False
def erase_all_lun(write_record: List[List[api.WriteRecordNode]]) -> None:
    for lun in range(shared.param.gMaxNumberLU):
        if not shared.param.gUnit[lun].b3_lu_enable:
            continue
        capacity = shared.param.gLUCapacity[lun]
        lba = 0
        while capacity > 0:
            length = min(ERASE_MAX_BLOCK_LEN, capacity)
            unmap = ExecuteCMD.Unmap()
            unmap.assign(lun=lun, lba=lba, length=length)
            ExecuteCMD.enqueue(unmap)
            capacity -= length
            lba += length            
    ExecuteCMD.send(clear_on_success=False)
    for cmd in ExecuteCMD._cmd_list:
        api.save_write_info_by_cmd(cmd, write_record)   
    ExecuteCMD.clear()
    f = ExecuteCMD.FormatUnit()
    f.assign(lun=api.WellKnownLUN.UFS_DEVICE, longlist=0, cmplist=0)
    ExecuteCMD.enqueue(f)
    ExecuteCMD.send()
    idn = api.FlagIDN.PURGE_EN
    logger.info(f'Host issue set purgeen flag idn = {idn}')
    set_flag = ExecuteCMD.SetFlag().assign(idn).enqueue()
    ExecuteCMD.send(clear_on_success=True)
    timeout_min = 0
    timeout_sec = 2000
    start_time = time.time()
    polling_cnt = 0
    while True:
        if check_timeout(start_time, timeout_min, timeout_sec):
            raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
        purge_status = api.read_attribute(idn=api.AttributeIDN.PURGE_STATUS)
        polling_cnt += 1
        logger.info(f'purge status = {purge_status}, polling count = {polling_cnt}')
        if purge_status is 0x03:
            logger.info(f'purge status = {purge_status}, complete')
            break


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

def get_written_data_buf(write_record: List[List[api.WriteRecordNode]], lun:int, lba:int) -> bytearray:
    for node in range(len(write_record[lun])):
        write_node = write_record[lun][node]
        start_lba = write_node.start_lba
        data_len = write_node.end_lba - write_node.start_lba + 1
        data_pattern_mode = write_node.data_pattern_mode
        add_tag = write_node.add_tag
        loop_count = write_node.mark_tag
        for j in range(data_len):
            if start_lba + j == lba:
                data_buffer = api.gen_data_pattern(api.DATA_SIZE_4K_BYTE, data_pattern_mode, start_lba + j, add_tag, loop_count)
                return data_buffer
    raise PATTERN_ASSERT_UNEXPECTED_CONDITION 


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
def SPOR_init_mp()-> bool:
    status = True
    try:
        # 這裡預期會失敗
        api.init_tester_to_unit_ready(
            resetmode=api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET),
            powerdown=False,
        )
    except Exception as e:                     # 若有特定例外類別，可改成 api.APIError
        # 錯誤處理：印出訊息、寫 log、或設定旗標等
        print(f"[ERROR] init_tester_to_unit_ready failed: {e}")
        status = False
        assertnum = api.get_fw_assert_number()
    else:
        status = True
    finally:
        if status == False:
            api.MP().execute()
            api.first_init_to_max_hs_gear(link_startup_mode=_param.current_speed.link_startup_mode, ref_clk=_param.current_speed.refclk)
        return status
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

def get_PCA_and_print(lun: int, lba: int, rpmb_region: int = 0) -> PCA:
    _pca = lba_to_pba(lun, lba, rpmb_region)
    pca = PCA()
    pca.from_bytes(bytearray(_pca.payload))
    logger.info(f'Lun{lun}, LBA = {lba}: Block = {(pca.b11_block_h<<8) | (pca.b10_block_l)}, mode = {pca.b4_mode}, CE = {pca.b5_ce}, Plane = {pca.b6_plane}, fPage = {pca.l12_fpage}(pageline = {pca.l12_fpage>>5}), lmu = {pca.b20_lmu}, format = {pca.b7_format}')
    return pca

def print_open_vb_info_cursor(cursor:api.OpenVBInfoUnit, cursor_name:str) -> None:
    logger.info(f"===== {cursor_name} =====")
    logger.info(f"logical_vb: {cursor.logical_vb.value}")
    logger.info(f"physical_vb: {cursor.physical_vb.value}")
    logger.info(f"first_empty_CE: {cursor.first_empty_CE.value}")
    logger.info(f"first_empty_plane: {cursor.first_empty_plane.value}")
    logger.info(f"first_empty_physical_page: {cursor.first_empty_physical_page.value}")
    logger.info(f"first_empty_node: {cursor.first_empty_node.value}")

def direct_read_raw_data(pca:PCA, conv_en:bool = True, read_parity:bool = False) -> tuple[bytearray, bytearray, List[bytearray]]:
    logger.info(f'Direct Read: Block = {(pca.b11_block_h<<8) | (pca.b10_block_l)}, mode = {pca.b4_mode}, CE = {pca.b5_ce}, Plane = {pca.b6_plane}, fPage = {pca.l12_fpage}(pageline = {pca.l12_fpage>>5}), lmu = {pca.b20_lmu}')
    FW_spare:List[bytearray] = []
    if read_parity:
        pca.l0_op = api.BIT20
        dire_read_payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=True)
        read_status = dire_read_payload[0x4080:0x4084+4]
        for i in range(4):
            FW_spare.append(dire_read_payload[0x4000 + i*16:0x4000 + (i+1)*16])
    else:
        if USE_MICRON_VU:
            if pca.b4_mode==1:
                page = pca.l12_fpage>>5
            else:
                page = (pca.l12_fpage>>5) * 3 + pca.b20_lmu
            _,dire_read_payload = project_api.issue_4060_to_read_raw_data(Die=pca.b5_ce, Plane=pca.b6_plane, Block=(pca.b11_block_h<<8) | (pca.b10_block_l), Page=page, SLC_Enable=int(pca.b4_mode==1),Ecc_Enable=1, Scrambler_Enable=int(conv_en))
            read_status = dire_read_payload[0x4000:0x4004]
            for i in range(4):
                FW_spare.append(dire_read_payload[0x4004 + i*16:0x4004 + (i+1)*16])
        else:
            if not conv_en:
                pca.l0_op = api.BIT24
            dire_read_payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=True)
            read_status = dire_read_payload[0x4080:0x4080+4]
            for i in range(4):
                FW_spare.append(dire_read_payload[0x4000 + i*16:0x4000 + (i+1)*16])
    data_payload_16K = dire_read_payload[0:DATA_SIZE_16K_BYTE]
    return read_status, data_payload_16K, FW_spare
    
def show_pca(pca:PCA)->None:
    logger.info(f'PCA: Block = {(pca.b11_block_h<<8) | (pca.b10_block_l)}, mode = {pca.b4_mode}, CE = {pca.b5_ce}, Plane = {pca.b6_plane}, fPage = {pca.l12_fpage}(pageline = {pca.l12_fpage>>5}), lmu = {pca.b20_lmu}')
def inject_UECC(pca:PCA) -> None:
    logger.info(f'Inject UECC: Block = {(pca.b11_block_h<<8) | (pca.b10_block_l)}, mode = {pca.b4_mode}, CE = {pca.b5_ce}, Plane = {pca.b6_plane}, fPage = {pca.l12_fpage}(pageline = {pca.l12_fpage>>5}), lmu = {pca.b20_lmu}')
    if USE_MICRON_VU:
        block = (pca.b11_block_h<<8) | (pca.b10_block_l)
        ce = pca.b5_ce
        plane = pca.b6_plane
        if pca.b4_mode == 0: #for system and hidden
            pca.b4_mode = 1
        mode = pca.b4_mode
        if pca.b4_mode==1:
            page = pca.l12_fpage>>5
            dire_read_payload = bytearray(DATA_SIZE_16K_BYTE)
        else:
            page = (pca.l12_fpage>>5) * 3
            dire_read_payload = bytearray(DATA_SIZE_16K_BYTE*3)
        for i in range(len(dire_read_payload)):
            dire_read_payload[i] = 0xAA
        _ = project_api.issue_C060_to_write_raw_data(Ce=ce, Plane=plane, Block=block, Page=page, SLC_Enable=int(mode==1),Ecc_Enable=1, datapayload=dire_read_payload)
    else:
        dire_read_payload = bytearray(DATA_SIZE_16K_BYTE)
        for i in range(len(dire_read_payload)):
            dire_read_payload[i] = 0xAA
        api.direct_write(pca = pca, block_count=4, data_buffer=dire_read_payload)
    return

def create_closed_vb(testMode:TestMode, lun:int, write_record: List[List[api.WriteRecordNode]]) -> tuple[int, int]:
    global _flash_setting, _fw_geometry
    slc_vb_size = (_fw_geometry.l84_vb_size_u0 * 512 // 4096)
    tlc_vb_size = (_fw_geometry.l88_vb_size_u1 * 512 // 4096)
    lba = 0
    total_size = tlc_vb_size if testMode == TestMode.TEST_TLC else slc_vb_size
    chunk_size = api.BLOCK4K_SIZE_128M_BYTE
    api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunk_size, fua = 0,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=write_record)
    lba+=total_size
    pca = get_PCA_and_print(lun=lun, lba=0)
    return lba -1, (pca.b11_block_h<<8) | (pca.b10_block_l)

def read_compare_rain_result(write_record: List[List[api.WriteRecordNode]], compare_method: int = api.CompareMethod.HW_COMPARE, expect_error:bool = False) -> None:
    try:
        api.read_compare(write_record = write_record, compare_method = compare_method)
        if expect_error:
            logger.error_lb(f'read compare data')
            logger.error_fp(f'expect compare fail, but compare pass, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    except (DLL_CRC32_COMPARE_FAIL, DLL_PATTERN_2_ERROR) as e:
        if expect_error:
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
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION
    if print_info:
        print_open_vb_info_cursor(cursor, name)
    return cursor

def get_specific_RAIN_SWAP_vb(testMode:TestMode) -> tuple[int, int]:
    rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
    if testMode == TestMode.TEST_TLC:
        vb = open_vb_information.open_logical_VB_number_for_SWAP_RAIN_TLC.value
        pageline = open_vb_information.start_physical_page_of_parity_storage_VB_for_SWAP_RAIN_TLC.value
    elif testMode == TestMode.TEST_SLC:
        vb = open_vb_information.open_logical_VB_number_for_SWAP_RAIN_EM1.value
        pageline = open_vb_information.start_physical_page_of_parity_storage_VB_for_SWAP_RAIN_EM1.value
    elif testMode == TestMode.TEST_WB:
        vb = open_vb_information.open_logical_VB_number_for_SWAP_RAIN_WB.value
        pageline = open_vb_information.start_physical_page_of_parity_storage_of_SWAP_RAIN_WB.value
    elif testMode == TestMode.TEST_TMP_RAIN:
        vb = open_vb_information.open_Logical_VB_of_TMP_RAIN_VB_SSU_VB.value
        pageline = open_vb_information.start_physical_page_of_VB_of_TMP_RAIN_VB_SSU_VB.value
    else:
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION
    return vb, pageline

def write_data_more_than_N_WL(WL_cnt:int, pageline_per_WL:int, lun:int, testMode:TestMode, write_record: List[List[api.WriteRecordNode]], start_lba:int = 0) -> tuple[int, api.OpenVBInfoUnit]:
    global _flash_setting, _fw_geometry
    # old_cursor = get_specific_open_vb_cursor(testMode)
    total_size = api.BLOCK4K_SIZE_32G_BYTE
    lba = start_lba
    fua = 0
    chunksize = api.BLOCK4K_SIZE_16K_BYTE * _flash_setting.Max_Fdevice * _flash_setting.Plane_Per_Die * pageline_per_WL
    while total_size:
        api.sequential_write(lun=lun, start_lba=lba, total_size=chunksize, chunk_size=chunksize, fua = fua,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=write_record)
        lba += chunksize
        total_size -= chunksize
        new_cursor = get_specific_open_vb_cursor(testMode)
        # if new_cursor.first_empty_physical_page.value - old_cursor.first_empty_physical_page.value > expect_pageline:
        if new_cursor.logical_vb.value != 0xFFFFFFFF:
            if new_cursor.first_empty_physical_page.value//pageline_per_WL > WL_cnt - 1:
                break
    return lba -1 , new_cursor

def write_data_more_than_N_pageline(pageline_cnt:int, lun:int, testMode:TestMode, write_record: List[List[api.WriteRecordNode]], start_lba:int = 0) -> tuple[int, api.OpenVBInfoUnit]:
    global _flash_setting, _fw_geometry
    cursor = get_specific_open_vb_cursor(testMode, print_info=False)
    lba = start_lba
    fua = 1
    if testMode == TestMode.TEST_PTE:
        page_line_len = api.BLOCK4K_SIZE_128M_BYTE
    elif testMode == TestMode.TEST_L1:
        page_line_len = api.BLOCK4K_SIZE_16K_BYTE
    else:
        page_line_len = api.BLOCK4K_SIZE_16K_BYTE * _flash_setting.Max_Fdevice * _flash_setting.Plane_Per_Die
    if cursor.logical_vb.value == 0xFFFFFFFF:
        cursor.first_empty_physical_page.value = 0
    total_size = (pageline_cnt - cursor.first_empty_physical_page.value) * page_line_len
    chunksize = min(WRITE_10_MAX_BLOCK_LEN, total_size) // page_line_len * page_line_len
    if pageline_cnt > cursor.first_empty_physical_page.value:
        api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunksize, fua = fua,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=write_record)
        lba += total_size
    cursor = get_specific_open_vb_cursor(testMode)

    chunksize = page_line_len
    max_write_len = api.BLOCK4K_SIZE_32G_BYTE
    while cursor.first_empty_physical_page.value <= pageline_cnt - 1 and max_write_len > 0:
        api.sequential_write(lun=lun, start_lba=lba, total_size=chunksize, chunk_size=chunksize, fua = fua,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=write_record)
        lba += chunksize
        max_write_len -= chunksize
        cursor = get_specific_open_vb_cursor(testMode)
    return lba -1 , cursor

def write_data_more_than_N_page(page_cnt:int, lun:int, testMode:TestMode, write_record: List[List[api.WriteRecordNode]], start_lba:int = 0) -> tuple[int, api.OpenVBInfoUnit]:
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
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=write_record)
        lba += total_size
    cursor = get_specific_open_vb_cursor(testMode)
    ce_plane = _flash_setting.Plane_Per_Die * cursor.first_empty_CE.value + cursor.first_empty_plane.value

    chunksize = page_len
    max_write_len = api.BLOCK4K_SIZE_32G_BYTE
    while ce_plane < page_cnt and max_write_len>0:
        api.sequential_write(lun=lun, start_lba=lba, total_size=chunksize, chunk_size=chunksize, fua = fua,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=write_record)
        lba += chunksize
        max_write_len -= chunksize
        cursor = get_specific_open_vb_cursor(testMode)
        ce_plane = _flash_setting.Plane_Per_Die * cursor.first_empty_CE.value + cursor.first_empty_plane.value
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
def get_and_print_open_vb_information() -> project_api.OpenVBInformation:
    rsp, open_vb_information = project_api.issue_40C1_to_get_open_vb_information()
    print_object_info_ai(open_vb_information)
    return open_vb_information    
def print_open_vb_information_phison(open_vb_info: OpenVBInfo) -> None:
    
    logger.info('================= open_vb_information =================')
    # 取得所有屬於 OpenVBInfoUnit 的子單元
    sub_units = {
        name: obj
        for name, obj in open_vb_info.__dict__.items()
        if hasattr(obj, "__dict__")               # 必須是物件
        and any(hasattr(v, "start_offset") for v in obj.__dict__.values())  # 內含欄位
    }

    for unit_name, unit_obj in sub_units.items():
        # 收集該單元內所有具有 start_offset / end_offset / value 的欄位
        fields = [
            (fname, fobj)
            for fname, fobj in unit_obj.__dict__.items()
            if hasattr(fobj, "start_offset")
            and hasattr(fobj, "end_offset")
            and hasattr(fobj, "value")
        ]

        # 依起始位元組排序
        fields.sort(key=lambda kv: kv[1].start_offset)

        # 輸出單元標頭
        logger.info(f'--- {unit_name} ---')
        # 輸出欄位資訊
        for fname, fobj in fields:
            logger.info(
                f'Byte[{fobj.start_offset}:{fobj.end_offset}]: '
                f'{unit_name}.{fname} = {fobj.value}'
            )
def get_ics_plane(vb:int) -> int:
    ics_bad_block = project_api.get_ics_bad_block()
    if ics_bad_block.ICSBadBlocks[vb].VB_index.value == vb:
        index_ics_plane = ics_bad_block.ICSBadBlocks[vb].invalid_VB_plane.value
        logger.info(f'index_ics_plane : {index_ics_plane}')
        return index_ics_plane
    else:
        return 0xFF
def check_ics(input_pca: PCA)-> bool:
    global _flash_setting
    read_pca = PCA()
    read_pca = input_pca
    ics_bad_block = project_api.get_ics_bad_block()
    vb = read_pca.b10_block_l + (read_pca.b11_block_h << 8)
    if ics_bad_block.ICSBadBlocks[vb].VB_index.value == vb:
        index_ics_plane = ics_bad_block.ICSBadBlocks[vb].invalid_VB_plane.value
        logger.info(f'index_ics_plane : {index_ics_plane}')
    if index_ics_plane != input_pca.b5_ce * _flash_setting.Plane_Per_Die + input_pca.b6_plane:
        return False
    else:
        return True
def compare_vb_fep(vb: int, fep:int, vb2: int, fep2:int)-> bool:
    if vb == vb2 and fep == fep2:
        return True
    else:
        return False
def compare_pb_fep(sub1: SubVBInfo, sub2: SubVBInfo)-> bool:
    logger.info(f'sub1.physicalblock : {sub1.physicalblock.value}, sub1.CE : {sub1.CE.value}, sub1.plane : {sub1.plane.value}, sub1.FEP : {sub1.FEP.value}')
    logger.info(f'sub2.physicalblock : {sub2.physicalblock.value}, sub2.CE : {sub2.CE.value}, sub2.plane : {sub2.plane.value}, sub2.FEP : {sub1.FEP.value}')
    if sub1.physicalblock.value == sub2.physicalblock.value and sub1.CE.value == sub2.CE.value and sub1.plane.value == sub2.plane.value and sub1.FEP.value == sub2.FEP.value:
        return True
    else:
        return False
def compare_pca_info(first_pca: PCA, second_pca: PCA) -> bool:
    #phison_ppage = self.wl_page_2_physical_page(phison_pca.b4_mode.value, phison_pca.w46_page.value, phison_pca.b20_lmu.value)
    #phison_offset = int((phison_pca.l12_fpage.value - phison_pca.w46_page.value *32) /8)
    if not (first_pca.b10_block_l == second_pca.b10_block_l and \
            first_pca.b6_plane == second_pca.b6_plane and \
            first_pca.b5_ce == second_pca.b5_ce and \
            first_pca.b11_block_h == second_pca.b11_block_h) :
        return False
    return True
def make_index_refresh_update_PT()-> None:
    ce_num = _flash_setting.Max_Fdevice
    plane_num = _flash_setting.Plane_Per_Die
    ce_plane_num = ce_num * plane_num
    tlc_ce_page = _flash_setting.Plane_Per_Die * 4 * 3
    tlc_pageline = tlc_ce_page * ce_num
    slc_ce_page = _flash_setting.Plane_Per_Die * 4
    logger.info(f'GET Open vb information by VU 0x40C1 as table2')
    get_open_vb = get_and_print_open_vb_information()
    open_vb_2: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
    ics_bad_block = project_api.get_ics_bad_block()
    direc_read_pca_2 = PCA()
    neg = 0
    while True:
        neg = neg + 1
        direc_read_pca_2.b10_block_l = open_vb_2.INDEX_VB_number_logical.value & 0xFF
        direc_read_pca_2.b11_block_h = (open_vb_2.INDEX_VB_number_logical.value >> 8) & 0xFF
        direc_read_pca_2.b5_ce = ((open_vb_2.INDEX_block_First_free_physical_page.value - neg)  % ce_plane_num) // plane_num
        direc_read_pca_2.b6_plane = ((open_vb_2.INDEX_block_First_free_physical_page.value - neg)  % ce_plane_num) % plane_num
        direc_read_pca_2.l12_fpage = ((open_vb_2.INDEX_block_First_free_physical_page.value - neg) // ce_plane_num) << 5
        logger.info('inject UECC on Index Mirror page LWP')
        if ics_bad_block.ICSBadBlocks[open_vb_2.INDEX_VB_number_logical.value].VB_index.value == open_vb_2.INDEX_VB_number_logical.value:
                index_ics_plane = ics_bad_block.ICSBadBlocks[open_vb_2.INDEX_VB_number_logical.value].invalid_VB_plane.value
                logger.info(f'index_ics_plane : {index_ics_plane}')
        if index_ics_plane != direc_read_pca_2.b5_ce * 6 + direc_read_pca_2.b6_plane:
            inject_UECC(direc_read_pca_2)
            break
    logger.info(f'HW reset without SSU')
    api.init_tester_to_unit_ready(resetmode = api.Dcmd5ResetType(api.Dcmd5ResetType.HW_RESET), powerdown = False)
    logger.info(f'GET Open vb information by VU 0x40C1 as table3')
    get_open_vb = get_and_print_open_vb_information()
    open_vb_3: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
    direc_read_pca_3 = PCA()
    direc_read_pca_3.b10_block_l = open_vb_3.INDEX_VB_number_logical.value & 0xFF
    direc_read_pca_3.b11_block_h = (open_vb_3.INDEX_VB_number_logical.value >> 8) & 0xFF
    direc_read_pca_3.b5_ce = ((open_vb_3.INDEX_block_First_free_physical_page.value - 1)  % ce_plane_num) // plane_num
    direc_read_pca_3.b6_plane = ((open_vb_3.INDEX_block_First_free_physical_page.value - 1)  % ce_plane_num) % plane_num
    direc_read_pca_3.l12_fpage = ((open_vb_3.INDEX_block_First_free_physical_page.value - 1) // ce_plane_num) << 5
    logger.info('compare table2 should different with table3')
    if compare_pca_info(direc_read_pca_2, direc_read_pca_3):
        logger.error_lb(f'inject UECC on Index Mirror page LWP and SPOR ')
        logger.error_fp(f'expect Index refresh, result Fail!')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
def injectUECC_from_FEP_to_page0_plane1(vb: int, fep: int)-> None:
    global _flash_setting
    ce_num = _flash_setting.Max_Fdevice
    plane_num = _flash_setting.Plane_Per_Die
    ce_plane_num = ce_num * plane_num
    uecc_pca = PCA()
    cnt = 1
    fep_page = fep // ce_plane_num << 5
    ics_plane = get_ics_plane(vb)
    last_plane = 0
    if ics_plane == 0:
        last_plane = 1
    while True:
        uecc_pca.b10_block_l = vb & 0xFF
        uecc_pca.b11_block_h = (vb >> 8) & 0xFF
        uecc_pca.b5_ce = ((fep - cnt)  % ce_plane_num) // plane_num
        uecc_pca.b6_plane = ((fep - cnt)  % ce_plane_num) % plane_num
        uecc_pca.l12_fpage = ((fep - cnt) // ce_plane_num) << 5
        if last_plane == uecc_pca.b6_plane and uecc_pca.b5_ce == 0 and uecc_pca.l12_fpage == 0:
            break
        if not check_ics(uecc_pca) :
            inject_UECC(uecc_pca)
        cnt = cnt +1
def injectUECC_from_FEP_to_ics(vb: int, fep: int)-> None:
    global _flash_setting
    ce_num = _flash_setting.Max_Fdevice
    plane_num = _flash_setting.Plane_Per_Die
    ce_plane_num = ce_num * plane_num
    uecc_pca = PCA()
    cnt = 1
    fep_page = fep // ce_plane_num << 5
    while True:
        uecc_pca.b10_block_l = vb & 0xFF
        uecc_pca.b11_block_h = (vb >> 8) & 0xFF
        uecc_pca.b5_ce = ((fep - cnt)  % ce_plane_num) // plane_num
        uecc_pca.b6_plane = ((fep - cnt)  % ce_plane_num) % plane_num
        uecc_pca.l12_fpage = ((fep - cnt) // ce_plane_num) << 5
        if not check_ics(uecc_pca) :
            inject_UECC(uecc_pca)
        else:
            if fep_page != uecc_pca.l12_fpage:
                break
        cnt = cnt +1
def print_array_tohex(databuff : bytearray, showlen :int, bytesperline: int) -> None:
    len = databuff.__len__()
    if len >= showlen:
        len = showlen
    for index in range(0,len,bytesperline):
        if(index + bytesperline < len):
            tmpdata = databuff[index: index+bytesperline]
            print(tmpdata.hex(' ',1) )
        else:            
            tmpdata = databuff[index: len]            
            print(tmpdata.hex(' ',1) )
    return
def injectUECC_from_FEP(vb: int, fep: int, startoffset: int, num:int)-> PCA:
    global _flash_setting
    ce_num = _flash_setting.Max_Fdevice
    plane_num = _flash_setting.Plane_Per_Die
    ce_plane_num = ce_num * plane_num
    uecc_pca = PCA()
    cnt = 1
    while num != 0:
        uecc_pca.b10_block_l = vb & 0xFF
        uecc_pca.b11_block_h = (vb >> 8) & 0xFF
        uecc_pca.b5_ce = ((fep - cnt)  % ce_plane_num) // plane_num
        uecc_pca.b6_plane = ((fep - cnt)  % ce_plane_num) % plane_num
        uecc_pca.l12_fpage = ((fep - cnt) // ce_plane_num) << 5
        if not check_ics(uecc_pca) :
            if startoffset <= 0:
                inject_UECC(uecc_pca)
                num = num-1
            else:
                startoffset = startoffset -1
        cnt = cnt +1
    return uecc_pca
def check_ics_and_jump_last_pca(input_pca: PCA)-> tuple[PCA,bool]:
    global _flash_setting
    read_pca = PCA()
    read_pca = input_pca
    ics_bad_block = project_api.get_ics_bad_block()
    vb = read_pca.b10_block_l + (read_pca.b11_block_h << 8)
    if ics_bad_block.ICSBadBlocks[vb].VB_index.value == vb:
        index_ics_plane = ics_bad_block.ICSBadBlocks[vb].invalid_VB_plane.value
        logger.info(f'index_ics_plane : {index_ics_plane}')
    if index_ics_plane != input_pca.b5_ce * _flash_setting.Plane_Per_Die + input_pca.b6_plane:
        return read_pca, True
    else:
        if read_pca.b5_ce == 0 and read_pca.b6_plane == 0 and read_pca.l12_fpage == 0:
            return read_pca, False
        elif read_pca.b6_plane != 0:
            read_pca.b6_plane = read_pca.b6_plane - 1
            return read_pca, True
        else:
            if read_pca.b5_ce != 0:
                read_pca.b5_ce = read_pca.b5_ce -1
                read_pca.b6_plane = 5
                return read_pca, True
            else:
                read_pca.b5_ce = _flash_setting.Max_Fdevice-1
                read_pca.b6_plane = 5
                read_pca.l12_fpage = read_pca.l12_fpage - (1<<5)
                return read_pca, True
def get_temp_code_vb() -> int:
    fw_code_physical_address = project_api.get_FW_code_physical_address_information()
    tempcode_vb = fw_code_physical_address.TempCodePhysicalAddress[0].block.value
    return tempcode_vb
def get_temp_code_ce() -> int:
    fw_code_physical_address = project_api.get_FW_code_physical_address_information()
    tempcode_ce = fw_code_physical_address.TempCodePhysicalAddress[0].CE.value
    return tempcode_ce
def get_isp_pca() -> tuple[PCA,PCA]:
    fw_code_physical_address = project_api.get_FW_code_physical_address_information()
    isp1 = fw_code_physical_address.CISCode1
    logger.info("ISP1: CISCode")
    print_object_info_ai(isp1)
    pca_isp1 = PCA()
    pca_isp1.b10_block_l = 0
    pca_isp1.b11_block_h = 0
    pca_isp1.b5_ce = isp1.CE.value
    pca_isp1.b6_plane = isp1.Plane.value
    pca_isp1.l12_fpage = (isp1.Page.value) << 5
    isp2 = fw_code_physical_address.CISCode2
    logger.info("ISP2: CISCode")
    print_object_info_ai(isp2)
    pca_isp2 = PCA()
    pca_isp2.b10_block_l = 0
    pca_isp2.b11_block_h = 0
    pca_isp2.b5_ce = isp2.CE.value
    pca_isp2.b6_plane = isp2.Plane.value
    pca_isp2.l12_fpage = (isp2.Page.value) << 5
    return pca_isp1, pca_isp2
def _bit_indices(start_bit: int, count: int) -> List[int]:
    """回傳連續的位元索引序列 [start_bit, start_bit+1, …, start_bit+count‑1]"""
    return list(range(start_bit, start_bit + count))
def print_bit_positions(indices: List[int], *, title: str = "") -> None:
    """
    把位元索引列印成兩欄：
      - 位元索引（0‑based）
      - 所屬 byte 與在 byte 內的 bit (LSB = 0)
    """
    if title:
        logger.info("\n=== " + title + " ===")
    logger.info(f"{'bit_idx':>8}  {'byte_idx':>8}  {'bit_in_byte':>11}")
    logger.info("-" * 30)
    for idx in sorted(indices):
        byte_idx = idx // 8
        bit_in_byte = idx % 8          # LSB 為 0
        logger.info(f"{idx:8d}  {byte_idx:8d}  {bit_in_byte:11d}")
def flip_bits_one_per_byte(
    raw: bytearray,
    *,
    total_bits: int = 500,
    block_index: int = 0,
    seed: int | None = None,
) -> List[int]:
    """
    在 *raw* 中的第 ``block_index`` 個 4 KB 區塊內，隨機翻轉 ``total_bits`` 個位元。
    - 每個 byte 只會翻 1 個 bit（使用 ``random.sample`` 產生不重複的 byte 索引）。
    - ``block_index = 0`` → 位元組 0  ~ 4095（原本行為）。
    - ``block_index = 1`` → 位元組 4096 ~ 8191（第 2 個 4 KB）。
    - 以此類推...

    參數
    ----------
    raw : bytearray
        會被原位元 (in‑place) 修改的緩衝區。
    total_bits : int, default 500
        要翻轉的位元數目。必須 ≤ 本區塊可用的 byte 數（每個 byte 最多 1 個 bit）。
    block_index : int, default 0
        想要操作的 4 KB 區塊編號，從 0 開始計算。
    seed : int | None
        若提供，會以此 seed 建立 ``random.Random``，讓測試可重現。

    回傳
    -------
    List[int]
        所有被翻轉的全域 bit 索引（0‑based），方便列印或除錯。
    """
    if total_bits < 0:
        raise ValueError("total_bits 必須為非負整數")
    if block_index < 0:
        raise ValueError("block_index 必須為非負整數")

    # 1️⃣ 计算本区块的起始 / 结束 byte
    block_start = block_index * 4096                     # 第 N 個 4 KB 的起點
    if block_start >= len(raw):
        raise ValueError(
            f"指定的 block_index ({block_index}) 超出 raw 的長度 "
            f"(len={len(raw)} bytes)。"
        )
    # 本区块实际可用的 byte 数（若 raw 在此处就截断了）
    max_bytes = min(4096, len(raw) - block_start)

    if total_bits > max_bytes:
        raise ValueError(
            f"欲翻轉的位元數 ({total_bits}) 大於本 4 KB 區塊可用的 byte 數 "
            f"({max_bytes})。每個 byte 只能翻 1 個 bit。"
        )

    # 2️⃣ 隨機抽樣不重複的 byte 索引（相對於整個 raw 的絕對位置）
    rng = random.Random(seed)
    byte_indices = rng.sample(
        range(block_start, block_start + max_bytes), total_bits
    )

    # 3️⃣ 為每個選中的 byte 隨機挑一個 bit (0~7) 並翻轉
    flipped_bit_positions: List[int] = []
    for b_idx in byte_indices:
        bit_off = rng.randint(0, 7)                 # 0~7 之間的整數
        global_bit_idx = b_idx * 8 + bit_off        # 全域 bit 索引
        flipped_bit_positions.append(global_bit_idx)

        # XOR 使該位元翻轉
        raw[b_idx] ^= 1 << bit_off

    # 4️⃣ 返回排序好的 bit 索引（方便列印）
    flipped_bit_positions.sort()
    return flipped_bit_positions
def flip_bits(
    raw: bytearray,
    *,
    start_bit: int = 0,
    count: int = 500,
    indices: Iterable[int] | None = None,
) -> List[int]:
    """
    在 *raw*（bytearray）內把指定的位元全部「翻轉」。
    
    參數說明
    ----------
    raw : bytearray
        必須是可寫的位元緩衝區。若是 `bytes`，請先 `bytearray(raw)`.
    start_bit : int, default 0
        起始位元 (0‑based)。只有在 **indices 為 None** 時會使用。
    count : int, default 500
        要翻轉的位元數目。只有在 **indices 為 None** 時會使用。
    indices : Iterable[int] | None, optional
        明確給出要翻轉的位元索引集合。若提供，`start_bit`、`count` 會被忽略。
        例如: `indices=[0, 5, 1023, 2048]`。
    
    用法
    ----
    >>> ba = bytearray(4096)               # 初始全 0
    >>> flip_bits(ba)                       # 翻轉前 500 個位元
    >>> flip_bits(ba, indices=[0, 10, 20])   # 只翻轉這三個位元
    >>> flip_bits(ba, count=1000, start_bit=2000)   # 翻轉第 2000~2999 位
    >>> flip_bits(ba, indices=random.sample(range(32768), 500))  # 隨機 500 位
    """
    # ---------- 1️⃣ 產生要翻轉的位元索引 ----------
    if indices is None:
        # 只翻連續的區段
        bit_idx_list = _bit_indices(start_bit, count)
    else:
        # 把傳入的任意 iterable 轉成 list（方便重複使用）
        bit_idx_list = list(indices)

    # ---------- 2️⃣ 依序翻轉 ----------
    for bit_idx in bit_idx_list:
        if bit_idx < 0:
            raise ValueError("bit index must be non‑negative")
        byte_idx = bit_idx // 8          # 哪一個 byte
        bit_off  = bit_idx % 8           # 在 byte 內的第幾個位元（LSB 為 0）
        # 檢查索引是否在緩衝區範圍內
        if byte_idx >= len(raw):
            raise IndexError(
                f"bit index {bit_idx} 超出緩衝區大小 "
                f"(max bits = {len(raw)*8 - 1})"
            )
        # 以 XOR 把該位元翻轉
        raw[byte_idx] ^= 1 << bit_off
    return bit_idx_list
# def _to_mapping(obj: Any) -> Mapping[str, Any]:
#         if is_dataclass(obj) and not isinstance(obj, type):
#             # asdict 只接受「實例」；此時 MyPy 能正確推斷型別
#             return cast(TMapping[str, Any], asdict(obj))

#         # 2️⃣ 已經是 Mapping（dict、OrderedDict …）
#         if isinstance(obj, Mapping):
#            return dict(obj)                     # -> dict[str, Any]

#         # 4️⃣ 有 __dict__（最常見的普通類別）
#         if hasattr(obj, "__dict__"):
#             return dict(vars(obj))
        
#         # 3️⃣ 有 __slots__ 的普通物件
#         if hasattr(obj, "__slots__"):
#             slots = getattr(obj, "__slots__")
#             if isinstance(slots, str):
#                 slots = (slots,)
#             return {slot: getattr(obj, slot) for slot in slots if hasattr(obj, slot)}


#         # 5️⃣ 其餘類型無法轉成 Mapping
#         raise TypeError(
#             f"Object of type {type(obj)!r} cannot be converted to a Mapping."
#         )
# def show_diff_open_vb_p2(open_vb_1: Any,open_vb_2: Any, lastclassname: str) -> bool:
#         if lastclassname == "":
#             OpenVBchangeList.clear()            # 這是您原本的全域 dict

#         # -------------------------------------------------------------
#         # 2️⃣ 把兩個物件都轉成 Mapping（key → value）
#         # -------------------------------------------------------------
#         dict1: Mapping[str, Any] = _to_mapping(open_vb_1)
#         dict2: Mapping[str, Any] = _to_mapping(open_vb_2)

#         # -------------------------------------------------------------
#         # 3️⃣ 取得所有 key 的聯集，確保「只在其中一側」的情形也能被偵測
#         # -------------------------------------------------------------
#         all_keys = set(dict1) | set(dict2)

#         all_equal = True   # 預設兩邊完全相同

#         for key in all_keys:
#             val1 = dict1.get(key)
#             val2 = dict2.get(key)

#             # ---------------------------------------------------------
#             # a) 任一側缺少此 key → 視為差異
#             # ---------------------------------------------------------
#             if val1 is None or val2 is None:
#                 all_equal = False
#                 logger.info(
#                     f"OpenVB change -> {lastclassname}.{key}: missing in one side"
#                 )
#                 continue

#             # ---------------------------------------------------------
#             # b) 兩側都是「BaseField」(或類似) 只比較 .value
#             # ---------------------------------------------------------
#             if isinstance(val1, _HasValue) and isinstance(val2, _HasValue):
#                 if val1.value != val2.value:
#                     all_equal = False
#                     logger.info(
#                         f"OpenVB change -> {lastclassname}.{key}: "
#                         f"0x{val1.value:x} != 0x{val2.value:x}"
#                     )
#                     # 把差異存到全域變數（保持您原有的行為）
#                     OpenVBchangeList.setdefault(lastclassname, {})[key] = val2
#                 continue

#             # ---------------------------------------------------------
#             # c) 兩側皆為 Mapping（巢狀結構） → 使用遞迴比較
#             # ---------------------------------------------------------
#             #if isinstance(val1, Mapping) and isinstance(val2, Mapping):
#             if isinstance(val1, OpenVBInfoUnit) and isinstance(val2, OpenVBInfoUnit):
#                 # 直接把 Mapping 傳下去，省去再一次 _to_mapping 的動作
#                 sub_equal = show_diff_open_vb_p2(val1, val2, key)
#                 if not sub_equal:
#                     all_equal = False
#                 continue

#             # ---------------------------------------------------------
#             # d) 其他類型（純量、List、bytes、bool …）直接比較
#             #    注意：若 key 為 'payload'（整段 bytearray），
#             #    只要不相等就直接列印十六進位差異
#             # ---------------------------------------------------------
#             if key != "payload" and val1 != val2:
#                 all_equal = False
#                 # 把可能不是 int 的值安全轉成十六進位字串
#                 try:
#                     hex1 = f"{int(val1):x}"
#                     hex2 = f"{int(val2):x}"
#                     logger.info(
#                         f"OpenVB change -> {lastclassname}.{key}: 0x{hex1} != 0x{hex2}"
#                     )
#                 except Exception:
#                     logger.info(
#                         f"OpenVB change -> {lastclassname}.{key}: {val1!r} != {val2!r}"
#                     )
#                 OpenVBchangeList.setdefault(lastclassname, {})[key] = val2
#                 continue

#             # 若是 key == "payload" 且值相同，就不需要再做任何事

#         # -------------------------------------------------------------
#         # 5️⃣ 回傳結果
#         # -------------------------------------------------------------
#         return all_equal
def collect_lwp_checks(
    opcode: int,
    vb: int,
    TLC: int,
    startpage: int,
    stoppage: int,
) -> List[APL_LWP_Check]:
    results: List[APL_LWP_Check] = []

    max_ce = _flash_setting.Max_Fdevice
    max_plane = _flash_setting.Plane_Per_Die
    for ce in range(max_ce):          # ce = 0,1,2,3
        for plane in range(max_plane):   # plane = 0~5
            logger.info(
                f"do LWP check on block{vb} ce{ce} plane{plane}"
            )
            rsp, lwpcheck_raw = issue_409D_to_do_power_loss_analysing(
                opcode,
                ce,
                plane,
                vb,
                TLC,
                startpage,
                stoppage,
            )
            # 依型別檢查器的需求把回傳值轉為 APL_LWP_Check
            lwpcheck: APL_LWP_Check = cast(APL_LWP_Check, lwpcheck_raw)

            # 若需檢查 rsp 是否成功(依實作而定)，可在此加判斷
            # if rsp != EXPECTED_OK:
            #     logger.warning("rsp not OK for ce=%s plane=%s", ce, plane)

            results.append(lwpcheck)

    return results

def compare_lwp_checks(lwpA: List[APL_LWP_Check],
                       lwpB: List[APL_LWP_Check]) -> Tuple[bool, List[str]]:
    """
    比較兩個 `collect_lwp_checks` 的結果。

    Parameters
    ----------
    lwpA, lwpB : List[APL_LWP_Check]
        兩筆由 `collect_lwp_checks` 產生的清單。

    Returns
    -------
    Tuple[bool, List[str]]
        - bool: 兩清單在所有欄位上完全一致。
        - List[str]: 差異說明（每筆不相等會產生一行文字）。
    """
    # 1️⃣ 長度檢查
    if len(lwpA) != len(lwpB):
        msg = f"長度不一致 → len(A)={len(lwpA)}, len(B)={len(lwpB)}"
        logger.error(msg)
        return False, [msg]

    all_ok = True
    details: List[str] = []

    # 2️⃣ 逐筆比對
    for idx, (a, b) in enumerate(zip(lwpA, lwpB)):
        equal, diffs = _compare_one(a, b)
        if not equal:
            all_ok = False
            for d in diffs:
                line = f"[index {idx}] {d}"
                details.append(line)
                logger.error(line)

    if all_ok:
        logger.info("lwpA 與 lwpB 完全相同 (共 %d 筆)", len(lwpA))
    else:
        logger.warning("lwpA 與 lwpB 有差異，請參考上方錯誤訊息")

    return all_ok, details
def count_diff_bytes(a: bytearray, b: bytearray) -> int:
    """
    計算兩個 bytearray 中不同的位元組數。

    - 同步長度的部分直接逐位元組比較。
    - 若長度不同，額外的位元組全部視為「不同」。
    """
    # 1️⃣ 先比較共同長度的部分
    diff = sum(x != y for x, y in zip(a, b))

    # 2️⃣ 再把長度差額加進去（多出的部份必定不同）
    diff += abs(len(a) - len(b))
    return diff
def build_write_payload20K(
    lp_fwrite: bytearray,
) -> bytearray:
    """
    每段資料的長度必須 ≤ 20 KB，超過時會拋出 ValueError。
    若實際長度小於 20 KB，剩餘的區段會保持為 0 (已於 write_payload 初始化)。
    """
    # 60 KB = 60 * 1024 bytes
    total_size = 20 * 1024
    write_payload = bytearray(total_size)       # 全部填 0

    # 各段的起始位元組偏移
    offsets = {
        "lp": 0,
    }

    # ------------------------------------------------------------------
    # 輔助函式：把 src 複製到 dst 的指定區段，並檢查長度上限
    # ------------------------------------------------------------------
    def _copy_into(src: bytearray, start: int, name: str) -> None:
        max_len = 20 * 1024                     # 每段允許的最大長度
        if len(src) > max_len:
            raise ValueError(f"{name}_fwrite 長度 {len(src)} 超過 20 KB 上限")
        end = start + len(src)                  # 只寫入實際長度
        write_payload[start:end] = src

    # ------------------------------------------------------------------
    # 依序寫入三段資料
    # ------------------------------------------------------------------
    _copy_into(lp_fwrite, offsets["lp"], "LP")

    return write_payload

def build_write_payload40K(
    lp_fwrite: bytearray,
    up_fwrite: bytearray,
) -> bytearray:
    """
    每段資料的長度必須 ≤ 20 KB，超過時會拋出 ValueError。
    若實際長度小於 20 KB，剩餘的區段會保持為 0 (已於 write_payload 初始化)。
    """
    # 60 KB = 60 * 1024 bytes
    total_size = 20 * 1024
    write_payload = bytearray(total_size)       # 全部填 0

    # 各段的起始位元組偏移
    offsets = {
        "lp": 0,
        "up": 20 * 1024,
    }

    # ------------------------------------------------------------------
    # 輔助函式：把 src 複製到 dst 的指定區段，並檢查長度上限
    # ------------------------------------------------------------------
    def _copy_into(src: bytearray, start: int, name: str) -> None:
        max_len = 20 * 1024                     # 每段允許的最大長度
        if len(src) > max_len:
            raise ValueError(f"{name}_fwrite 長度 {len(src)} 超過 20 KB 上限")
        end = start + len(src)                  # 只寫入實際長度
        write_payload[start:end] = src

    # ------------------------------------------------------------------
    # 依序寫入二段資料
    # ------------------------------------------------------------------
    _copy_into(lp_fwrite, offsets["lp"], "LP")
    _copy_into(up_fwrite, offsets["up"], "UP")

    return write_payload

def build_write_payload(
    lp_fwrite: bytearray,
    up_fwrite: bytearray,
    xp_fwrite: bytearray,
) -> bytearray:
    """
    合併三段資料成一個 60 KB 的 bytearray。

    每段資料的長度必須 ≤ 20 KB，超過時會拋出 ValueError。
    若實際長度小於 20 KB，剩餘的區段會保持為 0 (已於 write_payload 初始化)。
    """
    # 60 KB = 60 * 1024 bytes
    total_size = 60 * 1024
    write_payload = bytearray(total_size)       # 全部填 0

    # 各段的起始位元組偏移
    offsets = {
        "lp": 0,
        "up": 20 * 1024,
        "xp": 40 * 1024,
    }

    # ------------------------------------------------------------------
    # 輔助函式：把 src 複製到 dst 的指定區段，並檢查長度上限
    # ------------------------------------------------------------------
    def _copy_into(src: bytearray, start: int, name: str) -> None:
        max_len = 20 * 1024                     # 每段允許的最大長度
        if len(src) > max_len:
            raise ValueError(f"{name}_fwrite 長度 {len(src)} 超過 20 KB 上限")
        end = start + len(src)                  # 只寫入實際長度
        write_payload[start:end] = src

    # ------------------------------------------------------------------
    # 依序寫入三段資料
    # ------------------------------------------------------------------
    _copy_into(lp_fwrite, offsets["lp"], "LP")
    _copy_into(up_fwrite, offsets["up"], "UP")
    _copy_into(xp_fwrite, offsets["xp"], "XP")

    return write_payload
def write_data_until_dedicate_lwp(testlun:int, start_lba:int, dedicate_lwp: int, ce:int, plane:int, write_record:List[List[WriteRecordNode]])-> int:
    ce_num = _flash_setting.Max_Fdevice
    plane_num = _flash_setting.Plane_Per_Die
    pagesize = 4
    ce_plane_num = ce_num * plane_num
    tlc_ce_page = _flash_setting.Plane_Per_Die * 4 * 3
    mlc_ce_page = _flash_setting.Plane_Per_Die * 4 * 2
    tlc_pageline = tlc_ce_page * ce_num
    slc_ce_page = _flash_setting.Plane_Per_Die * 4
    slc_pageline = slc_ce_page * ce_num
    write_len = tlc_ce_page
    TLC = 0
    SLC = 1
    opcode = 0
    slc_max_page = 1103
    tlc_max_page = 3311
    startpage = 0
    stoppage = tlc_max_page
    
    get_open_vb = get_and_print_open_vb_information()
    open_vb_1: project_api.OpenVBInformation = project_api.OpenVBInformation(get_open_vb.payload.copy())
    vb = open_vb_1.L2_Open_logical_VB_Host_TLC_number.value
    rsp, lwpcheck_raw = issue_409D_to_do_power_loss_analysing(
                opcode,
                ce,
                plane,
                vb,
                TLC,
                startpage,
                stoppage,
            )
            # 依型別檢查器的需求把回傳值轉為 APL_LWP_Check
    lwpcheck: APL_LWP_Check = cast(APL_LWP_Check, lwpcheck_raw)
    currentlwp = lwpcheck.LWP.value
    if currentlwp == 65535:
        currentlwp = 0
    if (dedicate_lwp > currentlwp + 3) or currentlwp == 0xFFFF :
        # if dedicate_lwp < WL_Group.GroupA_TLC_end:
        #     write_len = (dedicate_lwp - currentlwp) // 3 * tlc_ce_page
        # elif dedicate_lwp < WL_Group.GroupB_MLC_end :
        #     write_len = (dedicate_lwp - currentlwp) // 3 * tlc_ce_page
        write_len = (dedicate_lwp - currentlwp - 3) * slc_pageline
        api.sequential_write(lun=testlun, start_lba=start_lba, total_size=write_len, chunk_size=slc_pageline, fua = 0,
                            need_compare=True, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)
        start_lba = start_lba + write_len
    rsp, lwpcheck_raw = issue_409D_to_do_power_loss_analysing(
                opcode,
                ce,
                plane,
                vb,
                TLC,
                startpage,
                stoppage,
            )
            # 依型別檢查器的需求把回傳值轉為 APL_LWP_Check
    lwpcheck: APL_LWP_Check = cast(APL_LWP_Check, lwpcheck_raw)
    currentlwp = lwpcheck.LWP.value
    while True:
        if currentlwp < WL_Group.GroupA_TLC_end:
            write_len = tlc_ce_page
        elif currentlwp < WL_Group.GroupB_MLC_end:
            write_len = mlc_ce_page
        elif currentlwp < WL_Group.GroupC_TLC_end:
            if currentlwp < TLC_parity.tlc_parity_start:
                write_len = tlc_ce_page
            else:
                write_len = tlc_ce_page - (pagesize *3) # parity
        else:
            write_len = 1

        api.sequential_write(lun=testlun, start_lba=start_lba, total_size=write_len, chunk_size=tlc_ce_page, fua = 1,
                            need_compare=True, compare_method=api.CompareMethod.HW_COMPARE, write_record=write_record)
        start_lba = start_lba + write_len
        rsp, lwpcheck_raw = issue_409D_to_do_power_loss_analysing(
                opcode,
                ce,
                plane,
                vb,
                TLC,
                startpage,
                stoppage,
            )
            # 依型別檢查器的需求把回傳值轉為 APL_LWP_Check
        lwpcheck = cast(APL_LWP_Check, lwpcheck_raw)
        currentlwp = lwpcheck.LWP.value
        if lwpcheck.LWP.value >= dedicate_lwp:
            break

    return start_lba
    
def flipbit_on_PTE_smart(lun:int, lba:int)->None:
    ce_num = _flash_setting.Max_Fdevice
    plane_num = _flash_setting.Plane_Per_Die
    ce_plane_num = ce_num * plane_num
    slc_ce_page = _flash_setting.Plane_Per_Die * 4
    #api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=int(slc_ce_page), chunk_size=slc_ce_page, fua = 1,
    #                 need_compare=False, compare_method=api.CompareMethod.HW_COMPARE, write_record=self.write_record)
    logger.info(f'GET Open vb information by VU 0x40C1')
    get_open_vb = get_and_print_open_vb_information()
    testlba = 0
    isSLC = 1
    logger.info(f'GET LUN {lun}，LBA {lba} physical address by VU 0x4051')
    _,micron_pca = project_api.issue_4051_to_get_physical_address(lun, lba)
    micron_pca.die.value = 0
    micron_pca.plane.value = 0
    micron_pca.virtual_block_number.value = get_open_vb.PTE_Block_VB_number_logical.value
    micron_pca.page.value = 0
    
    cnt = 1
    while True:
        micron_pca.die.value = ((get_open_vb.PTE_block_First_free_physical_page.value - cnt)  % ce_plane_num) // plane_num
        micron_pca.plane.value = ((get_open_vb.PTE_block_First_free_physical_page.value - cnt)  % ce_plane_num) % plane_num  
        micron_pca.page.value = ((get_open_vb.PTE_block_First_free_physical_page.value - cnt) // ce_plane_num) #<< 5 assert 0x5E8D
        ics_bad_block = project_api.get_ics_bad_block()
        vb = micron_pca.virtual_block_number.value
        if ics_bad_block.ICSBadBlocks[vb].VB_index.value == vb:
            index_ics_plane = ics_bad_block.ICSBadBlocks[vb].invalid_VB_plane.value
            logger.info(f'index_ics_plane : {index_ics_plane}')
        if index_ics_plane != micron_pca.die.value * plane_num + micron_pca.plane.value:
            break
        cnt+=1
    pagelist:List[bytearray] = []
    for idx_page in range(0,micron_pca.page.value+1):
        if idx_page == micron_pca.page.value:
            logger.flow(3, f'VU 4060 read raw data on page {idx_page} with ECC off')
            _, raw_data = project_api.issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=0)
            dumpfile("read_raw_data.bin", raw_data)
            flip_data = copy.deepcopy(raw_data)
            flipBitCount = 100
            flipbit = flipBitCount
            flipped = flip_bits_one_per_byte(flip_data, total_bits=flipbit, block_index=0) 
            diffcount = count_diff_bytes(raw_data, flip_data)
            logger.info(f'LP different count ={diffcount} after flip bits {flipbit}')
            
            print_bit_positions(flipped, title=f"{flipbit} bits position")
            logger.info(f"Flip first {flipbit} bits – done")
            logger.info(f"raw_data_flip = {len(flip_data)}") 
            write_payload = flip_data 
            pagelist.append(flip_data)
        else:
            logger.flow(3, f'VU 4060 read raw data on page {idx_page} with ECC off')
            _, raw_data_nonflip = project_api.issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=idx_page, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=0)
            dumpfile("read_raw_data_nonflop.bin", raw_data_nonflip)
            pagelist.append(raw_data_nonflip)

    #erase
    logger.flow(3, 'issue D060 to erase original data')
    project_api.issue_D060_to_erase_specific_block(Ce=micron_pca.die.value,Plane=micron_pca.plane.value,Block=micron_pca.virtual_block_number.value,SlcEnable=isSLC, psaEnable = 0)
        
    #write raw data
    for idx_page in range(0,micron_pca.page.value+1):
        write_payload = pagelist[idx_page]
        #dumpfile(f"write_raw_data.bin", write_payload)
        _ = project_api.issue_C060_to_write_raw_data(Ce=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=idx_page, SLC_Enable=isSLC,Ecc_Enable=0, datapayload=write_payload)
    
    #read raw data
    _, raw_data_1 = project_api.issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=1, Scrambler_Enable=1, PSA_Enable=0)
    raw_data_11 = copy.deepcopy(raw_data_1)
    # diffcount = self.count_diff_bytes(raw_dataLP, raw_data_11)
    diffcount = count_diff_bytes(raw_data, raw_data_1)
    logger.info(f'LP different count ={diffcount}')
    dumpfile(f"FW_FLOW_READ.bin", raw_data_1)

    logger.flow(13, f'Issue 409E VUC with ECC information = 1 to get error bit numbers')
    _, output_409E = issue_409E_to_get_error_bit_numbers()
    error_bits_409E = [output_409E.errorBitNumber1.value, output_409E.errorBitNumber2.value, output_409E.errorBitNumber3.value, output_409E.errorBitNumber4.value]
    logger.info(f'409E error bits ={error_bits_409E}')

    _, raw_data_after_flip = project_api.issue_4060_to_read_raw_data(Die=micron_pca.die.value, Plane=micron_pca.plane.value, Block=micron_pca.virtual_block_number.value, Page=micron_pca.page.value, SLC_Enable=isSLC, Ecc_Enable=0, Scrambler_Enable=0, PSA_Enable=0)
    dumpfile(f"pageLP_after.bin", raw_data_after_flip)
    diffcount = count_diff_bytes(raw_data, raw_data_after_flip)
    logger.info(f'LP different count ={diffcount}')
    pass
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
def sort_vb_info_with_details(vb_info: bytearray) -> tuple[bytearray, list[list[int]]]:
    view = memoryview(vb_info)
    result_bytearray = bytearray()
    groups_list = []  # 用來儲存每一組的整數內容
    
    index = 0
    length = len(view)
    
    while index < length:
        # 讀取 count (2 位元組)
        count = struct.unpack_from('<H', view, index)[0]
        index += 2
        
        # 一次讀取該組的所有整數
        fmt = f'<{count}H'
        info_list = list(struct.unpack_from(fmt, view, index))
        index += count * 2
        
        # 排序
        info_list.sort()
        
        # 記錄排序後的整數到對應的索引中（groups_list[0], groups_list[1]...）
        groups_list.append(info_list)
        
        # 重新打包
        result_bytearray.extend(struct.pack(f'<H{count}H', count, *info_list))
        
    return result_bytearray, groups_list
def sort_vb_info(vb_info: bytearray) -> bytearray:
    result_bytearray = bytearray()
    index = 0
    
    while index < len(vb_info):
        count = int.from_bytes(vb_info[index:index+2], byteorder='little')
        index += 2
        
        info_list = []
        for _ in range(count):
            info = int.from_bytes(vb_info[index:index+2], byteorder='little')
            info_list.append(info)
            index += 2
        info_list.sort()
        
        result_bytearray.extend(count.to_bytes(2, byteorder='little'))
        for info in info_list:
            result_bytearray.extend(info.to_bytes(2, byteorder='little'))
    
    return result_bytearray
def get_sorted_VB_group_from_VU_406D() -> list[list[int]]:
    resp = project_api.custom_vu.issue_406D_get_VB_list_info()
    api.util.dumpfile(filename = 'VB_list_info_fromVU', data = resp.data)
    sorted_bytes, vb_groups = sort_vb_info_with_details(resp.data)
    api.util.dumpfile(filename = 'VB_list_info_fromVU_sorted', data=sorted_bytes)
    return vb_groups
def find_LP_from_pageline(pageline:int) -> int:
    lp = 0
    tlc_sharepage = 3
    mlc_sharepage = 2
    slc_sharepage = 1
    if pageline <= WL_Group.GroupA_TLC_end:
        lp = pageline // tlc_sharepage * tlc_sharepage
    elif pageline <= WL_Group.GroupB_MLC_end:
        lp = (pageline - WL_Group.GroupB_MLC_start) // mlc_sharepage * mlc_sharepage + WL_Group.GroupB_MLC_start
    elif pageline <= WL_Group.GroupC_TLC_end:
        lp = (pageline - WL_Group.GroupC_TLC_start) // tlc_sharepage * tlc_sharepage + WL_Group.GroupC_TLC_start
    elif pageline <= WL_Group.GroupD_SLC_end:
        lp = (pageline - WL_Group.GroupD_SLC_start) // slc_sharepage * slc_sharepage + WL_Group.GroupD_SLC_start
    else:
        lp = 0
    return lp
def pageline_to_pageOrder(page:int)-> int:
    wl_base = [0, 540, 556, 1108]
    region_base = [0, 1620, 1652, 3308]
    REGION_TYPE_L   = 0
    REGION_TYPE_LU  = 1
    REGION_TYPE_LUX = 2
    tlc_sharepage = 3
    mlc_sharepage = 2
    slc_sharepage = 1
    lpage = 0
    if page < 1620:
        region = 0
        region_type = REGION_TYPE_LUX
    elif page < 1652:
        region = 1
        region_type = REGION_TYPE_LU
    elif page < 3308:
        region = 2
        region_type = REGION_TYPE_LUX
    elif page < 3312:
        region = 3
        region_type = REGION_TYPE_L
    else:
        return 1112 
    if region_type == REGION_TYPE_L:
        # slc region
        lpage = wl_base[region] + ((page - region_base[region]))
    elif region_type == REGION_TYPE_LU:
        # mlc region
        lpage = wl_base[region] + ((page - region_base[region])// mlc_sharepage)
    elif region_type == REGION_TYPE_LUX:
        # tlc region
        lpage = wl_base[region] + ((page - region_base[region]) // tlc_sharepage)
    else:
        lpage = 1112
    return lpage
def update_device_desc() -> None:
    device_descriptor = ExecuteCMD.ReadDescriptor()
    device_descriptor.assign(idn=api.DescriptorIDN.DEVICE)
    index = ExecuteCMD.enqueue(device_descriptor)
    ExecuteCMD.send(clear_on_success=False)
    api.update_descriptor(idn=api.DescriptorIDN.DEVICE, index=0, response=cast(api.QueryResponse, ExecuteCMD.read_response(index)))
    ExecuteCMD.clear()