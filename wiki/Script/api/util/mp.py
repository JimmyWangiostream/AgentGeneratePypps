import configparser
from enum import Enum
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time
from typing import Final, Tuple

from filelock import FileLock, Timeout
from Script.api.util.functions import track_activate_and_reset
from Script.lib import sdk_lib as lib
from Script.api import shared
from Script.api.exception import DEVICE_NOT_FOUND_ERROR, EXECUTE_MP_TOOL_EXE_FAILED, EXECUTE_TESTER_FW_ISP_EXCEPTION_OCCUR, EXECUTE_TESTER_FW_ISP_FAILED, EXECUTE_TESTER_FW_ISP_HAS_STDERR_MSG, EXECUTE_TESTER_FW_ISP_TIMEOUT, MP_PARAM_INI_NOT_FOUND, MP_TOOL_EXE_NOT_FOUND, MP_TOOL_EXECUTION_RESULT_FAILED, MP_TOOL_EXECUTION_RESULT_NOT_FOUND, TESTER_FW_NOT_FOUND_ERROR, TESTER_FW_ISP_SPIN_LOCK_WAIT_TOO_LONG, TESTER_PORT_NOT_FOUND_AFTER_EXECUTE_TESTER_FW_ISP
from Script.api.legacy_api.init import dll_init, get_dll_version, get_host_info, host_init
from Script.api.ufs_api._mp import TesterInfo, get_tester_info, scan_tester
from Script.api.util.common_path import CommonPath
from Script.api.util.dut.dut import Dut

_log = shared.logger

class TesterFwOpt(Enum):
    TESTER_FW = 0
    TESTER_ISP = 1

class MP:
    def __init__(self, tester_info: TesterInfo | None = None, mp_tool_path: str = '', mp_tester_fw_path: str = '', sdk_tester_fw_path: str = ''):
        if mp_tool_path == '':
            self.mp_tool_path = Path(CommonPath.mp_tool)
        else:
            self.mp_tool_path = Path(mp_tool_path)
        if mp_tester_fw_path == '':
            self.mp_tester_fw_path = Path(CommonPath.mp_tool)
        else:
            self.mp_tester_fw_path = Path(mp_tester_fw_path)
        if sdk_tester_fw_path == '':
            self.sdk_tester_fw_path = Path(CommonPath.mp_tool)
        else:
            self.sdk_tester_fw_path = Path(sdk_tester_fw_path)
        if tester_info is None:
            self.tester_info = Dut.get_instance().tester_info
        else:
            self.tester_info = tester_info
        self.dedicated_mp_tool_path:Path = Path()

    def execute(self) -> TesterInfo:
        self._update_tester_fw(self.mp_tester_fw_path, TesterFwOpt.TESTER_ISP)
        self._create_mp_folder_by_port()
        self._find_correspond_param_and_change_name()
        exe_path = self._get_mp_exe_path()
        ###-- Allow Multiple MP exe Execute at same time --###
        self._modify_mp_param(section="Multiport", option="Enable", value="1")
        self._modify_mp_param(section="Extend", option="manual_tester_physical_enable", value="1")
        ###-- Simple_PretestInit=1: disable test after open card --###
        # self._modify_mp_param(section="Extend", option="Simple_PretestInit", value="1")
        retry_cnt = 0
        while True:
            try:
                self._execute_mp_exe(exe_path)
                self._check_mp_exe_execution_result()
                break
            except (EXECUTE_MP_TOOL_EXE_FAILED, MP_TOOL_EXECUTION_RESULT_FAILED) as e:
                retry_cnt += 1
                if retry_cnt <= 4:
                    _log.warning(f'[MP] MP Tool Execution Failed. Delete MP Result and Retry({retry_cnt}/4)')
                    all_report_file = self.dedicated_mp_tool_path / 'AllReportFile'
                    report_file = self.dedicated_mp_tool_path / 'ReportFile'
                    if all_report_file.exists():
                        shutil.rmtree(all_report_file)
                    if report_file.exists():
                        shutil.rmtree(report_file)
                else:
                    _log.error('[MP] MP Tool Execution Failed after Multiple Retries.')
                    raise
        self._update_tester_fw(self.sdk_tester_fw_path, TesterFwOpt.TESTER_FW)
        # Get Host Info
        host_info = get_host_info()
        if(host_info.dll_enable == False):
            dll_init()
        get_dll_version()
        host_init(lib.HostInit.TESTER_POWER_OFF.value)
        shared.param.gHostInfo = host_info

        track_activate_and_reset()
        # SDK_Timeout_Setting(DCMD13)
        return self.tester_info

