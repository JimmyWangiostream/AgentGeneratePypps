import package_root
from Script import api
from Script.api.util.functions import dumpfile
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.cmd_seq.response import CommandResponse
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig, get_flash_setting, get_vb_info
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api import read_fw_value, vendor_cmd
import time
#from Script.project_api.block_budget.structs import GetCSICSInfoDescription, GetBoundaryBlocksForHiddenTableStaticDynamicPool, VBCount
import inspect
from Script.api.ufs_api.defines import CmdParamPatternMode, CompareMethod
#from Script.project_api.functions import issue_40F6_to_erase_in_direct_nand_mode,issue_4051,issue_40F5_to_PTE_Recovery
from typing import Any, List, cast
from Script.api.ufs_api import WellKnownLUN, init_tester_to_unit_ready
from Script.api import (shared, ExecuteCMD,
                        Dcmd5ResetType)
from Script.api.ufs_api.vendor_cmd.structs import PCA
from Script.api.ufs_api.defines.enum_define import RPMBRegion, RPMBVendorType, VendorCmd, VendorCmdRuleCdb2, VendorCmdRuleCdb3
from Script.api.ufs_api.vendor_cmd.functions import access_vendor_mode
from Script.project_api.custom_vu.erase_nand_pte.functions import issue_40F5_to_PTE_Recovery
from Script.project_api.custom_vu.lba_convert_vu import issue_4051_to_get_physical_address

