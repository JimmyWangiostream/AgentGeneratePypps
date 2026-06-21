from importlib import import_module
from typing import TypeAlias, cast

from Script.api import shared, cmd_seq as ExecuteCMD
from Script.api.cmd_seq.response import QueryResponse
from Script.project_api.micron_health_report.structs import MicronHealthReport
from Script.api.exception import PATTERN_ASSERT_MODULE_NOT_FOUND, PATTERN_ASSERT_ATTR_NOT_FOUND
from Script.api.util.dut.dut import Dut
from Script.lib.sdk_lib.user.exception import DLL_CRC32_COMPARE_FAIL, DLL_PATTERN_2_ERROR, DLL_RESPONSE_ERROR
from Script.api.cmd_seq.response import QueryResponseUpiu, get_query_response_byte_str, get_cmd_response_byte_str, get_scsi_status_str, get_sense_key_str, get_asc_ascq_description



_log = shared.logger
_structs_path = 'Script.api.ufs_api.descriptors.device_health_desc.structs'



def get_micron_health_report(keep_error:bool = False) -> tuple[QueryResponse, MicronHealthReport]:
    idn = 0xF8
    index = 0x00
    selector = 0x00
    cmd = ExecuteCMD.ReadDescriptor()
    cmd.assign(idn, index, selector)
    cmd_index = ExecuteCMD.enqueue(cmd)
    try:
        ExecuteCMD.send(clear_on_success=False)
        response = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
    except DLL_RESPONSE_ERROR:
        if keep_error:
            response = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
            _log.warning(f"task_tag = {hex(response.upiu.b3_tasktag)},  response = {get_query_response_byte_str(response)}")
        else:
            raise DLL_RESPONSE_ERROR
    ExecuteCMD.clear()
    micron_health_report = MicronHealthReport(response.data)
    return response, micron_health_report
