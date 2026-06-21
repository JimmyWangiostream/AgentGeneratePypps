import copy
import inspect
import struct
import Script.api.shared as shared
import Script.api.cmd_seq as ExecuteCMD
from typing import Dict

from Script.api.ufs_api.vendor_cmd.debug_info import DebugInfo
from Script.api.ufs_api.vendor_cmd.structs import FlashSetting, SmartInfo8329Bics8, PCA, FwGeometry, EventInfo, OpenVBInfo, L2P_PCA, Descptor_Att_Flag
from Script.api.ufs_api.defines.enum_define import WriteBufferMode, ReadBufferMode, RPMBRegion, RPMBVendorType, VendorCmd, VendorCmdRuleCdb2, VendorCmdRuleCdb3, VENDOR_CMD_GC_THRESHOLD

from Script.api.util.functions import dumpfile
from Script.lib.sdk_lib.user.constant import DATA_SIZE_4K_BYTE, DATA_SIZE_8K_BYTE, DATA_SIZE_16K_BYTE, DATA_SIZE_32K_BYTE
from Script.lib.sdk_lib.user.exception import DLL_CRC32_COMPARE_FAIL, DLL_PATTERN_2_ERROR, DLL_RESPONSE_ERROR
from Script.api.ufs_api.defines import UPIUResponse, Vendor_CMD_Query_Func
from Script.api.cmd_seq.response import CommandResponse, get_query_response_byte_str, get_cmd_response_byte_str, get_scsi_status_str, get_sense_key_str, get_asc_ascq_description
from Script.pattern.pattern_logger import logger

_log = shared.logger

def access_vendor_mode() -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore

    vendor_keys = {
        'PHISON': [0x50486953, 0x4F6EF52A, 0x163BABC3, 0xE10973DB],
        'KIC': [0x5453424D, 0x5E7DB238, 0x2905ABC3, 0xF149D6B3],
    }
    vendors = list(vendor_keys)

    for i, vendor_name in enumerate(vendors):
        _log.debug("[VUC] Get Rand Num")
        vendor_key = vendor_keys[vendor_name]
        vuc_read_rand_num = ExecuteCMD.VendorCmdRead()
        vuc_read_rand_num.assign(length=0x1000, cmd_index=VendorCmd.GET_RAND_NUM, cmd_set_type=0x0E)
        vuc_read_rand_num.upiu.u16_cdb.b4_cmd0 = 0x50
        vuc_read_rand_num.upiu.u16_cdb.b5_cmd1 = 0x48
        vuc_read_rand_num.upiu.u16_cdb.b6_cmd2 = 0x53
        vuc_read_rand_num.upiu.u16_cdb.b7_cmd3 = 0x4C

        cmd_index = ExecuteCMD.enqueue(vuc_read_rand_num)
        ExecuteCMD.send(clear_on_success=False)
        response = ExecuteCMD.read_response(cmd_index)
        ExecuteCMD.clear()
        dumpfile("VUC_rand_num.bin", response.data)

        rand_0 = struct.unpack('>L', response.data[0x04:0x08])[0]
        rand_1 = struct.unpack('>L', response.data[0x10:0x14])[0]
        rand_2 = struct.unpack('>L', response.data[0x40:0x44])[0]
        rand_3 = struct.unpack('>L', response.data[0x100:0x104])[0]
        final_pwd_0, final_pwd_1 = _compute_pass_key(rand_0, rand_1, rand_2, rand_3, vendor_key)

        _log.debug(f"[VUC] Verify Key: {vendor_name}")
        vuc_verify_key = ExecuteCMD.VendorCmdNoWR()
        vuc_verify_key.assign(cmd_index=VendorCmd.VERIFY_KEY, cmd_set_type=0x0E)
        vuc_verify_key.upiu.u16_cdb.b4_cmd0 = 0x50
        vuc_verify_key.upiu.u16_cdb.b5_cmd1 = 0x48
        vuc_verify_key.upiu.u16_cdb.b6_cmd2 = 0x53
        vuc_verify_key.upiu.u16_cdb.b7_cmd3 = 0x4D
        vuc_verify_key.upiu.u16_cdb.l8_pw_h = final_pwd_0
        vuc_verify_key.upiu.u16_cdb.l12_pw_l = final_pwd_1

        sdk_exception = shared.lib.exception
        try:
            ExecuteCMD.enqueue(vuc_verify_key)
            ExecuteCMD.send()
        except sdk_exception.DLL_ERROR:
            if i == len(vendor_keys) - 1:
                _log.error('All vendor key response failed.')
                raise
            _log.warning(f"{vendor_name} key is invalid. Try another key.")
            ExecuteCMD.clear()
        else:
            ExecuteCMD.clear()
            return

