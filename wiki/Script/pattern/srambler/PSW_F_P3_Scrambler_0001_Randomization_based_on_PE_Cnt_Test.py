import package_root
from Script import api
from Script.api import cmd_seq as ExecuteCMD
from Script.api import dumpfile
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api import shared
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import PCA
from Script.api.ufs_api.defines.constant_define import *
import copy
from Script.api.ufs_api import update_descriptor, QueryResponse,DescriptorIDN
from typing import List,cast

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self._param = shared.param
        self.total_au = self._param.gGeometry.q4_total_raw_device_capacity // (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size)
        self.fw_geometry = api.get_fw_geometry()
        self.TLC_VB_4K_SIZE = (self.fw_geometry.l88_vb_size_u1 * 512) // api.DATA_SIZE_4K_BYTE
        self.SLC_VB_4K_SIZE = (self.fw_geometry.l84_vb_size_u0 * 512) // api.DATA_SIZE_4K_BYTE
        self.wb_au = self._param.gGeometry.l79_write_booster_buffer_max_n_alloc_units
        self.wb_total_len = self.wb_au *  (self._param.gGeometry.l13_segment_size * self._param.gGeometry.b17_allocation_unit_size) // DATA_SIZE_4K_BYTE
        pass

    def step1(self) -> None:
        for case in ["L1", "SLC_L2", "WB_L2", "TLC_L2","PTE", "LOG"]: 
            logger.flow(1, f'case = {case}')
            logger.flow(1, 'Config')
            if case == "WB_L2" or case == "TLC_L2" or case == "PTE" or case == "LOG" or case == "L1":
                slc_lun, tlc_lun = self.config_lun(slc_au=0, tlc_au=self.total_au, wb_au=self.wb_au)
            else:
                slc_lun, tlc_lun = self.config_lun(slc_au=self.total_au, tlc_au=0)

            if case == "L1":
                lun = tlc_lun
                total_len = 4
            elif case == "TLC_L2" or case == "PTE" or case == "LOG":
                lun = tlc_lun
                total_len = self.TLC_VB_4K_SIZE - 1
            elif case == "WB_L2":
                lun = tlc_lun
                total_len = self.SLC_VB_4K_SIZE - 1
            else:
                lun = slc_lun
                total_len = self.SLC_VB_4K_SIZE - 1

            if case == "WB_L2":
                logger.flow(2, 'Enable writebooster')
                api.set_flag(api.FlagIDN.WRITEBOOSTER_EN)
            else:
                api.clear_flag(api.FlagIDN.WRITEBOOSTER_EN)

            logger.flow(2, f'Write 1 {case} VB')
            self.write_data(lun=lun,start_lba=0,len=api.WRITE_10_MAX_BLOCK_LEN,total_len=total_len)
            
            pca = PCA()
            if case == "LOG":
                logger.flow(3, 'Send VUC = 420D to get log vb pca')
                _, open_vb_info = api.get_open_vb_info()
                vb_number = open_vb_info.LOG.logical_vb.value
                pca.b5_ce = 0
                pca.b6_plane = 0
                pca.l12_fpage = 0
                pca.b11_block_h = (vb_number >> 8) & 0xFF
                pca.b10_block_l = vb_number & 0xFF
            elif case == "L1":
                logger.flow(3, 'Send VUC = 420D to get L1 pca')
                _, open_vb_info = api.get_open_vb_info()
                vb_number = open_vb_info.TLC_L1.logical_vb.value
                pca.b5_ce = 0
                pca.b6_plane = 0
                pca.l12_fpage = 0
                pca.b11_block_h = (vb_number >> 8) & 0xFF
                pca.b10_block_l = vb_number & 0xFF
            else:
                logger.flow(3, 'Send 4051 to get pca')
                _, vu_pca = project_api.issue_4051_to_get_physical_address(luID=lun, lba=0)
                if case == "WB_L2" or case == "TLC_L2" or case == "SLC_L2":
                    vb_number = vu_pca.virtual_block_number.value
                    pca.b5_ce = vu_pca.die.value
                    pca.b6_plane = vu_pca.plane.value
                    pca.l12_fpage = vu_pca.page.value
                    pca.b11_block_h = (vu_pca.virtual_block_number.value >> 8) & 0xFF
                    pca.b10_block_l = vu_pca.virtual_block_number.value & 0xFF
                
                elif case == "PTE":
                    vb_number = vu_pca.PPT_virtual_block_number.value
                    pca.b5_ce = vu_pca.PPT_die.value
                    pca.b6_plane = vu_pca.PPT_plane.value
                    pca.l12_fpage = int(vu_pca.PPT_page.value * 32 + vu_pca.PPT_offset.value)
                    pca.b11_block_h = (vu_pca.PPT_virtual_block_number.value >> 8) & 0xFF
                    pca.b10_block_l = vu_pca.PPT_virtual_block_number.value & 0xFF


            logger.flow(4, 'Send 4060 with step3 pca get raw data (scramble_enable = 0)')
            if case == "TLC_L2":
                slc_enable = 0
            else:
                slc_enable = 1
            
            undescramble_data = self.get_raw_data_buffer(pca, SLC_Enable=slc_enable, Scramble_Enable=0, ECC_Enable=1,desc="step4") #why data length not expect
            if case == "LOG":
                backup_undescramble_data = []
                for page in range(open_vb_info.LOG.first_empty_physical_page.value):
                    pca.l12_fpage = page << 5
                    backup_undescramble_data.append(self.get_raw_data_buffer(pca, SLC_Enable=slc_enable, Scramble_Enable=0, ECC_Enable=1))
                pca.l12_fpage = 0

            logger.flow(5, 'Send 4060 with step3 pca get raw data (scramble_enable = 1)')
            descramble_data = self.get_raw_data_buffer(pca, SLC_Enable=slc_enable, Scramble_Enable=1, ECC_Enable=1)
            logger.flow(6, 'Check randomizer is appiled on data')
            data_size = DATA_SIZE_16K_BYTE
            same = self.compare_payload(undescramble_data[:data_size], descramble_data[:data_size])
            if same == True:
                logger.error('Srammble data should not be same as unscramble data')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(7, 'Check randomizer is appiled on spare area')
            spare_area_size = 4 * 16
            read_status_size = 4
            same = self.compare_payload(undescramble_data[data_size + read_status_size:data_size + read_status_size+spare_area_size], descramble_data[data_size + read_status_size:data_size + read_status_size+spare_area_size])
            if same == True:
                logger.error('Srammble spare area should not be same as unscramble spare area')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL
            
            logger.flow(8, 'Get Erase count of vb')
            ec_cnt = self.get_vb_ec_cnt(vb_number)
            
            logger.flow(9, 'Send 40F6 to erase vb')
            die = 1 << pca.b5_ce
            plane = 1 << pca.b6_plane
            project_api.issue_40F6_to_erase_in_direct_nand_mode(die=die,plane=plane,start_blk=vb_number,end_blk=vb_number+1,slc_enable=slc_enable)

            logger.flow(10, 'Send C083 to set ec count = step 5 + 1 times')
            set_ec_val = ec_cnt + 1
            set_ec_table = self.set_vb_ec_cnt(vb_number,set_ec_val)

            logger.flow(11, 'Send C060 to write raw data on vb number (payload = data from step4)')
            metadata = descramble_data[0x4004:0x4044]
            data_payload = copy.deepcopy(descramble_data)
            data_payload[0x4000:0x4040] = metadata
            project_api.issue_C060_to_write_raw_data(Ce=pca.b5_ce,Block=vb_number,Plane=pca.b6_plane, Page=pca.l12_fpage >> 5,SLC_Enable=slc_enable,Ecc_Enable=1, datapayload=data_payload)
            
            logger.flow(12, 'Send 4060 with step3 pca get raw data')
            step12_undescramble_data = self.get_raw_data_buffer(pca, SLC_Enable=slc_enable, Scramble_Enable=0, ECC_Enable=1,desc="step12")

            logger.flow(13, 'Check step4 and step 12 data is not the same')
            same = self.compare_payload(undescramble_data, step12_undescramble_data, partial=True)
            if same == True:
                logger.error('randomizer should base on ec count, write same data on vb with ec and ec+1 should not get same data')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(14, 'Send 40F6 to erase vb')
            die = 1 << pca.b5_ce
            plane = 1 << pca.b6_plane
            project_api.issue_40F6_to_erase_in_direct_nand_mode(die=die,plane=plane,start_blk=vb_number,end_blk=vb_number+1,slc_enable=slc_enable)

            logger.flow(15, 'Send C083 to set ec count = step 5 + 8 times')
            set_ec_val = ec_cnt + 8
            set_ec_table = self.set_vb_ec_cnt(vb_number,set_ec_val)

            logger.flow(16, 'Send C060 to write raw data on vb number (payload = data from step4)')
            metadata = descramble_data[0x4004:0x4044]
            data_payload = copy.deepcopy(descramble_data)
            data_payload[0x4000:0x4040] = metadata
            project_api.issue_C060_to_write_raw_data(Ce=pca.b5_ce,Block=vb_number,Plane=pca.b6_plane, Page=pca.l12_fpage >> 5,SLC_Enable=slc_enable,Ecc_Enable=1, datapayload=data_payload)

            logger.flow(17, 'Send 4060 with step3 pca get raw data')
            step17_undescramble_data = self.get_raw_data_buffer(pca, SLC_Enable=slc_enable, Scramble_Enable=0, ECC_Enable=1, desc="step17")

            logger.flow(18, 'Check step4 and step 17 data is the same')
            same = self.compare_payload(undescramble_data, step17_undescramble_data, partial=True)
            if same != True:
                logger.error('randomizer should base on ec count, write same data on vb with ec and ec+8 should get same data')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(19, 'Send 40F6 to erase vb')
            die = 1 << pca.b5_ce
            plane = 1 << pca.b6_plane
            project_api.issue_40F6_to_erase_in_direct_nand_mode(die=die,plane=plane,start_blk=vb_number,end_blk=vb_number+1,slc_enable=slc_enable)

            logger.flow(20, 'Send C083 to set ec count = step 5 + 9 times')
            set_ec_val = ec_cnt + 9
            set_ec_table = self.set_vb_ec_cnt(vb_number,set_ec_val)

            logger.flow(21, 'Send C060 to write raw data on vb number (payload = data from step4)')
            metadata = descramble_data[0x4004:0x4044]
            data_payload = copy.deepcopy(descramble_data)
            data_payload[0x4000:0x4040] = metadata
            project_api.issue_C060_to_write_raw_data(Ce=pca.b5_ce,Block=vb_number,Plane=pca.b6_plane, Page=pca.l12_fpage >> 5,SLC_Enable=slc_enable,Ecc_Enable=1, datapayload=data_payload)
            
            logger.flow(22, 'Send 4060 with step3 pca get raw data')
            step22_undescramble_data = self.get_raw_data_buffer(pca, SLC_Enable=slc_enable, Scramble_Enable=0, ECC_Enable=1, desc="step22")

            logger.flow(23, 'Check step12 and step 22 data is the same')
            same = self.compare_payload(step12_undescramble_data, step22_undescramble_data, partial=True)
            if same != True:
                logger.error('randomizer should base on ec count, write same data on vb with ec and ec+8 should get same data')
                raise SIGHTING_FAIL_DATA_COMPARE_FAIL

            logger.flow(24, 'Send C083 to set ec count = step 5 for recover')
            set_ec_val = ec_cnt 
            set_ec_table = self.set_vb_ec_cnt(vb_number,set_ec_val)

            logger.flow(25, 'Send 40F6 to erase vb')
            die = 1 << pca.b5_ce
            plane = 1 << pca.b6_plane
            project_api.issue_40F6_to_erase_in_direct_nand_mode(die=die,plane=plane,start_blk=vb_number,end_blk=vb_number+1,slc_enable=slc_enable)

            logger.flow(26, 'Send C060 to write raw data on vb number (payload = data from step4)')
            if case == "LOG":
                for page in range(open_vb_info.LOG.first_empty_physical_page.value):
                    data = backup_undescramble_data[page]
                    metadata = data[0x4004:0x4044]
                    data_payload = copy.deepcopy(data)
                    data_payload[0x4000:0x4040] = metadata
                    project_api.issue_C060_to_write_raw_data(Ce=pca.b5_ce,Block=vb_number,Plane=pca.b6_plane, Page=page,SLC_Enable=slc_enable,Ecc_Enable=1, datapayload=data_payload)
            else:
                metadata = descramble_data[0x4004:0x4044]
                data_payload = copy.deepcopy(descramble_data)
                data_payload[0x4000:0x4040] = metadata
                project_api.issue_C060_to_write_raw_data(Ce=pca.b5_ce,Block=vb_number,Plane=pca.b6_plane, Page=pca.l12_fpage >> 5,SLC_Enable=slc_enable,Ecc_Enable=1, datapayload=data_payload)
                
        pass
    def randomizer_by_page_test(self) -> None:
        pass
    def test_flow(self) -> None:
        logger.info('[data2 4KB]')
        data2 = bytearray([0xAB] * 4096)
        logger.print_buffer(data2)
        w = ExecuteCMD.Write10()
        w.data = data2 
        w.assign(lun=0, lba=0, length=1, fua=1).set_option(manual_mode=True).enqueue()
    def post_process(self) -> None:
        pass
 
    def get_vb_ec_cnt(self, vb_number:int) -> int:
        rsp, data_payload = project_api.issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0=project_api.VU4097Paremeter.GET_EC_TABLE)
        erase_cnt_from_vu = int.from_bytes(data_payload[vb_number*4 : (vb_number + 1)*4], 'little')
        logger.info(f'vb number = {vb_number}, ec = {erase_cnt_from_vu}')
        return erase_cnt_from_vu

    def compare_payload(self,payload1:bytearray, payload2:bytearray, partial:bool=False) -> bool:
        if not partial:
            return payload1 == payload2
        
        if payload1[:0x4004] != payload2[:0x4004]:
            return False

        base = 0x4004
        step = 16
        temp_offset = 8
        for node in range(4):
            start = base + node * step
            if payload1[start:start + temp_offset] != payload2[start:start + temp_offset]:
                return False
            if payload1[start + temp_offset + 1:start+step] != payload2[start + temp_offset + 1:start+step]:
                return False
        return True

    def write_data(self,lun:int, start_lba:int, len:int, total_len:int) -> None:
    
        while total_len > 0:
            len = min(total_len, len)
            write10 = ExecuteCMD.Write10()
            logger.info(f'start lba = {start_lba}, len = {len}')
            write10.assign(lun=lun, lba=start_lba, length=len, fua=1)
            ExecuteCMD.enqueue(write10)
            start_lba += len
            total_len -= len

        ExecuteCMD.send(timeout=api.UniformTimeout(val=30000, unit=api.TimeResolution.ms), clear_on_success=False)
        ExecuteCMD.clear()
        
    def set_vb_ec_cnt(self,vb_number:int, set_ec_val:int) -> bytearray:
        field_offset = 4
        VB_Num = project_api.VUC083VB_Num.CHANGE_THE_EC_ONLY_IN_RAM
        _, curr_ec_table = project_api.issue_4097_to_get_erase_read_count_etc_tables_cis_tables(Parameter0=project_api.VU4097Paremeter.GET_EC_TABLE)
        bytes_val = set_ec_val.to_bytes(field_offset, 'little')
        curr_ec_table[vb_number * field_offset : (vb_number+1)*field_offset] = bytes_val
        response = project_api.issue_C083_to_set_erase_read_count_parameter(Parameter0=project_api.VUC083Paremeter.SET_EC_TABLE, VB_Num=VB_Num, RC_TH_Value=0, data_payload=curr_ec_table)
        return curr_ec_table
   
    def get_raw_data_buffer(self,pca:PCA,SLC_Enable:int,Scramble_Enable:int, ECC_Enable:int, desc:str="") -> bytearray:
        block = (pca.b11_block_h << 8) +  pca.b10_block_l
        _, dire_read_payload2 = project_api.issue_4060_to_read_raw_data(Die=pca.b5_ce, Plane=pca.b6_plane, Block=block, Page= pca.l12_fpage >>5, SLC_Enable=SLC_Enable, Ecc_Enable=ECC_Enable, Scrambler_Enable=Scramble_Enable)
        dumpfile(f'data_srcamble_{Scramble_Enable}_ECC_{ECC_Enable}_{desc}.bin', dire_read_payload2)
        return dire_read_payload2[:16452]  #bcs cmd seq aligh 512, will output other no need buffer
    def config_lun(self, slc_au:int, tlc_au:int, wb_au:int = 0) -> tuple[int,int]:
        
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
        config_descs[0].header.b7_secure_removal_type = 0
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

        #test unit ready all enable lun
        for lun in range(self._param.gMaxNumberLU):
            if self._param.gUnit[lun].b3_lu_enable:
                test_unit_ready = ExecuteCMD.CmdSeqTestUnitReady()
                test_unit_ready.set_option(lun)
                ExecuteCMD.enqueue(test_unit_ready)
        ExecuteCMD.send(clear_on_success=False)
        ExecuteCMD.clear()

        slc_lun = 0
        tlc_lun = 1
        return (slc_lun, tlc_lun) 
run = Pattern().run
if __name__ == "__main__":
    run()