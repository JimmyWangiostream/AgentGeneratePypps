import __main__
import sys
import os
from pathlib import Path
import traceback
import logging
import abc
from typing import Any, cast
from datetime import datetime
import Script
from Script import api
from Script.lib import sdk_lib as lib
from Script.pattern import pattern_logger
from Script.pattern.pattern_logger import logger

import Script.api.shared as shared
from Script.api.util.timeout.structs import usermode_timeout

class UFSTC(abc.ABC):
    def __init__(self) -> None:
        self.ptn_name: str = ''
        self.tcsargs: dict[str, str] = {}
        self.tester_info = api.TesterInfo(-1, -1, '')

    def run(self, tool_logger: logging.Logger | None = None, arg: Script.Argument | None = None, **tcsargs: str) -> Script.Result:
        global logger
        try:
            start_time = datetime.now()
            # get ptn name
            self.ptn_name = self._get_pattern_name()
            # Set tcsargs
            self.tcsargs = tcsargs
            # Set global param
            api.set_param()
            
            # Set Random Seed

            # Init Tester
            if arg is not None and arg.tester_name is not None:
                self.tester_info = api.get_tester_info(arg.tester_name)
            else:
                drives = api.scan_tester()
                if len(drives) == 0:
                    raise api.DEVICE_NOT_FOUND_ERROR("There is no driver")
                if len(drives) > 1:
                    for idx, d in enumerate(drives):
                        print(f'[{idx}] {d.tester_generation}, Port={d.port_num}, Drive={d.target_drive}')
                    select_idx = eval(input('Select Tester: '))
                    self.tester_info = drives[select_idx]
                else:
                    self.tester_info = drives[0]
            sdk = lib.SDKLib(self.tester_info.target_drive)
            #sdk.set_authenticate_ips(["192.168.10.90:8299"])
            api.set_sdk(sdk)

            # Set Common Path
            if arg is not None:
                api.CommonPath.init(port_num=self.tester_info.port_num,
                                    ptn_name=self.ptn_name, 
                                    dev_report_path=os.path.join(arg.report_dir, f'P{self.tester_info.port_num}_{self.tester_info.target_drive}'),
                                    mp_tool_path=os.path.join(api.CommonPath.root, 'mp_tool')) # hard coded location
            else:
                api.CommonPath.init(port_num=self.tester_info.port_num,
                                    ptn_name=self.ptn_name, 
                                    dev_report_path=os.path.join(api.CommonPath.report, 'development_report', f'P{self.tester_info.port_num}', f'{self.ptn_name}_{datetime.now().strftime("%Y%m%d_%H%M%S")}'),
                                    mp_tool_path=os.path.join(api.CommonPath.root, 'mp_tool'))

            # Set Logger
            if tool_logger is None:
                pattern_logger.set_to_debug_mode_logger(self.ptn_name, os.path.join(api.CommonPath.report, f'P{self.tester_info.port_num}'))
            else:
                pattern_logger.set_logger(tool_logger)
            api.set_logger(logger)

            # Get Host Info
            host_info = api.get_host_info()
            if(host_info.dll_enable == False):
                api.dll_init()
            api.get_dll_version()
            api.host_init(lib.HostInit.TESTER_POWER_OFF.value)
            shared.param.gHostInfo = host_info

            # SDK_Track_Activate
            api.track_activate_and_reset()

            # SDK_Timeout_Setting(DCMD13)

            # Set CMD_SEQ QD Limit
            self._set_cmd_seq_qd_limit(device_limit=32)

            # Init Device
            api.first_init_to_max_hs_gear(link_startup_mode=api.LinkStartUpMode.LS_RESET_MODE, ref_clk=api.RefClk.MHZ_26_0)
            # Determine DUT
            dut = api.Dut.get_instance()
            dut.tester_info = self.tester_info
            dut.print_info()

            usermode_timeout.read_timeout_setting_form_csv("default")

            # Run
            logger.info("=========Test Start %s=========" % self.ptn_name)
            if not self.is_support():
                raise api.UFS_NON_SUPPORT
            # self.backup_device_config_and_hw_page()
            self.pre_process()
            self.process()
            self.post_process()
            # logger.info("=========Restore Device =========")
            # self.restore_device_config_and_hw_page()
            logger.info("=========Test End %s=========" % self.ptn_name)
            result = Script.Result(is_ok=True, err_code="PASS")
            logger.info("Pattern Result: [PASS]")
        except (api.ApiErrorBase, lib.CommonLibErrorBase) as e:
            logger.error(' ')
            logger.error("================ ERROR REPORT ================")
            errcode = e.__class__.__name__
            result = Script.Result(is_ok=False, err_code=errcode)
            logger.error(traceback.format_exc())
            logger.error("----------------------------------------------")
            logger.error(f"Pattern Result: [FAIL]")
            logger.error(f"Error Code: {errcode}")
            logger.error(f"Message: '{str(e)}'")
            logger.error("----------------------------------------------")
            self._fail_handling_flow()
        except Exception as e:
            logger.error(' ')
            logger.error("================ ERROR REPORT ================")
            result = Script.Result(is_ok=False, err_code="EXCEPTION")
            logger.error(traceback.format_exc())
            logger.error("----------------------------------------------")
            logger.error(f"Pattern Result: [Exception]")
            logger.error(f"Error Code: {e.__class__.__name__}")
            logger.error(f"Message: '{str(e)}'")
            logger.error("----------------------------------------------")
            self._fail_handling_flow()
        finally:
            logger.info("--------------- FINALLY BLOCK ----------------")
            try:
                api.dumpfile('Track_Result.bin', sdk.sdk_track_result())
            except Exception as e:
                logger.error(f'An exception occurred in "FINALLY BLOCK". exception={e}')
            end_time = datetime.now()
            logger.info(f'Execution Time: {(end_time - start_time)}')
            logger.info('Return result.')
            return result

    def is_support(self) -> bool:
        return True
    
    # def backup_device_config_and_hw_page(self) -> None:
    #     self._backup_config = backup_device_config()
    #     read_hw_page(hw_bin_path=self._backup_hw_bin_path)

    # def restore_device_config_and_hw_page(self) -> None:
    #     restore_device_config()

    #     if '' == self._backup_hw_bin_path:
    #         logger.info("restore hw page fail - no backup hw page")
    #         REPORT_UNEXPECTED()

    #     write_hw_page(hw_bin_path=self._backup_hw_bin_path)

    @abc.abstractmethod
    def pre_process(self) -> None:
        raise NotImplementedError

    @classmethod
    def get_step_func(cls) -> list[Any]:
        """
        Get all step functions
        """
        def is_step(name: str) -> bool:
            """
            only step+number is step function
            """
            try:
                int(name[4:])
            except ValueError:
                return False
            return name.startswith("step")
        step_func_dict = {attr: val for attr, val in cls.__dict__.items()\
                          if callable(val) and is_step(attr)}
        step_func_name_list = list(step_func_dict.keys())
        def get_step_number(name: str) -> int:
            return int(name[4:])
        step_func_name_list.sort(key=get_step_number)
        return [step_func_dict[func] for func in step_func_name_list]

    def process(self) -> None:
        """
        run all test steps
        """
        for func in self.get_step_func():
            func(self)

    @abc.abstractmethod
    def post_process(self) -> None:
        raise NotImplementedError
    
    def _get_pattern_name(self) -> str:
        if self.__class__.__module__ == '__main__': # run pattern as main
            file = sys.modules['__main__'].__file__
            if file is None:
                raise api.PATTERN_ASSERT_UNEXPECTED_CONDITION('pattern_tempalte: get_pattern_name failed. sys.modules["__main__"].__file__ is None.')
            return Path(os.path.basename(file)).stem
        else: # run pattern as module(by import)
            return self.__class__.__module__.split(".")[-1]
        
    def _fail_handling_flow(self) -> None:
        try:
            api.dme_set_interrupt_device()
            api.dme_get_host_register_table()
            api.get_fw_assert_number()
        except Exception as e:
            logger.error(f'An exception occurred during "_fail_handling_flow". exception={e}')

    def _set_cmd_seq_qd_limit(self, device_limit: int) -> None:
        sdk_ver = shared.param.gHostInfo.sdk_ver1
        if sdk_ver is None:
            raise api.PATTERN_ASSERT_HOST_INFO_PARAM_CHACHE_REQUIRED
        sdk_qd_limit = 64 if sdk_ver >= 7 else 32
        qd_limit = min(sdk_qd_limit, device_limit)
        logger.info(f'QD Limit = {qd_limit}')
        import Script.api.cmd_seq as ExecuteCMD
        ExecuteCMD.set_qd_limit(qd_limit)