def push_send_vu_parameter(parameter:bytearray) -> int:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    payload = bytearray(4096)
    payload[0:len(parameter)] = parameter
    write_buffer = ExecuteCMD.WriteBuffer()
    byte2_param = 0xE0 | WriteBufferMode.VENDOR_SPECIFIC
    write_buffer.assign(lun=0, mode=byte2_param, buffer_id=0, buffer_offset=0, length=DATA_SIZE_4K_BYTE, vendor=True)
    write_buffer.set_option(wait_queue_empty=True)
    write_buffer.data = payload
    cmd_index = ExecuteCMD.enqueue(write_buffer)
    return cmd_index  

def push_read_vu_data(data_length:int) -> int:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    read_buffer = ExecuteCMD.ReadBuffer()
    byte2_param = ReadBufferMode.VENDOR_SPECIFIC
    read_buffer.assign(lun=0, mode=byte2_param, buffer_id=0, buffer_offset=0, length=data_length, vendor=True)
    read_buffer.set_option(wait_queue_empty=True)
    cmd_index = ExecuteCMD.enqueue(read_buffer)
    return cmd_index


def _compute_pass_key(rand_0: int, rand_1: int, rand_2: int, rand_3: int, vendor_key: list[int]) -> tuple[int, int]:
    rand_nums = [rand_0, rand_1, rand_2, rand_3]
    pwds = []
    for i in range(4):
        pwd = rand_nums[i] ^ vendor_key[i]
        pwds.append(pwd)

    final_pwd_0 = pwds[0] ^ pwds[1]
    final_pwd_1 = pwds[2] ^ pwds[3]

    return final_pwd_0, final_pwd_1


def buffer_get_smart_info(access_vendor: bool = True) -> bytearray:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()

    write_buffer = ExecuteCMD.WriteBuffer()
    write_buffer.assign(lun=0, mode=0xE1, buffer_id=0, buffer_offset=0, length=4096, vendor=True)
    write_buffer.set_option(wait_queue_empty=True)
    write_buffer.data = bytearray([0xFF, 0x40, 0x10, 0x00])
    ExecuteCMD.enqueue(write_buffer)

    read_buffer = ExecuteCMD.ReadBuffer()
    read_buffer.assign(lun=0, mode=0xC1, buffer_id=0, buffer_offset=0, length=4096, vendor=True)
    read_buffer.set_option(wait_queue_empty=True)
    cmd_index = ExecuteCMD.enqueue(read_buffer)

    write_buffer = ExecuteCMD.WriteBuffer()
    write_buffer.assign(lun=0, mode=0xE1, buffer_id=0, buffer_offset=0, length=4096, vendor=True)
    write_buffer.set_option(wait_queue_empty=True)
    ExecuteCMD.enqueue(write_buffer)
    
    ExecuteCMD.send(clear_on_success=False)

    response = ExecuteCMD.read_response(cmd_index)
    buf = copy.copy(response.data)
    ExecuteCMD.clear()
    return buf


def buffer_factory_reset(access_vendor: bool = True) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    data_len = 44
    buffer_data = bytearray(data_len)
    buffer_data[0] = 0xB0   # Opcode
    buffer_data[1] = 0xD0   # Function

    cmd_w_buf = ExecuteCMD.WriteBuffer()
    cmd_w_buf.assign(lun=0, mode=0xE1, buffer_id=0, buffer_offset=0, length=data_len, vendor=True)
    cmd_w_buf.set_option(wait_queue_empty=True)
    cmd_w_buf.data = buffer_data
    ExecuteCMD.enqueue(cmd_w_buf)
    ExecuteCMD.send()


