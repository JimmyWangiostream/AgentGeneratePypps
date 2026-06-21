from Script import api
from Script.lib import sdk_lib as lib
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_logger import logger
from Script import project_api
from Script.api.ufs_api.defines.constant_define import *
from Script.project_api.set_get_temperature.structs import GetNandTemperature, SetNandTemperature
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig, get_flash_setting
import copy
import time
from Script.api import shared
from typing import List, cast
from Script.api.ufs_api.vendor_cmd.structs import PCA
_sdk = api.shared.sdk
import random
def pattern_get_device_health_descriptor() ->  bytearray:
    idn = api.DescriptorIDN.DEVICE_HEALTH
    index = 0x00
    selector = 0x00
    cmd = ExecuteCMD.ReadDescriptor()
    cmd.assign(idn, index, selector)
    cmd_index = ExecuteCMD.enqueue(cmd)

    ExecuteCMD.send(clear_on_success=False)
    resp = cast(api.QueryResponse, ExecuteCMD.read_response(cmd_index))
    ExecuteCMD.clear()
    return resp.data

def config_lun() -> None:
    total_au = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
    bootlun_au = 0
    for unit_idx in range(32):
        logger.info(f"Get Unit Descriptor [{unit_idx}]")
        unit_desc =  api.get_unit_descriptor(unit_idx)
        if unit_desc.b4_boot_lun_id == 1 or unit_desc.b4_boot_lun_id == 2:
            logger.info(f'lun = {unit_idx}, bootlun au = {unit_desc.q11_logical_block_count}')
            if unit_desc.b8_memory_type == api.MemoryType.ENHANCED_1:
                bootlun_au = 3 * (unit_desc.q11_logical_block_count * 4096) // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size * 512)
            else:
                bootlun_au = (unit_desc.q11_logical_block_count * 4096) // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size * 512)

    config_descs = api.get_config_descriptors(print=True)
    for table in range(4):
        for unit in range(8):
            config_descs[table].header.b2_conf_desc_continue = 1
            config_descs[table].units[unit].b0_lu_enable = 0
            config_descs[table].units[unit].b1_boot_lun_id = 0
            config_descs[table].units[unit].l4_num_alloc_units = 0
            config_descs[table].units[unit].b9_logical_block_size = 0xc
            config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
            if (table * 8 + unit) == 0:
                config_descs[table].units[unit].b0_lu_enable = 1
                config_descs[table].units[unit].b3_memory_type = api.MemoryType.NORMAL
                config_descs[table].units[unit].l4_num_alloc_units = (total_au - 2*bootlun_au) // 2
            elif (table * 8 + unit) == 1:
                config_descs[table].units[unit].b0_lu_enable = 1
                config_descs[table].units[unit].b1_boot_lun_id = 1
                config_descs[table].units[unit].l4_num_alloc_units = bootlun_au
            elif (table * 8 + unit) == 2:
                config_descs[table].units[unit].b0_lu_enable = 1
                config_descs[table].units[unit].b1_boot_lun_id = 2
                config_descs[table].units[unit].l4_num_alloc_units = bootlun_au
            elif (table * 8 + unit) == 3:
                config_descs[table].units[unit].b0_lu_enable = 1
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                config_descs[table].units[unit].l4_num_alloc_units = (total_au - 2*bootlun_au) // 2
    
    config_descs[3].header.b2_conf_desc_continue = 0
    config_descs[0].header.b7_secure_removal_type = 0
    config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.ENABLE
    config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
    config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0
    for i in range(4):
        api.push_write_config(config_descs[i], index=i)
    ExecuteCMD.send()
    ExecuteCMD.clear()

    unit_desc_idxes:List[int] = []
    _param = api.shared.param
    for lun in range(0, _param.gMaxNumberLU):
        unit_descriptor = ExecuteCMD.ReadDescriptor()
        unit_descriptor.assign(api.DescriptorIDN.UNIT, lun)
        unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

    ExecuteCMD.send(clear_on_success=False)
    for index in unit_desc_idxes:
        api.update_descriptor(api.DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
    ExecuteCMD.clear()

    #test unit ready all enable lun
    for lun in range(_param.gMaxNumberLU):
        if _param.gUnit[lun].b3_lu_enable:
            test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
            test_unit_ready.set_option(lun)
            ExecuteCMD.enqueue(test_unit_ready)
    ExecuteCMD.send(clear_on_success=False)
    ExecuteCMD.clear()
    return
def check_timeout(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False
def set_ec(total_vb_cnt:int, set_ec:bytearray) -> None:

    api.ufs_api.vendor_cmd.access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=api.DATA_SIZE_16K_BYTE, cmd_index=api.VendorCmd.GET_FW_GEOMETRY, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = api.VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b6_cmd2 = 4
    vuc.data = set_ec
    vuc.enqueue()
    ExecuteCMD.send()
def get_PCA_and_print(lun: int, lba: int, rpmb_region: int = 0) -> PCA:
        _pca = api.lba_to_pba(lun, lba, rpmb_region)
        pca = PCA()
        pca.from_bytes(bytearray(_pca.payload))
        logger.info(f'Lun{lun}, LBA = {lba}: Block = {(pca.b11_block_h<<8) | (pca.b10_block_l)}, mode = {pca.b4_mode}, CE = {pca.b5_ce}, Plane = {pca.b6_plane}, fPage = {pca.l12_fpage}(pageline = {pca.l12_fpage>>5}), lmu = {pca.b20_lmu}, format = {pca.b7_format}')
        return pca
def inject_UECC(pca:PCA) -> None:
    logger.info(f'Inject UECC: Block = {(pca.b11_block_h<<8) | (pca.b10_block_l)}, mode = {pca.b4_mode}, CE = {pca.b5_ce}, Plane = {pca.b6_plane}, fPage = {pca.l12_fpage}(pageline = {pca.l12_fpage>>5}), lmu = {pca.b20_lmu}')
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
    # USE_MICRON_VU = True
    # if USE_MICRON_VU:
    #     block = (pca.b11_block_h<<8) | (pca.b10_block_l)
    #     ce = pca.b5_ce
    #     plane = pca.b6_plane
    #     if pca.b4_mode == 0: #for system and hidden
    #         pca.b4_mode = 1
    #     mode = pca.b4_mode
    #     if pca.b4_mode==1:
    #         page = pca.l12_fpage>>5
    #         dire_read_payload = bytearray(DATA_SIZE_16K_BYTE)
    #     else:
    #         page = (pca.l12_fpage>>5) * 3
    #         dire_read_payload = bytearray(DATA_SIZE_16K_BYTE*3)
    #     for i in range(len(dire_read_payload)):
    #         dire_read_payload[i] = 0xAA
    #     _ = project_api.issue_C060_to_write_raw_data(Ce=ce, Plane=plane, Block=block, Page=page, SLC_Enable=int(mode==1),Ecc_Enable=1, datapayload=dire_read_payload)
    # else:
    #     dire_read_payload = bytearray(DATA_SIZE_16K_BYTE)
    #     for i in range(len(dire_read_payload)):
    #         dire_read_payload[i] = 0xAA
    #     api.direct_write(pca = pca, block_count=4, data_buffer=dire_read_payload)
    # return
def Tnand_in_T1_T2_range(ce:int, T1:int, T2:int)->bool:
    temp_gap = 37
    rsp , GetNandTemperature = project_api.issue_4021_get_nand_temperature()
    if  (GetNandTemperature.temperature_of_die_0.value - temp_gap) < T1 or (GetNandTemperature.temperature_of_die_0.value - temp_gap) > T2:
        return False
    if ce >= 2:
        if  (GetNandTemperature.temperature_of_die_1.value - temp_gap) < T1 or (GetNandTemperature.temperature_of_die_1.value - temp_gap) > T2:
            return False
    if ce >= 4:
        if  (GetNandTemperature.temperature_of_die_2.value - temp_gap) < T1 or (GetNandTemperature.temperature_of_die_2.value - temp_gap) > T2:
            return False
        if  (GetNandTemperature.temperature_of_die_3.value - temp_gap) < T1 or (GetNandTemperature.temperature_of_die_3.value - temp_gap) > T2:
            return False
    return True
def get_xtemp_parameter() -> tuple[int,int,int,int,int]:
    rsp, mconfig = project_api.get_mConfig_data()
    XTEMP_ENABLE_PEC = mconfig.XTEMP_ENABLE_PEC.value
    XTEMP_TEMP_BUFFER = mconfig.XTEMP_TEMP_BUFFER.value
    XTEMP_TIME_DETECTION_VALUE = mconfig.XTEMP_TIME_DETECTION_VALUE.value
    XTEMP_REFRESH_T1 = mconfig.XTEMP_Refresh_T1.value if mconfig.XTEMP_Refresh_T1.value <= 127 else mconfig.XTEMP_Refresh_T1.value - 256
    XTEMP_REFRESH_T2 = mconfig.XTEMP_Refresh_T2.value if mconfig.XTEMP_Refresh_T2.value <= 127 else mconfig.XTEMP_Refresh_T2.value - 256
    logger.info(f'Xtemp enable EPC = {XTEMP_ENABLE_PEC}, temp buffer = {XTEMP_TEMP_BUFFER}, time detection = {XTEMP_TIME_DETECTION_VALUE}')
    logger.info(f'Xtemp refresh T1 = {XTEMP_REFRESH_T1}, Xtemp refresh T2 = {XTEMP_REFRESH_T2}')

    if mconfig.XTEMP_ENABLE_PEC.value != 10:
        mconfig.XTEMP_ENABLE_PEC.value = 10
        mconfig.payload[0:7] = "MCONFIG".encode("ascii")
        project_api.set_mConfig_data(mConfig=mconfig)

        rsp, mconfig = project_api.get_mConfig_data()
        XTEMP_ENABLE_PEC = mconfig.XTEMP_ENABLE_PEC.value
        XTEMP_TEMP_BUFFER = mconfig.XTEMP_TEMP_BUFFER.value
        XTEMP_TIME_DETECTION_VALUE = mconfig.XTEMP_TIME_DETECTION_VALUE.value
        XTEMP_REFRESH_T1 = mconfig.XTEMP_Refresh_T1.value if mconfig.XTEMP_Refresh_T1.value <= 127 else mconfig.XTEMP_Refresh_T1.value - 256
        XTEMP_REFRESH_T2 = mconfig.XTEMP_Refresh_T2.value if mconfig.XTEMP_Refresh_T2.value <= 127 else mconfig.XTEMP_Refresh_T2.value - 256
        logger.info(f'Xtemp enable EPC = {XTEMP_ENABLE_PEC}, temp buffer = {XTEMP_TEMP_BUFFER}, time detection = {XTEMP_TIME_DETECTION_VALUE}')
        logger.info(f'Xtemp refresh T1 = {XTEMP_REFRESH_T1}, Xtemp refresh T2 = {XTEMP_REFRESH_T2}')
    return XTEMP_ENABLE_PEC, XTEMP_TEMP_BUFFER, XTEMP_TIME_DETECTION_VALUE, XTEMP_REFRESH_T1, XTEMP_REFRESH_T2
def get_T1_T2() -> tuple[int,int,int, int]:
    rsp, mconfig = project_api.get_mConfig_data()
    mConfig_in_vu_bkup = copy.deepcopy(mconfig)
    XTEMP_ENABLE_PEC = mconfig.XTEMP_ENABLE_PEC.value
    XTEMP_TEMP_BUFFER = mconfig.XTEMP_TEMP_BUFFER.value
    XTEMP_TIME_DETECTION_VALUE = mconfig.XTEMP_TIME_DETECTION_VALUE.value
    XTEMP_REFRESH_T1 = mconfig.XTEMP_Refresh_T1.value if mconfig.XTEMP_Refresh_T1.value <= 127 else mconfig.XTEMP_Refresh_T1.value - 256
    XTEMP_REFRESH_T2 = mconfig.XTEMP_Refresh_T2.value if mconfig.XTEMP_Refresh_T2.value <= 127 else mconfig.XTEMP_Refresh_T2.value - 256
    logger.info(f'Xtemp enable EPC = {XTEMP_ENABLE_PEC}, temp buffer = {XTEMP_TEMP_BUFFER}, time detection = {XTEMP_TIME_DETECTION_VALUE}')
    logger.info(f'Xtemp refresh T1 = {XTEMP_REFRESH_T1}, Xtemp refresh T2 = {XTEMP_REFRESH_T2}')

    if mconfig.XTEMP_ENABLE_PEC.value != 10:
        mconfig.XTEMP_ENABLE_PEC.value = 10
        mconfig.payload[0:7] = "MCONFIG".encode("ascii")
        project_api.set_mConfig_data(mConfig=mconfig)

        rsp, mconfig = project_api.get_mConfig_data()
        XTEMP_ENABLE_PEC = mconfig.XTEMP_ENABLE_PEC.value
        XTEMP_TEMP_BUFFER = mconfig.XTEMP_TEMP_BUFFER.value
        XTEMP_TIME_DETECTION_VALUE = mconfig.XTEMP_TIME_DETECTION_VALUE.value
        XTEMP_REFRESH_T1 = mconfig.XTEMP_Refresh_T1.value if mconfig.XTEMP_Refresh_T1.value <= 127 else mconfig.XTEMP_Refresh_T1.value - 256
        XTEMP_REFRESH_T2 = mconfig.XTEMP_Refresh_T2.value if mconfig.XTEMP_Refresh_T2.value <= 127 else mconfig.XTEMP_Refresh_T2.value - 256
        logger.info(f'Xtemp enable EPC = {XTEMP_ENABLE_PEC}, temp buffer = {XTEMP_TEMP_BUFFER}, time detection = {XTEMP_TIME_DETECTION_VALUE}')
        logger.info(f'Xtemp refresh T1 = {XTEMP_REFRESH_T1}, Xtemp refresh T2 = {XTEMP_REFRESH_T2}')
    return XTEMP_REFRESH_T1, XTEMP_REFRESH_T2, XTEMP_TIME_DETECTION_VALUE, XTEMP_ENABLE_PEC

def set_nand_temp(ce:int, set_temp:int) -> None:
    temp_set = set_temp
    if temp_set < 0:
        temp_set = 65536 + temp_set
    set_nand_temp = project_api.SetNandTemperature()
    set_nand_temp.bEnableSetVuTemp.value = 1
    set_nand_temp.NAND_TEMPERATURE_DIE_0.value = temp_set
    if ce >= 2:
        set_nand_temp.NAND_TEMPERATURE_DIE_1.value = temp_set
    if ce >= 4:
        set_nand_temp.NAND_TEMPERATURE_DIE_2.value = temp_set
        set_nand_temp.NAND_TEMPERATURE_DIE_3.value = temp_set
    set_nand_temp.Use_Delayed_fake_tmeperatures.value = 0
    set_nand_temp.UC_TERMAL_SENSOR_1.value = temp_set
    rsp = project_api.issue_D08A_set_vu_temperature(set_nand_temp)
    # self.get_nand_temp()


def write_data(lun:int, start_lba:int, len:int, total_len:int, random_chunk:bool=False) -> None:
    while total_len > 0:
        if random_chunk == True:
            len = random.randint(BLOCK4K_SIZE_4K_BYTE, WRITE_10_MAX_BLOCK_LEN)
        len = min(total_len, len)
        write10 = ExecuteCMD.Write10()
        logger.info(f'start lba = {start_lba}, len = {len}')
        write10.assign(lun=lun, lba=start_lba, length=len, fua=1)
        ExecuteCMD.enqueue(write10)
        start_lba += len
        total_len -= len
    ExecuteCMD.send(clear_on_success=False)
    ExecuteCMD.clear()
