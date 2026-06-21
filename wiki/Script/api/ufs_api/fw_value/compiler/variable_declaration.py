# type: ignore
import re
import copy


class Parameter:
    def __init__(self):
        self.machine = 'Unknown'
        self.is_arm = True
        self.pointer_size = 4
        self.lines = []
        self.row = 0
        self.class_dic = None
        self.type_dic = {}
        self.length = 0
        self.unit_member = []
        self.var_dic = {}  # 快速找到某个全局变量
        self.enum_dic = {}
        self.struct_dic = {}
        self.union_dic = {}
        self.array_list = []

    def cur_line(self):
        return self.lines[self.row]


class AddSeq:
    class Item:
        def __init__(self):
            self.is_pointer = False
            self.base_add = 0x00000000
            self.shift = 0

        def print_item(self):
            print('\tis_pointer = %s' % (str(self.is_pointer),))
            print('\tbase_add = 0x%08x' % (self.base_add,))
            print('\tshift = %d' % (self.shift,))

    def __init__(self):
        self.pointer_size = 4  # 固定参数， CPU位数
        self.multiple = 0  # 数组类型的偏移倍数
        self.curr_item = None
        self.seq = []
        self.type_data = None
        self.type_list = []
        self.value_size = 0  # 最终读取的数据长度
        self.bit_mask = []  # union 类型的bit范围
        self.get_array_type = False  # 继续寻找array的元素类型
        self.address = 0x00000000  # 最终的地址
        self.is_constant = False  # For ARC
        self.constant_value = 0  # For ARC

    def add_shift(self, shift):
        self.curr_item.shift += shift

    def add_multiple(self, item_size):
        self.value_size = item_size
        self.curr_item.shift += item_size * self.multiple
        self.multiple = 0  # clear array multiple

    def new_item(self, is_pointer):
        self.curr_item = self.Item()
        self.curr_item.is_pointer = is_pointer
        self.seq.append(self.curr_item)

    def print_seq(self):
        print('pointer_size = %d' % (self.pointer_size,))
        print('multiple = %d' % (self.multiple,))
        print('value_size = %d' % (self.value_size,))
        print('bit_mask = %s' % (str(self.bit_mask),))
        for item in self.seq:
            item.print_item()
        for t in self.type_list:
            print('%s = %06x' % (t.dw_tag, t.key))



class ValueSource:
    def __init__(self):
        self.buf = None
        self.pointer = 0