def buffer_clear_rpmb_key(rpmb_region: RPMBRegion = RPMBRegion.REGION_0, access_vendor: bool = True) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    data_len = 44
    _log.info("Flow-a = set 4-byte password")
    buffer_data = bytearray(data_len)
    buffer_data[0] = 0x77   # Opcode
    buffer_data[1] = 0xD0   # Function
    buffer_data[17:21] = bytearray([0x78, 0x56, 0x34, 0x12])

    write_buffer = ExecuteCMD.WriteBuffer()
    write_buffer.assign(lun=0, mode=0xE1, buffer_id=0, buffer_offset=0, length=data_len, vendor=True)
    write_buffer.set_option(wait_queue_empty=True)
    write_buffer.data = buffer_data
    ExecuteCMD.enqueue(write_buffer)
    ExecuteCMD.send()
    
    _log.info("Flow-b = clear rpmb key")
    buffer_data = bytearray(data_len)
    buffer_data[0] = 0x79   # Opcode
    buffer_data[1] = 0xD0   # Function
    buffer_data[16] = rpmb_region
    buffer_data[17:21] = bytearray([0x78, 0x56, 0x34, 0x12])

    write_buffer = ExecuteCMD.WriteBuffer()
    write_buffer.assign(lun=0, mode=0xE1, buffer_id=0, buffer_offset=0, length=data_len, vendor=True)
    write_buffer.set_option(wait_queue_empty=True)
    write_buffer.data = buffer_data
    ExecuteCMD.enqueue(write_buffer)
    ExecuteCMD.send()


def vuc_clear_rpmb_key(rpmb_region: RPMBRegion, access_vendor: bool = True) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    data_len = 0x1000
    data_out = bytearray(data_len)
    data_out[0] = 0x00
    data_out[1] = RPMBVendorType.RESET_RPMB_KEY_COUNTER
    data_out[6] = _get_rpmb_region_val(rpmb_region)

    vuc_clr_rpmb_key = ExecuteCMD.VendorCmdWrite()
    vuc_clr_rpmb_key.assign(length=data_len, cmd_index=VendorCmd.RPMB_KEY_CLEAR)
    vuc_clr_rpmb_key.data = data_out
    ExecuteCMD.enqueue(vuc_clr_rpmb_key)
    ExecuteCMD.send()

def vuc_set_writecounter(rpmb_region: RPMBRegion, write_counter: int, access_vendor: bool = True) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    data_len = 0x1000
    data_out = bytearray(data_len)
    data_out[0] = 0x00
    data_out[1] = RPMBVendorType.SET_RPMB_COUNTER
    data_out[2:6] = struct.pack(">I", write_counter)
    data_out[6] = _get_rpmb_region_val(rpmb_region)

    vuc_set_writecounter = ExecuteCMD.VendorCmdWrite()
    vuc_set_writecounter.assign(length=data_len, cmd_index=VendorCmd.RPMB_KEY_CLEAR)
    vuc_set_writecounter.data = data_out
    ExecuteCMD.enqueue(vuc_set_writecounter)
    ExecuteCMD.send()


def vuc_backup_desc_attr_flag(access_vendor: bool = True) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    # No need data out
    vuc_backup = ExecuteCMD.VendorCmdWrite()
    vuc_backup.assign(length=0x1000, cmd_index=VendorCmd.WRITE_RETRY_TABLE)
    ExecuteCMD.enqueue(vuc_backup)
    ExecuteCMD.send()


def _get_rpmb_region_val(rpmb_region_id: RPMBRegion) -> int:
    rpmb_region_dict = {
        RPMBRegion.REGION_0 : 0,
        RPMBRegion.REGION_1 : 1,
        RPMBRegion.REGION_2 : 2,
        RPMBRegion.REGION_3 : 3,
    }
    return rpmb_region_dict.get(rpmb_region_id, 0)


def get_flash_setting_buffer(access_vendor: bool = True) -> bytearray:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    data_len = DATA_SIZE_4K_BYTE
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=data_len, cmd_index=VendorCmd.READ_FLASH_SETTING, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b3_rsvd = VendorCmdRuleCdb3.CMD_OTHER
    idx = vuc.enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = ExecuteCMD.read_response(idx)
    ExecuteCMD.clear()
    return rsp.data


def get_flash_setting(access_vendor: bool = True) -> FlashSetting:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    buf = get_flash_setting_buffer(access_vendor)
    f = FlashSetting()
    f.from_bytes(buf)
    return f


