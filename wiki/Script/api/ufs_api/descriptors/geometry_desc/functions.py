from importlib import import_module
from typing import TypeAlias, cast

from Script.api import shared, cmd_seq as ExecuteCMD
from Script.api.cmd_seq.response import QueryResponse
from Script.api.ufs_api.descriptors.geometry_desc.structs import GeometryDescriptor310, GeometryDescriptor400, GeometryDescriptor410
from Script.api.ufs_api.defines.enum_define import DescriptorIDN, MaxNumberLUN
from Script.api.exception import SPEC_ASSERT_GEOMETRY_DESC_UNKNOWN_MAX_NUMBER_LUN, PATTERN_ASSERT_MODULE_NOT_FOUND, PATTERN_ASSERT_ATTR_NOT_FOUND
from Script.api.util.dut.dut import Dut

_log = shared.logger
_structs_path = 'Script.api.ufs_api.descriptors.geometry_desc.structs'

GeometryDescriptorUnion: TypeAlias = GeometryDescriptor310 | GeometryDescriptor400 | GeometryDescriptor410

def get_geometry_descriptor() -> GeometryDescriptorUnion:
    idn = DescriptorIDN.GEOMETRY
    index = 0x00
    selector = 0x00
    cmd = ExecuteCMD.ReadDescriptor()
    cmd.assign(idn, index, selector)
    cmd_index = ExecuteCMD.enqueue(cmd)

    ExecuteCMD.send(clear_on_success=False)
    resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
    ExecuteCMD.clear()

    desc_name = f'GeometryDescriptor{Dut.get_instance().ufs_version:x}'
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

def get_max_number_of_lun() -> int:
    desc = get_geometry_descriptor()
    try:
        max_num_lun_str = MaxNumberLUN(desc.b12_max_number_lu).name
        max_num_lun = int(max_num_lun_str.split("_")[-1])
    except ValueError:
        raise SPEC_ASSERT_GEOMETRY_DESC_UNKNOWN_MAX_NUMBER_LUN
    return max_num_lun
