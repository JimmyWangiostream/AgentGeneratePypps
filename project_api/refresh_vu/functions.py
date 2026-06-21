import inspect
from typing import cast, List

from Script.api import shared, dumpfile, cmd_seq as ExecuteCMD

import random
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd
from Script.api.cmd_seq.response import CommandResponse
from Script.project_api.refresh_vu.define import *
from Script.project_api.refresh_vu.structs import *

_log = shared.logger

def issue_C088_to_start_or_stop_refresh(bParameter0:VUC088Paremeter, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_C088()
    vu.b0_opcode.value = 0x88
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.bParameter0.value = bParameter0
    response= send_data_out_vcmd(micron_vendor_cmd=vu, data_payload = bytearray(0x1000), keep_error=keep_error)
    return response

def issue_C087_to_add_VB_to_bookingQ_and_book_refresh(VB_type:VUC087VB_type, VB_list:List[int], booking_user:int, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_C087()
    vu.b0_opcode.value = 0x87
    vu.b1_func.value = 0xC0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.bParameter0.value = VB_type
    vu.bParameter1.value = len(VB_list)
    vu.bParameter2.value = booking_user
    data_payload = bytearray(0x1000)
    for idx, vb in enumerate(VB_list):
        data_payload[idx*2 : (idx+1)*2] = vb.to_bytes(2, 'little')        
    response= send_data_out_vcmd(micron_vendor_cmd=vu, data_payload = data_payload, keep_error=keep_error)
    return response

def issue_40C5_to_get_booking_queue(keep_error:bool = False) -> tuple[CommandResponse, BookingQueue]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40C5()
    vu.b0_opcode.value = 0xC5
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    bookingQ = BookingQueue(payload)
    bookingQ.BookingQueueVB = bookingQ.BookingQueueVB[0:bookingQ.LogicalVBNumberInBookingQueue.value]
    return response, bookingQ