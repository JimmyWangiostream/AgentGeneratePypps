from pathlib import Path
from Script.api import shared
import os
import subprocess
import tempfile
import shutil
from Script.api.exception import ENVIRONMENT_ASSERT_FFU_RESOURCE_FAIL
from Script.api.ufs_api.defines.enum_define import FFUBinType, FFUSvnType
from Script.api.ufs_api.vendor_cmd.functions import get_flash_setting
from Script.api.ufs_api._codesign_data import CODESIGN_EXE_DATA
import Script.api.cmd_seq as ExecuteCMD

_log = shared.logger

ffu_path = Path(r'\\172.23.99.220\pps_card\FFU\UFS')
# ffu_path = r'D:\FFU_BIN'

FW_FFU_HEADER_SIZE = 4096
FW_MP_HEADER_SIZE = 4096
FW_B_CODE_HEADER_SIZE = 4096
FW_HW_PAGE_SIZE = 4096
FW_MCONFIG_SIZE = 4096

BIN_Data_M1 = 0x1000
BIN_Data_M2 = 0x1001
BIN_Data_SVN = 0x1004
BIN_Data_FW_Vendor = 0x100C
BIN_Data_UFS_Version = 0x1019

FFU_BIN_Header_IC_Version = 0x02

_CODESIGN_PASSWORD = "brSq/Ke83/+QCvBMaqtDkA=="


