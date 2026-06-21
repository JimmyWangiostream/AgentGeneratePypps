import random

from typing import cast, Optional

import struct
import Script.api.shared as shared
import Script.api.cmd_seq as ExecuteCMD

from Script.api.cmd_seq.response import CommandResponse, get_scsi_status_str, get_sense_key_str, get_asc_ascq_description
from Script.api.ufs_api.rpmb.structs import RPMBMsgDataFrame
from Script.api.ufs_api.functions import dumpfile
from Script.api.ufs_api.defines import WellKnownLUN, ScsiStatus, RPMBMsgType, RPMBOperationResult

from Script.api.exception import *

from Script.api.ufs_api.rpmb.sha2 import hmac_sha256

_log = shared.logger

class RPMB():
    def __init__(self, region_id: int) -> None:
        self.write_counter = 0
        self.key = bytearray([0x78, 0x56, 0x34, 0x12] * 8)
        self.region_id = region_id

    def rpmb_read_counter(self) -> int:
        _log.info("function - rpmb_read_counter()")
        
        backup_nonce = bytearray(16)
        rpmb_data_frame = RPMBMsgDataFrame()

        write_counter = 0

        rpmb_data_frame.nonce = backup_nonce = bytearray(random.randbytes(16))

        _log.info("Flow-a = Read Write-Counter Request (Security Protocol Out)")

        rpmb_data_frame.req_rsp_type = RPMBMsgType.WRITE_COUNTER_READ_REQ

        security_protocol_out = ExecuteCMD.SecurityProtocolOut()
        security_protocol_out.assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 512)
        security_protocol_out.data = rpmb_data_frame.to_bytes()
        ExecuteCMD.enqueue(security_protocol_out)
        ExecuteCMD.send()

        _log.info("Flow-b = Read Write-Counter Response (Security Protocol In)")

        security_protocol_in = ExecuteCMD.SecurityProtocolIn()
        security_protocol_in.assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 512)
        cmd_index = ExecuteCMD.enqueue(security_protocol_in)
        ExecuteCMD.send(clear_on_success=False)

        response = ExecuteCMD.read_response(cmd_index)

        ExecuteCMD.clear()

        if not (response.upiu.b6_response == 0 and response.upiu.b7_status == ScsiStatus.GOOD):
            _log.info(f"status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}")
            raise SPEC_ASSERT_SECURITY_PROTOCOL_IN_FAIL

        _log.info("Flow-c = Check Read Write-Counter result code")

        rpmb_data_frame.from_bytes(response.data)

        if not (rpmb_data_frame.req_rsp_type == RPMBMsgType.WRITE_COUNTER_READ_RSP and rpmb_data_frame.result == RPMBOperationResult.RESULT_OK):
            _log.info(f"req_rsp_type = {rpmb_data_frame.req_rsp_type}, result = {rpmb_data_frame.result}")
                    
            if rpmb_data_frame.result == RPMBOperationResult.RESULT_OK_COUNTER_EXPIRED:
                raise SPEC_ASSERT_RPMB_WRITE_COUNTER_EXPIRED
            else:
                if rpmb_data_frame.result == RPMBOperationResult.KEY_NOT_PROGRAMMED:
                    raise SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET
                elif rpmb_data_frame.result == RPMBOperationResult.GENERAL_FAILURE:
                    raise SPEC_ASSERT_RPMB_GENERAL_FAILURE
                else:
                    raise SPEC_ASSERT_RPMB_WRITE_COUNTER_READ_FAIL

        _log.info("Flow-d = Check Read Write-Counter Nonce is match or not")

        if rpmb_data_frame.nonce != backup_nonce:
            raise SPEC_ASSERT_RPMB_NONCE_MISMATCH

        _log.info(f"write_counter = {rpmb_data_frame.write_counter}")

        self.write_counter = rpmb_data_frame.write_counter

        return rpmb_data_frame.write_counter

    def rpmb_key_programming(self, key: Optional[bytearray] = None) -> None:
        _log.info("function - rpmb_key_programming()")
        
        rpmb_data_frame = RPMBMsgDataFrame()

        if key == None:
            pass
        else:
            self.key = key

        rpmb_data_frame.key_mac = self.key

        # print('===========================================')    
        # ExecuteCMD.print_bytearray(rpmb_data_frame.key_mac)

        _log.info("Flow-a = Authentication Key Programming Request (Security Protocol Out) ")

        rpmb_data_frame.req_rsp_type = RPMBMsgType.KEY_PROGRAM_REQ

        security_protocol_out = ExecuteCMD.SecurityProtocolOut()
        security_protocol_out.assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 512)
        security_protocol_out.set_option(wait_queue_empty=True)
        security_protocol_out.data = rpmb_data_frame.to_bytes()
        ExecuteCMD.enqueue(security_protocol_out)
        # ExecuteCMD.send()

        _log.info("Flow-b = Key Programming Result Request (Security Protocol Out) ")

        rpmb_data_frame.req_rsp_type = RPMBMsgType.RESULT_READ_REQ
        rpmb_data_frame.key_mac = bytearray(0)

        security_protocol_out = ExecuteCMD.SecurityProtocolOut()
        security_protocol_out.assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 512)
        security_protocol_out.set_option(wait_queue_empty=True)
        security_protocol_out.data = rpmb_data_frame.to_bytes()
        ExecuteCMD.enqueue(security_protocol_out)
        # ExecuteCMD.send()

        _log.info("Flow-c = Key Programming Result Response (Security Protocol In)")

        security_protocol_in = ExecuteCMD.SecurityProtocolIn()
        security_protocol_in.assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 512)
        security_protocol_in.set_option(wait_queue_empty=True)
        cmd_index = ExecuteCMD.enqueue(security_protocol_in)
        ExecuteCMD.send(clear_on_success=False)

        response = ExecuteCMD.read_response(cmd_index)

        ExecuteCMD.clear()

        if not (response.upiu.b6_response == 0 and response.upiu.b7_status == ScsiStatus.GOOD):
            _log.info(f"status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}")
            raise SPEC_ASSERT_SECURITY_PROTOCOL_IN_FAIL

        rpmb_data_frame.from_bytes(response.data)

        if not (rpmb_data_frame.req_rsp_type == RPMBMsgType.KEY_PROGRAM_RSP and rpmb_data_frame.result == RPMBOperationResult.RESULT_OK):
            _log.info(f"req_rsp_type = {rpmb_data_frame.req_rsp_type}, result = {rpmb_data_frame.result}")

            if rpmb_data_frame.result == RPMBOperationResult.GENERAL_FAILURE:
                raise SPEC_ASSERT_RPMB_GENERAL_FAILURE
            else:
                raise SPEC_ASSERT_RPMB_KEY_PROGRAMMING_FAIL
            
    def gen_mac_for_write_rpmb_data(self, rpmb_data_frame: RPMBMsgDataFrame) -> bytearray:
        _log.info("function - gen_mac_for_write_rpmb_data()")

        address = rpmb_data_frame.address
        block_count = rpmb_data_frame.block_count
        key = self.key

        rpmb_data_buffer = bytearray(block_count * 512)   # 用來放 rpmb data
        mac_buffer = bytearray(block_count * 284) # 用來放 gen mac 的 buffer

        rpmb_data_frame.key_mac = bytearray(0)

        for i in range(block_count):

            for j in range(64):     # 建立 data pattern
                rpmb_data_frame.data[j*4: (j+1)*4] = struct.pack('>L', address)

            address += 1
            
            temp_data = rpmb_data_frame.to_bytes()

            mac_buffer[i*284: (i+1)*284] = temp_data[228:512]

            if i == block_count - 1:
                rpmb_data_frame.key_mac = hmac_sha256(key, mac_buffer)                
                # print(f"HMAC-SHA-256 Result: {rpmb_data_frame.key_mac.hex()}")
            
            rpmb_data_buffer[i*512: (i+1)*512] = rpmb_data_frame.to_bytes()
        
        # dumpfile("key.bin", bytearray(key))
        # dumpfile("key_mac.bin", bytearray(rpmb_data_frame.key_mac))
        # dumpfile("mac_buffer.bin", mac_buffer)
        # dumpfile("rpmb_data_buffer.bin", rpmb_data_buffer)

        return rpmb_data_buffer
        
    def rpmb_write_data(self, start_lba: int, data_len: int) -> None:
        _log.info("function - rpmb_write_data()")
        
        rpmb_data_frame = RPMBMsgDataFrame()

        rpmb_data_frame.key_mac = self.key

        _log.info("Flow-a = Write data Request (Security Protocol Out) ")

        rpmb_data_frame.write_counter = self.write_counter
        rpmb_data_frame.address = start_lba
        rpmb_data_frame.block_count = data_len
        rpmb_data_frame.req_rsp_type = RPMBMsgType.DATA_WRITE_REQ
        
        rpmb_data_buffer = bytearray(rpmb_data_frame.block_count * 512)   # 用來放 rpmb data
        rpmb_data_buffer = self.gen_mac_for_write_rpmb_data(rpmb_data_frame)
        #dumpfile('writebuffer',rpmb_data_buffer)

        security_protocol_out = ExecuteCMD.SecurityProtocolOut()
        security_protocol_out.assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 512 * data_len)
        security_protocol_out.set_option(wait_queue_empty=True)
        security_protocol_out.data = rpmb_data_buffer
        ExecuteCMD.enqueue(security_protocol_out)
        # ExecuteCMD.send()

        _log.info("Flow-b = Write data result Request (Security Protocol Out) ")

        rpmb_data_frame.req_rsp_type = RPMBMsgType.RESULT_READ_REQ
        rpmb_data_frame.key_mac = bytearray(0)

        security_protocol_out = ExecuteCMD.SecurityProtocolOut()
        security_protocol_out.assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 512)
        security_protocol_out.set_option(wait_queue_empty=True)
        security_protocol_out.data = rpmb_data_frame.to_bytes()
        ExecuteCMD.enqueue(security_protocol_out)
        # ExecuteCMD.send()

        _log.info("Flow-c = Write data result Response (Security Protocol In) ")

        security_protocol_in = ExecuteCMD.SecurityProtocolIn()
        security_protocol_in.assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 512)
        security_protocol_in.set_option(wait_queue_empty=True)
        cmd_index = ExecuteCMD.enqueue(security_protocol_in)
        ExecuteCMD.send(clear_on_success=False)

        response = ExecuteCMD.read_response(cmd_index)

        ExecuteCMD.clear()

        if not (response.upiu.b6_response == 0 and response.upiu.b7_status == ScsiStatus.GOOD):
            _log.info(f"status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}")
            raise SPEC_ASSERT_SECURITY_PROTOCOL_IN_FAIL

        rpmb_data_frame.from_bytes(response.data)

        _log.info("Flow-d = Check Write data result code ")

        if not (rpmb_data_frame.req_rsp_type == RPMBMsgType.DATA_WRITE_RSP and rpmb_data_frame.result == RPMBOperationResult.RESULT_OK):
            _log.info(f"req_rsp_type = {rpmb_data_frame.req_rsp_type}, result = {rpmb_data_frame.result}")

            if rpmb_data_frame.result == RPMBOperationResult.KEY_NOT_PROGRAMMED:
                raise SPEC_ASSERT_RPMB_KEY_NOT_PROGRAMMED_YET
            
        self.write_counter = rpmb_data_frame.write_counter

    def rpmb_read_data(self, start_lba: int, data_len: int) -> CommandResponse:
        _log.info("function - rpmb_read_data()")
        
        backup_nonce = bytearray(16)

        _log.info("Flow-a = Read data Request (Security Protocol Out) ")

        rpmb_data_frame = RPMBMsgDataFrame()

        rpmb_data_frame.nonce = backup_nonce = bytearray(random.randbytes(16))

        rpmb_data_frame.address = start_lba
        rpmb_data_frame.block_count = data_len
        rpmb_data_frame.req_rsp_type = RPMBMsgType.DATA_READ_REQ

        security_protocol_out = ExecuteCMD.SecurityProtocolOut()
        security_protocol_out.assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 512)
        security_protocol_out.data = rpmb_data_frame.to_bytes()
        ExecuteCMD.enqueue(security_protocol_out)
        ExecuteCMD.send()

        _log.info("Flow-b = Read data Response (Security Protocol In) ")

        security_protocol_in = ExecuteCMD.SecurityProtocolIn()
        security_protocol_in.assign(WellKnownLUN.RPMB, 0xEC, self.region_id, 512 * data_len)
        cmd_index = ExecuteCMD.enqueue(security_protocol_in)
        ExecuteCMD.send(clear_on_success=False)

        response = ExecuteCMD.read_response(cmd_index)
        ExecuteCMD.clear()

        if not (response.upiu.b6_response == 0 and response.upiu.b7_status == ScsiStatus.GOOD):
            _log.info(f"status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}")
            raise SPEC_ASSERT_SECURITY_PROTOCOL_IN_FAIL

        _log.info("Flow-c = Check Read Write-Counter result code and device MAC ")

        # dumpfile("rpmb_read_data.bin", response.data)

        rpmb_data = bytearray(data_len * 284)

        for i in range(data_len):            
            rpmb_data_frame.from_bytes(response.data[i*512: (i+1)*512])
            temp_data = rpmb_data_frame.to_bytes()
            rpmb_data[i*284: (i+1)*284] = temp_data[228:512]

            if i == data_len - 1:
                device_mac = rpmb_data_frame.key_mac
                check_mac = hmac_sha256(self.key, rpmb_data)

                # dumpfile("device_mac.bin", device_mac)
                # dumpfile("check_mac.bin", check_mac)

                if device_mac != check_mac:
                    raise SPEC_ASSERT_RPMB_MAC_MISMATCH

        if not (rpmb_data_frame.req_rsp_type == RPMBMsgType.DATA_READ_RSP and rpmb_data_frame.result == RPMBOperationResult.RESULT_OK):
            _log.info(f"req_rsp_type = {rpmb_data_frame.req_rsp_type}, result = {rpmb_data_frame.result}")
                    
            if rpmb_data_frame.result == RPMBOperationResult.RESULT_OK_COUNTER_EXPIRED:
                raise SPEC_ASSERT_RPMB_WRITE_COUNTER_EXPIRED
            
        _log.info("Flow-d = Check Read data Nonce is match or not")

        if rpmb_data_frame.nonce != backup_nonce:
            raise SPEC_ASSERT_RPMB_NONCE_MISMATCH
        return response
