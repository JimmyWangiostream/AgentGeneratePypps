class DLL_VID_ERROR(Exception): pass
class DLL_SDK_FW_ERROR(Exception): pass
class DLL_HANDSHAKE_ERROR(Exception): pass
class DLL_VERSION_ERROR(Exception): pass
class DLL_AUTH_ERROR(Exception): pass
class DLL_GENERAL_ERROR(Exception): pass

def a():
    tmp = bytearray(512)
    print(len(tmp))
    #raise DLL_VID_ERROR("yoyo")

def swap_endian(i):
    hex_str = hex(i)[2:]  # 去掉前綴 '0x'
    byte_array = bytes.fromhex(hex_str)  # 將十六進制字符串解碼為字節序列
    swapped_byte_array = byte_array[::-1]  # 反轉字節序列
    swapped_hex_str = swapped_byte_array.hex()  # 將反轉後的字節序列編碼為十六進制字符串
    return swapped_hex_str

def swap_endian_2(num, length):
    """
    交換整數的字節順序。

    :param num: 要轉換的整數
    :param length: 整數的字節長度
    :return: 轉換後的整數
    """
    byte_array = num.to_bytes(length, byteorder='little')
    swapped_byte_array = byte_array[::-1]
    return int.from_bytes(swapped_byte_array, byteorder='little')

def b():
    try:
        a()
        #num = 1
        #num_big = swap_endian_2(1, 4)
        #print(num_big)
    except DLL_VID_ERROR as e:
        print(f"i am b except")
        raise DLL_SDK_FW_ERROR("SDK FW 錯誤") from e
    print("b")

def main():
    try:
        b()
    except DLL_VID_ERROR as e:
        print(f"處理 VID 誤誤: {e}")
    except DLL_SDK_FW_ERROR as e:
        print(f"處理 SDK FW 誤誤: {e}")
    except Exception as e:
        print(f"处理未知錯誤: {e}")

    print("DLL 初始化成功")

if __name__ == "__main__":
    main()