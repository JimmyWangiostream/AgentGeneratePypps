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
from Script.api.ufs_api.defines.enum_define import *

USE_PHISON_VU = False


class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        normal_lun_list, em1_lun_list = self.config_lun(50, 50)
        self.TestNormalLun = normal_lun_list[0]
        self.TestEM1Lun = em1_lun_list[0]
        self.write_record = api.get_empty_write_record()
        
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()
        self.fw_debug_mode_bkup = self.hw_setting.get_local_val(api.HwSettingField.FW_DEBUG_MODE)
        self.hw_setting.set_local_val(api.HwSettingField.FW_DEBUG_MODE, 0)
        self.hw_setting.set_to_device()
        pass

    def step1(self) -> None:
        if USE_PHISON_VU:
            logger.flow(1, 'Disable background operation')
            api.clear_flag(api.FlagIDN.BG_OP_EN)
        else:
            logger.flow(1, 'Disable background operation (VU0xD0FD)')
            project_api.issue_D0FD_en_disable_BKOPS(bValue = 0x00)
        lun = self.TestEM1Lun
        logger.flow(2, 'Get the largest LUN id and size (EM1 LUN)')
        max_lba = shared.param.gLUCapacity[lun]
        logger.info(f'LUN id = {lun} and size = {max_lba} (EM1 LUN)')
        
        logger.flow(3, 'Sequential write to get one host open VB (write EM1)')
        total_size = 23050
        chunksize = api.WRITE_6_MAX_LBA
        lba = 0
        api.sequential_write(lun=lun, start_lba=lba, total_size=total_size, chunk_size=chunksize, fua = 1,
                        need_compare=False, compare_method=api.CompareMethod.SW_COMPARE, write_record=self.write_record)
        
        logger.flow(4, 'SSU to ensure all data flush to NAND')
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x02, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.StartStopUnit().assign(lun=api.WellKnownLUN.UFS_DEVICE, immed=0, power_condition=0x01, no_flush=0, start=0).set_option(wait_queue_empty=True).enqueue()
        ExecuteCMD.send(QD=1,clear_on_success=True)
        
        logger.flow(5, 'Select some LBAs to inject error')
        injectUECC_list:List[int] = [13098, 13099, 13100, 13101, 13102, 13103, 13104, 13105, 13106, 13107, 13108, 13109, 13110, 13111, 13112, 13113, 13114, 13115, 13116, 13117, 13118, 13119, 13120, 13121]
        logger.info(f'lba list = {injectUECC_list}')
        for lba in injectUECC_list:
            pca = self.get_PCA_and_print(lun=lun, lba=lba)
            self.inject_UECC(pca=pca, SLC_enable=True)
            
        logger.flow(6, 'Unmap some LBAs overlap with UECC LBAs')
        lba = 13107
        length = 12
        unmap = ExecuteCMD.Unmap()
        unmap.assign(lun=lun, lba=lba, length=length)
        ExecuteCMD.enqueue(unmap)
        logger.info(f'push: Unmap LUN{lun}, lba = {lba}, length = {length}')
        ExecuteCMD.send(clear_on_success=False)
        for cmd in ExecuteCMD._cmd_list:
            api.save_write_info_by_cmd(cmd, self.write_record)   
        ExecuteCMD.clear()
            
        logger.flow(7, 'Host Read the injected error LBAs and unmap LBAs')
        lba = 13094
        length = 72
        read10 = ExecuteCMD.Read10()
        read10.assign(lun=lun, lba=lba, length=length)
        cmd = ExecuteCMD.enqueue(read10)
        logger.info(f'push: read LUN{lun}, lba = {lba}, length = {length}')
        try:
            ExecuteCMD.send(clear_on_success=False)
            response = ExecuteCMD.read_response(cmd)
        except DLL_RESPONSE_ERROR:
            response = ExecuteCMD.read_response(cmd)
            logger.warning(f"lun = {response.upiu.b2_lun}, task_tag = {hex(response.upiu.b3_tasktag)},  response = {get_cmd_response_byte_str(response)}, status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}")
        ExecuteCMD.clear()
        if response.upiu.b6_response != api.UPIUResponse.TARGET_FAILURE or response.upiu.b7_status != api.ScsiStatus.CHECK_CONDITION or response.b32_sense_data.b2_sense_key != api.SenseKey.MEDIUM_ERROR:
            logger.error_lb(f'check read resp after read uecc area')
            logger.error_fp(f'expect response fail, but status = {get_scsi_status_str(response)}, sense_key = {get_sense_key_str(response)}, asc = {get_asc_ascq_description(response)}')
            raise SIGHTING_RESPONSE_UNEXPECTED
        
        logger.flow(8, 'Host Read the non-injected LBAs and non-unmaped LBAs')
        length = 1
        for lba in range(0, 13096):
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=lun, lba=lba, length=length)
            ExecuteCMD.enqueue(read10)
            # logger.info(f'push: read LUN{lun}, lba = {lba}, length = {length}')
        for lba in range(13124, 13124 + 9926):
            read10 = ExecuteCMD.Read10()
            read10.assign(lun=lun, lba=lba, length=length)
            ExecuteCMD.enqueue(read10)
            # logger.info(f'push: read LUN{lun}, lba = {lba}, length = {length}')
        ExecuteCMD.send()

    def post_process(self) -> None:
        self.hw_setting.update_from_device()
        self.hw_setting.set_local_val(api.HwSettingField.FW_DEBUG_MODE, self.fw_debug_mode_bkup)
        self.hw_setting.set_to_device()
        pass
    
    
    def split_range_excluding(self, start: int, end: int, exclude_list: List[int]) -> List[List[int]]:
        if start >= end:
            return []
        excl = sorted({x for x in exclude_list if start <= x < end})
        out: List[List[int]] = []
        cur = start
        for x in excl:
            if x > cur:
                out.append([cur, x - cur])
            cur = x + 1
            if cur >= end:
                break
        if cur < end:
            out.append([cur, end - cur])
        return out
    
    def get_PCA_and_print(self, lun: int, lba: int) -> L2P_PCA | project_api.physical_address_info:
        if USE_PHISON_VU:
            pca = lba_to_pba(lun, lba)
            logger.info(f'Lun{lun}, LBA = {lba}: Block = {(pca.w10_block.value)}, mode = {pca.b4_mode.value}, CE = {pca.b5_ce.value}, Plane = {pca.b6_plane.value}, fPage = {pca.l12_fpage.value}(pageline = {pca.l12_fpage.value>>5}), lmu = {pca.b20_lmu.value}, format = {pca.b7_format.value}')
            return pca
        else:
            return get_PCA_and_print(lun, lba)
        
    def inject_UECC(self, pca:L2P_PCA | project_api.physical_address_info, SLC_enable:bool = False) -> None:
        if isinstance(pca, L2P_PCA):
            dire_read_payload = bytearray(DATA_SIZE_16K_BYTE)
            for i in range(len(dire_read_payload)):
                dire_read_payload[i] = 0xAA
            logger.info(f'Inject UECC: Block = {(pca.w10_block.value)}, mode = {pca.b4_mode.value}, CE = {pca.b5_ce.value}, Plane = {pca.b6_plane.value}, fPage = {pca.l12_fpage.value}(pageline = {pca.l12_fpage.value>>5}), lmu = {pca.b20_lmu.value}, format = {pca.b7_format.value}')
            temp_pca = PCA()
            temp_pca.from_bytes(bytearray(pca.payload))
            api.direct_write(pca = temp_pca, block_count=4, data_buffer=dire_read_payload)
            pass
        elif isinstance(pca, project_api.physical_address_info):
            inject_UECC(pca=pca, SLC_enable=SLC_enable)
            
    def random_distribute(self,config_au:int,lun_list:list[int]) -> Dict[int,int]:
        base_au = config_au // len(lun_list)
        extra_au = config_au % len(lun_list)
        lun_au_map = {i:base_au for i in lun_list}
        for i in random.sample(lun_list, extra_au):
            lun_au_map[i] += 1
        return lun_au_map
    def config_lun(self, normal_ratio:int, em1_ratio:int) -> tuple[list[int], list[int]]:
        max_lun_cnt = self._param.gMaxNumberLU 
        normal_lun_count = 0
        em1_lun_count = 0
        total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        
        #get each config au
        config_normal_au = (total_au * normal_ratio) // 100
        config_em1_au = total_au - config_normal_au

        #dispatch each lun cnt
        if normal_ratio > 0 and em1_ratio > 0:
            normal_lun_count = random.randint(1, max_lun_cnt -1)
            em1_lun_count = random.randint(1, max_lun_cnt - normal_lun_count)
        elif normal_ratio > 0:
            normal_lun_count = random.randint(1, max_lun_cnt)
        else:
            em1_lun_count = random.randint(1, max_lun_cnt)
        
        #get choosen lun list
        all_luns = list(range(max_lun_cnt))
        normal_luns_list = random.sample(all_luns, normal_lun_count)
        remaining = [i for i in all_luns if i not in normal_luns_list]
        em1_luns_list = random.sample(remaining, em1_lun_count)
        
        if config_normal_au > 0:
            normal_lun_au_map = self.random_distribute(config_normal_au, normal_luns_list)
        if config_em1_au > 0:
            em1_lun_au_map = self.random_distribute(config_em1_au, em1_luns_list)
        
        config_descs = api.get_config_descriptors(print=False)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b0_lu_enable = 0
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].l4_num_alloc_units = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xc
                config_descs[table].units[unit].b10_provisioning_type = ProvisioningType.THIN_PROVISIONING_ERASE
                if (table * 8 + unit) in normal_luns_list:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b3_memory_type = MemoryType.NORMAL
                    config_descs[table].units[unit].l4_num_alloc_units = normal_lun_au_map[table * 8 + unit]
                elif (table * 8 + unit) in em1_luns_list:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b3_memory_type = MemoryType.ENHANCED_1
                    config_descs[table].units[unit].l4_num_alloc_units =em1_lun_au_map[table * 8 + unit]
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = 0
        config_descs[3].header.b2_conf_desc_continue = 0

        for table in range(4):
            api.push_write_config(config_descs[table], index=table)

        ExecuteCMD.send()
        ExecuteCMD.clear()
        config_descs = api.get_config_descriptors(print=True)

        #update descriptor to get new capacity
        unit_desc_idxes:List[int] = []
        for lun in range(0, self._param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            api.update_descriptor(DescriptorIDN.UNIT, index, cast(api.QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        #test unit ready all enable lun
        for lun in range(self._param.gMaxNumberLU):
            if self._param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

        return (normal_luns_list, em1_luns_list)

run = Pattern().run
if __name__ == "__main__":
    run()