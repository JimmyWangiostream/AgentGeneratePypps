import inspect
from Script.pattern.pattern_logger import logger
from typing import cast, List, Generator, Tuple, Dict, Optional
from Script.api.exception import SIGHTING_RESPONSE_UNEXPECTED
from Script.project_api.reh.structs import \
    ERROR_NUMBER_INFORMATION_RECORD, \
    ERROR_NUMBER_INFORMATION, \
    micron_vu_D014_option_0, \
    micron_vu_D014_option_1, \
    micron_vu_D014_option_2, \
    micron_vu_D014_option_6, \
    micron_vu_D014_option_7, \
    micron_vu_D014_option_8, \
    micron_vu_40F9, \
    micron_vu_4014_option_0, \
    micron_vu_4014_option_1, \
    micron_vu_4014_option_2, \
    micron_vu_4014_option_5, \
    micron_vu_4014_option_7, \
    micron_vu_409E, \
    micron_vu_40BB, \
    micron_vu_D019, \
    rr_number_and_error_bits, \
    read_recovery_info_read_last, \
    error_bit_number_of_last_reading, \
    error_bit_number_and_read_retry_step, \
    error_recovery_statistics, \
    READ_LAST_TABLE, \
    PAGE_TYPE, \
    BLOCK_PAGE_TYPE, REH_STEP_TABLE, \
    ERROR_RECOVERY_STATISTICS_RECORD, \
    ERROR_RECOVERY_STATISTICS
from Script.api import shared, dumpfile, cmd_seq as ExecuteCMD
import random
from Script import api
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_no_data_vcmd
from Script.project_api.mconfig_vu.structs import mConfig, pConfig
from Script.api.cmd_seq.response import CommandResponse

_log = shared.logger

ReadLastTableDict = Dict[READ_LAST_TABLE, List[int]]
READ_LAST_TABLE_TYPE= Dict[PAGE_TYPE, ReadLastTableDict]   # die0、die1…的最外層型別

def iter_reh_steps(type: BLOCK_PAGE_TYPE, start_big_step: int = 0)-> Generator[Tuple[int, int], None, None]:
    table = REH_STEP_TABLE.get(type, {})
    for big_step in sorted(table): 
        if(big_step < start_big_step):
            continue        
        for small_step in table[big_step]:  
            yield big_step, small_step  

def create_read_last_ref_table(maxDie: int)-> Dict[int, READ_LAST_TABLE_TYPE]:
    result : Dict[int, READ_LAST_TABLE_TYPE] = {}

    def _rand_list(length: int) -> list[int]:
        rand_vals = [(random.randint(-20, 20) & 0xFF) for _ in range(length)]
        if length < 3:
            rand_vals.extend([0] * (3 - length))
        return rand_vals
    
    for ce in range(maxDie):
        table: READ_LAST_TABLE_TYPE = {}
        for page in PAGE_TYPE:
            table[page] = {
                READ_LAST_TABLE.LAST_TABLE_1: _rand_list(page.offset_count),
                READ_LAST_TABLE.LAST_TABLE_2: _rand_list(page.offset_count)
            }
        result[ce] = table
    return result

def set_read_last_table(maxDie: int, read_last_table:Dict[int, READ_LAST_TABLE_TYPE]) -> None:

    """將 0‑255 的 byte 轉成有號 byte（-128 ~ 127）。"""
    def _to_signed_byte(val: int) -> int:
        return val - 256 if val > 127 else val
    
    for ce in range(maxDie):
        for page in PAGE_TYPE:
            for index in READ_LAST_TABLE:
                offsets = read_last_table[ce][page][index]
                _ = issue_D014_to_set_last_table_content(ce, page, index, offsets[0], offsets[1], offsets[2])
                signed_offsets = [_to_signed_byte(o) for o in offsets[:3]]
                logger.info(f'read last offset ce: {ce}, page_type: {page.label}, index: {index}, offset:[{signed_offsets[0]}, {signed_offsets[1]}, {signed_offsets[2]}]')
    pass

