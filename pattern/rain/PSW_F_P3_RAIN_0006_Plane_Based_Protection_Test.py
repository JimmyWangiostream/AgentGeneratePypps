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
        self.phison_pca = PCA()
        self.pca_saved = False
        pass

    def step1(self) -> None:
        logger.flow(1, f'Write data until PTE VB has more than 1 pageline')
        last_lba, self.cursor = write_data_more_than_N_pageline(pageline_cnt=1, lun=self.TestNormalLun, testMode=TestMode.TEST_PTE, write_record=self.write_record)
        pass
    
    def step2(self) -> None:
        logger.flow(2, f'Direct Read PTE VB data and calculate parity')
        self.data_buf_list = self.get_raw_data_buffer(self.cursor)
        raw_data_list =self.data_buf_list[:-1]
        self.parity_manual = bytearray(8)
        self.parity_manual = bytearray_xor(bytearray_list=raw_data_list, initXOR=self.parity_manual, check_len=8)
        for data in self.data_buf_list:
            logger.info(f'data: {format_bytearray(data[0:8])}')
        logger.info(f'parity_manual: {format_bytearray(self.parity_manual[0:8])}')
        pass
    
    def step3(self) -> None:
        logger.flow(3, f'Direct Read PTE VB parity data and compare')
        raw_parity = self.data_buf_list[-1]
        logger.info(f'raw_parity: {format_bytearray(raw_parity[0:8])}')
        if raw_parity[0:8] != self.parity_manual[0:8]:
            logger.error_lb(f'issue direct read to get parity')
            logger.error_fp(f'expect parity calculated manually match last valid page, but parity_manual = {format_bytearray(self.parity_manual[0:8])}, raw_parity = {format_bytearray(raw_parity[0:8])}, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
        pass
    
    def step4(self) -> None:
        pca = phison_pca_to_micron_pca(self.phison_pca)
        logger.flow(4, 'Inject UECC')
        inject_UECC(pca=pca, SLC_enable=True)
        pass

    def step5(self) -> None:
        logger.flow(5, 'SPOR and Stop Refresh')
        api.init_tester_to_unit_ready(api.Dcmd5ResetType.HW_RESET, powerdown=False)
        project_api.issue_C088_to_start_or_stop_refresh(bParameter0=project_api.VUC088Paremeter.StopRefreshRefreshCanStillBeEnqueue)
        
    def step6(self) -> None:
        logger.flow(6, 'Compare data')
        # dire_read_payload = api.direct_read(pca=self.phison_pca, block_count=4, include_FW_spare=False)
        read_compare_rain_result(write_record=self.write_record)
    
    def step7(self) -> None:
        logger.flow(7, f"issue VU 40C5 to check the refresh booking queue")
        check_UECC_refresh_booking_Q(VB_list=[(self.phison_pca.b11_block_h<<8) | (self.phison_pca.b10_block_l)])
        pass

    def post_process(self) -> None:
        pass

    def get_raw_data_buffer(self, cursor:api.OpenVBInfoUnit) -> List[bytearray]:
        invalid_plane_list = get_invalid_plane_list()
        data_buf_list = []
        pageline = cursor.first_empty_physical_page.value - 1
        block = cursor.logical_vb.value
        last_valid_page_ce_plane = self.max_plane * self.max_ce - 1
        if invalid_plane_list[block] == last_valid_page_ce_plane:
            last_valid_page_ce_plane -= 1
        for ce in range(self.max_ce):
            for plane in range(self.max_plane):
                ce_plane = self.max_plane * ce + plane
                if invalid_plane_list[block] == ce_plane:
                    continue
                pca = PCA()
                pca.l0_op = api.BIT24 if ce_plane != last_valid_page_ce_plane else api.BIT20
                pca.b4_mode = 1
                pca.b5_ce = ce
                pca.b6_plane = plane
                pca.b11_block_h = (block>>8) & 0xFF
                pca.b10_block_l = block & 0xFF
                pca.l12_fpage = pageline<<5
                logger.info(f'Direct Read: op = {hex(pca.l0_op)}, Block = {(pca.b11_block_h<<8) | (pca.b10_block_l)}, mode = {pca.b4_mode}, CE = {pca.b5_ce}, Plane = {pca.b6_plane}, fPage = {pca.l12_fpage}(pageline = {pca.l12_fpage>>5}), lmu = {pca.b20_lmu}')
                dire_read_payload = api.direct_read(pca=pca, block_count=4, include_FW_spare=False)
                data_buf_list.append(dire_read_payload)
                if not self.pca_saved:
                    self.phison_pca = pca
                    self.pca_saved = True
                dumpfile(f"dire_read_payload_pageline{pageline}_ce{ce}_plane{plane}.bin", dire_read_payload)
        return data_buf_list


run = Pattern().run
if __name__ == "__main__":
    run()