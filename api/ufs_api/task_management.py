from typing import List, cast
from Script.api import shared
import Script.api.cmd_seq as ExecuteCMD
from Script.api.cmd_seq.response import CmdSeqTaskMgmtDummyResponse, TaskMgmtResponse
from Script.api.exception import PATTERN_ASSERT_INDEX_NOT_FOUND_IN_CMD_LIST, PATTERN_ASSERT_TASK_MANAG_INVALID_TARGET
from Script.api.ufs_api.defines.enum_define import TaskManagementFunction, TaskMgmtServiceResponse
from Script.api.ufs_api.upiu import structs

_log = shared.logger

def push_abort_task(target_idx: int) -> int:
    """
    target_idx: The index of the target to be aborted in cmd_list.  
    return val: The index of task management request in cmd_list.
    """
    try:
        target = ExecuteCMD._cmd_list[target_idx]
    except IndexError:
        _log.error('Invalid task management abort target index. Not found in cmd_list.')
        raise PATTERN_ASSERT_INDEX_NOT_FOUND_IN_CMD_LIST
    if not isinstance(target.upiu, structs.CommandUpiu):
        _log.error(f'Invalid task management abort target. CMD={type(target)}. Expect SCSI Command.')
        raise PATTERN_ASSERT_TASK_MANAG_INVALID_TARGET
    
    target_lun = target.upiu.b2_lun
    target_tasktag = target.upiu.b3_tasktag
    target_iid = target.upiu.b4_iid
    tm = ExecuteCMD.TaskManagement()
    tm.assign(lun=target_lun, iid=target_iid, task_management_function=TaskManagementFunction.ABORT_TASK,
                target_lun=target_lun, target_tasktag=target_tasktag, target_iid=target_iid)
    return ExecuteCMD.enqueue(tm)

def push_query_task(target_idx: int) -> int:
    """
    target_idx: The index of the target to be query in cmd_list.  
    return val: The index of task management request in cmd_list.
    """
    try:
        target = ExecuteCMD._cmd_list[target_idx]
    except IndexError:
        _log.error('Invalid task management query target index. Not found in cmd_list.')
        raise PATTERN_ASSERT_INDEX_NOT_FOUND_IN_CMD_LIST
    if not isinstance(target.upiu, (structs.CommandUpiu, structs.TaskMngmtRequestUpiu)):
        _log.error(f'Invalid task management abort target. CMD={type(target)}. Expect SCSI Command.')
        raise PATTERN_ASSERT_TASK_MANAG_INVALID_TARGET
    
    target_lun = target.upiu.b2_lun
    target_tasktag = target.upiu.b3_tasktag
    target_iid = target.upiu.b4_iid
    tm = ExecuteCMD.TaskManagement()
    tm.assign(lun=target_lun, iid=target_iid, task_management_function=TaskManagementFunction.QUERY_TASK,
                target_lun=target_lun, target_tasktag=target_tasktag, target_iid=target_iid)
    return ExecuteCMD.enqueue(tm)

def check_if_target_is_aborted(target_idx: int, tm_abort_idx: int) -> bool:
    """
    target_idx: The index of the target to be aborted in cmd_list.  
    tm_abort_idx: The index of the task management abort in cmd_list.  
    return val: Whether target is aborted or not.
    """
    is_aborted = True
    try:
        target = ExecuteCMD._cmd_list[target_idx]
    except IndexError:
        _log.error('Invalid abort target index. Not found in cmd_list.')
        raise PATTERN_ASSERT_INDEX_NOT_FOUND_IN_CMD_LIST
    try:
        ExecuteCMD._cmd_list[tm_abort_idx]
    except IndexError:
        _log.error('Invalid task management upiu index. Not found in cmd_list.')
        raise PATTERN_ASSERT_INDEX_NOT_FOUND_IN_CMD_LIST
    
    rsp = cast(TaskMgmtResponse, ExecuteCMD.read_response(tm_abort_idx))
    if rsp.upiu.l12_output_parameter1 != TaskMgmtServiceResponse.FUNC_COMPLETE:
        _log.warning(f'Task Management Service Response Not Complete. '
                     f'Service Response = {TaskMgmtServiceResponse(rsp.upiu.l12_output_parameter1)}')
        is_aborted = False
    
    if not isinstance(target.upiu, structs.CommandUpiu):
        _log.error(f'Invalid task management abort target. CMD={type(target)}. Expect SCSI Command.')
        raise PATTERN_ASSERT_TASK_MANAG_INVALID_TARGET
    
    target_lun = target.upiu.b2_lun
    target_tasktag = target.upiu.b3_tasktag
    target_iid = target.upiu.b4_iid
    target_rsp = ExecuteCMD.read_response(target_idx)
    if isinstance(target_rsp, CmdSeqTaskMgmtDummyResponse):
        _log.warning(f'Target CMD ({target_lun=}, {target_tasktag=}, {target_iid=}) is aborted. Aborted task tag time stamp = {target_rsp.l59_abort_timestamp} us')
    else:
        _log.warning(f'Target CMD ({target_lun=}, {target_tasktag=}, {target_iid=}) is NOT aborted. '
                    f'Found Response in cmd list')
        is_aborted = False
    
    return is_aborted

def check_if_query_succeeded(tm_query_idx: int) -> bool:
    """
    tm_query_idx: Index of Task Mangement Query Task / Query Task Set in cmd_list.  
    return value: Whether query succeeded or not.
    """
    is_succeeded = True
    try:
        ExecuteCMD._cmd_list[tm_query_idx]
    except IndexError:
        _log.error('Invalid task management upiu index. Not found in cmd_list.')
        raise PATTERN_ASSERT_INDEX_NOT_FOUND_IN_CMD_LIST
    
    rsp = cast(TaskMgmtResponse, ExecuteCMD.read_response(tm_query_idx))
    if rsp.upiu.l12_output_parameter1 != TaskMgmtServiceResponse.FUNC_SUCCEEDED:
        _log.warning(f'Task Management Service Response Not Succeeded. '
                     f'Service Response = {TaskMgmtServiceResponse(rsp.upiu.l12_output_parameter1)}')
        is_succeeded = False

    return is_succeeded