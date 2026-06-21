from importlib import import_module
from typing import TypeAlias, cast, List

from prettytable import PrettyTable

from Script.api import shared, cmd_seq as ExecuteCMD
from Script.api.cmd_seq.response import QueryResponse
from Script.api.ufs_api.descriptors.configuration_desc.structs import ConfigDescriptor, ConfigDescriptor310, ConfigDescriptor400, ConfigDescriptor410
from Script.api.ufs_api.defines import DescriptorIDN
from Script.api.exception import PATTERN_ASSERT_MODULE_NOT_FOUND, PATTERN_ASSERT_ATTR_NOT_FOUND
from Script.api.util.dut.dut import Dut

_log = shared.logger
_structs_path = 'Script.api.ufs_api.descriptors.configuration_desc.structs'

ConfigDescriptorUnion: TypeAlias = ConfigDescriptor310 | ConfigDescriptor400 | ConfigDescriptor410

def get_config_descriptors(print: bool=False) -> List[ConfigDescriptorUnion]:
    idn = DescriptorIDN.CONFIGURATION
    selector = 0x00
    cmd_idx_l = []
    for index in range(4):
        cmd = ExecuteCMD.ReadDescriptor()
        cmd.assign(idn, index, selector)
        cmd_index = ExecuteCMD.enqueue(cmd)
        cmd_idx_l.append(cmd_index)

    ExecuteCMD.send(clear_on_success=False)
    resp_l = [cast(QueryResponse, ExecuteCMD.read_response(i)) for i in cmd_idx_l]
    ExecuteCMD.clear()

    config_desc_name = f'ConfigDescriptor{Dut.get_instance().ufs_version:x}'
    config_desc_l = []
    for resp in resp_l:
        try:
            desc = getattr(import_module(_structs_path), config_desc_name)()
            desc.from_bytes(resp.data)
            config_desc_l.append(desc)
        except ModuleNotFoundError:
            _log.error(f"Module not found: {_structs_path}")
            raise PATTERN_ASSERT_MODULE_NOT_FOUND
        except AttributeError:
            _log.error(f"Attribute not found: {config_desc_name}")
            raise PATTERN_ASSERT_ATTR_NOT_FOUND

    if print:
        for idx, desc in enumerate(config_desc_l):
            print_config(desc, index=idx)

    return config_desc_l

def push_write_config(config_desc: ConfigDescriptorUnion, index: int, selector: int=0) -> None:
    cmd = ExecuteCMD.WriteDescriptor()
    cmd.assign(DescriptorIDN.CONFIGURATION, index, selector, config_desc.header.b0_length)
    cmd.set_desc(config_desc)
    ExecuteCMD.enqueue(cmd)

def print_config(config_desc: ConfigDescriptorUnion, index: int) -> None:
    # print header
    table = PrettyTable(header=False)
    table.title = f'Config Descriptor Header (Index={index})'
    table.align = 'l'
    keys = list(vars(config_desc.header).keys())
    vals = list(vars(config_desc.header).values())
    for i in range(0, len(keys), 3):
        table.add_row([f'{keys[i]} = 0x{vals[i]:x}', f'{keys[i+1]} = 0x{vals[i+1]:x}', f'{keys[i+2]} = 0x{vals[i+2]:x}'])
    table_str = table.get_string()
    for line in table_str.splitlines():
        _log.info(line)
    
    # print units
    for i in range(8):
        table = PrettyTable(header=False)
        table.title = f'Config Descriptor Unit{i} (LUN{index * 8 + i})'
        table.align = 'l'
        keys = list(vars(config_desc.units[i]).keys())
        vals = list(vars(config_desc.units[i]).values())
        for i in range(0, len(keys), 3):
            table.add_row([f'{keys[i]} = 0x{vals[i]:x}', f'{keys[i+1]} = 0x{vals[i+1]:x}', f'{keys[i+2]} = 0x{vals[i+2]:x}'])
        table_str = table.get_string()
        for line in table_str.splitlines():
            _log.info(line)