def search_ffu_bin(ffu_bin_type: FFUBinType, ffu_bin_svn_type: FFUSvnType, include_mConfig: bool = False) -> bytearray:

    if ffu_bin_type == FFUBinType.HW_BIN:
        raise ENVIRONMENT_ASSERT_FFU_RESOURCE_FAIL
    flashsettingdata = get_flash_setting()
    ic_path = os.path.join(ffu_path, str(flashsettingdata.IC_Version))

    if ffu_bin_type == FFUBinType.FW_HW_BIN:
        hw_page_size = FW_HW_PAGE_SIZE * 4
        mconfig_size = FW_MCONFIG_SIZE * 4 if include_mConfig else 0
    elif ffu_bin_type == FFUBinType.FW_BIN:
        hw_page_size = 0
        mconfig_size = 0

    b_bin_offset = FW_FFU_HEADER_SIZE + hw_page_size + mconfig_size + FW_MP_HEADER_SIZE + FW_B_CODE_HEADER_SIZE

    svn_offset = b_bin_offset + BIN_Data_SVN
    fw_vendor_offset = b_bin_offset + BIN_Data_FW_Vendor
    ufs_version_offset = b_bin_offset + BIN_Data_UFS_Version
    m1_offset = b_bin_offset + BIN_Data_M1
    m2_offset = b_bin_offset + BIN_Data_M2

    for root, dirs, files in os.walk(ic_path):
        dirs.sort(key=lambda d: os.path.getctime(os.path.join(root, d)), reverse=True)
        for bin_file in files:
            if ffu_bin_type.value in bin_file:
                if ffu_bin_type == FFUBinType.FW_BIN:
                    if FFUBinType.FW_HW_BIN.value in bin_file:
                        continue
                bin_file = os.path.join(root, bin_file)
                with open(bin_file, 'rb') as f:
                    bin_data = f.read()

                bin_svn = int.from_bytes(bin_data[svn_offset:svn_offset + 4], 'little')
                bin_ic_version = int.from_bytes(bin_data[FFU_BIN_Header_IC_Version:FFU_BIN_Header_IC_Version + 2], 'little')
                bin_fw_vendor = bin_data[fw_vendor_offset]
                ufs_version = bin_data[ufs_version_offset]
                bin_m1 = bin_data[m1_offset]
                bin_m2 = bin_data[m2_offset]
                if ffu_bin_svn_type == FFUSvnType.CURRENT_SVN_BIN:
                    if bin_svn == flashsettingdata.FW_SVN and bin_ic_version == flashsettingdata.IC_Version and bin_fw_vendor == flashsettingdata.FW_Vendor and ufs_version == flashsettingdata.FW_UFS_version_M3_128 and bin_m1 == flashsettingdata.M1 and bin_m2 == flashsettingdata.M2:
                        _log.info(f"current svn file match, file = {bin_file}")
                        _log.info(f"current svn file match, bin info {bin_svn=}, {bin_ic_version=}, {bin_fw_vendor=}, {ufs_version=}, {bin_m1=}, {bin_m2=}")
                        return bytearray(bin_data)
                elif ffu_bin_svn_type == FFUSvnType.OLD_SVN_BIN:
                    if bin_svn < flashsettingdata.FW_SVN and bin_ic_version == flashsettingdata.IC_Version and bin_fw_vendor == flashsettingdata.FW_Vendor and ufs_version == flashsettingdata.FW_UFS_version_M3_128 and bin_m1 == flashsettingdata.M1 and bin_m2 == flashsettingdata.M2:
                        _log.info(f"old svn file match, file = {bin_file}")
                        _log.info(f"old svn file match, bin info {bin_svn=}, {bin_ic_version=}, {bin_fw_vendor=}, {ufs_version=}, {bin_m1=}, {bin_m2=}")
                        return bytearray(bin_data)
                elif ffu_bin_svn_type == FFUSvnType.NEW_SVN_BIN:
                    if bin_svn > flashsettingdata.FW_SVN and bin_ic_version == flashsettingdata.IC_Version and bin_fw_vendor == flashsettingdata.FW_Vendor and ufs_version == flashsettingdata.FW_UFS_version_M3_128 and bin_m1 == flashsettingdata.M1 and bin_m2 == flashsettingdata.M2:
                        _log.info(f"new svn file match, file = {bin_file}")
                        _log.info(f"new svn file match, bin info {bin_svn=}, {bin_ic_version=}, {bin_fw_vendor=}, {ufs_version=}, {bin_m1=}, {bin_m2=}")
                        return bytearray(bin_data)
                _log.info(f"not match file = {bin_file}")
                _log.info(f"not match bin info {bin_svn=}, {bin_ic_version=}, {bin_fw_vendor=}, {ufs_version=}, {bin_m1=}, {bin_m2=}")
                _log.info(f"expect bin info bin_ic_version = {flashsettingdata.IC_Version}, bin_fw_vendor = {flashsettingdata.FW_Vendor}, ufs_version = {flashsettingdata.FW_UFS_version_M3_128}, bin_m1 = {flashsettingdata.M1}, bin_m2 = {flashsettingdata.M2}")
    raise ENVIRONMENT_ASSERT_FFU_RESOURCE_FAIL


def send_ffu_write_buffer(chunksize: int, bin_offset: int, bin_buff: bytearray) -> None:
    write_buffer = ExecuteCMD.WriteBuffer()
    write_buffer.assign(lun=0, mode=0x0E, buffer_id=0, buffer_offset=bin_offset, length=chunksize, vendor=False)
    write_buffer.data = bin_buff[bin_offset:]
    ExecuteCMD.enqueue(write_buffer)
    ExecuteCMD.send()


# ============================================================
# Codesign API
# ============================================================
# temp180117.exe (CodeSign_v1.0.0.10.21) is embedded as a byte
# array in _codesign_data.py. It is extracted to a temp directory
# at runtime and deleted after use — never left on disk.


def _write_codesign_exe(dst_dir: str) -> str:
    """Write the embedded temp180117.exe to *dst_dir*, return its full path."""
    exe_path = os.path.join(dst_dir, "temp180117.exe")
    with open(exe_path, "wb") as f:
        f.write(CODESIGN_EXE_DATA)
    return exe_path


