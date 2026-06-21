import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.defines.constant_define import *
from Script.pattern.rain.mutual_fun import *
from enum import IntEnum, auto

class TEST_ITEM(IntEnum):
    NOTHING = 0
    DEEPSLEEP = auto()
    POR = auto()
    SWITCH_PARTITION = auto()
    DUMMY = auto()

class Pattern(UFSTC):
    def pre_process(self) -> None:       
        self.TestNormalLun, self.TestEM1Lun, self.TestWBLun, self.flash_setting, self.fw_geometry = rain_pattern_precondition()
        self.max_ce, self.max_plane, self.max_pageline = get_geometry_parameter()
        self.write_record = api.get_empty_write_record()
        self._param = shared.param
        self.pageline_per_WL = 12
        self.READ_SCAN_SAFE_AREA = 8
        pass

    def step1(self) -> None:
        for i in range(TEST_ITEM.DUMMY):
            logger.flow(1, 'reconfig to clear data')
            reconfig_to_erase_all_lun(write_record=self.write_record)
            logger.flow(2, 'Write TLC data 5 pages')
            self.last_lba, cursor = write_data_more_than_N_page(page_cnt=3, lun=self.TestNormalLun, testMode=TestMode.TEST_TLC, write_record=self.write_record)
            logger.flow(3, 'Inject UECC')
            self.inject_UECC_in_random_written_pca(lun=self.TestNormalLun, last_lba=self.last_lba)
            if i == TEST_ITEM.NOTHING:
                logger.flow(4, 'Do nothing')
                pass
            elif i == TEST_ITEM.DEEPSLEEP:
                logger.flow(4, 'DeepSleep + SPOR')
                ssu = ExecuteCMD.StartStopUnit()
                ssu.assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x04, no_flush=0, start=0)
                ssu.set_option(wait_queue_empty=True)
                ExecuteCMD.enqueue(ssu)
                ExecuteCMD.send(clear_on_success=True)
                api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
            elif i == TEST_ITEM.POR:
                logger.flow(4, 'POR')
                api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=True)
            elif i == TEST_ITEM.SWITCH_PARTITION:
                logger.flow(4, 'write SLC to switch partition + SPOR')
                api.sequential_write(lun=self.TestEM1Lun, start_lba=0, total_size=api.BLOCK4K_SIZE_4K_BYTE, chunk_size=api.BLOCK4K_SIZE_4K_BYTE, fua = 0,
                                        need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
                api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
            logger.flow(5, 'Compare data')
            read_compare_rain_result(write_record=self.write_record)
        pass

    def inject_UECC_in_random_written_pca(self, lun:int, last_lba:int) -> None:
        SLC_en = lun != self.TestNormalLun
        lba = random.randint(0, last_lba)
        pca = get_PCA_and_print(lun=lun, lba = lba)
        inject_UECC(pca=pca, SLC_enable=SLC_en)
        return

    def post_process(self) -> None:
        pass
    
run = Pattern().run
if __name__ == "__main__":
    run()