def lba_to_pba(lun: int, lba: int, rpmb_region: int = 0, access_vendor: bool = True) -> L2P_PCA:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()

    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.L2P_READ, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b3_rsvd = VendorCmdRuleCdb3.CMD_OTHER

    vuc.upiu.u16_cdb.l8_pw_h = int.from_bytes(lba.to_bytes(4, byteorder='little', signed=False), byteorder='big')
    vuc.upiu.u16_cdb.l12_pw_l = lun << 24 | rpmb_region << 16
    idx = vuc.enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = ExecuteCMD.read_response(idx)
    ExecuteCMD.clear()

    pca = L2P_PCA(rsp.data[0:len(L2P_PCA().payload)])
    # logger.print_buffer(rsp.data)

    return pca

def load_PTE_data(index: int, access_vendor: bool = True) -> bytearray:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()

    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=2*DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.LOAD_PTE_TABLE, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b3_rsvd = VendorCmdRuleCdb3.CMD_OTHER

    packed_lba = struct.pack(r'<L', index)
    unpacked_lba = struct.unpack(r'>L', packed_lba)[0]
    vuc.upiu.u16_cdb.l8_pw_h = unpacked_lba  
    idx = vuc.enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = ExecuteCMD.read_response(idx)
    ExecuteCMD.clear()

    return rsp.data[0:DATA_SIZE_4K_BYTE]   

def load_PMD_data(LUN:int, LBA: int, access_vendor: bool = True) -> bytearray:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()

    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length= 2* DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.LOAD_PMD_TABLE)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b3_rsvd = VendorCmdRuleCdb3.CMD_OTHER

    packed_lba = struct.pack(r'<L', LBA)
    unpacked_lba = struct.unpack(r'>L', packed_lba)[0]
    vuc.upiu.u16_cdb.l8_pw_h = unpacked_lba  
    vuc.upiu.u16_cdb.l12_pw_l = LUN << 24
    idx = vuc.enqueue()
    ExecuteCMD.enqueue(vuc)
    ExecuteCMD.send(clear_on_success=False)
    rsp = ExecuteCMD.read_response(idx)
    ExecuteCMD.clear()
    
    return rsp.data[0:DATA_SIZE_4K_BYTE]  

def direct_read(pca: PCA, block_count: int, include_FW_spare:bool = False, access_vendor: bool = True) -> bytearray:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()

    pca.w8_len_4k = block_count    
    data_out = pca.to_bytes()

    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.WRITE_FOR_READ)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_DOUT
    vuc.data = data_out

    ExecuteCMD.enqueue(vuc)
    ExecuteCMD.send()

    expect_length = block_count * DATA_SIZE_4K_BYTE + DATA_SIZE_4K_BYTE
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=expect_length, cmd_index=VendorCmd.DIRECT_READ, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_DOUT
    
    idx = vuc.enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = ExecuteCMD.read_response(idx)
    ExecuteCMD.clear()
    if include_FW_spare:
        return rsp.data[:(block_count + 1) * DATA_SIZE_4K_BYTE]
    else:
        return rsp.data[:block_count * DATA_SIZE_4K_BYTE]   # 只回傳需要的資料，最後1個4K不是資料，所以不回傳


def direct_erase(pca: PCA, block_count: int, access_vendor: bool = True) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()

    write_size = block_count * DATA_SIZE_4K_BYTE

    data_out = bytearray(write_size)
    data_out[4] = pca.b4_mode
    data_out[5] = pca.b5_ce
    data_out[6] = pca.b6_plane
    data_out[7] = pca.b7_format
    data_out[8:10] = struct.pack("<H", block_count)
    data_out[10:12] = struct.pack("<H", (pca.b11_block_h<<8) | (pca.b10_block_l))
    data_out[12:14] = struct.pack("<H", pca.l12_fpage)

    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=write_size, cmd_index=VendorCmd.DIRECT_ERASE)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_DOUT
    vuc.data = data_out

    ExecuteCMD.enqueue(vuc)
    ExecuteCMD.send()