def _run_codesign_once(data_to_sign: bytearray, codesign_exe: str, work_dir: str,
                       label: str = "", read_size: int | None = None) -> bytearray:
    """
    Run one codesign pass.

    Mirrors C++ API_dwProduceNew_FFU_Code:
      1. Write (len-4096) bytes to fin.bin (reserve last 4K as RSA slot)
      2. Execute temp180117.exe
      3. Read fin.bin.sig.bin back (first *read_size* bytes if given, else all),
         then splice into the front of *data_to_sign*
      4. Return *data_to_sign* (modified in-place, length unchanged)

    Pass 1 (CODE_HEADER_FORMAT): read_size = len(data) - 4096 + 512
    Pass 2 (FFU_HEADER_FORMAT):  read_size = None (read full file)
    """
    rsa_size = 4096
    todo_size = len(data_to_sign) - rsa_size

    fin_path = os.path.join(work_dir, "fin.bin")
    fout_path = fin_path + ".sig.bin"

    with open(fin_path, "wb") as f:
        f.write(data_to_sign[:todo_size])

    _log.info(f"  [{label}] -> sign {todo_size} bytes...")
    result = subprocess.run(
        [codesign_exe, _CODESIGN_PASSWORD, "", "fin.bin"],
        cwd=work_dir, capture_output=True, text=True, timeout=300,
    )
    if result.returncode != 0:
        err_msgs = {
            -1: "ARGU_INVALID", -2: "RUN_EXCEPTION_FAILED",
            -3: "LOGIN_FAILED", -4: "SEARCH_DATA_IS_NULL",
            -5: "STATE_INVALID", -6: "EXEC_EXCEPTIOM",
            -7: "SESSION_TIMEOUT", -8: "RESP_EMPTY",
            -9: "CODE_SIFN_FAILED", -10: "WRITE_DATA_FAILED",
            -11: "BIN_FILE_NOT_EXIST", -12: "TOKEN_INVALID",
            -13: "SERVER_CMP_CHECKSUM_FAILED", -14: "HOST_CMP_CHECKSUM_FAILED",
            -15: "USER_PWD_IS_INVALID", -16: "USER_ID_IS_INVALID",
            -17: "USER_AUTH_FAIL", -18: "OTHERS_FAILED",
            -19: "USER_PC_IP_ADDR_INVALID", -20: "USER_PC_IP_ADDR_UNRECOGNIZED",
            -21: "USER_PC_GET_LOCAL_IP_FAIL", -22: "AUTO_LOGIN_RUN_FAILED",
        }
        signed_exit = result.returncode & 0xFFFFFFFF
        if signed_exit > 0x7FFFFFFF:
            signed_exit = signed_exit - 0x100000000
        msg = err_msgs.get(signed_exit, f"UNKNOWN({signed_exit})")
        raise RuntimeError(
            f"[{label}] codesign failed exit={signed_exit} ({msg}): {result.stderr}"
        )

    import time
    for _ in range(30):
        if os.path.isfile(fout_path):
            break
        time.sleep(5)
    else:
        raise RuntimeError(f"[{label}] output file not found: {fout_path}")

    # C++: for CODE_HEADER_FORMAT, read only (ToDoRSA_size + 512) bytes;
    #      for FFU_HEADER_FORMAT, read the whole file via file_length.
    with open(fout_path, "rb") as f:
        sig_data = f.read() if read_size is None else f.read(read_size)
    _log.info(f"  [{label}] -> read {len(sig_data)} bytes, write into data front")
    data_to_sign[:len(sig_data)] = sig_data

    return data_to_sign