########################### Tester Related Methods ###########################

    def _search_tester_fw(self, testerfw_path: Path, testerfw_opt: TesterFwOpt) -> Tuple[Path, Path, Path]:
        _log.info(f'[MP] Searching TesterFW ISP files from {testerfw_path}')
        keyword = [self.tester_info.tester_generation.split('_')[-1]]
        if testerfw_opt == TesterFwOpt.TESTER_FW:
            keyword.append('TesterFW')
        elif testerfw_opt == TesterFwOpt.TESTER_ISP:
            keyword.append('Tester_ISP')
        else:
            raise NotImplemented(f"pass a invalid tester_opt={testerfw_opt} to api: _search_tester_fw")
        
        list_of_folders = [item for item in os.listdir(testerfw_path) if (testerfw_path / item).is_dir()]
        for item in list_of_folders:
            if _contains_all_keywords(item, keyword):
                testerfw_path = testerfw_path / item
                for (dirpath, dirnames, filenames) in os.walk(testerfw_path):
                    for file in filenames:
                        if ".exe" in file and "MultiISP" in file:
                            ispDirPath = Path(dirpath)
                            ispPath = ispDirPath / file
                            ispIniPath = ispDirPath / 'SlotState.ini'
                            _log.info(f'ISP Directory = {ispDirPath}')
                            _log.info(f'ISP exe Path = {ispPath}')
                            _log.info(f'ISP SlotState Path = {ispIniPath}')
                            return ispDirPath, ispPath, ispIniPath
        _log.error(f'[MP] Cannot find any TesterFW. Path = {testerfw_path}')
        raise TESTER_FW_NOT_FOUND_ERROR
    
    def _execute_tester_fw_isp_exe(self, ispDirPath: Path, ispPath: Path, ispIniPath: Path) -> None:
        if ispIniPath.exists():
            os.remove(ispIniPath)
        _log.info(f'[MP] Execute TesterFW ISP, Drive={self.tester_info.target_drive}, Port={self.tester_info.port_num}, Path={ispPath}')
        p = subprocess.Popen([ispPath, "ISP", "P%d" % self.tester_info.port_num], cwd = ispDirPath)
        try:
            stdout, stderr = p.communicate(timeout=600)
        except subprocess.TimeoutExpired:
            p.kill()
            _log.error("[MP] ISP Timeout")
            raise EXECUTE_TESTER_FW_ISP_TIMEOUT
        except Exception as e:
            _log.error(f"[MP] Exception Occur during ISP Execution: {e}")
            raise EXECUTE_TESTER_FW_ISP_EXCEPTION_OCCUR
        else:
            if stdout:
                _log.info(stdout)
            if stderr:
                _log.error("[MP] ISP Execution Error")
                raise EXECUTE_TESTER_FW_ISP_HAS_STDERR_MSG
            
    def _check_tester_fw_isp_execution_result(self, ispDirPath: Path) -> None:
        _log.info('[MP] Read SlotState.ini to Check ISP Execution Result')
        ini = configparser.ConfigParser()
        ini.read(ispDirPath / 'SlotState.ini')
        if 'Pass' in ini.get('ISP Record', ("Tester_%02d" % self.tester_info.port_num), fallback=''):
            _log.info('[MP] ISP Execution is Succesful!')
        else:
            _log.error(f'[MP] ISP Record of Tester_{self.tester_info.port_num:02d} is not Pass in {ispDirPath / "SlotState.ini"}')
            raise EXECUTE_TESTER_FW_ISP_FAILED

    def _update_if_tester_drive_id_changed(self) -> None:
        _log.info(f'[MP] Check if DriveID of TesterP{self.tester_info.port_num} Changed after ISP Execution.')
        for i in range(60):
            sec = 5
            _log.warning(f'Sleep {sec} seconds')
            time.sleep(sec)
            _log.info('[MP] Scan All Tester')
            new_drivers = scan_tester()
            if len(new_drivers) == 0:
                _log.warning(f'Cannot Find Any Tester.')
                continue
            for d in new_drivers:
                _log.info(f'{d.tester_generation}, Port={d.port_num}, Drive={d.target_drive}')
            for d in new_drivers:
                if d.port_num == self.tester_info.port_num and d.tester_generation == self.tester_info.tester_generation:
                    if d.target_drive == self.tester_info.target_drive:
                        _log.info('[MP] Drive ID is not Changed.')
                    else:
                        _log.warning(f'[MP] Drive ID of TesterP{self.tester_info.port_num} Change from {self.tester_info.target_drive} to {d.target_drive}')
                        self.tester_info = d
                        Dut.get_instance().tester_info = d
                        sdk = lib.SDKLib(d.target_drive)
                        shared.set_sdk(sdk)
                    return
            _log.warning(f'Retry Count: {i+1}. Cannot find matched Tester Port.') 
        raise TESTER_PORT_NOT_FOUND_AFTER_EXECUTE_TESTER_FW_ISP

    def _update_tester_fw(self, testerfw_path: Path, testerfw_opt: TesterFwOpt) -> None:
        ispDirPath, ispPath, ispIniPath = self._search_tester_fw(testerfw_path, testerfw_opt)
        
        isp_ini_file_path = ispDirPath / f'{testerfw_opt}_filelock.ini'
        lock_path = f'{isp_ini_file_path}.lock'
        _log.info(f'[MP] Acquiring ISP filelock.... FileLock={lock_path}')
        lock = FileLock(lock_path, timeout=30 * 60)
        
        try:
            with lock:
                local_time = time.localtime()
                _log.info(f'[MP] Lock Acquired.')
                open(isp_ini_file_path, "a").write(f"[{time.strftime('%m-%d %H:%M:%S', local_time)}] Drive = {self.tester_info.target_drive}, PortNo = {self.tester_info.port_num} is using ISP\n")
                self._execute_tester_fw_isp_exe(ispDirPath, ispPath, ispIniPath)
                self._check_tester_fw_isp_execution_result(ispDirPath)
                _log.info('[MP] Tester ISP Execution is Successful!!')
                self._update_if_tester_drive_id_changed()
        except Timeout:
            _log.error('[MP] Cannot Get Lock Over 30 Minutes')
            raise TESTER_FW_ISP_SPIN_LOCK_WAIT_TOO_LONG
        except EXECUTE_TESTER_FW_ISP_FAILED:
            self._update_if_tester_drive_id_changed()


