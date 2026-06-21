from dataclasses import dataclass
import time
import ctypes
from ctypes import sizeof
from typing import Dict
import win32file
import win32con
import win32api
import os
from Script.api.exception import DEVICE_NOT_FOUND_ERROR
from Script.lib import sdk_lib as lib

# 定義常量
C_MAX_PHYSICAL_NUM = 20
SCSIOP_INQUIRY = 0x12
PHISON_CMD = 0x06
DIRECT_READ_PAGE = 0x05
SCSI_PASS_THROUGH_WITH_BUFFER_DATA_BUFFER_SIZE = 129 * 512 # 129 << 9
ULONG_PTR = ctypes.c_uint64
SCSI_IOCTL_DATA_IN = 1
IOCTL_SCSI_BASE = 0x00000004
METHOD_BUFFERED = 0
FILE_READ_ACCESS = 0x0001
FILE_WRITE_ACCESS = 0x0002

def CTL_CODE(device_type: int, function: int, method: int, access: int) -> int: 
    return (device_type << 16) | (access << 14) | (function << 2) | method

IOCTL_SCSI_PASS_THROUGH = CTL_CODE(IOCTL_SCSI_BASE, 0x0401, METHOD_BUFFERED, FILE_READ_ACCESS | FILE_WRITE_ACCESS)

class SCSI_PASS_THROUGH(ctypes.Structure):
    _fields_ = [
        ('Length', ctypes.c_ushort),
        ('ScsiStatus', ctypes.c_ubyte),
        ('PathId', ctypes.c_ubyte),
        ('TargetId', ctypes.c_ubyte),
        ('Lun', ctypes.c_ubyte),
        ('CdbLength', ctypes.c_ubyte),
        ('SenseInfoLength', ctypes.c_ubyte),
        ('DataIn', ctypes.c_ubyte),
        ('DataTransferLength', ctypes.c_ulong),
        ('TimeOutValue', ctypes.c_ulong),
        ('DataBufferOffset', ULONG_PTR),
        ('SenseInfoOffset', ctypes.c_ulong),
        ('Cdb', ctypes.c_ubyte * 16)
    ]

class SCSI_PASS_THROUGH_WITH_BUFFERS(ctypes.Structure):
    _fields_ = [
        ('Spt', SCSI_PASS_THROUGH),
        ('Filler', ctypes.c_ulong),
        ('ucSenseBuf', ctypes.c_ubyte * 32),
        ('ucDataBuf', ctypes.c_ubyte * SCSI_PASS_THROUGH_WITH_BUFFER_DATA_BUFFER_SIZE)
    ]

def dwSCSIPtBuilder(stSptwb, cdbLength, CDB, direction, transferLength, timeout): # type: ignore
    CDB12GENERIC_LENGTH = 12
    if 0 > cdbLength or 16 < cdbLength:
        return -1
    stSptwb.Spt.Length = sizeof(SCSI_PASS_THROUGH)
    stSptwb.Spt.PathId = 0
    stSptwb.Spt.TargetId = 1
    stSptwb.Spt.Lun = 0
    stSptwb.Spt.CdbLength = CDB12GENERIC_LENGTH
    stSptwb.Spt.SenseInfoLength = 24
    stSptwb.Spt.TimeOutValue = timeout
    stSptwb.Spt.DataIn = direction
    stSptwb.Spt.DataTransferLength = transferLength
    stSptwb.Spt.DataBufferOffset = ctypes.addressof(stSptwb.ucDataBuf) - ctypes.addressof(stSptwb)
    stSptwb.Spt.SenseInfoOffset = ctypes.addressof(stSptwb.ucSenseBuf) - ctypes.addressof(stSptwb)
    ctypes.memmove(stSptwb.Spt.Cdb, CDB, cdbLength)
    return 0

def hMyCreateFile(drive): # type: ignore
    sDeviceName = f"\\\\.\\PhysicalDrive{drive}"
    accessMode = 3221225472#win32con.GENERIC_READ | win32con.GENERIC_WRITE #3221225472
    shareMode = win32con.FILE_SHARE_READ | win32con.FILE_SHARE_WRITE
    try:
        hdl = win32file.CreateFile(sDeviceName, accessMode, shareMode, None, win32con.OPEN_EXISTING, win32con.FILE_ATTRIBUTE_NORMAL, None)
    except win32api.error as e:
        print(f"Error creating file: {e}")
        return win32file.INVALID_HANDLE_VALUE
    return hdl

def iMyCloseHandle(devHandle): # type: ignore
    win32file.CloseHandle(devHandle)
    return 0

def dwTestUnitReady(targetDisk): # type: ignore
    length = 0
    CDB = (ctypes.c_ubyte * 12)(0)
    devHdl = None

    devHdl = hMyCreateFile(targetDisk)
    err = win32api.GetLastError()
    if devHdl == win32file.INVALID_HANDLE_VALUE:
        return err

    stSptwb = SCSI_PASS_THROUGH_WITH_BUFFERS()
    ctypes.memset(ctypes.byref(stSptwb), 0, ctypes.sizeof(stSptwb))
    ctypes.memset(CDB, 0, ctypes.sizeof(CDB))

    dwSCSIPtBuilder(stSptwb, cdbLength=12, CDB=CDB, direction=1, transferLength=0, timeout=10)
    length = ctypes.addressof(stSptwb.ucDataBuf) - ctypes.addressof(stSptwb) + stSptwb.Spt.DataTransferLength
    in_buffer = ctypes.string_at(ctypes.byref(stSptwb), length)
    out_buffer = win32file.AllocateReadBuffer(ctypes.sizeof(stSptwb))
    
    try:
        win32file.DeviceIoControl(devHdl, IOCTL_SCSI_PASS_THROUGH, in_buffer, out_buffer, None)
    except Exception as e:
        print(f"DeviceIoControl 錯誤: {e}")
        err = win32api.GetLastError()
        print("LastErrorCode: {err}")
        return err
    finally:
        iMyCloseHandle(devHdl)
    
    return 0