def direct_write(pca: PCA, block_count: int, data_buffer: bytearray, access_vendor: bool = True) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()

    write_size = (block_count+1) * DATA_SIZE_4K_BYTE

    data_out = bytearray(write_size)
    data_out[4] = pca.b4_mode
    data_out[5] = pca.b5_ce
    data_out[6] = pca.b6_plane
    data_out[7] = pca.b7_format
    data_out[8:10] = struct.pack("<H", block_count)
    data_out[10] = pca.b10_block_l
    data_out[11] = pca.b11_block_h
    data_out[12:14] = struct.pack("<L", pca.l12_fpage)

    data_out[4096:] = data_buffer

    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=write_size, cmd_index=VendorCmd.DIRECT_WRITE)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_DOUT
    vuc.data = data_out

    ExecuteCMD.enqueue(vuc)
    ExecuteCMD.send()


def get_fw_geometry(access_vendor: bool = True) -> FwGeometry:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()

    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_8K_BYTE, cmd_index=VendorCmd.GET_FW_GEOMETRY, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    idx = vuc.enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = ExecuteCMD.read_response(idx)
    ExecuteCMD.clear()

    fw_geometry = FwGeometry()
    fw_geometry.from_bytes(rsp.data)

    return fw_geometry

def get_event_info(access_vendor: bool = True) -> EventInfo:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()

    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.GET_EVENT_INFO, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    idx = vuc.enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = ExecuteCMD.read_response(idx)
    ExecuteCMD.clear()

    event_info = EventInfo()
    event_info.from_bytes(rsp.data)

    return event_info


def get_smart_info_data(access_vendor: bool = True) -> bytearray:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()

    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.GET_SMART_INFO_0XF0)
    i = vuc.enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = ExecuteCMD.read_response(i)
    rsp_data = rsp.data
    ExecuteCMD.clear()

    return rsp_data


def get_mconfig(keep_error:bool = False, access_vendor: bool = True) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.READ_MCONFIG, cmd_set_type=0x0F)

    cmd_index = ExecuteCMD.enqueue(vuc)
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
    return response, response.data

def set_mconfig(data_buffer: bytearray, keep_error:bool = False, access_vendor: bool = True) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.WRITE_MCONFIG, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_DOUT
    vuc.data = data_buffer

    cmd_index = ExecuteCMD.enqueue(vuc)
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

def read_memory(address: int, length: int=1, keep_error:bool = False, access_vendor: bool = True) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE*length, cmd_index=VendorCmd.READ_MEMORY, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b3_rsvd = VendorCmdRuleCdb3.CMD_ATTRIBUTE
    # vuc.upiu.u16_cdb.l8_pw_h = int.from_bytes(address.to_bytes(4, byteorder='little', signed=False), byteorder='little')
    vuc.upiu.u16_cdb.l8_pw_h = address
    # vuc.upiu.u16_cdb.l12_pw_l = int.from_bytes((DATA_SIZE_4K_BYTE).to_bytes(4, byteorder='little', signed=False), byteorder='little') << 16
    vuc.upiu.u16_cdb.l12_pw_l = DATA_SIZE_4K_BYTE << 16
    # for cygnus use
    vuc.upiu.u16_cdb.l12_pw_l |= (0x01 << 8)
    #
    cmd_index = ExecuteCMD.enqueue(vuc)
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
    return response, response.data

def read_Xmemory(sram_address: int, keep_error:bool = False, access_vendor: bool = True) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.READ_XMEMORY, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.l8_pw_h = int.from_bytes(sram_address.to_bytes(4, byteorder='little', signed=False), byteorder='big')
    cmd_index = ExecuteCMD.enqueue(vuc)
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
    return response, response.data

def get_debug_info(keep_error:bool = False, access_vendor: bool = True) -> tuple[CommandResponse, DebugInfo]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.GET_BLOCK_LIST, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    cmd_index = ExecuteCMD.enqueue(vuc)
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
    return response, DebugInfo(response.data)

def get_vb_info(keep_error:bool = False, access_vendor: bool = True) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.DUMP_VB_INFO, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b3_rsvd = 0 #all vb info
    cmd_index = ExecuteCMD.enqueue(vuc)
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
    return response, response.data

def get_vb_valid_cnt_info(keep_error:bool = False, access_vendor: bool = True) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_8K_BYTE, cmd_index=VendorCmd.DUMP_VB_INFO, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b3_rsvd = 1 #all vb valid count info
    cmd_index = ExecuteCMD.enqueue(vuc)
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
    return response, response.data

