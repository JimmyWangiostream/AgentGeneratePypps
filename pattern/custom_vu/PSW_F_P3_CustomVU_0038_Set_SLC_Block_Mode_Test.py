import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from typing import cast
from Script.api import shared
from Script.api.ufs_api import *
from Script.api.cmd_seq import QueryResponse
from Script.api.ufs_api.vendor_cmd.structs import FwGeometry
from typing import Callable
from Script.project_api.structs import micron_vendor_cmd
from Script.project_api.functions import send_data_in_vcmd, send_data_out_vcmd, send_data_in_vcmd


class Pattern(UFSTC):
    def pre_process(self) -> None:
        pass
    def step1(self) -> None:

        self._param = shared.param
        self.total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.max_wb_size = self._param.gGeometry.l79_write_booster_buffer_max_n_alloc_units
        logger.flow(1, 'Precondition SLC/TLC, WB')
        slc_lun, tlc_lun = self.config_lun(slc_au=self.total_au//2, tlc_au=self.total_au//2, wb_au=self.max_wb_size)
        logger.flow(2, 'write slc data')
        self.write_data(lun=slc_lun,start_lba=0,len=1,total_len=1)

        logger.flow(3, 'write write booster data')
        api.set_flag(FlagIDN.WRITEBOOSTER_EN)
        self.write_data(lun=tlc_lun,start_lba=0,len=1,total_len=1)

        logger.flow(4, 'Send VU D098 mode = 0')
        project_api.issue_D098_to_set_slc_block_mode(mode=0)
        logger.flow(5, 'read slc data, writebooster data')
        self.read_data(lun=slc_lun,start_lba=0,len=1,total_len=1)
        self.read_data(lun=tlc_lun,start_lba=0,len=1,total_len=1)

        logger.flow(6, 'Send VU D098 mode = 1')
        project_api.issue_D098_to_set_slc_block_mode(mode=1)
        logger.flow(7, 'read slc data, writebooster data')
        self.read_data(lun=slc_lun,start_lba=0,len=1,total_len=1)
        self.read_data(lun=tlc_lun,start_lba=0,len=1,total_len=1)

        logger.flow(8, 'Send VU D098 mode = 2')
        project_api.issue_D098_to_set_slc_block_mode(mode=2)
        logger.flow(9, 'read slc data, writebooster data')
        self.read_data(lun=slc_lun,start_lba=0,len=1,total_len=1)
        self.read_data(lun=tlc_lun,start_lba=0,len=1,total_len=1)
        pass

    def post_process(self) -> None:
        pass
    def read_data(self, lun:int, start_lba:int, len:int, total_len:int, write_record:List[List[WriteRecordNode]]=[]) -> None:
        while total_len > 0:
            len = min(total_len, len)
            read10 = ExecuteCMD.Read10()
            logger.info(f'start lba = {start_lba}, len = {len}')
            read10.assign(lun=lun, lba=start_lba, length=len, fua=0)
            ExecuteCMD.enqueue(read10)
            start_lba += len
            total_len -= len
        ExecuteCMD.send(timeout=api.UniformTimeout(val=30000, unit=api.TimeResolution.ms), clear_on_success=False)
        ExecuteCMD.clear()
    def write_data(self, lun:int, start_lba:int, len:int, total_len:int, write_record:List[List[WriteRecordNode]]=[]) -> None:
        while total_len > 0:
            len = min(total_len, len)
            write10 = ExecuteCMD.Write10()
            logger.info(f'start lba = {start_lba}, len = {len}')
            write10.assign(lun=lun, lba=start_lba, length=len, fua=0)
            ExecuteCMD.enqueue(write10)
            start_lba += len
            total_len -= len
        ExecuteCMD.send(timeout=api.UniformTimeout(val=30000, unit=api.TimeResolution.ms), clear_on_success=False)
        ExecuteCMD.clear()
    def config_lun(self, slc_au:int, tlc_au:int, wb_au:int) -> tuple[int,int]:
    
        config_descs = api.get_config_descriptors(print=True)
        for table in range(4):
            for unit in range(8):
                config_descs[table].header.b2_conf_desc_continue = 1
                config_descs[table].units[unit].b0_lu_enable = 0
                config_descs[table].units[unit].b1_boot_lun_id = 0
                config_descs[table].units[unit].l4_num_alloc_units = 0
                config_descs[table].units[unit].b9_logical_block_size = 0xc
                config_descs[table].units[unit].b10_provisioning_type = api.ProvisioningType.THIN_PROVISIONING_ERASE
                if (table * 8 + unit) == 0:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.ENHANCED_1
                    config_descs[table].units[unit].l4_num_alloc_units = slc_au
                elif (table * 8 + unit) == 1:
                    config_descs[table].units[unit].b0_lu_enable = 1
                    config_descs[table].units[unit].b1_boot_lun_id = 0
                    config_descs[table].units[unit].b3_memory_type = api.MemoryType.NORMAL
                    config_descs[table].units[unit].l4_num_alloc_units = tlc_au
        
        config_descs[3].header.b2_conf_desc_continue = 0
        config_descs[0].header.b16_write_booster_buffer_preserve_user_space_en = api.WriteBoosterBufferPreserveUserSpaceEn.ENABLE
        config_descs[0].header.b17_write_booster_buffer_type = api.WriteBoosterBufferType.SHARED
        config_descs[0].header.l18_num_shared_write_booster_buffer_alloc_units = wb_au
        for i in range(4):
            api.push_write_config(config_descs[i], index=i)
        ExecuteCMD.send()
        ExecuteCMD.clear()

        unit_desc_idxes:List[int] = []
        for lun in range(0, self._param.gMaxNumberLU):
            unit_descriptor = ExecuteCMD.ReadDescriptor()
            unit_descriptor.assign(DescriptorIDN.UNIT, lun)
            unit_desc_idxes.append(ExecuteCMD.enqueue(unit_descriptor))

        ExecuteCMD.send(clear_on_success=False)
        for index in unit_desc_idxes:
            update_descriptor(DescriptorIDN.UNIT, index, cast(QueryResponse, ExecuteCMD.read_response(index)))
        ExecuteCMD.clear()

        slc_lun = 0
        tlc_lun = 1
        return (slc_lun, tlc_lun)  

run = Pattern().run
if __name__ == "__main__":
    run()