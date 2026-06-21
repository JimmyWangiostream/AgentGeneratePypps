import inspect
import struct
import Script.api.shared as shared
import Script.api.cmd_seq as ExecuteCMD

from Script.api.ufs_api import dumpfile, VendorCmd, PCA
from Script.lib.sdk_lib.user.constant import DATA_SIZE_4K_BYTE, DATA_SIZE_8K_BYTE

from Script.project_api.structs import micron_vendor_cmd
from Script.lib.sdk_lib.user.exception import DLL_CRC32_COMPARE_FAIL, DLL_PATTERN_2_ERROR, DLL_RESPONSE_ERROR
from Script.api.exception import *
from Script.api.ufs_api.defines import UPIUResponse
from Script.api.cmd_seq.response import CommandResponse, get_query_response_byte_str, get_cmd_response_byte_str, get_scsi_status_str, get_sense_key_str, get_asc_ascq_description
from Script.pattern.pattern_logger import logger
from typing import Any, Optional

_log = shared.logger
_param = shared.param

def print_array_tohex(databuff : bytearray) -> None:
    len = databuff.__len__()
    for index in range(0,len,16):
        if(index +16 < len):
            tmpdata = databuff[index: index+16]
            print(tmpdata.hex(' ',1) )
        else:            
            tmpdata = databuff[index: len]            
            print(tmpdata.hex(' ',1) )
    return

def send_data_in_vcmd(micron_vendor_cmd:micron_vendor_cmd, specific_read_buffer_len:int = 0, keep_error:bool = False) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    logger.info(f"=================== send VU {int.from_bytes(micron_vendor_cmd.payload[0:2], 'little'):X} ===================", extra_dump=True)
    print_object_info_ai(micron_vendor_cmd, extra_dump=True)
    write_buffer = ExecuteCMD.WriteBuffer()
    enablelun = 0
    for lunidx in range(0, _param.gMaxNumberLU):
        if _param.gUnit[lunidx].b3_lu_enable:
            enablelun = lunidx
            break
    write_buffer.assign(lun=enablelun, mode=0xE1, buffer_id=0, buffer_offset=0, length=micron_vendor_cmd.parameter_length, vendor=True)
    write_buffer.set_option(wait_queue_empty=True)
    write_buffer.data = bytearray(micron_vendor_cmd.payload)
    cmd_queue = []
    cmd_queue.append(ExecuteCMD.enqueue(write_buffer))    

    read_buffer = ExecuteCMD.ReadBuffer()
    read_buffer_len = specific_read_buffer_len if specific_read_buffer_len else micron_vendor_cmd.w2_transfer_length.value

    read_buffer.assign(lun=enablelun, mode=0xC1, buffer_id=0, buffer_offset=0, length=read_buffer_len, vendor=True)
    read_buffer.set_option(wait_queue_empty=True)
    cmd_queue.append(ExecuteCMD.enqueue(read_buffer))
    try:
        ExecuteCMD.send(clear_on_success=False)
        response = ExecuteCMD.read_response(cmd_queue[-1])
    except DLL_RESPONSE_ERROR:
        if keep_error:
            for cmd_index in cmd_queue:
                response = ExecuteCMD.read_response(cmd_index)
                _log.warning(f"lun = {response.upiu.b2_lun}, task_tag = {hex(response.upiu.b3_tasktag)},  response = {get_cmd_response_byte_str(response)}, status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}")
                if response.upiu.b6_response != UPIUResponse.TARGET_SUCCESS:
                    break
        else:
            raise DLL_RESPONSE_ERROR
    ExecuteCMD.clear()
    logger.info(f"=================== get DIN ===================", extra_dump=True)
    logger.print_buffer(response.data[:read_buffer_len], extra_dump=True)
    return response, response.data

def push_data_in_vcmd(micron_vendor_cmd:micron_vendor_cmd, specific_read_buffer_len:int = 0, keep_error:bool = False) -> int:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    logger.info(f"=================== push VU {int.from_bytes(micron_vendor_cmd.payload[0:2], 'little'):X} ===================", extra_dump=True)
    print_object_info_ai(micron_vendor_cmd, extra_dump=True)
    write_buffer = ExecuteCMD.WriteBuffer()
    enablelun = 0
    for lunidx in range(0, _param.gMaxNumberLU):
        if _param.gUnit[lunidx].b3_lu_enable:
            enablelun = lunidx
            break
    write_buffer.assign(lun=0, mode=0xE1, buffer_id=0, buffer_offset=0, length=micron_vendor_cmd.parameter_length, vendor=True)
    write_buffer.set_option(wait_queue_empty=True)
    write_buffer.data = bytearray(micron_vendor_cmd.payload)
    ExecuteCMD.enqueue(write_buffer)

    read_buffer = ExecuteCMD.ReadBuffer()
    read_buffer_len = specific_read_buffer_len if specific_read_buffer_len else micron_vendor_cmd.w2_transfer_length.value

    read_buffer.assign(lun=enablelun, mode=0xC1, buffer_id=0, buffer_offset=0, length=read_buffer_len, vendor=True)
    read_buffer.set_option(wait_queue_empty=True)
    cmd_idx = ExecuteCMD.enqueue(read_buffer)
    return cmd_idx