def get_remap_table(keep_error:bool = False, access_vendor: bool = True) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.DUMP_VB_INFO, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b3_rsvd = 2 #all remap table
    cmd_index = ExecuteCMD.enqueue(vuc)
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
    return response, response.data

def get_vb_group_size(keep_error:bool = False, access_vendor: bool = True) -> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.DUMP_VB_INFO, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b3_rsvd = 3 #vb grp size
    cmd_index = ExecuteCMD.enqueue(vuc)
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
    return response, response.data

def get_open_vb_info(keep_error:bool = False, access_vendor: bool = True) -> tuple[CommandResponse, OpenVBInfo]:
    if access_vendor:
        access_vendor_mode()
    parameter = bytearray(4096)
    parameter[0] = 0x0D;                            # Opcode
    parameter[1] = 0x42 + 0x2;                            # Func
    parameter[2] = (DATA_SIZE_4K_BYTE >> 8) & 0xFF; # DataLen_H
    parameter[3] = DATA_SIZE_4K_BYTE & 0xFF;        # DataLen_L
    cmd_queue = []
    cmd_queue.append(push_send_vu_parameter(parameter))
    data_index = push_read_vu_data(DATA_SIZE_32K_BYTE)
    cmd_queue.append(data_index)
    try:
        ExecuteCMD.send(clear_on_success=False)
        response = ExecuteCMD.read_response(data_index)
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
    return response, OpenVBInfo(response.data)

def get_previous_info(keep_error:bool = False, access_vendor: bool = True) -> tuple[CommandResponse, bytearray]:
    if access_vendor:
        access_vendor_mode()
    parameter = bytearray(4096)
    parameter[0] = 0x0A;                            # Opcode
    parameter[1] = 0x42 + 0x2;                            # Func
    parameter[2] = (DATA_SIZE_4K_BYTE >> 8) & 0xFF; # DataLen_H
    parameter[3] = DATA_SIZE_4K_BYTE & 0xFF;        # DataLen_L
    cmd_queue = []
    cmd_queue.append(push_send_vu_parameter(parameter))
    data_index = push_read_vu_data(DATA_SIZE_32K_BYTE)
    cmd_queue.append(data_index)
    try:
        ExecuteCMD.send(clear_on_success=False)
        response = ExecuteCMD.read_response(data_index)
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
    return response, response.data

def get_ics_table(keep_error:bool = False, access_vendor: bool = True) -> tuple[CommandResponse, bytearray]:
    if access_vendor:
        access_vendor_mode()
    parameter = bytearray(4096)
    parameter[0] = 0x04;                            # Opcode
    parameter[1] = 0x42 + 0x2;                            # Func
    parameter[2] = (DATA_SIZE_4K_BYTE >> 8) & 0xFF; # DataLen_H
    parameter[3] = DATA_SIZE_4K_BYTE & 0xFF;        # DataLen_L
    cmd_queue = []
    cmd_queue.append(push_send_vu_parameter(parameter))
    data_index = push_read_vu_data(DATA_SIZE_32K_BYTE)
    cmd_queue.append(data_index)
    try:
        ExecuteCMD.send(clear_on_success=False)
        response = ExecuteCMD.read_response(data_index)
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
    return response, response.data

def get_gc_threshold(access_vendor: bool = True) -> tuple[int ,int]:
    # _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignored
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.GET_GENERAL_INFO)
    i = vuc.enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = ExecuteCMD.read_response(i)
    rsp_data = rsp.data
    ExecuteCMD.clear()
    slc_gc_threshold = int.from_bytes(rsp_data[0:2], byteorder='little')
    mlc_gc_threhold = int.from_bytes(rsp_data[2:4], byteorder='little')
    return (slc_gc_threshold, mlc_gc_threhold)