def get_page_type_by_physical_page(page:int, block:int, isSLC: int) -> tuple[int, int]:
    page_type =0
    block_type = 0
    if(isSLC):
        if block < 20:
            page_type = PAGE_TYPE.PAGE_POR_SSLC
        else:
            page_type = PAGE_TYPE.PAGE_POR_DSLC
        
        block_type = BLOCK_PAGE_TYPE.SLC_BLOCK_SLC_PAGE
    else:
        if page >= 3308:
            page_type = PAGE_TYPE.PAGE_SLC_LP
            block_type = BLOCK_PAGE_TYPE.TLC_BLOCK_SLC_PAGE
        elif page >= 1620 and page <= 1651:
            if (page-1620) % 2 == 0:
                page_type = PAGE_TYPE.PAGE_MLC_LP
            else:
                page_type = PAGE_TYPE.PAGE_MLC_UP
            block_type = BLOCK_PAGE_TYPE.TLC_BLOCK_MLC_PAGE
        else:
            if page % 3 == 0:
                page_type = PAGE_TYPE.PAGE_TLC_LP
            elif page % 3 == 1:
                page_type = PAGE_TYPE.PAGE_TLC_UP
            else:
                page_type = PAGE_TYPE.PAGE_TLC_XP
            block_type = BLOCK_PAGE_TYPE.TLC_BLOCK_TLC_PAGE
    return page_type, block_type

