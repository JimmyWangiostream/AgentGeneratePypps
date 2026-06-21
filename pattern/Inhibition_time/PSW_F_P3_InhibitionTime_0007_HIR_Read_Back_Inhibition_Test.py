import package_root
from Script import api
from Script.api import dumpfile, cmd_seq as ExecuteCMD
from Script.pattern.pattern_template import UFSTC
from Script.pattern.pattern_logger import logger
from Script import project_api
import random
from Script.api.exception import *
from Script.api.ufs_api.vendor_cmd.functions import set_mconfig, get_mconfig
from Script.api.ufs_api.defines.constant_define import *
from typing import cast
from Script.api.ufs_api import *
import time
from Script.pattern.Inhibition_time.mutual_fun import *
 
class Pattern(UFSTC):
    def pre_process(self) -> None:
       
        pass

    def step1(self) -> None:
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock')) # for ARM load in cache
        logger.flow(1, 'get hw setting of inhibition time')
        self.inhibition_time_sec = self.get_hwsetting_inhibition_time()
        self.backup_inhibition_time_sec = self.inhibition_time_sec
        logger.flow(2, 'power cycle + init')
        self.power_cycle()
        logger.flow(3, 'check if gInhibitMgr.lock = 1')
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))
        if self.inhibination_enable != 1:
            logger.error_fp(f'inhibination_enable({self.inhibination_enable}) != 1')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL           
        logger.flow(4, 'HIR + Read back target GC (FG only) ')        
        # need feature owner describe details 
        trigger_hir()
        before_node = get_read_back_node()

        logger.flow(5, 'check if gc trigger , if  not triggered determine fail')
        check_hir_trigger()
        # need feature owner describe details 
        if check_if_Read_Back_triggered(before_node=before_node) != True:
            logger.error_lb(f'check if read_back was triggered')
            logger.error_fp(f'The expected read_back was triggered, but it did not happen as expected, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL

        logger.flow(6, f'idle for inhibition time {self.inhibition_time_sec} sec')
        time.sleep(self.inhibition_time_sec)

        logger.flow(7, f'check if  gInhibitMgr.lock = 0')
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))
        time.sleep(0.01)
        self.inhibination_enable = cast(int,read_fw_value('gInhibitMgr.lock'))            
        if self.inhibination_enable != 0:
            logger.error_fp(f'inhibination_enable({self.inhibination_enable}) != 0')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL   
        logger.flow(8, 'HIR + Read back target GC (FG only) ')        
        # need feature owner describe detail
        trigger_hir()
        before_node = get_read_back_node()
        logger.flow(9, 'check if gc trigger , if  not triggered determine fail')
        check_hir_trigger()
        # need feature owner describe details 
        if check_if_Read_Back_triggered(before_node=before_node) != True:
            logger.error_lb(f'check if read_back was triggered')
            logger.error_fp(f'The expected read_back was triggered, but it did not happen as expected, result Fail!')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
                     
    def power_cycle(self)->None:
       if random.randint(0,1):
            init_tester_to_unit_ready(resetmode = Dcmd5ResetType.HW_RESET, powerdown = False)
       else:
           init_tester_to_unit_ready(resetmode = Dcmd5ResetType.HW_RESET, powerdown = True)
       access_vendor_mode()
    def get_hwsetting_inhibition_time(self) -> int:
 
        self.hw_setting = api.HwSetting.get_instance()
        self.hw_setting.update_from_device()        
        value = self.hw_setting.get_local_val(api.HwSettingField.INHIBITION_TIME)
        return value
    def post_process(self) -> None:
        pass
def host_write_data(lun:int, start_lba:int, len:int, total_len:int, random_chunk:bool=False) -> None:
    while total_len > 0:
        if random_chunk == True:
            len = random.randint(BLOCK4K_SIZE_4K_BYTE, WRITE_10_MAX_BLOCK_LEN)
        len = min(total_len, len)
        write10 = ExecuteCMD.Write10()
        logger.info(f'start lba = {start_lba}, len = {len}')
        write10.assign(lun=lun, lba=start_lba, length=len, fua=1)
        ExecuteCMD.enqueue(write10)
        start_lba += len
        total_len -= len
    ExecuteCMD.send(clear_on_success=False)
    ExecuteCMD.clear()   