##############################################################################

########################### MPTool Related Methods ###########################

    def _execute_mp_exe(self, exe_path: Path) -> None:
        _log.info(f'[MP] Execute MP, MP Path = {self.dedicated_mp_tool_path}')
        p = subprocess.Popen([exe_path, "%d" % self.tester_info.target_drive], cwd = self.dedicated_mp_tool_path)
        try:
            timeout = 600
            stdout, stderr = p.communicate(timeout=timeout)
        except subprocess.TimeoutExpired:
            p.kill()
            _log.error(f"[MP] MP Timeout Fail ({timeout}s)")
            raise EXECUTE_MP_TOOL_EXE_FAILED
        except Exception as e:
            p.kill()
            _log.error(f"[MP] MP fail, Unexpected Error: {e}")
            raise EXECUTE_MP_TOOL_EXE_FAILED
        else:
            if stdout:
                _log.info(stdout)
            if stderr:
                _log.error("[MP] MP Tool Execution Error")
                _log.error(stderr)
                raise EXECUTE_MP_TOOL_EXE_FAILED

    def _get_mp_exe_execution_result(self) -> str:
        mp_report_file = r'\[(.+?)\]_.+\.txt'
        for (dirpath, dirnames, filenames) in os.walk(self.dedicated_mp_tool_path):
            for file in filenames:
                match = re.match(mp_report_file, file)
                if match:
                    return match.group(1)
                
        _log.error(f'Cannot find MP Report File in {self.dedicated_mp_tool_path}')
        raise MP_TOOL_EXECUTION_RESULT_NOT_FOUND

    def _check_mp_exe_execution_result(self) -> None:
        mp_result = self._get_mp_exe_execution_result()
        if mp_result == 'PASS':
            _log.info('[MP] MP Pass!')
        else:
            _log.error(f'[MP] MP Failed. MP result = {mp_result}')
            raise MP_TOOL_EXECUTION_RESULT_FAILED

    def _modify_mp_param(self, section: str, option: str, value: str) -> None:
        _log.info(f'[MP] Modify MP param.ini in dedicated port folder: Set[{section}][{option}] => {value}')
        mp_param_path = self.dedicated_mp_tool_path / 'param.ini'

        config = configparser.ConfigParser()
        config.optionxform = str # type: ignore
        config.read(mp_param_path)
        if config.has_section(section) != True:
            config.add_section(section)
        config[section][option] = value
        with open(mp_param_path, 'w', encoding='cp950') as f:
            config.write(f, space_around_delimiters=False)

    def _get_mp_exe_path(self) -> Path:
        for file in self.dedicated_mp_tool_path.iterdir():
            if ".exe" in str(file.name) and "_AP(Normal)" in str(file.name):
                return file
        _log.error(f"Cannot find any MPTool exe, Path = {self.dedicated_mp_tool_path}")
        raise MP_TOOL_EXE_NOT_FOUND

    def _create_mp_folder_by_port(self) -> None:
        self.dedicated_mp_tool_path = self.mp_tool_path / f'MpTool_P{self.tester_info.port_num}'
        if self.dedicated_mp_tool_path.exists():
            shutil.rmtree(self.dedicated_mp_tool_path)
        os.makedirs(self.dedicated_mp_tool_path)

        _log.debug('Collect MP files')
        mp_file_list = []
        for item in self.mp_tool_path.iterdir():
            if item.is_file():
                mp_file_list.append(item.name)

        _log.info('Copy MP files to new folder by port number')
        for file in mp_file_list:
            retry_cnt = 1
            max_retry_cnt = 5
            while True:
                original_file_path = self.mp_tool_path / file
                new_file_path = self.dedicated_mp_tool_path / file
                try:
                    shutil.copy(original_file_path, new_file_path)
                except PermissionError as e:
                    _log.warning(f'Copy attempt {retry_cnt} failed: {original_file_path} -> {new_file_path} | {e}')
                    if retry_cnt >= max_retry_cnt:
                        _log.error(f'Retry Copy MP files Exceeds Max Retry Count ({max_retry_cnt} times)')
                        raise
                    retry_cnt += 1
                    time.sleep(1)
                else:
                    break

    def _find_correspond_param_and_change_name(self) -> None:
        ce_num = Dut.get_instance().ce_num
        config = configparser.ConfigParser()
        target_param = Path()

        _log.info('[MP] Iterate all ini files in mp folder & get value in section=Flash Info, option=Flh_Number')
        for f in self.dedicated_mp_tool_path.iterdir():
            if f.is_file() and len(f.suffixes) != 0 and f.suffixes[-1] == '.ini':
                config.read(f)
                try:
                    flh_num = config['Flash Info'].getint('Flh_Number')
                    if flh_num == ce_num:
                        _log.info(f'[MP] Found MP param file with Matched Flh_Number({flh_num}), file:{f}')
                        target_param = f
                        break
                except KeyError:
                    _log.warning(f'[MP] Section=Flash Info, Option=Flh_Number is not exist in file:{f}')
        if target_param == Path():
            _log.error(f'[MP] Cannot find any MP param file with Matched Flh_Number parameter in {self.dedicated_mp_tool_path}')
            raise MP_PARAM_INI_NOT_FOUND
        
        expected_name = (self.dedicated_mp_tool_path / 'param.ini')
        if target_param != expected_name:
            _log.info('[MP] Copy target param as param.ini (would replace if needed)')
            shutil.copy(target_param, expected_name)
        
        
##############################################################################


def _contains_all_keywords(text: str, keywords: list[str]) -> bool:
    return all(keyword in text for keyword in keywords)