def get_page_range_by_type(page_type :int)->int:
    page = 0
    if page_type == PAGE_TYPE.PAGE_POR_SSLC or page_type == PAGE_TYPE.PAGE_POR_DSLC or page_type == PAGE_TYPE.PAGE_PSA_SLC:
        page = random.randint(0, 1102)  # 有些 plane 的最後一個 page 是存 bitmap parity 不會轉 LBA
    else:
        logical_page_base   = [0, 1620, 1652, 3308]
        wl_base             = [0, 540, 556, 1108]
        wl_size             = [540, 16, 552, 3] #有些 plane 的最後一個 page 是存 bitmap parity 不會轉 LBA
        if(page_type == PAGE_TYPE.PAGE_SLC_LP):
            region_index = 3
            shared_page_num = 1
            offset = 0
        elif(page_type == PAGE_TYPE.PAGE_MLC_LP):
            region_index = 1
            shared_page_num = 2
            offset = 0
        elif(page_type == PAGE_TYPE.PAGE_MLC_UP):
            region_index = 1
            shared_page_num = 2
            offset = 1
        elif(page_type == PAGE_TYPE.PAGE_TLC_LP):
            region_index = random.choice([0,2])
            shared_page_num = 3
            offset = 0
        elif(page_type == PAGE_TYPE.PAGE_TLC_UP):
            region_index = random.choice([0,2])
            shared_page_num = 3
            offset = 1
        elif(page_type == PAGE_TYPE.PAGE_TLC_XP):
            region_index = random.choice([0,2])
            shared_page_num = 3
            offset = 2
        else:
            logger.error(f'unexpected value - page type ={page_type}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        
        wl_num = random.randint(0, wl_size[region_index]-1)
        page = logical_page_base[region_index]+wl_num*shared_page_num+offset
    return page

def issue_D014_to_set_read_recovery_module(die:int, bigIndex:int, smallIndex:int, nandMode:int, isSpeciBlock:int, block:int, isPSA:int, keep_error:bool = False) -> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D014_option_0()
    vu.b0_opcode.value = 0x14
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option.value = 0
    vu.dieId.value = die
    vu.bigIndex.value = bigIndex
    vu.smallIndex.value = smallIndex
    vu.nandMode.value = nandMode
    vu.isSpeciBlock.value = isSpeciBlock
    vu.block.value = block
    vu.isPSA.value = isPSA
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    return response

def issue_D014_to_en_dis_read_recovery_module(pageType:int, bigStepBitMap:int, smallStepBitMap:int, keep_error:bool = False)->CommandResponse:
    vu = micron_vu_D014_option_1()
    vu.b0_opcode.value = 0x14
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option.value = 1
    vu.pageType.value = pageType
    vu.bigStepBitMap.value = bigStepBitMap
    vu.smallStepBitMap.value = smallStepBitMap
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    return response

def issue_D014_to_set_last_table_content(die:int, pageType:int, tableIndex:int, offset1:int, offset2:int, offset3:int, keep_error:bool = False)-> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D014_option_2()
    vu.b0_opcode.value = 0x14
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option.value = 2
    vu.dieId.value = die
    vu.pageType.value = pageType
    vu.tableIndex.value = tableIndex
    vu.recipeType.value = 0
    vu.recipeContent.value = 0
    vu.offset1.value = offset1
    vu.offset2.value = offset2
    vu.offset3.value = offset3
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    return response

def issue_D014_to_en_dis_HRD_in_read_recovery_flow(isEnable:int, keep_error:bool = False)-> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D014_option_6()
    vu.b0_opcode.value = 0x14
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0x1000
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option.value = 6
    vu.autoSwitch.value = isEnable
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    return response

def issue_D014_to_alloc_release_codeword_buffer_to_save_REH_info(action:int, keep_error:bool = False)-> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D014_option_7()
    vu.b0_opcode.value = 0x14
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option.value = 7
    vu.action.value = action
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    return response

def issue_D014_to_set_nand_temperature(isEnable:int, temperature:int, keep_error:bool = False)-> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D014_option_8()
    vu.b0_opcode.value = 0x14
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option.value = 8
    vu.enable.value = isEnable
    vu.temperature.value = temperature
    response = send_no_data_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    return response

def issue_40F9_to_get_rr_number_and_error_bits(dieBitMap:int, planeBitMap:int, block:int, startPage:int, stopPage:int, isSLCBlock:int, isPSA:int, bin:int, fwBlock:int, keep_error:bool = False) -> tuple[CommandResponse, bytearray, int]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40F9()
    vu.b0_opcode.value = 0xF9
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.dieBitMap.value = dieBitMap
    vu.planeBitMap.value = planeBitMap
    vu.block.value = block
    vu.startPage.value = startPage
    vu.stopPage.value = stopPage
    vu.isSLCBlock.value = isSLCBlock
    vu.isPSA.value = isPSA
    vu.bin.value = bin
    vu.fwBlock.value = fwBlock
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    maxCount = int(4096 / len(rr_number_and_error_bits().payload))
    count = dieBitMap.bit_count() * planeBitMap.bit_count() * (stopPage - startPage +1)
    count = count if count < maxCount else maxCount
    length = count * len(rr_number_and_error_bits().payload)
    return response, payload[0:length], count

def issue_4014_to_get_read_recovery_info_read_last(die:int, pageType:int, tableIndex:int, keep_error:bool = False)-> tuple[CommandResponse, read_recovery_info_read_last]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4014_option_0()
    vu.b0_opcode.value = 0x14
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option.value = 0
    vu.die.value = die
    vu.pageType.value = pageType
    vu.lastTableIndex.value = tableIndex
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    _read_recovery_info_read_last = read_recovery_info_read_last(payload)
    return response, _read_recovery_info_read_last

def issue_4014_to_get_REH_tracing_info(die:int, keep_error:bool = False)-> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4014_option_1()
    vu.b0_opcode.value = 0x14
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option.value = 1
    vu.die.value = die
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    return response, payload

def issue_4014_to_get_ecc_result_for_all_step(die:int, keep_error:bool = False)-> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4014_option_2()
    vu.b0_opcode.value = 0x14
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option.value = 2
    vu.die.value = die
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    return response, payload[0:4096]

def issue_4014_to_get_sure_ARC_data(die:int, keep_error:bool = False)-> tuple[CommandResponse, bytearray]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_4014_option_5()
    vu.b0_opcode.value = 0x14
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.option.value = 5
    vu.die.value = die
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    return response, payload[0:498]

def issue_4014_to_get_HRD_triggering_information(keep_error:bool = False)-> tuple[CommandResponse, bytearray]:
    vu = micron_vu_4014_option_7()
    vu.b0_opcode.value = 0x14
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.d8_split_pkg_index.value = 0
    vu.option.value = 7
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error=keep_error)
    return response, payload[0:144]

def issue_409E_to_get_ECC_information(keep_error:bool = False) ->tuple[CommandResponse, int, int]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_409E()
    vu.b0_opcode.value = 0x9E
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.eccInfo.value = 0
    vu.eccType.value = 0
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    dumpfile('VU409E.bin', payload)
    _ecc_info = error_bit_number_of_last_reading(payload)
    return response, _ecc_info.errorBitNumber1.value, _ecc_info.errorBitNumber2.value