def set_gc_threshold(parition:int, value:int, access_vendor: bool = True) -> None:
    #_log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignored
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.SET_GC_THRESHOLD)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b6_cmd2 = 0x03

    data_out = bytearray(DATA_SIZE_4K_BYTE)
    data_out[VENDOR_CMD_GC_THRESHOLD.GC_THRESHOLD_PARTITION] = parition
    data_out[VENDOR_CMD_GC_THRESHOLD.GC_THRESHOLD_DATA_NORMAL * 4 : VENDOR_CMD_GC_THRESHOLD.GC_THRESHOLD_DATA_NORMAL * 4 + 4] = struct.pack("<I", value)

    for i in range(4):
        data_out[VENDOR_CMD_GC_THRESHOLD.GC_THRESHOLD_DATA_ACTIVE * 4 + i] = 0xFF
        data_out[VENDOR_CMD_GC_THRESHOLD.GC_THRESHOLD_PTE_NORMAL * 4 + i] = 0xFF
        data_out[VENDOR_CMD_GC_THRESHOLD.GC_THRESHOLD_PTE_ACTIVE * 4 + i] = 0xFF
    vuc.data = data_out

    ExecuteCMD.enqueue(vuc)
    ExecuteCMD.send()


def get_block_read_count_table(access_vendor: bool = True) -> bytearray:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_8K_BYTE, cmd_index=VendorCmd.GET_BLOCK_READ_CNT)
    vuc.upiu.u16_cdb.b3_rsvd = VendorCmdRuleCdb3.CMD_OTHER
    cmd_index = ExecuteCMD.enqueue(vuc)
    ExecuteCMD.send(clear_on_success=False)
    response = ExecuteCMD.read_response(cmd_index)
    ExecuteCMD.clear()
    return response.data

def force_trigger_refresh_job(vb_number:int, priority:int=0, access_vendor: bool = True) -> None:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()

    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.TRIGGER_REFRESH_JOB, cmd_set_type=0x0F)
    
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b4_cmd0 = vb_number & 0xFF
    vuc.upiu.u16_cdb.b5_cmd1 = (vb_number >> 8) & 0xFF
    vuc.upiu.u16_cdb.b6_cmd2 = (vb_number >> 16) & 0xFF
    vuc.upiu.u16_cdb.b7_cmd3 = (vb_number >> 24) & 0xFF
    idx = vuc.enqueue()
   
    ExecuteCMD.send(clear_on_success=False)
    rsp = ExecuteCMD.read_response(idx)
    ExecuteCMD.clear()
    return
