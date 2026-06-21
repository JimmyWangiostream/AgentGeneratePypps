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
import pandas as pd
from pathlib import Path
import math
from typing import Any

def xlsx_data_process(xlsx_path:Path, OTP_value:int) -> tuple[int, Dict[int, Dict[str, str]]]:
    df_raw = pd.read_excel(
        xlsx_path,
        header=1,
        engine="openpyxl"
    )
    df = df_raw.fillna("")
    index = 0
    for col in df.columns:
        if pd.api.types.is_numeric_dtype(df_raw[col]):
            df[col] = df[col].apply(
                lambda v: "" if v == "" else int(v)
            )
        else:
            df[col] = df[col].astype(str).str.strip()
    
    try:
        mask = df["Parameter Name"] == "OTP value"
        row_idx = df.index[mask][0]
        row_series = df.loc[row_idx]
        target_cols = str(row_series[row_series == OTP_value].index.tolist()[0])
        index = list(row_series).index(OTP_value)+1 - len(row_series) + 4
        pass
    except:
        raise ValueError(f"Can't find 'OTP value' which is {OTP_value} in xlsx")
            
    keep_cols = ["Parameter Name"]
    keep_cols += [
        c for c in df.columns
        if ("Size" in c) or ("Start Offset" in c) or ("End offset" in c)
    ]
    if target_cols not in keep_cols:
        keep_cols.append(target_cols)
    df = df[keep_cols]
    df = df.rename(columns={target_cols: "Value"})
    
    df_str = df.astype(str)
    result_dict: Dict[int, Dict[str, str]] = cast(
        Dict[int, Dict[str, str]],
        df_str.to_dict(orient="index")
    )
    return index, result_dict


def load_mConfig_pConfig_from_xlsx(OTP_value:int) -> tuple[int, Dict[int, Dict[str, str]], Dict[int, Dict[str, str]]]:
    dir = Path(__file__).parent
    mConfig_xlsx_path = dir / "Cygnus Auto B68S mConfig rev0.4.xlsx"
    pConfig_xlsx_path = dir / "Cygnus Auto B68S pConfig rev0.4_external.xlsx"
    
    index, mConfig_dict = xlsx_data_process(mConfig_xlsx_path, OTP_value)
    _, pConfig_dict = xlsx_data_process(pConfig_xlsx_path, OTP_value)
    
    return index, mConfig_dict, pConfig_dict

def compare_payload(mConfig_pConfig_dict:Dict[int, Dict[str, str]], payload:bytearray) -> None:
    remain_bit = 0
    total_bit = 0
    last_start = 0xFFFFFFFF
    otp_value = 0
    for idx, item in mConfig_pConfig_dict.items():
        if item["Parameter Name"] == "OTP value":
            otp_value = int(item["Value"])
            break
    for idx, item in mConfig_pConfig_dict.items():
        if not item["Value"]:
            continue
        try:
            name = item["Parameter Name"]
            size = int(item["Size (bit)"])
            start = int(item["Start Offset (dec)"])
            end = int(item["End offset (dec)"])
            value = int(item["Value"])
            vu_value = int.from_bytes(payload[start:end+1], 'little')
            if start != last_start:
                remain_bit = 0
                total_bit = 0
            if size%8:
                if total_bit == 0:
                    total_bit = (end-start+1)*8
                    remain_bit = total_bit
                vu_value = vu_value >> (total_bit-remain_bit)
                remain_bit -= size
            value_unsigned =  value & ((1 << size) - 1)
            vu_value =  vu_value & ((1 << size) - 1)
            last_start = start
            if vu_value != value_unsigned:
                if name == "Name 4" and vu_value == otp_value:
                    continue
                logger.error_lb(f'check data in mConfig/pConfig')
                logger.error_fp(f'ERROR {name}, Value = {value}, payload[{start}:{end}] = {vu_value} (0x{vu_value:X})')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        except:
            pass
    pass

