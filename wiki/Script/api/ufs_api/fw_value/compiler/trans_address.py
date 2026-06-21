# type: ignore
import re
import os
import Script.api.ufs_api.fw_value.compiler.variable_declaration as vd
from Script.api.ufs_api.fw_value import config
from typing import Literal, Optional

class Parsing:
    def __init__(self):
        self.source = config.config_compiler_debug_info
        self.lines = []

        self.re_seek = re.compile(r'(?<=  )[0-9a-f]+(?::)')
        self.re_at_name = re.compile(r'(?<=DW_AT_name ).+')
        self.re_type = re.compile(r'DW_TAG_[_\w]+')

        self.type_main = vd.Main()
        self.tran = self.type_main.tran
        self.member = None
        return

    def load_data(self):
        if not os.path.exists(self.source):
            print('[SYS]: can not find file %s' % (self.source,))
            return False
        m_file = open(self.source, 'r')
        # self.data = m_file.read()
        self.lines = m_file.readlines()
        m_file.close()
        return True

    def get_seek(self, string):
        seeks = self.re_seek.findall(string)
        if seeks:
            return int(seeks[0], 16)
        else:
            print('[SYS]: get_seek error')
            print(string)
            return None

    def get_header_name(self, string):
        names = self.re_at_name.findall(string)
        if names:
            return names[0]
        else:
            print('[SYS]: get_header_name fail')
            print(string)
            return None

    def get_types(self):
        if not self.load_data():
            return None
        self.type_main.p.lines = self.lines
        self.type_main.p.length = len(self.lines)
        self.member = self.type_main.get_types()
        return self.member

    def get_add_seq(self, v_name) -> Optional[vd.AddSeq]:
        if not self.member:
            if not self.get_types():
                return None
        v_name = v_name.replace('[', '.[')  # 将index作为一个元素来解析
        name_list = v_name.replace('->', '.').split('.')
        type_seq = vd.AddSeq()
        if self.type_main.p.var_dic[name_list[0]].dw_tag == 'variable':
            if self.type_main.variable.get_add(type_seq, name_list):
                # type_seq.print_seq()
                return type_seq
        else:
            if self.type_main.constant.get_add(type_seq, name_list):
                # type_seq.print_seq()
                return type_seq
        return None

    def init_by_buffer(self, name='', buf: bytearray = None):
        if not self.member:
            if not self.get_types():
                return None
        data = self.member.struct_dic[name]
        source = vd.ValueSource()
        source.buf = buf
        data = self.tran.get_compiler(data).set_value(data, source)
        return data

    def enum_value(self, name):
        data = self.type_main.p.enum_dic[name]
        return data.const_value


address_set: Parsing
if __name__ == '__main__':
    address_set = Parsing()
    address_set.get_types()
    add_seq = address_set.get_add_seq('gFtlApiStruct->page_table.l2_max_node_num[1][1]')
    for item in add_seq.seq:
        if item.is_pointer:
            pass
        add_seq.address = item.base_add + item.shift
    print('0x%08x' % add_seq.address)
    print(address_set.member.struct_dic['mmc_api_struct'].member_dic.items())
else:
    address_set = Parsing()