class Translate:
    class Data:
        def __init__(self):
            self.dw_tag = 'translate'

    def __init__(self, p: Parameter()):
        self.re_type = re.compile('DW_TAG_[_\w]+')
        self.re_key = re.compile(r'(?<= {2})[0-9a-f]+(?::)')
        self.re_deep = re.compile(r'(?<= {2}[0-9a-f]{6}:) +')
        self.re_num_16 = re.compile(r'(?<=0x)[a-fA-F0-9]+')

        self.re_DW_AT_name = re.compile(r'(?<=DW_AT_name ).+')
        self.re_DW_AT_byte_size = re.compile(r'(?<=DW_AT_byte_size 0x)[a-fA-F0-9]+')
        self.re_DW_AT_type = re.compile(r' DW_AT_type ')
        self.re_DW_AT_location = re.compile(r' DW_AT_location ')
        self.re_DW_AT_external = re.compile(r'(?<=DW_AT_external 0x)[a-fA-F0-9]+')
        self.re_DW_AT_count = re.compile(r'(?<=DW_AT_count 0x)[a-fA-F0-9]+')
        self.re_DW_AT_upper_bound = re.compile(r'(?<=DW_AT_upper_bound 0x)[a-fA-F0-9]+')
        self.re_DW_AT_data_member_location = re.compile(r'(?<=DW_AT_data_member_location 0x)[a-fA-F0-9]+')
        self.re_DW_AT_plus_uconst = re.compile(r'(?<=DW_OP_plus_uconst )\d+')
        self.re_DW_AT_bit_size = re.compile(r'(?<=DW_AT_bit_size 0x)[a-fA-F0-9]+')
        self.re_DW_AT_bit_offset = re.compile(r'(?<=DW_AT_bit_offset 0x)[a-fA-F0-9]+')
        self.re_DW_AT_const_value = re.compile(r'(?<=DW_AT_const_value 0x)[a-fA-F0-9]+')

        self.p = p

    def get_compiler(self, data):
        next_type_dw_tag = 'DW_TAG_' + data.dw_tag
        return self.p.class_dic[next_type_dw_tag]

    def get_add(self, type_seq, item_list):
        data = self.Data()
        print('[SYS]: %s no query function' % (data.dw_tag,))
        return False

    def set_value(self, data, source: ValueSource):
        data = self.Data()
        print('[SYS]: %s no query function' % (data.dw_tag,))
        return False

    def get_sub_size(self, data):
        if hasattr(data, 'byte_size'):
            return data.byte_size
        type_data = self.p.type_dic[data.type]
        return self.get_compiler(type_data).get_sub_size(type_data)

    def get_sub_define(self, data):
        if data.dw_tag in ['array_type', 'variable', 'pointer_type', 'structure_type', 'union_type', 'base_type']:
            return data
        type_data = self.p.type_dic[data.type]
        return self.get_compiler(type_data).get_sub_define(type_data)

    def get_key(self):
        line = self.p.cur_line()
        key = -1
        try:
            if line[8] == ':':
                key = int(line[2:8], 16)
        except:
            print('key error')
            print(line)
        return key

    def get_deep(self):
        deep = self.re_deep.findall(self.p.cur_line())
        if deep:
            return len(deep[0])
        return -1

    def get_type_name(self):
        m_type = self.re_type.findall(self.p.cur_line())
        if m_type:
            return m_type[0]
        else:
            return None

    def get_dw_at_name(self):
        name = self.re_DW_AT_name.findall(self.p.cur_line())
        if name:
            return name[0]
        else:
            return ''

    def get_dw_at_byte_size(self):
        byte_size = self.re_DW_AT_byte_size.findall(self.p.cur_line())
        if byte_size:
            return int(byte_size[0], 16)
        else:
            return 0

    def get_dw_at_type(self):
        if self.re_DW_AT_type.findall(self.p.cur_line()):
            key = self.re_num_16.findall(self.p.cur_line())
            if key:
                return int(key[-1], 16)  # 有些type中只有一个数字， 暂不清楚一个数字是何含义
            else:
                print('Error: get_dw_at_type,', end=' ')
                print(self.p.cur_line())
                return 0

    def get_dw_at_location(self):
        if self.re_DW_AT_location.findall(self.p.cur_line()):
            return self.p.cur_line().split('DW_AT_location ')[1]
        else:
            return ''

    def get_dw_at_external(self):
        external = self.re_DW_AT_external.findall(self.p.cur_line())
        if external:
            return int(external[0], 16)
        else:
            return 0

    def get_dw_at_count(self):
        if self.p.is_arm:
            count = self.re_DW_AT_count.findall(self.p.cur_line())
            if count:
                return int(count[0], 16)
        else:
            count = self.re_DW_AT_upper_bound.findall(self.p.cur_line())
            if count:
                return int(count[0], 16) + 1
        return 0

    def get_dw_at_data_member_location(self):
        if self.p.is_arm:
            location = self.re_DW_AT_data_member_location.findall(self.p.cur_line())
            if location:
                return int(location[0], 16)
        else:
            location = self.re_DW_AT_plus_uconst.findall(self.p.cur_line())
            if location:
                return int(location[0])
        return 0

    def get_dw_at_bit_size(self):
        bit_size = self.re_DW_AT_bit_size.findall(self.p.cur_line())
        if bit_size:
            return int(bit_size[0], 16)
        else:
            return 0

    def get_dw_at_bit_offset(self):
        offset = self.re_DW_AT_bit_offset.findall(self.p.cur_line())
        if offset:
            return int(offset[0], 16)
        else:
            return 0

    def get_dw_at_const_value(self):
        value = self.re_DW_AT_const_value.findall(self.p.cur_line())
        if value:
            return int(value[0], 16)
        else:
            return 0

    def get_add_from_location(self, location):
        add = self.re_num_16.findall(location)
        if not add:
            print('[SYS]: location error->%s' % (location,))
            return 0
        else:
            add = add[-1]
        return int(add, 16)


