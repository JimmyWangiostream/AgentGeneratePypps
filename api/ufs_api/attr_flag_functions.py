from typing import Tuple, cast
from Script.api.cmd_seq.response import QueryResponse
from Script.api.exception import SPEC_ASSERT_UFS_RSP_IDN_NOT_MATCH, SPEC_ASSERT_UFS_RSP_IDX_NOT_MATCH, SPEC_ASSERT_UFS_RSP_SELECTOR_NOT_MATCH, SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
from Script.api.ufs_api.defines.enum_define import AttributeIDN, FlagIDN, QueryFunctionOpcode
import Script.api.shared as shared
from Script.api import cmd_seq as ExecuteCMD

_log = shared.logger

def parse_read_attr_rsp(rsp: QueryResponse) -> Tuple[int, int, int, int]:
    """
    return: idn, index, selector, val  
      
    idn, index, selector, val = parse_read_attr_rsp(rsp)
    """
    idn = rsp.upiu.u12_specific_fields[1]
    index = rsp.upiu.u12_specific_fields[2]
    selector = rsp.upiu.u12_specific_fields[3]
    val = int.from_bytes(rsp.upiu.u12_specific_fields[4:12])

    try:
        qry_func = QueryFunctionOpcode(rsp.upiu.u12_specific_fields[0]).name
    except ValueError:
        _log.warning(f'Undefined Query Function Opcode: 0x{rsp.upiu.u12_specific_fields[0]:x}')
        qry_func = f'Query Function Opcode({rsp.upiu.u12_specific_fields[0]})'

    try:
        idn_enum = f'{AttributeIDN(rsp.upiu.u12_specific_fields[1]).name}({rsp.upiu.u12_specific_fields[1]})'
    except ValueError:
        _log.warning(f'Undefined Attribute IDN: 0x{rsp.upiu.u12_specific_fields[1]:x}')
        idn_enum = f'Attr IDN({rsp.upiu.u12_specific_fields[1]})'

    _log.info(f'{qry_func} = {idn_enum}, AttrValue = {val}, Index = {index}, Selector = {selector}')

    return idn, index, selector, val

def parse_flag_rsp(rsp: QueryResponse) -> Tuple[int, int, int, int]:
    """
    return: idn, index, selector, val  
      
    idn, index, selector, val = parse_flag_rsp(rsp)
    """
    idn = rsp.upiu.u12_specific_fields[1]
    index = rsp.upiu.u12_specific_fields[2]
    selector = rsp.upiu.u12_specific_fields[3]
    val = rsp.upiu.u12_specific_fields[11]

    try:
        qry_func = QueryFunctionOpcode(rsp.upiu.u12_specific_fields[0]).name
    except ValueError:
        _log.warning(f'Undefined Query Function Opcode: 0x{rsp.upiu.u12_specific_fields[0]:x}')
        qry_func = f'Query Function Opcode({rsp.upiu.u12_specific_fields[0]})'

    try:
        idn_enum = f'{FlagIDN(rsp.upiu.u12_specific_fields[1]).name}({rsp.upiu.u12_specific_fields[1]})'
    except ValueError:
        _log.warning(f'Undefined FlagIDN: 0x{rsp.upiu.u12_specific_fields[1]:x}')
        idn_enum = f'Flag IDN({rsp.upiu.u12_specific_fields[1]})'

    _log.info(f'{qry_func} = {idn_enum}, FlagValue = {val}, Index = {index}, Selector = {selector}')

    return idn, index, selector, val

def read_attribute(idn: int, index: int=0, selector: int=0) -> int:
    """
    return: value
    """
    read_attr = ExecuteCMD.ReadAttribute().assign(idn=idn, index=index, selector=selector).enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = cast(QueryResponse, ExecuteCMD.read_response(read_attr))
    ExecuteCMD.clear()
    ret_idn, ret_index, ret_selector, ret_val = parse_read_attr_rsp(rsp)
    if ret_idn != idn:
        raise SPEC_ASSERT_UFS_RSP_IDN_NOT_MATCH
    if ret_index != index:
        raise SPEC_ASSERT_UFS_RSP_IDX_NOT_MATCH
    if ret_selector != selector:
        raise SPEC_ASSERT_UFS_RSP_SELECTOR_NOT_MATCH

    return ret_val

