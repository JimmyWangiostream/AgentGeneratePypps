from importlib import import_module
from typing import TypeAlias, cast

from Script.api import shared, cmd_seq as ExecuteCMD
from Script.api.cmd_seq.response import QueryResponse
from Script.api.ufs_api.descriptors.product_rev_level_str_desc.structs import ProductRevisionLevelStringDescriptor310, ProductRevisionLevelStringDescriptor400, ProductRevisionLevelStringDescriptor410
from Script.api.ufs_api.defines import DescriptorIDN
from Script.api.exception import PATTERN_ASSERT_MODULE_NOT_FOUND, PATTERN_ASSERT_ATTR_NOT_FOUND
from Script.api.util.dut.dut import Dut

_log = shared.logger
_structs_path = 'Script.api.ufs_api.descriptors.product_rev_level_str_desc.structs'

ProductRevisionLevelStringDescriptorUnion: TypeAlias = ProductRevisionLevelStringDescriptor310 | ProductRevisionLevelStringDescriptor400 | ProductRevisionLevelStringDescriptor410

def get_product_revision_level_string_descriptor(product_revision_level: int) -> ProductRevisionLevelStringDescriptorUnion:
    idn = DescriptorIDN.STRING
    index = product_revision_level
    selector = 0x00
    cmd = ExecuteCMD.ReadDescriptor()
    cmd.assign(idn, index, selector)
    cmd_index = ExecuteCMD.enqueue(cmd)

    ExecuteCMD.send(clear_on_success=False)
    resp = cast(QueryResponse, ExecuteCMD.read_response(cmd_index))
    ExecuteCMD.clear()

    desc_name = f'ProductRevisionLevelStringDescriptor{Dut.get_instance().ufs_version:x}'
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
