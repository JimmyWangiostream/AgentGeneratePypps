from importlib import import_module
from typing import TypeAlias, cast

from Script.api import shared, cmd_seq as ExecuteCMD
from Script.api.cmd_seq.response import QueryResponse
from Script.api.ufs_api.descriptors.rpmb_unit_desc.structs import RPMBUnitDescriptor310, RPMBUnitDescriptor400, RPMBUnitDescriptor410
from Script.api.ufs_api.defines import DescriptorIDN
from Script.api.exception import PATTERN_ASSERT_MODULE_NOT_FOUND, PATTERN_ASSERT_ATTR_NOT_FOUND
from Script.api.util.dut.dut import Dut

_log = shared.logger
_structs_path = 'Script.api.ufs_api.descriptors.rpmb_unit_desc.structs'

RPMBUnitDescriptorUnion: TypeAlias = RPMBUnitDescriptor310 | RPMBUnitDescriptor400 | RPMBUnitDescriptor410

def get_rpmb_unit_descriptor() -> RPMBUnitDescriptorUnion:
    idn = DescriptorIDN.UNIT
    index = 0xC4
    selector = 0x00
    cmd = ExecuteCMD.ReadDescriptor()
    cmd.assign(idn, index, selector)
    cmd_index = ExecuteCMD.enqueue(cmd)

    ExecuteCMD.send(clear_on_success=False)
    resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
    ExecuteCMD.clear()

    desc_name = f'RPMBUnitDescriptor{Dut.get_instance().ufs_version:x}'
    try:
        desc = getattr(import_module(_structs_path), desc_name)()
        desc.from_bytes(resp.data)
    except ModuleNotFoundError:
        _log.error(f"Module not found: {_structs_path}")
        raise PATTERN_ASSERT_MODULE_NOT_FOUND
    except AttributeError:
        _log.error(f"Attribute not found: {desc_name}")
        raise PATTERN_ASSERT_ATTR_NOT_FOUND

    return desc  # type: ignore