def dwNT_find_device(targetDisk): # type: ignore
    TRANSFER_LENGTH = 36
    devHdl = hMyCreateFile(targetDisk)
    if devHdl == win32file.INVALID_HANDLE_VALUE:
        return win32api.GetLastError(), None
    stSptwb = SCSI_PASS_THROUGH_WITH_BUFFERS()
    CDB = (ctypes.c_ubyte * 6)(SCSIOP_INQUIRY, 0, 0, 0, TRANSFER_LENGTH, 0)  # INQUIRY 指令
    dwSCSIPtBuilder(stSptwb, 6, CDB, SCSI_IOCTL_DATA_IN, 36, 10)
    length = ctypes.addressof(stSptwb.ucDataBuf) - ctypes.addressof(stSptwb) + 36
    in_buffer = ctypes.string_at(ctypes.byref(stSptwb), length)
    out_buffer = win32file.AllocateReadBuffer(ctypes.sizeof(stSptwb))
    try:
        win32file.DeviceIoControl(devHdl, IOCTL_SCSI_PASS_THROUGH, in_buffer, out_buffer, None)
        offset = stSptwb.Spt.DataBufferOffset
        data = bytearray(out_buffer)[offset:offset + TRANSFER_LENGTH]
        return 0, bytes(data)
    except Exception as e:
        return win32api.GetLastError(), None
    finally:
        iMyCloseHandle(devHdl)

def NT_read_page(targetDisk): # type: ignore
   TRANSFER_LENGTH = 528
   hDeviceHandle = hMyCreateFile(targetDisk)
   if hDeviceHandle == win32file.INVALID_HANDLE_VALUE:
       return win32api.GetLastError(), None
   stSptwb = SCSI_PASS_THROUGH_WITH_BUFFERS()
   CDB = (ctypes.c_ubyte * 12)(PHISON_CMD, DIRECT_READ_PAGE, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
   ctypes.memset(ctypes.byref(stSptwb), 0, ctypes.sizeof(stSptwb))
   dwSCSIPtBuilder(stSptwb, 12, CDB, SCSI_IOCTL_DATA_IN, TRANSFER_LENGTH, 10)

   length = ctypes.addressof(stSptwb.ucDataBuf) - ctypes.addressof(stSptwb) + stSptwb.Spt.DataTransferLength
   in_buffer = ctypes.string_at(ctypes.byref(stSptwb), length)
   out_buffer = win32file.AllocateReadBuffer(ctypes.sizeof(stSptwb))
   try:
       win32file.DeviceIoControl(hDeviceHandle, IOCTL_SCSI_PASS_THROUGH, in_buffer, out_buffer, None)
       offset = stSptwb.Spt.DataBufferOffset
       data = bytearray(out_buffer)[offset : offset + TRANSFER_LENGTH]
       return 0, data
   except Exception as e:
       print(f"DeviceIoControl 錯誤: {e}")
       err = win32api.GetLastError()
       return err, None
   finally:
       iMyCloseHandle(hDeviceHandle)

def ascii22hex(char: str) -> int:
    if 48 <= ord(char) <= 57:         # '0' 到 '9'
        return ord(char) - 48         # 轉成 0 到 9
    elif 65 <= ord(char) <= 70:       # 'A' 到 'F'
        return ord(char) - 55         # 轉成 10 到 15
    elif 97 <= ord(char) <= 102:      # 'a' 到 'f'
        return ord(char) - 87         # 轉成 10 到 15
    else:
        return 0                      # 其他字元回傳 0

@dataclass
class TesterInfo:
    target_drive: int
    port_num: int
    tester_generation: str

def scan_tester() -> list[TesterInfo]:
    test_info_list = []
    for byTargetDrive in range(C_MAX_PHYSICAL_NUM):
        try:
            test_info_list.append(get_tester_info(byTargetDrive))
        except DEVICE_NOT_FOUND_ERROR:
            pass
    
    return test_info_list

def get_tester_info(driver: int) -> TesterInfo:
    sTesterName = ["UFS_Tester_V4", "UFS_Tester_V6"]

    iCount = 0
    while iCount < 10:
        result = dwTestUnitReady(driver)
        iCount += 1
        if result in [2, 0]:
            break
        time.sleep(0.01)

    result, pStr = dwNT_find_device(driver)
    if result != 0:
        raise DEVICE_NOT_FOUND_ERROR(f"Cannot find drive {driver}")

    prod = bytearray(16)
    prod[:] = pStr[16:31]
    prod_str = prod.decode('utf-8')
    # print(f"find {prod_str}")
    for iTester, tester_name in enumerate(sTesterName):
        if tester_name in prod_str:
            bHostIsFound = True
            status, page_data = NT_read_page(driver)
            if status == 0 and page_data:
                a1 = chr(page_data[0x76])
                a2 = chr(page_data[0x78])
                b1 = ascii22hex(a1)
                b2 = ascii22hex(a2)
                dwPortNum = (b1 << 4) + b2 + 1
                # print(f"{tester_name} is found!! Port Num={dwPortNum}")
                return TesterInfo(driver, dwPortNum, tester_name)
    raise DEVICE_NOT_FOUND_ERROR(f"Failed to Read page(CDB OPCODE 0x06) from drive {driver}")