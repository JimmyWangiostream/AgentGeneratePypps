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

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.TestNormalLun, self.TestEM1Lun, self.TestWBLun, self.flash_setting, self.fw_geometry = rain_pattern_precondition()
        self.max_ce, self.max_plane, self.max_pageline = get_geometry_parameter()
        self.write_record = api.get_empty_write_record()
        pass

    def step1(self) -> None:
        for testMode in [TestMode.TEST_TLC, TestMode.TEST_SLC, TestMode.TEST_WB]:
            lun, mode_str = get_general_parameter(testMode)            
            rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode)
            logger.info(f'============ Test {mode_str} VB ============')
            logger.flow(1, f'Write until {mode_str} VB has enough data')
            if testMode == TestMode.TEST_WB:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            last_lba, cursor = write_data_more_than_N_page(page_cnt=3, lun=lun, testMode=testMode, write_record=self.write_record)
            
            logger.flow(2, f'SPOR')
            api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
            
            
            logger.flow(3, f'Direct Read {mode_str} VB data and calculate parity')
            mode = 2 if rain_user == project_api.RainUser.HOST_TLC_RAIN else 1
            data_buf_list = self.get_raw_data_buffer(cursor, mode=mode)
            parity = bytearray(8)
            parity = bytearray_xor(bytearray_list=data_buf_list, initXOR=parity, check_len=8)
            
            logger.flow(4, f'issue VU4055 to check {mode_str} VB parity and compare')
            _, fw_spare_list, get_parity = project_api.issue_4055_to_get_rain_parity(rain_user=rain_user, group=cursor.first_empty_physical_page.value % rain_goup_cnt)
            
            logger.info(f'parity_manual: {format_bytearray(parity[0:8])}, parity_vu: {format_bytearray(get_parity[0:8])}')
            dumpfile(f"VU4055_parity.bin", get_parity)
            if parity[0:8] != get_parity[0:8]:
                logger.error_lb(f'issue VU4055 to get parity')
                logger.error_fp(f'expect parity calculated manually match vu result, but parity_manual = {format_bytearray(parity[0:8])}, parity_vu = {format_bytearray(get_parity[0:8])}, result Fail!')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

    def post_process(self) -> None:
        pass

    def get_raw_data_buffer(self, cursor:api.OpenVBInfoUnit, mode:int) -> List[bytearray]:
        invalid_plane_list = get_invalid_plane_list()
        data_buf_list = []
        max_ce_plane = self.max_plane * cursor.first_empty_CE.value + cursor.first_empty_plane.value
        for ce in range(self.max_ce):
            for plane in range(self.max_plane):
                block = cursor.logical_vb.value
                if invalid_plane_list[block] == self.max_plane * ce + plane:
                    continue
                ce_plane = self.max_plane * ce + plane
                if ce_plane >= max_ce_plane:
                    break
                pca = PCA()
                pca.l0_op = api.BIT24
                pca.b4_mode = mode
                pca.b5_ce = ce
                pca.b6_plane = plane
                pca.b11_block_h = (block>>8) & 0xFF
                pca.b10_block_l = block & 0xFF
                pca.l12_fpage = cursor.first_empty_physical_page.value<<5
                dire_read_payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=True)
                data_buf_list.append(dire_read_payload[0:8])
                dumpfile(f"dire_read_payload_ce{ce}_plane{plane}.bin", dire_read_payload)
        return data_buf_list


run = Pattern().run
if __name__ == "__main__":
    run()