def check_timeout(start_time: float, timeout_min: int, timeout_sec:int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60 + timeout_sec:
        return True
    else:
        return False

def ori_lba_to_pba(lun: int, lba: int, rpmb_region: int = 0) -> PCA:

    access_vendor_mode()

    vuc = ExecuteCMD.VendorCmdRead()
    vuc.assign(length=DATA_SIZE_4K_BYTE, cmd_index=VendorCmd.L2P_READ, cmd_set_type=0x0F)
    vuc.upiu.u16_cdb.b2_rsvd = VendorCmdRuleCdb2.CMD_IN_CDB
    vuc.upiu.u16_cdb.b3_rsvd = VendorCmdRuleCdb3.CMD_OTHER

    vuc.upiu.u16_cdb.l8_pw_h = int.from_bytes(lba.to_bytes(4, byteorder='little', signed=False), byteorder='big')
    vuc.upiu.u16_cdb.l12_pw_l = lun << 24 | rpmb_region << 16
    idx = vuc.enqueue()
    ExecuteCMD.send(clear_on_success=False)
    rsp = ExecuteCMD.read_response(idx)
    ExecuteCMD.clear()

    pca = PCA()
    pca.from_bytes(rsp.data)

    return pca
def is_bit4_set(n:int)->bool:
    return (n & 0x10) != 0
def show_pca(pca:PCA)->None:
    logger.info(f'PCA: Block = {(pca.b11_block_h<<8) | (pca.b10_block_l)}, mode = {pca.b4_mode}, CE = {pca.b5_ce}, Plane = {pca.b6_plane}, fPage = {pca.l12_fpage}(pageline = {pca.l12_fpage>>5}), lmu = {pca.b20_lmu}')

class Pattern(UFSTC):
    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)    
        self.random_en_lun = 0
        logger.flow(5,'option 5 test')
        self.erase_all_card()

        #self.sub_opcode5_test_1()
        self.sub_opcode5_test()

        self.write_one_used_vb_get_logical_vb()


        logger.flow(1,'option 1 test')
        self.sub_opcode1_test()
        logger.flow(2,'option 2 test')
        self.sub_opcode2_test()
        logger.flow(3,'option 3 test')
        self.sub_opcode3_test()# bug return 0xFF
        logger.flow(4,'option 4 test')
        self.sub_opcode4_test()
        logger.flow(6,'option 6 test')
        self.sub_opcode6_test()

        pass
    def flow3(self) -> None:
        logger.flow(3,'Issue 40DC VUC to get next TLC VB')
        response, self.next_vb_info = project_api.issue_40DC_to_get_next_open_vb_information(0)  
        pass
    def flow4(self) -> None:
        logger.flow(4,'Host can get byte[4:7] to get next VB index')
        self.next_vb_idx = self.next_vb_info.DM_NORMAL_HOST_VB.value
        logger.flow(4,f'next_vb_idx = {self.next_vb_idx}')
        pass    
    def write_one_used_vb_get_logical_vb(self)->int:
        self.flow3()
        self.flow4()
        vb = 0
        self.fw_geometry = api.get_fw_geometry()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)        
        logger.flow(1,'write data on lun1, 16M, get PCA')
        lun = 0
        lba = 0
        chunk_size = 65535
        total_len = 65535 * 6
        #self.show_vb_info(10)
        while(total_len):
            write10 = ExecuteCMD.Write10()
            write10.assign(lun=lun, lba=lba, length=chunk_size, fua=0)
            write10.set_option(pattern_mode=CmdParamPatternMode.HW_FIX)
            ExecuteCMD.enqueue(write10)

            ExecuteCMD.send(clear_on_success=False)
            ExecuteCMD.clear()
            chunk_size = min(chunk_size,total_len)
            total_len -= chunk_size
        pca = ori_lba_to_pba(0,0)
        vb = (pca.b11_block_h << 8) + pca.b10_block_l
        _,pca = issue_4051_to_get_physical_address(lun, lba)
        return vb
    
    def write_4k_get_logical_vb(self, data_size_4k:int)->int:
        vb = 0
        self.fw_geometry = api.get_fw_geometry()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)        
        logger.flow(1,'write data on lun1, 16M, get PCA')
        lun = 0
        lba = 0
        chunk_size = 65535
        total_len = data_size_4k
        while(total_len):
            write10 = ExecuteCMD.Write10()
            chunk_size = min(chunk_size,total_len)
            write10.assign(lun=lun, lba=lba, length=chunk_size, fua=0)
            write10.set_option(pattern_mode=CmdParamPatternMode.HW_FIX)
            ExecuteCMD.enqueue(write10)

            ExecuteCMD.send(clear_on_success=False)
            ExecuteCMD.clear()
            total_len -= chunk_size
        pca = ori_lba_to_pba(0,0)
        vb = (pca.b11_block_h << 8) + pca.b10_block_l
        return vb    
    def read_cmd(self, lun:int,lba:int, len:int)->None:      

        read10 = ExecuteCMD.Read10()
        read10.assign(lun=lun, lba=lba, length=len, fua=0)
        ExecuteCMD.enqueue(read10)
        try:
            ExecuteCMD.send(clear_on_success=False)
            #rsp = cast(CommandResponse, ExecuteCMD.read_response(read10))
        except api.TIMEOUT_EXCEPTIONS:
            logger.info('send command error')
            #rsp = cast(CommandResponse, ExecuteCMD.read_response(read10))
        ExecuteCMD.clear()

    def sub_opcode2_test(self)->None: # check if in free vb list
        logger.flow(1, 'get free vb')
        free_vb_list = self.get_target_vb_list(27)
        used_vb_list = self.get_target_vb_list(17)
        rsp, payload = issue_40F5_to_PTE_Recovery(2, free_vb_list[0])
        logger.info(f'free blk in option 2 = {payload[0]}') #expected = 1
        if payload[0] != 1:
            logger.error_fp(f'free blk option 2 = {payload[0]} != 1')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL        
        rsp, payload = issue_40F5_to_PTE_Recovery(2, used_vb_list[0])   
        logger.info(f'used_vb_list in option 2 = {payload[0]}') #expected = 2
        if payload[0] != 2:
            logger.error_fp(f'used blk option 2 = {payload[0]} != 2')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL          
    def sub_opcode1_test(self)->None:
        logger.flow(1, 'get free vb')
        target_used_vb = self.write_one_used_vb_get_logical_vb()
        free_vb_list = self.get_target_vb_list(27)
        used_vb_list = self.get_target_vb_list(17)
        rsp, payload = issue_40F5_to_PTE_Recovery(1, free_vb_list[0])
        logger.info(f'free blk in option 1 = {payload[0]}') #expected = 1
        if payload[0] != 1:
            logger.error_fp(f'free blk option 1 = {payload[0]} != 1')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL        
        rsp, payload = issue_40F5_to_PTE_Recovery(1, used_vb_list[0])   
        logger.info(f'used_vb_list in option 1 = {payload[0]}') #expected = 2
        if payload[0] != 2:
            logger.error_fp(f'used blk option 1 = {payload[0]} != 2')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL   
    def sub_opcode3_test(self)->None: # check if in free vb list
        rsp, payload = issue_40F5_to_PTE_Recovery(3, random.randint(0x1, 0xFFFFFFFF))
        if payload[0] != 1:
            logger.error_fp(f'used blk option 3 = {payload[0]} != 1')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL         
        pass
    def sub_opcode4_test(self)->None: # check if in free vb list
        rsp, payload = issue_40F5_to_PTE_Recovery(4, random.randint(0x1, 0xFFFFFFFF))
        if payload[0] != 1:
            logger.error_fp(f'used blk option 4 = {payload[0]} != 1')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL   
        pass
    def sub_opcode6_test(self)->None: # check if in free vb list
        logger.flow(1, 'get free vb')
        used_vb_list = self.get_target_vb_list(17)
        target_vb = used_vb_list[0]
        logger.info(f'select used vb = {target_vb}')
        rsp, payload = issue_40F5_to_PTE_Recovery(6, target_vb)
        if payload[0] != 1:
            logger.error_fp(f'rsp = {payload[0]} != 1')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL             
        used_vb_list = self.get_target_vb_list(17)
        if target_vb in used_vb_list:
            logger.error_fp(f'target_vb {target_vb} in used_vb_list {used_vb_list}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL             
        free_vb_list = self.get_target_vb_list(27)
        if target_vb not in free_vb_list:
            logger.error_fp(f'target_vb {target_vb} not in free_vb_list {free_vb_list}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL  
        
    def erase_all_card(self)->None:
        start_lba = 0
        data_len = 65535
        _param = shared.param
        continue_push_unmap = True
        while continue_push_unmap:
            start_lba = min(start_lba, _param.gLUCapacity[self.random_en_lun])
            if (start_lba + data_len) > _param.gLUCapacity[self.random_en_lun]:
                data_len = _param.gLUCapacity[self.random_en_lun] - start_lba
                continue_push_unmap = False
            logger.info(f'unmap, start_lba = {start_lba}, data_len = {data_len}')
            unmap = ExecuteCMD.Unmap()
            unmap.assign(lun=self.random_en_lun, lba=start_lba, length=data_len)
            ExecuteCMD.enqueue(unmap)      
            start_lba += data_len
        ExecuteCMD.send(clear_on_success=True)
        idn = api.FlagIDN.PURGE_EN
        set_flag = ExecuteCMD.SetFlag().assign(idn).enqueue()
        ExecuteCMD.send(clear_on_success=True)
        timeout_min = 0
        timeout_sec = 2000
        start_time = time.time()
        polling_cnt = 0
        while True:
            if check_timeout(start_time, timeout_min, timeout_sec):
                raise PATTERN_ASSERT_STUCK_WHILE_TIMEOUT
            purge_status = api.read_attribute(idn=api.AttributeIDN.PURGE_STATUS)
            polling_cnt += 1
            logger.info(f'purge status = {purge_status}, polling count = {polling_cnt}')
            if purge_status == 0x03:
                logger.info(f'purge status = {purge_status}, complete')
                break
        pass        

    def sub_opcode5_test(self)->None:
        logger.flow(1, 'get free vb')
        target_used_vb = self.write_4k_get_logical_vb(256)
        used_vb_list = self.get_target_vb_list(17)
        rsp, payload = issue_40F5_to_PTE_Recovery(5, target_used_vb)
        if payload[0] != 0:
            logger.error_fp(f'rsp = {payload[0]} != 0')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL                
        logger.info(f'option 5 test : {payload[0]}')
        target_used_vb = self.write_4k_get_logical_vb(self.tlc_vb_size )

        pca = ori_lba_to_pba(0,0)
        write_buffer = bytearray(4096)
        write_buffer_0xff = bytearray([0xFF] * 4096)
        backup_lmu = pca.b20_lmu
        pca.b20_lmu = 0
        
        lba = 1
        pca_other_plane = PCA()
        pca_other_plane.b38_plane = pca.b38_plane
        while pca_other_plane.b38_plane == pca.b38_plane:
            pca_other_plane = ori_lba_to_pba(0,lba)
            lba += 1
        show_pca(pca_other_plane)
        show_pca(pca)
        vendor_cmd.direct_write(pca,1,write_buffer)
        vendor_cmd.direct_write(pca_other_plane,1,write_buffer_0xff)
        logger.info(f'target vb = {target_used_vb}')
        rsp, payload = issue_40F5_to_PTE_Recovery(6, target_used_vb)

        
        payload = vendor_cmd.direct_read(pca, 1,include_FW_spare = True)
        logger.flow(3,'check if data uecc')
        status_of_blk = payload[128 + DATA_SIZE_4K_BYTE]
        logger.info(f'status_of_blk = {status_of_blk}')
        if not (is_bit4_set(status_of_blk)):        
            logger.info(f'not uecc')
        else:
            logger.info(f'uecc')
        payload = vendor_cmd.direct_read(pca, 1,include_FW_spare = True)
        logger.flow(3,'check if data uecc')
        status_of_blk = payload[128 + DATA_SIZE_4K_BYTE]
        logger.info(f'status_of_blk = {status_of_blk}')            
        if not (is_bit4_set(status_of_blk)):        
            logger.info(f'not uecc')
        else:
            logger.info(f'uecc')            
        # self.read_cmd(0,0,128)
        # self.read_cmd(0,0,128)
        logger.flow(1, 'get vb list')
        vb_list = self.get_vb_list()
        Result_get_uecc_target_vb = False
        for vb in vb_list:
            rsp, payload = issue_40F5_to_PTE_Recovery(5, vb)
            if payload[0] == 1:
                logger.info(f'option 5 test : {vb} result = 1')
                Result_get_uecc_target_vb= True
                break
        if not Result_get_uecc_target_vb: 
            logger.error_fp(f'rsp = {payload[0]} != 1')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL                   
        #init_tester_to_unit_ready(Dcmd5ResetType.RESET_N)
        pass
    def step1(self) -> None:
                       
        pass
    def post_process(self) -> None:
        pass
    def get_target_vb_list(self, group:int)-> list[int]:
        retval = 0
        vb_list = []
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'access_mode': {'pos': 6, 'len': 2, 'mask': 0x3}, 
            'dirty': {'pos': 8, 'len': 1, 'mask': 0x1}, 
        }
        response, rep_data = get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if self.fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break

            ftl_vb_list_data.update({vb : {k: (((rep_data[vb*4]|rep_data[vb*4+1]<<8) >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        used_mlc_cout = 0
        map_vb_cnt = {} # type: ignore
        logger.info(f'[show all vb info at begin]')
        for vb, vb_info in ftl_vb_list_data.items():
            last_type = vb_info['group']
            dirtybit = vb_info['dirty']
            if last_type in map_vb_cnt:
                map_vb_cnt[last_type] += 1
            else:
                map_vb_cnt[last_type] = 1
            logger.info(f'[vb = {vb}, group type = {last_type}, dirtybit = {dirtybit}]')
            if last_type == group:
                vb_list.append(vb)
        for k,v in map_vb_cnt.items():
            logger.info(f'group type = {k}, cnt = {v}]')
        logger.info(f'get target vb list of vb {group} cnt = {len(vb_list)}')
        return vb_list
    def get_vb_list(self)-> list[int]:
        retval = 0
        vb_list = []
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'access_mode': {'pos': 6, 'len': 2, 'mask': 0x3}, 
            'dirty': {'pos': 8, 'len': 1, 'mask': 0x1}, 
        }
        response, rep_data = get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if self.fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break

            ftl_vb_list_data.update({vb : {k: (((rep_data[vb*4]|rep_data[vb*4+1]<<8) >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        used_mlc_cout = 0
        map_vb_cnt = {} # type: ignore
        logger.info(f'[show all vb info at begin]')
        for vb, vb_info in ftl_vb_list_data.items():
            last_type = vb_info['group']
            dirtybit = vb_info['dirty']
            if last_type in map_vb_cnt:
                map_vb_cnt[last_type] += 1
            else:
                map_vb_cnt[last_type] = 1
            logger.info(f'[vb = {vb}, group type = {last_type}, dirtybit = {dirtybit}]')
            vb_list.append(vb)

        return vb_list    

    def show_vb_info(self, group:int)-> int:
        retval = 0
        vb_list_data_format = {
            'group': {'pos': 0, 'len': 6, 'mask': 0x3f}, 
            'access_mode': {'pos': 6, 'len': 2, 'mask': 0x3}, 
            'dirty': {'pos': 8, 'len': 1, 'mask': 0x1}, 
        }
        response, rep_data = get_vb_info()
        dumpfile("rep_data.bin", bytearray(rep_data))
        ftl_vb_list_data = dict()

        for vb in range(len(rep_data)):
            if self.fw_geometry.l52_total_vb_count <= vb:
                break
            if vb *4  >= len(rep_data):
                break

            ftl_vb_list_data.update({vb : {k: (((rep_data[vb*4]|rep_data[vb*4+1]<<8) >> v['pos']) & v['mask']) for k, v in vb_list_data_format.items()}})
        used_mlc_cout = 0
        map_vb_cnt = {}# type: ignore
        logger.info(f'[show all vb info at begin]')
        for vb, vb_info in ftl_vb_list_data.items():
            last_type = vb_info['group']
            dirtybit = vb_info['dirty']
            if last_type in map_vb_cnt:
                map_vb_cnt[last_type] += 1
            else:
                map_vb_cnt[last_type] = 1
            logger.info(f'[vb = {vb}, group type = {last_type}, dirtybit = {dirtybit}]')
            if last_type == group:
                return vb
        for k,v in map_vb_cnt.items():
            logger.info(f'group type = {k}, cnt = {v}]')
        return retval    



run = Pattern().run
if __name__ == "__main__":
    run()