class CompileUnit(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'compile_unit'
            self.symbol = 'compile_unit'
            self.name = ''
            self.member = []

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.name:
                type_data.name = self.get_dw_at_name()
                if type_data.name:
                    continue
            if deep >= self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                member = self.p.class_dic[new_type].get_type()
                if member:
                    type_data.member.append(member)

        return type_data


class Variable(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'variable'
            self.symbol = 'variable'
            self.name = ''
            self.type = 0
            self.location = ''
            self.external = 0

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        # self.p.type_dic[type_data.key] = type_data  # variable?
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.name:
                type_data.name = self.get_dw_at_name()
                if type_data.name:
                    self.p.var_dic[type_data.name] = type_data
                    continue

            if not type_data.type:
                type_data.type = self.get_dw_at_type()
                if type_data.type:
                    continue

            if not type_data.location:
                type_data.location = self.get_dw_at_location()
                if type_data.location:
                    continue

            if not type_data.external:
                type_data.external = self.get_dw_at_external()
                if type_data.external:
                    continue

            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                print('Error: Variable, should not new type')

        return type_data

    def get_add(self, type_seq: AddSeq, item_list):
        if not item_list:
            return True
        type_seq.new_item(False)  # variable type, create new address base
        try:
            item_data = self.p.var_dic[item_list[0]]
            type_seq.curr_item.base_add = self.get_add_from_location(item_data.location)
        except KeyError:
            print('[SYS]: can not find %s in variable dic' % (item_list[0],))
            return False

        type_seq.type_list.append(item_data)
        type_seq.type_data = self.p.type_dic[item_data.type]
        next_type_dw_tag = 'DW_TAG_' + type_seq.type_data.dw_tag
        return self.p.class_dic[next_type_dw_tag].get_add(type_seq, item_list[1:])

    def set_value(self, data, source: ValueSource):
        type_data = self.p.type_dic[data.type].type_data
        next_type_dw_tag = 'DW_TAG_' + type_data.dw_tag
        return self.p.class_dic[next_type_dw_tag].set_value(type_data, source)


class Constant(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'constant'
            self.symbol = 'variable'
            self.name = ''
            self.const_value = 0
            self.type = 0
            self.location = ''
            self.external = 0

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        # self.p.type_dic[type_data.key] = type_data  # variable?
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.name:
                type_data.name = self.get_dw_at_name()
                if type_data.name:
                    self.p.var_dic[type_data.name] = type_data
                    continue

            if not type_data.type:
                type_data.type = self.get_dw_at_type()
                if type_data.type:
                    continue

            if not type_data.const_value:
                type_data.const_value = self.get_dw_at_const_value()
                if type_data.const_value:
                    continue

            if not type_data.location:
                type_data.location = self.get_dw_at_location()
                if type_data.location:
                    continue

            if not type_data.external:
                type_data.external = self.get_dw_at_external()
                if type_data.external:
                    continue

            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                print('Error: Variable, should not new type')

        return type_data

    def get_add(self, type_seq: AddSeq, item_list):
        if not item_list:
            return True
        type_seq.new_item(False)  # variable type, create new address base
        type_seq.is_constant = True
        try:
            item_data = self.p.var_dic[item_list[0]]
        except KeyError:
            print('[SYS]: can not find %s in variable dic' % (item_list[0],))
            return False
        type_seq.constant_value = item_data.const_value
        type_seq.type_list.append(item_data)
        type_seq.type_data = self.p.type_dic[item_data.type]
        return True

    def set_value(self, data, source: ValueSource):
        type_data = self.p.type_dic[data.type].type_data
        next_type_dw_tag = 'DW_TAG_' + type_data.dw_tag
        return self.p.class_dic[next_type_dw_tag].set_value(type_data, source)


class ArrayType(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'array_type'
            self.symbol = 'array'
            self.key = 0
            self.type = 0
            self.sub = []
            self.items = []

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_index(self, item):
        index = item.split('[')[1].split(']')[0]
        if '0x' in index:
            index = int(index.replace('0x', ''), 16)
        else:
            index = int(index)
        return index

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.type:
                type_data.type = self.get_dw_at_type()
                if type_data.type:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break
            new_type = self.get_type_name()
            if new_type:
                if new_type != 'DW_TAG_subrange_type':
                    print('Error: ArrayType, get error type')
                    break
                type_data.sub.append(self.p.class_dic[new_type].get_type())
        self.p.array_list.append(type_data)
        return type_data

    def get_add(self, type_seq: AddSeq, item_list):
        item_data = type_seq.type_data
        index_0 = 0
        index_1 = 0
        max_cnt_0 = 0
        max_cnt_1 = 0
        calculate_items = 0
        if not (item_list and '[' in item_list[0]):
            if len(item_list) > 1:
                print('[SYS]: %s lost index' % (item_list[0],))
                return False
            else:  # 访问数组首地址
                item_list = ['[0]']  # 向下寻找元素类型
                type_seq.get_array_type = True
        if len(item_data.sub) == 2:
            if len(item_list) >= 2 and '[' in item_list[1]:  # 二维数组
                max_cnt_0 = item_data.sub[0].count
                index_0 = self.get_index(item_list[0])
                max_cnt_1 = item_data.sub[1].count
                index_1 = self.get_index(item_list[1])
                if index_0 >= max_cnt_0 or index_1 >= max_cnt_1:
                    print('[SYS]: index = [%d][%d] > max index = [%d][%d]' %
                          (index_0, index_1, max_cnt_0, max_cnt_1))
                    return False
                calculate_items = 2
            else:  # 二维数组中的第一维数组
                max_cnt_0 = item_data.sub[0].count
                max_cnt_1 = item_data.sub[1].count
                index_0 = self.get_index(item_list[0])
                if index_0 >= max_cnt_0:
                    print('[SYS]: index = %d > max index = %d' % (index_0, max_cnt_0))
                    return False
                calculate_items = 1
        else:
            max_cnt_1 = item_data.sub[0].count
            index_1 = self.get_index(item_list[0])
            if index_1 >= max_cnt_1:
                print('[SYS]: index = %d > max index = %d' % (index_1, max_cnt_1))
                return False
            calculate_items = 1

        type_seq.multiple += index_0 * max_cnt_1 + index_1  # 兼容一维和二维数组
        type_seq.type_list.append(item_data)
        type_seq.type_data = self.p.type_dic[item_data.type]
        next_type_dw_tag = 'DW_TAG_' + type_seq.type_data.dw_tag
        if not item_list:
            return True
        return self.p.class_dic[next_type_dw_tag].get_add(type_seq, item_list[calculate_items:])

    def set_value(self, data, source: ValueSource):
        new_data = copy.deepcopy(data)
        type_data = self.p.type_dic[new_data.type]
        sub_define = self.get_sub_define(type_data)
        sub_size = self.get_sub_size(type_data)
        new_data.items = []
        for sub in new_data.sub:
            temp_items = []
            for i in range(sub.count):
                temp_pointer = source.pointer
                temp_items.append(self.get_compiler(sub_define).set_value(sub_define, source))
                source.pointer = temp_pointer + sub_size  # alignment
            new_data.items.append(temp_items)
        return new_data


class SubrangeType(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'subrange_type'
            self.symbol = 'subrange'
            self.key = 0
            self.type = 0
            self.count = 0

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.type:
                type_data.type = self.get_dw_at_type()
                if type_data.type:
                    continue

            if not type_data.count:
                type_data.count = self.get_dw_at_count()
                if type_data.count:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break
            new_type = self.get_type_name()
            if new_type:
                print('Error: SubrangeType, get error type')
                print(type_data.key)
                break
        return type_data


class Pointer(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'pointer_type'
            self.symbol = '*'
            self.key = 0
            self.type = ''
            self.byte_size = 4

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_index(self, item):
        index = item.split('[')[1].split(']')[0]
        if '0x' in index:
            index = int(index.replace('0x', ''), 16)
        else:
            index = int(index)
        return index

    def get_type(self):
        type_data = self.Data()
        type_data.byte_size = self.p.pointer_size
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.type:
                type_data.type = self.get_dw_at_type()
                if type_data.type:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break
            new_type = self.get_type_name()
            if new_type:
                print('Error: Pointer, get error type')
                print(type_data.key)
                break
        return type_data

    def get_add(self, type_seq: AddSeq, item_list):
        type_seq.add_multiple(type_seq.pointer_size)
        type_seq.new_item(True)  # pointer type, create new address base

        item_data = type_seq.type_data

        if item_list and '[' in item_list[0]:
            index = self.get_index(item_list[0])
            type_seq.multiple = index
            item_list = item_list[1:]

        type_seq.type_list.append(item_data)
        if not item_data.type:  # void type
            type_seq.add_multiple(type_seq.pointer_size)
            return True
        type_seq.type_data = self.p.type_dic[item_data.type]
        next_type_dw_tag = 'DW_TAG_' + type_seq.type_data.dw_tag
        return self.p.class_dic[next_type_dw_tag].get_add(type_seq, item_list)

    def set_value(self, data, source: ValueSource):
        value = 0
        for i in range(self.p.pointer_size):
            value |= source.buf[source.pointer + i] << (i * 8)
        source.pointer += self.p.pointer_size
        return value


class Structure(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'structure_type'
            self.symbol = 'struct'
            self.key = 0
            self.name = ''
            self.byte_size = 0
            self.member = []
            self.member_dic = {}

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.name:
                type_data.name = self.get_dw_at_name()
                if type_data.name:
                    continue
            if not type_data.byte_size:
                type_data.byte_size = self.get_dw_at_byte_size()
                if type_data.byte_size:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break
            new_type = self.get_type_name()
            if new_type:
                member = self.p.class_dic[new_type].get_type()
                if member.name:  # '0 null' case
                    type_data.member.append(member)
                    type_data.member_dic[member.name] = member
        self.p.struct_dic[type_data.name] = type_data
        return type_data

    def get_add(self, type_seq: AddSeq, item_list):
        item_data = type_seq.type_data
        type_seq.add_multiple(item_data.byte_size)
        if not item_list:
            return True
        try:
            member = item_data.member_dic[item_list[0]]
        except KeyError:
            print('[SYS]: can not find member %s' % (item_list[0],))
            return False

        type_seq.add_shift(member.location)
        if member.bit_size > 0:
            type_seq.bit_mask = [member.bit_size, member.bit_offset]
        type_seq.type_list.append(item_data)
        type_seq.type_data = self.p.type_dic[member.type]
        next_type_dw_tag = 'DW_TAG_' + type_seq.type_data.dw_tag
        if not item_list:
            return True
        return self.p.class_dic[next_type_dw_tag].get_add(type_seq, item_list[1:])

    def set_value(self, data, source: ValueSource):
        base_pointer = source.pointer
        new_data = copy.copy(data)
        new_data.member = []
        new_data.member_dic = {}
        for m in data.member:
            source.pointer = base_pointer + m.location
            member = self.get_compiler(m).set_value(m, source)
            new_data.member.append(member)
            new_data.member_dic[member.name] = member
        return new_data


class UnionType(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'union_type'
            self.symbol = 'union'
            self.key = 0
            self.name = ''
            self.byte_size = 0
            self.member = []
            self.member_dic = {}

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.name:
                type_data.name = self.get_dw_at_name()
                if type_data.name:
                    continue
            if not type_data.byte_size:
                type_data.byte_size = self.get_dw_at_byte_size()
                if type_data.byte_size:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                member = self.p.class_dic[new_type].get_type()
                if member.name:
                    type_data.member.append(member)
                    type_data.member_dic[member.name] = member
        self.p.union_dic[type_data.name] = type_data
        return type_data

    def get_add(self, type_seq: AddSeq, item_list):
        item_data = type_seq.type_data
        type_seq.add_multiple(item_data.byte_size)
        if not item_list:
            return True
        try:
            member = item_data.member_dic[item_list[0]]
        except KeyError:
            print('[SYS]: can not find member %s' % (item_list[0],))
            return False

        type_seq.add_shift(member.location)
        if member.bit_size > 0:
            type_seq.bit_mask = [member.bit_size, member.bit_offset]
        type_seq.type_list.append(item_data)
        type_seq.type_data = self.p.type_dic[member.type]
        next_type_dw_tag = 'DW_TAG_' + type_seq.type_data.dw_tag
        if not item_list:
            return True
        return self.p.class_dic[next_type_dw_tag].get_add(type_seq, item_list[1:])

    def set_value(self, data, source: ValueSource):
        base_pointer = source.pointer
        new_data = copy.copy(data)
        new_data.member = []
        new_data.member_dic = {}
        for m in data.member:
            source.pointer = base_pointer + m.location
            member = self.get_compiler(m).set_value(m, source)
            new_data.member.append(member)
            new_data.member_dic[member.name] = member
        return new_data


class Member(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'member'
            self.symbol = 'member'
            self.name = ''
            self.type = 0
            self.location = 0
            self.byte_size = 0
            self.offset = 0
            self.bit_size = 0
            self.bit_offset = 0
            self.value = None

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        type_data.type_dic = self.p.type_dic
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.name:
                type_data.name = self.get_dw_at_name()
                if type_data.name:
                    continue
            if not type_data.type:
                type_data.type = self.get_dw_at_type()
                if type_data.type:
                    continue
            if not type_data.location:
                type_data.location = self.get_dw_at_data_member_location()
                if type_data.location:
                    continue
            if not type_data.byte_size:
                type_data.byte_size = self.get_dw_at_byte_size()
                if type_data.byte_size:
                    continue
            if not type_data.bit_size:
                type_data.bit_size = self.get_dw_at_bit_size()
                if type_data.bit_size:
                    continue
            if not type_data.bit_offset:
                type_data.bit_offset = self.get_dw_at_bit_offset()
                if type_data.bit_offset:
                    type_data.offset = type_data.bit_offset
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                print('Error: Member, should not new type')

        return type_data

    def set_value(self, data, source: ValueSource):
        new_data = copy.copy(data)
        type_data = self.p.type_dic[new_data.type]
        next_type_dw_tag = 'DW_TAG_' + type_data.dw_tag
        new_data.value = self.p.class_dic[next_type_dw_tag].set_value(type_data, source)
        if new_data.bit_size > 0:  # 注意当union里面的struct的成员对齐时， 是不存在byte size的
            new_data.value = new_data.value >> new_data.bit_offset
            new_data.value = new_data.value & (~(0xFFFFFFFF << new_data.bit_size))
        return new_data


class EnumerationType(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'enumeration_type'
            self.symbol = 'enumeration'
            self.key = 0
            self.byte_size = 0
            self.member = []

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.byte_size:
                type_data.byte_size = self.get_dw_at_byte_size()
                if type_data.byte_size:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                member = self.p.class_dic[new_type].get_type()
                member.enum_set = type_data  # 找到枚举值所在的枚举集
                type_data.member.append(member)

        return type_data


class Enumerator(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'enumerator'
            self.symbol = 'enumerator'
            self.key = 0
            self.name = ''
            self.const_value = 0
            self.enum_set = None

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.name:
                type_data.name = self.get_dw_at_name()
                if type_data.name:
                    continue
            if not type_data.const_value:
                type_data.const_value = self.get_dw_at_const_value()
                if type_data.const_value:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                break
        if type_data.name:
            self.p.enum_dic[type_data.name] = type_data
        return type_data


class Typedef(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'typedef'
            self.symbol = 'typedef'
            self.key = 0
            self.name = ''
            self.type = 0

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.name:
                type_data.name = self.get_dw_at_name()
                if type_data.name:
                    continue
            if not type_data.type:
                type_data.type = self.get_dw_at_type()
                if type_data.type:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                break

        return type_data

    def get_add(self, type_seq: AddSeq, item_list):
        item_data = type_seq.type_data

        type_seq.type_list.append(item_data)
        type_seq.type_data = self.p.type_dic[item_data.type]
        next_type_dw_tag = 'DW_TAG_' + type_seq.type_data.dw_tag
        return self.p.class_dic[next_type_dw_tag].get_add(type_seq, item_list)

    def set_value(self, data, source: ValueSource):
        type_data = self.p.type_dic[data.type]
        next_type_dw_tag = 'DW_TAG_' + type_data.dw_tag
        return self.p.class_dic[next_type_dw_tag].set_value(type_data, source)


class BaseType(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'base_type'
            self.symbol = 'base'
            self.key = 0
            self.name = ''
            self.byte_size = 0

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.name:
                type_data.name = self.get_dw_at_name()
                if type_data.name:
                    continue
            if not type_data.byte_size:
                type_data.byte_size = self.get_dw_at_byte_size()
                if type_data.byte_size:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                break

        return type_data

    def get_add(self, type_seq: AddSeq, item_list):
        item_data = type_seq.type_data
        type_seq.type_list.append(item_data)
        type_seq.add_multiple(item_data.byte_size)
        return True

    def set_value(self, data, source: ValueSource):
        value = 0
        for i in range(data.byte_size):
            value |= source.buf[source.pointer + i] << (i * 8)
        source.pointer += data.byte_size
        return value


class ConstType(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'const_type'
            self.symbol = 'const'
            self.key = 0
            self.type = 0

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.type:
                type_data.type = self.get_dw_at_type()
                if type_data.type:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                break

        return type_data

    def get_add(self, type_seq: AddSeq, item_list):
        item_data = type_seq.type_data

        type_seq.type_list.append(item_data)
        type_seq.type_data = self.p.type_dic[item_data.type]
        next_type_dw_tag = 'DW_TAG_' + type_seq.type_data.dw_tag
        return self.p.class_dic[next_type_dw_tag].get_add(type_seq, item_list)

    def set_value(self, data, source: ValueSource):
        type_data = self.p.type_dic[data.type]
        next_type_dw_tag = 'DW_TAG_' + type_data.dw_tag
        return self.p.class_dic[next_type_dw_tag].set_value(type_data, source)


class VolatileType(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'volatile_type'
            self.symbol = 'volatile'
            self.key = 0
            self.type = 0

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.type:
                type_data.type = self.get_dw_at_type()
                if type_data.type:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                break

        return type_data

    def get_add(self, type_seq: AddSeq, item_list):
        item_data = type_seq.type_data

        type_seq.type_list.append(item_data)
        type_seq.type_data = self.p.type_dic[item_data.type]
        next_type_dw_tag = 'DW_TAG_' + type_seq.type_data.dw_tag
        return self.p.class_dic[next_type_dw_tag].get_add(type_seq, item_list)

    def set_value(self, data, source: ValueSource):
        type_data = self.p.type_dic[data.type]
        next_type_dw_tag = 'DW_TAG_' + type_data.dw_tag
        return self.p.class_dic[next_type_dw_tag].set_value(type_data, source)


class SubroutineType(Translate):
    class data():
        def __init__(self):
            self.dw_tag = 'subroutine_type'
            self.symbol = 'subroutine'
            self.key = 0
            self.type = 0
            self.prototyped = 0
            self.member = []

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.type:
                type_data.type = self.get_dw_at_type()
                if type_data.type:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                member = self.p.class_dic[new_type].get_type()
                type_data.member.append(member)

        return type_data


class InlinedSubroutine(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'inlined_subroutine'
            self.symbol = 'inlined_subroutine'
            self.key = 0
            self.member = []

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if deep == self.get_deep():
                self.p.row -= 1
                break
            new_type = self.get_type_name()
            if new_type:
                member = self.p.class_dic[new_type].get_type()
                type_data.member.append(member)

        return type_data


class Subprogram(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'subprogram'
            self.symbol = 'subprogram'
            self.key = 0
            self.type = 0
            self.name = ''
            self.member = []

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.name:
                type_data.name = self.get_dw_at_name()
                if type_data.name:
                    continue
            if not type_data.type:
                type_data.type = self.get_dw_at_type()
                if type_data.type:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                member = self.p.class_dic[new_type].get_type()
                type_data.member.append(member)

        return type_data


class FormalParameter(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'formal_parameter'
            self.symbol = 'formal_parameter'
            self.key = 0
            self.type = 0
            self.name = ''
            self.location = 0
            self.const_value = 0

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if not type_data.name:
                type_data.name = self.get_dw_at_name()
                if type_data.name:
                    continue
            if not type_data.type:
                type_data.type = self.get_dw_at_type()
                if type_data.type:
                    continue
            if not type_data.const_value:
                type_data.const_value = self.get_dw_at_const_value()
                if type_data.const_value:
                    continue
            if not type_data.location:
                type_data.location = self.get_dw_at_location()
                if type_data.location:
                    continue
            if deep == self.get_deep():
                self.p.row -= 1
                break

            new_type = self.get_type_name()
            if new_type:
                break

        return type_data


class LexicalBlock(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'lexical_block'
            self.symbol = 'lexical_block'
            self.key = 0
            self.member = []

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if deep == self.get_deep():
                self.p.row -= 1
                break
            new_type = self.get_type_name()
            if new_type:
                member = self.p.class_dic[new_type].get_type()
                type_data.member.append(member)

        return type_data


class Unspecified(Translate):
    class Data:
        def __init__(self):
            self.dw_tag = 'unspecified_parameters'
            self.symbol = 'unspecified_parameters'
            self.member = []

    def __init__(self, p: Parameter()):
        Translate.__init__(self, p)

    def get_type(self):
        type_data = self.Data()
        type_data.key = self.get_key()
        self.p.type_dic[type_data.key] = type_data
        deep = self.get_deep()
        while True:
            self.p.row += 1
            if deep == self.get_deep():
                self.p.row -= 1
                break
            new_type = self.get_type_name()
            if new_type:
                member = self.p.class_dic[new_type].get_type()
                type_data.member.append(member)

        return type_data


class Main:
    def __init__(self):
        self.p = Parameter()

        self.tran = Translate(self.p)
        self.compile_unit = CompileUnit(self.p)
        self.subprogram = Subprogram(self.p)
        self.variable = Variable(self.p)
        self.pointer_type = Pointer(self.p)
        self.structure_type = Structure(self.p)
        self.member = Member(self.p)
        self.typedef = Typedef(self.p)
        self.base_type = BaseType(self.p)
        self.formal_parameter = FormalParameter(self.p)
        self.lexical_block = LexicalBlock(self.p)
        self.const_type = ConstType(self.p)
        self.volatile_type = VolatileType(self.p)
        self.enumeration_type = EnumerationType(self.p)
        self.enumerator = Enumerator(self.p)
        self.union_type = UnionType(self.p)
        self.inlined_subroutine = InlinedSubroutine(self.p)
        self.array_type = ArrayType(self.p)
        self.subrange_type = SubrangeType(self.p)
        self.subroutine_type = SubroutineType(self.p)
        self.constant = Constant(self.p)  # For ARC
        self.unspecified = Unspecified(self.p)  # For ARC

        self.p.class_dic = {
            'DW_TAG_compile_unit': self.compile_unit,
            'DW_TAG_subprogram': self.subprogram,
            'DW_TAG_variable': self.variable,
            'DW_TAG_pointer_type': self.pointer_type,
            'DW_TAG_structure_type': self.structure_type,
            'DW_TAG_member': self.member,
            'DW_TAG_typedef': self.typedef,
            'DW_TAG_base_type': self.base_type,
            'DW_TAG_formal_parameter': self.formal_parameter,
            'DW_TAG_lexical_block': self.lexical_block,
            'DW_TAG_const_type': self.const_type,
            'DW_TAG_volatile_type': self.volatile_type,
            'DW_TAG_enumeration_type': self.enumeration_type,
            'DW_TAG_enumerator': self.enumerator,
            'DW_TAG_union_type': self.union_type,
            'DW_TAG_inlined_subroutine': self.inlined_subroutine,
            'DW_TAG_array_type': self.array_type,
            'DW_TAG_subrange_type': self.subrange_type,
            'DW_TAG_subroutine_type': self.subroutine_type,
            'DW_TAG_constant': self.constant,
            'DW_TAG_unspecified_parameters': self.unspecified
        }

    def get_types(self):

        for line in self.p.lines:
            if 'Machine:' in line:
                self.p.machine = line.split(':')[1].strip()
                if 'ARM' not in self.p.machine:
                    self.p.is_arm = False
                print('[SYS]: Current machine is %s' % self.p.machine)
                break

        while self.p.row < self.p.length:
            new_type = self.tran.re_type.findall(self.p.cur_line())
            if new_type:
                if self.tran.get_key() <= 0:
                    self.p.row += 1
                    continue
                if new_type[0] == 'DW_TAG_compile_unit' and '(DW_TAG_compile_unit)' in self.p.cur_line():
                    self.p.unit_member.append(self.compile_unit.get_type())
            self.p.row += 1

        if not self.p.is_arm:
            for array in self.p.array_list:
                sub_data = self.p.type_dic[array.type]
                if sub_data.dw_tag == 'array_type':
                    array.sub.append(sub_data.sub[0])
        return self.p


def types_type(source):
    type_dic = {}
    type_list = []
    cur_type = ''
    re_type = re.compile(r'DW_TAG_[_\w]+')
    re_tag = re.compile(' +')
    with open(source, 'r') as f:
        for line in f:
            is_type = re_type.findall(line)

            if is_type:
                cur_type = is_type[0]
                if not cur_type in type_list:
                    type_list.append(cur_type)
                    type_dic[cur_type] = []
                continue
            if not cur_type:
                continue

            tag = re_tag.split(line)
            if len(tag) < 3:
                continue
            tag = tag[2]

            if 'DW_AT_' not in tag:
                continue

            if not tag in type_dic[cur_type]:
                type_dic[cur_type].append(tag)
    for item in type_dic.items():
        print(item[0])
        for tag in item[1]:
            print('\t', end='')
            print(tag)


def list_type():
    re_type = re.compile(r'DW_TAG_[_\w]+')  # _type

    m_file = open('ps8229_w_aom_b_bin_debug_info.txt', 'r')
    data = m_file.read()

    type_list = re_type.findall(data)

    type_all = []
    for item in type_list:
        if item in type_all:
            continue
        type_all.append(item)

    print(type_all)
    return type_list
