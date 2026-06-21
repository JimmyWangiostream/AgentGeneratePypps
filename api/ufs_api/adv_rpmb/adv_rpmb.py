import random
import struct
import Script.api.shared as shared
import Script.api.cmd_seq as ExecuteCMD
from Script.api.ufs_api.upiu.structs import AdvRpmbMetaInfo, EhsAdvRpmb
from Script.api.util.functions import dumpfile
from Script.api.ufs_api.defines import WellKnownLUN, RPMBMsgType, RPMBOperationResult

from Script.api.exception import *

from Script.api.ufs_api.rpmb.sha2 import hmac_sha256

_log = shared.logger

class AdvRPMB():
    def __init__(self, region_id: int) -> None:
        self.write_counter = 0
        self.key = bytearray([0x78, 0x56, 0x34, 0x12] * 8)
        self.region_id = region_id

    def adv_rpmb_read_counter(self) -> int:
        _log.info("function - adv_rpmb_read_counter()")
        
        nonce = bytearray(random.randbytes(16))

        _log.info("Flow-a = Read Write-Counter Request (Security Protocol In)")
        meta_info = AdvRpmbMetaInfo()
        meta_info.w0_message_type = RPMBMsgType.WRITE_COUNTER_READ_REQ
        meta_info.dq2_nonce = nonce

        sp_in = ExecuteCMD.SecurityProtocolIn().assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 0)
        sp_in.set_adv_rpmb_ehs(meta_info)
        cmd_index = sp_in.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        response = ExecuteCMD.read_response(cmd_index)
        ExecuteCMD.clear()

        ehs_rsp = EhsAdvRpmb()
        ehs_rsp.from_bytes(response.ehs.to_bytes())

        _log.info("Flow-c = Check Read Write-Counter result code")
        if not (ehs_rsp.meta_info.w0_message_type == RPMBMsgType.WRITE_COUNTER_READ_RSP and
                ehs_rsp.meta_info.w26_result == RPMBOperationResult.RESULT_OK):
            _log.warning(f"req_rsp_type = {ehs_rsp.meta_info.w0_message_type}, result = {ehs_rsp.meta_info.w26_result}")
                    
            if ehs_rsp.meta_info.w26_result == RPMBOperationResult.RESULT_OK_COUNTER_EXPIRED:
                raise SPEC_ASSERT_RPMB_WRITE_COUNTER_EXPIRED
            elif ehs_rsp.meta_info.w26_result == RPMBOperationResult.KEY_NOT_PROGRAMMED:
                raise SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET
            elif ehs_rsp.meta_info.w26_result == RPMBOperationResult.GENERAL_FAILURE:
                raise SPEC_ASSERT_RPMB_GENERAL_FAILURE
            else:
                raise SPEC_ASSERT_RPMB_WRITE_COUNTER_READ_FAIL

        _log.info("Flow-d = Check Read Write-Counter Nonce is match or not")
        if ehs_rsp.meta_info.dq2_nonce != nonce:
            raise SPEC_ASSERT_RPMB_NONCE_MISMATCH

        _log.info(f"write_counter = {ehs_rsp.meta_info.l18_write_counter}")
        self.write_counter = ehs_rsp.meta_info.l18_write_counter

        return ehs_rsp.meta_info.l18_write_counter

    def adv_rpmb_key_programming(self, key:bytearray | None=None) -> None:
        _log.info("function - adv_rpmb_key_programming()")
        if key is not None:
            self.key = key

        meta_info = AdvRpmbMetaInfo()
        meta_info.w0_message_type = RPMBMsgType.KEY_PROGRAM_REQ
        sp_out = ExecuteCMD.SecurityProtocolOut()
        sp_out.assign(lun=WellKnownLUN.RPMB, security_protocol=0xEC, security_protocol_spec=self.region_id, transfer_length=0)
        sp_out.set_adv_rpmb_ehs(meta_info, self.key)

        idx = sp_out.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        response = ExecuteCMD.read_response(idx)
        ExecuteCMD.clear()

        ehs_rsp = EhsAdvRpmb()
        ehs_rsp.from_bytes(response.ehs.to_bytes())
        if not (ehs_rsp.meta_info.w0_message_type == RPMBMsgType.KEY_PROGRAM_RSP and 
                ehs_rsp.meta_info.w26_result == RPMBOperationResult.RESULT_OK):
            _log.info(f"req_rsp_type = {ehs_rsp.meta_info.w0_message_type}, result = {ehs_rsp.meta_info.w26_result}")
            if ehs_rsp.meta_info.w26_result == RPMBOperationResult.GENERAL_FAILURE:
                raise SPEC_ASSERT_RPMB_GENERAL_FAILURE
            else:
                raise SPEC_ASSERT_RPMB_KEY_PROGRAMMING_FAIL
    
    def gen_mac_for_adv_write_rpmb_data(self, meta_info: AdvRpmbMetaInfo) -> tuple[bytearray, bytearray]:
        _log.info("function - gen_mac_for_write_rpmb_data()")

        address = meta_info.w22_address_lun
        block_count = meta_info.w24_block_count
        key = self.key
        mac = bytearray(32)
        
        temp_data_buffer = bytearray(4096)
        rpmb_data_buffer = bytearray(block_count * 4096)
        mac_buffer = bytearray(block_count * 4096 + 32) # 用來放 gen mac 的 buffer, 除了資料還要加上 meta_info + 4個0, 共 32 bytes
        
        for i in range(block_count):

            for j in range(1024):     # 建立 data pattern
                temp_data_buffer[j*4: (j+1)*4] = struct.pack('>L', address)

            address += 1
        
            rpmb_data_buffer[i*4096: (i+1)*4096] = temp_data_buffer[0:4096]

            # dumpfile("rpmb_data_buffer.bin", rpmb_data_buffer)

            if i == block_count - 1:
                mac_buffer[0:] = rpmb_data_buffer[0:]
                mac_buffer[(i+1)*4096:] = meta_info.to_bytes() + bytearray(4)
                mac = hmac_sha256(key, mac_buffer)
                        
                # dumpfile("key.bin", bytearray(key))
                # dumpfile("mac.bin", bytearray(mac))
                # dumpfile("mac_buffer_meta.bin", mac_buffer)

        return rpmb_data_buffer, mac

    def adv_rpmb_write_data(self, start_lba: int, data_len: int) -> None:
        _log.info("function - adv_rpmb_write_data()")
        
        nonce = bytearray(random.randbytes(16))

        _log.info("Flow-a = Write data Request (Security Protocol Out) ")
        meta_info = AdvRpmbMetaInfo()
        meta_info.w0_message_type = RPMBMsgType.DATA_WRITE_REQ
        meta_info.dq2_nonce = nonce
        meta_info.l18_write_counter = self.write_counter
        meta_info.w22_address_lun = start_lba
        meta_info.w24_block_count = data_len
        rpmb_data_buffer, mac = self.gen_mac_for_adv_write_rpmb_data(meta_info)

        sp_out = ExecuteCMD.SecurityProtocolOut().assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 4096 * data_len)
        sp_out.set_adv_rpmb_ehs(meta_info, mac)
        sp_out.data = rpmb_data_buffer
        cmd_index = sp_out.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        response = ExecuteCMD.read_response(cmd_index)
        ExecuteCMD.clear()

        ehs_rsp = EhsAdvRpmb()
        ehs_rsp.from_bytes(response.ehs.to_bytes())
        _log.info("Flow-b = Check Write data result code ")
        if not (ehs_rsp.meta_info.w0_message_type == RPMBMsgType.DATA_WRITE_RSP and ehs_rsp.meta_info.w26_result == RPMBOperationResult.RESULT_OK):
            _log.info(f"req_rsp_type = {ehs_rsp.meta_info.w0_message_type}, result = {ehs_rsp.meta_info.w26_result}")

            if ehs_rsp.meta_info.w26_result == RPMBOperationResult.KEY_NOT_PROGRAMMED:
                raise SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET
            elif ehs_rsp.meta_info.w26_result == RPMBOperationResult.AUTHENTICATION_FAILURE:
                raise SPEC_ASSERT_RPMB_MAC_MISMATCH
            
        self.write_counter = ehs_rsp.meta_info.l18_write_counter

    def adv_rpmb_read_data(self, start_lba: int, data_len: int) -> None:
        _log.info("function - adv_rpmb_read_data()")
        nonce = bytearray(random.randbytes(16))

        _log.info("Flow-a = Read data Request (Security Protocol In) ")
        meta_info = AdvRpmbMetaInfo()
        meta_info.w0_message_type = RPMBMsgType.DATA_READ_REQ
        meta_info.dq2_nonce = nonce
        meta_info.l18_write_counter = 0
        meta_info.w22_address_lun = start_lba
        meta_info.w24_block_count = data_len
        sp_in = ExecuteCMD.SecurityProtocolIn().assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 0)     
        sp_in.set_adv_rpmb_ehs(meta_info)
        cmd_index = sp_in.enqueue()
        ExecuteCMD.send(clear_on_success=False)
        response = ExecuteCMD.read_response(cmd_index)
        ExecuteCMD.clear()

        _log.info("Flow-b = Check Read Write-Counter result code and device MAC ")
        # dumpfile("rpmb_read_data.bin", response.data)
        ehs_rsp = EhsAdvRpmb()
        ehs_rsp.from_bytes(response.ehs.to_bytes())
        
        temp_data = bytearray()
        temp_data[0:] = response.data[0:]
        temp_data[data_len*4096:] = ehs_rsp.meta_info.to_bytes() + bytearray(4)

        check_mac = hmac_sha256(self.key, temp_data)

        # dumpfile("device_mac.bin", ehs_rsp.mac_key)
        # dumpfile("check_mac.bin", check_mac)

        if ehs_rsp.mac_key != check_mac:
            raise SPEC_ASSERT_RPMB_MAC_MISMATCH

        if not (ehs_rsp.meta_info.w0_message_type == RPMBMsgType.DATA_READ_RSP and ehs_rsp.meta_info.w26_result == RPMBOperationResult.RESULT_OK):
            _log.info(f"req_rsp_type = {ehs_rsp.meta_info.w0_message_type}, result = {ehs_rsp.meta_info.w26_result}")
                    
            if ehs_rsp.meta_info.w26_result == RPMBOperationResult.RESULT_OK_COUNTER_EXPIRED:
                raise SPEC_ASSERT_RPMB_WRITE_COUNTER_EXPIRED
            
        _log.info("Flow-d = Check Read data Nonce is match or not")
        if ehs_rsp.meta_info.dq2_nonce != nonce:
            raise SPEC_ASSERT_RPMB_NONCE_MISMATCH