def trigger_hir() -> None:
    reconfig_to_erase_all_lun() # clear refreshprogress
    flashsetting = api.get_flash_setting()
    CE = flashsetting.FLH_Quantity * (BIT0 << flashsetting.Parallel)
    fw_geometry = api.get_fw_geometry()
    TLC_VB_4K_SIZE = (fw_geometry.l88_vb_size_u1 * 512) // api.DATA_SIZE_4K_BYTE
    SLC_VB_4K_SIZE = (fw_geometry.l84_vb_size_u0 * 512) // api.DATA_SIZE_4K_BYTE

    logger.flow("4-1","Set bRefreshUnit = 1, bRefreshMethod = 1, read dRefreshTotalCount")
    api.write_attribute(idn=api.AttributeIDN.REFRESH_UNIT, val=1)
    api.write_attribute(idn=api.AttributeIDN.REFRESH_METHOD, val=1)
    dev_desc = pattern_get_device_health_descriptor()
    refreshProgress_before = int.from_bytes(dev_desc[41:45])
    resfreshCount_before = int.from_bytes(dev_desc[37:41])
    logger.info(f'refreshprogress = {refreshProgress_before}, refreshCount = {resfreshCount_before}')

    logger.flow("2-1","write LUN 0 1.5 TLC VB size (small chunk and big chunk both)")
    data_len = WRITE_10_MAX_BLOCK_LEN
    total_len = (TLC_VB_4K_SIZE * 15) // 10
    host_write_data(lun=0,start_lba=0,len=data_len,total_len=total_len, random_chunk=True)
    api.set_flag(api.FlagIDN.REFRESH_EN)
    pass   
def check_hir_trigger() -> None:
    logger.flow(5,"read bRefreshStatus")
    start_time_inner = time.time()
    while True:
        check_timeout_min(start_time=start_time_inner,timeout_min=15)
        val = api.read_attribute(api.AttributeIDN.REFRESH_STATUS)
        if val == 3:
            break
        elif val == 1:
            continue
        else:
            logger.error_lb(f'check bRefreshStatus until 03h')
            logger.error_fp(f'Expect refresh status = 03h, but = {val}')
            raise SIGHTING_FAIL_DATA_COMPARE_FAIL
    dev_desc = pattern_get_device_health_descriptor()
    refreshProgress_after = int.from_bytes(dev_desc[41:45])
    resfreshCount_after = int.from_bytes(dev_desc[37:41])
    logger.info(f'refreshprogress = {refreshProgress_after}, refreshCount = {resfreshCount_after}')
    pass
def pattern_get_device_health_descriptor() ->  bytearray:
    idn = api.DescriptorIDN.DEVICE_HEALTH
    index = 0x00
    selector = 0x00
    cmd = ExecuteCMD.ReadDescriptor()
    cmd.assign(idn, index, selector)
    cmd_index = ExecuteCMD.enqueue(cmd)

    ExecuteCMD.send(clear_on_success=False)
    resp = cast(api.QueryResponse, ExecuteCMD.read_response(cmd_index))
    ExecuteCMD.clear()
    return resp.data

def check_timeout_min(start_time: float, timeout_min: int) -> bool:
    current_time = time.time()
    if (current_time - start_time) >= timeout_min * 60:
        return True
    else:
        return False
def reconfig_to_erase_all_lun() -> None:
    config_descs = api.get_config_descriptors(print=False)
    for index in range(4):
        config_descs[index].header.b2_conf_desc_continue = api.ConfDescContinue.DISABLE if index == 3 else api.ConfDescContinue.ENABLE
    for index in range(4):
        api.push_write_config(config_descs[index], index=index)
    ExecuteCMD.send()

 
run = Pattern().run
if __name__ == "__main__":
    run()