def load_bbt(keep_error:bool = False, access_vendor: bool = True) -> tuple[int, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=0x9000, cmd_index=VendorCmd.LOAD_RESULT_BLOCK_AND_BBT, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    cmd_index = ExecuteCMD.enqueue(vuc)
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
    print(f'plane per die={response.data[2]}')
    bitmap_size_of_ce, data = int.from_bytes(response.data[0:2], byteorder='little'), response.data[0x1000:0x9000]

    return bitmap_size_of_ce, data


def write_memory(data_buffer: bytearray, keep_error:bool = False, access_vendor: bool = True) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.WRITE_MEMORY, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_DOUT
    vuc.data = data_buffer
    cmd_index = ExecuteCMD.enqueue(vuc)
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

def write_Xmemory(sram_address:int, data_buffer: bytearray, isSectorMode:bool = False, keep_error:bool = False, access_vendor: bool = True) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=DATA_SIZE_8K_BYTE, cmd_index=VendorCmd.WRITE_XMEMORY, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_DOUT
    payload = bytearray(DATA_SIZE_8K_BYTE)
    payload[4:8] = sram_address.to_bytes(4, 'little')
    if isSectorMode:
        payload[0x1000 : 0x1000 +512] = data_buffer[0:512]
    else:
        payload[0x1000 : 0x2000] = data_buffer[0:0x1000]
    vuc.data = payload
    cmd_index = ExecuteCMD.enqueue(vuc)
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

def modify_desc_attr_flag(QuerryType: Vendor_CMD_Query_Func, Index:int, Value:int, IndexLen:int, keep_error:bool = False, access_vendor: bool = True) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    _param = shared.param
    if _param.gDevice.w16_spec_version == 0x310:
        UFS_Version = 0x04;
    elif _param.gDevice.w16_spec_version == 0x300 and _param.gMaxNumberLU == 32:
        UFS_Version = 0x03;
    elif _param.gDevice.w16_spec_version == 0x210 and _param.gMaxNumberLU == 32:
        UFS_Version = 0x02;
    elif _param.gDevice.w16_spec_version == 0x220:
        UFS_Version = 0x05;
    elif _param.gDevice.w16_spec_version == 0x400:
        UFS_Version = 0x06;
    elif _param.gDevice.w16_spec_version == 0x410:
        UFS_Version = 0x07;
    else:
        UFS_Version = 0x01;
    dwTotal4K_Count = 1;
    
    desc_info = Descptor_Att_Flag()
    attr_info = Descptor_Att_Flag()
    flag_info = Descptor_Att_Flag()
    scsiinfo = Descptor_Att_Flag()
    data_buffer = bytearray(DATA_SIZE_4K_BYTE)
    byQueryOft = 4 + 4
    if QuerryType == Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_DESCRIPTOR:
        desc_info.QueryType.value = QuerryType
        desc_info.QueryCount.value = 1
        desc_info.Index.value = Index
        desc_info.ValueOft.value = 0x200
        desc_info.IndexLen.value = IndexLen
        data_buffer[byQueryOft:byQueryOft+len(desc_info.payload)] = desc_info.payload.copy()
        byQueryOft += len(desc_info.payload)
    else:
        desc_info.QueryType.value = Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_DESCRIPTOR
        desc_info.QueryCount.value = 0
        data_buffer[byQueryOft:byQueryOft+len(desc_info.payload)] = desc_info.payload.copy()
        byQueryOft += 4
    if QuerryType == Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_ATTRIBUTE:
        attr_info.QueryType.value = QuerryType
        attr_info.QueryCount.value = 1
        attr_info.Index.value = Index
        attr_info.ValueOft.value = 0x200
        attr_info.IndexLen.value = IndexLen
        data_buffer[byQueryOft:byQueryOft+len(attr_info.payload)] = attr_info.payload.copy()
        byQueryOft += len(attr_info.payload)
    else:
        attr_info.QueryType.value = Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_ATTRIBUTE
        attr_info.QueryCount.value = 0
        data_buffer[byQueryOft:byQueryOft+len(attr_info.payload)] = attr_info.payload.copy()
        byQueryOft += 4
    if QuerryType == Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_FLAG:
        flag_info.QueryType.value = QuerryType
        flag_info.QueryCount.value = 1
        flag_info.Index.value = Index
        flag_info.ValueOft.value = 0x200
        flag_info.IndexLen.value = IndexLen
        data_buffer[byQueryOft:byQueryOft+len(flag_info.payload)] = flag_info.payload.copy()
        byQueryOft += len(flag_info.payload)
    else:
        flag_info.QueryType.value = Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_FLAG
        flag_info.QueryCount.value = 0
        data_buffer[byQueryOft:byQueryOft+len(flag_info.payload)] = flag_info.payload.copy()
        byQueryOft += 4
    scsiinfo.QueryType.value = Vendor_CMD_Query_Func.VENDOR_CMD_QUERY_SCSI
    data_buffer[byQueryOft: byQueryOft +4] = scsiinfo.payload[0:4]

    data_buffer[0:4] = UFS_Version.to_bytes(4, 'little')
    data_buffer[4:8] = dwTotal4K_Count.to_bytes(4, 'little')
    data_buffer[0x200:0x200+4] = Value.to_bytes(4, 'little')
    
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.WRITE_PARAMETER, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_DOUT
    vuc.data = data_buffer
    cmd_index = ExecuteCMD.enqueue(vuc)
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

def set_ftl_version(slc_partition_current_vb_version:int = 0xFFFFFFFF, mlc_partition_current_vb_version:int = 0xFFFFFFFF, set_VB_version:Dict[int, int] = {}, access_vendor: bool = True) -> None:
    #_log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignored
    if access_vendor:
        access_vendor_mode()
    vuc = ExecuteCMD.VendorCmdWrite()
    vuc.assign(length=DATA_SIZE_16K_BYTE, cmd_index=VendorCmd.SET_GC_THRESHOLD)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b6_cmd2 = 0x05

    data_out = bytearray(DATA_SIZE_16K_BYTE)
    for i in range(len(data_out)):
        data_out[i] = 0xFF
    for (vb, value) in set_VB_version.items():
        data_out[vb*4:(vb+1)*4] = value.to_bytes(4, 'little')
    data_out[0:4] = slc_partition_current_vb_version.to_bytes(4, 'little')
    data_out[4:8] = mlc_partition_current_vb_version.to_bytes(4, 'little')
    vuc.data = data_out

    ExecuteCMD.enqueue(vuc)
    ExecuteCMD.send()