def codesign_ffu_bin(
    ffu_bin: bytearray,
    ffu_bin_type: FFUBinType = FFUBinType.FW_HW_BIN,
    include_mconfig: bool = False,
) -> bytearray:
    """
    Two-pass codesign of a modified FFU binary.

    Mirrors C++ ``api_Four_HW_Page_create_FFU_diff_bin``:

      Pass 1 — CODE_HEADER_FORMAT
        1. Zero Code_Header[0x21] and Code_Header[0x2B]
        2. Sign [Code_Header | B-Bin_Data] (LLR table excluded)
        3. Write the signed code portion back into the FFU

      Pass 2 — FFU_HEADER_FORMAT
        1. Zero FFU_Header[0x21] and FFU_Header[0x2B]
        2. Sign the full FFU binary
        3. Return the signed result

    ``temp180117.exe`` is extracted from embedded data on every call and
    cleaned up afterwards — it is never left on disk outside the temp dir.

    Args:
        ffu_bin: Modified FFU binary (bytearray, modified in-place).
        ffu_bin_type: ``FFUBinType.FW_HW_BIN`` or ``FFUBinType.FW_BIN``.
        include_mconfig: Whether the binary contains an mConfig section.

    Returns:
        The fully signed FFU binary (same object as *ffu_bin*).
    """
    # Calculate Code_Header offset from layout (same logic as search_ffu_bin)
    if ffu_bin_type == FFUBinType.FW_HW_BIN:
        hw_page_size = FW_HW_PAGE_SIZE * 4
        mconfig_size = FW_MCONFIG_SIZE * 4 if include_mconfig else 0
    elif ffu_bin_type == FFUBinType.FW_BIN:
        hw_page_size = 0
        mconfig_size = 0
    else:
        raise ValueError(f"unsupported FFU bin type: {ffu_bin_type}")
    # Code_Header offset = FFU_HEADER + HW_page + mConfig + B_BIN_HEADER
    code_offset = FW_FFU_HEADER_SIZE + hw_page_size + mconfig_size + FW_MP_HEADER_SIZE

    work_dir = tempfile.mkdtemp(prefix="ffu_codesign_")
    codesign_exe = None
    try:
        codesign_exe = _write_codesign_exe(work_dir)

        # ================================================================
        # Pass 1 — CODE_HEADER_FORMAT
        # ================================================================
        rsa_size = 4096
        code_size = len(ffu_bin) - code_offset - rsa_size
        code_portion = ffu_bin[code_offset:code_offset + code_size]

        # V13 excludes the LLR table (at the tail of B-Bin_Data) from signing.
        # table_size = *(Code_Header + 491) * 16 * 1024
        llr_table_count = code_portion[491]
        llr_table_size = llr_table_count * 16 * 1024

        if llr_table_size > 0:
            codesign_size = code_size - llr_table_size
            _log.info(f"  exclude LLR table: count={llr_table_count}, size={llr_table_size}")
        else:
            codesign_size = code_size

        # Zero status flags that the codesign tool checks
        code_portion[0x21] = 0  # FFU_BIN_PUBLIC_KEY_TOTAL_SIZE
        code_portion[0x2B] = 0  # FFU_BIN_CODESIGN_DONE

        _log.info(f"[Pass 1] code_offset={hex(code_offset)}, "
                  f"codesign_size={codesign_size}, code_size={code_size}")
        signed_code = _run_codesign_once(
            code_portion[:codesign_size], codesign_exe, work_dir, "Pass1",
            read_size=(codesign_size - 4096 + 512),
        )

        # Write signed data back; LLR table at the tail is untouched
        code_portion[:codesign_size] = signed_code
        ffu_bin[code_offset:code_offset + code_size] = code_portion

        # ================================================================
        # Pass 2 — FFU_HEADER_FORMAT
        # ================================================================
        ffu_bin[0x21] = 0  # FFU_BIN_PUBLIC_KEY_TOTAL_SIZE
        ffu_bin[0x2B] = 0  # FFU_BIN_CODESIGN_DONE

        _log.info(f"[Pass 2] total size={len(ffu_bin)}")
        signed_full = _run_codesign_once(ffu_bin, codesign_exe, work_dir, "Pass2")

        return signed_full

    finally:
        try:
            shutil.rmtree(work_dir)
        except OSError:
            pass