def get_m_p_config_in_FW_HW_BIN(FW_HW_BIN : bytearray, index_offset:int) -> tuple[project_api.mConfig, project_api.pConfig]:
    mConfig_in_FW_HW_BIN_offset = 0x5000 + index_offset
    pConfig_in_FW_HW_BIN_offset = 0x5400 + index_offset
    mConfig_size = 437
    pConfig_size = 1612
    mConfig_in_bin = project_api.mConfig(FW_HW_BIN, mConfig_in_FW_HW_BIN_offset, mConfig_in_FW_HW_BIN_offset + mConfig_size-1)
    pConfig_in_bin = project_api.pConfig(FW_HW_BIN, pConfig_in_FW_HW_BIN_offset, pConfig_in_FW_HW_BIN_offset + pConfig_size-1)
    return mConfig_in_bin, pConfig_in_bin

def get_PRL_in_FW_HW_BIN(FW_HW_BIN : bytearray) -> int:
    PRL_offset = 0x100
    return int.from_bytes(FW_HW_BIN[PRL_offset: PRL_offset+2], "little")

def compare_mConfig_data(get_mConfig:project_api.mConfig, set_mConfig:project_api.mConfig) -> None:
    signature = bytearray(set_mConfig.payload[0:7]).decode('ascii')
    if signature != "MCONFIG":
        dumpfile('set_mConfig_data.bin', set_mConfig.payload)
        dumpfile('get_mConfig_data.bin', get_mConfig.payload)
        logger.error_lb(f'check mConfig after setting')
        logger.error_fp(f'current mConfig signature = {signature}, not match "MCONFIG", Pattern result: Fail')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    set_mConfig_copy = copy.deepcopy(set_mConfig)
    get_mConfig_copy = copy.deepcopy(get_mConfig)
    set_mConfig_copy.payload[3] = 0
    get_mConfig_copy.payload[3] = 0
    if set_mConfig_copy.payload != get_mConfig_copy.payload:
        dumpfile('set_mConfig_data.bin', set_mConfig.payload)
        dumpfile('get_mConfig_data.bin', get_mConfig.payload)
        logger.error_lb(f'check mConfig after setting')
        logger.error_fp(f'data conpare fail, please check dump file')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    pass

def compare_pConfig_data(get_pConfig:project_api.pConfig, set_pConfig:project_api.pConfig) -> None:
    signature = bytearray(set_pConfig.payload[0:7]).decode('ascii')
    if signature != "PCONFIG":
        dumpfile('set_pConfig_data.bin', set_pConfig.payload)
        dumpfile('get_pConfig_data.bin', get_pConfig.payload)
        logger.error_lb(f'check pConfig after setting')
        logger.error_fp(f'current pConfig signature = {signature}, not match "PCONFIG", Pattern result: Fail')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    set_pConfig_copy = copy.deepcopy(set_pConfig)
    get_pConfig_copy = copy.deepcopy(get_pConfig)
    set_pConfig_copy.payload[3] = 0
    get_pConfig_copy.payload[3] = 0
    if set_pConfig_copy.payload != get_pConfig_copy.payload:
        dumpfile('set_pConfig_data.bin', set_pConfig.payload)
        dumpfile('get_pConfig_data.bin', get_pConfig.payload)
        logger.error_lb(f'check pConfig after setting')
        logger.error_fp(f'data conpare fail, please check dump file')
        raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    pass

def config_lun() -> tuple[int,int]:
    Total_AU_Count = shared.param.gGeometry.q4_total_raw_device_capacity // (shared.param.gGeometry.l13_segment_size * shared.param.gGeometry.b17_allocation_unit_size)
    config_descs = api.get_config_descriptors(print=False)
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
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                config_descs[table].units[unit].l4_num_alloc_units = min(shared.param.gGeometry.l44_enhanced1_max_n_alloc_u, Total_AU_Count//2)
            elif (table * 8 + unit) == 1:
                config_descs[0].units[unit].b0_lu_enable = 1
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[0].units[unit].b3_memory_type = api.MemoryType.NORMAL
                config_descs[0].units[unit].l4_num_alloc_units = Total_AU_Count//2
    
    config_descs[3].header.b2_conf_desc_continue = 0
    config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.ENABLE
    config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
    config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0
    for i in range(4):
        api.push_write_config(config_descs[i], index=i)
    ExecuteCMD.send()
    ExecuteCMD.clear()

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
    ExecuteCMD.send(clear_on_success=False)
    ExecuteCMD.clear()

    slc_lun = 0
    tlc_lun = 1
    return (slc_lun, tlc_lun)