def write_attribute(idn: int, val: int, index: int=0, selector: int=0) -> None:
    write_attr = ExecuteCMD.WriteAttribute().assign(idn=idn, index=index, selector=selector).set_attr(val).enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = cast(QueryResponse, ExecuteCMD.read_response(write_attr))
    ExecuteCMD.clear()
    ret_idn, ret_index, ret_selector, ret_val = parse_read_attr_rsp(rsp)
    if ret_idn != idn:
        raise SPEC_ASSERT_UFS_RSP_IDN_NOT_MATCH
    if ret_index != index:
        raise SPEC_ASSERT_UFS_RSP_IDX_NOT_MATCH
    if ret_selector != selector:
        raise SPEC_ASSERT_UFS_RSP_SELECTOR_NOT_MATCH
    if ret_val != val:
        raise SPEC_ASSERT_UFS_RSP_VALUE_NOT_MATCH
    
def read_flag(idn: int, index: int=0, selector: int=0) -> int:
    """
    return: value
    """
    cmd_idx = ExecuteCMD.ReadFlag().assign(idn=idn, index=index, selector=selector).enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = cast(QueryResponse, ExecuteCMD.read_response(cmd_idx))
    ret_idn, ret_index, ret_selector, ret_val = parse_flag_rsp(rsp)
    if ret_idn != idn:
        raise SPEC_ASSERT_UFS_RSP_IDN_NOT_MATCH
    if ret_index != index:
        raise SPEC_ASSERT_UFS_RSP_IDX_NOT_MATCH
    if ret_selector != selector:
        raise SPEC_ASSERT_UFS_RSP_SELECTOR_NOT_MATCH
    ExecuteCMD.clear()

    return ret_val

def set_flag(idn: int, index: int=0, selector: int=0) -> int:
    """
    return: value
    """    
    cmd_idx = ExecuteCMD.SetFlag().assign(idn=idn, index=index, selector=selector).enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = cast(QueryResponse, ExecuteCMD.read_response(cmd_idx))
    ret_idn, ret_index, ret_selector, ret_val = parse_flag_rsp(rsp)
    if ret_idn != idn:
        raise SPEC_ASSERT_UFS_RSP_IDN_NOT_MATCH
    if ret_index != index:
        raise SPEC_ASSERT_UFS_RSP_IDX_NOT_MATCH
    if ret_selector != selector:
        raise SPEC_ASSERT_UFS_RSP_SELECTOR_NOT_MATCH
    ExecuteCMD.clear()

    return ret_val

def clear_flag(idn: int, index: int=0, selector: int=0) -> int:
    """
    return: value
    """    
    cmd_idx = ExecuteCMD.ClearFlag().assign(idn=idn, index=index, selector=selector).enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = cast(QueryResponse, ExecuteCMD.read_response(cmd_idx))
    ret_idn, ret_index, ret_selector, ret_val = parse_flag_rsp(rsp)
    if ret_idn != idn:
        raise SPEC_ASSERT_UFS_RSP_IDN_NOT_MATCH
    if ret_index != index:
        raise SPEC_ASSERT_UFS_RSP_IDX_NOT_MATCH
    if ret_selector != selector:
        raise SPEC_ASSERT_UFS_RSP_SELECTOR_NOT_MATCH
    ExecuteCMD.clear()

    return ret_val

def toggle_flag(idn: int, index: int=0, selector: int=0) -> int:
    """
    return: value
    """    
    cmd_idx = ExecuteCMD.ToggleFlag().assign(idn=idn, index=index, selector=selector).enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = cast(QueryResponse, ExecuteCMD.read_response(cmd_idx))
    ret_idn, ret_index, ret_selector, ret_val = parse_flag_rsp(rsp)
    if ret_idn != idn:
        raise SPEC_ASSERT_UFS_RSP_IDN_NOT_MATCH
    if ret_index != index:
        raise SPEC_ASSERT_UFS_RSP_IDX_NOT_MATCH
    if ret_selector != selector:
        raise SPEC_ASSERT_UFS_RSP_SELECTOR_NOT_MATCH
    ExecuteCMD.clear()

    return ret_val