def issue_409E_to_get_error_bit_numbers(keep_error:bool = False) ->tuple[CommandResponse, error_bit_number_of_last_reading]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_409E()
    vu.b0_opcode.value = 0x9E
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.eccInfo.value = 1
    vu.eccType.value = 0
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    dumpfile('VU409E.bin', payload)
    _error_bit_number_of_last_reading = error_bit_number_of_last_reading(payload)
    return response, _error_bit_number_of_last_reading

def issue_40BB_to_get_error_bit_numbers_and_read_retry_step(die:int, keep_error:bool = False) ->tuple[CommandResponse, error_bit_number_and_read_retry_step]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_40BB()
    vu.b0_opcode.value = 0xBB
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.die.value = die
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    dumpfile('VU40BB.bin', payload)
    _error_bit_number_and_read_retry_step = error_bit_number_and_read_retry_step(payload)
    return response, _error_bit_number_and_read_retry_step

def issue_40BA_to_get_error_recovery_statistics(keep_error:bool = False) ->tuple[CommandResponse, error_recovery_statistics]:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vendor_cmd()
    vu.b0_opcode.value = 0xBA
    vu.b1_func.value = 0x40
    vu.w2_transfer_length.value = 4096
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    dumpfile('VU40BA.bin', payload)
    _error_recovery_statistics = error_recovery_statistics(payload)
    return response, _error_recovery_statistics

_ERROR_BY_STEPS: Dict[Tuple[int, int, int, int], ERROR_RECOVERY_STATISTICS_RECORD] = {
    (rec.big_step, rec.small_step, rec.isSLC, rec.isPSA): rec for rec in ERROR_RECOVERY_STATISTICS
}

def get_error_recovery_record_by_steps(big_step: int, small_step: int, isSLC:int , isPSA:int = 0) -> Optional[ERROR_RECOVERY_STATISTICS_RECORD]:
    record = _ERROR_BY_STEPS.get((big_step, small_step, isSLC, isPSA))
    if record is not None:
        return record
    # Don’t‑care (isSLC=2) 作為 fallback
    return _ERROR_BY_STEPS.get((big_step, small_step, 2, 0))

_ERROR_BY_INDEX: Dict[int, ERROR_RECOVERY_STATISTICS_RECORD] = {
    rec.index: rec for rec in ERROR_RECOVERY_STATISTICS
}
def get_error_recovery_record_by_index(idx: int) -> Optional[ERROR_RECOVERY_STATISTICS_RECORD]:
    return _ERROR_BY_INDEX.get(idx)

def get_error_number_info_record_by_steps(
    big_step: int,
    small_step: int,
    isSLC: int
) -> Optional[ERROR_NUMBER_INFORMATION_RECORD]:
    """
    依照 big_step、small_step、isSLC 從 ``ERROR_NUMBER_STEP`` 取得對應的記錄。

    1. 先找完全匹配的 (big_step, small_step, isSLC)。
    2. 若找不到，且 isSLC 為 2（Don’t‑care）或找不到完全匹配，則以
       ``isSLC == 2`` 為 fallback（不在意 SLC/TLC）。
    3. 若仍找不到，回傳 None。
    """
    for rec in ERROR_NUMBER_INFORMATION:
        if rec.big_step == big_step and rec.small_step == small_step and (rec.isSLC == isSLC or rec.isSLC == 2):
            return rec

    return None
def issue_D019_to_en_dis_success_read_count(isEnable: int, keep_error:bool = False)-> CommandResponse:
    _log.info(f"{inspect.currentframe().f_code.co_name}()")  # type: ignore
    vu = micron_vu_D019()
    vu.b0_opcode.value = 0x19
    vu.b1_func.value = 0xD0
    vu.w2_transfer_length.value = 0
    vu.d4_random_stamp.value = random.randint(0x1, 0xFFFFFFFF)
    vu.Flag.value = isEnable
    response, payload = send_data_in_vcmd(micron_vendor_cmd=vu, keep_error= keep_error)
    return response
