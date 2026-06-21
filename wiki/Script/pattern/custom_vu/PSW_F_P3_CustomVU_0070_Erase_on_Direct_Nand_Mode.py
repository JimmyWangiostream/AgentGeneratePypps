import package_root
from Script import api
from Script.api.util.functions import dumpfile
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api import cmd_seq as ExecuteCMD
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig, get_flash_setting
from Script.api.ufs_api.defines.constant_define import *
from Script.api.ufs_api import read_fw_value, vendor_cmd
import time
from Script.project_api.block_budget.structs import GetCSICSInfoDescription, GetBoundaryBlocksForHiddenTableStaticDynamicPool, VBCount
import inspect
from Script.api.ufs_api.defines import CmdParamPatternMode, CompareMethod
from Script.project_api.custom_vu.erase_nand_pte.functions import issue_40F6_to_erase_in_direct_nand_mode
import pickle
from Script.api.ufs_api.vendor_cmd.structs import PCA
from Script.api.ufs_api.defines.enum_define import RPMBRegion, RPMBVendorType, VendorCmd, VendorCmdRuleCdb2, VendorCmdRuleCdb3
from Script.api.ufs_api.vendor_cmd.functions import access_vendor_mode


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
def is_bit3_set(n:int)->bool:
    # 0x08 是 1000 (binary)，即第3位为1，其余为0
    return (n & 0x08) != 0
class Pattern(UFSTC):
    def write_data(self, lun:int, start_lba:int, total_size: int, chunk_size:int) -> None:
        chunk_size = 65535
        lba = start_lba
        total_len = total_size
        while(total_len):
            write10 = ExecuteCMD.Write10()
            chunk_size = min(int(chunk_size),int(total_len))
            write10.assign(lun=lun, lba=lba, length=chunk_size, fua=0)
            write10.set_option(pattern_mode=CmdParamPatternMode.HW_FIX)
            ExecuteCMD.enqueue(write10)
            total_len -= chunk_size     
            lba += chunk_size
        ExecuteCMD.send(clear_on_success=True)
         

        
    def pre_process(self) -> None:
        self.fw_geometry = api.get_fw_geometry()
        flash_setting = get_flash_setting()
        self.ce_num = flash_setting.Max_Fdevice        
        self.geometry_desc = api.get_geometry_descriptor()
        self.slc_vb_size = (self.fw_geometry.l84_vb_size_u0 * 512 // 4096)
        self.test_vb = 0
        self.test_ce = 0
        self.tlc_vb_size = (self.fw_geometry.l88_vb_size_u1 * 512 // 4096)           
        logger.flow(1,'write data on lun0, 1.5 tlc vb, get PCA')
        lun = 0
        lba = 0
        chunk_size = 65535
        total_len = self.tlc_vb_size * 1.5
        self.write_data(0, 0, self.tlc_vb_size, 65535)
        pca = ori_lba_to_pba(0,0)
        dump_array = pickle.dumps(pca)
        dump_array = bytearray(dump_array)
        dumpfile('PCA.bin',dump_array)
        blk = (pca.b11_block_h << 8) + pca.b10_block_l
        print(blk)
        logger.flow(2,'issue 40F6,0 ce  0~1plane')
        ce_bit = 0
        #ce_bit = 1 + 2 + 4 + 8# 0 1 2 3
        for i in range(max(1,self.ce_num)): # 
            ce_bit += 1 << i
        rsp, payload = issue_40F6_to_erase_in_direct_nand_mode(ce_bit, 3, blk, blk+1,slc_enable=0)        
        payload = vendor_cmd.direct_read(pca, 1,include_FW_spare = True)
        logger.flow(3,'check if data erase')
        status_of_blk = payload[128 + DATA_SIZE_4K_BYTE]
        logger.info(f'status_of_blk = {status_of_blk}')
        if not (is_bit3_set(status_of_blk)):
            logger.error_fp(f'data compare fail, bit 3(ERASE status) of value({status_of_blk}) != 1)')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL               
        pass    
    def pre_process_assert_0x5014(self) -> None:
        logger.flow(1,'write data on lun0, 65535(4K), get PCA')
        lun = 0
        lba = 0
        chunk_size = 65535
        total_len = 65535 * 6
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
        dump_array = pickle.dumps(pca)
        dump_array = bytearray(dump_array)
        dumpfile('PCA.bin',dump_array)
        blk = (pca.b11_block_h << 8) + pca.b10_block_l
        print(blk)
        logger.flow(2,'issue 40F6,0 ce  0~1plane')
        ce_bit = 1
        rsp, payload = issue_40F6_to_erase_in_direct_nand_mode(ce_bit, 3, blk, blk+1,slc_enable=0)
        payload = vendor_cmd.direct_read(pca, 1,include_FW_spare = True)
        logger.flow(3,'check if data erase')
        print(payload[128 + DATA_SIZE_4K_BYTE])
        pass
    def step1(self) -> None:
                       
        pass
    def post_process(self) -> None:
        pass
    



run = Pattern().run
if __name__ == "__main__":
    run()