def send_data_out_vcmd(micron_vendor_cmd:micron_vendor_cmd, data_payload:bytearray, specific_read_buffer_len:int = 0, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    logger.info(f"=================== send VU {int.from_bytes(micron_vendor_cmd.payload[0:2], 'little'):X} ===================", extra_dump=True)
    print_object_info_ai(micron_vendor_cmd, extra_dump=True)
    write_buffer = ExecuteCMD.WriteBuffer()
    enablelun = 0
    for lunidx in range(0, _param.gMaxNumberLU):
        if _param.gUnit[lunidx].b3_lu_enable:
            enablelun = lunidx
    write_buffer.assign(lun=enablelun, mode=0xE1, buffer_id=0, buffer_offset=0, length=micron_vendor_cmd.parameter_length, vendor=True)
    write_buffer.set_option(wait_queue_empty=True)
    write_buffer.data = bytearray(micron_vendor_cmd.payload)
    cmd_queue = []
    cmd_queue.append(ExecuteCMD.enqueue(write_buffer))
    write_buffer = ExecuteCMD.WriteBuffer()
    write_buffer_len = specific_read_buffer_len if specific_read_buffer_len else micron_vendor_cmd.w2_transfer_length.value
    write_buffer.assign(lun=enablelun, mode=0xC1, buffer_id=0, buffer_offset=0, length=write_buffer_len, vendor=True)
    write_buffer.set_option(wait_queue_empty=True)
    write_buffer.data = data_payload
    logger.info(f"=================== send DOUT ===================", extra_dump=True)
    logger.print_buffer(data_payload[:write_buffer_len])
    cmd_queue.append(ExecuteCMD.enqueue(write_buffer))
    try:
        ExecuteCMD.send(clear_on_success=False)
        response = ExecuteCMD.read_response(cmd_queue[-1])
    except DLL_RESPONSE_ERROR:
        if keep_error:
            for cmd_index in cmd_queue:
                response = ExecuteCMD.read_response(cmd_index)
                _log.warning(f"lun = {response.upiu.b2_lun}, task_tag = {hex(response.upiu.b3_tasktag)},  response = {get_cmd_response_byte_str(response)}, status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}")
                if response.upiu.b6_response != UPIUResponse.TARGET_SUCCESS:
                    break
        else:
            raise DLL_RESPONSE_ERROR
    ExecuteCMD.clear()
    return response

def send_no_data_vcmd(micron_vendor_cmd:micron_vendor_cmd, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    logger.info(f"=================== send VU {int.from_bytes(micron_vendor_cmd.payload[0:2], 'little'):X} ===================", extra_dump=True)
    print_object_info_ai(micron_vendor_cmd, extra_dump=True)
    write_buffer = ExecuteCMD.WriteBuffer()
    enablelun = 0
    _param = shared.param
    for lunidx in range(0, _param.gMaxNumberLU):
        if _param.gUnit[lunidx].b3_lu_enable:
            enablelun = lunidx
    write_buffer.assign(lun=enablelun, mode=0xE1, buffer_id=0, buffer_offset=0, length=micron_vendor_cmd.parameter_length, vendor=True)
    write_buffer.set_option(wait_queue_empty=True)
    write_buffer.data = bytearray(micron_vendor_cmd.payload)
    cmd_index = ExecuteCMD.enqueue(write_buffer)
    try:
        ExecuteCMD.send(clear_on_success=False)
        response = ExecuteCMD.read_response(cmd_index)
    except DLL_RESPONSE_ERROR:
        if keep_error:
            response = ExecuteCMD.read_response(cmd_index)
            _log.warning(f"lun = {response.upiu.b2_lun}, task_tag = {hex(response.upiu.b3_tasktag)},  response = {get_cmd_response_byte_str(response)}, status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}")
        else:
            raise DLL_RESPONSE_ERROR
    ExecuteCMD.clear()
    return response  
def page_to_pageOrder(page:int)-> int:
    wl_base = [0, 540, 556, 1108]
    region_base = [0, 1620, 1652, 3308]
    REGION_TYPE_L   = 0
    REGION_TYPE_LU  = 1
    REGION_TYPE_LUX = 2
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
        lpage = wl_base[region] + (page - region_base[region])
    elif region_type == REGION_TYPE_LU:
        # mlc region
        lpage = wl_base[region] + (page - region_base[region])
    elif region_type == REGION_TYPE_LUX:
        # tlc region
        lpage = wl_base[region] + (page - region_base[region])
    else:
        lpage = 1112
    return lpage

def print_object_info_ai(object: Any, extra_dump:bool = False) -> None:
    logger.info(f'================= [{object.__class__.__name__}]=================', extra_dump=extra_dump)
    fields = [
        (name, field) for name, field in object.__dict__.items()
        if hasattr(field, "start_offset") and hasattr(field, "end_offset") and hasattr(field, "value")
    ]
    from collections import defaultdict
    offset_groups = defaultdict(list)
    for name, field in fields:
        offset_groups[field.start_offset].append((name, field))
    filtered = []
    for offset, items in offset_groups.items():
        if len(items) > 1:
            items = [(n, f) for n, f in items if n != "d12_reserved"]
        filtered.extend(items)
    filtered.sort(key=lambda kv: kv[1].start_offset)
    for name, field in filtered:
        logger.info(
            f'Byte[{field.start_offset}:{field.end_offset}]: {name} = {field.value} (0x{field.value:X})',
            extra_dump=extra_dump
        )

def get_physical_layout(pca:Optional[PCA] = None, pageline:Optional[int] = None, block_type:str = "TLC") -> tuple[int, str, int, int, int, int, int]:
    phy_region_max_page = [1620, 1652, 3308, 3312]
    phy_region_max_WL = [135, 139, 277, 278]
    loc_region_max_page = [540, 556, 1108, 1112]
    if pca:
        local_page = pca.l12_fpage>>5
        if pca.b4_mode == 2:
            lmu = pca.b20_lmu
            if local_page < loc_region_max_page[0]:
                pageline = local_page * 3 + lmu
            elif local_page < loc_region_max_page[1]:
                pageline = (local_page - loc_region_max_page[0]) * 2 + lmu + phy_region_max_page[0]
            elif local_page < loc_region_max_page[2]:
                pageline = (local_page - loc_region_max_page[1]) * 3 + lmu + phy_region_max_page[1]
            elif local_page < loc_region_max_page[3]:
                pageline = (local_page - loc_region_max_page[2]) * 1 + lmu + phy_region_max_page[2]
        else:
            pageline = local_page
            block_type = "SLC"
    if pageline == None:
        raise PATTERN_ASSERT_UNEXPECTED_CONDITION
    if block_type == "TLC":
        if pageline < phy_region_max_page[0]:
            pageline_per_WL = 12
            phy_WL = pageline // pageline_per_WL
            SubBlock = pageline % pageline_per_WL // (pageline_per_WL//4)
            WL_type = "TLC"
        elif pageline < phy_region_max_page[1]:
            pageline_per_WL = 8
            phy_WL = (pageline - phy_region_max_page[0]) // pageline_per_WL + phy_region_max_WL[0]
            SubBlock = (pageline - phy_region_max_page[0]) % pageline_per_WL // (pageline_per_WL//4)
            WL_type = "MLC"
        elif pageline < phy_region_max_page[2]:
            pageline_per_WL = 12
            phy_WL = (pageline - phy_region_max_page[1]) // pageline_per_WL + phy_region_max_WL[1]
            SubBlock = (pageline - phy_region_max_page[1]) % pageline_per_WL // (pageline_per_WL//4)
            WL_type = "TLC"
        elif pageline < phy_region_max_page[3]:
            pageline_per_WL = 4
            phy_WL = (pageline - phy_region_max_page[2]) // pageline_per_WL + phy_region_max_WL[2]
            SubBlock = (pageline - phy_region_max_page[2]) % pageline_per_WL // (pageline_per_WL//4)
            WL_type = "SLC"
        else:
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        FlushGroup = pageline // 6
        TwoWLGroup = phy_WL // 2
        RainGoup = pageline % 24
    else:
        if pageline >= 1104:
            raise PATTERN_ASSERT_UNEXPECTED_CONDITION
        WL_type = "SLC"
        phy_WL = pageline // 4
        SubBlock = pageline % 4
        FlushGroup = TwoWLGroup =  pageline // 8
        RainGoup = pageline % 8
    return pageline, WL_type, phy_WL, SubBlock, FlushGroup, TwoWLGroup, RainGoup