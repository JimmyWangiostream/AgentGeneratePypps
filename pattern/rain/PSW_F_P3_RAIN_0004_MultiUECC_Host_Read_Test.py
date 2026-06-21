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
from Script.project_api.functions import get_physical_layout

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.TestNormalLun, self.TestEM1Lun, self.TestWBLun, self.flash_setting, self.fw_geometry = rain_pattern_precondition()
        self.max_ce, self.max_plane, self.max_pageline = get_geometry_parameter()
        self.write_record = api.get_empty_write_record()
        self.ufs = UFSMapper(M=self.max_ce, N=self.max_plane)
        pass

    def step1(self) -> None:
        for testMode in [TestMode.TEST_TLC, TestMode.TEST_SLC, TestMode.TEST_WB]:
            SLC_enable = testMode!=TestMode.TEST_TLC
            lun, mode_str = get_general_parameter(testMode)            
            rain_goup_cnt, rain_user = get_rain_parity_parameter(testMode)
            logger.info(f'============ Test {mode_str} VB ============')
            logger.flow(1, f'Write until {mode_str} VB has enough data')
            if testMode == TestMode.TEST_WB:
                api.set_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(idn=api.FlagIDN.WRITEBOOSTER_EN)
                
            if testMode == TestMode.TEST_TLC:
                vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)
                chunksize = api.BLOCK4K_SIZE_128M_BYTE // (self.max_plane * 3) * (self.max_plane * 3)
            else:
                vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
                chunksize = api.BLOCK4K_SIZE_128M_BYTE
            total_size = vb_size //2
            lba = 0
            api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunksize, fua = 1,
                            need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
            lba += total_size
            injectUECC_list:List[int] = []
            UECC_LBA:List[int] = []
            UECC_cnt = 24
            while len(UECC_LBA) < UECC_cnt:
                randomlba = random.randint(0, lba)
                randomlba = randomlba // api.BLOCK4K_SIZE_16K_BYTE * api.BLOCK4K_SIZE_16K_BYTE
                temp = self.ufs.lba_to_location(randomlba, is_TLC=(testMode == TestMode.TEST_TLC))
                if temp['lmu'] !=0:
                    continue
                
                for lmu in range(self.ufs._lmu_count(temp['pageline'], is_TLC=(testMode == TestMode.TEST_TLC))):
                    tempLBA = randomlba + lmu * self.max_plane * api.BLOCK4K_SIZE_16K_BYTE
                    for i in range(api.BLOCK4K_SIZE_16K_BYTE):
                        if tempLBA+i not in UECC_LBA:
                            UECC_LBA.append(tempLBA+i)
                    if randomlba not in injectUECC_list:
                        injectUECC_list.append(randomlba)
            injectUECC_list = sorted(injectUECC_list)
            UECC_LBA = sorted(UECC_LBA)
                    
            logger.flow(2, f'SSU Sleep then Active')
            ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
            ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
            ExecuteCMD.send(QD=1,clear_on_success=True)
            
            logger.flow(3, f'Inject UECC lba list: {injectUECC_list}')
            for lba in injectUECC_list:
                pca = get_PCA_and_print(lun=lun, lba=lba)
                inject_UECC(pca=pca, SLC_enable=SLC_enable)
                        
            logger.flow(4, f'read non-UECC area')
            read_range = self.split_range_excluding(start=0, end=total_size, exclude_list=UECC_LBA)
            for each_range in read_range:
                start_lba = each_range[0]
                length = each_range[1]
                read10 = ExecuteCMD.Read10()
                read10.assign(lun=lun, lba=start_lba, length=length)
                ExecuteCMD.enqueue(read10)
                logger.info(f'push: read LUN{lun}, lba = {start_lba}, length = {length}')
            ExecuteCMD.send()
            
            logger.flow(5, f'Unmap UECC area')
            for lba in UECC_LBA:
                unmap = ExecuteCMD.Unmap()
                unmap.assign(lun=lun, lba=lba, length=1)
                ExecuteCMD.enqueue(unmap)
                logger.info(f'push: Unmap LUN{lun}, lba = {lba}, length = {1}')
            ExecuteCMD.send(clear_on_success=False)
            for cmd in ExecuteCMD._cmd_list:
                api.save_write_info_by_cmd(cmd, self.write_record)   
            ExecuteCMD.clear()
            
            logger.flow(6, f'read UECC area')
            for lba in UECC_LBA:
                read10 = ExecuteCMD.Read10()
                read10.assign(lun=lun, lba=lba, length=1)
                ExecuteCMD.enqueue(read10)
                logger.info(f'push: read LUN{lun}, lba = {lba}, length = {1}')
            ExecuteCMD.send()
            pass

    def post_process(self) -> None:
        pass
    
    def split_range_excluding(self, start: int, end: int, exclude_list: List[int]) -> List[List[int]]:
        if start >= end:
            return []
        excl = sorted({x for x in exclude_list if start <= x < end})
        out: List[List[int]] = []
        cur = start

        def append_chunks(s: int, length: int) -> None:
            while length > 0:
                chunk_len = min(length, api.WRITE_10_MAX_BLOCK_LEN)
                out.append([s, chunk_len])
                s += chunk_len
                length -= chunk_len

        for x in excl:
            if x > cur:
                append_chunks(cur, x - cur)
            cur = x + 1
            if cur >= end:
                break

        if cur < end:
            append_chunks(cur, end - cur)

        return out



run = Pattern().run
if __name__ == "__main__":
    run()